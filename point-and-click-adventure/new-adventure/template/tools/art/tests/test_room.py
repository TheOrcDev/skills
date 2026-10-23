"""The room builder's effects presets (plan 008 slice 2)."""

from adv_art import room


def test_exterior_preset_fills_light_depth_and_adds_mist_and_then():
    fx = room.effects({"effects": {"preset": "exterior", "light": [100, 50], "aim": 200}}, "res://r/art", has_then=True)
    names = [(entry["era"], entry["name"]) for entry in fx]
    assert ("now", "Moonlight") in names and ("now", "GroundMist") in names and ("then", "GoldenShafts") in names
    moon = next(entry for entry in fx if entry["name"] == "Moonlight")
    assert moon["properties"]["origin"] == [100, 50] and moon["properties"]["aim"] == 200.0
    far = next(entry for entry in fx if entry["name"] == "FogFar")
    assert far["properties"]["depth_texture"] == "res://r/art/depth_now.png"
    assert next(entry for entry in fx if entry["name"] == "GroundMist")["layer"] == "foreground"


def test_no_past_no_then_effects_and_extras_kept():
    extra = {"type": "DustMotes", "name": "Moths", "era": "now", "properties": {}}
    fx = room.effects({"effects": {"preset": "interior", "ground_mist": False, "extra": [extra]}}, "res://r/art", has_then=False)
    assert all(entry["era"] == "now" for entry in fx)
    assert not any(entry["name"] == "GroundMist" for entry in fx)
    assert fx[-1] == extra
