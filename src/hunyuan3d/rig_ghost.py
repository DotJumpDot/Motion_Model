"""Rig + animate the AI-generated ghost mesh and export Unity FBX.

    blender --background --python tools/hunyuan3d/rig_ghost.py

Pipeline: import ghost_ai.glb (Hunyuan3D output) -> decimate to the
tri budget -> normalize to origin-at-feet -> build a 15-bone humanoid
rig (hips/spine/head + 2x3 arm + 2x3 leg) -> auto-skin by nearest
bone segment with explicit skirt/leg zones -> hand-key Idle/Walk/
Attack -> export FBX (embedded texture if the GLB carries one).

Render checks: rest + mid-walk pose, textured, front + close.
"""

import math
import os
import sys

import bpy
from mathutils import Vector

REPO = "C:/Code/Motion_Model"
sys.path.insert(0, os.path.join(REPO, "src", "blender"))
import blender_lib as bl  # noqa: E402

GLB = os.path.join(REPO, "tools", "hunyuan3d", "out", "ghost_ai.glb")
OUT_DIR = os.path.join(REPO, "tools", "hunyuan3d", "out")
OUT_FBX = os.path.join(REPO, "assets", "fbx", "Ghost_Woman.fbx")
TRI_BUDGET = 8000

# ---- 1. import + decimate + normalize ---------------------------------

bpy.ops.wm.read_factory_settings(use_empty=True)
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
ALL_BONES = ["Hips", "Spine", "Head"] + ARM_BONES + LEG_BONES
SEG = {b[0]: (b[2], b[3]) for b in bones}

bl.parent_to(src, arm)
# smooth skinning: top-2 nearest bone segments, inverse-square weights
# (hard 1.0 weights tore the skirt hem when the legs swung)
pairs = {}
for v in src.data.vertices:
    p = v.co
    dists = sorted((dist_to_seg(p, *SEG[n]), n) for n in ALL_BONES)
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
            Thigh_L={"rot": (-8, 0, 0)}, Thigh_R={"rot": (8, 0, 0)})),
        (14, pose(
            Hips={"loc": (0, -0.17, 0.005), "rot": (0, 0, 0)},
            Spine={"rot": (22, 0, 0)}, Head={"rot": (16, 0, 0)},
            UpperArm_L={"rot": (-35, 0, -18)},
            UpperArm_R={"rot": (-35, 0, 18)},
            Forearm_L={"rot": (-20, 0, 0)}, Forearm_R={"rot": (-20, 0, 0)},
            Thigh_L={"rot": (14, 0, 0)}, Thigh_R={"rot": (-12, 0, 0)},
            Shin_R={"rot": (-20, 0, 0)})),
        (22, pose(
            Hips={"loc": (0, -0.18, 0), "rot": (0, 0, 0)},
            Spine={"rot": (19, 0, 2)}, Head={"rot": (13, 0, 4)},
            UpperArm_L={"rot": (-28, 0, -18)},
            UpperArm_R={"rot": (-28, 0, 18)},
            Forearm_L={"rot": (-14, 0, 0)}, Forearm_R={"rot": (-14, 0, 0)},
            Thigh_L={"rot": (12, 0, 0)}, Thigh_R={"rot": (-10, 0, 0)})),
        (36, zero),
    ]


bl.add_clip(arm, "Idle", 96, idle)
bl.add_clip(arm, "Walk", 48, walk)
bl.add_clip(arm, "Attack", 36, bl.pose_from_keys(attack_keys()))

# ---- 5. projection texture bake ---------------------------------------
# The mesh was GENERATED from the reference image, so a front-view
# projection aligns almost perfectly. Back/sides blend to procedural
# dark fabric. One EMIT bake in Cycles onto a smart-UV atlas.

REF_IMG = os.path.join(REPO, "tools", "hunyuan3d", "out",
                       "input_clean.png")
