"""Registers one image onto another (SIFT + RANSAC homography) and reports how well
they line up. Used for then/now pairs and reveal rings (docs/art-pipeline.md §5)."""

from dataclasses import asdict, dataclass

import cv2
import numpy as np

from .imageio import to_bgr


@dataclass
class Registration:
    homography: list[list[float]]  # maps moving -> fixed pixel coordinates
    matches: int
    inliers: int
    residual_median_px: float
    residual_p90_px: float
    scale: float
    rotation_deg: float
    tx_px: float
    ty_px: float
    corner_shift_px: list[float]  # how far the moving image's corners and centre move under the homography

    def to_dict(self) -> dict:
        return asdict(self)


def _features(image: np.ndarray):
    grey = cv2.cvtColor(to_bgr(image), cv2.COLOR_BGR2GRAY)
    # Equalise so a dark ruin and a bright restored scene compare on structure, not brightness.
    grey = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(grey)
    return cv2.SIFT_create(10000).detectAndCompute(grey, None)


def register(fixed: np.ndarray, moving: np.ndarray) -> Registration:
    kp_fixed, des_fixed = _features(fixed)
    kp_moving, des_moving = _features(moving)
    if des_fixed is None or des_moving is None:
        raise ValueError("no features found")
    pairs = cv2.BFMatcher().knnMatch(des_moving, des_fixed, k=2)
    good = [p[0] for p in pairs if len(p) == 2 and p[0].distance < 0.75 * p[1].distance]
    if len(good) < 8:
        raise ValueError(f"only {len(good)} matches; the images may not show the same scene")
    src = np.float32([kp_moving[m.queryIdx].pt for m in good])
    dst = np.float32([kp_fixed[m.trainIdx].pt for m in good])
    homography, mask = cv2.findHomography(src, dst, cv2.RANSAC, 4.0)
    if homography is None:
        raise ValueError("homography estimation failed")
    inlier = mask.ravel() == 1
    projected = cv2.perspectiveTransform(src[inlier].reshape(-1, 1, 2), homography).reshape(-1, 2)
    residuals = np.linalg.norm(projected - dst[inlier], axis=1)
    affine, _ = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=4.0)
    h, w = moving.shape[:2]
    corners = np.float32([[0, 0], [w, 0], [w, h], [0, h], [w / 2, h / 2]]).reshape(-1, 1, 2)
    moved = cv2.perspectiveTransform(corners, homography).reshape(-1, 2)
    return Registration(
        homography=homography.tolist(),
        matches=len(good),
        inliers=int(inlier.sum()),
        residual_median_px=float(np.median(residuals)),
        residual_p90_px=float(np.percentile(residuals, 90)),
        scale=float(np.hypot(affine[0, 0], affine[1, 0])),
        rotation_deg=float(np.degrees(np.arctan2(affine[1, 0], affine[0, 0]))),
        tx_px=float(affine[0, 2]),
        ty_px=float(affine[1, 2]),
        corner_shift_px=[round(float(d), 2) for d in np.linalg.norm(moved - corners.reshape(-1, 2), axis=1)],
    )


def warp(moving: np.ndarray, registration: Registration, size: tuple[int, int]) -> np.ndarray:
    """Warps `moving` into the fixed image's frame. `size` is (width, height)."""
    return cv2.warpPerspective(
        moving,
        np.array(registration.homography, dtype=np.float64),
        size,
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_REPLICATE,
    )
