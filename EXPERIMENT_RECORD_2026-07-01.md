# YOLO26 楔形片瑕疵检测实验记录

记录日期：2026-07-01

## 说明

本文档记录目前已经完成的数据集准备、模型训练实验和阶段性结论。  
所有指标均来自训练终端截图或本地数据统计结果；没有实际运行或没有结果截图确认的内容，均标注为“待验证”或“未运行”。

当前主要目标：

- 基于 YOLO26 进行楔形片瑕疵检测。
- 探索三分类、二分类、增强、切图、预处理等方案对 `mAP50` 的影响。
- 为后续半监督实验和实际部署阈值选择做准备。

## 1. 数据集基础信息

原始数据为 YOLO 格式：

- 图片：`.png`
- 标签：`.txt`
- 标签格式：`class x_center y_center width height`

类别定义：

| 类别编号 | 类别名称 |
|---:|---|
| 0 | splash |
| 1 | scratch |
| 2 | chipping |

重新划分后的原始三分类数据集：

| 集合 | 图片数 | 标签数 |
|---|---:|---:|
| train | 565 | 565 |
| val | 161 | 161 |
| test | 81 | 81 |

训练集类别框数量：

| 类别 | 框数 |
|---|---:|
| splash | 2815 |
| scratch | 364 |
| chipping | 390 |

验证集类别框数量：

| 类别 | 框数 |
|---|---:|
| splash | 835 |
| scratch | 169 |
| chipping | 117 |

测试集类别框数量：

| 类别 | 框数 |
|---|---:|
| splash | 394 |
| scratch | 52 |
| chipping | 71 |

阶段性观察：

- `splash` 数量远高于 `scratch/chipping`。
- `scratch` 是当前最难类别。
- 空标注图片存在，可作为正常/负样本参考。

## 2. 已准备的数据集版本

### 2.1 原始三分类数据集

路径：

```text
photo/
```

结构：

```text
photo/train/images
photo/train/labels
photo/val/images
photo/val/labels
photo/test/images
photo/test/labels
```

用途：

- 三分类 baseline。
- 三分类高分辨率实验。
- 后续标注清洗实验。

### 2.2 少数类离线增强数据集

路径：

```text
photo/train_aug
```

说明：

- 基于训练集做少数类离线增强。
- 包含 `scratch/chipping` 的图片被增强。
- 该版本会同时增加部分 `splash` 数量，因为很多图片中少数类与 `splash` 共存。

增强前后训练集框数量：

| 类别 | 原始 train | train_aug |
|---|---:|---:|
| splash | 2815 | 5847 |
| scratch | 364 | 1092 |
| chipping | 390 | 840 |

该方向后续实验效果不佳，未作为主线继续。

### 2.3 避免增加 splash 的离线增强数据集

路径：

```text
photo/train_aug_no_splash
```

配置文件：

```text
photo/data_aug_no_splash.yaml
```

说明：

- 只增强“不含 splash，但含 scratch/chipping”的训练图片。
- 不删除原始标注，不制造漏标。
- 原始 `photo/train` 未被修改。

增强前后训练集框数量：

| 类别 | 原始 train | train_aug_no_splash |
|---|---:|---:|
| splash | 2815 | 2815 |
| scratch | 364 | 604 |
| chipping | 390 | 657 |

校验：

- 图片与标签一一对应。
- bbox 坐标均在 `0..1` 范围内。

### 2.4 2x2 切图数据集

路径：

```text
photo_tile_2x2
```

配置文件：

```text
photo_tile_2x2/data.yaml
```

生成规则：

- train/val/test 全部切成 `2x2`。
- 每张原图生成 4 张切片。
- 标签根据切片坐标自动转换。
- 空切片保留为空标签，可作为负样本。

切图后统计：

| 集合 | 原图数 | 切片数 | 有标注切片 | 目标框数 |
|---|---:|---:|---:|---:|
| train | 565 | 2260 | 1202 | 3662 |
| val | 161 | 644 | 363 | 1158 |
| test | 81 | 324 | 181 | 527 |

切图后类别框数量：

| 集合 | splash | scratch | chipping |
|---|---:|---:|---:|
| train | 2839 | 413 | 410 |
| val | 843 | 192 | 123 |
| test | 398 | 57 | 72 |

