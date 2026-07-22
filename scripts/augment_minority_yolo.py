from __future__ import annotations

import argparse
import math
import random
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageOps


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def read_labels(path: Path) -> list[list[float]]:
    rows: list[list[float]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            continue
        rows.append([float(parts[0]), *map(float, parts[1:])])
    return rows


def write_labels(path: Path, rows: list[list[float]]) -> None:
    text = "\n".join(
        f"{int(row[0])} {row[1]:.6f} {row[2]:.6f} {row[3]:.6f} {row[4]:.6f}"
        for row in rows
    )
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def find_image(images_dir: Path, stem: str) -> Path | None:
    for ext in IMAGE_EXTS:
        candidate = images_dir / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    lower_stem = stem.lower()
    for image in images_dir.iterdir():
        if image.is_file() and image.suffix.lower() in IMAGE_EXTS and image.stem.lower() == lower_stem:
            return image
    return None


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def flip_labels(rows: list[list[float]]) -> list[list[float]]:
    return [[row[0], 1.0 - row[1], row[2], row[3], row[4]] for row in rows]


def rotate_point(x: float, y: float, angle_rad: float, cx: float, cy: float) -> tuple[float, float]:
    dx = x - cx
    dy = y - cy
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    return cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a


def rotate_labels(rows: list[list[float]], angle_degrees: float) -> list[list[float]]:
    angle_rad = math.radians(angle_degrees)
    rotated: list[list[float]] = []
    for cls, x, y, w, h in rows:
        x1 = x - w / 2
        y1 = y - h / 2
        x2 = x + w / 2
        y2 = y + h / 2
        corners = [
            rotate_point(x1, y1, angle_rad, 0.5, 0.5),
            rotate_point(x2, y1, angle_rad, 0.5, 0.5),
            rotate_point(x2, y2, angle_rad, 0.5, 0.5),
            rotate_point(x1, y2, angle_rad, 0.5, 0.5),
        ]
        xs = [p[0] for p in corners]
        ys = [p[1] for p in corners]
        nx1 = clamp(min(xs))
        ny1 = clamp(min(ys))
        nx2 = clamp(max(xs))
        ny2 = clamp(max(ys))
        nw = nx2 - nx1
        nh = ny2 - ny1
        if nw <= 0.001 or nh <= 0.001:
            continue
        rotated.append([cls, (nx1 + nx2) / 2, (ny1 + ny2) / 2, nw, nh])
    return rotated


def add_noise(image: Image.Image, sigma: float) -> Image.Image:
    arr = np.asarray(image).astype(np.float32)
    noise = np.random.normal(0, sigma, arr.shape).astype(np.float32)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def augment_image(
    image: Image.Image,
    rows: list[list[float]],
    rng: random.Random,
    variant_index: int,
) -> tuple[Image.Image, list[list[float]], str]:
    aug = image.convert("RGB")
    labels = [row[:] for row in rows]
    ops: list[str] = []

    brightness = rng.uniform(0.90, 1.10)
    contrast = rng.uniform(0.90, 1.12)
    aug = ImageEnhance.Brightness(aug).enhance(brightness)
    aug = ImageEnhance.Contrast(aug).enhance(contrast)
    ops.append(f"b{brightness:.2f}")
    ops.append(f"c{contrast:.2f}")

    if variant_index % 2 == 0:
        aug = ImageOps.mirror(aug)
        labels = flip_labels(labels)
        ops.append("flip")

    angle = rng.uniform(-3.0, 3.0)
    if abs(angle) >= 0.5:
        fill = tuple(int(v) for v in np.asarray(aug).reshape(-1, 3).mean(axis=0))
        aug = aug.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=fill)
        labels = rotate_labels(labels, angle)
        ops.append(f"r{angle:.1f}")

    if variant_index % 3 == 0:
        sigma = rng.uniform(1.5, 4.0)
        aug = add_noise(aug, sigma)
        ops.append(f"n{sigma:.1f}")

    return aug, labels, "_".join(ops)


def count_classes(labels_dir: Path) -> dict[int, int]:
    counts: dict[int, int] = {}
    for label_path in labels_dir.glob("*.txt"):
        for row in read_labels(label_path):
            cls = int(row[0])
            counts[cls] = counts.get(cls, 0) + 1
    return dict(sorted(counts.items()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=Path, default=Path("photo/train"))
    parser.add_argument("--dst", type=Path, default=Path("photo/train_aug"))
    parser.add_argument("--seed", type=int, default=20260625)
    parser.add_argument("--exclude-class", type=int, action="append", default=[])
    parser.add_argument("--scratch-variants", type=int, default=2)
    parser.add_argument("--chipping-variants", type=int, default=1)
    args = parser.parse_args()

    src_images = args.src / "images"
    src_labels = args.src / "labels"
    dst_images = args.dst / "images"
    dst_labels = args.dst / "labels"

    if not src_images.exists() or not src_labels.exists():
        raise SystemExit(f"Expected YOLO folders under {args.src}: images/ and labels/")

    if args.dst.exists():
        shutil.rmtree(args.dst)
    dst_images.mkdir(parents=True, exist_ok=True)
    dst_labels.mkdir(parents=True, exist_ok=True)

    for image_path in src_images.iterdir():
        if image_path.is_file() and image_path.suffix.lower() in IMAGE_EXTS:
            shutil.copy2(image_path, dst_images / image_path.name)
    for label_path in src_labels.glob("*.txt"):
        shutil.copy2(label_path, dst_labels / label_path.name)

    rng = random.Random(args.seed)
    augmented = 0
    selected = 0
    skipped_excluded = 0

    for label_path in sorted(src_labels.glob("*.txt")):
        rows = read_labels(label_path)
        classes = {int(row[0]) for row in rows}
        if any(cls in classes for cls in args.exclude_class):
            if 1 in classes or 2 in classes:
                skipped_excluded += 1
            continue
        has_scratch = 1 in classes
        has_chipping = 2 in classes
        if not (has_scratch or has_chipping):
            continue

        image_path = find_image(src_images, label_path.stem)
        if image_path is None:
            continue

        selected += 1
        variants = args.scratch_variants if has_scratch else args.chipping_variants
        image = Image.open(image_path)
        for variant_index in range(variants):
            aug_image, aug_rows, op_name = augment_image(image, rows, rng, variant_index)
            if not aug_rows:
                continue
            out_stem = f"{image_path.stem}_minor_aug{variant_index + 1}_{op_name}"
            out_image = dst_images / f"{out_stem}{image_path.suffix.lower()}"
            out_label = dst_labels / f"{out_stem}.txt"
            aug_image.save(out_image)
            write_labels(out_label, aug_rows)
            augmented += 1

    before = count_classes(src_labels)
    after = count_classes(dst_labels)
    print(f"source: {args.src}")
    print(f"output: {args.dst}")
    print(f"selected minority images: {selected}")
    print(f"skipped minority images with excluded classes: {skipped_excluded}")
    print(f"created augmented images: {augmented}")
    print(f"class counts before: {before}")
    print(f"class counts after: {after}")
    print(f"total images after: {len(list(dst_images.iterdir()))}")
    print(f"total labels after: {len(list(dst_labels.glob('*.txt')))}")


if __name__ == "__main__":
    main()
