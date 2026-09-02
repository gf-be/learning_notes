"""用当前 best.pt 在训练集上评估四类瑕疵的 P、R。

运行前只需确认 MODEL_PATH 指向当前最优权重；其余参数应与该权重训练时一致。
"""

from ultralytics import YOLO


# ===== 只需要修改这里：改为你当前最优 best.pt 的实际路径 =====
MODEL_PATH = (
    "/home/featurize/work/yolo26_1/ultralytics/runs/detect/"
    "runs_668/stage8_yolo26m_imgsz2048_lr1e4_mosaic010_v1/weights/best.pt"
)

# 数据集配置与训练时保持一致
DATA_PATH = "/home/featurize/data/yolo_dataset/data.yaml"


model = YOLO(MODEL_PATH)

# split="train"：只改变评估数据划分，不会重新训练，也不会修改权重。
metrics = model.val(
    data=DATA_PATH,
    split="train",
    imgsz=2048,
    batch=2,
    device=0,
    workers=4,
    plots=True,
    project="runs_668_eval",
    name="bestpt_train_eval_2048",
)

print("\n===== best.pt 在训练集上的评估结果 =====")
print(f"总体 Precision: {metrics.box.mp:.4f}")
print(f"总体 Recall:    {metrics.box.mr:.4f}")
print(f"总体 mAP50:     {metrics.box.map50:.4f}")
print(f"总体 mAP50-95:  {metrics.box.map:.4f}")

print("\n===== 各类别 P / R =====")
for class_id, class_name in metrics.names.items():
    precision, recall, map50, map50_95 = metrics.box.class_result(class_id)
    print(
        f"{class_id}: {class_name:<10} "
        f"P={precision:.4f}, R={recall:.4f}, "
        f"mAP50={map50:.4f}, mAP50-95={map50_95:.4f}"
    )

print(f"\n结果图保存至: {metrics.save_dir}")
