#!/usr/bin/env python3
"""Interactively simulate transmitted-light and dark-field exposure variation."""

from __future__ import annotations

import math
import random
import numpy as np
from PIL import Image, ImageEnhance

from physical_augmentation_common import interactive_context, prompt_float, run_augmentation


def main() -> None:
    context, count = interactive_context("物理增强 3：透光强度 / 暗场照明不均")
    strength = prompt_float("最大照明变化强度（建议 0.08-0.18）", 0.12, 0.01, 0.35)

    def transform(image: Image.Image, labels: list[list[float]], rng: random.Random, _: np.random.Generator):
        brightness = rng.uniform(1 - strength, 1 + strength)
        contrast = rng.uniform(1 - strength * 0.55, 1 + strength * 0.55)
        result = ImageEnhance.Brightness(image).enhance(brightness)
        result = ImageEnhance.Contrast(result).enhance(contrast)
        array = np.asarray(result.convert("RGB"), dtype=np.float32)
        height, width = array.shape[:2]
        yy, xx = np.mgrid[-1:1:complex(height), -1:1:complex(width)]
        angle = rng.uniform(0, 2 * math.pi)
        plane = (xx * math.cos(angle) + yy * math.sin(angle))
        gradient = 1 + rng.uniform(-strength, strength) * plane
        result = Image.fromarray(np.clip(array * gradient[..., None], 0, 255).astype(np.uint8), "RGB")
        return result, labels, {"brightness": round(brightness, 4), "contrast": round(contrast, 4), "illumination_gradient": round(float(gradient.max() - gradient.min()), 4)}

    run_augmentation(context, count, "transillumination", transform)


if __name__ == "__main__":
    main()
