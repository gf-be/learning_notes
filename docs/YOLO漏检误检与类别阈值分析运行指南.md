# YOLO 漏检、误检与类别阈值分析运行指南

## 1. 指南用途

本指南基于项目中已有的四个脚本，完成以下工作：

1. 对固定模型进行统一置信度阈值扫描；
2. 统计每个阈值下的 TP、FP、FN、Precision、Recall 和 F1；
3. 找到每个类别的候选置信度阈值；
4. 使用分类别阈值重新生成预测结果；
5. 导出漏检（FN）与误检（FP）图片和 CSV；
6. 对错误来源进行人工分析。

使用的脚本：

```text
scripts/predict_yolo26_2048_thresholds.py
scripts/analyze_yolo_thresholds.py
scripts/predict_yolo_class_thresholds.py
scripts/export_yolo_fn_fp.py
```

这些操作均属于推理和后处理，不会重新训练模型，也不会修改 `best.pt`。

---

## 2. 当前项目约定

### 2.1 类别编号

运行前必须确认模型、真值标签和脚本使用相同的类别顺序：

```text
0: chipping
1: scratch
2: splash
3: spot
```

`--class-conf` 后面的四个数严格按照上述类别 ID 排列，不是按照英文首字母排列。

### 2.2 当前服务器路径

以下命令按照当前 Featurize 环境编写：

```text
项目目录：/home/featurize/work/yolo26_1/ultralytics
模型权重：/home/featurize/work/yolo26_1/ultralytics/runs/detect/runs_668/stage8_yolo26m_imgsz2048_lr2e4_mosaic010_v1/weights/best.pt
验证图片：/home/featurize/data/yolo_dataset/images/val
验证标签：/home/featurize/data/yolo_dataset/labels/val
```

开始前进入项目目录：

```bash
cd /home/featurize/work/yolo26_1/ultralytics
```

如果脚本放在项目根目录，而不是 `scripts/` 目录，将命令中的 `scripts/` 删除即可。

### 2.3 三种阈值不能混淆

| 参数 | 含义 | 当前建议值 |
|---|---|---:|
| Confidence | 是否保留一个预测框 | 扫描或分类别设置 |
| NMS IoU | 预测框之间去重时的 IoU | 0.70 |
| 匹配 IoU | 判断预测框是否与真值匹配 | 0.50 |

例如目录名中的 `iou070` 通常指预测阶段的 NMS IoU；运行统计脚本时的 `--iou 0.50` 指 TP 匹配标准，两者用途不同。

---

## 3. 运行前检查

确认以下内容：

- [ ] `best.pt` 路径存在；
- [ ] `images/val` 和 `labels/val` 路径存在；
- [ ] 图片与标签的文件主名一致，例如 `123.bmp` 对应 `123.txt`；
- [ ] 标签类别 ID 为 0～3；
- [ ] 使用当前项目的 Python/Ultralytics 环境；
- [ ] 输出目录名称没有被之前实验占用。

可查看脚本帮助：

```bash
python scripts/predict_yolo26_2048_thresholds.py --help
python scripts/analyze_yolo_thresholds.py --help
python scripts/predict_yolo_class_thresholds.py --help
python scripts/export_yolo_fn_fp.py --help
```

---

## 4. 第一步：统一置信度阈值扫描

### 4.1 生成不同阈值的预测结果

```bash
python scripts/predict_yolo26_2048_thresholds.py \
  --model /home/featurize/work/yolo26_1/ultralytics/runs/detect/runs_668/stage8_yolo26m_imgsz2048_lr2e4_mosaic010_v1/weights/best.pt \
  --source /home/featurize/data/yolo_dataset/images/val \
  --imgsz 2048 \
  --device 0 \
  --conf 0.05 0.10 0.15 0.20 0.25 0.30 \
  --project runs_668_threshold
```

脚本会为每个阈值生成一个目录：

