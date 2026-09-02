# Scripts 使用指南

本文档整理 `scripts/` 下现有 29 个 Python 脚本和 1 个 PowerShell 辅助脚本的用途、依赖关系、输入输出和常用命令。除特别说明外，命令均在项目根目录执行。

## 1. 快速导航

| 阶段 | 推荐脚本 | 作用 |
|---|---|---|
| Labelme 转 YOLO | `labelme_to_yolo.py` | 普通随机划分并转换检测/分割标签 |
| Labelme 重新分层划分 | `repartition_labelme_stratified.py` | 按类别分布生成可复现的 train/val 划分 |
| 少数类增强 | `augment_yolo_minority.py` | 定向扩充指定类别，支持检测框和分割多边形 |
| 翻转/旋转/明暗增强 | `augment_yolo_flip_rotate_bc.py` | 对全部训练图增强并同步变换检测框 |
| 类别平衡增强 | `augment_yolo_balanced_flip_rotate_bc.py` | 优化增强来源，使最终各类实例数尽量一致 |
| 全物理增强 | `augment_wedge_all_physical_interactive.py` | 交互式组合位置、离焦、照明和反光变化 |
| 批量物理增强 | `augment_yolo_physical_3k.py` | 命令行方式扩充到指定训练图数量 |
| scratch 合成 | `synthesize_scratch_residual_yolo.py` | 将 scratch 残差融合到正常背景，减少粘贴痕迹 |
| 基线训练 | `train_yolo26m_v3_7_3_baseline.py` | 新 7:3 数据划分的 2048 分辨率基线 |
| 通用验证 | `validate_yolo.py` | 验证模型并导出总体/分类 P、R、F1、mAP |
| 严格复验 | `revalidate_yolo_best.py` | 验证前检查图片和实例数量，可清缓存 |
| 多阈值预测 | `predict_yolo26_2048_thresholds.py` | 用多组统一置信度生成预测标签和图片 |
| 分类别阈值 | `predict_yolo_class_thresholds.py` | 对不同类别应用不同置信度阈值 |
| 阈值统计 | `analyze_yolo_thresholds.py` | 根据预测 TXT 计算 TP、FP、FN、P、R、F1 |
| 错误样本导出 | `export_yolo_fn_fp.py` | 导出漏检和误检图片、标签及诊断表 |

## 2. 环境与数据结构

主要 Python 依赖：

```text
ultralytics
numpy
Pillow
opencv-python
PyYAML
```

典型 YOLO 数据集结构：

```text
dataset/
├─ data.yaml
├─ classes.txt                 # 部分脚本可选
├─ images/
│  ├─ train/
│  └─ val/
└─ labels/
   ├─ train/
   └─ val/
```

项目中存在两种旧数据结构：

- 新脚本通常使用 `images/train`、`labels/train`。
- `augment_minority_yolo.py`、`make_binary_defect_dataset.py`、`make_clahe_dataset.py` 和 `tile_yolo_dataset.py` 使用 `train/images`、`train/labels`。

运行前必须先确认脚本要求的目录结构，不能直接混用。

## 3. 标注转换与数据划分

### `labelme_to_yolo.py`

把同一目录中的 Labelme JSON 和图片转换为 YOLO 数据集，并随机划分 train/val。

- 支持 `segment` 多边形分割和 `detect` 检测框。
- 默认验证集比例为 20%，随机种子为 42。
- 可显式指定类别顺序，避免类别编号随名称排序改变。
- 图片可使用硬链接、复制或不复制。
- 输出 `data.yaml`、`classes.txt`、图片和标签目录。

```powershell
python scripts/labelme_to_yolo.py raw_labelme yolo_dataset `
  --task detect --val-ratio 0.2 --seed 42 `
  --classes chipping scratch splash spot
```

已有输出目录时，只有显式加入 `--overwrite` 才会删除并重建。

### `repartition_labelme_stratified.py`

