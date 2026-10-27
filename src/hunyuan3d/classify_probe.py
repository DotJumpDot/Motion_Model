"""Classify the AI ghost mesh into hair / skin / robe regions.

    blender --background --python tools/hunyuan3d/classify_probe.py

Same import path as rig_ghost.py (ghost_ai.glb -> decimate -> origin
at feet), then labels every vertex:
- HAIR: dark pixels in the reference photo at the vertex's projection
  (the photo's black curtains/drape), or back-facing verts inside the
  center-back drape column.
- SKIN: pale front-facing pixels inside the narrow face column.
- ROBE: everything else.

Labels are written as a vertex-color attribute ("mask": R=hair,
G=skin) and rendered as debug views (front / back / head close-up) for
threshold tuning. rig_ghost.py reuses the same rules for the texture
bake and the hair-bone skinning gates.
"""

import os
import sys

import bpy
import numpy as np
from mathutils import Vector

REPO = "C:/Code/Motion_Model"
OUT_DIR = os.path.join(REPO, "tools", "hunyuan3d", "out")
GLB = os.path.join(OUT_DIR, "ghost_ai.glb")
REF_IMG = os.path.join(OUT_DIR, "input_clean.png")
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
src.data.transform(__import__("mathutils").Matrix.Translation(
    (-cx, -cy, -zmin)))
src.matrix_world = __import__("mathutils").Matrix.Identity(4)
H = max(v.co.z for v in src.data.vertices)
print(f"PROBE: height={H:.3f}")

# ---- photo luminance sampler (same alignment as the v0.4 bake) --------

ref = bpy.data.images.load(REF_IMG)
w, h = ref.size
px = np.array(ref.pixels[:], dtype=np.float32).reshape(h, w, 4)
alpha = px[:, :, 3] > 0.1
cols = np.where(alpha.any(axis=0))[0]
rows = np.where(alpha.any(axis=1))[0]
gx0, gx1 = cols[0] / w, (cols[-1] + 1) / w
gy0, gy1 = rows[0] / h, (rows[-1] + 1) / h
xs = [v.co.x for v in src.data.vertices]
ww = max(xs) - min(xs)
gcx = (gx0 + gx1) / 2
SU = -(gx1 - gx0) / ww          # mirrored: viewer's left is +X
CV = gy0
SV = (gy1 - gy0) / H


def photo_sample(u, v):
    """Nearest-photo-pixel RGB (0..1) at uv, transparent -> None."""
    c = int(u * w)
    r = int(v * h)
    if not (0 <= c < w and 0 <= r < h):
        return None
    if px[r, c, 3] < 0.1:
        return None
    return px[r, c, :3]


# ---- classify ---------------------------------------------------------

# luminance reference bands, printed once to tune thresholds:
# the photo's hair is jet black, dress mid-gray, face dim pale
FACE_Z0, FACE_Z1 = 0.76 * H, 0.94 * H
FACE_XMAX = 0.055 * H
HAIR_ZMIN = 0.50 * H
BACK_ZMIN = 0.55 * H
BACK_XMAX = 0.115 * H

bands = {
    "face_col": [], "bodice": [], "sleeve": [], "skirt": [],
    "curtain": [], "back_drape": [],
}
for v in src.data.vertices:
    x, y, z = v.co.x, v.co.y, v.co.z
    ny = v.normal.y
    s = photo_sample(x * SU + gcx, z * SV + CV)
    lum = (s[0] + s[1] + s[2]) / 3 if s is not None else -1.0
    if ny < -0.3 and abs(x) < FACE_XMAX and FACE_Z0 < z < FACE_Z1:
        bands["face_col"].append(lum)
    elif ny < -0.3 and 0.55 * H < z < 0.75 * H and abs(x) < 0.10 * H:
        bands["bodice"].append(lum)
    elif ny < -0.3 and 0.6 * H < z < 0.8 * H and 0.10 * H < abs(x) < 0.17 * H:
        bands["sleeve"].append(lum)
    elif z < 0.45 * H:
        bands["skirt"].append(lum)
    elif ny < -0.3 and HAIR_ZMIN < z < 0.80 * H and 0.04 * H < abs(x) < 0.11 * H:
        bands["curtain"].append(lum)
    elif ny > 0.35 and z > BACK_ZMIN and abs(x) < BACK_XMAX:
        bands["back_drape"].append(lum)
