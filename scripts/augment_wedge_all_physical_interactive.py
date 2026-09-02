#!/usr/bin/env python3
"""Build one YOLO training set covering all realistic wedge-filter imaging changes.

The source images are composite microscope images of wedge filters.  Generated
training samples are balanced across five plausible acquisition variations:

* position: sample placement / microscope field shift;
* wedge_defocus: non-uniform defocus caused by the tilted wedge surface;
* transillumination: transmitted-light and dark-field intensity variation;
* reflection: coating reflection / smooth local highlight variation;
* combined: mild co-occurrence of placement, defocus, illumination and sensor noise.

Validation is copied unchanged.  Run interactively and choose the desired total
number of training images.  A manifest records the source and parameters of every
generated image.
"""

from __future__ import annotations

import math
import random

import numpy as np
from PIL import Image, ImageEnhance

from physical_augmentation_common import (
    DatasetContext,
    gradient_blur,
    interactive_context,
    prompt_choice,
    prompt_float,
    prompt_int,
    run_augmentation,
    translate_scale,
)


# More samples are allocated to the two dominant real acquisition factors:
# manual placement and wedge-induced focus variation.
RECIPE_WEIGHTS = {
    "position": 0.30,
    "wedge_defocus": 0.25,
    "transillumination": 0.20,
    "reflection": 0.15,
    "combined": 0.10,
}


def choose_recipe(index: int, count: int, rng: random.Random) -> str:
    """Create a shuffled exact-ish allocation, rather than random drifting ratios."""
    if index == 1:
        global _RECIPE_PLAN
        allocated: list[str] = []
        assigned = 0
        names = list(RECIPE_WEIGHTS)
        for recipe in names[:-1]:
            amount = round(count * RECIPE_WEIGHTS[recipe])
            allocated.extend([recipe] * amount)
            assigned += amount
        allocated.extend([names[-1]] * (count - assigned))
        rng.shuffle(allocated)
        _RECIPE_PLAN = allocated
    return _RECIPE_PLAN[index - 1]


_RECIPE_PLAN: list[str] = []


def add_reflection(image: Image.Image, rng: random.Random, strength: float) -> tuple[Image.Image, dict[str, float]]:
    array = np.asarray(image.convert("RGB"), dtype=np.float32)
    height, width = array.shape[:2]
    yy, xx = np.mgrid[0:height, 0:width]
    cx, cy = rng.uniform(0.15, 0.85) * width, rng.uniform(0.15, 0.85) * height
    sx, sy = rng.uniform(0.18, 0.42) * width, rng.uniform(0.10, 0.30) * height
    gain = rng.uniform(strength * 0.35, strength)
    halo = gain * np.exp(-0.5 * (((xx - cx) / sx) ** 2 + ((yy - cy) / sy) ** 2))
    result = Image.fromarray(np.clip(array * (1 + halo[..., None]), 0, 255).astype(np.uint8), "RGB")
    return result, {"highlight_x": round(cx / width, 4), "highlight_y": round(cy / height, 4), "highlight_strength": round(gain, 4)}


def add_transillumination(image: Image.Image, rng: random.Random, strength: float) -> tuple[Image.Image, dict[str, float]]:
    brightness = rng.uniform(1 - strength, 1 + strength)
    contrast = rng.uniform(1 - strength * 0.55, 1 + strength * 0.55)
    result = ImageEnhance.Contrast(ImageEnhance.Brightness(image).enhance(brightness)).enhance(contrast)
    array = np.asarray(result.convert("RGB"), dtype=np.float32)
    height, width = array.shape[:2]
    yy, xx = np.mgrid[-1:1:complex(height), -1:1:complex(width)]
    angle = rng.uniform(0, 2 * math.pi)
    gradient_strength = rng.uniform(-strength, strength)
    gradient = 1 + gradient_strength * (xx * math.cos(angle) + yy * math.sin(angle))
    result = Image.fromarray(np.clip(array * gradient[..., None], 0, 255).astype(np.uint8), "RGB")
    return result, {"brightness": round(brightness, 4), "contrast": round(contrast, 4), "gradient_strength": round(gradient_strength, 4)}


