"""Polygon masks and RGBA cut-outs (walk-behind occluders, layers)."""

import cv2
import numpy as np

from .imageio import to_bgr


def polygon_mask(size: tuple[int, int], polygon: list[list[float]], feather_px: float = 0.0) -> np.ndarray:
    """A uint8 mask (255 inside) of `size` (width, height), optionally feathered with a Gaussian."""
    mask = np.zeros((size[1], size[0]), dtype=np.uint8)
    cv2.fillPoly(mask, [np.round(np.array(polygon, dtype=np.float32)).astype(np.int32)], 255, lineType=cv2.LINE_AA)
    if feather_px > 0:
        mask = cv2.GaussianBlur(mask, (0, 0), sigmaX=feather_px)
    return mask


def scale_polygon(polygon: list[list[float]], factor: float) -> list[list[float]]:
    return [[x * factor, y * factor] for x, y in polygon]


def cut(image: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """The masked part of `image` as BGRA, cropped to the mask's bounding box.
    Returns (rgba, (x, y, width, height)) with the box in source pixels."""
    ys, xs = np.nonzero(mask)
    if xs.size == 0:
        raise ValueError("empty mask")
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1
    bgr = to_bgr(image)[y0:y1, x0:x1]
    rgba = np.dstack([bgr, mask[y0:y1, x0:x1]])
    return rgba, (x0, y0, x1 - x0, y1 - y0)