for nm, vals in bands.items():
    vals = [v for v in vals if v >= 0]
    if vals:
        vals.sort()
        print(f"PROBE lum {nm}: n={len(vals)} p10={vals[len(vals)//10]:.2f} "
              f"med={vals[len(vals)//2]:.2f} p90={vals[len(vals)*9//10]:.2f}")

# rules v4 — depth-based split. The curtains are the FRONTMOST surface
# in each (x,z) cell of the head/torso band; the face, sockets and neck
# are recessed behind them. The photo luminance breaks ties (jet-black
# strands vs brighter dress) and adds pale hands/feet.
Z_FACE0, Z_FACE1 = 0.785 * H, 0.945 * H
Z_CROWN = 0.945 * H
Z_HEAD = 0.82 * H
Z_BAND0 = 0.55 * H
BACK_ZMIN = 0.55 * H
BACK_XMAX = 0.115 * H

verts = src.data.vertices
cells = {}
band_ids = set()
for i, v in enumerate(verts):
    x, z = v.co.x, v.co.z
    if (Z_BAND0 < z < Z_FACE1 and abs(x) < 0.095 * H
            and v.normal.y < 0.3):
        key = (round(x / 0.012), round(z / 0.012))
        cells[key] = min(cells.get(key, 1e9), v.co.y)
        band_ids.add(i)

mask = src.data.color_attributes.new("mask", "FLOAT_COLOR", "POINT")
n_hair = n_skin = 0
for v in verts:
    x, y, z = v.co.x, v.co.y, v.co.z
    ny = v.normal.y
    s = photo_sample(x * SU + gcx, z * SV + CV)
    lum = (s[0] + s[1] + s[2]) / 3 if s is not None else 0.0
    key = (round(x / 0.012), round(z / 0.012))
    in_band = v.index in band_ids
    frontmost = in_band and y <= cells[key] + 0.012
    recessed = in_band and y > cells[key] + 0.012
    face_zone = (ny < -0.2 and abs(x) < 0.05 * H
                 and Z_FACE0 < z < Z_FACE1)
    skin = (face_zone and (abs(x) < 0.025 * H or recessed)) or \
        (ny < 0.5 and lum > 0.42 and abs(x) > 0.105 * H
         and 0.40 * H < z < 0.62 * H) or \
        (lum > 0.42 and z < 0.11 * H)
    hair = (not skin) and (
        z > Z_CROWN
        or (frontmost and lum < 0.30)
        or z > Z_HEAD
        or (ny > 0.35 and z > BACK_ZMIN and abs(x) < BACK_XMAX))
    if hair:
        n_hair += 1
    if skin:
        n_skin += 1
    mask.data[v.index].color = (1.0 if hair else 0.0,
                                1.0 if skin else 0.0, 0.0, 1.0)
print(f"PROBE: hair={n_hair} skin={n_skin} "
      f"robe={len(src.data.vertices) - n_hair - n_skin}")

# ---- debug renders ----------------------------------------------------

mat = bpy.data.materials.new("probe")
mat.use_nodes = True
for n in list(mat.node_tree.nodes):
    if n.type != "OUTPUT_MATERIAL":
        mat.node_tree.nodes.remove(n)
src.data.materials.append(mat)

scene = bpy.context.scene
world = bpy.data.worlds.new("w")
world.color = (0.02, 0.02, 0.025)
scene.world = world
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "VERTEX"
scene.display.shading.background_type = "WORLD"
scene.display.shading.show_cavity = True

cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
for view, target, off, lens, res in (
        ("front", Vector((0, 0, 0.5 * H)), (0.2, -1.4, 0.12), 40, (512, 720)),
        ("back", Vector((0, 0, 0.5 * H)), (-0.15, 1.4, 0.12), 40, (512, 720)),
        ("head", Vector((0, 0, 0.84 * H)), (0.45, -1.0, 0.18), 55,
         (560, 640)),
        ("torso", Vector((0, 0, 0.66 * H)), (0.4, -0.9, 0.05), 55,
         (560, 640))):
    dist = 1.15 * H if view != "head" else 0.85
    cam.location = target + Vector(off).normalized() * dist
    look = (target - Vector(cam.location)).normalized()
    cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
    cam_data.lens = lens
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = os.path.join(OUT_DIR, f"probe_{view}.png")
    bpy.ops.render.render(write_still=True)
    print("SAVED", scene.render.filepath)
print("PROBE OK")
