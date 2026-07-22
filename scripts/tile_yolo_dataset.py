from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from PIL import Image


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
    for image in images_dir.iterdir():
        if image.is_file() and image.suffix.lower() in IMAGE_EXTS and image.stem == stem:
            return image
    return None


def clip_box_to_tile(
    row: list[float],
    image_w: int,
    image_h: int,
    tile: tuple[int, int, int, int],
    min_visible: float,
    min_pixels: int,
) -> list[float] | None:
    cls, x, y, w, h = row
    x1 = (x - w / 2) * image_w
    y1 = (y - h / 2) * image_h
    x2 = (x + w / 2) * image_w
    y2 = (y + h / 2) * image_h
    orig_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    if orig_area <= 0:
        return None

    tx1, ty1, tx2, ty2 = tile
    ix1 = max(x1, tx1)
    iy1 = max(y1, ty1)
    ix2 = min(x2, tx2)
    iy2 = min(y2, ty2)
    iw = ix2 - ix1
    ih = iy2 - iy1
    if iw < min_pixels or ih < min_pixels:
        return None
    if (iw * ih) / orig_area < min_visible:
        return None

    tile_w = tx2 - tx1
    tile_h = ty2 - ty1
    nx = ((ix1 + ix2) / 2 - tx1) / tile_w
    ny = ((iy1 + iy2) / 2 - ty1) / tile_h
    nw = iw / tile_w
    nh = ih / tile_h
    return [cls, nx, ny, nw, nh]


def tile_split(
    src_split: Path,
    dst_split: Path,
    grid: int,
    min_visible: float,
    min_pixels: int,
) -> dict[str, int]:
    src_images = src_split / "images"
    src_labels = src_split / "labels"
    dst_images = dst_split / "images"
    dst_labels = dst_split / "labels"
    dst_images.mkdir(parents=True, exist_ok=True)
    dst_labels.mkdir(parents=True, exist_ok=True)

    image_count = 0
    tile_count = 0
    labeled_tiles = 0
    object_count = 0
    class_counts: dict[int, int] = {}

    for image_path in sorted(src_images.iterdir()):
        if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTS:
            continue
        image_count += 1
        labels = read_labels(src_labels / f"{image_path.stem}.txt")
        with Image.open(image_path) as image:
            width, height = image.size
            for row in range(grid):
                for col in range(grid):
                    tx1 = round(col * width / grid)
                    ty1 = round(row * height / grid)
                    tx2 = round((col + 1) * width / grid)
                    ty2 = round((row + 1) * height / grid)
                    tile = (tx1, ty1, tx2, ty2)
                    tile_img = image.crop(tile)
                    out_stem = f"{image_path.stem}_tile{grid}x{grid}_r{row}_c{col}"
                    out_image = dst_images / f"{out_stem}{image_path.suffix.lower()}"
                    out_label = dst_labels / f"{out_stem}.txt"

                    tile_labels: list[list[float]] = []
                    for label in labels:
                        clipped = clip_box_to_tile(label, width, height, tile, min_visible, min_pixels)
                        if clipped is not None:
                            tile_labels.append(clipped)
                            cls = int(clipped[0])
                            class_counts[cls] = class_counts.get(cls, 0) + 1

                    tile_img.save(out_image)
                    write_labels(out_label, tile_labels)
                    tile_count += 1
                    object_count += len(tile_labels)
                    if tile_labels:
                        labeled_tiles += 1

    return {
        "images": image_count,
        "tiles": tile_count,
        "labeled_tiles": labeled_tiles,
        "objects": object_count,
        **{f"class_{cls}": count for cls, count in sorted(class_counts.items())},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=Path, default=Path("photo"))
    parser.add_argument("--dst", type=Path, default=Path("photo_tile_2x2"))
    parser.add_argument("--grid", type=int, default=2)
    parser.add_argument("--min-visible", type=float, default=0.20)
    parser.add_argument("--min-pixels", type=int, default=2)
    parser.add_argument("--path-in-yaml", default="/home/featurize/data/photo_tile_2x2")
    args = parser.parse_args()

    if args.dst.exists():
        shutil.rmtree(args.dst)
    args.dst.mkdir(parents=True, exist_ok=True)

    print(f"source: {args.src}")
    print(f"output: {args.dst}")
    print(f"grid: {args.grid}x{args.grid}")
    print(f"min_visible: {args.min_visible}")

    for split in ("train", "val", "test"):
        stats = tile_split(
            args.src / split,
            args.dst / split,
            args.grid,
            args.min_visible,
            args.min_pixels,
        )
        print(f"{split}: {stats}")

    yaml_text = f"""path: {args.path_in_yaml}
train: train/images
val: val/images
test: test/images

names:
  0: splash
  1: scratch
  2: chipping
"""
    (args.dst / "data.yaml").write_text(yaml_text, encoding="utf-8")


if __name__ == "__main__":
    main()
