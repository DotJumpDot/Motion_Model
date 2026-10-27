"""Rig + animate the AI-generated ghost mesh and export Unity FBX.

    blender --background --python tools/hunyuan3d/rig_ghost.py

Pipeline: import ghost_ai_tex.glb (Hunyuan multiview paint output;
falls back to ghost_ai.glb + projection bake) -> decimate to the
tri budget -> normalize to origin-at-feet -> classify every vertex as
hair / skin / robe (depth vs the reference photo) -> build a 26-bone
rig (hips/spine/head + 2x3 arm + 2x3 leg + 7 hair-whip chain bones +
4 robe-hem bones) -> auto-skin by nearest bone segment with class
gates -> hand-key Idle/Walk/Attack incl. hair/hem secondary sway ->
export FBX (embedded texture).

Render checks: rest, mid-walk and mid-attack poses, textured,
front + close + back.
"""

import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

REPO = "C:/Code/Motion_Model"
sys.path.insert(0, os.path.join(REPO, "src", "blender"))
import blender_lib as bl  # noqa: E402

GLB = os.path.join(REPO, "tools", "hunyuan3d", "out", "ghost_ai.glb")
TEX_GLB = os.path.join(REPO, "tools", "hunyuan3d", "out",
                       "ghost_ai_tex_8k.glb")  # paint on the 8k mesh
OUT_DIR = os.path.join(REPO, "tools", "hunyuan3d", "out")
REF_IMG = os.path.join(OUT_DIR, "input_clean.png")
BAKE_PNG = os.path.join(REPO, "assets", "textures", "gw_ai_bake.png")
PAINT_PNG = os.path.join(REPO, "assets", "textures", "gw_ai_paint.png")
OUT_FBX = os.path.join(REPO, "assets", "fbx", "Ghost_Woman.fbx")
TRI_BUDGET = 8000

# ---- 1. import + decimate + normalize ---------------------------------

bpy.ops.wm.read_factory_settings(use_empty=True)
# prefer the Hunyuan-paint textured mesh (same geometry, xatlas UVs
# and a 1024 albedo baked by the multiview diffusion); the projection
# bake path below stays as fallback when the texgen output is absent
if os.path.exists(TEX_GLB):
    GLB = TEX_GLB
bpy.ops.import_scene.gltf(filepath=GLB)
src = [o for o in bpy.data.objects if o.type == "MESH"][0]

bpy.context.view_layer.objects.active = src
src.select_set(True)
n_tris = sum(len(p.vertices) - 2 for p in src.data.polygons)
mod = src.modifiers.new("dec", "DECIMATE")
mod.ratio = TRI_BUDGET / max(n_tris, 1)
bpy.ops.object.modifier_apply(modifier="dec")
print(f"RIG: decimated {n_tris} -> {sum(len(p.vertices) - 2 for p in src.data.polygons)} tris")

# GLB is Y-up; Blender importer already converted to Z-up. Move the
# origin to ground center so Unity placement is trivial.
pts = [src.matrix_world @ Vector(c) for c in src.bound_box]
zmin = min(p.z for p in pts)
cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
src.data.transform(__import__("mathutils").Matrix.Translation(
    (-cx, -cy, -zmin)))
src.matrix_world = __import__("mathutils").Matrix.Identity(4)
HEIGHT = max(v.co.z for v in src.data.vertices)
print(f"RIG: normalized, height={HEIGHT:.3f}")

# ---- 1b. classify verts: hair / skin / robe ----------------------------
# Depth-based split against the reference photo (same projection the
# bake uses): the hair curtains are the FRONTMOST surface in each
# (x,z) cell of the head/torso band, the face/neck are recessed behind
# them. Photo luminance breaks ties (jet-black strands vs brighter
# dress) and adds the pale bare hands + feet. The masks drive both the
# texture bake and which bones may grab a vertex during skinning.

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
SV = (gy1 - gy0) / HEIGHT


def photo_lum(x, z):
    c = int((x * SU + gcx) * w)
    r = int((z * SV + CV) * h)
    if 0 <= c < w and 0 <= r < h and px[r, c, 3] >= 0.1:
        return float(px[r, c, :3].mean())
    return 0.0


