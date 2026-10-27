"""Clay-render the AI-generated mesh for a shape-quality check.

    blender --background --python tools/hunyuan3d/clay_check.py
"""

import os

import bpy
from mathutils import Vector

REPO = "C:/Code/Motion_Model"
GLB = os.path.join(REPO, "tools", "hunyuan3d", "out", "ghost_ai.glb")
OUT_DIR = os.path.join(REPO, "tools", "hunyuan3d", "out")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
print("IMPORTED:", [(o.name, len(o.data.polygons)) for o in meshes])

pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts),
             min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts),
             max(p.z for p in pts)))
center = (lo + hi) / 2
size = hi - lo
print(f"BBOX size: {tuple(round(v, 3) for v in size)}")

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
radius = max(size.length / 2, 0.01)
for view, off in (("front", (0.2, 1.4, 0.1)),
                  ("back", (-0.2, -1.4, 0.1)),
                  ("side", (1.4, 0.15, 0.05))):
    cam.location = center + Vector(off).normalized() * radius * 2.3
    look = (center - Vector(cam.location)).normalized()
    cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x = 512
    scene.render.resolution_y = 720
    scene.render.filepath = os.path.join(OUT_DIR, f"clay_{view}.png")
    bpy.ops.render.render(write_still=True)
    print("SAVED", scene.render.filepath)
print("CLAY CHECK OK")
