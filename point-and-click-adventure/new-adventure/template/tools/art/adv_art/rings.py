"""Prepares nested reveal rings (docs/art-pipeline.md §5B): each inner ring is
registered onto the outer ring's matching region, level-matched to it so the
crossfade doesn't pop, and given feathered alpha edges."""

import cv2
import numpy as np

from .align import Registration, register, warp
from .grade import resize
from .imageio import to_bgr


def match_levels(image: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Matches each channel's mean and standard deviation to `reference`."""
    src = to_bgr(image).astype(np.float32)
    ref = to_bgr(reference).astype(np.float32)
    out = np.empty_like(src)
    for c in range(3):
        s_mean, s_std = src[:, :, c].mean(), src[:, :, c].std() + 1e-6
        r_mean, r_std = ref[:, :, c].mean(), ref[:, :, c].std()
        out[:, :, c] = (src[:, :, c] - s_mean) * (r_std / s_std) + r_mean
    return np.clip(np.rint(out), 0, 255).astype(np.uint8)


def feather_alpha(size: tuple[int, int], fraction: float) -> np.ndarray:
    """Alpha that ramps from 0 at the border to 255 at `fraction` of the shorter side inwards."""
    w, h = size
    ramp = max(1.0, fraction * min(w, h))
    xs = np.minimum(np.arange(w), np.arange(w)[::-1]).astype(np.float32)
    ys = np.minimum(np.arange(h), np.arange(h)[::-1]).astype(np.float32)
    distance = np.minimum.outer(ys, xs)
    t = np.clip(distance / ramp, 0.0, 1.0)
    return np.rint(255.0 * t * t * (3.0 - 2.0 * t)).astype(np.uint8)


def prepare_ring(outer: np.ndarray, inner: np.ndarray, rect: tuple[int, int, int, int], feather: float = 0.08) -> tuple[np.ndarray, Registration]:
    """`rect` (x, y, width, height) is where `inner` sits in `outer`'s pixels.
    Returns the inner ring as BGRA in its own resolution, aligned to the outer region."""
    x, y, w, h = rect
    ih, iw = inner.shape[:2]
    region = resize(to_bgr(outer)[y : y + h, x : x + w], (iw, ih))
    registration = register(region, inner)
    aligned = warp(to_bgr(inner), registration, (iw, ih))
    leveled = match_levels(aligned, region)
    return np.dstack([leveled, feather_alpha((iw, ih), feather)]), registration


def zoom_scale(level: int) -> float:
    """World scale of ring `level` when ring 0 is drawn at 1: each ring is half the size of the one outside it."""
    return 0.5**level


def blend_preview(outer: np.ndarray, ring_rgba: np.ndarray, rect: tuple[int, int, int, int]) -> np.ndarray:
    """The ring composited over the outer image at `rect`, for checking seams by eye."""
    x, y, w, h = rect
    out = to_bgr(outer).copy()
    ring = cv2.resize(ring_rgba, (w, h), interpolation=cv2.INTER_AREA)
    alpha = ring[:, :, 3:4].astype(np.float32) / 255.0
    out[y : y + h, x : x + w] = np.rint(ring[:, :, :3] * alpha + out[y : y + h, x : x + w] * (1 - alpha)).astype(np.uint8)
    return out
