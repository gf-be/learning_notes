"""Run YOLO prediction with a confidence threshold specific to each class.

The model is run once at the smallest configured threshold, then predictions
are retained only when their confidence meets the threshold for their class.
This is post-processing only: it does not retrain or change model weights.

Default thresholds are the current validation-set F1 candidates:
    chipping=0.30, scratch=0.15, splash=0.30, spot=0.25
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
from ultralytics import YOLO


DEFAULT_MODEL = (
    "/home/featurize/work/yolo26_1/ultralytics/runs/detect/runs_668/"
    "stage8_yolo26m_imgsz2048_lr2e4_mosaic010_v1/weights/best.pt"
)
DEFAULT_SOURCE = "/home/featurize/data/yolo_dataset/images/val"
DEFAULT_THRESHOLDS = [0.30, 0.15, 0.30, 0.25]
COLORS = [(255, 140, 0), (0, 200, 255), (70, 70, 230), (90, 220, 110)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Predict once and apply confidence thresholds by class."
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Path to best.pt")
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="Image folder or source")
    parser.add_argument("--imgsz", type=int, default=2048)
    parser.add_argument("--device", default="0")
    parser.add_argument(
        "--class-conf",
        type=float,
        nargs="+",
        default=DEFAULT_THRESHOLDS,
        metavar="CONF",
        help="One threshold per class ID, e.g. 0.30 0.15 0.30 0.25.",
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=0.70,
        help="NMS IoU threshold. Keep 0.70 for the baseline comparison.",
    )
    parser.add_argument("--project", default="runs_668_postprocess")
    parser.add_argument("--name", default="class_conf_c30_s15_sp30_st25_iou070")
    return parser.parse_args()


def draw_box(image, xyxy, label: str, color: tuple[int, int, int]) -> None:
    x1, y1, x2, y2 = (int(value) for value in xyxy)
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
    (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    label_y = max(text_h + 5, y1)
    cv2.rectangle(image, (x1, label_y - text_h - 5), (x1 + text_w + 6, label_y), color, -1)
    cv2.putText(
        image,
        label,
        (x1 + 3, label_y - 4),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def main() -> None:
    args = parse_args()
    if any(not 0 <= value <= 1 for value in args.class_conf):
        raise ValueError("Every --class-conf value must be in [0, 1].")
    if not 0 < args.iou <= 1:
        raise ValueError("--iou must be in (0, 1].")

    output_dir = Path(args.project) / args.name
    label_dir = output_dir / "labels"
    image_dir = output_dir / "images"
    if output_dir.exists():
        raise FileExistsError(
            f"Output already exists: {output_dir}. Choose a different --name to avoid overwriting."
        )
    label_dir.mkdir(parents=True)
    image_dir.mkdir(parents=True)

    model = YOLO(args.model)
    names = model.names
    min_conf = min(args.class_conf)
    kept_total = 0
    raw_total = 0

    for result in model.predict(
        source=args.source,
        imgsz=args.imgsz,
        conf=min_conf,
        iou=args.iou,
        device=args.device,
        stream=True,
        save=False,
        verbose=False,
    ):
        stem = Path(result.path).stem
        image = result.orig_img.copy()
        height, width = image.shape[:2]
        lines: list[str] = []

        if result.boxes is not None:
            raw_total += len(result.boxes)
            xyxy_boxes = result.boxes.xyxy.cpu().tolist()
            class_ids = result.boxes.cls.int().cpu().tolist()
            confidences = result.boxes.conf.cpu().tolist()
            for xyxy, class_id, confidence in zip(xyxy_boxes, class_ids, confidences):
                if class_id >= len(args.class_conf):
                    raise ValueError(
                        f"Model returned class ID {class_id}, but only {len(args.class_conf)} class thresholds were supplied."
                    )
                if confidence < args.class_conf[class_id]:
                    continue

                x1, y1, x2, y2 = xyxy
                x_center = ((x1 + x2) / 2) / width
                y_center = ((y1 + y2) / 2) / height
                box_w = (x2 - x1) / width
                box_h = (y2 - y1) / height
                lines.append(
                    f"{class_id} {x_center:.6f} {y_center:.6f} {box_w:.6f} {box_h:.6f} {confidence:.6f}"
                )
                class_name = names[class_id]
                draw_box(
                    image,
                    xyxy,
                    f"{class_name} {confidence:.2f}",
                    COLORS[class_id % len(COLORS)],
                )
                kept_total += 1

        # Write an empty TXT too, so every validation image has an explicit counterpart.
        (label_dir / f"{stem}.txt").write_text("\n".join(lines), encoding="utf-8")
        cv2.imwrite(str(image_dir / Path(result.path).name), image)

    print("\n=== Class-specific threshold prediction completed ===")
    print(f"Raw predictions at conf>={min_conf:.2f}: {raw_total}")
    print(f"Predictions after class-specific filtering: {kept_total}")
    print(f"Labels: {label_dir}")
    print(f"Images: {image_dir}")
    print("Class thresholds:")
    for class_id, threshold in enumerate(args.class_conf):
        class_name = names.get(class_id, str(class_id)) if isinstance(names, dict) else names[class_id]
        print(f"  {class_id}: {class_name} -> {threshold:.2f}")


if __name__ == "__main__":
    main()