Z_FACE0, Z_FACE1 = 0.785 * HEIGHT, 0.945 * HEIGHT
Z_CROWN = 0.945 * HEIGHT
Z_HEAD = 0.82 * HEIGHT
Z_BAND0 = 0.55 * HEIGHT
cells = {}
band_ids = set()
for i, v in enumerate(src.data.vertices):
    x, z = v.co.x, v.co.z
    if (Z_BAND0 < z < Z_FACE1 and abs(x) < 0.095 * HEIGHT
            and v.normal.y < 0.3):
        key = (round(x / 0.012), round(z / 0.012))
        cells[key] = min(cells.get(key, 1e9), v.co.y)
        band_ids.add(i)

HAIR_IDS = set()
SKIN_IDS = set()
vmask = src.data.color_attributes.new("mask", "FLOAT_COLOR", "POINT")
for i, v in enumerate(src.data.vertices):
    x, y, z = v.co.x, v.co.y, v.co.z
    ny = v.normal.y
    lum = photo_lum(x, z)
    key = (round(x / 0.012), round(z / 0.012))
    in_band = i in band_ids
    frontmost = in_band and y <= cells[key] + 0.012
    recessed = in_band and y > cells[key] + 0.012
    face_zone = (ny < -0.2 and abs(x) < 0.05 * HEIGHT
                 and Z_FACE0 < z < Z_FACE1)
    skin = (face_zone and (abs(x) < 0.025 * HEIGHT or recessed)) or \
        (ny < 0.5 and lum > 0.42 and abs(x) > 0.105 * HEIGHT
         and 0.40 * HEIGHT < z < 0.62 * HEIGHT) or \
        (lum > 0.42 and z < 0.11 * HEIGHT)
    hair = (not skin) and (
        z > Z_CROWN
        or (frontmost and lum < 0.30)
        or z > Z_HEAD
        or (ny > 0.35 and z > 0.55 * HEIGHT and abs(x) < 0.115 * HEIGHT))
    if hair:
        HAIR_IDS.add(i)
    if skin:
        SKIN_IDS.add(i)
    vmask.data[i].color = (1.0 if hair else 0.0,
                           1.0 if skin else 0.0, 0.0, 1.0)
print(f"RIG: classified hair={len(HAIR_IDS)} skin={len(SKIN_IDS)} "
      f"robe={len(src.data.vertices) - len(HAIR_IDS) - len(SKIN_IDS)}")

# ---- 2. armature (15 bones, proportions from the mesh bbox) -----------

H = HEIGHT
SHOULDER_Z = 0.745 * H
HIP_Z = 0.50 * H
KNEE_Z = 0.265 * H
ANKLE_Z = 0.045 * H
LEG_X = 0.048 * H / 0.1  # ~0.095 at H=1.96 -> derive from H
LEG_X = 0.048 * H
SHOULDER_X = 0.105 * H
ELBOW_X = 0.122 * H
WRIST_X = 0.127 * H
RH = max((v.co.x ** 2 + v.co.y ** 2) ** 0.5
         for v in src.data.vertices if v.co.z < 0.12 * H)

bones = [
    ("Hips", None, (0, 0, 0.92 * H * 0.5 + HIP_Z * 0.5),
     (0, 0, HIP_Z + 0.06), True),
    ("Spine", "Hips", (0, 0, HIP_Z + 0.06), (0, 0, SHOULDER_Z - 0.06),
     True),
    ("Head", "Spine", (0, 0, SHOULDER_Z - 0.06), (0, 0, 0.88 * H), True),
]
for side, x in (("L", 1), ("R", -1)):
    bones += [
        (f"UpperArm_{side}", "Spine",
         (SHOULDER_X * x, 0, SHOULDER_Z),
         (ELBOW_X * x, 0.015, SHOULDER_Z - 0.29), True),
        (f"Forearm_{side}", f"UpperArm_{side}",
         (ELBOW_X * x, 0.015, SHOULDER_Z - 0.29),
         (WRIST_X * x, 0.04, SHOULDER_Z - 0.55), True),
        (f"Hand_{side}", f"Forearm_{side}",
         (WRIST_X * x, 0.04, SHOULDER_Z - 0.55),
         (WRIST_X * x, 0.06, SHOULDER_Z - 0.66), True),
        (f"Thigh_{side}", "Hips",
         (LEG_X * x, 0, HIP_Z), (LEG_X * x, 0.01, KNEE_Z), True),
        (f"Shin_{side}", f"Thigh_{side}",
         (LEG_X * x, 0.01, KNEE_Z), (LEG_X * x, -0.005, ANKLE_Z), True),
        (f"Foot_{side}", f"Shin_{side}",
         (LEG_X * x, -0.005, ANKLE_Z), (LEG_X * x, 0.09, 0.015), True),
    ]
