"""验证 YOLO 检测模型，并导出总体及各类别 P、R、F1 指标。

示例：
python validate_yolo.py \
  --model /home/featurize/work/yolo26_1/ultralytics/runs/detect/runs_668/stage8_yolo26m_imgsz2048_lr2e4_mosaic010_v1/weights/best.pt \
  --data /home/featurize/data/yolo_dataset/data.yaml \
  --split val --imgsz 2048 --batch 2 \
  --project runs_668_eval --name adamw_2048_val

若要判断模型是否过拟合，将 --split val 改为 --split train，
其余参数（尤其是权重、imgsz）保持完全一致后再次运行。
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="验证 YOLO 权重并导出按类别统计的 P/R/F1。")
    parser.add_argument("--model", required=True, help="待验证的 best.pt 权重路径")
    parser.add_argument("--data", required=True, help="data.yaml 路径")
    parser.add_argument(
        "--split",
        choices=("train", "val", "test"),
        default="val",
        help="验证数据划分；默认 val",
    )
    parser.add_argument("--imgsz", type=int, default=2048, help="验证图像尺寸")
    parser.add_argument("--batch", type=int, default=2, help="验证 batch size")
    parser.add_argument("--device", default="0", help="GPU 编号，例如 0；CPU 用 cpu")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--project", default="runs_668_eval", help="结果根目录")
    parser.add_argument("--name", default=None, help="本次结果子目录名")
    return parser.parse_args()


def write_summary(metrics, split: str) -> Path:
    """把 Ultralytics 的 box 指标输出为易于汇报的 CSV。"""
    save_dir = Path(metrics.save_dir)
    output_file = save_dir / "pr_metrics_summary.csv"

    # class_result(i) 的顺序为 P、R、mAP50、mAP50-95。
    rows = []
    for class_id in range(len(metrics.box.p)):
        precision, recall, map50, map50_95 = metrics.box.class_result(class_id)
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        rows.append(
            {
                "split": split,
                "class_id": class_id,
                "class_name": metrics.names[class_id],
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "map50": map50,
                "map50_95": map50_95,
            }
        )

    overall_p = float(metrics.box.mp)
    overall_r = float(metrics.box.mr)
    overall_f1 = 2 * overall_p * overall_r / (overall_p + overall_r) if overall_p + overall_r else 0.0
    rows.append(
        {
            "split": split,
            "class_id": "all",
            "class_name": "all",
            "precision": overall_p,
            "recall": overall_r,
            "f1": overall_f1,
            "map50": float(metrics.box.map50),
            "map50_95": float(metrics.box.map),
        }
    )

    with output_file.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    return output_file


def main() -> None:
    args = parse_args()
    model = YOLO(args.model)

    # 不指定 conf：保持 Ultralytics 的标准评估逻辑，结果可与训练日志直接对比。
    metrics = model.val(
        data=args.data,
        split=args.split,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        project=args.project,
        name=args.name,
        plots=True,
        save_json=False,
    )

    summary_file = write_summary(metrics, args.split)
    print(f"\n验证划分: {args.split}")
    print(f"结果目录: {metrics.save_dir}")
    print(f"P/R 汇总表: {summary_file}")


if __name__ == "__main__":
    main()
