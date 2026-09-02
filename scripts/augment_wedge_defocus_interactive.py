#!/usr/bin/env python3
"""Interactively simulate non-uniform defocus produced by a tilted wedge filter."""

from __future__ import annotations

import random
import numpy as np
from PIL import Image

from physical_augmentation_common import gradient_blur, interactive_context, prompt_choice, prompt_float, run_augmentation


def main() -> None:
    context, count = interactive_context("物理增强 2：楔形倾斜表面的非均匀离焦")
    direction = prompt_choice("楔形厚度/焦面梯度方向", ("vertical", "horizontal", "diagonal"), "vertical")
    max_blur = prompt_float("最强端高斯模糊半径（像素，建议 0.8-2.0）", 1.4, 0.1, 4.0)
    min_blur = prompt_float("清晰端高斯模糊半径（像素，建议 0.0-0.4）", 0.15, 0.0, max_blur)

    def transform(image: Image.Image, labels: list[list[float]], rng: random.Random, _: np.random.Generator):
        far = rng.uniform(max_blur * 0.65, max_blur)
        near = rng.uniform(0, min(min_blur, far))
        return gradient_blur(image, direction, near, far), labels, {"direction": direction, "near_blur_px": round(near, 4), "far_blur_px": round(far, 4)}

    run_augmentation(context, count, "wedge_defocus", transform)


if __name__ == "__main__":
    main()