从 Labelme 原始文件重新建立图像级分层 train/val 划分。相比普通随机划分，更适合类别不均衡数据。

- 同一张图片只会进入一个划分，避免数据泄漏。
- 根据每张图片包含的多个类别进行贪心分层与交换优化。
- 可为稀有类别指定验证集最少实例数。
- 无 JSON 的图片作为空标签背景样本保留。
- 输出 `split_manifest.csv` 和 `split_summary.json`，便于审计划分结果。

```powershell
python scripts/repartition_labelme_stratified.py raw_labelme yolo_dataset_v3_7_3 `
  --task detect --val-ratio 0.30 --seed 42 `
  --classes chipping scratch splash spot `
  --min-val-instances scratch=31
```

默认拒绝覆盖已有目录；`--overwrite` 会删除原输出目录后重建。

### `make_binary_defect_dataset.py`

将旧结构三分类数据集中的全部类别统一改成类别 `0: defect`，图片和框位置不变。

```powershell
python scripts/make_binary_defect_dataset.py `
  --src photo --dst photo_binary_defect `
  --path-in-yaml /home/featurize/data/photo_binary_defect
```

输出目录存在时会被直接删除并重建，使用前必须检查 `--dst`。

## 4. 数据增强与合成

### `augment_yolo_balanced_flip_rotate_bc.py`

通过整数优化选择各原图的增强次数，使最终训练集中的各类别实例数量尽量接近。全部稀有类别来源图至少使用一次，同时限制单张原图的最大增强次数。增强方式为水平翻转、小角度旋转、亮度和对比度变化，并同步更新检测框。

```powershell
python scripts/augment_yolo_balanced_flip_rotate_bc.py yolo_dataset output_balanced `
  --target-train-images 1500 --max-per-source 75 --seed 42 `
  --rotation 3 --brightness 0.90 1.10 --contrast 0.90 1.10 --dry-run
```

输出 `augmentation_manifest.csv` 和 `balance_summary.csv`。该脚本依赖 `scipy`，只支持五列 YOLO 检测框，输出目录必须不存在。

### `augment_yolo_flip_rotate_bc.py`

对每张训练图片生成“水平翻转 + 小角度旋转 + 亮度变化 + 对比度变化”的增强版本，并使用同一旋转矩阵同步更新 YOLO 检测框。原始训练图片和验证集均保留不变。

```powershell
python scripts/augment_yolo_flip_rotate_bc.py yolo_dataset output_aug `
  --variants 1 --seed 42 --rotation 3 `
  --brightness 0.90 1.10 --contrast 0.90 1.10 --dry-run
```

- 默认每张训练图生成 1 个版本。
- 增强图保存为质量 95 的 JPEG，原始图默认使用硬链接保留。
- 输出 `augmentation_manifest.csv`，记录每张增强图的角度、亮度和对比度参数。
- 只支持五列 YOLO 检测框；输出目录必须不存在。

### `augment_yolo_minority.py`（推荐少数类增强）

定向增强包含指定类别的训练图片；验证集保持不变。

- 同时支持五列检测框和多边形分割标签。
- 使用亮度、对比度、水平翻转和高斯噪声。
- 默认用硬链接保留原图片，减少磁盘占用。
- 支持 `--dry-run` 先统计选中图片和计划生成数量。
- 输出目录必须不存在，因此不会误覆盖已有实验。

```powershell
python scripts/augment_yolo_minority.py yolo_dataset yolo_dataset_scratch_aug `
  --target-class 1 --variants 2 --seed 42 --dry-run
```

确认计划后移除 `--dry-run` 正式生成。

### `augment_minority_yolo.py`（旧结构兼容版）

面向 `photo/train/images`、`photo/train/labels` 旧结构的少数类增强脚本。

- 默认 scratch 每图生成 2 个版本，chipping 每图生成 1 个版本。
- 使用亮度、对比度、翻转、小角度旋转和噪声。
- `--exclude-class 0` 可跳过含 splash 的图片。

