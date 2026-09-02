#!/usr/bin/env python3
"""Augment every YOLO training image with flip, rotation, brightness and contrast.

The source must use images/{train,val} and labels/{train,val}. Originals and
validation data are retained. Each training image receives reproducible variants
whose YOLO detection boxes are transformed with the image geometry.
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageStat


IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="YOLO dataset root")
    parser.add_argument("output", type=Path, help="New output dataset; must not exist")
    parser.add_argument("--variants", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--rotation", type=float, default=3.0, help="Maximum absolute rotation in degrees")
    parser.add_argument("--brightness", nargs=2, type=float, default=(0.90, 1.10), metavar=("MIN", "MAX"))
    parser.add_argument("--contrast", nargs=2, type=float, default=(0.90, 1.10), metavar=("MIN", "MAX"))
    parser.add_argument("--image-mode", choices=("hardlink", "copy"), default="hardlink")
    parser.add_argument("--jpg-quality", type=int, default=95)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def read_labels(path: Path) -> list[list[float]]:
    rows: list[list[float]] = []
    if not path.exists():
        return rows
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 5:
            raise ValueError(f"Expected detection label with 5 fields: {path}:{number}")
        rows.append([float(value) for value in parts])
    return rows


def write_labels(path: Path, rows: list[list[float]]) -> None:
    text = "\n".join(
        f"{int(cls)} {x:.6f} {y:.6f} {w:.6f} {h:.6f}" for cls, x, y, w, h in rows
    )
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def link_or_copy(source: Path, target: Path, mode: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if mode == "hardlink":
        try:
            os.link(source, target)
            return
        except OSError:
            pass
    shutil.copy2(source, target)


def clone_dataset(source: Path, output: Path, mode: str) -> None:
    for split in ("train", "val"):
        for image in sorted((source / "images" / split).iterdir()):
            if image.is_file() and image.suffix.lower() in IMAGE_SUFFIXES:
                link_or_copy(image, output / "images" / split / image.name, mode)
                label = source / "labels" / split / f"{image.stem}.txt"
                destination = output / "labels" / split / f"{image.stem}.txt"
                destination.parent.mkdir(parents=True, exist_ok=True)
                if label.exists():
                    shutil.copy2(label, destination)
                else:
                    destination.write_text("", encoding="utf-8")
    for name in ("classes.txt", "split_manifest.csv", "split_summary.json"):
        path = source / name
        if path.exists():
            shutil.copy2(path, output / name)


def transform_boxes(
    rows: list[list[float]], width: int, height: int, matrix: np.ndarray
) -> list[list[float]]:
    transformed: list[list[float]] = []
    for cls, x, y, w, h in rows:
        # Horizontal flip is applied before rotation.
        x = 1.0 - x
        x1, y1 = (x - w / 2) * width, (y - h / 2) * height
        x2, y2 = (x + w / 2) * width, (y + h / 2) * height
        corners = np.array([[x1, y1, 1], [x2, y1, 1], [x2, y2, 1], [x1, y2, 1]], dtype=np.float64)
        points = corners @ matrix.T
        nx1 = max(0.0, float(points[:, 0].min()))
        ny1 = max(0.0, float(points[:, 1].min()))
        nx2 = min(float(width), float(points[:, 0].max()))
        ny2 = min(float(height), float(points[:, 1].max()))
        if nx2 - nx1 < 1.0 or ny2 - ny1 < 1.0:
            continue
        transformed.append([
            cls,
            ((nx1 + nx2) / 2) / width,
            ((ny1 + ny2) / 2) / height,
            (nx2 - nx1) / width,
            (ny2 - ny1) / height,
        ])
    return transformed


def augment(
    image: Image.Image,
    rows: list[list[float]],
    angle: float,
    brightness: float,
    contrast: float,
) -> tuple[Image.Image, list[list[float]]]:
    rgb = image.convert("RGB").transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    width, height = rgb.size
    matrix = cv2.getRotationMatrix2D((width / 2.0, height / 2.0), angle, 1.0)
    fill = tuple(int(value) for value in ImageStat.Stat(rgb).median[:3])
    array = cv2.warpAffine(
        np.asarray(rgb), matrix, (width, height), flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT, borderValue=fill,
    )
    result = Image.fromarray(array, "RGB")
    result = ImageEnhance.Brightness(result).enhance(brightness)
    result = ImageEnhance.Contrast(result).enhance(contrast)
    return result, transform_boxes(rows, width, height, matrix)


def main() -> int:
    args = parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    train_images, train_labels = source / "images" / "train", source / "labels" / "train"
    if not train_images.is_dir() or not train_labels.is_dir():
        raise SystemExit("Source must contain images/train and labels/train")
    if output.exists():
        raise SystemExit(f"Output already exists: {output}")
    if args.variants < 1 or args.rotation < 0:
        raise SystemExit("--variants must be positive and --rotation cannot be negative")
    if not (0 < args.brightness[0] <= args.brightness[1] and 0 < args.contrast[0] <= args.contrast[1]):
        raise SystemExit("Invalid brightness or contrast range")

    images = sorted(
        (path for path in train_images.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES),
        key=lambda path: path.name.casefold(),
    )
    print(f"Source train images: {len(images)}")
    print(f"Generated variants: {len(images) * args.variants}")
    print(f"Final train images: {len(images) * (args.variants + 1)}")
    if args.dry_run:
        return 0

    output.mkdir(parents=True)
    clone_dataset(source, output, args.image_mode)
    rng = random.Random(args.seed)
    manifest: list[dict[str, object]] = []
    for image_path in images:
        rows = read_labels(train_labels / f"{image_path.stem}.txt")
        with Image.open(image_path) as opened:
            for variant in range(1, args.variants + 1):
                angle = rng.uniform(-args.rotation, args.rotation)
                brightness = rng.uniform(*args.brightness)
                contrast = rng.uniform(*args.contrast)
                image, labels = augment(opened, rows, angle, brightness, contrast)
                stem = f"{image_path.stem}_flip_rot_bc_v{variant}"
                image.save(output / "images" / "train" / f"{stem}.jpg", quality=args.jpg_quality, subsampling=0)
                write_labels(output / "labels" / "train" / f"{stem}.txt", labels)
                manifest.append({
                    "generated_image": f"{stem}.jpg", "source_image": image_path.name,
                    "horizontal_flip": True, "rotation_deg": round(angle, 5),
                    "brightness": round(brightness, 5), "contrast": round(contrast, 5),
                    "source_objects": len(rows), "output_objects": len(labels), "seed": args.seed,
                })

    yaml = source / "data.yaml"
    if yaml.exists():
        lines = yaml.read_text(encoding="utf-8").splitlines()
        path_line = f"path: '{output.as_posix()}'"
        if lines and lines[0].startswith("path:"):
            lines[0] = path_line
        else:
            lines.insert(0, path_line)
        (output / "data.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")

    with (output / "augmentation_manifest.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest[0].keys()))
        writer.writeheader()
        writer.writerows(manifest)
    print(f"Created: {output}")
    print(f"Manifest: {output / 'augmentation_manifest.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