### 2.5 二分类 defect 数据集

路径：

```text
photo_binary_defect
```

配置文件：

```text
photo_binary_defect/data.yaml
```

转换规则：

- 将 `splash/scratch/chipping` 全部合并为 `defect`。
- 所有目标类别编号统一为 `0`。
- 图片不变。
- 空标签保持为空。

统计：

| 集合 | 图片数 | 标签数 | 目标框数 |
|---|---:|---:|---:|
| train | 565 | 565 | 3569 |
| val | 161 | 161 | 1121 |
| test | 81 | 81 | 517 |

校验：

- 所有目标类别均为 `0`。
- bbox 坐标均在 `0..1`。

### 2.6 CLAHE 二分类数据集
提亮暗部细节、改善光照不均画面，同时抑制噪点过度放大
路径：

```text
photo_binary_defect_clahe
```

配置文件：

```text
photo_binary_defect_clahe/data.yaml
```

处理规则：

- 基于 `photo_binary_defect`。
- train/val/test 全部做同样 CLAHE 预处理。
- 标签不变。
- CLAHE 参数：`clipLimit=2.0`，`tileGridSize=8x8`。

统计：

| 集合 | 图片数 | 标签数 |
|---|---:|---:|
| train | 565 | 565 |
| val | 161 | 161 |
| test | 81 | 81 |

## 3. 已完成实验结果

说明：

- 表格中的指标均来自验证集输出截图。
- 除非特别说明，以下结果不是最终 test 集结果。
- `mAP50-95` 也记录，因为它能反映定位质量。

### 3.1 YOLO26 三尺度 baseline

训练设置概要：

- 数据集：原始三分类 `photo`
- 输入尺寸：`1280`
- epochs：`150`
- optimizer：`AdamW`
- 主要增强：基本关闭，仅保留很轻的 `hsv_v=0.03`

| 实验 | 模型 | P | R | mAP50 | mAP50-95 | splash AP50 | scratch AP50 | chipping AP50 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| stage1 | YOLO26n | 0.614 | 0.545 | 0.555 | 0.309 | 0.656 | 0.235 | 0.774 |
| stage1 | YOLO26s | 0.678 | 0.580 | 0.595 | 0.334 | 0.715 | 0.267 | 0.803 |
| stage1 | YOLO26m | 0.661 | 0.592 | 0.617 | 0.352 | 0.727 | 0.300 | 0.824 |

结论：

- YOLO26m 是三尺度中最优。
- `scratch` 明显最弱。
- 模型从 n 到 m 有提升，但提升幅度有限。

### 3.2 在线轻增强实验

实验名：

```text
stage2_yolo26m_recall_aug_v1
```

训练设置概要：

- 模型：YOLO26m
- 数据集：原始三分类 `photo`
- 输入尺寸：`1280`
- epochs：`220`
- 轻量 mosaic、亮度、缩放、平移等增强

mosaic:一次性随机拼接 4 张训练图片，合成一张新训练图，用来丰富数据集、提升模型泛化能力。
结果：

| 实验 | P | R | mAP50 | mAP50-95 | splash AP50 | scratch AP50 | chipping AP50 |
|---|---:|---:|---:|---:|---:|---:|---:|
| recall_aug_v1 | 0.615 | 0.617 | 0.598 | 0.338 | 0.717 | 0.281 | 0.796 |

结论：

- Recall 有小幅提高。
- Precision 和 mAP50 下降。
- 对 `scratch` 无明显帮助。

### 3.3 原始数据长训练实验

实验名：

```text
stage2_yolo26m_no_aug_longer
```

训练设置概要：

- 模型：YOLO26m
- 数据集：原始三分类 `photo`
- 输入尺寸：`1280`
- epochs：`260`
- 基本不增强

结果：

| 实验 | P | R | mAP50 | mAP50-95 | splash AP50 | scratch AP50 | chipping AP50 |
|---|---:|---:|---:|---:|---:|---:|---:|
| no_aug_longer | 0.672 | 0.579 | 0.598 | 0.343 | 0.716 | 0.299 | 0.778 |

结论：

- 单纯拉长训练无效。
- `scratch` 基本不变。
- 后期存在过拟合倾向。

### 3.4 离线增强 no_splash 实验

实验名：

