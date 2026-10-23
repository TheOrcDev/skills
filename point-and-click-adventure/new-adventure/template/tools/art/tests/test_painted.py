"""Painted character frames (plan 010): the guide layout and its inverse, the
key nearest a pose, painted eyes deciding the eye anchors, and standing a
painted figure on the guide's soles."""

import numpy as np

from adv_art import painted


def test_cell_to_frame_inverts_the_guide_layout():
    crop = [34, 125, 380, 520]
    scale, pad_x, pad_y = painted.fit(crop)
    back = painted.cell_to_frame(crop)
    for frame_point in ([34.0, 125.0], [224.0, 617.0], [300.0, 400.0]):
        cell = [(frame_point[0] - crop[0]) * scale + pad_x, (frame_point[1] - crop[1]) * scale + pad_y]
        mapped = back @ np.array([cell[0], cell[1], 1.0])
        assert np.allclose(mapped, frame_point, atol=1e-3)


def test_a_squeeze_narrows_about_the_crops_centre_and_keeps_heights():
    matrix = painted.squeeze_matrix({"squeeze": 0.8}, [100, 0, 200, 400])
    anchors = painted.squeeze_anchors({"head": [300.0, 50.0], "feet": [200.0, 400.0], "eyes_visible": [True, False]}, matrix)
    assert anchors["feet"] == [200.0, 400.0]
    assert np.isclose(anchors["head"][0], 280.0) and anchors["head"][1] == 50.0
    assert anchors["eyes_visible"] == [True, False]


def test_each_frame_takes_the_key_nearest_its_pose():
    rest = {"head": [0, 0], "hand_l": [0, 100], "hand_r": [0, 100]}
    reach = {"head": [0, 0], "hand_l": [0, 100], "hand_r": [80, 40]}
    keys = [("idle", rest), ("reach", reach)]
    assert painted.nearest_key({"head": [0, 0], "hand_l": [0, 100], "hand_r": [10, 90]}, keys) == "idle"
    assert painted.nearest_key({"head": [0, 0], "hand_l": [0, 100], "hand_r": [70, 50]}, keys) == "reach"


def test_painted_eyes_decide_where_and_whether_eyes_show():
    rig = {"eye_l": [1, 1], "eye_r": [2, 2], "eyes_visible": [False, True]}
    assert painted.place_eyes(rig, [], "r")["eyes_visible"] == [False, False]
    profile = painted.place_eyes(rig, [(50.0, 60.0, 4.0)], "r")
    assert profile["eye_r"] == [50.0, 60.0] and profile["eyes_visible"] == [False, True]
    front = painted.place_eyes(rig, [(90.0, 60.0, 4.0), (70.0, 61.0, 4.0)], "d")
    assert front["eye_r"] == [70.0, 61.0] and front["eye_l"] == [90.0, 60.0] and front["eyes_visible"] == [True, True]
    assert painted.place_eyes(rig, [(1.0, 1.0, 1.0)], "u")["eyes_visible"] == [False, False]


def test_registration_stands_the_figure_on_the_guides_soles():
    guide = np.zeros((300, 200), np.uint8)
    guide[100:250, 80:120] = 255  # a figure whose soles are at row 249
    figure = np.zeros((300, 200, 4), np.uint8)
    figure[90:236, 95:135, 3] = 255  # 13 rows higher and 15 columns right
    assert painted.register(figure, guide, 249.0) == (-15, 14)