```text
runs_668_threshold/
├── imgsz2048_conf0p05/
│   ├── labels/
│   └── 预测图片
├── imgsz2048_conf0p10/
├── imgsz2048_conf0p15/
├── imgsz2048_conf0p20/
├── imgsz2048_conf0p25/
└── imgsz2048_conf0p30/
```

预测 TXT 格式为：

```text
class_id x_center y_center width height confidence
```

### 4.2 注意事项

- 每次运行必须使用新的 `--project`，或者确保目标运行目录不存在；
- 脚本设置 `exist_ok=False`，不会自动覆盖以前的结果；
- 阈值扫描只改变保留预测框的条件，不改变模型参数；
- 第一轮建议使用 0.05 的步长，不必一开始扫描大量非常接近的阈值。

如需在最佳区间内细扫，可新建一个输出目录，例如：

```bash
python scripts/predict_yolo26_2048_thresholds.py \
  --model /home/featurize/work/yolo26_1/ultralytics/runs/detect/runs_668/stage8_yolo26m_imgsz2048_lr2e4_mosaic010_v1/weights/best.pt \
  --source /home/featurize/data/yolo_dataset/images/val \
  --imgsz 2048 \
  --device 0 \
  --conf 0.20 0.22 0.24 0.26 0.28 0.30 \
  --project runs_668_threshold_fine
```

---

## 5. 第二步：统计阈值扫描结果

```bash
python scripts/analyze_yolo_thresholds.py \
  --runs-root runs_668_threshold \
  --gt-labels /home/featurize/data/yolo_dataset/labels/val \
  --output runs_668_threshold/threshold_metrics \
  --iou 0.50 \
  --names chipping scratch splash spot \
  --diagnose
```

输出文件：

| 文件 | 内容 |
|---|---|
| `threshold_overall.csv` | 每个阈值的总体 TP、FP、FN、P、R、F1 |
| `threshold_per_class.csv` | 每个阈值下四个类别的独立指标 |
| `matching_diagnostics.csv` | 每个真值实例的文件匹配、同类 IoU 和任意类 IoU 诊断 |

终端还会输出：

```text
Overall best F1
Per-class best F1
Prediction filename found ratio
Any-class best IoU
Same-class best IoU
```

### 5.1 如何选择统一阈值

根据实际目标选择：

- 更重视少漏检：优先看 Recall，可以选择较低置信度阈值；
- 更重视少误报：优先看 Precision，可以选择较高置信度阈值；
- 希望兼顾 P 和 R：选择 F1 较高且 P/R 不过度失衡的位置。

当前验证集上，统一阈值基线为：

```text
conf=0.25
P=0.509
R=0.509
F1=0.509
TP/FP/FN=433/418/417
```

该结果仅作为当前固定验证集的后处理基线，不能推广为所有新数据的永久最佳阈值。

### 5.2 如何检查 TP=0 等异常

如果统计结果出现所有阈值 `TP=0`，先查看 `matching_diagnostics.csv`：

1. `prediction_file_found` 是否为 True；
2. 图片和预测 TXT 是否同名；
3. `gt_class_id` 是否与模型类别顺序一致；
4. `best_iou_any_class` 是否接近 0；
5. 真值是检测框还是分割多边形。

当前统计脚本已经兼容：

- YOLO 检测框真值；
- Labelme 转换得到的 YOLO 分割多边形真值，并使用外接框参与检测 IoU 统计。

---

## 6. 第三步：确定分类别候选阈值

打开：

```text
runs_668_threshold/threshold_metrics/threshold_per_class.csv
```

分别观察每个类别在不同置信度下的 P、R、F1。当前候选值为：

| 类别 ID | 类别 | 候选阈值 |
|---:|---|---:|
| 0 | chipping | 0.30 |
| 1 | scratch | 0.15 |
| 2 | splash | 0.30 |
| 3 | spot | 0.25 |