```powershell
python scripts/augment_minority_yolo.py `
  --src photo/train --dst photo/train_aug_no_splash `
  --exclude-class 0
```

注意：输出目录存在时会被删除。新结构数据优先使用 `augment_yolo_minority.py`。

### 交互式物理增强脚本

以下脚本运行后会询问源数据集、输出目录、生成数量、随机种子和输出格式。它们共享 `physical_augmentation_common.py`，只增强训练集，验证集原样复制，并生成：

```text
augmentation_manifest.csv       # 每张增强图的来源、配方和参数
augmentation_summary.json       # 本次生成数量和配置摘要
```

| 脚本 | 模拟的物理变化 |
|---|---|
| `augment_position_shift_interactive.py` | 样品位置偏移和显微放大率微扰，同时变换标签 |
| `augment_wedge_defocus_interactive.py` | 楔形倾斜表面造成的方向性、非均匀离焦 |
| `augment_transillumination_interactive.py` | 透光强度、对比度和暗场照明梯度变化 |
| `augment_reflection_interactive.py` | 镀膜反射或平滑局部高光变化 |
| `augment_wedge_physical_combined_interactive.py` | 轻度组合位置、离焦、照明和传感器噪声 |
| `augment_wedge_all_physical_interactive.py` | 按比例混合全部配方，推荐用于完整物理增强对照 |

推荐入口：

```powershell
python scripts/augment_wedge_all_physical_interactive.py
```

全物理脚本默认建议将训练集扩充到约 3000 张，配方比例约为：位置 30%、离焦 25%、透射照明 20%、反光 15%、组合变化 10%。输出目录必须是新目录。

### `physical_augmentation_common.py`

这是上述交互式脚本的公共模块，负责：

- 读取交互参数和检查目录。
- 复制/硬链接原始数据集。
- 同步变换检测框或分割多边形。
- 生成渐变离焦、平移缩放等公共变换。
- 写入增强清单和摘要。

它不是独立入口，不需要直接运行。

### `augment_yolo_physical_3k.py`

全命令行版本的物理增强工具，适合在服务器或可复现实验中使用。

- 默认把训练集扩充到 3000 张。
- 配方包括位置、姿态、焦点、照明和组合变化。
- 几何变化同步更新 YOLO 检测框。
- 验证集保持不变。
- 输出 `augmentation_manifest.csv` 和 `augmentation_summary.json`。

```powershell
python scripts/augment_yolo_physical_3k.py yolo_dataset output_phys3k `
  --target-train-images 3000 --seed 42 --dry-run
```

该脚本主要面向 YOLO 检测框；若使用分割多边形，应优先使用交互式公共框架或先小规模核验标签。

### `synthesize_scratch_only_yolo.py`

从分割标签中截取 class 1 的 scratch 区域，粘贴到空标签正常背景上，生成只包含一个 scratch 的合成图片。

```powershell
python scripts/synthesize_scratch_only_yolo.py yolo_segment scratch_only_aug `
  --variants 2 --seed 42 --dry-run
```

要求源数据包含多边形分割标签，并且训练集中存在空标签背景图片。

### `synthesize_scratch_residual_yolo.py`（推荐 scratch 合成）

先估计 scratch 周围的局部背景，再提取残差并融合到正常背景，减少直接复制粘贴产生的边缘和亮度伪影。

```powershell
python scripts/synthesize_scratch_residual_yolo.py yolo_segment scratch_residual_aug `
  --variants 1 --blur-sigma 5 --strength-min 0.8 --strength-max 1.2 --dry-run
```

它同样要求 class 1 为 scratch、多边形标签和空标签背景。正式生成前建议用少量样本进行人工目视检查。

### `make_clahe_dataset.py`

对旧结构数据集的 train/val/test 全部图片进行 CLAHE 局部对比度增强，标签原样复制。

```powershell
python scripts/make_clahe_dataset.py `
  --src photo_binary_defect --dst photo_binary_defect_clahe `
  --clip-limit 2.0 --tile-grid-size 8
