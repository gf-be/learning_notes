#!/usr/bin/env python3
"""Validate a saved YOLO ``best.pt`` after checking the validation labels.

Example (run this on the Linux training server)::

    python revalidate_yolo_best.py \
      --weights /home/featurize/work/yolo26_1/ultralytics/runs/detect/runs_668_v3/base2/weights/best.pt \
      --data /home/featurize/data/yolo_dataset_v3_7_3/data.yaml \
      --imgsz 2048 --batch 6 --device 0 \
      --project runs_668_v3/revalidate --name base2_best_fixed_labels \
      --expected-val-images 200 --expected-val-instances 1798 --strict

The script never trains or changes the model.  It evaluates the saved best.pt
against the selected validation split only.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import yaml
from ultralytics import YOLO


IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--weights", required=True, type=Path, help="Saved best.pt path")
    parser.add_argument("--data", required=True, type=Path, help="YOLO data.yaml path")
    parser.add_argument("--imgsz", type=int, default=2048, help="Validation image size")
    parser.add_argument("--batch", type=int, default=6, help="Validation batch size")
    parser.add_argument("--device", default="0", help="CUDA device, e.g. 0")
    parser.add_argument("--project", default="runs_668_v3/revalidate", help="Validation result root")
    parser.add_argument("--name", default="bestpt_revalidate", help="Validation run name")
    parser.add_argument("--expected-val-images", type=int, default=None, help="Expected validation image count")
    parser.add_argument("--expected-val-instances", type=int, default=None, help="Expected validation instance count")
    parser.add_argument("--strict", action="store_true", help="Stop if expected counts do not match")
    parser.add_argument("--clear-cache", action="store_true", help="Delete labels/val.cache before validation so Ultralytics rebuilds it")
    return parser.parse_args()


def resolve_dataset_root(data_path: Path, config: dict) -> Path:
    configured_path = config.get("path")
    if configured_path:
        root = Path(str(configured_path))
        if not root.is_absolute():
            root = (data_path.parent / root).resolve()
    else:
        root = data_path.parent.resolve()
    return root


def resolve_split_dir(dataset_root: Path, split_value: str) -> Path:
    split_path = Path(str(split_value))
    return split_path if split_path.is_absolute() else (dataset_root / split_path)


def count_labels(labels_dir: Path) -> tuple[int, Counter[int]]:
    total = 0
    per_class: Counter[int] = Counter()
    for label_path in labels_dir.glob("*.txt"):
        for line_number, line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            fields = line.split()
            if len(fields) != 5:
                raise ValueError(f"{label_path}:{line_number} 应为 5 列检测标签，实际为 {len(fields)} 列")
            class_id = int(float(fields[0]))
            total += 1
            per_class[class_id] += 1
    return total, per_class


def main() -> None:
    args = parse_args()
    weights, data_path = args.weights.expanduser().resolve(), args.data.expanduser().resolve()
    if not weights.is_file():
        raise SystemExit(f"未找到权重文件：{weights}")
    if not data_path.is_file():
        raise SystemExit(f"未找到 data.yaml：{data_path}")

    with data_path.open("r", encoding="utf-8-sig") as stream:
        config = yaml.safe_load(stream) or {}
    if "val" not in config:
        raise SystemExit("data.yaml 中缺少 val 配置。")
    dataset_root = resolve_dataset_root(data_path, config)
    val_image_dir = resolve_split_dir(dataset_root, config["val"])
    if val_image_dir.name != "val":
        print(f"警告：data.yaml 的 val 目录为 {val_image_dir}")
    val_label_dir = val_image_dir.parent.parent / "labels" / val_image_dir.name
    if not val_image_dir.is_dir() or not val_label_dir.is_dir():
        raise SystemExit(f"验证图片或标签目录不存在：\n  images: {val_image_dir}\n  labels: {val_label_dir}")

    image_count = sum(path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES for path in val_image_dir.iterdir())
    label_count = sum(path.is_file() for path in val_label_dir.glob("*.txt"))
    instance_count, per_class = count_labels(val_label_dir)
    names = config.get("names", {})

    print("=== 验证集预检查 ===")
    print(f"data.yaml: {data_path}")
    print(f"验证图片目录: {val_image_dir}")
    print(f"验证标签目录: {val_label_dir}")
    print(f"图片数: {image_count}")
    print(f"标签文件数: {label_count}")
    print(f"标注实例数: {instance_count}")
    for class_id in sorted(per_class):
        label = names.get(class_id, names.get(str(class_id), f"class_{class_id}")) if isinstance(names, dict) else f"class_{class_id}"
        print(f"  {class_id}: {label} = {per_class[class_id]}")

    mismatches = []
    if args.expected_val_images is not None and image_count != args.expected_val_images:
        mismatches.append(f"图片数应为 {args.expected_val_images}，实际为 {image_count}")
    if args.expected_val_instances is not None and instance_count != args.expected_val_instances:
        mismatches.append(f"实例数应为 {args.expected_val_instances}，实际为 {instance_count}")
    if image_count != label_count:
        mismatches.append(f"图片数 {image_count} 与标签文件数 {label_count} 不一致")
    if mismatches:
        message = "验证集预检查异常：\n- " + "\n- ".join(mismatches)
        if args.strict:
            raise SystemExit(message + "\n已启用 --strict，停止验证。")
        print("警告：" + message)

    cache_path = val_label_dir.parent / f"{val_label_dir.name}.cache"
    if args.clear_cache and cache_path.is_file():
        cache_path.unlink()
        print(f"已删除旧验证集缓存：{cache_path}")

    print("\n=== 开始 best.pt 验证 ===")
    model = YOLO(str(weights))
    model.val(
        data=str(data_path),
        split="val",
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name,
        exist_ok=False,
        plots=True,
    )


if __name__ == "__main__":
    main()