选择规则：

- `scratch` 漏检严重，因此采用较低阈值 0.15，优先提高 Recall；
- `chipping`、`splash` 误检较多，因此提高到 0.30；
- `spot` 在现有扫描中阈值调整收益不明显，暂时保留 0.25。

注意：分别取每类最高 F1 阈值，不保证组合后总体 F1 一定显著提高，必须重新生成预测并进行统一统计。

---

## 7. 第四步：运行分类别阈值预测

```bash
python scripts/predict_yolo_class_thresholds.py \
  --model /home/featurize/work/yolo26_1/ultralytics/runs/detect/runs_668/stage8_yolo26m_imgsz2048_lr2e4_mosaic010_v1/weights/best.pt \
  --source /home/featurize/data/yolo_dataset/images/val \
  --imgsz 2048 \
  --device 0 \
  --class-conf 0.30 0.15 0.30 0.25 \
  --iou 0.70 \
  --project runs_668_postprocess \
  --name class_conf_c30_s15_sp30_st25_iou070
```

输出结构：

```text
runs_668_postprocess/class_conf_c30_s15_sp30_st25_iou070/
├── images/    # 画出筛选后预测框的图片
└── labels/    # 带置信度的预测 TXT
```

脚本先以四个阈值中的最小值运行模型，然后按照类别分别过滤预测框。

### 7.1 输出目录已存在

如果出现：

```text
FileExistsError: Output already exists
```

不要覆盖原实验，修改 `--name`：

```bash
--name class_conf_c30_s15_sp30_st25_iou070_v2
```

---

## 8. 第五步：导出统一阈值的漏检和误检

以统一阈值 `conf=0.25` 为基线：

```bash
python scripts/export_yolo_fn_fp.py \
  --images /home/featurize/data/yolo_dataset/images/val \
  --gt-labels /home/featurize/data/yolo_dataset/labels/val \
  --pred-labels runs_668_threshold/imgsz2048_conf0p25/labels \
  --output runs_668_error_analysis/baseline_conf025_iou070_errors \
  --iou 0.50 \
  --partial-iou 0.10
```

这里的 `--iou 0.50` 是判断 TP 的匹配 IoU，不是预测阶段 NMS IoU。

---

## 9. 第六步：导出分类别阈值的漏检和误检

```bash
python scripts/export_yolo_fn_fp.py \
  --images /home/featurize/data/yolo_dataset/images/val \
  --gt-labels /home/featurize/data/yolo_dataset/labels/val \
  --pred-labels runs_668_postprocess/class_conf_c30_s15_sp30_st25_iou070/labels \
  --output runs_668_error_analysis/class_threshold_trial_01_errors \
  --iou 0.50 \
  --partial-iou 0.10
```

输出目录结构：

```text
runs_668_error_analysis/class_threshold_trial_01_errors/
├── fn/
│   ├── chipping/
│   ├── scratch/
│   ├── splash/
│   └── spot/
├── fp/
│   ├── chipping/
│   ├── scratch/
│   ├── splash/
│   └── spot/
├── error_cases.csv
└── pr_metrics.csv
```

每个类别目录下包含：

```text
images/       # 已绘制 GT、预测框和重点错误框
gt_labels/    # 对应真值标签副本
pred_labels/  # 对应预测标签副本
```

脚本不会修改原始图片和标签。

---

## 10. `pr_metrics.csv` 的解读

字段：

| 字段 | 含义 |
|---|---|
| `tp` | 正确检测到的目标数 |
| `fp` | 没有正确对应真值的预测数，即误检数 |
| `fn` | 没有被正确检测到的真值数，即漏检数 |
| `precision` | `TP / (TP + FP)` |
| `recall` | `TP / (TP + FN)` |
| `f1` | Precision 与 Recall 的调和平均 |

当前两组结果示例：