```

输出目录存在时会被删除并重建。CLAHE 会同时改变训练、验证和测试图像的外观，只适合评估“固定预处理流水线”。

### `tile_yolo_dataset.py`

将旧结构数据集的图片切成非重叠网格，并裁剪、重算检测框坐标。默认 2×2，每张原图生成 4 张切片。

```powershell
python scripts/tile_yolo_dataset.py `
  --src photo --dst photo_tile_2x2 `
  --grid 2 --min-visible 0.20 --min-pixels 2
```

空切片会保留为负样本；跨边界目标满足可见比例后可能出现在多个切片。输出目录存在时会被删除。

## 5. 训练脚本

以下脚本的模型、数据路径和输出名称直接写在代码中，运行前必须打开脚本检查服务器路径。

### `train_yolo26m_v3_7_3_baseline.py`

当前推荐基线：新 7:3 分层划分、YOLO26m、`imgsz=2048`、AdamW、轻量 Mosaic 0.10。用于和后续物理增强数据进行公平对照。

```powershell
python scripts/train_yolo26m_v3_7_3_baseline.py
```

### `train_yolo26m_online_aug.py`

原始数据上的轻量在线增强实验：亮度、2° 旋转、小幅平移缩放和水平翻转；关闭 Mosaic、MixUp、CutMix。

### `train_yolo26m_scratch_residual.py`

scratch 残差合成数据的对照训练。所有在线增强关闭，以单独观察离线合成数据是否有效。

## 6. 模型验证

### `validate_yolo.py`（通用推荐）

验证任意 YOLO 权重，导出总体和各类别的 Precision、Recall、F1、mAP50、mAP50-95。

```powershell
python scripts/validate_yolo.py `
  --model path/to/best.pt --data path/to/data.yaml `
  --split val --imgsz 2048 --batch 2 --device 0
```

结果目录中会新增 `pr_metrics_summary.csv`，方便直接用于日报和汇报。

### `revalidate_yolo_best.py`

在验证 `best.pt` 前先解析 `data.yaml`、统计验证图片和标签实例，并可与预期数量比较。适合修改标注、重划分或怀疑缓存失效后的严格复验。

```powershell
python scripts/revalidate_yolo_best.py `
  --weights path/to/best.pt --data path/to/data.yaml `
  --expected-val-images 200 --expected-val-instances 1798 `
  --strict --clear-cache
```

- `--strict`：实际数量和预期不一致时停止。
- `--clear-cache`：删除 `labels/val.cache`，让 Ultralytics 重建缓存。

### `eval_best_on_train.py`

用当前 `best.pt` 在训练集上计算总体和各类别 P、R、mAP，用于和验证集比较、辅助判断过拟合。模型和数据路径写死在文件顶部，必须先修改。

## 7. 阈值推理与部署选择

### `predict_yolo26_2048_thresholds.py`

对同一批图片依次使用多组统一置信度阈值预测，保存可视化图片以及带置信度的 YOLO TXT。

```powershell
python scripts/predict_yolo26_2048_thresholds.py `
  --model path/to/best.pt --source path/to/images/val `
  --conf 0.05 0.10 0.15 0.20 0.25 0.30 `
  --imgsz 2048 --device 0
```

它用于生成后续阈值统计的输入，不会重新训练模型，也不能替代标准 mAP 验证。

### `predict_yolo_class_thresholds.py`

只推理一次，然后为每个类别应用独立置信度阈值。适合 scratch 召回较弱、不同类别需要不同部署门槛的情况。

```powershell
python scripts/predict_yolo_class_thresholds.py `
  --model path/to/best.pt --source path/to/images/val `
  --thresholds 0.30 0.15 0.30 0.25 --iou 0.70 `
  --project runs_668_postprocess --name class_threshold_trial_01
```

