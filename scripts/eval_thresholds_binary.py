from __future__ import annotations

import csv
from pathlib import Path

import yaml
from ultralytics import YOLO


WEIGHTS = "runs_defect/binary_defect_img1536/weights/best.pt"
DATA_YAML = "./data_01_binary.yaml"
IMGSZ = 1536
IOU = 0.50
CONF_LIST = [0.10, 0.15, 0.20, 0.25, 0.30]
PROJECT = "runs_defect_threshold"
SPLIT = "test"


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def resolve_split_paths(data_yaml: str, split: str) -> tuple[Path, Path]:
    yaml_path = Path(data_yaml)
    with yaml_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    root = Path(data.get("path", yaml_path.parent))
    image_dir = Path(data[split])
    if not image_dir.is_absolute():
        image_dir = root / image_dir

    label_dir = Path(str(image_dir).replace("/images", "/labels").replace("\\images", "\\labels"))
    return image_dir, label_dir


def is_empty_label(label_path: Path) -> bool:
    if not label_path.exists():
        return True
    return not any(line.strip() for line in label_path.read_text(encoding="utf-8").splitlines())


def collect_normal_images(data_yaml: str, split: str) -> list[Path]:
    image_dir, label_dir = resolve_split_paths(data_yaml, split)
    normal_images: list[Path] = []

    for image_path in sorted(image_dir.iterdir()):
        if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTS:
            continue
        label_path = label_dir / f"{image_path.stem}.txt"
        if is_empty_label(label_path):
            normal_images.append(image_path)

    return normal_images


def metric_value(results, key: str) -> float:
    values = results.results_dict
    aliases = {
        "precision": ["metrics/precision(B)", "precision"],
        "recall": ["metrics/recall(B)", "recall"],
        "map50": ["metrics/mAP50(B)", "map50"],
        "map50_95": ["metrics/mAP50-95(B)", "map50_95"],
    }
    for candidate in aliases[key]:
        if candidate in values:
            return float(values[candidate])
    return float("nan")


def count_false_positives(model: YOLO, normal_images: list[Path], conf: float, iou: float) -> tuple[int, int]:
    if not normal_images:
        return 0, 0

    false_positive_images = 0
    false_positive_boxes = 0

    predictions = model.predict(
        source=[str(p) for p in normal_images],
        imgsz=IMGSZ,
        conf=conf,
        iou=iou,
        verbose=False,
        save=False,
        stream=False,
    )

    for pred in predictions:
        boxes = 0 if pred.boxes is None else len(pred.boxes)
        if boxes > 0:
            false_positive_images += 1
            false_positive_boxes += boxes

    return false_positive_images, false_positive_boxes


def main() -> None:
    model = YOLO(WEIGHTS)
    normal_images = collect_normal_images(DATA_YAML, SPLIT)

    print(f"Normal {SPLIT} images: {len(normal_images)}")

    rows = []
    for conf in CONF_LIST:
        run_name = f"conf_{conf:.2f}_iou_{IOU:.2f}".replace(".", "p")

        val_results = model.val(
            data=DATA_YAML,
            imgsz=IMGSZ,
            conf=conf,
            iou=IOU,
            split=SPLIT,
            project=PROJECT,
            name=run_name,
            plots=True,
        )

        fp_images, fp_boxes = count_false_positives(model, normal_images, conf, IOU)

        row = {
            "conf": conf,
            "iou": IOU,
            "precision": metric_value(val_results, "precision"),
            "recall": metric_value(val_results, "recall"),
            "mAP50": metric_value(val_results, "map50"),
            "mAP50-95": metric_value(val_results, "map50_95"),
            "normal_images": len(normal_images),
            "normal_fp_images": fp_images,
            "normal_fp_boxes": fp_boxes,
            "normal_fp_image_rate": fp_images / len(normal_images) if normal_images else 0.0,
        }
        rows.append(row)

        print(
            f"conf={conf:.2f} "
            f"P={row['precision']:.4f} "
            f"R={row['recall']:.4f} "
            f"mAP50={row['mAP50']:.4f} "
            f"normal_fp_images={fp_images}/{len(normal_images)} "
            f"normal_fp_boxes={fp_boxes}"
        )

    out_dir = Path(PROJECT)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / "threshold_summary.csv"

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved summary to: {out_csv}")


if __name__ == "__main__":
    main()
