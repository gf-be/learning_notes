#!/usr/bin/env python3
"""Convert Labelme JSON annotations into a YOLO dataset.

Supports YOLO segmentation (Labelme polygons) and detection (polygon bounding
boxes). Only the Python standard library is required.
"""
# 运行指令：python .\scripts\labelme_to_yolo.py "Labelme目录" "YOLO输出目录"

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Labelme JSON files to a train/val YOLO dataset."
    )
    parser.add_argument("input_dir", type=Path, help="Directory containing Labelme JSON/images")
    parser.add_argument("output_dir", type=Path, help="Output YOLO dataset directory")
    parser.add_argument(
        "--task",
        choices=("segment", "detect"),
        default="segment",
        help="YOLO task: polygon segmentation (default) or bounding-box detection",
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.2,
        help="Fraction of images assigned to validation (default: 0.2)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Split random seed (default: 42)")
    parser.add_argument(
        "--classes",
        nargs="+",
        help="Explicit class order. By default labels are sorted alphabetically.",
    )
    parser.add_argument(
        "--image-mode",
        choices=("hardlink", "copy", "none"),
        default="hardlink",
        help="How to populate images: hardlink (default), copy, or none",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing output directory",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read {path}: {exc}") from exc


def find_image(json_path: Path, data: dict, images_by_stem: dict[str, Path]) -> Path | None:
    image_path = data.get("imagePath")
    if image_path:
        candidate = json_path.parent / Path(str(image_path)).name
        if candidate.is_file():
            return candidate
    return images_by_stem.get(json_path.stem.casefold())


def clipped_points(shape: dict, width: float, height: float, source: Path) -> list[tuple[float, float]]:
    points = shape.get("points") or []
    result: list[tuple[float, float]] = []
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            raise ValueError(f"Invalid point in {source}")
        x = min(max(float(point[0]), 0.0), width)
        y = min(max(float(point[1]), 0.0), height)
        result.append((x, y))
    return result


def yolo_line(
    class_id: int,
    points: list[tuple[float, float]],
    width: float,
    height: float,
    task: str,
) -> str | None:
    if task == "segment":
        if len(points) < 3:
            return None
        values: Iterable[float] = (value for xy in points for value in (xy[0] / width, xy[1] / height))
    else:
        if len(points) < 2:
            return None
        xs, ys = zip(*points)
        x1, x2 = min(xs), max(xs)
        y1, y2 = min(ys), max(ys)
        if x2 <= x1 or y2 <= y1:
            return None
        values = (
            ((x1 + x2) / 2) / width,
            ((y1 + y2) / 2) / height,
            (x2 - x1) / width,
            (y2 - y1) / height,
        )
    return f"{class_id} " + " ".join(f"{value:.8f}" for value in values)


def materialize_image(source: Path, target: Path, mode: str) -> None:
    if mode == "none":
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if mode == "copy":
        shutil.copy2(source, target)
        return
    try:
        os.link(source, target)
    except OSError:
        print(f"Warning: hardlink failed for {source.name}; copying instead.", file=sys.stderr)
        shutil.copy2(source, target)


def yaml_quote(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    if not input_dir.is_dir():
        print(f"Error: input directory does not exist: {input_dir}", file=sys.stderr)
        return 2
    if not 0.0 <= args.val_ratio < 1.0:
        print("Error: --val-ratio must be in [0, 1).", file=sys.stderr)
        return 2
    if output_dir == input_dir or input_dir in output_dir.parents:
        print("Error: output directory must not be inside the input directory.", file=sys.stderr)
        return 2
    if output_dir.exists():
        if not args.overwrite:
            print(f"Error: output exists; use --overwrite: {output_dir}", file=sys.stderr)
            return 2
        shutil.rmtree(output_dir)

    image_files = sorted(
        (path for path in input_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES),
        key=lambda path: path.name.casefold(),
    )
    images_by_stem = {path.stem.casefold(): path for path in image_files}
    json_files = sorted(input_dir.glob("*.json"), key=lambda path: path.name.casefold())
    records: dict[Path, dict] = {}
    labels: set[str] = set()
    warnings: list[str] = []

    for json_path in json_files:
        try:
            data = load_json(json_path)
        except ValueError as exc:
            warnings.append(str(exc))
            continue
        image = find_image(json_path, data, images_by_stem)
        if image is None:
            warnings.append(f"No matching image for {json_path.name}")
            continue
        records[image] = data
        for shape in data.get("shapes") or []:
            label = str(shape.get("label", "")).strip()
            if label:
                labels.add(label)

    classes = args.classes or sorted(labels, key=str.casefold)
    if len(classes) != len(set(classes)):
        print("Error: --classes contains duplicates.", file=sys.stderr)
        return 2
    unknown = sorted(labels - set(classes))
    if unknown:
        print(f"Error: labels absent from --classes: {', '.join(unknown)}", file=sys.stderr)
        return 2
    class_to_id = {name: index for index, name in enumerate(classes)}

    shuffled = image_files.copy()
    random.Random(args.seed).shuffle(shuffled)
    val_count = round(len(shuffled) * args.val_ratio)
    val_images = set(shuffled[:val_count])
    counts: Counter[str] = Counter()
    skipped_shapes = 0

    for image in image_files:
        split = "val" if image in val_images else "train"
        materialize_image(image, output_dir / "images" / split / image.name, args.image_mode)
        label_path = output_dir / "labels" / split / f"{image.stem}.txt"
        label_path.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        data = records.get(image)
        if data:
            width = float(data.get("imageWidth") or 0)
            height = float(data.get("imageHeight") or 0)
            if width <= 0 or height <= 0:
                warnings.append(f"Invalid image dimensions in {image.stem}.json")
            else:
                for shape in data.get("shapes") or []:
                    label = str(shape.get("label", "")).strip()
                    if label not in class_to_id:
                        skipped_shapes += 1
                        continue
                    try:
                        points = clipped_points(shape, width, height, input_dir / f"{image.stem}.json")
                        line = yolo_line(class_to_id[label], points, width, height, args.task)
                    except (TypeError, ValueError) as exc:
                        warnings.append(str(exc))
                        line = None
                    if line:
                        lines.append(line)
                        counts[label] += 1
                    else:
                        skipped_shapes += 1
        label_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "classes.txt").write_text("\n".join(classes) + "\n", encoding="utf-8")
    yaml_lines = [
        f"path: {yaml_quote(output_dir.as_posix())}",
        "train: images/train",
        "val: images/val",
        f"nc: {len(classes)}",
        "names:",
        *(f"  {index}: {yaml_quote(name)}" for index, name in enumerate(classes)),
    ]
    (output_dir / "data.yaml").write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")

    print(f"Created YOLO {args.task} dataset: {output_dir}")
    print(f"Images: {len(image_files)} (train={len(image_files) - val_count}, val={val_count})")
    print(f"JSON annotations read: {len(records)}/{len(json_files)}")
    print("Classes: " + ", ".join(f"{i}={name} ({counts[name]})" for i, name in enumerate(classes)))
    print(f"Empty-label images: {sum(1 for image in image_files if image not in records)}")
    print(f"Skipped invalid shapes: {skipped_shapes}")
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