阈值顺序必须严格对应模型类别 ID。输出目录已存在时脚本会停止，避免覆盖结果。

### `eval_thresholds_binary.py`

旧单类 defect 模型的固定阈值评估脚本。依次测试 `conf=0.10～0.30`，并额外统计空标签正常图片上的误报图片数和误报框数。

结果写入：

```text
runs_defect_threshold/threshold_summary.csv
```

权重、数据集和参数写在文件顶部；默认路径可能与当前环境不一致，运行前必须修改。

## 8. 指标分析与错误样本

### `analyze_yolo_thresholds.py`

读取 `predict_yolo26_2048_thresholds.py` 生成的多组预测标签，与真实标签按类别和 IoU 贪心匹配，计算 TP、FP、FN、Precision、Recall 和 F1。

```powershell
python scripts/analyze_yolo_thresholds.py `
  --runs-root runs_668_threshold `
  --gt-labels path/to/labels/val `
  --output runs_668_threshold/threshold_metrics `
  --iou 0.50 `
  --names chipping scratch splash spot
```

输出：

- `threshold_overall.csv`：每个阈值的总体指标。
- `threshold_per_class.csv`：每个阈值、每个类别的指标。
- `matching_diagnostics.csv`：逐标注匹配诊断和最佳 IoU；仅在加入 `--diagnose` 时生成。

该脚本既能读取五列检测标签，也会把分割多边形转换为外接框后比较。

### `export_yolo_fn_fp.py`

将预测标签与真实标签匹配，按类别导出漏检 FN、误检 FP 的原图、标注、预测标签和诊断 CSV。

```powershell
python scripts/export_yolo_fn_fp.py `
  --images path/to/images/val `
  --gt-labels path/to/labels/val `
  --pred-labels path/to/prediction/labels `
  --output runs_error_analysis/trial_01 `
  --iou 0.50 --partial-iou 0.10
```

输出包括：

- `fn/<类别>/` 与 `fp/<类别>/` 错误样本目录。
- `error_cases.csv`：错误类型、原因、置信度和最佳 IoU。
- `pr_metrics.csv`：各类别 TP、FP、FN、P、R、F1。

输出目录必须不存在，避免不同实验的错误样本混在一起。

## 9. 每日记录辅助脚本

### `new_daily_log.ps1`

根据 `docs/templates/DAILY_LOG_TEMPLATE.md` 创建当天日志：

```powershell
.\scripts\new_daily_log.ps1
```

也可指定日期：

```powershell
.\scripts\new_daily_log.ps1 -Date 2026-08-30
```

如果当天文件已经存在，脚本不会覆盖。

## 10. 推荐工作流

```text
Labelme 原始标注
  ↓ labelme_to_yolo / repartition_labelme_stratified
YOLO 基础数据集
  ↓ baseline 训练
基线 best.pt
  ↓ validate_yolo / revalidate_yolo_best
稳定基线指标
  ↓ 少数类增强、scratch 合成或物理增强
增强数据集与对照训练
  ↓ 多阈值预测 + analyze_yolo_thresholds
阈值 P/R/F1 对比
  ↓ export_yolo_fn_fp
漏检、误检和标注问题分析
```

## 11. 运行安全检查

每次运行数据生成脚本前建议确认：

1. 数据结构是否与脚本要求一致。
2. 类别 ID 顺序是否正确，尤其 `scratch` 是否仍为 class 1。
3. 输出目录是否写错；部分旧脚本会直接删除已有输出目录。
4. `data.yaml` 中的 `path` 是否适合本机或服务器。
5. 先使用 `--dry-run` 的脚本查看计划数量。
6. 训练前抽查增强图和同步后的标签。
7. 不要修改原验证集；增强实验只改变训练集。
8. 每次使用新的输出名称，避免实验结果互相覆盖。
