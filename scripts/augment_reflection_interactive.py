#!/usr/bin/env python3
"""Interactively simulate weak, smooth reflection/highlight variation on coated optics."""

from __future__ import annotations

import random
import numpy as np
from PIL import Image

from physical_augmentation_common import interactive_context, prompt_float, run_augmentation


def main() -> None:
    context, count = interactive_context("物理增强 4：镀膜反射 / 局部高光背景变化")
    max_strength = prompt_float("最大局部反光增益（建议 0.05-0.15）", 0.10, 0.01, 0.25)

    def transform(image: Image.Image, labels: list[list[float]], rng: random.Random, _: np.random.Generator):
        array = np.asarray(image.convert("RGB"), dtype=np.float32)
        height, width = array.shape[:2]
        yy, xx = np.mgrid[0:height, 0:width]
        cx, cy = rng.uniform(0.15, 0.85) * width, rng.uniform(0.15, 0.85) * height
        sx, sy = rng.uniform(0.18, 0.42) * width, rng.uniform(0.10, 0.30) * height
        strength = rng.uniform(max_strength * 0.35, max_strength)
        halo = strength * np.exp(-0.5 * (((xx - cx) / sx) ** 2 + ((yy - cy) / sy) ** 2))
        result = Image.fromarray(np.clip(array * (1 + halo[..., None]), 0, 255).astype(np.uint8), "RGB")
        return result, labels, {"highlight_x": round(cx / width, 4), "highlight_y": round(cy / height, 4), "strength": round(strength, 4)}

    run_augmentation(context, count, "reflection", transform)


if __name__ == "__main__":
    main()
