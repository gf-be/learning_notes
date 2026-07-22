from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import cv2


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def apply_clahe(image_path: Path, output_path: Path, clip_limit: float, tile_grid_size: int) -> None:
    image = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise RuntimeError(f"Failed to read image: {image_path}")

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_grid_size, tile_grid_size))

    if image.ndim == 2:
        enhanced = clahe.apply(image)
    else:
        if image.shape[2] == 4:
            bgr = image[:, :, :3]
            alpha = image[:, :, 3]
        else:
            bgr = image
            alpha = None

        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        enhanced_bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        enhanced = cv2.merge([enhanced_bgr[:, :, 0], enhanced_bgr[:, :, 1], enhanced_bgr[:, :, 2], alpha]) if alpha is not None else enhanced_bgr

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), enhanced):
        raise RuntimeError(f"Failed to write image: {output_path}")


def convert_split(src_split: Path, dst_split: Path, clip_limit: float, tile_grid_size: int) -> dict[str, int]:
    src_images = src_split / "images"
    src_labels = src_split / "labels"
    dst_images = dst_split / "images"
    dst_labels = dst_split / "labels"
    dst_images.mkdir(parents=True, exist_ok=True)
    dst_labels.mkdir(parents=True, exist_ok=True)

    images = 0
    labels = 0
    for image_path in sorted(src_images.iterdir()):
        if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTS:
            continue
        out_image = dst_images / image_path.name
        apply_clahe(image_path, out_image, clip_limit, tile_grid_size)
        images += 1

        src_label = src_labels / f"{image_path.stem}.txt"
        dst_label = dst_labels / f"{image_path.stem}.txt"
        if src_label.exists():
            shutil.copy2(src_label, dst_label)
        else:
            dst_label.write_text("", encoding="utf-8")
        labels += 1

    return {"images": images, "labels": labels}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=Path, default=Path("photo_binary_defect"))
    parser.add_argument("--dst", type=Path, default=Path("photo_binary_defect_clahe"))
    parser.add_argument("--clip-limit", type=float, default=2.0)
    parser.add_argument("--tile-grid-size", type=int, default=8)
    parser.add_argument("--path-in-yaml", default="/home/featurize/data/photo_binary_defect_clahe")
    args = parser.parse_args()

    if args.dst.exists():
        shutil.rmtree(args.dst)
    args.dst.mkdir(parents=True, exist_ok=True)

    print(f"source: {args.src}")
    print(f"output: {args.dst}")
    print(f"clip_limit: {args.clip_limit}")
    print(f"tile_grid_size: {args.tile_grid_size}")

    for split in ("train", "val", "test"):
        stats = convert_split(args.src / split, args.dst / split, args.clip_limit, args.tile_grid_size)
        print(f"{split}: {stats}")

    yaml_text = f"""path: {args.path_in_yaml}
train: train/images
val: val/images
test: test/images

names:
  0: defect
"""
    (args.dst / "data.yaml").write_text(yaml_text, encoding="utf-8")


if __name__ == "__main__":
    main()
