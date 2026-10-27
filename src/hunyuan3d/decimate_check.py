"""Decimate the AI mesh and check quality at target budgets.

    blender --background --python tools/hunyuan3d/decimate_check.py

Renders clay previews at 5k and 10k tris to pick the budget.
"""

import os

import bpy
import bmesh
from mathutils import Vector

REPO = "C:/Code/Motion_Model"
GLB = os.path.join(REPO, "tools", "hunyuan3d", "out", "ghost_ai.glb")
OUT_DIR = os.path.join(REPO, "tools", "hunyuan3d", "out")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
src = [o for o in bpy.data.objects if o.type == "MESH"][0]

pts = [src.matrix_world @ Vector(c) for c in src.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts),
             min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts),
             max(p.z for p in pts)))
center = (lo + hi) / 2
radius = max((hi - lo).length / 2, 0.01)

scene = bpy.context.scene
world = bpy.data.worlds.new("w")
world.color = (0.02, 0.02, 0.025)
scene.world = world
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "SINGLE"
scene.display.shading.single_color = (0.55, 0.53, 0.50)
scene.display.shading.background_type = "WORLD"
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "BOTH"

cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = center + Vector((0.2, 1.4, 0.1)).normalized() * radius * 2.3
look = (center - Vector(cam.location)).normalized()
cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
scene.render.resolution_x = 512
scene.render.resolution_y = 720


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


for target in (5000, 10000):
    obj = src.copy()
    obj.data = src.data.copy()
    scene.collection.objects.link(obj)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    ratio = target / max(tris(src), 1)
    mod = obj.modifiers.new("dec", "DECIMATE")
    mod.ratio = ratio
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="dec")
    n = tris(obj)
    scene.render.filepath = os.path.join(OUT_DIR, f"dec_{n // 1000}k.png")
    bpy.ops.render.render(write_still=True)
    print(f"DECIMATED target={target} actual={n} -> {scene.render.filepath}")
    bpy.data.objects.remove(obj, do_unlink=True)
print("DECIMATE CHECK OK")