| 策略 | TP | FP | FN | P | R | F1 |
|---|---:|---:|---:|---:|---:|---:|
| 统一阈值 0.25 | 433 | 418 | 417 | 0.509 | 0.509 | 0.509 |
| 分类别阈值 | 415 | 358 | 435 | 0.537 | 0.488 | 0.511 |

当前分类别阈值减少了 60 个 FP，但增加了 18 个 FN。因此它适合减少误报，不代表模型本身的检出能力得到明显提升。

---

## 11. `error_cases.csv` 的解读

字段：

| 字段 | 含义 |
|---|---|
| `kind` | `FN` 漏检或 `FP` 误检 |
| `image` | 原始图片名 |
| `class` | 当前错误对应类别 |
| `reason` | 根据类别和 IoU 自动生成的初步诊断 |
| `confidence` | 相关预测框置信度；完全无预测时可能为空 |
| `best_iou` | 当前错误框与另一侧所有框的最大 IoU |
| `exported_image` | 导出可视化图片路径 |

`reason` 是自动诊断假设，不是人工确认结论。必须结合图片、GT 和预测标签检查。

---

## 12. 漏检（FN）分析方法

脚本把 FN 初步划分为三种：

### 12.1 完全未检测到

CSV 表现：

```text
reason=未检测到
best_iou < partial_iou
```

人工检查内容：

- 缺陷是否非常小或细长；
- 缺陷与背景对比度是否过低；
- 是否受到反光、曝光或模糊影响；
- 真值标签是否正确；
- 是否属于训练集中极少出现的外观；
- 图片是否与训练图像来自不同工件、批次或光照。

### 12.2 定位偏差或置信度不足

CSV 表现：

```text
partial_iou <= best_iou < match_iou
```

人工检查内容：

- 预测框是否只覆盖目标一部分；
- GT 框是否过紧或过松；
- 密集目标是否被合并成一个大框；
- 小目标是否因 2048 缩放、特征层分辨率或标注框形态造成偏移。

### 12.3 类别混淆

CSV 表现：

```text
best_iou >= match_iou
预测类别 != GT 类别
```

人工检查内容：

- splash 与 spot 的标注界限是否统一；
- scratch 与边缘纹理是否混淆；
- 同一外观是否在不同图片中被标成不同类别；
- 类别定义是否需要增加文字和图例规范。

### 12.4 漏检分析优先级

当前建议顺序：

1. 检查全部 scratch 验证实例；
2. 检查 spot 的完全漏检；
3. 检查 splash 的密集和小目标漏检；
4. 再检查 chipping 的边缘目标。

---

## 13. 误检（FP）分析方法

脚本把 FP 初步划分为三种：

### 13.1 背景、反光、边缘干扰或可能漏标

CSV 表现：

```text
best_iou < partial_iou
```

需要人工区分：

- 工件圆环边缘；
- 高亮反光；
- 灰尘、噪点或背景纹理；
- 实际存在缺陷但 GT 漏标；
- 模型产生没有真实依据的预测。

### 13.2 定位偏差或重复预测

CSV 表现：

```text
partial_iou <= best_iou < match_iou
```

检查内容：

- 一个真实目标是否产生多个预测框；
- 预测框是否覆盖相邻两个目标；
- NMS 是否未能去掉重复框；
- GT 是否把一个连片缺陷拆成多个实例。

### 13.3 类别混淆

CSV 表现：

```text
best_iou >= match_iou
预测类别 != GT 类别
```

检查预测类别与 GT 类别的混淆方向，例如：

```text
spot -> splash
splash -> spot
边缘反光 -> chipping
细纹理 -> scratch
```

---

## 14. 人工错误记录建议

建议在 CSV 后增加人工记录列，或单独建立表格：

| 图片 | 错误类型 | 类别 | 自动原因 | 人工确认原因 | 是否标注问题 | 是否需要补数据 | 备注 |
|---|---|---|---|---|---|---|---|
| `157.bmp` | FN | spot | 未检测到 | 低对比度小目标 | 否 | 是 | 暗区 |

