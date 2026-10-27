"""Render quick CPU previews of the exported FBX (Workbench engine).

Headless run:
    blender --background --python src/blender/render_check.py

No GPU involved — Workbench is a CPU viewport shading pass used to
eyeball shapes and textures. Writes assets/preview/<name>_<view>.png
(full body + face close-up per character, dark background + cavity
shading for mood).
"""

import os

import bpy
from mathutils import Vector

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TARGETS = [
    ("GhostWoman", os.path.join(REPO, "assets", "fbx", "Ghost_Woman.fbx"),
     1.50),   # z of the face for the close-up
    ("Krasue", os.path.join(REPO, "assets", "fbx", "Krasue.fbx"), 1.64),
]
# camera offset direction (x, y, z) relative to the target point
VIEWS = {"front": (0.20, 1.35, 0.05), "close": (0.50, 1.05, 0.22)}


def setup_cam(name, target, off, dist, out, lens=40):
    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.location = Vector(target) + Vector(off).normalized() * dist
    look = (Vector(target) - Vector(cam.location)).normalized()
    cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
    cam_data.lens = lens
    bpy.context.scene.render.filepath = out


def render_one(label, path, face_z):
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

    world = bpy.data.worlds.new("dark")
    world.color = (0.015, 0.015, 0.02)
    scene.world = world

    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "TEXTURE"
    scene.display.shading.background_type = "WORLD"
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"

    out_dir = os.path.join(REPO, "assets", "preview")
    os.makedirs(out_dir, exist_ok=True)
    for view, off in VIEWS.items():
        if view == "front":
            target, dist = (center.x, center.y, center.z), radius * 2.6
            scene.render.resolution_x = 512
            scene.render.resolution_y = 720
            setup_cam(label, target, off, dist, out_dir and
                      os.path.join(out_dir, f"{label}_{view}.png"), 40)
        else:
            target = (center.x, center.y, face_z)
            dist = 0.75
            scene.render.resolution_x = 560
            scene.render.resolution_y = 640
            setup_cam(label, target, off, dist,
                      os.path.join(out_dir, f"{label}_{view}.png"), 55)
        bpy.ops.render.render(write_still=True)
        print(f"RENDER {label}_{view} -> "
              f"{scene.render.filepath}")


for label, path, face_z in TARGETS:
    render_one(label, path, face_z)
print("RENDER CHECK OK")
