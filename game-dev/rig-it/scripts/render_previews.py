#!/usr/bin/env python3
"""Render deterministic orthographic review views for an FBX/GLB/Blend model.

Run with Blender, for example:

    blender --background --factory-startup \
      --python tools/3d/render_model_previews.py -- \
      --input model.glb --output-directory previews
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector


VIEW_DIRECTIONS = {
    "front": Vector((0.0, -1.0, 0.0)),
    "back": Vector((0.0, 1.0, 0.0)),
    "left": Vector((-1.0, 0.0, 0.0)),
    "right": Vector((1.0, 0.0, 0.0)),
    "hero": Vector((1.0, -1.0, 0.65)).normalized(),
}


def parse_arguments() -> argparse.Namespace:
    arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--resolution", type=int, default=768)
    parser.add_argument("--action", help="activate this action before rendering")
    parser.add_argument("--frame", type=int, default=1)
    parser.add_argument(
        "--light-scale",
        type=float,
        default=1.0,
        help="multiply the source-material review light energies",
    )
    parser.add_argument(
        "--background-value",
        type=float,
        default=0.015,
        help="linear neutral background value for source-material renders",
    )
    parser.add_argument(
        "--material-mode",
        choices=("clay", "source"),
        default="clay",
        help="use neutral review clay or render the source PBR materials",
    )
    parser.add_argument(
        "--view",
        action="append",
        choices=tuple(VIEW_DIRECTIONS),
        dest="views",
        help="render only this named view; repeat for multiple views",
    )
    return parser.parse_args(arguments)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for block in list(collection):
            if block.users == 0:
                collection.remove(block)


def import_model(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix == ".blend":
        result = bpy.ops.wm.open_mainfile(filepath=str(path))
    elif suffix in {".glb", ".gltf"}:
        result = bpy.ops.import_scene.gltf(
            filepath=str(path),
            disable_bone_shape=True,
        )
    elif suffix == ".fbx":
        result = bpy.ops.import_scene.fbx(filepath=str(path), use_anim=False)
    else:
        raise RuntimeError(f"unsupported model extension {suffix!r}")
    if "FINISHED" not in result:
        raise RuntimeError(f"Blender import failed for {path}: {result}")


def mesh_bounds() -> tuple[Vector, Vector]:
    corners = [
        obj.matrix_world @ Vector(corner)
        for obj in bpy.context.scene.objects
        if obj.type == "MESH"
        for corner in obj.bound_box
    ]
    if not corners:
        raise RuntimeError("imported model contains no mesh objects")
    minimum = Vector(tuple(min(point[axis] for point in corners) for axis in range(3)))
    maximum = Vector(tuple(max(point[axis] for point in corners) for axis in range(3)))
    return minimum, maximum


def configure_animation(action_name: str | None, frame: int) -> None:
    if action_name:
        action = bpy.data.actions.get(action_name)
        if action is None:
            raise RuntimeError(f"source has no action named {action_name!r}")
        rigs = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
        if len(rigs) != 1:
            raise RuntimeError(
                f"action rendering requires one armature, found {len(rigs)}"
            )
        rigs[0].animation_data_create()
        for track in rigs[0].animation_data.nla_tracks:
            track.mute = True
        rigs[0].animation_data.action = action
    bpy.context.scene.frame_set(frame)


def ensure_review_materials() -> None:
    fallback = bpy.data.materials.new("ReviewClay")
    fallback.diffuse_color = (0.22, 0.075, 0.025, 1.0)
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        obj.color = fallback.diffuse_color
        if not obj.data.materials:
            obj.data.materials.append(fallback)
        for material in obj.data.materials:
            if material is not None:
                material.diffuse_color = fallback.diffuse_color


def add_area_light(
    name: str,
    location: Vector,
    center: Vector,
    *,
    energy: float,
    size: float,
) -> None:
    light_data = bpy.data.lights.new(name, type="AREA")
    light_data.energy = energy
    light_data.shape = "DISK"
    light_data.size = size
    light = bpy.data.objects.new(name, light_data)
    bpy.context.scene.collection.objects.link(light)
    light.location = location
    light.rotation_euler = ((center - location).to_track_quat("-Z", "Y")).to_euler()


def configure_scene(
    resolution: int,
    material_mode: str,
    minimum: Vector,
    maximum: Vector,
    light_scale: float,
    background_value: float,
) -> bpy.types.Object:
    scene = bpy.context.scene
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    if material_mode == "clay":
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.display.shading.light = "STUDIO"
        scene.display.shading.studio_light = "paint.sl"
        scene.display.shading.color_type = "MATERIAL"
        scene.display.shading.show_shadows = True
        scene.display.shading.show_cavity = True
        scene.display.shading.cavity_type = "WORLD"
        scene.display.shading.curvature_ridge_factor = 1.5
        scene.display.shading.curvature_valley_factor = 1.0
        scene.display.shading.background_type = "VIEWPORT"
        scene.display.shading.background_color = (0.035, 0.04, 0.05)
    else:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
        scene.render.image_settings.color_mode = "RGB"
        if scene.world is None:
            scene.world = bpy.data.worlds.new("ReviewWorld")
        scene.world.color = (background_value,) * 3
        scene.view_settings.look = "AgX - Medium High Contrast"
        center = (minimum + maximum) * 0.5
        span = max(maximum - minimum)
        add_area_light(
            "ReviewKey",
            center + Vector((-1.8, -2.0, 2.4)) * span,
            center,
            energy=900.0 * span * span * light_scale,
            size=span * 1.5,
        )
        add_area_light(
            "ReviewFill",
            center + Vector((2.2, -0.5, 1.1)) * span,
            center,
            energy=500.0 * span * span * light_scale,
            size=span * 1.8,
        )
        add_area_light(
            "ReviewRim",
            center + Vector((0.0, 2.2, 2.0)) * span,
            center,
            energy=700.0 * span * span * light_scale,
            size=span * 1.2,
        )

    camera_data = bpy.data.cameras.new("ReviewCamera")
    camera_data.type = "ORTHO"
    camera = bpy.data.objects.new("ReviewCamera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    return camera


def projected_span(minimum: Vector, maximum: Vector, direction: Vector) -> float:
    corners = [
        Vector((x, y, z))
        for x in (minimum.x, maximum.x)
        for y in (minimum.y, maximum.y)
        for z in (minimum.z, maximum.z)
    ]
    up = Vector((0.0, 0.0, 1.0))
    if abs(direction.dot(up)) > 0.98:
        up = Vector((0.0, 1.0, 0.0))
    horizontal = direction.cross(up).normalized()
    vertical = horizontal.cross(direction).normalized()
    horizontal_values = [point.dot(horizontal) for point in corners]
    vertical_values = [point.dot(vertical) for point in corners]
    return max(
        max(horizontal_values) - min(horizontal_values),
        max(vertical_values) - min(vertical_values),
    )


def aim_camera(
    camera: bpy.types.Object,
    center: Vector,
    minimum: Vector,
    maximum: Vector,
    direction: Vector,
) -> None:
    extent = maximum - minimum
    distance = max(extent) * 2.5
    camera.location = center + direction * distance
    camera.rotation_euler = ((center - camera.location).to_track_quat("-Z", "Y")).to_euler()
    camera.data.ortho_scale = projected_span(minimum, maximum, direction) * 1.18
    camera.data.clip_start = max(0.001, distance * 0.01)
    camera.data.clip_end = distance * 4.0


def render_views(
    output_directory: Path,
    camera: bpy.types.Object,
    minimum: Vector,
    maximum: Vector,
    views: list[str],
) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    center = (minimum + maximum) * 0.5
    for view in views:
        direction = VIEW_DIRECTIONS[view]
        aim_camera(camera, center, minimum, maximum, direction)
        output = (output_directory / f"preview-{view}.png").resolve()
        bpy.context.scene.render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
        if not output.is_file():
            raise RuntimeError(f"preview render was not created: {output}")
        print(f"Rendered {view}: {output}")


def main() -> int:
    arguments = parse_arguments()
    if arguments.resolution < 64 or arguments.resolution > 4096:
        raise RuntimeError("resolution must be between 64 and 4096")
    if arguments.light_scale <= 0.0:
        raise RuntimeError("light scale must be positive")
    if arguments.background_value < 0.0 or arguments.background_value > 1.0:
        raise RuntimeError("background value must be between 0 and 1")
    input_path = arguments.input.resolve()
    if not input_path.is_file():
        raise RuntimeError(f"input does not exist: {input_path}")
    clear_scene()
    import_model(input_path)
    configure_animation(arguments.action, arguments.frame)
    minimum, maximum = mesh_bounds()
    if not all(math.isfinite(value) for value in (*minimum, *maximum)):
        raise RuntimeError("model bounds contain non-finite values")
    if arguments.material_mode == "clay":
        ensure_review_materials()
    camera = configure_scene(
        arguments.resolution,
        arguments.material_mode,
        minimum,
        maximum,
        arguments.light_scale,
        arguments.background_value,
    )
    views = arguments.views or list(VIEW_DIRECTIONS)
    render_views(arguments.output_directory.resolve(), camera, minimum, maximum, views)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
