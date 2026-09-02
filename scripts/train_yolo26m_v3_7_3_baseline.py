"""YOLO26m 基准训练：新 7:3 划分上的高分辨率可比基线。

本配置用于后续“物理变化模拟扩增”对照：本轮只使用原始重划分数据，
不加入新的位置偏移、模糊、照明等增强。保留此前验证较稳定的轻 Mosaic，
使其与历史 2048 最优候选具有可比性。

运行：
    python train_yolo26m_v3_7_3_baseline.py
"""

from ultralytics import YOLO


# 使用官方 YOLO26m 预训练权重；不要改为师兄的自定义模型，避免混淆模型结构对比。
model = YOLO("yolo26m.pt")

model.train(
    # 新 7:3 图像级分层划分：train=465，val=200；scratch 验证实例=31。
    data="/home/featurize/data/yolo_dataset_v3_7_3/data.yaml",

    # 师兄配置中保留“足够长上限 + 耐心早停”；实际训练以 best.pt 为准。
    epochs=200,
    patience=100,

    # 你的高分辨率验证结果表明：2048 有利于细小/细长瑕疵定位。
    imgsz=2048,
    batch=2,          # RTX 4090 上 YOLO26m 2048 的已验证安全批量
    device=0,
    workers=4,
    cache=False,
    amp=True,

    # 使用你在 YOLO26m 上已验证更合适的 AdamW；不直接采用师兄 SGD 的 lr0=0.01。
    optimizer="AdamW",
    lr0=0.0001,
    lrf=0.01,
    cos_lr=True,
    warmup_epochs=5,
    weight_decay=0.0005,

    # 仅保留历史有效的轻 Mosaic；本轮不叠加任何新的物理模拟增强。
    mosaic=0.10,
    close_mosaic=15,
    mixup=0.0,
    cutmix=0.0,
    copy_paste=0.0,
    hsv_h=0.0,
    hsv_s=0.0,
    hsv_v=0.02,
    degrees=0.0,
    translate=0.0,
    scale=0.0,
    shear=0.0,
    perspective=0.0,
    fliplr=0.0,
    flipud=0.0,
    erasing=0.0,

    # 与数据划分和后续增强实验使用同一随机种子，保证可复现。
    seed=42,
    deterministic=True,

    project="runs_668_v3",
    name="baseline_yolo26m_2048_adamw_lr1e4_mosaic010",
    save=True,
    save_period=20,
    plots=True,
)
