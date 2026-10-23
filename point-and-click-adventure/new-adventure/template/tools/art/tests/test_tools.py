import json

import cv2
import numpy as np
import pytest

from adv_art import align, grade, masks, pack, rings
from adv_art.cli import main
from adv_art.imageio import load, save


def texture(w: int = 640, h: int = 400, seed: int = 7) -> np.ndarray:
    """A detailed synthetic image with plenty of corners for SIFT."""
    rng = np.random.default_rng(seed)
    noise = rng.integers(0, 256, (h // 8, w // 8, 3), dtype=np.uint8)
    image = cv2.resize(noise, (w, h), interpolation=cv2.INTER_CUBIC)
    for _ in range(60):
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        cv2.circle(image, (x, y), int(rng.integers(4, 18)), tuple(int(v) for v in rng.integers(0, 256, 3)), -1)
    return image


def shifted(image: np.ndarray, dx: float, dy: float, angle: float = 0.0) -> np.ndarray:
    h, w = image.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    m[:, 2] += (dx, dy)
    return cv2.warpAffine(image, m, (w, h), borderMode=cv2.BORDER_REFLECT)


def test_register_recovers_a_small_shift_and_rotation():
    fixed = texture()
    moving = shifted(fixed, 6, -4, angle=0.8)
    registration = align.register(fixed, moving)
    assert registration.residual_p90_px < 1.0
    assert abs(registration.rotation_deg - 0.8) < 0.1  # maps moving back onto fixed
    warped = align.warp(moving, registration, (fixed.shape[1], fixed.shape[0]))
    error = np.abs(warped[40:-40, 40:-40].astype(int) - fixed[40:-40, 40:-40].astype(int)).mean()
    assert error < 6


def test_monochrome_and_resize():
    image = texture()
    mono = grade.monochrome(grade.resize(image, (320, 200)))
    assert mono.shape == (200, 320)
    assert grade.saturation_percent(mono) == 0.0
    assert grade.saturation_percent(image) > 10


def test_region_luminance_reads_inside_the_mask_only():
    image = np.zeros((100, 100), np.uint8)
    image[50:, :] = 200
    stats = grade.region_luminance(image, masks.polygon_mask((100, 100), [[0, 60], [100, 60], [100, 100], [0, 100]]))
    assert stats["median"] == pytest.approx(200, abs=1)


def test_cut_returns_rgba_and_its_box():
    image = texture(200, 100)
    rgba, rect = masks.cut(image, masks.polygon_mask((200, 100), [[20, 10], [80, 10], [80, 60], [20, 60]]))
    assert rgba.shape[2] == 4
    assert rect[0] == pytest.approx(20, abs=1) and rect[1] == pytest.approx(10, abs=1)
    assert rect[2] == pytest.approx(61, abs=2) and rect[3] == pytest.approx(51, abs=2)


def test_prepare_ring_aligns_levels_and_feathers():
    outer = texture(1024, 640)
    rect = (256, 160, 512, 320)
    x, y, w, h = rect
    true_inner = cv2.resize(outer[y : y + h, x : x + w], (1024, 640), interpolation=cv2.INTER_CUBIC)
    inner = cv2.convertScaleAbs(shifted(true_inner, 5, 3), alpha=1.2, beta=15)  # misaligned and brighter
    ring, registration = rings.prepare_ring(outer, inner, rect)
    assert registration.residual_p90_px < 1.5
    assert ring.shape == (640, 1024, 4)
    assert ring[0, 0, 3] == 0 and ring[320, 512, 3] == 255
    core = (slice(80, -80), slice(80, -80))
    assert abs(float(ring[core][:, :, :3].mean()) - float(true_inner[core].mean())) < 6


def test_cli_align_fails_above_the_threshold(tmp_path):
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    fixed = texture()
    cv2.imwrite(str(a), fixed)
    cv2.imwrite(str(b), shifted(fixed, 3, 2))
    assert main(["align", "--fixed", str(a), "--moving", str(b), "--max-p90", "3"]) == 0
    assert main(["align", "--fixed", str(a), "--moving", str(b), "--max-p90", "0.0001"]) == 1


def test_pack_trims_frames_and_records_regions(tmp_path):
    renders = tmp_path / "renders"
    frames = []
    for index in range(3):
        image = np.zeros((200, 160, 4), np.uint8)
        image[80:110, 60 + index : 70 + index, 3] = 255
        save(renders / "walk_r" / f"walk_r_{index:03d}.png", image)
        frames.append(f"walk_r_{index:03d}.png")
    anchors = [{"feet": [20.0, 50.0]}] * 3
    meta = {"frame_size": [160, 200], "character_px": 30, "fps": 12.0,
            "animations": {"walk_r": {"frames": frames, "loop": True, "anchors": anchors, "ground_px_per_second": 10.0}}}
    (renders / "anchors.json").write_text(json.dumps(meta))
    manifest = pack.pack([renders], tmp_path / "out", tmp_path / "m.json", "res://x", "hero")
    walk = manifest["animations"]["walk_r"]
    assert walk["fps"] == 12.0 and walk["ground_px_per_second"] == 10.0
    sheet = load(tmp_path / "out" / "hero_walk_r.png")
    assert sheet.ndim == 2  # one byte per pixel
    for index, frame in enumerate(walk["frames"]):
        x, y, w, h = frame["region"]
        ox, oy = frame["offset"]
        assert (ox, oy, w, h) == (60 + index - pack.BORDER, 80 - pack.BORDER, 10 + 2 * pack.BORDER, 30 + 2 * pack.BORDER)
        region = sheet[y : y + h, x : x + w]
        assert region[pack.BORDER : -pack.BORDER, pack.BORDER : -pack.BORDER].min() == 255
        assert region[: pack.BORDER].max() == 0


def test_grey_alpha_png_round_trips(tmp_path):
    grey = np.arange(48, dtype=np.uint8).reshape(6, 8) * 5
    alpha = (255 - grey).astype(np.uint8)
    from adv_art.imageio import save_grey_alpha
    save_grey_alpha(tmp_path / "la.png", grey, alpha)
    back = cv2.imread(str(tmp_path / "la.png"), cv2.IMREAD_UNCHANGED)
    assert back.shape == (6, 8, 4)  # OpenCV reads grey + alpha as BGRA
    assert np.array_equal(back[:, :, 0], grey) and np.array_equal(back[:, :, 3], alpha)



def test_the_stand_in_hero_packs_like_rig_renders(tmp_path):
    from adv_art import placeholder

    summary = placeholder.build(tmp_path / "hero", ("r",))
    assert summary["animations"] == 12
    manifest = pack.pack([tmp_path / "hero/renders", tmp_path / "hero/renders-walk"], tmp_path / "out", tmp_path / "m.json", "res://x", "hero", shaded=True)
    walk = manifest["animations"]["walk_r"]
    assert walk["fps"] == 8.0 and walk["loop"] and len(walk["frames"]) == 8
    assert walk["ground_px_per_second"] > 0
    assert [e["name"] for e in walk["events"]] == ["step", "step"]
    assert set(walk["anchors"][0]) >= {"head", "eye_l", "eye_r", "hand_l", "hand_r", "feet", "eyes_visible"}
    assert manifest["animations"]["pickup_low_r"]["events"] == [{"frame": 11, "name": "grab"}]
