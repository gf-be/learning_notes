from ultralytics import YOLO

# 轻量在线增强检测实验：使用原始数据集，不使用离线增强数据集。
model = YOLO("yolo26m.pt")

model.train(
    data="/home/featurize/data/yolo_dataset/data.yaml",

    epochs=150,
    patience=80,
    imgsz=1280,
    batch=8,
    device=0,
    workers=4,
    cache=False,
    amp=True,

    optimizer="AdamW",
    lr0=0.0003,
    lrf=0.02,
    cos_lr=True,
    warmup_epochs=5,
    weight_decay=0.0005,

    # 轻量在线增强：适配固定拍摄视角与圆形工件。
    mosaic=0.0,
    close_mosaic=0,
    mixup=0.0,
    cutmix=0.0,
    copy_paste=0.0,
    hsv_h=0.0,
    hsv_s=0.0,
    hsv_v=0.08,
    degrees=2.0,
    translate=0.03,
    scale=0.10,
    shear=0.0,
    perspective=0.0,
    fliplr=0.5,
    flipud=0.0,
    erasing=0.0,

    seed=42,
    deterministic=True,

    project="runs_668",
    name="stage3_yolo26m_online_lightaug_v1",
    plots=True,
    save_period=10,
)
