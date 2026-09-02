"""Run a YOLO26 model at 2048 resolution with multiple confidence thresholds.

This is for deployment-threshold selection and visual error analysis. It does
not retrain the model and does not replace mAP evaluation.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


DEFAULT_MODEL = (
    "/home/featurize/work/yolo26_1/ultralytics/runs/detect/runs_668/"
    "stage8_yolo26m_imgsz2048_lr2e4_mosaic010_v1/weights/best.pt"
)
DEFAULT_SOURCE = "/home/featurize/data/yolo_dataset/images/val"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Save 2048-pixel predictions for a set of confidence thresholds."
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Path to best.pt")
    parser.add_argument(
        "--source",
        default=DEFAULT_SOURCE,
        help="Image file, directory, video, or glob accepted by Ultralytics.",
    )
    parser.add_argument(
        "--conf",
        type=float,
        nargs="+",
        default=[0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
        help="Confidence thresholds to compare.",
    )
    parser.add_argument("--imgsz", type=int, default=2048)
    parser.add_argument("--device", default="0")
    parser.add_argument("--project", default="runs_668_threshold")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = YOLO(args.model)

    for conf in args.conf:
        if not 0.0 <= conf <= 1.0:
            raise ValueError(f"Confidence threshold must be in [0, 1], got {conf}")

        run_name = f"imgsz{args.imgsz}_conf{conf:.2f}".replace(".", "p")
        print(f"\nRunning conf={conf:.2f}; saving to {Path(args.project) / run_name}")
        model.predict(
            source=args.source,
            imgsz=args.imgsz,
            conf=conf,
            device=args.device,
            save=True,
            save_txt=True,
            save_conf=True,
            project=args.project,
            name=run_name,
            exist_ok=False,
            verbose=False,
        )


if __name__ == "__main__":
    main()
