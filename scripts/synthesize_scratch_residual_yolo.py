#!/usr/bin/env python3
"""Create low-artifact scratch-only synthetic samples for a YOLO polygon dataset.

Unlike direct copy-paste, this script transfers only the high-frequency local
residual inside a scratch polygon onto a clean background at the same position.
This retains the target image's illumination and texture while preserving the
original scratch polygon exactly. Each synthetic label contains only class 1.
"""

from __future__ import annotations

import argparse
import os
import random
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np


IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
SCRATCH_CLASS = "1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create residual-blended scratch-only YOLO samples.")
    parser.add_argument("source", type=Path, help="Source YOLO polygon dataset root")
    parser.add_argument("output", type=Path, help="New output dataset root; it must not exist")
    parser.add_argument("--variants", type=int, default=1, help="Synthetic images per scratch instance (default: 1)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--padding", type=int, default=12, help="Crop padding around scratch polygon in pixels")
    parser.add_argument("--blur-sigma", type=float, default=5.0, help="Gaussian sigma used to estimate local background")
    parser.add_argument("--strength-min", type=float, default=0.8, help="Minimum residual blend strength")
    parser.add_argument("--strength-max", type=float, default=1.2, help="Maximum residual blend strength")
    parser.add_argument("--image-mode", choices=("hardlink", "copy"), default="hardlink")
    parser.add_argument("--path-in-yaml", help="Path written to output/data.yaml")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def label_rows(path: Path) -> list[list[str]]:
    if not path.is_file():
        return []
    return [line.split() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def polygon(row: list[str], width: int, height: int) -> np.ndarray | None:
    if len(row) < 7 or len(row) % 2 != 1:
        return None
    try:
        coordinates = np.array([float(value) for value in row[1:]], dtype=np.float32).reshape(-1, 2)
    except ValueError:
        return None
    coordinates[:, 0] *= width
    coordinates[:, 1] *= height
    return coordinates


def materialize(source: Path, target: Path, mode: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if mode == "copy":
        shutil.copy2(source, target)
        return
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def read_gray(path: Path) -> np.ndarray | None:
    """Read images from Unicode Windows paths, which cv2.imread may reject."""
    try:
        raw = np.fromfile(str(path), dtype=np.uint8)
    except OSError:
        return None
    return cv2.imdecode(raw, cv2.IMREAD_GRAYSCALE)


def write_gray(path: Path, image: np.ndarray) -> bool:
    suffix = path.suffix or ".bmp"
    ok, encoded = cv2.imencode(suffix, image)
    if not ok:
        return False
    try:
        encoded.tofile(str(path))
    except OSError:
        return False
    return True


def clone_dataset(source: Path, output: Path, mode: str) -> None:
    for split in ("train", "val", "test"):
        image_dir = source / "images" / split
        if not image_dir.is_dir():
            continue
        for image in image_dir.iterdir():
            if not image.is_file() or image.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            materialize(image, output / "images" / split / image.name, mode)
            source_label = source / "labels" / split / f"{image.stem}.txt"
            target_label = output / "labels" / split / f"{image.stem}.txt"
            target_label.parent.mkdir(parents=True, exist_ok=True)
            if source_label.is_file():
                shutil.copy2(source_label, target_label)
            else:
                target_label.write_text("", encoding="utf-8")


def write_yaml(source: Path, output: Path, output_path: str | None) -> None:
    classes_file = source / "classes.txt"
    names = classes_file.read_text(encoding="utf-8-sig").splitlines() if classes_file.is_file() else ["chipping", "scratch", "splash", "spot"]
    lines = [
        f"path: '{output_path or output.as_posix()}'",
        "train: images/train",
        "val: images/val",
        f"nc: {len(names)}",
        "names:",
        *(f"  {index}: '{name}'" for index, name in enumerate(names)),
    ]
    (output / "data.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output / "classes.txt").write_text("\n".join(names) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    image_dir = source / "images" / "train"
    label_dir = source / "labels" / "train"
    if not image_dir.is_dir() or not label_dir.is_dir():
        print("Error: expected images/train and labels/train under source.", file=sys.stderr)
        return 2
    if output.exists():
        print(f"Error: output already exists: {output}", file=sys.stderr)
        return 2
    if args.variants < 1 or args.strength_min <= 0 or args.strength_max < args.strength_min:
        print("Error: invalid variant count or residual-strength range.", file=sys.stderr)
        return 2

    images = sorted(
        (path for path in image_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES),
        key=lambda path: path.name.casefold(),
    )
    clean_backgrounds = [path for path in images if not label_rows(label_dir / f"{path.stem}.txt")]
    scratches: list[tuple[Path, list[str]]] = []
    for image in images:
        for row in label_rows(label_dir / f"{image.stem}.txt"):
            if row and row[0] == SCRATCH_CLASS and len(row) >= 7 and len(row) % 2 == 1:
                scratches.append((image, row))
    if not clean_backgrounds or not scratches:
        print("Error: clean backgrounds or polygon scratch labels were not found.", file=sys.stderr)
        return 2

    print(f"Clean training backgrounds: {len(clean_backgrounds)}")
    print(f"Scratch instances available: {len(scratches)}")
    print(f"New residual-blended scratch images: {len(scratches) * args.variants}")
    if args.dry_run:
        return 0

    output.mkdir(parents=True)
    clone_dataset(source, output, args.image_mode)
    write_yaml(source, output, args.path_in_yaml)
    rng = random.Random(args.seed)
    created = 0

    for source_image, row in scratches:
        foreground = read_gray(source_image)
        if foreground is None:
            continue
        height, width = foreground.shape
        points = polygon(row, width, height)
        if points is None:
            continue
        x1 = max(0, int(np.floor(points[:, 0].min())) - args.padding)
        y1 = max(0, int(np.floor(points[:, 1].min())) - args.padding)
        x2 = min(width, int(np.ceil(points[:, 0].max())) + args.padding + 1)
        y2 = min(height, int(np.ceil(points[:, 1].max())) + args.padding + 1)
        if x2 <= x1 or y2 <= y1:
            continue

        source_crop = foreground[y1:y2, x1:x2].astype(np.float32)
        local_background = cv2.GaussianBlur(source_crop, (0, 0), args.blur_sigma)
        residual = source_crop - local_background
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillPoly(mask, [np.round(points).astype(np.int32)], 255)
        alpha = cv2.GaussianBlur(mask[y1:y2, x1:x2].astype(np.float32) / 255.0, (0, 0), 0.6)

        for variant in range(1, args.variants + 1):
            background_path = rng.choice(clean_backgrounds)
            background = read_gray(background_path)
            if background is None or background.shape != foreground.shape:
                continue
            target_crop = background[y1:y2, x1:x2].astype(np.float32)
            strength = rng.uniform(args.strength_min, args.strength_max)
            blended_crop = np.clip(target_crop + strength * residual, 0, 255)
            background[y1:y2, x1:x2] = np.clip(
                target_crop * (1.0 - alpha) + blended_crop * alpha, 0, 255
            ).astype(np.uint8)
            stem = f"scratch_residual_{source_image.stem.replace(' ', '_')}_{created + 1:03d}_v{variant}"
            target_image = output / "images" / "train" / f"{stem}.bmp"
            target_label = output / "labels" / "train" / f"{stem}.txt"
            if not write_gray(target_image, background):
                raise RuntimeError(f"Could not write {target_image}")
            target_label.write_text(" ".join(row) + "\n", encoding="utf-8")
            created += 1

    print(f"Created residual-blended scratch images: {created}")
    print(f"Output: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
