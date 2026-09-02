"""Multi-scale edge-information enhancement blocks."""

import torch
import torch.nn as nn
import torch.nn.functional as F

from ..modules.block import C3k, C3k2
from ..modules.conv import Conv

__all__ = ("C3k2_MutilScaleEdgeInformationEnhance",)


class EdgeEnhancer(nn.Module):
    """Enhance local high-frequency information with average-pooling residuals."""

    def __init__(self, in_dim: int):
        super().__init__()
        self.out_conv = Conv(in_dim, in_dim, act=nn.Sigmoid())
        self.pool = nn.AvgPool2d(3, stride=1, padding=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Return input features enhanced by their local high-frequency response."""
        edge = x - self.pool(x)
        return x + self.out_conv(edge)


class MutilScaleEdgeInformationEnhance(nn.Module):
    """Fuse local features with enhanced edge features at multiple scales."""

    def __init__(self, inc: int, bins: tuple[int, ...]):
        super().__init__()
        branch_channels = inc // len(bins)
        self.features = nn.ModuleList(
            nn.Sequential(
                nn.AdaptiveAvgPool2d(bin_size),
                Conv(inc, branch_channels, 1),
                Conv(branch_channels, branch_channels, 3, g=branch_channels),
            )
            for bin_size in bins
        )
        self.ees = nn.ModuleList(EdgeEnhancer(branch_channels) for _ in bins)
        self.local_conv = Conv(inc, inc, 3)
        self.final_conv = Conv(inc * 2, inc)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply local and multi-scale edge branches and fuse their outputs."""
        out = [self.local_conv(x)]
        for enhancer, feature in zip(self.ees, self.features):
            branch = F.interpolate(feature(x), x.shape[2:], mode="bilinear", align_corners=True)
            out.append(enhancer(branch))
        return self.final_conv(torch.cat(out, 1))


class C3k_MutilScaleEdgeInformationEnhance(C3k):
    """C3k block using multi-scale edge-information enhancement."""

    def __init__(self, c1: int, c2: int, n: int = 1, shortcut: bool = False, g: int = 1, e: float = 0.5, k: int = 3):
        super().__init__(c1, c2, n, shortcut, g, e, k)
        hidden_channels = int(c2 * e)
        self.m = nn.Sequential(
            *(MutilScaleEdgeInformationEnhance(hidden_channels, (3, 6, 9, 12)) for _ in range(n))
        )


class C3k2_MutilScaleEdgeInformationEnhance(C3k2):
    """C3k2 block using multi-scale edge-information enhancement."""

    def __init__(
        self,
        c1: int,
        c2: int,
        n: int = 1,
        c3k: bool = False,
        e: float = 0.5,
        g: int = 1,
        shortcut: bool = True,
    ):
        # Ultralytics 8.4 adds ``attn`` before ``g`` in C3k2; keywords keep this custom block API compatible.
        super().__init__(c1=c1, c2=c2, n=n, c3k=c3k, e=e, attn=False, g=g, shortcut=shortcut)
        self.m = nn.ModuleList(
            C3k_MutilScaleEdgeInformationEnhance(self.c, self.c, 2, shortcut, g)
            if c3k
            else MutilScaleEdgeInformationEnhance(self.c, (3, 6, 9, 12))
            for _ in range(n)
        )