# secondary-motion chains: hair whip (parented to Head) and robe hem
# flutter (parented to Hips); sway is keyed into every clip below
bones += [
    ("HairB_1", "Head", (0, 0.045 * H, 0.86 * H),
     (0, 0.055 * H, 0.72 * H), True),
    ("HairB_2", "HairB_1", (0, 0.055 * H, 0.72 * H),
     (0, 0.06 * H, 0.58 * H), True),
    ("HairB_3", "HairB_2", (0, 0.06 * H, 0.58 * H),
     (0, 0.06 * H, 0.46 * H), True),
    ("HairL_1", "Head", (0.055 * H, -0.015 * H, 0.85 * H),
     (0.065 * H, -0.02 * H, 0.70 * H), True),
    ("HairL_2", "HairL_1", (0.065 * H, -0.02 * H, 0.70 * H),
     (0.065 * H, -0.01 * H, 0.56 * H), True),
    ("HairR_1", "Head", (-0.055 * H, -0.015 * H, 0.85 * H),
     (-0.065 * H, -0.02 * H, 0.70 * H), True),
    ("HairR_2", "HairR_1", (-0.065 * H, -0.02 * H, 0.70 * H),
     (-0.065 * H, -0.01 * H, 0.56 * H), True),
    ("Robe_F", "Hips", (0, -0.8 * RH, 0.14 * H),
     (0, -0.88 * RH, 0.03 * H), True),
    ("Robe_B", "Hips", (0, 0.8 * RH, 0.14 * H),
     (0, 0.88 * RH, 0.03 * H), True),
    ("Robe_L", "Hips", (0.8 * RH, 0, 0.14 * H),
     (0.88 * RH, 0, 0.03 * H), True),
    ("Robe_R", "Hips", (-0.8 * RH, 0, 0.14 * H),
     (-0.88 * RH, 0, 0.03 * H), True),
]
arm = bl.build_armature("GhostWoman_Armature", bones)

# ---- 3. skinning: zone rules + nearest segment ------------------------


def dist_to_seg(p, a, b):
    a, b = Vector(a), Vector(b)
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (p - (a + ab * t)).length


def nearest_bone(p, names):
    lookup = {b[0]: (b[2], b[3]) for b in bones}
    return min(names, key=lambda n: dist_to_seg(p, *lookup[n]))

ARM_BONES = [f"UpperArm_{s}" for s in ("L", "R")] + \
            [f"Forearm_{s}" for s in ("L", "R")] + \
            [f"Hand_{s}" for s in ("L", "R")]
LEG_BONES = [f"Thigh_{s}" for s in ("L", "R")] + \
            [f"Shin_{s}" for s in ("L", "R")] + \
            [f"Foot_{s}" for s in ("L", "R")]
HAIR_BONES = [f"HairB_{i}" for i in (1, 2, 3)] + \
             [f"Hair{side}_{i}" for side in ("L", "R") for i in (1, 2)]
ROBE_BONES = ["Robe_F", "Robe_B", "Robe_L", "Robe_R"]
ALL_BONES = ["Hips", "Spine", "Head"] + ARM_BONES + LEG_BONES
SEG = {b[0]: (b[2], b[3]) for b in bones}

