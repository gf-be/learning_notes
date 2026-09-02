#!/usr/bin/env python3
"""Interactively simulate sample placement and microscope field-position shifts."""

from __future__ import annotations

import random
import numpy as np
from PIL import Image

from physical_augmentation_common import interactive_context, prompt_float, run_augmentation, translate_scale


def main() -> None:
    context, count = interactive_context("物理增强 1：显微视场位置偏移 / 放大率微扰")
    max_shift = prompt_float("最大横纵位移（图像宽高比例，建议 0.02-0.06）", 0.04, 0.0, 0.12)
    max_scale = prompt_float("最大放大率偏差（建议 0.01-0.04）", 0.025, 0.0, 0.10)

    def transform(image: Image.Image, labels: list[list[float]], rng: random.Random, _: np.random.Generator):
        scale = rng.uniform(1 - max_scale, 1 + max_scale)
        tx, ty = rng.uniform(-max_shift, max_shift), rng.uniform(-max_shift, max_shift)
        image, labels = translate_scale(image, labels, scale, tx, ty)
        return image, labels, {"scale": round(scale, 5), "translate_x": round(tx, 5), "translate_y": round(ty, 5)}

    run_augmentation(context, count, "position", transform)


if __name__ == "__main__":
    main()
