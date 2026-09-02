#!/usr/bin/env python3
"""Create a YOLO training dataset with targeted offline minority-class augmentation.

The source dataset must use the standard ``images/{train,val}`` and
``labels/{train,val}`` layout. Both YOLO detection (five-column) and instance
segmentation (polygon) label rows are supported. Validation images/labels are
copied unchanged; only selected training images receive new variants.

Example (run on the training server):
    python augment_yolo_minority.py /home/featurize/data/yolo_dataset \
        /home/featurize/data/yolo_dataset_scratch_aug --target-class 1 \
        --variants 2 --path-in-yaml /home/featurize/data/yolo_dataset_scratch_aug
"""

from __future__ import annotations

import argparse
import os
import random
import re
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageOps


IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline-augment only training images containing one YOLO class.")
    parser.add_argument("source", type=Path, help="YOLO dataset root (images/train, labels/train)")
    parser.add_argument("output", type=Path, help="New dataset root; it must not already exist")
    parser.add_argument("--target-class", type=int, required=True, help="Class ID to oversample")
    parser.add_argument("--variants", type=int, default=2, help="Augmented variants per selected image (default: 2)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--hflip-prob", type=float, default=0.5, help="Horizontal-flip probability (default: 0.5)")
    parser.add_argument("--brightness", nargs=2, type=float, default=(0.90, 1.10), metavar=("MIN", "MAX"))
    parser.add_argument("--contrast", nargs=2, type=float, default=(0.90, 1.15), metavar=("MIN", "MAX"))
    parser.add_argument("--noise-std", type=float, default=3.0, help="Gaussian-noise standard deviation; 0 disables it")
    parser.add_argument("--image-mode", choices=("hardlink", "copy"), default="hardlink")
    parser.add_argument("--data-yaml", type=Path, help="Source dataset YAML (default: source/data.yaml)")
    parser.add_argument("--path-in-yaml", help="Absolute path to write into the output data.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Report selected files without creating output")
    return parser.parse_args()


