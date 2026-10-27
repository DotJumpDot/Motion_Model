"""Render the Hunyuan-textured GLB for comparison with the bake.

    blender --background --python tools/hunyuan3d/tex_check.py
"""

import os

import bpy
from mathutils import Vector

REPO = "C:/Code/Motion_Model"
GLB = os.path.join(REPO, "tools", "hunyuan3d", "out", "ghost_ai_tex.glb")
OUT_DIR = os.path.join(REPO, "tools", "hunyuan3d", "out")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
print("TEXCHECK: meshes:", [o.name for o in meshes])
for o in meshes:
    for m in o.data.materials:
        if m:
            print("TEXCHECK mat:", m.name,
                  "has tex:", any(n.type == "TEX_IMAGE" and n.image
                                  for n in m.node_tree.nodes))

pts = [o.matrix_world @ Vector(c) for o in meshes
       for c in o.bound_box]
zmin = min(p.z for p in pts)
cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
H = max(p.z for p in pts) - zmin
for o in meshes:
    o.location = (o.location.x - cx, o.location.y - cy,
                  o.location.z - zmin)
print(f"TEXCHECK: height={H:.3f}")

scene = bpy.context.scene
world = bpy.data.worlds.new("w")
world.color = (0.02, 0.02, 0.025)
scene.world = world
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.background_type = "WORLD"

cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
for view, target_z, off, lens, res in (
        ("front", 0.5, (0.2, -1.4, 0.12), 40, (512, 720)),
        ("close", 0.84, (0.45, -1.0, 0.18), 55, (560, 640)),
        ("back", 0.5, (-0.15, 1.4, 0.12), 40, (512, 720))):
    target = Vector((0, 0, target_z * H))
    dist = 1.15 * H
    cam.location = target + Vector(off).normalized() * dist
    look = (target - Vector(cam.location)).normalized()
    cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
    cam_data.lens = lens
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = os.path.join(OUT_DIR, f"tex_{view}.png")
    bpy.ops.render.render(write_still=True)
    print("SAVED", scene.render.filepath)
print("TEXCHECK OK")
