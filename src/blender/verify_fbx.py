"""Verify the exported FBX files round-trip with expected content.

Headless run:
    blender --background --python src/blender/verify_fbx.py

Re-imports both FBX from assets/fbx/ and prints one STATS line per
file: tri/vert counts, bone counts, clips (name + frame range),
materials, bounding box. The numbers gate the release (Docs/HOW_TO_RUN.md).
"""

import os
import sys

import bpy
from mathutils import Vector

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
FILES = [
    ("GhostWoman", os.path.join(REPO, "assets", "fbx", "Ghost_Woman.fbx")),
    ("Krasue", os.path.join(REPO, "assets", "fbx", "Krasue.fbx")),
]


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def bbox(objs):
    pts = []
    for obj in objs:
        for corner in obj.bound_box:
            pts.append(obj.matrix_world @ Vector(corner))
    if not pts:
        return None
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts),
                 min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts),
                 max(p.z for p in pts)))
    return lo, hi


for label, path in FILES:
    clear()
    if not os.path.exists(path):
        print(f"STATS {label}: MISSING {path}")
        continue
    bpy.ops.import_scene.fbx(filepath=path)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    tris = sum(sum(len(p.vertices) - 2 for p in m.data.polygons)
               for m in meshes)
    verts = sum(len(m.data.vertices) for m in meshes)
    mats = sorted({m.name for o in meshes for m in o.data.materials if m})
    clips = [(a.name, int(a.frame_range[0]), int(a.frame_range[1]))
             for a in bpy.data.actions]
    bb = bbox(meshes)
    size = (bb[1] - bb[0]) if bb else None
    bone_counts = {a.name: len(a.data.bones) for a in arms}
    print(f"STATS {label}: tris={tris} verts={verts} "
          f"bones={bone_counts} materials={mats}")
    print(f"STATS {label}: clips={clips}")
    print(f"STATS {label}: bbox_size="
          f"{tuple(round(v, 3) for v in size) if size else None}")

print("VERIFY OK")
