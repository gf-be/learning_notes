# YOLO26 瑕疵检测半监督实验日志

## 1. 实验目标

本项目目标是基于 YOLO26 或后续分割模型，完成工业瑕疵检测实验，并逐步探索半监督学习方案，最终希望将检测任务的 `mAP50` 提升至 `0.90` 左右。

当前阶段为第一阶段：建立纯监督基线，分析当前数据集和模型的主要瓶颈，为后续数据增强、半监督伪标签和物理补采实验提供依据。

## 2. 数据集情况

原始数据集中包含图片及对应 YOLO 格式标注文件：

- 图片格式：`.png`
- 标注格式：`.txt`
- 标注格式示例：`class x_center y_center width height`
- 总样本数：807 张图片
- 瑕疵类别数：3 类

类别名称如下：

| 类别编号 | 类别名称 |
|---:|---|
| 0 | splash |
| 1 | scratch |
| 2 | chipping |

## 3. 数据集重新划分

将原始训练集和验证集合并后，重新按照 `7:2:1` 划分为训练集、验证集、测试集。

| 数据集 | 图片数 | 标注文件数 |
|---|---:|---:|
| train | 565 | 565 |
| val | 161 | 161 |
| test | 81 | 81 |

划分后已检查：

- 每张 `.png` 图片均有同名 `.txt` 标注文件。
- 图片和标注文件一一对应。
- 根目录下无散落图片或标注文件。

## 4. 类别分布统计

### 4.1 目标框数量

| 数据集 | splash | scratch | chipping | 空标注图 |
|---|---:|---:|---:|---:|
| train | 2815 | 364 | 390 | 51 |
| val | 835 | 169 | 117 | 17 |
| test | 394 | 52 | 71 | 4 |
| total | 4044 | 585 | 578 | 72 |

### 4.2 包含该类别的图片数量

| 类别 | 总图片数 | train | val | test |
|---|---:|---:|---:|---:|
| splash | 630 | 447 | 122 | 61 |
| scratch | 207 | 138 | 46 | 23 |
| chipping | 396 | 267 | 85 | 44 |

### 4.3 初步判断

当前数据集具备半监督实验基础，但类别分布不均衡明显：

- `splash` 样本最多，目标框约占总框数的 77.66%。
- `scratch` 和 `chipping` 属于相对少数类。
- `scratch` 的检测难度较高，是当前最主要瓶颈。
- 当前所有图片都有标注文件，后续半监督实验可以先通过隐藏部分训练集标签模拟未标注数据，也可以继续补采真实未标注图片。

## 5. 第一阶段：YOLO26 三尺度纯监督基线

### 5.1 训练设置

第一阶段训练 `YOLO26n / YOLO26s / YOLO26m` 三个尺度，保持数据、输入尺寸、训练轮数和主要超参数一致，用于判断模型容量对当前任务的影响。

基础配置如下：

```python
from ultralytics import YOLO

model = YOLO("yolo26m.pt")

model.train(
    data="/home/featurize/data/split_aug/data.yaml",
    epochs=150,
    imgsz=1280,
    batch=16,
    device=0,

    optimizer="AdamW",
    lr0=0.0005,
    lrf=0.05,
    cos_lr=True,
    warmup_epochs=5,

    mosaic=0.0,
    mixup=0.0,
    hsv_h=0.0,
    hsv_s=0.0,
    hsv_v=0.03,

    seed=42,
    deterministic=True,
    project="runs_defect",
    name="stage1_yolo26m_baseline",
    plots=True,
    patience=50,
)
```


### 5.2 三尺度实验结果

| 模型 | Precision | Recall | mAP50 | mAP50-95 | splash AP50 | scratch AP50 | chipping AP50 |
|---|---:|---:|---:|---:|---:|---:|---:|
| YOLO26n | 0.614 | 0.545 | 0.555 | 0.309 | 0.656 | 0.235 | 0.774 |
| YOLO26s | 0.678 | 0.580 | 0.595 | 0.334 | 0.715 | 0.267 | 0.803 |
| YOLO26m | 0.661 | 0.592 | 0.617 | 0.352 | 0.727 | 0.300 | 0.824 |

### 5.3 结果分析

从 `YOLO26n -> YOLO26s -> YOLO26m`，整体 mAP50 有稳定提升：

- YOLO26n 到 YOLO26s：`+0.040`
- YOLO26s 到 YOLO26m：`+0.022`

说明模型容量对当前任务有帮助，但提升幅度有限。当前主要瓶颈不是单纯模型过小，而是：

- `scratch` 类别检测效果明显偏低。
- 整体 Recall 偏低，漏检较多。
- `mAP50-95` 偏低，说明定位质量仍不稳定。
- 类别分布不均衡，`splash` 占比过高。

当前最优基线为：

```text
YOLO26m
mAP50 = 0.617
mAP50-95 = 0.352
```

## 6. YOLO26m 错误分析

### 6.1 混淆矩阵分析

YOLO26m 的混淆矩阵显示，主要问题不是类别之间互相混淆，而是大量目标被漏检为 background。

| 真实类别 | 正确检出 | 漏检为 background | 主要问题 |
|---|---:|---:|---|
| splash | 633 | 198 | 漏检较多，同时有背景误检为 splash |
| scratch | 60 | 107 | 漏检非常严重 |
| chipping | 93 | 23 | 表现最好 |

背景误检情况：

| 预测类别 | 背景被误检数量 |
|---|---:|
| splash | 305 |
| scratch | 78 |
| chipping | 27 |

结论：

