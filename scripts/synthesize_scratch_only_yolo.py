#!/usr/bin/env python3
"""Create scratch-only synthetic training samples for a YOLO segmentation dataset.

Original images and labels are retained. New samples paste one annotated
scratch polygon onto an image with an empty label file, so each new label file
contains only class 1 (scratch). Other class counts therefore do not increase.
"""

from __future__ import annotations

import argparse
import os
import random
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
SCRATCH_CLASS_ID = 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synthesize scratch-only YOLO polygon samples on clean backgrounds.")
    parser.add_argument("source", type=Path, help="Source YOLO segmentation dataset root")
    parser.add_argument("output", type=Path, help="New dataset root; must not already exist")
    parser.add_argument("--variants", type=int, default=2, help="Synthetic images per scratch instance (default: 2)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--padding", type=int, default=8, help="Pixel padding around each scratch polygon")
    parser.add_argument("--image-mode", choices=("hardlink", "copy"), default="hardlink")
    parser.add_argument("--path-in-yaml", help="Path written to output/data.yaml")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def read_rows(path: Path) -> list[list[str]]:
    if not path.is_file():
        return []
    return [line.split() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def polygon_from_row(row: list[str], width: int, height: int) -> list[tuple[float, float]] | None:
    if len(row) < 7 or len(row) % 2 != 1:
        return None
    try:
        values = [float(value) for value in row[1:]]
    except ValueError:
        return None
    return [(values[index] * width, values[index + 1] * height) for index in range(0, len(values), 2)]


def materialize(source: Path, target: Path, mode: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if mode == "copy":
        shutil.copy2(source, target)
        return
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def clone_source(source: Path, output: Path, mode: str) -> None:
    for split in ("train", "val", "test"):
        image_dir = source / "images" / split
        if not image_dir.is_dir():
            continue
        for image_path in image_dir.iterdir():
            if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            materialize(image_path, output / "images" / split / image_path.name, mode)
            label_path = source / "labels" / split / f"{image_path.stem}.txt"
            target_label = output / "labels" / split / f"{image_path.stem}.txt"
            target_label.parent.mkdir(parents=True, exist_ok=True)
            if label_path.is_file():
                shutil.copy2(label_path, target_label)
            else:
                target_label.write_text("", encoding="utf-8")


def write_yaml(source: Path, output: Path, path_in_yaml: str | None) -> None:
    names_path = source / "classes.txt"
    names = names_path.read_text(encoding="utf-8-sig").splitlines() if names_path.is_file() else ["chipping", "scratch", "splash", "spot"]
    dataset_path = path_in_yaml or output.as_posix()
    content = [
        f"path: '{dataset_path}'",
        "train: images/train",
        "val: images/val",
        f"nc: {len(names)}",
        "names:",
        *(f"  {index}: '{name}'" for index, name in enumerate(names)),
    ]
    (output / "data.yaml").write_text("\n".join(content) + "\n", encoding="utf-8")
    (output / "classes.txt").write_text("\n".join(names) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    images_dir = source / "images" / "train"
    labels_dir = source / "labels" / "train"
    if not images_dir.is_dir() or not labels_dir.is_dir():
        print("Error: expected images/train and labels/train under source.", file=sys.stderr)
        return 2
    if output.exists():
        print(f"Error: output already exists: {output}", file=sys.stderr)
        return 2
    if args.variants < 1 or args.padding < 0:
        print("Error: --variants must be positive and --padding cannot be negative.", file=sys.stderr)
        return 2

    images = sorted(
        (path for path in images_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES),
        key=lambda path: path.name.casefold(),
    )
    clean_backgrounds = [
        image for image in images if not read_rows(labels_dir / f"{image.stem}.txt")
    ]
    scratch_rows: list[tuple[Path, list[str]]] = []
    for image in images:
        for row in read_rows(labels_dir / f"{image.stem}.txt"):
            if row and row[0] == str(SCRATCH_CLASS_ID) and len(row) >= 7 and len(row) % 2 == 1:
                scratch_rows.append((image, row))
    if not clean_backgrounds:
        print("Error: no empty-label training images are available as clean backgrounds.", file=sys.stderr)
        return 2
    if not scratch_rows:
        print("Error: no polygon scratch labels (class 1) found.", file=sys.stderr)
        return 2

    print(f"Clean training backgrounds: {len(clean_backgrounds)}")
    print(f"Scratch instances available: {len(scratch_rows)}")
    print(f"New scratch-only images: {len(scratch_rows) * args.variants}")
    if args.dry_run:
        return 0

    output.mkdir(parents=True)
    clone_source(source, output, args.image_mode)
    write_yaml(source, output, args.path_in_yaml)
    rng = random.Random(args.seed)
    created = 0

    for source_image, row in scratch_rows:
        with Image.open(source_image) as opened:
            source_pixels = opened.convert("RGB")
        width, height = source_pixels.size
        polygon = polygon_from_row(row, width, height)
        if polygon is None:
            continue
        xs, ys = zip(*polygon)
        left = max(0, int(min(xs)) - args.padding)
        top = max(0, int(min(ys)) - args.padding)
        right = min(width, int(max(xs)) + args.padding + 1)
        bottom = min(height, int(max(ys)) + args.padding + 1)
        if right <= left or bottom <= top:
            continue
        patch = source_pixels.crop((left, top, right, bottom))
        alpha = Image.new("L", (width, height), 0)
        ImageDraw.Draw(alpha).polygon(polygon, fill=255)
        alpha = alpha.crop((left, top, right, bottom)).filter(ImageFilter.GaussianBlur(radius=0.6))

        for variant in range(1, args.variants + 1):
            background_path = rng.choice(clean_backgrounds)
            with Image.open(background_path) as opened:
                background = opened.convert("RGB")
            # Small photometric variation changes the pasted scratch only,
            # without changing its polygon or introducing another class.
            foreground = ImageEnhance.Brightness(patch).enhance(rng.uniform(0.96, 1.04))
            foreground = ImageEnhance.Contrast(foreground).enhance(rng.uniform(0.96, 1.08))
            background.paste(foreground, (left, top), alpha)
            stem = f"scratch_synth_{source_image.stem.replace(' ', '_')}_{created + 1:03d}_v{variant}"
            image_target = output / "images" / "train" / f"{stem}.bmp"
            label_target = output / "labels" / "train" / f"{stem}.txt"
            background.save(image_target)
            label_target.write_text(" ".join(row) + "\n", encoding="utf-8")
            created += 1

    print(f"Created scratch-only synthetic images: {created}")
    print(f"Output: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
