#!/usr/bin/env python3
"""Create a reproducible, image-level stratified YOLO split from Labelme files.

The script preserves the source directory, keeps each image and its JSON label in
exactly one split, converts polygons to YOLO detection or segmentation labels,
and writes a split manifest plus per-class statistics.

Example
-------
python scripts/repartition_labelme_stratified.py \
  "photo/668/origin" "photo/668/yolo_dataset_stratified_v2" \
  --task detect --val-ratio 0.20 --classes chipping scratch splash spot \
  --min-val scratch=32 --seed 42
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import shutil
import sys
from collections import Counter
from pathlib import Path


IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path, help="Labelme image/JSON directory")
    parser.add_argument("output_dir", type=Path, help="New YOLO dataset directory")
    parser.add_argument("--task", choices=("detect", "segment"), default="detect")
    parser.add_argument("--val-ratio", type=float, default=0.20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--classes", nargs="+", required=True, help="Fixed class order")
    parser.add_argument(
        "--min-val", nargs="*", default=[], metavar="CLASS=COUNT",
        help="Minimum validation instances for selected rare classes, e.g. scratch=32",
    )
    parser.add_argument("--image-mode", choices=("hardlink", "copy"), default="hardlink")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def parse_minimums(items: list[str], classes: list[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid --min-val value: {item!r}; use CLASS=COUNT")
        label, value = item.split("=", 1)
        if label not in classes:
            raise ValueError(f"Unknown class in --min-val: {label}")
        count = int(value)
        if count < 0:
            raise ValueError("--min-val counts must be non-negative")
        result[label] = count
    return result


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def find_image(json_path: Path, data: dict, images_by_stem: dict[str, Path]) -> Path | None:
    image_path = data.get("imagePath")
    if image_path:
        candidate = json_path.parent / Path(str(image_path)).name
        if candidate.is_file():
            return candidate
    return images_by_stem.get(json_path.stem.casefold())


def shape_to_yolo(shape: dict, width: float, height: float, class_id: int, task: str) -> str | None:
    raw = shape.get("points") or []
    points: list[tuple[float, float]] = []
    for point in raw:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            return None
        x = min(max(float(point[0]), 0.0), width)
        y = min(max(float(point[1]), 0.0), height)
        points.append((x, y))
    if task == "segment":
        if len(points) < 3:
            return None
        values = [value for x, y in points for value in (x / width, y / height)]
    else:
        if len(points) < 2:
            return None
        xs, ys = zip(*points)
        x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
        if x2 <= x1 or y2 <= y1:
            return None
        values = [((x1 + x2) / 2) / width, ((y1 + y2) / 2) / height,
                  (x2 - x1) / width, (y2 - y1) / height]
    return f"{class_id} " + " ".join(f"{value:.8f}" for value in values)


def loss(counts: Counter[str], targets: dict[str, int], classes: list[str]) -> float:
    """Class-target loss. Relative error keeps common classes from dominating."""
    total = 0.0
    for label in classes:
        target = max(targets[label], 1)
        delta = counts[label] - targets[label]
        total += (delta / target) ** 2
    return total


def stratified_validation(
    records: list[dict],
    classes: list[str],
    targets: dict[str, int],
    n_val: int,
    seed: int,
    candidate_indices: list[int] | None = None,
    protected_indices: set[int] | None = None,
) -> set[int]:
    """Greedy multi-label selection followed by deterministic swap refinement."""
    rng = random.Random(seed)
    order = list(candidate_indices if candidate_indices is not None else range(len(records)))
    rng.shuffle(order)
    selected: set[int] = set(protected_indices or set())
    current: Counter[str] = Counter()
    for index in selected:
        current.update(records[index]["counts"])

    # Greedily add the image that produces the smallest class-distribution loss.
    while len(selected) < n_val:
        best_index: int | None = None
        best_score: float | None = None
        for index in order:
            if index in selected:
                continue
            candidate = current + records[index]["counts"]
            score = loss(candidate, targets, classes)
            # Prefer images containing still-deficient rare classes in a tie.
            deficit_bonus = sum(
                min(records[index]["counts"][label], max(targets[label] - current[label], 0))
                / max(targets[label], 1)
                for label in classes
            )
            score -= deficit_bonus * 0.02
            if best_score is None or score < best_score - 1e-12:
                best_index, best_score = index, score
        assert best_index is not None
        selected.add(best_index)
        current.update(records[best_index]["counts"])

    # Exchange selected/non-selected images if it improves class balance.
    for _ in range(8):
        improved = False
        # Protected samples are quota-controlled background images and must not
        # be swapped back into the training set.
        selected_order = [index for index in selected if index not in (protected_indices or set())]
        unselected_order = [i for i in order if i not in selected]
        rng.shuffle(selected_order)
        rng.shuffle(unselected_order)
        base_loss = loss(current, targets, classes)
        for out_index in selected_order:
            without = current - records[out_index]["counts"]
            for in_index in unselected_order:
                candidate = without + records[in_index]["counts"]
                candidate_loss = loss(candidate, targets, classes)
                if candidate_loss + 1e-12 < base_loss:
                    selected.remove(out_index)
                    selected.add(in_index)
                    current = candidate
                    improved = True
                    break
            if improved:
                break
        if not improved:
            break
    return selected


def materialize(source: Path, target: Path, mode: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if mode == "copy":
        shutil.copy2(source, target)
    else:
        try:
            os.link(source, target)
        except OSError:
            shutil.copy2(source, target)


def main() -> int:
    args = parse_args()
    if not 0 < args.val_ratio < 1:
        raise SystemExit("--val-ratio must be between 0 and 1")
    if len(args.classes) != len(set(args.classes)):
        raise SystemExit("--classes contains duplicate names")

    source = args.input_dir.resolve()
    output = args.output_dir.resolve()
    if not source.is_dir():
        raise SystemExit(f"Input directory does not exist: {source}")
    if output == source or source in output.parents:
        raise SystemExit("Output directory must not be the source directory or inside it")
    if output.exists():
        if not args.overwrite:
            raise SystemExit(f"Output already exists: {output}; use --overwrite to replace it")
        shutil.rmtree(output)

    try:
        minimums = parse_minimums(args.min_val, args.classes)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    class_ids = {label: index for index, label in enumerate(args.classes)}

    images = sorted((p for p in source.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES), key=lambda p: p.name.casefold())
    images_by_stem = {p.stem.casefold(): p for p in images}
    records: list[dict] = []
    warnings: list[str] = []
    annotations: dict[Path, tuple[Path, dict]] = {}

    for json_path in sorted(source.glob("*.json"), key=lambda p: p.name.casefold()):
        try:
            data = load_json(json_path)
        except (OSError, json.JSONDecodeError) as exc:
            warnings.append(f"Unreadable JSON {json_path.name}: {exc}")
            continue
        image = find_image(json_path, data, images_by_stem)
        if image is None:
            warnings.append(f"No image found for {json_path.name}")
            continue
        annotations[image] = (json_path, data)

    # Keep images that have no JSON file as empty-label background samples. This
    # preserves the original dataset size and avoids silently dropping negatives.
    for image in images:
        json_path, data = annotations.get(image, (None, None))
        if data is None:
            records.append({"image": image, "json": None, "counts": Counter(), "lines": []})
            continue
        width, height = float(data.get("imageWidth") or 0), float(data.get("imageHeight") or 0)
        if width <= 0 or height <= 0:
            warnings.append(f"Invalid dimensions in {json_path.name}")
            continue
        counts: Counter[str] = Counter()
        lines: list[str] = []
        for shape in data.get("shapes") or []:
            label = str(shape.get("label", "")).strip()
            if label not in class_ids:
                if label:
                    warnings.append(f"Skipped unknown label {label!r} in {json_path.name}")
                continue
            line = shape_to_yolo(shape, width, height, class_ids[label], args.task)
            if line is not None:
                lines.append(line)
                counts[label] += 1
        records.append({"image": image, "json": json_path, "counts": counts, "lines": lines})

    if not records:
        raise SystemExit("No valid Labelme image/JSON pairs found")
    n_val = round(len(records) * args.val_ratio)
    totals = Counter()
    for record in records:
        totals.update(record["counts"])
    targets = {label: max(round(totals[label] * args.val_ratio), minimums.get(label, 0)) for label in args.classes}
    impossible = [f"{label}={targets[label]} > total {totals[label]}" for label in args.classes if targets[label] > totals[label]]
    if impossible:
        raise SystemExit("Impossible validation targets: " + "; ".join(impossible))

    # Background/empty-label images are not informative for class balancing.
    # Reserve their validation share explicitly, so all negatives do not drift
    # into validation during the class-focused greedy selection.
    background_indices = [index for index, record in enumerate(records) if not record["counts"]]
    background_rng = random.Random(args.seed + 1)
    background_rng.shuffle(background_indices)
    n_background_val = round(len(background_indices) * args.val_ratio)
    protected_background = set(background_indices[:n_background_val])
    annotated_indices = [index for index in range(len(records)) if index not in background_indices]
    selected = stratified_validation(
        records,
        args.classes,
        targets,
        n_val,
        args.seed,
        candidate_indices=annotated_indices,
        protected_indices=protected_background,
    )
    train_counts: Counter[str] = Counter()
    val_counts: Counter[str] = Counter()
    manifest_rows: list[dict[str, object]] = []

    for index, record in enumerate(records):
        split = "val" if index in selected else "train"
        materialize(record["image"], output / "images" / split / record["image"].name, args.image_mode)
        label_path = output / "labels" / split / f"{record['image'].stem}.txt"
        label_path.parent.mkdir(parents=True, exist_ok=True)
        label_path.write_text("\n".join(record["lines"]) + ("\n" if record["lines"] else ""), encoding="utf-8")
        (val_counts if split == "val" else train_counts).update(record["counts"])
        manifest_rows.append({
            "image": record["image"].name,
            "source_json": record["json"].name if record["json"] else "",
            "split": split,
            **{label: record["counts"][label] for label in args.classes},
        })

    output.mkdir(parents=True, exist_ok=True)
    (output / "classes.txt").write_text("\n".join(args.classes) + "\n", encoding="utf-8")
    yaml = [f"path: '{output.as_posix()}'", "train: images/train", "val: images/val", f"nc: {len(args.classes)}", "names:"]
    yaml += [f"  {index}: '{label}'" for index, label in enumerate(args.classes)]
    (output / "data.yaml").write_text("\n".join(yaml) + "\n", encoding="utf-8")

    with (output / "split_manifest.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["image", "source_json", "split", *args.classes])
        writer.writeheader()
        writer.writerows(manifest_rows)

    summary = {
        "source": str(source), "seed": args.seed, "task": args.task, "val_ratio": args.val_ratio,
        "images": {"all": len(records), "train": len(records) - len(selected), "val": len(selected)},
        "classes": args.classes, "requested_val_instances": targets,
        "instances": {"all": dict(totals), "train": dict(train_counts), "val": dict(val_counts)},
        "warnings": warnings,
    }
    (output / "split_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Created: {output}")
    print(f"Images: all={len(records)}, train={len(records) - len(selected)}, val={len(selected)}; seed={args.seed}")
    print("Class instance counts:")
    for label in args.classes:
        print(f"  {label:10s} all={totals[label]:4d} train={train_counts[label]:4d} val={val_counts[label]:4d} target={targets[label]:4d}")
    print(f"Manifest: {output / 'split_manifest.csv'}")
    if warnings:
        print(f"Warnings: {len(warnings)} (see split_summary.json)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