bl.parent_to(src, arm)
# smooth skinning: top-2 nearest bone segments, inverse-square weights
# (hard 1.0 weights tore the skirt hem when the legs swung). Hair
# verts blend only between the hair chains and the spine chain, so
# hair bones never steal the face; robe hem bones join the candidate
# set below z 0.35H.
pairs = {}
for v in src.data.vertices:
    p = v.co
    if v.index in HAIR_IDS:
        cands = ["Head", "Spine", "Hips"] + HAIR_BONES
    else:
        cands = list(ALL_BONES)
        if p.z < 0.22 * H:
            cands += ROBE_BONES
        # arm bones must not steal robe verts below the sleeve line —
        # the skirt's outer edge sits right beside the hanging hands,
        # and at the attack lunge those verts would dangle off the arm
        if p.z < 0.58 * H and v.index not in SKIN_IDS:
            cands = [n for n in cands
                     if not n.startswith(("UpperArm", "Forearm",
                                          "Hand"))]
    dists = sorted((dist_to_seg(p, *SEG[n]), n) for n in cands)
    (d1, n1), (d2, n2) = dists[0], dists[1]
    if d2 > 4.0 * max(d1, 1e-4):
        pairs.setdefault(n1, []).append((v.index, 1.0))
    else:
        w1 = (1.0 / max(d1, 1e-4)) ** 2
        w2 = (1.0 / max(d2, 1e-4)) ** 2
        s = w1 + w2
        pairs.setdefault(n1, []).append((v.index, w1 / s))
        pairs.setdefault(n2, []).append((v.index, w2 / s))
for bname, entries in pairs.items():
    vg = src.vertex_groups.get(bname) or src.vertex_groups.new(name=bname)
    for idx, w in entries:
        vg.add([idx], w, "REPLACE")
print("RIG: skinned, bones used:", sorted(pairs.keys()))

# ---- 4. clips ---------------------------------------------------------

# ---- 4. clips ---------------------------------------------------------


def rest_zero():
    d = {}
    for bname, *_ in bones:
        d[bname] = {"loc": (0, 0, 0), "rot": (0, 0, 0)}
    return d


def idle(f):
    t = 2 * math.pi * (f - 1) / 96
    d = {}
    for bname, *_ in bones:
        d[bname] = {"rot": (0, 0, 0)}
    d["Hips"]["loc"] = (0, 0, 0.008 * math.sin(t))
    d["Spine"]["rot"] = (0, 2.0 * math.sin(t), 0)
    head = {"rot": (1.5 * math.sin(2 * t), 0, 3 * math.sin(t))}
    if 45 <= f <= 52:  # twitch glitch
        k = 13 if f <= 47 else (7 if f <= 49 else
                                (3 if f <= 51 else 0))
        head["rot"] = (head["rot"][0], head["rot"][1],
                       3 * math.sin(t) + k)
    d["Head"] = head
    for side, ph in (("L", 0.0), ("R", math.pi)):
        d[f"UpperArm_{side}"]["rot"] = (2.5 * math.sin(t + ph), 0,
                                        1.5 * math.sin(t + ph))
        d[f"Forearm_{side}"]["rot"] = (3.5 * math.sin(t + ph + 0.6), 0, 0)
    # secondary motion: hair whip + hem flutter lag the body wave,
    # amplitude grows and phase delays toward the chain tips
    d["HairB_1"]["rot"] = (2.5 * math.sin(t + 0.3), 0,
                           1.2 * math.sin(t))
    d["HairB_2"]["rot"] = (4.0 * math.sin(t + 0.8), 0,
                           1.8 * math.sin(t + 0.3))
    d["HairB_3"]["rot"] = (5.5 * math.sin(t + 1.3), 0,
                           2.2 * math.sin(t + 0.6))
    for side, sx in (("L", 1), ("R", -1)):
        d[f"Hair{side}_1"]["rot"] = (2.5 * math.sin(t + 0.4), 0,
                                     sx * 1.5 * math.sin(t + 0.6))
        d[f"Hair{side}_2"]["rot"] = (4.0 * math.sin(t + 0.9), 0,
                                     sx * 2.2 * math.sin(t + 1.1))
    for name, ph in (("Robe_F", 0.0), ("Robe_R", 1.6), ("Robe_B", 3.1),
                     ("Robe_L", 4.7)):
        d[name]["rot"] = (1.8 * math.sin(t + ph), 0,
                          1.2 * math.sin(t + ph + 0.5))
    return d


