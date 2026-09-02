#!/usr/bin/env python3
"""Create a class-balanced YOLO training set with physical image augmentation.

An integer program selects source-image repetition counts so that final class
instance totals are as close as possible. Every image containing the rarest
class is used at least once to retain diversity. Generated images use horizontal
flip, small rotation, brightness and contrast changes; detection boxes follow
the same geometry.
"""

from __future__ import annotations

import argparse
import csv
import random
import shutil
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.optimize import Bounds, LinearConstraint, milp

from augment_yolo_flip_rotate_bc import (
    IMAGE_SUFFIXES,
    augment,
    clone_dataset,
    read_labels,
    write_labels,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--target-train-images", type=int, default=1500)
    parser.add_argument("--max-per-source", type=int, default=75)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--rotation", type=float, default=3.0)
    parser.add_argument("--brightness", nargs=2, type=float, default=(0.90, 1.10))
    parser.add_argument("--contrast", nargs=2, type=float, default=(0.90, 1.10))
    parser.add_argument("--image-mode", choices=("hardlink", "copy"), default="hardlink")
    parser.add_argument("--jpg-quality", type=int, default=95)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def class_vector(rows: list[list[float]], class_count: int) -> np.ndarray:
    counts = np.zeros(class_count, dtype=float)
    for row in rows:
        class_id = int(row[0])
        if class_id < 0 or class_id >= class_count:
            raise ValueError(f"Class {class_id} is outside 0..{class_count - 1}")
        counts[class_id] += 1
    return counts


def optimize_repetitions(
    matrix: np.ndarray,
    generated_count: int,
    max_per_source: int,
) -> tuple[np.ndarray, np.ndarray]:
    class_count, image_count = matrix.shape
    base = matrix.sum(axis=1)
    rarest_class = int(np.argmin(base))
    lower = np.zeros(image_count)
    lower[matrix[rarest_class] > 0] = 1
    if lower.sum() > generated_count:
        raise SystemExit("Target is too small to include every rare-class source image")

    # Variables: integer repetitions per image, continuous maximum and minimum
    # final class counts. Minimize their range.
    rows: list[np.ndarray] = []
    lows: list[float] = []
    highs: list[float] = []
    total = np.zeros(image_count + 2)
    total[:image_count] = 1
    rows.append(total)
    lows.append(generated_count)
    highs.append(generated_count)
    for class_id in range(class_count):
        upper_row = np.zeros(image_count + 2)
        upper_row[:image_count] = matrix[class_id]
        upper_row[image_count] = -1
        rows.append(upper_row)
        lows.append(-np.inf)
        highs.append(-base[class_id])

        lower_row = np.zeros(image_count + 2)
        lower_row[:image_count] = -matrix[class_id]
        lower_row[image_count + 1] = 1
        rows.append(lower_row)
        lows.append(-np.inf)
        highs.append(base[class_id])

    objective = np.zeros(image_count + 2)
    objective[image_count] = 1
    objective[image_count + 1] = -1
    result = milp(
        objective,
        integrality=np.r_[np.ones(image_count), 0, 0],
        bounds=Bounds(
            np.r_[lower, 0, 0],
            np.r_[np.full(image_count, max_per_source), np.inf, np.inf],
        ),
        constraints=LinearConstraint(np.asarray(rows), lows, highs),
    )
    if not result.success or result.x is None:
        raise SystemExit(f"Could not build a balanced augmentation plan: {result.message}")
    repetitions = np.rint(result.x[:image_count]).astype(int)
    return repetitions, (base + matrix @ repetitions).astype(int)


def main() -> int:
    args = parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if output.exists():
        raise SystemExit(f"Output already exists: {output}")
    train_images = source / "images" / "train"
    train_labels = source / "labels" / "train"
    if not train_images.is_dir() or not train_labels.is_dir():
        raise SystemExit("Source must contain images/train and labels/train")

    images = sorted(
        (p for p in train_images.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES),
        key=lambda p: p.name.casefold(),
    )
    generated_count = args.target_train_images - len(images)
    if generated_count < 0:
        raise SystemExit("Target train size cannot be smaller than the source train size")
    labels = [read_labels(train_labels / f"{image.stem}.txt") for image in images]
    yaml_text = (source / "data.yaml").read_text(encoding="utf-8")
    class_count = 4
    for line in yaml_text.splitlines():
        if line.strip().startswith("nc:"):
            class_count = int(line.split(":", 1)[1].strip())
    matrix = np.stack([class_vector(rows, class_count) for rows in labels], axis=1)
    repetitions, final_counts = optimize_repetitions(matrix, generated_count, args.max_per_source)

    print(f"Original train images: {len(images)}")
    print(f"Generated images: {generated_count}")
    print(f"Final train images: {args.target_train_images}")
    print(f"Selected source images: {int(np.count_nonzero(repetitions))}")
    print(f"Maximum variants from one source: {int(repetitions.max(initial=0))}")
    print("Planned final class instances: " + ", ".join(map(str, final_counts.tolist())))
    if args.dry_run:
        return 0

    output.mkdir(parents=True)
    clone_dataset(source, output, args.image_mode)
    rng = random.Random(args.seed)
    manifest: list[dict[str, object]] = []
    for image_path, rows, count in zip(images, labels, repetitions):
        if count == 0:
            continue
        with Image.open(image_path) as opened:
            for variant in range(1, count + 1):
                angle = rng.uniform(-args.rotation, args.rotation)
                brightness = rng.uniform(*args.brightness)
                contrast = rng.uniform(*args.contrast)
                generated, new_labels = augment(opened, rows, angle, brightness, contrast)
                stem = f"{image_path.stem}_balanced_phys_v{variant:03d}"
                generated.save(
                    output / "images" / "train" / f"{stem}.jpg",
                    quality=args.jpg_quality,
                    subsampling=0,
                )
                write_labels(output / "labels" / "train" / f"{stem}.txt", new_labels)
                manifest.append({
                    "generated_image": f"{stem}.jpg",
                    "source_image": image_path.name,
                    "source_repeat": variant,
                    "horizontal_flip": True,
                    "rotation_deg": round(angle, 5),
                    "brightness": round(brightness, 5),
                    "contrast": round(contrast, 5),
                    "class_counts": "|".join(str(int(v)) for v in class_vector(rows, class_count)),
                    "seed": args.seed,
                })

    yaml_lines = yaml_text.splitlines()
    path_line = f"path: '{output.as_posix()}'"
    if yaml_lines and yaml_lines[0].startswith("path:"):
        yaml_lines[0] = path_line
    else:
        yaml_lines.insert(0, path_line)
    (output / "data.yaml").write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")
    with (output / "augmentation_manifest.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest[0].keys()))
        writer.writeheader()
        writer.writerows(manifest)
    with (output / "balance_summary.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["class_id", "original_instances", "generated_instances", "final_instances"])
        original = matrix.sum(axis=1).astype(int)
        for class_id in range(class_count):
            writer.writerow([class_id, original[class_id], final_counts[class_id] - original[class_id], final_counts[class_id]])
    print(f"Created: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