- `scratch` 的主要问题是检不出来，而不是和其他类别混淆。
- `splash` 同时存在漏检和误检。
- `chipping` 是当前最稳定类别，已经接近可用水平。

### 6.2 F1 和 Recall 曲线分析

F1 曲线显示，全部类别的最佳 F1 约为：

```text
F1 = 0.62 at confidence = 0.340
```

Recall 曲线显示，在较低置信度下整体召回更高。当前阶段不建议推理时使用过高置信度阈值。

建议：

```python
conf=0.25
```

如果主要用于排查漏检，可以临时使用：

```python
conf=0.15
```

## 7. 第二阶段计划：召回率增强实验

根据第一阶段结果，第二阶段优先目标不是直接做半监督，而是先提升 `scratch` 和整体 Recall。

推荐实验名称：

```text
stage2_yolo26m_recall_aug_v1
```

推荐配置：

```python
from ultralytics import YOLO

model = YOLO("yolo26m.pt")

model.train(
    data="/home/featurize/data/split_aug/data.yaml",
    epochs=220,
    imgsz=1280,
    batch=8,
    device=0,
    workers=0,
    cache=False,

    optimizer="AdamW",
    lr0=0.0003,
    lrf=0.02,
    cos_lr=True,
    warmup_epochs=5,

    mosaic=0.25,
    close_mosaic=40,
    mixup=0.0,
    cutmix=0.0,

    hsv_h=0.0,
    hsv_s=0.04,
    hsv_v=0.10,

    fliplr=0.5,
    flipud=0.0,
    degrees=3,
    translate=0.06,
    scale=0.25,
    shear=0.0,
    perspective=0.0,

    seed=42,
    deterministic=True,
    project="runs_defect",
    name="stage2_yolo26m_recall_aug_v1",
    plots=True,
    patience=80,
)
```

该组实验目的：

- 使用轻量 `mosaic` 增强小目标和多目标场景。
- 使用 `close_mosaic` 保证后期训练回到真实图片分布。
- 通过轻微亮度增强提升低对比瑕疵适应能力。
- 通过缩放和平移增强目标尺度和位置变化。
- 优先观察 `scratch AP50` 和整体 Recall 是否提升。

## 8. 关于离线图片增强

YOLO26/Ultralytics 本身已经内置在线数据增强，不一定需要先做离线增强。当前建议顺序为：

1. 先做 YOLO 内置轻增强实验。
2. 如果 `scratch AP50` 明显提升，再考虑针对 `scratch` 做少量离线增强。
3. 不建议对所有类别平均离线增强，避免进一步放大 `splash` 类别优势。

### 8.1 推荐的离线增强对象

优先增强：

- `scratch`
- 少量 `chipping`

暂不建议大量增强：

- `splash`

### 8.2 推荐增强方式

| 增强方式 | 推荐强度 |
|---|---|
| 亮度变化 | ±10% |
| 对比度变化 | ±10% |
| 小角度旋转 | ±3° |
| 水平翻转 | 视物理合理性决定 |
| 轻微缩放 | 0.9-1.1 |
| 轻微高斯噪声 | 少量 |

不建议：

- 大角度旋转
- 强颜色扰动
- 强模糊
- 随机裁剪
- 过强 MixUp
- 过强 Mosaic

## 9. 半监督实验启动条件

当前最优纯监督基线 `mAP50 = 0.617`，其中 `scratch AP50 = 0.300`。此时直接使用模型生成全部伪标签风险较高，尤其是 `scratch` 伪标签质量可能不稳定。

建议半监督启动门槛：

- 总体 `mAP50 >= 0.70`
- `scratch AP50 >= 0.45`
- 或者先只对 `splash/chipping` 使用高置信度伪标签，暂缓 `scratch`

推荐半监督流程：

1. 使用当前最佳模型作为 teacher。
2. 对未标注图片或隐藏标签图片生成伪标签。
3. 分类别设置置信度阈值。
4. 人工抽查伪标签质量。
5. 使用真标签和伪标签混合训练 student。
6. 迭代 2-3 轮，观察 val/test 指标变化。

## 10. 物理实验补采建议

下一批物理实验优先补采：

1. `scratch` 类样本，建议至少新增 150-300 张包含 scratch 的图片。
2. 低对比、细长、边缘位置的 scratch。
3. 容易被误检为 splash/scratch 的正常背景纹理。
4. 不同光照、角度和拍摄距离下的瑕疵图。
5. 每次补采后保留约 20% 作为外部测试集，不参与训练。

## 11. 后续实验记录模板

每轮实验建议记录以下信息：

```text
实验编号：
实验名称：
模型：
训练方式：纯监督 / 数据增强 / 半监督 / 分割
有标注图片数：
未标注图片数：
训练轮数：
输入尺寸：
batch：
主要增强方式：

Precision：
Recall：
mAP50：
mAP50-95：
splash AP50：
scratch AP50：
chipping AP50：

主要漏检类别：
主要误检现象：
混淆矩阵结论：
PR/F1/Recall 曲线结论：
下一步计划：
```

## 12. 当前阶段结论

当前实验表明：

- YOLO26m 是目前三个尺度中的最优基线。
- 当前性能距离 `mAP50 = 0.90` 仍有明显差距。
- 最大短板是 `scratch` 类别的召回率和 AP50。
- 模型容量不是唯一瓶颈，数据质量、类别不均衡、低对比小目标、标注一致性更关键。
- 下一步应优先进行召回率增强实验和 scratch 定向补采，再考虑半监督伪标签。