def walk(f):
    t = 2 * math.pi * (f - 1) / 48
    d = rest_zero()
    d["Hips"]["loc"] = (0, 0, 0.014 * (1 - math.cos(2 * t)))
    d["Hips"]["rot"] = (2, 0, 2.5 * math.sin(t))
    d["Spine"]["rot"] = (4 + 1.5 * math.sin(2 * t), 2 * math.sin(t),
                         -2.5 * math.sin(t))
    d["Head"]["rot"] = (-3, 0, 3 * math.sin(t))
    for side, ph in (("L", 0.0), ("R", math.pi)):
        swing = math.sin(t + ph)                       # +1 forward
        d[f"Thigh_{side}"]["rot"] = (24 * swing, 0, 0)
        d[f"Shin_{side}"]["rot"] = (-34 * max(0.0, math.sin(t + ph - 0.9)),
                                    0, 0)
        d[f"Foot_{side}"]["rot"] = (12 * math.sin(t + ph + 0.9), 0, 0)
        d[f"UpperArm_{side}"]["rot"] = (-14 * swing, 0, 2 * math.sin(t + ph))
        d[f"Forearm_{side}"]["rot"] = (-10 * max(0.0, swing) - 4, 0, 0)
    # hair trails the stride with per-chain lag; the hem see-saws
    # fore/aft around it (front hem forward while the back hem kicks)
    d["HairB_1"]["rot"] = (-4 * math.sin(t + 0.5), 0,
                           2 * math.sin(2 * t + 0.3))
    d["HairB_2"]["rot"] = (-6 * math.sin(t + 0.9), 0,
                           2.6 * math.sin(2 * t + 0.6))
    d["HairB_3"]["rot"] = (-7 * math.sin(t + 1.3), 0,
                           3.2 * math.sin(2 * t + 0.9))
    for side, sx in (("L", 1), ("R", -1)):
        d[f"Hair{side}_1"]["rot"] = (-3.5 * math.sin(t + 0.6), 0,
                                     sx * 1.8 * math.sin(t + 0.9))
        d[f"Hair{side}_2"]["rot"] = (-4.5 * math.sin(t + 1.0), 0,
                                     sx * 2.2 * math.sin(t + 1.3))
    d["Robe_F"]["rot"] = (6 * math.sin(t + 0.9), 0, 2 * math.sin(2 * t))
    d["Robe_B"]["rot"] = (-6 * math.sin(t + 0.9), 0,
                          2 * math.sin(2 * t + math.pi))
    d["Robe_L"]["rot"] = (2 * math.sin(2 * t), 0, 5 * math.sin(t + 0.9))
    d["Robe_R"]["rot"] = (2 * math.sin(2 * t + math.pi), 0,
                          -5 * math.sin(t + 0.9))
    return d


