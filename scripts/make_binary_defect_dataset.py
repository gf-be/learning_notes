from __future__ import annotations

import argparse
import shutil
from pathlib import Path


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def convert_label(src_label: Path, dst_label: Path) -> tuple[int, int]:
    kept = 0
    skipped = 0
    out_lines: list[str] = []

    if src_label.exists():
        for line in src_label.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 5:
                skipped += 1
                continue
            out_lines.append("0 " + " ".join(parts[1:]))
            kept += 1

    dst_label.write_text("\n".join(out_lines) + ("\n" if out_lines else ""), encoding="utf-8")
    return kept, skipped


def convert_split(src_split: Path, dst_split: Path) -> dict[str, int]:
    src_images = src_split / "images"
    src_labels = src_split / "labels"
    dst_images = dst_split / "images"
    dst_labels = dst_split / "labels"
    dst_images.mkdir(parents=True, exist_ok=True)
    dst_labels.mkdir(parents=True, exist_ok=True)

    images = 0
    labels = 0
    objects = 0
    skipped_lines = 0

    for image_path in sorted(src_images.iterdir()):
        if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTS:
            continue
        images += 1
        shutil.copy2(image_path, dst_images / image_path.name)

        src_label = src_labels / f"{image_path.stem}.txt"
        dst_label = dst_labels / f"{image_path.stem}.txt"
        kept, skipped = convert_label(src_label, dst_label)
        objects += kept
        skipped_lines += skipped
        labels += 1

    return {
        "images": images,
        "labels": labels,
        "objects": objects,
        "skipped_bad_label_lines": skipped_lines,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=Path, default=Path("photo"))
    parser.add_argument("--dst", type=Path, default=Path("photo_binary_defect"))
    parser.add_argument("--path-in-yaml", default="/home/featurize/data/photo_binary_defect")
    args = parser.parse_args()

    if args.dst.exists():
        shutil.rmtree(args.dst)
    args.dst.mkdir(parents=True, exist_ok=True)

    print(f"source: {args.src}")
    print(f"output: {args.dst}")

    for split in ("train", "val", "test"):
        stats = convert_split(args.src / split, args.dst / split)
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