人工原因建议统一为：

```text
低对比度
强反光
边缘干扰
小目标
细长目标
密集目标
定位偏差
重复预测
类别混淆
GT 漏标
GT 类别错误
GT 框不合理
疑似缺陷/无法确认
```

优先检查错误记录最多的图片，但要注意：错误数多可能只是因为一张图中真实缺陷较密集。

---

## 15. 推荐的完整运行顺序

```text
固定 best.pt 和验证集
        ↓
统一置信度阈值扫描
        ↓
统计 threshold_overall.csv 和 threshold_per_class.csv
        ↓
确定统一阈值基线和分类别候选阈值
        ↓
运行分类别阈值预测
        ↓
分别导出统一阈值、分类别阈值的 FN/FP
        ↓
比较 P、R、F1、TP、FP、FN
        ↓
人工归因高频错误图片
        ↓
决定是调整阈值、修正标签、补充数据还是重新训练
```

---

## 16. 如何根据结果决定下一步

| 观察结果 | 主要判断 | 后续方向 |
|---|---|---|
| 提高阈值后 FP 明显下降、FN 上升 | 阈值正常权衡 | 按部署需求选择 P 或 R |
| 大部分 FN 完全没有预测 | 模型或数据能力不足 | 补数据、查标签、重新训练 |
| 大部分 FN 有部分重叠 | 定位能力不足 | 检查框、分辨率、损失和小目标特征 |
| 大部分 FP 来自反光或边缘 | 场景干扰明显 | 补负样本、轻量光照增强、ROI 约束 |
| splash 与 spot 经常互相混淆 | 类别边界不清 | 统一标注规范并补充难例 |
| 训练集 P/R 高、验证集低 | 过拟合或数据域差异 | 增加真实多样数据 |
| 训练集和验证集 P/R 都低 | 欠拟合、标签或任务定义问题 | 先查数据，再改模型和训练策略 |

当前结果中约 80% 的 FN 属于完全未检测到。因此现阶段继续细扫 NMS IoU 的价值有限，应优先完成人工错误归因，并对同一权重进行训练集与验证集对照评估。

---

## 17. 常见报错

### 17.1 输出目录已经存在

```text
FileExistsError: Output already exists
```

处理方法：修改 `--project` 或 `--name`，保留旧实验结果。

### 17.2 找不到预测标签目录

```text
Prediction labels folder missing
```

处理方法：

- 确认预测时开启 `save_txt=True` 和 `save_conf=True`；
- 检查 `--runs-root` 是否指向包含各个 `conf` 子目录的上一级目录；
- 检查 `--pred-labels` 是否直接指向 `labels/`。

### 17.3 所有 TP 都为 0

处理顺序：

1. 使用 `--diagnose`；
2. 检查文件名对应率；
3. 检查类别顺序；
4. 检查坐标格式；
5. 检查真值是否为分割多边形；
6. 检查预测和 GT 是否来自同一套图片。

### 17.4 类别阈值数量不正确

四分类模型必须提供四个值：

```bash
--class-conf 0.30 0.15 0.30 0.25
```

如果模型返回的类别 ID 超过阈值数量，脚本会主动报错。

---

## 18. 结果归档规范

建议每次实验使用独立名称：

```text
runs_668_threshold/<统一阈值扫描批次>/
runs_668_postprocess/<分类别阈值配置>/
runs_668_error_analysis/<预测策略>_errors/
```

实验日志至少记录：

```text
模型权重路径
数据集版本
验证集图片数和实例数
imgsz
统一/分类别 confidence
预测 NMS IoU
统计匹配 IoU
TP、FP、FN、P、R、F1
输出目录
运行日期
```

不要使用相同目录覆盖旧实验，否则后续无法确认某个 CSV 对应哪组预测参数。