def attack_keys():
    zero = rest_zero()

    def pose(**over):
        d = {k: dict(v) for k, v in zero.items()}
        for bname, entry in over.items():
            d[bname] = {"loc": entry.get("loc", (0, 0, 0)),
                        "rot": entry.get("rot", (0, 0, 0))}
        return d

    return [
        (1, pose()),
        (7, pose(
            Hips={"loc": (0, 0, 0.02), "rot": (0, 0, 0)},
            Spine={"rot": (-10, 0, 0)}, Head={"rot": (0, 0, -8)},
            UpperArm_L={"rot": (165, 0, -12)},
            UpperArm_R={"rot": (165, 0, 12)},
            Forearm_L={"rot": (25, 0, 0)}, Forearm_R={"rot": (25, 0, 0)},
            Thigh_L={"rot": (-8, 0, 0)}, Thigh_R={"rot": (8, 0, 0)},
            HairB_1={"rot": (-5, 0, 0)}, HairB_2={"rot": (-8, 0, 0)},
            HairB_3={"rot": (-10, 0, 0)},
            HairL_1={"rot": (-4, 0, 3)}, HairL_2={"rot": (-6, 0, 4)},
            HairR_1={"rot": (-4, 0, -3)}, HairR_2={"rot": (-6, 0, -4)},
            Robe_F={"rot": (2, 0, 0)}, Robe_B={"rot": (-2, 0, 0)})),
        (14, pose(
            Hips={"loc": (0, -0.15, 0.005), "rot": (0, 0, 0)},
            Spine={"rot": (22, 0, 0)}, Head={"rot": (16, 0, 0)},
            UpperArm_L={"rot": (-35, 0, -18)},
            UpperArm_R={"rot": (-35, 0, 18)},
            Forearm_L={"rot": (-20, 0, 0)}, Forearm_R={"rot": (-20, 0, 0)},
            Thigh_L={"rot": (14, 0, 0)}, Thigh_R={"rot": (-12, 0, 0)},
            Shin_R={"rot": (-20, 0, 0)},
            HairB_1={"rot": (12, 0, 0)}, HairB_2={"rot": (16, 0, 0)},
            HairB_3={"rot": (18, 0, 0)},
            HairL_1={"rot": (9, 0, -4)}, HairL_2={"rot": (12, 0, -6)},
            HairR_1={"rot": (9, 0, 4)}, HairR_2={"rot": (12, 0, 6)},
            Robe_F={"rot": (5, 0, 0)}, Robe_B={"rot": (5, 0, 0)},
            Robe_L={"rot": (0, 0, -5)}, Robe_R={"rot": (0, 0, 5)})),
        (22, pose(
            Hips={"loc": (0, -0.18, 0), "rot": (0, 0, 0)},
            Spine={"rot": (19, 0, 2)}, Head={"rot": (13, 0, 4)},
            UpperArm_L={"rot": (-28, 0, -18)},
            UpperArm_R={"rot": (-28, 0, 18)},
            Forearm_L={"rot": (-14, 0, 0)}, Forearm_R={"rot": (-14, 0, 0)},
            Thigh_L={"rot": (12, 0, 0)}, Thigh_R={"rot": (-10, 0, 0)},
            HairB_1={"rot": (8, 0, 0)}, HairB_2={"rot": (10, 0, 0)},
            HairB_3={"rot": (12, 0, 0)},
            HairL_1={"rot": (6, 0, -2)}, HairL_2={"rot": (8, 0, -3)},
            HairR_1={"rot": (6, 0, 2)}, HairR_2={"rot": (8, 0, 3)},
            Robe_F={"rot": (3, 0, 0)}, Robe_B={"rot": (3, 0, 0)})),
        (36, zero),
    ]


bl.add_clip(arm, "Idle", 96, idle)
bl.add_clip(arm, "Walk", 48, walk)
bl.add_clip(arm, "Attack", 36, bl.pose_from_keys(attack_keys()))

# ---- 5. texture --------------------------------------------------------
# Two sources: (a) the Hunyuan multiview-paint atlas shipped inside the
# tex GLB (v0.6 default — painted face, skin and hair), (b) the photo
# projection bake (v0.5 fallback when the texgen output is absent).

if GLB == TEX_GLB:
    os.makedirs(os.path.dirname(PAINT_PNG), exist_ok=True)
    src_img = next(n.image for m in src.data.materials if m
                   for n in m.node_tree.nodes
                   if n.type == "TEX_IMAGE" and n.image)
    src_img.filepath_raw = PAINT_PNG
    src_img.file_format = "PNG"
    src_img.save()
    mat2 = bl.textured_material("gw_ai_tex", src_img, rough=0.85)
    src.data.materials.clear()
    src.data.materials.append(mat2)
    print("TEXTURE: using Hunyuan paint atlas ->", PAINT_PNG)
