#!/usr/bin/env python3
"""Shared helpers for physically motivated YOLO image augmentation.

The scripts importing this module are for *wedge-filter composite microscope
images*.  They only augment ``images/train`` and copy validation unchanged.
Every generated sample receives a matching YOLO label file and is logged in a
manifest, making the experiment reproducible and auditable.
"""

from __future__ import annotations

import csv
import json
import os
import random
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image, ImageFilter, ImageStat


IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


@dataclass
class DatasetContext:
    source: Path
    output: Path
    image_mode: str
    output_format: str
    jpg_quality: int
    seed: int
    train_pairs: list[tuple[Path, Path, list[list[float]]]]


def prompt_path(message: str, default: Path | None = None) -> Path:
    suffix = f" [{default}]" if default else ""
    value = input(f"{message}{suffix}: ").strip().strip('"')
    return Path(value) if value else (default if default else Path())


def prompt_int(message: str, default: int, minimum: int = 1) -> int:
    while True:
        raw = input(f"{message} [{default}]: ").strip()
        try:
            value = default if not raw else int(raw)
            if value < minimum:
                raise ValueError
            return value
        except ValueError:
            print(f"请输入不小于 {minimum} 的整数。")


def prompt_float(message: str, default: float, minimum: float, maximum: float) -> float:
    while True:
        raw = input(f"{message} [{default}]: ").strip()
        try:
            value = default if not raw else float(raw)
            if not minimum <= value <= maximum:
                raise ValueError
            return value
        except ValueError:
            print(f"请输入 {minimum} 到 {maximum} 之间的数值。")


def prompt_choice(message: str, choices: tuple[str, ...], default: str) -> str:
    choices_text = "/".join(choices)
    while True:
        value = input(f"{message} ({choices_text}) [{default}]: ").strip().lower()
        value = default if not value else value
        if value in choices:
            return value
        print(f"请输入：{choices_text}")


def read_labels(path: Path) -> list[list[float]]:
    rows: list[list[float]] = []
    if not path.exists():
        return rows
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split()
        # Detection rows are ``class x_center y_center width height``.  YOLO
        # segmentation rows are ``class x1 y1 x2 y2 ...`` (at least 3 points).
        if len(fields) != 5 and (len(fields) < 7 or len(fields) % 2 == 0):
            raise ValueError(
                f"{path}:{line_number} 不是有效的 YOLO 检测或分割标签"
                "（检测应为 5 列；分割应为类别加至少 3 个坐标点）。"
            )
        values = list(map(float, fields))
        if len(values) == 5:
            if values[3] > 0 and values[4] > 0:
                rows.append(values)
        else:
            rows.append(values)
    return rows


