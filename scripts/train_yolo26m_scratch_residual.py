from ultralytics import YOLO

# scratch 残差融合离线增强对照实验。
# 使用 78 张 scratch-only 合成图；不叠加在线增强，以单独评估数据合成方法。
model = YOLO("yolo26m.pt")

model.train(
    data="/home/featurize/data/yolo_dataset_scratch_residual_aug/data.yaml",

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

    # 关闭在线增强，确保本实验只评估残差融合离线数据。
    mosaic=0.0,
    close_mosaic=0,
    mixup=0.0,
    cutmix=0.0,
    copy_paste=0.0,
    hsv_h=0.0,
    hsv_s=0.0,
    hsv_v=0.0,
    degrees=0.0,
    translate=0.0,
    scale=0.0,
    shear=0.0,
    perspective=0.0,
    fliplr=0.0,
    flipud=0.0,
    erasing=0.0,

    seed=42,
    deterministic=True,

    project="runs_668",
    name="stage4_yolo26m_scratch_residual_v1",
    plots=True,
    save_period=10,
)