elif os.path.exists(REF_IMG):
    os.makedirs(os.path.dirname(BAKE_PNG), exist_ok=True)

    bpy.context.view_layer.objects.active = src
    src.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=66 * bl.DEG, island_margin=0.03)
    bpy.ops.object.mode_set(mode="OBJECT")

    fabric = bl.make_texture(
        "gw_ai_fabric", 512, base=(0.44, 0.42, 0.39),
        blotch=(0.22, 0.19, 0.15), blotch_amount=0.65, blotch_seed=21,
        streak=((0.24, 0.22, 0.19), 24, 0.2), dirt_bottom=0.8, seed=20)
    hair_img = bl.make_texture(
        "gw_hair", 512, base=(0.050, 0.046, 0.056),
        blotch=(0.016, 0.014, 0.020), blotch_amount=0.45, blotch_seed=31,
        streak=((0.016, 0.014, 0.020), 44, 0.55), seed=30)
    print(f"BAKE align: su={SU:.3f} sv={SV:.3f} cv={CV:.3f} "
          f"gcx={gcx:.3f} (computed in the classify pass)")

    mat = bpy.data.materials.new("gw_bake_src")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out_node = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")

    # projection: u = x*SU + gcx, v = z*SV + CV (model faces -Y, so the
    # horizontal axis is mirrored to match the photo). The same mapping
    # feeds the hair streak atlas — v = world z keeps strands vertical.
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    mp = nt.nodes.new("ShaderNodeMapping")
    img_ref = nt.nodes.new("ShaderNodeTexImage")
    img_ref.image = ref
    img_ref.extension = "EXTEND"
    tex_fab = nt.nodes.new("ShaderNodeTexImage")
    tex_fab.image = fabric
    tex_hair = nt.nodes.new("ShaderNodeTexImage")
    tex_hair.image = hair_img
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = (0.0, -1.0, 0.0)
    front = nt.nodes.new("ShaderNodeMapRange")
    front.inputs["From Min"].default_value = -0.25
    front.inputs["From Max"].default_value = 0.35
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "mask"
    sep_m = nt.nodes.new("ShaderNodeSeparateColor")
    pale = nt.nodes.new("ShaderNodeRGB")
    pale.outputs[0].default_value = (0.62, 0.59, 0.53, 1.0)
    bright = nt.nodes.new("ShaderNodeBrightContrast")
    bright.inputs["Bright"].default_value = 0.18
    bright.inputs["Contrast"].default_value = 0.08

    def mix():
        m = nt.nodes.new("ShaderNodeMix")
        m.data_type = "RGBA"
        return m

    m_robe, m_hair, m_skin, m_out = mix(), mix(), mix(), mix()
    emit = nt.nodes.new("ShaderNodeEmission")

    def sock(node, ident, inputs=True):
        src_sockets = node.inputs if inputs else node.outputs
        for s in src_sockets:
            if s.identifier == ident:
                return s
        raise KeyError(ident)

    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs["X"], comb.inputs["X"])
    nt.links.new(sep.outputs["Z"], comb.inputs["Y"])
    mp.inputs["Scale"].default_value = (SU, SV, 1.0)
    mp.inputs["Location"].default_value = (gcx, CV, 0.0)
    nt.links.new(comb.outputs[0], mp.inputs["Vector"])
    nt.links.new(mp.outputs[0], img_ref.inputs["Vector"])
    nt.links.new(mp.outputs[0], tex_hair.inputs["Vector"])
    nt.links.new(tc.outputs["UV"], tex_fab.inputs["Vector"])
    nt.links.new(geo.outputs["Normal"], dot.inputs[0])
    nt.links.new(dot.outputs["Value"], front.inputs["Value"])
    nt.links.new(attr.outputs["Color"], sep_m.inputs[0])
    nt.links.new(img_ref.outputs["Color"], bright.inputs["Color"])

    # robe: photo on the front, procedural fabric on the back
    nt.links.new(tex_fab.outputs["Color"], sock(m_robe, "A_Color"))
    nt.links.new(bright.outputs["Color"], sock(m_robe, "B_Color"))
    nt.links.new(front.outputs["Result"], sock(m_robe, "Factor_Float"))
    # hair: black streak atlas overrides robe on BOTH sides (fixes the
    # gray back of the head/drape) via the vertex hair mask
    nt.links.new(sock(m_robe, "Result_Color", inputs=False),
                 sock(m_hair, "A_Color"))
    nt.links.new(tex_hair.outputs["Color"], sock(m_hair, "B_Color"))
    nt.links.new(sep_m.outputs["Red"], sock(m_hair, "Factor_Float"))
    # skin: pale corpse base lightly tinted by the photo (never black —
    # the sockets/mouth shading comes from the geometry)
    nt.links.new(pale.outputs[0], sock(m_skin, "A_Color"))
    nt.links.new(img_ref.outputs["Color"], sock(m_skin, "B_Color"))
    sock(m_skin, "Factor_Float").default_value = 0.22
    # final: hair first, then skin wins on the face/hands/feet
    nt.links.new(sock(m_hair, "Result_Color", inputs=False),
                 sock(m_out, "A_Color"))
    nt.links.new(sock(m_skin, "Result_Color", inputs=False),
                 sock(m_out, "B_Color"))
    nt.links.new(sep_m.outputs["Green"], sock(m_out, "Factor_Float"))
    nt.links.new(sock(m_out, "Result_Color", inputs=False),
                 emit.inputs["Color"])
    nt.links.new(emit.outputs[0], out_node.inputs["Surface"])

    bake_img = bpy.data.images.new("gw_ai_bake", 1024, 1024)
    scene = bpy.context.scene
    # the bake target image must be an active image node in the material
    img_node = nt.nodes.new("ShaderNodeTexImage")
    img_node.image = bake_img
    for n in nt.nodes:
        n.select = False
    img_node.select = True
    nt.nodes.active = img_node
    src.data.materials.clear()
    src.data.materials.append(mat)
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 1
    bpy.ops.object.select_all(action="DESELECT")
    src.select_set(True)
    bpy.context.view_layer.objects.active = src
    bpy.ops.object.bake(type="EMIT", use_clear=True, margin=8)
    bake_img.filepath_raw = BAKE_PNG
    bake_img.file_format = "PNG"
    bake_img.save()
    print("BAKED", BAKE_PNG)

    # final material for Unity/preview
    mat2 = bl.textured_material("gw_ai_tex", bake_img, rough=0.8)
    src.data.materials.clear()
    src.data.materials.append(mat2)

