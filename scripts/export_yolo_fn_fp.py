"""将 YOLO 预测与标注匹配，导出漏检(FN)和误检(FP)图片、标签及诊断 CSV。

示例：
python export_yolo_fn_fp.py \
  --images /home/featurize/data/yolo_dataset/images/val \
  --gt-labels /home/featurize/data/yolo_dataset/labels/val \
  --pred-labels runs_668_postprocess/class_conf_c30_s15_sp30_st25_iou050/labels \
  --output runs_668_error_analysis/class_thresholds_iou050

预测标签须为 ``class x_center y_center width height confidence``，可由
predict_yolo_class_thresholds.py 生成。此脚本不会修改模型或原始数据。
"""

from __future__ import annotations

import argparse
import csv
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import cv2


CLASS_NAMES = ["chipping", "scratch", "splash", "spot"]
IMAGE_SUFFIXES = (".bmp", ".png", ".jpg", ".jpeg", ".tif", ".tiff")


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
        return self.x - self.w / 2, self.y - self.h / 2, self.x + self.w / 2, self.y + self.h / 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="导出 YOLO 的 FN/FP 错误样本。")
    parser.add_argument("--images", type=Path, required=True, help="验证集图片目录")
    parser.add_argument("--gt-labels", type=Path, required=True, help="真实标注 TXT 目录")
    parser.add_argument("--pred-labels", type=Path, required=True, help="预测 TXT 目录")
    parser.add_argument("--output", type=Path, required=True, help="错误样本输出目录")
    parser.add_argument("--iou", type=float, default=0.50, help="TP 匹配 IoU 阈值")
    parser.add_argument("--partial-iou", type=float, default=0.10, help="诊断定位偏差的最低重叠 IoU")
    return parser.parse_args()