def configure() -> tuple[DatasetContext, int, str, float]:
    context, _ = interactive_context("楔形滤光片：全物理变化模拟增强数据集")
    original = len(context.train_pairs)
    target = prompt_int(f"目标训练集总图数（当前原图 {original} 张；建议约 3000）", 3000, minimum=original)
    count = target - original
    direction = prompt_choice("楔形焦面梯度方向", ("vertical", "horizontal", "diagonal"), "vertical")
    strength = prompt_float("整体物理变化强度（建议先使用 0.7）", 0.7, 0.2, 1.0)
    print("\n生成计划：")
    print(f"  保留原训练图：{original} 张")
    print(f"  新增物理增强：{count} 张")
    print(f"  最终训练图：{target} 张；验证集不变")
    print("  变化分配：" + "、".join(f"{name}≈{round(count * weight)}" for name, weight in RECIPE_WEIGHTS.items()))
    return context, count, direction, strength


def main() -> None:
    context, count, direction, strength = configure()
    if count == 0:
        print("目标数量等于原训练图数量，无需生成增强图。")
        return

    call_index = 0

    def transform(image: Image.Image, labels: list[list[float]], rng: random.Random, np_rng: np.random.Generator):
        nonlocal call_index
        call_index += 1
        recipe = choose_recipe(call_index, count, rng)
        params: dict[str, float | str] = {"recipe": recipe, "strength": strength}
        if recipe == "position":
            scale = rng.uniform(1 - 0.04 * strength, 1 + 0.04 * strength)
            tx, ty = rng.uniform(-0.06 * strength, 0.06 * strength), rng.uniform(-0.06 * strength, 0.06 * strength)
            image, labels = translate_scale(image, labels, scale, tx, ty)
            params.update(scale=round(scale, 5), translate_x=round(tx, 5), translate_y=round(ty, 5))
        elif recipe == "wedge_defocus":
            far = rng.uniform(0.70, 1.85) * strength
            near = rng.uniform(0, min(0.25 * strength, far))
            image = gradient_blur(image, direction, near, far)
            params.update(direction=direction, near_blur_px=round(near, 4), far_blur_px=round(far, 4))
        elif recipe == "transillumination":
            image, detail = add_transillumination(image, rng, 0.18 * strength)
            params.update(detail)
        elif recipe == "reflection":
            image, detail = add_reflection(image, rng, 0.15 * strength)
            params.update(detail)
        else:
            scale = rng.uniform(1 - 0.025 * strength, 1 + 0.025 * strength)
            tx, ty = rng.uniform(-0.035 * strength, 0.035 * strength), rng.uniform(-0.035 * strength, 0.035 * strength)
            image, labels = translate_scale(image, labels, scale, tx, ty)
            far = rng.uniform(0.50, 1.30) * strength
            image = gradient_blur(image, direction, 0, far)
            image, light_detail = add_transillumination(image, rng, 0.10 * strength)
            image, reflection_detail = add_reflection(image, rng, 0.07 * strength)
            noise_std = rng.uniform(0.2, 1.2) * strength
            array = np.asarray(image, dtype=np.float32) + np_rng.normal(0, noise_std, np.asarray(image).shape)
            image = Image.fromarray(np.clip(array, 0, 255).astype(np.uint8), "RGB")
            params.update(scale=round(scale, 5), translate_x=round(tx, 5), translate_y=round(ty, 5),
                          direction=direction, far_blur_px=round(far, 4), noise_std=round(noise_std, 4),
                          **light_detail, **reflection_detail)
        return image, labels, params

    run_augmentation(context, count, "all_physical", transform)


if __name__ == "__main__":
    main()