def label_rows(path: Path) -> list[list[str]]:
    if not path.is_file():
        return []
    return [line.split() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def has_class(rows: list[list[str]], class_id: int) -> bool:
    return any(len(row) >= 2 and row[0].isdigit() and int(row[0]) == class_id for row in rows)


def flip_label_rows(rows: list[list[str]]) -> list[list[str]]:
    """Flip detection boxes or segmentation polygons horizontally."""
    flipped: list[list[str]] = []
    for row in rows:
        if len(row) == 5:  # class, x_center, y_center, width, height
            transformed = row.copy()
            transformed[1] = f"{1.0 - float(row[1]):.8f}"
        elif len(row) >= 7 and len(row) % 2 == 1:  # class, x1, y1, x2, y2, ...
            transformed = row.copy()
            for index in range(1, len(row), 2):
                transformed[index] = f"{1.0 - float(row[index]):.8f}"
        else:
            raise ValueError("unsupported YOLO label row: " + " ".join(row[:8]))
        flipped.append(transformed)
    return flipped


def add_noise(image: Image.Image, rng: np.random.Generator, std: float) -> Image.Image:
    if std <= 0:
        return image
    array = np.asarray(image).astype(np.float32)
    noise = rng.normal(0.0, std, size=array.shape)
    return Image.fromarray(np.clip(array + noise, 0, 255).astype(np.uint8))


def augment_image(
    source: Path,
    rows: list[list[str]],
    rng: random.Random,
    np_rng: np.random.Generator,
    args: argparse.Namespace,
) -> tuple[Image.Image, list[list[str]], str]:
    with Image.open(source) as opened:
        image = opened.copy()
    brightness = rng.uniform(*args.brightness)
    contrast = rng.uniform(*args.contrast)
    image = ImageEnhance.Brightness(image).enhance(brightness)
    image = ImageEnhance.Contrast(image).enhance(contrast)
    image = add_noise(image, np_rng, args.noise_std)
    out_rows = rows
    operation = f"b{brightness:.2f}_c{contrast:.2f}_n{args.noise_std:g}"
    if rng.random() < args.hflip_prob:
        image = ImageOps.mirror(image)
        out_rows = flip_label_rows(rows)
        operation += "_flip"
    return image, out_rows, operation


def materialize(source: Path, target: Path, mode: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if mode == "copy":
        shutil.copy2(source, target)
        return
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def clone_original_dataset(source: Path, output: Path, mode: str) -> None:
    for split in ("train", "val", "test"):
        image_dir = source / "images" / split
        if not image_dir.is_dir():
            continue
        for image in image_dir.iterdir():
            if image.is_file() and image.suffix.lower() in IMAGE_SUFFIXES:
                materialize(image, output / "images" / split / image.name, mode)
                label = source / "labels" / split / f"{image.stem}.txt"
                target_label = output / "labels" / split / f"{image.stem}.txt"
                target_label.parent.mkdir(parents=True, exist_ok=True)
                if label.is_file():
                    shutil.copy2(label, target_label)
                else:
                    target_label.write_text("", encoding="utf-8")


def write_dataset_yaml(source: Path, output: Path, supplied_yaml: Path | None, path_in_yaml: str | None) -> None:
    yaml_path = supplied_yaml or source / "data.yaml"
    if not yaml_path.is_file():
        print("Warning: source data YAML not found; create output/data.yaml manually.", file=sys.stderr)
        return
    content = yaml_path.read_text(encoding="utf-8-sig")
    output_path = path_in_yaml or output.as_posix()
    replacement = f"path: {output_path}"
    if re.search(r"^path:\s*.*$", content, flags=re.MULTILINE):
        content = re.sub(r"^path:\s*.*$", replacement, content, count=1, flags=re.MULTILINE)
    else:
        content = replacement + "\n" + content
    (output / "data.yaml").write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    train_images = source / "images" / "train"
    if not train_images.is_dir() or not (source / "labels" / "train").is_dir():
        print("Error: expected images/train and labels/train under source.", file=sys.stderr)
        return 2
    if output.exists():
        print(f"Error: output already exists: {output}", file=sys.stderr)
        return 2
    if args.variants < 1 or not 0 <= args.hflip_prob <= 1:
        print("Error: --variants must be positive and --hflip-prob must be in [0, 1].", file=sys.stderr)
        return 2

    selected: list[tuple[Path, list[list[str]]]] = []
    for image in sorted(train_images.iterdir(), key=lambda path: path.name.casefold()):
        if not image.is_file() or image.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        rows = label_rows(source / "labels" / "train" / f"{image.stem}.txt")
        if has_class(rows, args.target_class):
            selected.append((image, rows))
    print(f"Selected train images containing class {args.target_class}: {len(selected)}")
    print(f"New augmented train images: {len(selected) * args.variants}")
    if args.dry_run:
        return 0

    output.mkdir(parents=True)
    clone_original_dataset(source, output, args.image_mode)
    rng = random.Random(args.seed)
    np_rng = np.random.default_rng(args.seed)
    created = 0
    for image, rows in selected:
        for index in range(1, args.variants + 1):
            aug_image, aug_rows, operation = augment_image(image, rows, rng, np_rng, args)
            stem = f"{image.stem}_minority_c{args.target_class}_v{index}_{operation}"
            target_image = output / "images" / "train" / f"{stem}{image.suffix.lower()}"
            target_label = output / "labels" / "train" / f"{stem}.txt"
            aug_image.save(target_image)
            target_label.write_text("\n".join(" ".join(row) for row in aug_rows) + "\n", encoding="utf-8")
            created += 1
    write_dataset_yaml(source, output, args.data_yaml, args.path_in_yaml)
    print(f"Created: {output}")
    print(f"Augmented images written: {created}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