```text
stage2_yolo26m_offline_aug_no_splash
```

训练设置概要：

- 模型：YOLO26m
- 数据集：`photo/train_aug_no_splash`
- 验证集：原始 `photo/val`
- 输入尺寸：`1280`8
- 训练时不叠加强增强

结果：

| 实验 | P | R | mAP50 | mAP50-95 | splash AP50 | scratch AP50 | chipping AP50 |
|---|---:|---:|---:|---:|---:|---:|---:|
| offline_aug_no_splash | 0.643 | 0.556 | 0.570 | 0.328 | 0.716 | 0.256 | 0.738 |

结论：

- 离线增强 no_splash 方向无效。
- `scratch` 和 `chipping` 均下降。

### 3.5 2x2 切图实验
一拆四
实验名：

```text
stage3_yolo26m_tile_2x2
```

训练设置概要：

- 模型：YOLO26m
- 数据集：`photo_tile_2x2`
- 输入尺寸：`1280`

结果：

| 实验 | 验证图片数 | P | R | mAP50 | mAP50-95 | splash AP50 | scratch AP50 | chipping AP50 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| tile_2x2 | 644 | 0.611 | 0.596 | 0.578 | 0.331 | 0.726 | 0.241 | 0.766 |

结论：

- 简单 2x2 非重叠切图无效。
- `scratch` 下降，`chipping` 也下降。
- 可能破坏了圆形边缘和整体上下文。

### 3.6 二分类 defect 实验

实验名：

```text
stage4_yolo26m_binary_defect
```

训练设置概要：

- 模型：YOLO26m
- 数据集：`photo_binary_defect`
- 输入尺寸：`1280`
- 目标类别：单类 `defect`

结果：

| 实验 | imgsz | P | R | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|---:|
| binary_defect | 1280 | 0.727 | 0.636 | 0.664 | 0.337 |

结论：

- 相比三分类 baseline 的 `mAP50=0.617` 有提升。
- 说明类别划分和标注一致性确实拖累三分类。
- 但 `mAP50-95` 未提升，说明定位质量仍是瓶颈。

### 3.7 二分类 defect 高分辨率实验

实验名：

```text
stage4_yolo26m_binary_defect_img1536
```

训练设置概要：

- 模型：YOLO26m
- 数据集：`photo_binary_defect`
- 输入尺寸：`1536`

结果：

| 实验 | imgsz | P | R | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|---:|
| binary_defect_img1536 | 1536 | 0.725 | 0.633 | 0.675 | 0.346 |

结论：

- 相比二分类 1280 有小幅提升。
- 高分辨率有帮助，但不是决定性因素。
- 当前所有已确认实验中，该结果是 mAP50 最高的一组。

### 3.8 CLAHE 二分类高分辨率实验

实验名：

```text
stage4_yolo26m_binary_defect_clahe_img1536
```

训练设置概要：

- 模型：YOLO26m
- 数据集：`photo_binary_defect_clahe`
- 输入尺寸：`1536`
- CLAHE 参数：`clipLimit=2.0`，`tileGridSize=8x8`

结果：

| 实验 | imgsz | P | R | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|---:|
| binary_defect_clahe_img1536 | 1536 | 0.668 | 0.665 | 0.662 | 0.337 |

结论：

- CLAHE 提高了 Recall。
- Precision 下降明显。
- `mAP50` 低于普通二分类 1536。
- 说明 CLAHE 可能增强了弱瑕疵，也增强了背景纹理和噪声。

## 4. 当前实验横向对比

| 实验方向 | 最好结果 mAP50 | 结论 |
|---|---:|---|
| 三分类 baseline | 0.617 | YOLO26m 最好，scratch 最弱 |
| 在线轻增强 | 0.598 | 无效，误报增加 |
| 长训练 | 0.598 | 无效，可能过拟合 |
| 离线增强 no_splash | 0.570 | 无效 |
| 2x2 切图 | 0.578 | 无效 |
| 二分类 1280 | 0.664 | 有提升，类别定义有影响 |
| 二分类 1536 | 0.675 | 当前最好 |
| CLAHE 二分类 1536 | 0.662 | Recall 提升但 Precision 下降 |

当前最好已确认结果：

```text
stage4_yolo26m_binary_defect_img1536
mAP50 = 0.675
mAP50-95 = 0.346
```

