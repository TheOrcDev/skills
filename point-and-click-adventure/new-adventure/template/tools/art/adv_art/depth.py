"""Depth maps with Depth Anything V2 Small, run locally (Apple MPS when available).
Needs the optional extra: `uv sync --extra depth`."""

import numpy as np

MODEL = "depth-anything/Depth-Anything-V2-Small-hf"


def estimate(image_bgr: np.ndarray) -> np.ndarray:
    """Relative depth as uint16, normalised so 65535 is nearest and 0 farthest."""
    import torch
    from PIL import Image
    from transformers import pipeline

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    estimator = pipeline("depth-estimation", model=MODEL, device=device)
    rgb = Image.fromarray(image_bgr[:, :, ::-1] if image_bgr.ndim == 3 else image_bgr)
    result = estimator(rgb)
    depth = np.asarray(result["predicted_depth"].squeeze().cpu().numpy(), dtype=np.float32)
    import cv2

    depth = cv2.resize(depth, (rgb.width, rgb.height), interpolation=cv2.INTER_CUBIC)
    depth -= depth.min()
    depth /= max(float(depth.max()), 1e-6)
    return np.rint(depth * 65535.0).astype(np.uint16)