BAKE_PNG = os.path.join(REPO, "assets", "textures", "gw_ai_bake.png")
if os.path.exists(REF_IMG):
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
    ref = bpy.data.images.load(REF_IMG)

    # projection from object coords: horizontal = world X (model faces
    # -Y), vertical = world Z. Align the model's world bbox to the
    # ghost's pixel bbox in the reference (alpha channel).
    import numpy as np
    w, h = ref.size
    px = np.array(ref.pixels[:], dtype=np.float32).reshape(h, w, 4)
    alpha = px[:, :, 3] > 0.1
    cols = np.where(alpha.any(axis=0))[0]
    rows = np.where(alpha.any(axis=1))[0]
    gx0, gx1 = cols[0] / w, (cols[-1] + 1) / w
    gy0, gy1 = rows[0] / h, (rows[-1] + 1) / h
    xs = [v.co.x for v in src.data.vertices]
    ww = max(xs) - min(xs)
    WH = max(v.co.z for v in src.data.vertices)
    gcx = (gx0 + gx1) / 2
    SU = -(gx1 - gx0) / ww          # mirrored: viewer's left is +X
    CV = gy0
    SV = (gy1 - gy0) / WH
    print(f"BAKE align: ghost uv box=({gx0:.2f},{gx1:.2f},{gy0:.2f},"
          f"{gy1:.2f}) su={SU:.3f} sv={SV:.3f} cv={CV:.3f}")

    mat = bpy.data.materials.new("gw_bake_src")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out_node = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")

    # projection from object coords: u = x*SU + gcx, v = z*SV + CV
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    mp = nt.nodes.new("ShaderNodeMapping")
    img_ref = nt.nodes.new("ShaderNodeTexImage")
    img_ref.image = ref
    img_ref.extension = "EXTEND"
    tex_fab = nt.nodes.new("ShaderNodeTexImage")
    tex_fab.image = fabric
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = (0.0, -1.0, 0.0)
    mask = nt.nodes.new("ShaderNodeMapRange")
    mask.inputs["From Min"].default_value = -0.25
    mask.inputs["From Max"].default_value = 0.35
    mixc = nt.nodes.new("ShaderNodeMix")
    mixc.data_type = "RGBA"
    emit = nt.nodes.new("ShaderNodeEmission")

    def sock(node, ident, inputs=True):
        src_sockets = node.inputs if inputs else node.outputs
        for s in src_sockets:
            if s.identifier == ident:
                return s
        raise KeyError(ident)

    # horizontal = world X (model faces -Y), vertical = world Z,
    # aligned to the ghost's pixel bbox computed above
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs["X"], comb.inputs["X"])
    nt.links.new(sep.outputs["Z"], comb.inputs["Y"])
    mp.inputs["Scale"].default_value = (SU, SV, 1.0)
    mp.inputs["Location"].default_value = (gcx, CV, 0.0)
    nt.links.new(comb.outputs[0], mp.inputs["Vector"])
    nt.links.new(mp.outputs[0], img_ref.inputs["Vector"])
    bright = nt.nodes.new("ShaderNodeBrightContrast")
    bright.inputs["Bright"].default_value = 0.18
    bright.inputs["Contrast"].default_value = 0.08
    nt.links.new(img_ref.outputs["Color"], bright.inputs["Color"])
    nt.links.new(bright.outputs["Color"], sock(mixc, "B_Color"))
    nt.links.new(tc.outputs["UV"], tex_fab.inputs["Vector"])
    nt.links.new(geo.outputs["Normal"], dot.inputs[0])
    nt.links.new(dot.outputs["Value"], mask.inputs["Value"])

    nt.links.new(tex_fab.outputs["Color"], sock(mixc, "A_Color"))
    nt.links.new(bright.outputs["Color"], sock(mixc, "B_Color"))
    nt.links.new(mask.outputs["Result"], sock(mixc, "Factor_Float"))
    nt.links.new(sock(mixc, "Result_Color", inputs=False),
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
for label, pose_at, frame in (("rest", None, 1), ("walk", walk, 12)):
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