# ---- 6. export + pose renders -----------------------------------------

os.makedirs(os.path.dirname(OUT_FBX), exist_ok=True)
bl.export_fbx(OUT_FBX)
bl.report("GhostWomanAI")

scene = bpy.context.scene
world = bpy.data.worlds.new("w")
world.color = (0.02, 0.02, 0.025)
scene.world = world
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
if any(m.use_nodes and any(n.type == "TEX_IMAGE" and n.image
                           for n in m.node_tree.nodes)
       for m in bpy.data.materials):
    scene.display.shading.color_type = "TEXTURE"
else:
    scene.display.shading.color_type = "SINGLE"
    scene.display.shading.single_color = (0.55, 0.53, 0.50)
scene.display.shading.background_type = "WORLD"
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "BOTH"

cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

CENTER = Vector((0, 0, 0.5 * H))
attack_fn = bl.pose_from_keys(attack_keys())
for label, pose_at, frame in (("rest", None, 1), ("walk", walk, 12),
                              ("attack", attack_fn, 14)):
    if pose_at:
        for bname, entry in pose_at(frame).items():
            pb = arm.pose.bones.get(bname)
            if not pb:
                continue
            if entry.get("loc"):
                pb.location = entry["loc"]
            if entry.get("rot"):
                pb.rotation_euler = tuple(r * bl.DEG for r in entry["rot"])
    # the mesh faces -Y: cameras sit on the -Y side
    for view, off, lens in (("front", (0.2, -1.4, 0.12), 40),
                            ("close", (0.45, -1.0, 0.30), 55),
                            ("back", (-0.15, 1.4, 0.12), 40)):
        target = CENTER if view == "front" else Vector((0, 0, 0.80 * H))
        dist = 1.15 * H if view == "front" else 0.85
        cam.location = target + Vector(off).normalized() * dist
        look = (target - Vector(cam.location)).normalized()
        cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = lens
        scene.render.resolution_x = 512 if view == "front" else 560
        scene.render.resolution_y = 720 if view == "front" else 640
        scene.render.filepath = os.path.join(
            OUT_DIR, f"rig_{label}_{view}.png")
        bpy.ops.render.render(write_still=True)
        print("SAVED", scene.render.filepath)
    # reset pose
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
print("RIG OK")
