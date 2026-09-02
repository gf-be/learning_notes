#!/usr/bin/env python3
"""Expand a YOLO detection training split with reproducible physical simulations.

Only ``images/train`` is augmented. ``images/val`` and all validation labels are
materialized unchanged, so validation remains an independent fixed benchmark.
The default expands 532 original training images to 3000 total training images.

The five augmentation recipes are deliberately mild and traceable:
  - position: systematic imaging-position shift plus scale variation;
  - pose: small rotation / mounting-angle variation;
  - focus: mild defocus combined with a small position shift;
  - illumination: exposure, contrast, gamma and mild vignette variation;
  - combined: a light combination of position, illumination and sensor noise.

All geometric transforms are applied to YOLO detection boxes. A CSV manifest
records each generated image, its parent image, recipe and sampled parameters.

Example
-------
python scripts/augment_yolo_physical_3k.py \
  photo/668/yolo_dataset_stratified_v2 \
  photo/668/yolo_dataset_stratified_v2_physaug3k \
  --target-train-images 3000 --seed 42
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageStat


IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
RECIPES = ("position", "pose", "focus", "illumination", "combined")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path, help="YOLO dataset root containing images/train and labels/train")
    parser.add_argument("output", type=Path, help="New output dataset directory; must not exist")
    parser.add_argument("--target-train-images", type=int, default=3000, help="Total train images including originals (default: 3000)")
    parser.add_argument("--seed", type=int, default=42, help="Fixed random seed (default: 42)")
    parser.add_argument("--image-mode", choices=("hardlink", "copy"), default="hardlink", help="How to preserve original images")
    parser.add_argument("--output-format", choices=("jpg", "png", "bmp"), default="jpg", help="Format for generated images (default: jpg to control disk usage)")
    parser.add_argument("--jpg-quality", type=int, default=95, help="JPEG quality for generated images (default: 95)")
    parser.add_argument("--position-shift", type=float, default=0.08, help="Maximum x/y systematic shift in image fraction (default: 0.08)")
    parser.add_argument("--scale-delta", type=float, default=0.06, help="Maximum scale deviation from 1 (default: 0.06)")
    parser.add_argument("--rotation-deg", type=float, default=4.0, help="Maximum rotation in degrees (default: 4.0)")
    parser.add_argument("--dry-run", action="store_true", help="Print plan only; do not write output")
    return parser.parse_args()


def read_labels(path: Path) -> list[list[float]]:
    rows: list[list[float]] = []
    if not path.is_file():
        return rows
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        fields = line.split()
        if not fields:
            continue
        if len(fields) != 5:
            raise ValueError(f"{path}:{line_number}: expected detection label with 5 columns, found {len(fields)}")
        try:
            cls, x, y, w, h = map(float, fields)
        except ValueError as exc:
            raise ValueError(f"{path}:{line_number}: invalid numeric label") from exc
        if w <= 0 or h <= 0:
            continue
        rows.append([cls, x, y, w, h])
    return rows


def write_labels(path: Path, rows: list[list[float]]) -> None:
    text = "\n".join(f"{int(cls)} {x:.8f} {y:.8f} {w:.8f} {h:.8f}" for cls, x, y, w, h in rows)
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def materialize(source: Path, target: Path, mode: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if mode == "copy":
        shutil.copy2(source, target)
        return
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def clone_original_splits(source: Path, output: Path, mode: str) -> None:
    for split in ("train", "val", "test"):
        image_dir = source / "images" / split
        if not image_dir.is_dir():
            continue
        for image_path in sorted(image_dir.iterdir(), key=lambda p: p.name.casefold()):
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


def box_corners(row: list[float]) -> list[tuple[float, float]]:
    _, x, y, w, h = row
    return [(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)]


def transform_boxes(rows: list[list[float]], transform) -> list[list[float]]:
    """Transform box corners in normalized coordinates and re-fit clipped boxes."""
    transformed: list[list[float]] = []
    for row in rows:
        points = [transform(x, y) for x, y in box_corners(row)]
        xs = [min(1.0, max(0.0, x)) for x, _ in points]
        ys = [min(1.0, max(0.0, y)) for _, y in points]
        x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
        if x2 - x1 < 0.001 or y2 - y1 < 0.001:
            continue
        transformed.append([row[0], (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1])
    return transformed


def fill_color(image: Image.Image) -> tuple[int, int, int]:
    median = ImageStat.Stat(image).median
    if len(median) == 1:
        return (int(median[0]),) * 3
    return tuple(int(value) for value in median[:3])


def position_transform(image: Image.Image, rows: list[list[float]], scale: float, tx: float, ty: float) -> tuple[Image.Image, list[list[float]]]:
    """Apply forward transform x'=scale*x+tx, y'=scale*y+ty."""
    width, height = image.size
    affine = (1 / scale, 0, -tx * width / scale, 0, 1 / scale, -ty * height / scale)
    moved = image.transform(
        image.size, Image.Transform.AFFINE, affine, resample=Image.Resampling.BICUBIC, fillcolor=fill_color(image)
    )
    labels = transform_boxes(rows, lambda x, y: (scale * x + tx, scale * y + ty))
    return moved, labels


def rotate_transform(image: Image.Image, rows: list[list[float]], angle: float) -> tuple[Image.Image, list[list[float]]]:
    radians = math.radians(angle)
    cos_a, sin_a = math.cos(radians), math.sin(radians)
    rotated = image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=fill_color(image))
    labels = transform_boxes(
        rows,
        lambda x, y: (0.5 + (x - 0.5) * cos_a - (y - 0.5) * sin_a,
                      0.5 + (x - 0.5) * sin_a + (y - 0.5) * cos_a),
    )
    return rotated, labels


def gamma_adjust(image: Image.Image, gamma: float) -> Image.Image:
    array = np.asarray(image).astype(np.float32) / 255.0
    array = np.clip(np.power(array, gamma) * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(array, mode="RGB")


def add_vignette(image: Image.Image, strength: float) -> Image.Image:
    if strength <= 0:
        return image
    width, height = image.size
    y, x = np.ogrid[-1:1:complex(height), -1:1:complex(width)]
    radius = np.minimum(1.0, np.sqrt(x * x + y * y) / math.sqrt(2.0))
    factor = 1.0 - strength * radius * radius
    array = np.asarray(image).astype(np.float32)
    return Image.fromarray(np.clip(array * factor[..., None], 0, 255).astype(np.uint8), mode="RGB")


def add_noise(image: Image.Image, rng: np.random.Generator, std: float) -> Image.Image:
    if std <= 0:
        return image
    array = np.asarray(image).astype(np.float32)
    noise = rng.normal(0.0, std, size=array.shape)
    return Image.fromarray(np.clip(array + noise, 0, 255).astype(np.uint8), mode="RGB")


def illumination_transform(image: Image.Image, brightness: float, contrast: float, gamma: float, vignette: float) -> Image.Image:
    result = ImageEnhance.Brightness(image).enhance(brightness)
    result = ImageEnhance.Contrast(result).enhance(contrast)
    result = gamma_adjust(result, gamma)
    return add_vignette(result, vignette)


def sample_position(rng: random.Random, max_shift: float, max_scale_delta: float) -> tuple[float, float, float]:
    return (
        rng.uniform(1.0 - max_scale_delta, 1.0 + max_scale_delta),
        rng.uniform(-max_shift, max_shift),
        rng.uniform(-max_shift, max_shift),
    )


def apply_recipe(
    image: Image.Image,
    rows: list[list[float]],
    recipe: str,
    rng: random.Random,
    np_rng: np.random.Generator,
    args: argparse.Namespace,
) -> tuple[Image.Image, list[list[float]], dict[str, float | str]]:
    image = image.convert("RGB")
    labels = [row[:] for row in rows]
    params: dict[str, float | str] = {"recipe": recipe}

    if recipe in {"position", "pose", "focus", "combined"}:
        shift = args.position_shift if recipe == "position" else args.position_shift * 0.65
        scale_delta = args.scale_delta if recipe != "focus" else args.scale_delta * 0.50
        scale, tx, ty = sample_position(rng, shift, scale_delta)
        image, labels = position_transform(image, labels, scale, tx, ty)
        params.update(scale=round(scale, 5), translate_x=round(tx, 5), translate_y=round(ty, 5))

    if recipe == "pose":
        angle = rng.uniform(-args.rotation_deg, args.rotation_deg)
        image, labels = rotate_transform(image, labels, angle)
        params["rotation_deg"] = round(angle, 4)

    if recipe == "focus":
        radius = rng.uniform(0.35, 1.20)
        image = image.filter(ImageFilter.GaussianBlur(radius=radius))
        params["gaussian_blur_radius"] = round(radius, 4)

    if recipe in {"illumination", "combined"}:
        brightness = rng.uniform(0.88, 1.14)
        contrast = rng.uniform(0.88, 1.14)
        gamma = rng.uniform(0.90, 1.12)
        vignette = rng.uniform(0.02, 0.10)
        image = illumination_transform(image, brightness, contrast, gamma, vignette)
        params.update(brightness=round(brightness, 4), contrast=round(contrast, 4), gamma=round(gamma, 4), vignette=round(vignette, 4))

    if recipe == "combined":
        noise_std = rng.uniform(0.8, 2.5)
        image = add_noise(image, np_rng, noise_std)
        params["noise_std"] = round(noise_std, 4)

    return image, labels, params


def count_instances(labels_dir: Path) -> Counter[int]:
    counts: Counter[int] = Counter()
    for label_path in labels_dir.glob("*.txt"):
        for row in read_labels(label_path):
            counts[int(row[0])] += 1
    return counts


def write_yaml(source: Path, output: Path) -> None:
    source_yaml = source / "data.yaml"
    if not source_yaml.is_file():
        return
    content = source_yaml.read_text(encoding="utf-8-sig")
    replacement = f"path: '{output.as_posix()}'"
    if re.search(r"^path:\s*.*$", content, flags=re.MULTILINE):
        content = re.sub(r"^path:\s*.*$", replacement, content, count=1, flags=re.MULTILINE)
    else:
        content = replacement + "\n" + content
    (output / "data.yaml").write_text(content, encoding="utf-8")


def save_generated(image: Image.Image, path: Path, image_format: str, jpg_quality: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if image_format == "jpg":
        image.save(path, format="JPEG", quality=jpg_quality, subsampling=0, optimize=True)
    elif image_format == "png":
        image.save(path, format="PNG", optimize=True)
    else:
        image.save(path, format="BMP")


def main() -> int:
    args = parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    train_images = source / "images" / "train"
    train_labels = source / "labels" / "train"
    if not train_images.is_dir() or not train_labels.is_dir():
        raise SystemExit("Expected a YOLO detection dataset with images/train and labels/train")
    if output.exists():
        raise SystemExit(f"Output already exists: {output}; choose a new directory")
    if args.target_train_images < 1:
        raise SystemExit("--target-train-images must be positive")
    if not 0 <= args.position_shift <= 0.20 or not 0 <= args.scale_delta <= 0.20:
        raise SystemExit("position shift and scale delta should be between 0 and 0.20")
    if not 20 <= args.jpg_quality <= 100:
        raise SystemExit("--jpg-quality must be 20..100")

    pairs: list[tuple[Path, Path, list[list[float]]]] = []
    for image_path in sorted(train_images.iterdir(), key=lambda p: p.name.casefold()):
        if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        label_path = train_labels / f"{image_path.stem}.txt"
        pairs.append((image_path, label_path, read_labels(label_path)))
    if not pairs:
        raise SystemExit("No training images found")
    if args.target_train_images < len(pairs):
        raise SystemExit(f"Target {args.target_train_images} is smaller than original train set {len(pairs)}")

    needed = args.target_train_images - len(pairs)
    recipe_plan = [RECIPES[index % len(RECIPES)] for index in range(needed)]
    rng = random.Random(args.seed)
    np_rng = np.random.default_rng(args.seed)
    source_order = list(range(len(pairs)))
    rng.shuffle(source_order)
    plan = [(source_order[index % len(source_order)], recipe_plan[index]) for index in range(needed)]

    print(f"Original training images: {len(pairs)}")
    print(f"Planned generated images: {needed}")
    print(f"Target training images: {args.target_train_images}")
    print("Recipe counts: " + ", ".join(f"{recipe}={recipe_plan.count(recipe)}" for recipe in RECIPES))
    if args.dry_run:
        return 0

    output.mkdir(parents=True)
    clone_original_splits(source, output, args.image_mode)
    extension = ".jpg" if args.output_format == "jpg" else f".{args.output_format}"
    manifest: list[dict[str, str]] = []

    for generated_index, (source_index, recipe) in enumerate(plan, 1):
        image_path, _, rows = pairs[source_index]
        with Image.open(image_path) as opened:
            augmented, labels, params = apply_recipe(opened.copy(), rows, recipe, rng, np_rng, args)
        stem = f"{image_path.stem}_phys_{recipe}_{generated_index:04d}"
        image_target = output / "images" / "train" / f"{stem}{extension}"
        label_target = output / "labels" / "train" / f"{stem}.txt"
        save_generated(augmented, image_target, args.output_format, args.jpg_quality)
        write_labels(label_target, labels)
        manifest.append({
            "generated_image": image_target.name,
            "source_image": image_path.name,
            "recipe": recipe,
            "parameters": json.dumps(params, ensure_ascii=False, sort_keys=True),
            "seed": str(args.seed),
        })
        if generated_index % 100 == 0 or generated_index == needed:
            print(f"Generated {generated_index}/{needed}")

    write_yaml(source, output)
    classes = (source / "classes.txt")
    if classes.is_file():
        shutil.copy2(classes, output / "classes.txt")
    with (output / "augmentation_manifest.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["generated_image", "source_image", "recipe", "parameters", "seed"])
        writer.writeheader()
        writer.writerows(manifest)

    summary = {
        "source": str(source), "seed": args.seed, "target_train_images": args.target_train_images,
        "original_train_images": len(pairs), "generated_train_images": needed,
        "recipes": {recipe: recipe_plan.count(recipe) for recipe in RECIPES},
        "parameters": {"position_shift": args.position_shift, "scale_delta": args.scale_delta, "rotation_deg": args.rotation_deg,
                       "output_format": args.output_format, "jpg_quality": args.jpg_quality},
        "train_instances": dict(count_instances(output / "labels" / "train")),
        "val_instances": dict(count_instances(output / "labels" / "val")),
    }
    (output / "augmentation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created: {output}")
    print(f"Manifest: {output / 'augmentation_manifest.csv'}")
    print("Train instances after augmentation: " + json.dumps(summary["train_instances"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
