"""Export the decimated, origin-normalized ghost mesh for texgen.

    blender --background --python tools/hunyuan3d/export_8k.py

Same steps as rig_ghost's stage 1 (import Hunyuan GLB, decimate to
the tri budget, origin at feet) but WITHOUT rig/texture — the paint
pipeline needs the final-resolution mesh, because decimating after
painting scrambles the xatlas UVs.
"""

import os

import bpy
from mathutils import Matrix, Vector

REPO = "C:/Code/Motion_Model"
GLB = os.path.join(REPO, "tools", "hunyuan3d", "out", "ghost_ai.glb")
OUT = os.path.join(REPO, "tools", "hunyuan3d", "out", "ghost_ai_8k.glb")
TRI_BUDGET = 8000

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
src = [o for o in bpy.data.objects if o.type == "MESH"][0]
bpy.context.view_layer.objects.active = src
src.select_set(True)
n_tris = sum(len(p.vertices) - 2 for p in src.data.polygons)
mod = src.modifiers.new("dec", "DECIMATE")
mod.ratio = TRI_BUDGET / max(n_tris, 1)
bpy.ops.object.modifier_apply(modifier="dec")

pts = [src.matrix_world @ Vector(c) for c in src.bound_box]
zmin = min(p.z for p in pts)
cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
src.data.transform(Matrix.Translation((-cx, -cy, -zmin)))
src.matrix_world = Matrix.Identity(4)

bpy.ops.object.select_all(action="DESELECT")
src.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB",
                          export_materials="NONE")
n = sum(len(p.vertices) - 2 for p in src.data.polygons)
print(f"EXPORT8K: {n} tris -> {OUT}")