def read_boxes(path: Path, prediction: bool) -> list[Box]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        values = line.split()
        if len(values) < 5:
            continue
        cls = int(float(values[0]))
        coords = list(map(float, values[1:]))
        if prediction:
            result.append(Box(cls, *coords[:4], coords[4] if len(coords) > 4 else 1.0))
        elif len(coords) == 4:
            result.append(Box(cls, *coords))
        else:  # 兼容分割多边形标注：使用其外接框。
            xs, ys = coords[0::2], coords[1::2]
            x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
            result.append(Box(cls, (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1))
    return result


def iou(a: Box, b: Box) -> float:
    ax1, ay1, ax2, ay2 = a.corners
    bx1, by1, bx2, by2 = b.corners
    inter = max(0.0, min(ax2, bx2) - max(ax1, bx1)) * max(0.0, min(ay2, by2) - max(ay1, by1))
    union = a.w * a.h + b.w * b.h - inter
    return inter / union if union else 0.0


def match_same_class(gts: list[Box], preds: list[Box], threshold: float) -> tuple[set[int], set[int]]:
    """按置信度贪心匹配同类框，返回已匹配 GT / 预测的索引。"""
    matched_gt, matched_pred = set(), set()
    for pred_index in sorted(range(len(preds)), key=lambda i: preds[i].conf, reverse=True):
        pred = preds[pred_index]
        candidates = [
            (iou(pred, gt), gt_index)
            for gt_index, gt in enumerate(gts)
            if gt_index not in matched_gt and gt.cls == pred.cls
        ]
        best_iou, best_index = max(candidates, default=(0.0, -1))
        if best_iou >= threshold:
            matched_gt.add(best_index)
            matched_pred.add(pred_index)
    return matched_gt, matched_pred


def best_match(box: Box, candidates: list[Box]) -> tuple[float, int]:
    return max(((iou(box, item), index) for index, item in enumerate(candidates)), default=(0.0, -1))


def find_image(image_dir: Path, stem: str) -> Path | None:
    for suffix in IMAGE_SUFFIXES:
        candidate = image_dir / f"{stem}{suffix}"
        if candidate.exists():
            return candidate
    return None


def draw(image, box: Box, label: str, color: tuple[int, int, int]) -> None:
    height, width = image.shape[:2]
    x1, y1, x2, y2 = box.corners
    x1, y1 = int(x1 * width), int(y1 * height)
    x2, y2 = int(x2 * width), int(y2 * height)
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
    cv2.putText(image, label, (x1, max(20, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)


def save_case(
    image_path: Path,
    gt_path: Path,
    pred_path: Path,
    output: Path,
    kind: str,
    class_name: str,
    index: int,
    focus: Box,
    all_gts: list[Box],
    all_preds: list[Box],
) -> Path:
    case_dir = output / kind / class_name
    image_dir, gt_dir, pred_dir = case_dir / "images", case_dir / "gt_labels", case_dir / "pred_labels"
    image_dir.mkdir(parents=True, exist_ok=True)
    gt_dir.mkdir(exist_ok=True)
    pred_dir.mkdir(exist_ok=True)

    image = cv2.imread(str(image_path))
    if image is None:
        raise RuntimeError(f"Cannot read image: {image_path}")
    for gt in all_gts:
        draw(image, gt, f"GT {CLASS_NAMES[gt.cls]}", (0, 220, 0))
    for pred in all_preds:
        draw(image, pred, f"Pred {CLASS_NAMES[pred.cls]} {pred.conf:.2f}", (0, 180, 255))
    draw(image, focus, f"{kind.upper()} {class_name}", (0, 0, 255))

    stem = f"{image_path.stem}__{kind}__{class_name}__{index:02d}"
    destination = image_dir / f"{stem}{image_path.suffix}"
    cv2.imwrite(str(destination), image)
    shutil.copy2(gt_path, gt_dir / f"{stem}.txt")
    if pred_path.exists():
        shutil.copy2(pred_path, pred_dir / f"{stem}.txt")
    else:
        (pred_dir / f"{stem}.txt").write_text("", encoding="utf-8")
    return destination


def main() -> None:
    args = parse_args()
    for folder in (args.images, args.gt_labels, args.pred_labels):
        if not folder.is_dir():
            raise FileNotFoundError(f"Directory not found: {folder}")
    if not 0 < args.partial_iou < args.iou <= 1:
        raise ValueError("Require 0 < --partial-iou < --iou <= 1.")
    if args.output.exists():
        raise FileExistsError(f"Output already exists: {args.output}; please choose a new directory.")

    rows: list[dict[str, object]] = []
    counts: dict[int, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    gt_files = sorted(args.gt_labels.glob("*.txt"))
    for gt_path in gt_files:
        stem = gt_path.stem
        image_path = find_image(args.images, stem)
        if image_path is None:
            print(f"Warning: image not found for {gt_path.name}; skipped")
            continue
        pred_path = args.pred_labels / gt_path.name
        gts, preds = read_boxes(gt_path, False), read_boxes(pred_path, True)
        matched_gt, matched_pred = match_same_class(gts, preds, args.iou)

        for class_id in range(len(CLASS_NAMES)):
            counts[class_id]["tp"] += sum(
                index in matched_gt and box.cls == class_id for index, box in enumerate(gts)
            )
            counts[class_id]["fn"] += sum(
                index not in matched_gt and box.cls == class_id for index, box in enumerate(gts)
            )
            counts[class_id]["fp"] += sum(
                index not in matched_pred and box.cls == class_id for index, box in enumerate(preds)
            )

        # FN：未匹配真实框；通过任意类别预测的重叠情况给出初步原因。
        for gt_index, gt in enumerate(gts):
            if gt_index in matched_gt:
                continue
            overlap, pred_index = best_match(gt, preds)
            if overlap >= args.iou and preds[pred_index].cls != gt.cls:
                reason = "类别混淆（同位置预测成其他类别）"
            elif overlap >= args.partial_iou:
                reason = "定位偏差或置信度不足（存在部分重叠预测）"
            else:
                reason = "未检测到（建议检查尺度、反光、对比度或漏标）"
            image_out = save_case(image_path, gt_path, pred_path, args.output, "fn", CLASS_NAMES[gt.cls], gt_index, gt, gts, preds)
            rows.append({"kind": "FN", "image": image_path.name, "class": CLASS_NAMES[gt.cls], "reason": reason,
                         "confidence": preds[pred_index].conf if pred_index >= 0 else "", "best_iou": round(overlap, 4), "exported_image": str(image_out)})

        # FP：未匹配预测框；同样分析是否落在其他类别/部分标注上。
        for pred_index, pred in enumerate(preds):
            if pred_index in matched_pred:
                continue
            overlap, gt_index = best_match(pred, gts)
            if overlap >= args.iou and gts[gt_index].cls != pred.cls:
                reason = "类别混淆（预测类别错误）"
            elif overlap >= args.partial_iou:
                reason = "定位偏差或重复预测"
            else:
                reason = "背景误检、反光/边缘干扰，或真实缺陷漏标"
            image_out = save_case(image_path, gt_path, pred_path, args.output, "fp", CLASS_NAMES[pred.cls], pred_index, pred, gts, preds)
            rows.append({"kind": "FP", "image": image_path.name, "class": CLASS_NAMES[pred.cls], "reason": reason,
                         "confidence": round(pred.conf, 4), "best_iou": round(overlap, 4), "exported_image": str(image_out)})

    args.output.mkdir(parents=True, exist_ok=True)
    csv_path = args.output / "error_cases.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["kind", "image", "class", "reason", "confidence", "best_iou", "exported_image"])
        writer.writeheader()
        writer.writerows(rows)

    metric_rows = []
    for class_id, class_name in enumerate(CLASS_NAMES):
        tp, fp, fn = counts[class_id]["tp"], counts[class_id]["fp"], counts[class_id]["fn"]
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        metric_rows.append({"class": class_name, "tp": tp, "fp": fp, "fn": fn,
                            "precision": round(precision, 6), "recall": round(recall, 6), "f1": round(f1, 6)})
    total_tp = sum(row["tp"] for row in metric_rows)
    total_fp = sum(row["fp"] for row in metric_rows)
    total_fn = sum(row["fn"] for row in metric_rows)
    total_p = total_tp / (total_tp + total_fp) if total_tp + total_fp else 0.0
    total_r = total_tp / (total_tp + total_fn) if total_tp + total_fn else 0.0
    total_f1 = 2 * total_p * total_r / (total_p + total_r) if total_p + total_r else 0.0
    metric_rows.append({"class": "all", "tp": total_tp, "fp": total_fp, "fn": total_fn,
                        "precision": round(total_p, 6), "recall": round(total_r, 6), "f1": round(total_f1, 6)})
    metrics_path = args.output / "pr_metrics.csv"
    with metrics_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["class", "tp", "fp", "fn", "precision", "recall", "f1"])
        writer.writeheader()
        writer.writerows(metric_rows)

    fn_count = sum(row["kind"] == "FN" for row in rows)
    fp_count = sum(row["kind"] == "FP" for row in rows)
    print(f"\n完成：FN={fn_count}，FP={fp_count}")
    print(f"错误样本目录：{args.output}")
    print(f"诊断清单：{csv_path}")
    print(f"P/R 汇总表：{metrics_path}")
    print("\n各类别 P / R / F1：")
    for row in metric_rows:
        print(f"{row['class']:<10} P={row['precision']:.3f} R={row['recall']:.3f} F1={row['f1']:.3f}")


if __name__ == "__main__":
    main()
