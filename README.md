# 楔形片瑕疵检测实验

本仓库用于记录基于 YOLO26 的楔形片瑕疵检测工作，包括数据准备、训练实验、结果分析、学习笔记与每日进展。

## 当前进展

- 已完成 YOLO26n、YOLO26s、YOLO26m 三分类基线对比。
- 已验证在线增强、离线增强、2×2 切图、二分类与 CLAHE 预处理。
- 当前已记录的最佳方案：`YOLO26m + binary defect + imgsz=1536`。
- 当前最佳验证结果：`mAP50=0.675`，`mAP50-95=0.346`。
- 主要瓶颈：`scratch` 标注一致性、低对比小目标定位、正常图片误报。

> 上述结论来自截至 2026-07-01 的实验记录。新结果应以 `docs/daily/` 中的每日记录和后续汇总为准。

## 文档导航

| 内容 | 文件 |
|---|---|
| 完整阶段实验记录 | [EXPERIMENT_RECORD_2026-07-01.md](EXPERIMENT_RECORD_2026-07-01.md) |
| 早期基线与半监督计划 | [EXPERIMENT_LOG.md](EXPERIMENT_LOG.md) |
| 项目文件说明 | [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) |
| 每日记录使用说明 | [docs/daily/README.md](docs/daily/README.md) |
| 每日记录模板 | [docs/templates/DAILY_LOG_TEMPLATE.md](docs/templates/DAILY_LOG_TEMPLATE.md) |
| Scripts 使用指南 | [scripts/README.md](scripts/README.md) |

## 目录说明

```text
.
├─ docs/                         # 项目说明、每日记录和模板（上传 GitHub）
├─ scripts/                      # 数据处理与评估脚本（上传 GitHub）
├─ outputs/                      # 阶段汇报成品（默认仅保留最终文件）
├─ photo*/                       # 数据集及派生版本（仅本地保存）
├─ stage1_yolo26m_baseline/      # 训练结果与权重（仅本地保存）
├─ work/                         # 汇报材料的临时工作目录（仅本地保存）
├─ EXPERIMENT_LOG.md             # 初期实验日志
└─ EXPERIMENT_RECORD_2026-07-01.md # 截至 7 月 1 日的完整汇总
```

## 每日记录方式

每天新建一个 `docs/daily/YYYY-MM-DD.md`，重点记录：

1. 今天完成了什么，以及对应文件或实验名称。
2. 实验参数、结果指标和证据来源。
3. 今天学习了什么，是否能用于当前项目。
4. 遇到的问题、判断依据和下一步行动。

可在 PowerShell 中运行：

```powershell
.\scripts\new_daily_log.ps1
```

然后填写新生成的记录，并提交：

```powershell
git add README.md docs scripts *.md
git commit -m "docs: 记录 YYYY-MM-DD 工作与学习进展"
git push
```

首次推送前，需要先在 GitHub 创建一个空仓库并配置远程地址。仓库不跟踪原始图片、派生数据集、压缩包、模型权重和临时构建文件。