def write_labels(path: Path, rows: list[list[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(
        " ".join([str(int(row[0])), *(f"{value:.8f}" for value in row[1:])])
        for row in rows
    )
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def link_or_copy(source: Path, target: Path, image_mode: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if image_mode == "copy":
        shutil.copy2(source, target)
        return
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def copy_original_dataset(source: Path, output: Path, image_mode: str) -> None:
    for split in ("train", "val", "test"):
        image_dir = source / "images" / split
        if not image_dir.is_dir():
            continue
        for image_path in sorted(image_dir.iterdir(), key=lambda path: path.name.casefold()):
            if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            link_or_copy(image_path, output / "images" / split / image_path.name, image_mode)
            label = source / "labels" / split / f"{image_path.stem}.txt"
            destination = output / "labels" / split / f"{image_path.stem}.txt"
            destination.parent.mkdir(parents=True, exist_ok=True)
            if label.exists():
                shutil.copy2(label, destination)
            else:
                destination.write_text("", encoding="utf-8")
    for name in ("data.yaml", "classes.txt"):
        if (source / name).is_file():
            shutil.copy2(source / name, output / name)


def update_yaml_path(output: Path) -> None:
    yaml_path = output / "data.yaml"
    if not yaml_path.exists():
        return
    lines = yaml_path.read_text(encoding="utf-8-sig").splitlines()
    replaced = False
    for index, line in enumerate(lines):
        if line.startswith("path:"):
            lines[index] = f"path: '{output.as_posix()}'"
            replaced = True
            break
    if not replaced:
        lines.insert(0, f"path: '{output.as_posix()}'")
    yaml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_context(source: Path, output: Path, seed: int, image_mode: str, output_format: str, jpg_quality: int) -> DatasetContext:
    source, output = source.resolve(), output.resolve()
    if output.exists():
        raise SystemExit(f"输出目录已存在：{output}\n请换一个新目录，避免覆盖既有实验。")
    image_dir, label_dir = source / "images" / "train", source / "labels" / "train"
    if not image_dir.is_dir() or not label_dir.is_dir():
        raise SystemExit("输入目录应为 YOLO 数据集根目录，且包含 images/train 与 labels/train。")
    pairs: list[tuple[Path, Path, list[list[float]]]] = []
    for image_path in sorted(image_dir.iterdir(), key=lambda path: path.name.casefold()):
        if image_path.is_file() and image_path.suffix.lower() in IMAGE_SUFFIXES:
            label_path = label_dir / f"{image_path.stem}.txt"
            pairs.append((image_path, label_path, read_labels(label_path)))
    if not pairs:
        raise SystemExit("未发现训练图片。")
    return DatasetContext(source, output, image_mode, output_format, jpg_quality, seed, pairs)


def fill_color(image: Image.Image) -> tuple[int, int, int]:
    median = ImageStat.Stat(image.convert("RGB")).median
    return tuple(int(value) for value in median[:3])


def transform_boxes(rows: list[list[float]], transform: Callable[[float, float], tuple[float, float]]) -> list[list[float]]:
    """Transform YOLO detection boxes or segmentation polygons."""
    result: list[list[float]] = []
    for row in rows:
        cls = row[0]
        is_box = len(row) == 5
        if is_box:
            _, x, y, w, h = row
            points = [(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)]
        else:
            points = list(zip(row[1::2], row[2::2]))
        points = [transform(px, py) for px, py in points]
        xs = [min(1.0, max(0.0, px)) for px, _ in points]
        ys = [min(1.0, max(0.0, py)) for _, py in points]
        x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
        if x2 - x1 >= 0.001 and y2 - y1 >= 0.001:
            if is_box:
                result.append([cls, (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1])
            else:
                coordinates = [coordinate for point in zip(xs, ys) for coordinate in point]
                result.append([cls, *coordinates])
    return result


def translate_scale(image: Image.Image, rows: list[list[float]], scale: float, tx: float, ty: float) -> tuple[Image.Image, list[list[float]]]:
    width, height = image.size
    inverse = (1 / scale, 0, -tx * width / scale, 0, 1 / scale, -ty * height / scale)
    transformed = image.transform(image.size, Image.Transform.AFFINE, inverse, Image.Resampling.BICUBIC, fillcolor=fill_color(image))
    labels = transform_boxes(rows, lambda x, y: (scale * x + tx, scale * y + ty))
    return transformed, labels


def gradient_blur(image: Image.Image, direction: str, near_radius: float, far_radius: float) -> Image.Image:
    """Blend sharp and blurred images with a monotonic wedge-like focus gradient."""
    sharp = np.asarray(image.convert("RGB"), dtype=np.float32)
    blurred = np.asarray(image.convert("RGB").filter(ImageFilter.GaussianBlur(far_radius)), dtype=np.float32)
    height, width = sharp.shape[:2]
    if direction == "vertical":
        ratio = np.linspace(near_radius / max(far_radius, 0.001), 1.0, height)[:, None]
        ratio = np.repeat(ratio, width, axis=1)
    elif direction == "horizontal":
        ratio = np.linspace(near_radius / max(far_radius, 0.001), 1.0, width)[None, :]
        ratio = np.repeat(ratio, height, axis=0)
    else:
        yy, xx = np.mgrid[0:height, 0:width]
        ratio = np.clip((xx / max(width - 1, 1) + yy / max(height - 1, 1)) / 2, 0, 1)
        ratio = near_radius / max(far_radius, 0.001) + ratio * (1 - near_radius / max(far_radius, 0.001))
    result = sharp * (1 - ratio[..., None]) + blurred * ratio[..., None]
    return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8), mode="RGB")


def save_image(image: Image.Image, destination: Path, output_format: str, jpg_quality: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "jpg":
        image.convert("RGB").save(destination, "JPEG", quality=jpg_quality, subsampling=0, optimize=True)
    else:
        image.convert("RGB").save(destination, "PNG", optimize=True)


def run_augmentation(
    context: DatasetContext,
    count: int,
    recipe: str,
    transform: Callable[[Image.Image, list[list[float]], random.Random, np.random.Generator], tuple[Image.Image, list[list[float]], dict]],
) -> None:
    rng, np_rng = random.Random(context.seed), np.random.default_rng(context.seed)
    source_order = list(range(len(context.train_pairs)))
    rng.shuffle(source_order)
    context.output.mkdir(parents=True)
    copy_original_dataset(context.source, context.output, context.image_mode)
    update_yaml_path(context.output)
    extension = ".jpg" if context.output_format == "jpg" else ".png"
    manifest: list[dict[str, str]] = []
    for index in range(1, count + 1):
        image_path, _, labels = context.train_pairs[source_order[(index - 1) % len(source_order)]]
        with Image.open(image_path) as opened:
            augmented, new_labels, parameters = transform(opened.convert("RGB"), [row[:] for row in labels], rng, np_rng)
        stem = f"{image_path.stem}_phys_{recipe}_{index:05d}"
        save_image(augmented, context.output / "images" / "train" / f"{stem}{extension}", context.output_format, context.jpg_quality)
        write_labels(context.output / "labels" / "train" / f"{stem}.txt", new_labels)
        manifest.append({"generated_image": f"{stem}{extension}", "source_image": image_path.name, "recipe": str(parameters.get("recipe", recipe)),
                         "parameters": json.dumps(parameters, ensure_ascii=False, sort_keys=True), "seed": str(context.seed)})
        if index % 50 == 0 or index == count:
            print(f"已生成 {index}/{count} 张")
    with (context.output / "augmentation_manifest.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=["generated_image", "source_image", "recipe", "parameters", "seed"])
        writer.writeheader()
        writer.writerows(manifest)
    (context.output / "augmentation_summary.json").write_text(json.dumps({
        "source": str(context.source), "seed": context.seed, "recipe": recipe,
        "original_train_images": len(context.train_pairs), "generated_train_images": count,
        "total_train_images": len(context.train_pairs) + count,
        "validation_augmented": False,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n完成。输出数据集：{context.output}")
    print("验证集未增强，可作为固定对照。")


def interactive_context(script_title: str) -> tuple[DatasetContext, int]:
    print("=" * 60)
    print(script_title)
    print("只增强训练集；验证集保持不变；默认随机种子为 42。")
    print("=" * 60)
    source = prompt_path("输入 YOLO 数据集根目录", Path("photo/668/yolo_dataset_v3_7_3"))
    output = prompt_path("输出新数据集目录", Path("photo/668/yolo_dataset_v3_7_3_physaug"))
    count = prompt_int("本次新增增强训练图数量", 500)
    seed = prompt_int("随机种子", 42, minimum=0)
    mode = prompt_choice("原图保存方式", ("hardlink", "copy"), "hardlink")
    fmt = prompt_choice("增强图格式", ("jpg", "png"), "jpg")
    quality = prompt_int("JPEG 质量（仅 jpg 生效）", 95, minimum=20)
    if quality > 100:
        raise SystemExit("JPEG 质量不能超过 100。")
    return make_context(source, output, seed, mode, fmt, quality), count
