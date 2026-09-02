"""Evaluate YOLO prediction label files across confidence-threshold runs.

The script compares Ultralytics prediction TXT files (written with
``save_txt=True, save_conf=True``) against YOLO ground-truth label TXT files.
It exports per-threshold and per-class TP/FP/FN, Precision, Recall and F1.

Example
-------
python scripts/analyze_yolo_thresholds.py \
  --runs-root runs_668_threshold \
  --gt-labels /home/featurize/data/yolo_dataset/labels/val \
  --output runs_668_threshold/threshold_metrics

Expected directory layout (created by predict_yolo26_2048_thresholds.py):
    runs-root/
      imgsz2048_conf0p05/labels/*.txt
      imgsz2048_conf0p10/labels/*.txt
      ...

Important: this is a deployment-threshold analysis. It does not change mAP.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_NAMES = ["chipping", "scratch", "splash", "spot"]


@dataclass(frozen=True)
class Box:
    cls: int
    x: float
    y: float
    w: float
    h: float
    conf: float = 1.0

    @property
    def corners(self) -> tuple[float, float, float, float]:
        return (
            self.x - self.w / 2,
            self.y - self.h / 2,
            self.x + self.w / 2,
            self.y + self.h / 2,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate TP/FP/FN, P/R/F1 for YOLO confidence-threshold runs."
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        required=True,
        help="Folder containing imgsz2048_conf0pXX run folders.",
    )
    parser.add_argument(
        "--gt-labels",
        type=Path,
        required=True,
        help="YOLO ground-truth validation labels folder, for example labels/val.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("threshold_metrics"),
        help="Directory for CSV outputs (default: threshold_metrics).",
    )
    parser.add_argument("--iou", type=float, default=0.50, help="Match IoU threshold.")
    parser.add_argument(
        "--names",
        nargs="+",
        default=DEFAULT_NAMES,
        help="Class names in numeric YOLO label order.",
    )
    parser.add_argument(
        "--include-empty-runs",
        action="store_true",
        help="Keep runs without a labels directory instead of reporting them as errors.",
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help=(
            "Export per-ground-truth matching diagnostics. Use when TP is unexpectedly zero "
            "to distinguish filename, class-order, and coordinate-format issues."
        ),
    )
    return parser.parse_args()


def polygon_to_box(cls: int, coordinates: list[float], conf: float = 1.0) -> Box:
    """Convert normalized YOLO polygon points to its enclosing normalized box."""
    if len(coordinates) < 6 or len(coordinates) % 2:
        raise ValueError("A segmentation polygon needs at least three x/y point pairs.")
    xs = coordinates[0::2]
    ys = coordinates[1::2]
    x1, x2 = min(xs), max(xs)
    y1, y2 = min(ys), max(ys)
    return Box(cls, (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1, conf)


def read_boxes(path: Path, prediction: bool) -> list[Box]:
    """Read detection boxes or segmentation polygons from one YOLO TXT file.

    Ground-truth files produced from Labelme often store segmentation polygons as
    ``class x1 y1 x2 y2 ...``.  Ultralytics detection predictions, on the other
    hand, are normally ``class x_center y_center width height confidence``.
    For an IoU-based detection evaluation, a ground-truth polygon is converted
    to its enclosing bounding box.
    """
    if not path.exists() or path.stat().st_size == 0:
        return []

    boxes: list[Box] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        values = raw.split()
        if len(values) < 5:
            raise ValueError(f"{path}:{line_no} needs at least 5 fields, got: {raw!r}")
        try:
            cls = int(float(values[0]))
            numbers = list(map(float, values[1:]))
        except ValueError as exc:
            raise ValueError(f"Invalid numeric YOLO label in {path}:{line_no}: {raw!r}") from exc
        if prediction:
            # Detection predictions: class, x_center, y_center, width, height, confidence.
            x, y, w, h = numbers[:4]
            conf = numbers[4] if len(numbers) >= 5 else 1.0
            boxes.append(Box(cls, x, y, w, h, conf))
        elif len(numbers) == 4:
            # Detection ground truth: class, x_center, y_center, width, height.
            x, y, w, h = numbers
            boxes.append(Box(cls, x, y, w, h))
        elif len(numbers) >= 6 and len(numbers) % 2 == 0:
            # Segmentation ground truth: class, x1, y1, x2, y2, ...
            boxes.append(polygon_to_box(cls, numbers))
        else:
            raise ValueError(
                f"Unsupported ground-truth format in {path}:{line_no}. "
                "Expected YOLO box (5 fields total) or polygon (1 + an even number of coordinates)."
            )
    return boxes


def iou(a: Box, b: Box) -> float:
    ax1, ay1, ax2, ay2 = a.corners
    bx1, by1, bx2, by2 = b.corners
    inter_w = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    inter_h = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = inter_w * inter_h
    union = a.w * a.h + b.w * b.h - inter
    return inter / union if union > 0 else 0.0


def match_one_class(preds: list[Box], gts: list[Box], iou_threshold: float) -> tuple[int, int, int]:
    """Greedily match high-confidence predictions to one ground truth at most once."""
    matched_gt: set[int] = set()
    tp = 0
    fp = 0
    for pred in sorted(preds, key=lambda item: item.conf, reverse=True):
        candidates = [
            (iou(pred, gt), index)
            for index, gt in enumerate(gts)
            if index not in matched_gt
        ]
        best_iou, best_index = max(candidates, default=(0.0, -1))
        if best_iou >= iou_threshold:
            tp += 1
            matched_gt.add(best_index)
        else:
            fp += 1
    return tp, fp, len(gts) - tp


def safe_div(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def metrics(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    f1 = safe_div(2 * precision * recall, precision + recall)
    return precision, recall, f1


def highest_iou(reference: Box, candidates: list[Box]) -> float:
    """Best IoU for one GT box against a list of prediction boxes."""
    return max((iou(reference, candidate) for candidate in candidates), default=0.0)


def threshold_from_name(path: Path) -> float:
    match = re.search(r"conf(\d+)p(\d+)", path.name)
    if not match:
        return float("inf")
    return float(f"{match.group(1)}.{match.group(2)}")


def list_runs(root: Path) -> list[Path]:
    """Return only actual prediction runs, never CSV/metric output directories."""
    return sorted(
        [
            path
            for path in root.iterdir()
            if path.is_dir() and "conf" in path.name and (path / "labels").is_dir()
        ],
        key=threshold_from_name,
    )


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    if not 0 < args.iou <= 1:
        raise ValueError("--iou must be in (0, 1].")
    if not args.runs_root.is_dir():
        raise FileNotFoundError(f"Runs root not found: {args.runs_root}")
    if not args.gt_labels.is_dir():
        raise FileNotFoundError(f"Ground-truth labels folder not found: {args.gt_labels}")

    run_dirs = list_runs(args.runs_root)
    if not run_dirs:
        raise FileNotFoundError(
            f"No threshold-run folders containing 'conf' found under: {args.runs_root}"
        )

    gt_files = sorted(args.gt_labels.glob("*.txt"))
    if not gt_files:
        raise FileNotFoundError(f"No ground-truth TXT labels found in: {args.gt_labels}")

    args.output.mkdir(parents=True, exist_ok=True)
    per_class_rows: list[dict[str, object]] = []
    overall_rows: list[dict[str, object]] = []
    diagnostic_rows: list[dict[str, object]] = []

    for run_dir in run_dirs:
        pred_dir = run_dir / "labels"
        if not pred_dir.is_dir():
            message = f"Prediction labels folder missing: {pred_dir}"
            if args.include_empty_runs:
                print(f"Warning: {message}; treating all predictions as empty.")
            else:
                raise FileNotFoundError(
                    message + "\nRe-run prediction with save_txt=True and save_conf=True."
                )

        counts: dict[int, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
        for gt_path in gt_files:
            gt_boxes = read_boxes(gt_path, prediction=False)
            pred_path = pred_dir / gt_path.name
            pred_boxes = read_boxes(pred_path, prediction=True) if pred_dir.is_dir() else []

            if args.diagnose:
                for index, gt in enumerate(gt_boxes):
                    same_class = [box for box in pred_boxes if box.cls == gt.cls]
                    diagnostic_rows.append(
                        {
                            "run": run_dir.name,
                            "threshold": threshold_from_name(run_dir),
                            "label_file": gt_path.name,
                            "prediction_file_found": pred_path.exists(),
                            "gt_index": index,
                            "gt_class_id": gt.cls,
                            "gt_class_name": (
                                args.names[gt.cls] if 0 <= gt.cls < len(args.names) else f"unknown_{gt.cls}"
                            ),
                            "prediction_count_in_image": len(pred_boxes),
                            "same_class_prediction_count": len(same_class),
                            "best_iou_same_class": round(highest_iou(gt, same_class), 6),
                            "best_iou_any_class": round(highest_iou(gt, pred_boxes), 6),
                        }
                    )

            for class_id in range(len(args.names)):
                gt_class = [box for box in gt_boxes if box.cls == class_id]
                pred_class = [box for box in pred_boxes if box.cls == class_id]
                tp, fp, fn = match_one_class(pred_class, gt_class, args.iou)
                counts[class_id]["tp"] += tp
                counts[class_id]["fp"] += fp
                counts[class_id]["fn"] += fn

        threshold = threshold_from_name(run_dir)
        total_tp = total_fp = total_fn = 0
        for class_id, class_name in enumerate(args.names):
            tp, fp, fn = counts[class_id].values()
            precision, recall, f1 = metrics(tp, fp, fn)
            per_class_rows.append(
                {
                    "run": run_dir.name,
                    "threshold": threshold,
                    "class_id": class_id,
                    "class_name": class_name,
                    "tp": tp,
                    "fp": fp,
                    "fn": fn,
                    "precision": round(precision, 6),
                    "recall": round(recall, 6),
                    "f1": round(f1, 6),
                }
            )
            total_tp += tp
            total_fp += fp
            total_fn += fn

        precision, recall, f1 = metrics(total_tp, total_fp, total_fn)
        overall_rows.append(
            {
                "run": run_dir.name,
                "threshold": threshold,
                "iou": args.iou,
                "tp": total_tp,
                "fp": total_fp,
                "fn": total_fn,
                "precision": round(precision, 6),
                "recall": round(recall, 6),
                "f1": round(f1, 6),
            }
        )

    overall_rows.sort(key=lambda row: float(row["threshold"]))
    per_class_rows.sort(key=lambda row: (float(row["threshold"]), int(row["class_id"])))
    write_csv(
        args.output / "threshold_overall.csv",
        overall_rows,
        ["run", "threshold", "iou", "tp", "fp", "fn", "precision", "recall", "f1"],
    )
    write_csv(
        args.output / "threshold_per_class.csv",
        per_class_rows,
        [
            "run", "threshold", "class_id", "class_name", "tp", "fp", "fn",
            "precision", "recall", "f1",
        ],
    )
    if args.diagnose:
        write_csv(
            args.output / "matching_diagnostics.csv",
            diagnostic_rows,
            [
                "run", "threshold", "label_file", "prediction_file_found", "gt_index",
                "gt_class_id", "gt_class_name", "prediction_count_in_image",
                "same_class_prediction_count", "best_iou_same_class", "best_iou_any_class",
            ],
        )

    print("\n=== Overall results by run ===")
    for row in sorted(overall_rows, key=lambda item: str(item["run"])):
        print(
            f"{str(row['run']):44s}  P={float(row['precision']):.3f}  "
            f"R={float(row['recall']):.3f}  F1={float(row['f1']):.3f}  "
            f"TP/FP/FN={row['tp']}/{row['fp']}/{row['fn']}"
        )

    best = max(overall_rows, key=lambda row: float(row["f1"]))
    print("\n=== Overall best F1 ===")
    print(
        f"threshold={best['threshold']:.2f}  P={best['precision']:.3f}  "
        f"R={best['recall']:.3f}  F1={best['f1']:.3f}  "
        f"TP/FP/FN={best['tp']}/{best['fp']}/{best['fn']}"
    )
    print(f"\nSaved: {args.output / 'threshold_overall.csv'}")
    print(f"Saved: {args.output / 'threshold_per_class.csv'}")
    if args.diagnose:
        found_ratio = safe_div(
            sum(bool(row["prediction_file_found"]) for row in diagnostic_rows),
            len(diagnostic_rows),
        )
        any_iou50 = safe_div(
            sum(float(row["best_iou_any_class"]) >= args.iou for row in diagnostic_rows),
            len(diagnostic_rows),
        )
        same_iou50 = safe_div(
            sum(float(row["best_iou_same_class"]) >= args.iou for row in diagnostic_rows),
            len(diagnostic_rows),
        )
        print(f"Saved: {args.output / 'matching_diagnostics.csv'}")
        print("\n=== Diagnosis across all threshold runs ===")
        print(f"Prediction filename found ratio: {found_ratio:.3f}")
        print(f"Any-class best IoU >= {args.iou:.2f}: {any_iou50:.3f}")
        print(f"Same-class best IoU >= {args.iou:.2f}: {same_iou50:.3f}")
    print("\nPer-class best F1:")
    for class_name in args.names:
        rows = [row for row in per_class_rows if row["class_name"] == class_name]
        best_row = max(rows, key=lambda row: float(row["f1"]))
        print(
            f"  {class_name:10s} conf={best_row['threshold']:.2f}  "
            f"P={best_row['precision']:.3f} R={best_row['recall']:.3f} "
            f"F1={best_row['f1']:.3f}"
        )


if __name__ == "__main__":
    main()
