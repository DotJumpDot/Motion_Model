"""Render 4 azimuths to find which way the AI mesh faces."""
import math
import os

import bpy
from mathutils import Vector

REPO = "C:/Code/Motion_Model"
GLB = os.path.join(REPO, "tools", "hunyuan3d", "out", "ghost_ai.glb")
OUT_DIR = os.path.join(REPO, "tools", "hunyuan3d", "out")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
src = [o for o in bpy.data.objects if o.type == "MESH"][0]

pts = [src.matrix_world @ Vector(c) for c in src.bound_box]
center = (min(p.x for p in pts) + max(p.x for p in pts)) / 2, \
         (min(p.y for p in pts) + max(p.y for p in pts)) / 2, \
         (min(p.z for p in pts) + max(p.z for p in pts)) / 2
center = Vector(center)
radius = max((max(p.x for p in pts) - min(p.x for p in pts),
              max(p.y for p in pts) - min(p.y for p in pts),
              max(p.z for p in pts) - min(p.z for p in pts))) / 2

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "SINGLE"
scene.display.shading.single_color = (0.6, 0.58, 0.55)
cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
for deg in (0, 90, 180, 270):
    a = math.radians(deg)
    off = Vector((math.sin(a), math.cos(a), 0.08)).normalized()
    cam.location = center + off * radius * 2.4
    look = (center - Vector(cam.location)).normalized()
    cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x = 380
    scene.render.resolution_y = 540
    scene.render.filepath = os.path.join(OUT_DIR, f"az_{deg}.png")
    bpy.ops.render.render(write_still=True)
    print("SAVED az", deg)
print("AZ PROBE OK")