## 5. 关键问题分析

### 5.1 scratch 是主要瓶颈

三分类中 `scratch AP50` 长期在 `0.24~0.30` 左右波动。  
在线增强、离线增强、长训练、切图均未明显提升。

根据可视化结果观察：

- 同一条 scratch 有时被多个框分割标注。
- 有些框包整段，有些框包局部亮斑。
- 框大小和重叠情况不一致。
- scratch 与背景纹理/亮纹区分困难。

因此，scratch 问题更可能来自：

- 标注规则不统一；
- 目标低对比；
- 目标形态细长且不规则；
- 类别边界与 splash 存在不稳定。

### 5.2 二分类提升说明类别定义确实有影响

将三类合并为 `defect` 后，mAP50 从三分类 baseline 的 `0.617` 提升到 `0.664/0.675`。  
这说明模型检测“有瑕疵”比区分具体瑕疵类型更容易。

但二分类 `mAP50-95` 并没有大幅提高，说明定位质量仍未解决。

### 5.3 CLAHE 不适合作为当前主线

CLAHE 二分类实验中：

- Recall 上升；
- Precision 下降；
- mAP50 下降。

说明 CLAHE 可能把背景纹理也增强为疑似瑕疵，不适合作为当前默认预处理方案。

## 6. 阈值测试方案

已准备阈值测试脚本：

```text
scripts/eval_thresholds_binary.py
```

建议使用当前最好模型和数据：

```text
模型：stage4_yolo26m_binary_defect_img1536 的 best.pt
数据集：photo_binary_defect/data.yaml
split：test
```

建议测试：

| 实验 | conf | iou | 目的 |
|---|---:|---:|---|
| T1 | 0.10 | 0.50 | 高召回，观察漏检能否减少 |
| T2 | 0.15 | 0.50 | 重点候选 |
| T3 | 0.20 | 0.50 | 平衡 |
| T4 | 0.25 | 0.50 | 默认附近 |
| T5 | 0.30 | 0.50 | 控制误报 |

需要记录：

| conf | P | R | mAP50 | mAP50-95 | 正常图数量 | 正常图误报张数 | 正常图误报框数 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 | 待运行 |

注意：

- 阈值测试脚本已经准备，但本文档编写时尚未记录实际运行结果。
- 正常图误报数是工业部署时必须关注的指标。

## 7. 后续建议

### 7.1 优先进行 test 阈值测试

当前最需要知道的是：

- 在 `conf=0.10~0.30` 下，召回率能提高多少；
- 正常图误报数量是否可接受；
- 最终部署阈值应选偏召回还是偏精度。

推荐先使用：

```text
photo_binary_defect
stage4_yolo26m_binary_defect_img1536
split=test
```

### 7.2 做 scratch 标注清洗小闭环

建议先小规模清洗：

- train 中 50 张含 scratch 图片；
- val 中 20 张含 scratch 图片；
- 统一 scratch 标注规则。

推荐规则：

- 一条连续 scratch 尽量标为一个框；
- 不把同一条 scratch 拆成多个高度重叠的小框；
- 框尽量贴合，不包含大量背景；
- 多条明显分离的 scratch 才标多个框。

该实验尚未执行。

### 7.3 三分类 1536 待验证

二分类 1536 有小幅提升，但三分类 1536 尚未在本文档中记录实际结果。  
建议后续运行：

```text
stage4_yolo26m_multiclass_img1536
```

用途：

- 判断高分辨率是否也能提升三分类。
- 确定后续三分类是否固定 `imgsz=1536`。

## 8. 当前阶段结论

已经验证无效或收益较小的方向：

- 单纯拉长训练；
- 普通在线增强；
- 少数类离线增强；
- 避免增加 splash 的离线增强；
- 非重叠 2x2 切图训练；
- CLAHE 固定预处理。

当前相对有效的方向：

- 二分类 defect；
- 输入尺寸从 1280 提高到 1536；
- 后续阈值调优。

当前最大瓶颈：

- scratch 标注一致性；
- 小目标/低对比目标定位；
- 类别定义与背景纹理混淆；
- 正常图误报控制尚未量化。

当前最好已确认模型方向：

```text
YOLO26m + binary defect + imgsz1536
```

