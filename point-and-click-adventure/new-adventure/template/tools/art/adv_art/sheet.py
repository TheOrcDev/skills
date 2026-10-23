"""Contact sheets for reviewing variants side by side."""

import cv2
import numpy as np

from .grade import resize
from .imageio import to_bgr


def contact_sheet(images: list[np.ndarray], labels: list[str], columns: int, tile: tuple[int, int], background: int = 32) -> np.ndarray:
    """A grid of `tile`-sized (width, height) thumbnails with a label under each."""
    w, h = tile
    label_h = 36
    rows = (len(images) + columns - 1) // columns
    sheet = np.full((rows * (h + label_h + 8) + 8, columns * (w + 8) + 8, 3), background, dtype=np.uint8)
    for index, (image, label) in enumerate(zip(images, labels)):
        r, c = divmod(index, columns)
        x, y = 8 + c * (w + 8), 8 + r * (h + label_h + 8)
        bgr = to_bgr(image)
        if bgr.shape[2] == 3 and image.ndim == 3 and image.shape[2] == 4:
            alpha = image[:, :, 3:4].astype(np.float32) / 255.0
            bgr = np.rint(bgr * alpha + 138 * (1 - alpha)).astype(np.uint8)
        sheet[y : y + h, x : x + w] = resize(bgr, (w, h))
        cv2.putText(sheet, label, (x + 4, y + h + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (235, 235, 235), 2, cv2.LINE_AA)
    return sheet
