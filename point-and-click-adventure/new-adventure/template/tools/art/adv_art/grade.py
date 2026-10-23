"""Resizes and grades backgrounds, and measures luminance where the hero walks
(docs/art-pipeline.md §3 rule 3 and §8 gate 3)."""

import cv2
import numpy as np

from .imageio import luminance, to_bgr


def resize(image: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    """Area filter for downscaling (clean, no ringing), Lanczos for upscaling. `size` is (width, height)."""
    h, w = image.shape[:2]
    interpolation = cv2.INTER_AREA if size[0] <= w and size[1] <= h else cv2.INTER_LANCZOS4
    return cv2.resize(image, size, interpolation=interpolation)


def monochrome(image: np.ndarray) -> np.ndarray:
    """Pure greyscale (single channel) from Rec. 709 luma. Present-day images ship this way;
    any tint is applied in the engine (docs/art-pipeline.md §2)."""
    return np.clip(np.rint(luminance(to_bgr(image))), 0, 255).astype(np.uint8)


def saturation_percent(image: np.ndarray) -> float:
    if image.ndim == 2:
        return 0.0
    hls = cv2.cvtColor(to_bgr(image), cv2.COLOR_BGR2HLS)
    return float(hls[:, :, 2].mean() / 255.0 * 100.0)


def region_luminance(image: np.ndarray, mask: np.ndarray) -> dict:
    """Luminance statistics (0–255) inside a mask."""
    values = luminance(image)[mask > 0]
    if values.size == 0:
        raise ValueError("empty region")
    return {
        "mean": round(float(values.mean()), 1),
        "median": round(float(np.median(values)), 1),
        "p10": round(float(np.percentile(values, 10)), 1),
        "p90": round(float(np.percentile(values, 90)), 1),
    }
