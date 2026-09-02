#!/usr/bin/env python3
"""Interactively combine mild placement, defocus, illumination and reflection changes."""

from __future__ import annotations

import random
import numpy as np
from PIL import Image, ImageEnhance

from physical_augmentation_common import gradient_blur, interactive_context, prompt_choice, prompt_float, run_augmentation, translate_scale


def main() -> None:
    context, count = interactive_context("物理增强 5：楔形滤光片成像变化组合")
    direction = prompt_choice("非均匀离焦梯度方向", ("vertical", "horizontal", "diagonal"), "vertical")
    strength = prompt_float("整体增强强度（建议 0.5-1.0；先选 0.7）", 0.7, 0.2, 1.0)

    def transform(image: Image.Image, labels: list[list[float]], rng: random.Random, _: np.random.Generator):
        scale = rng.uniform(1 - 0.025 * strength, 1 + 0.025 * strength)
        tx, ty = rng.uniform(-0.04 * strength, 0.04 * strength), rng.uniform(-0.04 * strength, 0.04 * strength)
        result, labels = translate_scale(image, labels, scale, tx, ty)
        far_blur = rng.uniform(0.65, 1.60) * strength
        result = gradient_blur(result, direction, rng.uniform(0, 0.20 * strength), far_blur)
        brightness = rng.uniform(1 - 0.12 * strength, 1 + 0.12 * strength)
        contrast = rng.uniform(1 - 0.07 * strength, 1 + 0.07 * strength)
        result = ImageEnhance.Contrast(ImageEnhance.Brightness(result).enhance(brightness)).enhance(contrast)
        array = np.asarray(result.convert("RGB"), dtype=np.float32)
        noise_std = rng.uniform(0.2, 1.4) * strength
        array += np_rng.normal(0, noise_std, array.shape)
        result = Image.fromarray(np.clip(array, 0, 255).astype(np.uint8), "RGB")
        return result, labels, {"strength": strength, "scale": round(scale, 5), "translate_x": round(tx, 5), "translate_y": round(ty, 5), "focus_direction": direction, "far_blur_px": round(far_blur, 4), "brightness": round(brightness, 4), "contrast": round(contrast, 4), "noise_std": round(noise_std, 4)}

    run_augmentation(context, count, "combined", transform)


if __name__ == "__main__":
    main()
