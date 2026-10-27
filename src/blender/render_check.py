"""Render quick CPU previews of the exported FBX (Workbench engine).

Headless run:
    blender --background --python src/blender/render_check.py

No GPU involved — Workbench is a CPU viewport shading pass used only
to eyeball the shapes. Writes assets/preview/<name>.png.
"""

import math
import os

import bpy
from mathutils import Vector

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TARGETS = [
    ("GhostWoman", os.path.join(REPO, "assets", "fbx", "Ghost_Woman.fbx")),
    ("Krasue", os.path.join(REPO, "assets", "fbx", "Krasue.fbx")),
]
LOOK_FROM = {  # camera offset direction relative to the subject centre
    "GhostWoman": (0.75, 1.35, 0.25),
    "Krasue": (0.75, 1.35, 0.30),
}


def render_one(label, path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    scene = bpy.context.scene

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts),
                 min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts),
                 max(p.z for p in pts)))
    center = (lo + hi) / 2
    radius = max((hi - lo).length / 2, 0.01)

    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    scene.camera = cam
    off = Vector(LOOK_FROM[label]).normalized() * radius * 2.2
    cam.location = center + off
    look = (center - Vector(cam.location)).normalized()
    cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
    cam_data.lens = 50

    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.render.resolution_x = 640
    scene.render.resolution_y = 720
    out_dir = os.path.join(REPO, "assets", "preview")
    os.makedirs(out_dir, exist_ok=True)
    scene.render.filepath = os.path.join(out_dir, f"{label}.png")
    bpy.ops.render.render(write_still=True)
    print(f"RENDER {label} -> {scene.render.filepath}")


for label, path in TARGETS:
    render_one(label, path)
print("RENDER CHECK OK")
