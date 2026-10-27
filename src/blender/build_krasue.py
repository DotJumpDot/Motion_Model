"""Build the Krasue (v0.2) and export FBX.

Headless run:
    blender --background --python src/blender/build_krasue.py

Output: assets/fbx/Krasue.fbx — floating head + trailing organs,
7-bone rig, clips Float/Lunge/Scream. See Docs/CONCEPT.md.
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_lib as bl  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
OUT = os.path.join(REPO, "assets", "fbx", "Krasue.fbx")

# Palette from Docs/CONCEPT.md
SKIN = (0.851, 0.788, 0.722, 1.0)   # wan pallor   #D9C9B8
HAIR = (0.090, 0.075, 0.063, 1.0)   # near black   #171310
DARKRED = (0.361, 0.051, 0.063, 1.0)  # eyes/mouth #5C0D10
ORGAN = (0.557, 0.184, 0.165, 1.0)  # organs       #8E2F2A
HEART = (0.431, 0.122, 0.110, 1.0)  # heart        #6E1F1C

OPEN = {"start_angle": 135 * bl.DEG, "sweep": 270 * bl.DEG}  # face at +Y


def organ_tube(name, mat, pts, bevel=0.026):
    """Bezier curve with bevel, converted to a mesh."""
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = bevel
    curve.bevel_resolution = 3
    curve.resolution_u = 8
    curve.use_fill_caps = True
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(pts) - 1)
    for bp, p in zip(spline.bezier_points, pts):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bl.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj.select_set(False)
    obj.data.materials.append(mat)
    return obj


def build_meshes():
    mats = {
        "kr_skin": bl.flat_material("kr_skin", SKIN),
        "kr_hair": bl.flat_material("kr_hair", HAIR),
        "kr_dark": bl.flat_material("kr_dark", DARKRED, rough=0.4),
        "kr_organ": bl.flat_material("kr_organ", ORGAN),
        "kr_heart": bl.flat_material("kr_heart", HEART),
    }
    objs = {}
    objs["kr_head"] = bl.sphere(
        "kr_head", mats["kr_skin"], (0, 0.02, 1.66), 0.14,
        scale=(1.0, 1.05, 1.08))
    objs["kr_hair"] = bl.lathe(
        "kr_hair", mats["kr_hair"],
        [(0.02, 1.84), (0.17, 1.79), (0.195, 1.66), (0.175, 1.55),
         (0.14, 1.50), (0.10, 1.47)],
        segments=24, force_outward=True, **OPEN)
    for side, x in (("L", 1), ("R", -1)):
        objs[f"kr_eye_{side}"] = bl.sphere(
            f"kr_eye_{side}", mats["kr_dark"],
            (0.055 * x, 0.145, 1.675), 0.024, u=8, v=6)
    objs["kr_mouth"] = bl.sphere(
        "kr_mouth", mats["kr_dark"], (0, 0.135, 1.585), 0.055,
        scale=(1.0, 0.5, 0.9), u=10, v=8)
    objs["kr_jaw"] = bl.sphere(
        "kr_jaw", mats["kr_skin"], (0, 0.115, 1.505), 0.085,
        scale=(1.0, 1.1, 0.55), u=12, v=8)
    objs["kr_gut1"] = organ_tube(
        "kr_gut1", mats["kr_organ"],
        [(0.02, 0.01, 1.50), (0.10, -0.02, 1.35), (0.02, 0.05, 1.18),
         (0.12, 0.00, 1.02)])
    objs["kr_gut2"] = organ_tube(
        "kr_gut2", mats["kr_organ"],
        [(-0.03, 0.00, 1.49), (-0.12, 0.03, 1.30), (-0.02, -0.03, 1.12),
         (-0.10, 0.02, 0.95)])
    objs["kr_gut3"] = organ_tube(
        "kr_gut3", mats["kr_organ"],
        [(0.00, 0.02, 1.47), (0.05, 0.10, 1.25), (-0.06, 0.05, 1.05),
         (0.03, 0.10, 0.88)])
    objs["kr_heart"] = bl.sphere(
        "kr_heart", mats["kr_heart"], (0.09, 0.02, 1.28), 0.07,
        scale=(0.85, 1.0, 1.15), u=10, v=8)
    objs["kr_stomach"] = bl.sphere(
        "kr_stomach", mats["kr_organ"], (-0.05, 0.00, 1.12), 0.06,
        scale=(1.1, 0.9, 0.8), u=10, v=8)
    return objs


def build_rig(objs):
    bones = [
        ("Root", None, (0, 0, 0.0), (0, 0, 0.45), False),
        ("Head", "Root", (0, 0, 1.55), (0, 0, 1.78), True),
        ("Jaw", "Head", (0, 0.10, 1.60), (0, 0.14, 1.48), True),
        ("Organ1", "Head", (0, 0, 1.48), (0.01, 0, 1.24), True),
        ("Organ2", "Organ1", (0.01, 0, 1.24), (-0.01, 0.01, 1.00), True),
        ("Organ3", "Organ2", (-0.01, 0.01, 1.00),
         (0.01, -0.01, 0.80), True),
    ]
    arm = bl.build_armature("Krasue_Armature", bones)

    head_rule = [("Head", lambda c: True)]
    for name in ("kr_head", "kr_hair", "kr_eye_L", "kr_eye_R", "kr_mouth"):
        bl.parent_and_skin(objs[name], arm, head_rule)
    bl.parent_and_skin(objs["kr_jaw"], arm, [("Jaw", lambda c: True)])

    # organs: parent each mesh once, then z-band the verts to 3 bones
    organ_meshes = ("kr_gut1", "kr_gut2", "kr_gut3", "kr_heart",
                    "kr_stomach")
    for name in organ_meshes:
        bl.parent_to(objs[name], arm)
        bl.add_group_rule(objs[name], "Organ1", lambda c: c.z > 1.36)
        bl.add_group_rule(objs[name], "Organ2",
                          lambda c: 1.10 < c.z <= 1.36)
        bl.add_group_rule(objs[name], "Organ3", lambda c: c.z <= 1.10)
    return arm


def add_clips(arm):
    # Float — 96 f loop: bob, tilt, organs sway out of phase
    def float_(f):
        t = 2 * math.pi * (f - 1) / 96
        return {
            "Root": {"loc": (0, 0, 0.06 * math.sin(t))},
            "Head": {"rot": (3 * math.sin(2 * t), 5 * math.sin(t),
                             2 * math.sin(t + math.pi / 3))},
            "Jaw": {"rot": (2 + 2 * math.sin(2 * t), 0, 0)},
            "Organ1": {"rot": (8 * math.sin(t), 3 * math.sin(t + 0.4), 0)},
            "Organ2": {"rot": (8 * math.sin(t + math.pi / 3),
                               3 * math.sin(t + 0.9), 0)},
            "Organ3": {"rot": (8 * math.sin(t + 2 * math.pi / 3),
                               3 * math.sin(t + 1.4), 0)},
        }

    # Lunge — 30 f one-shot: wind back, dart, snap back
    def lunge_keys():
        H = lambda loc, rot: {"loc": loc, "rot": rot}  # noqa: E731
        S = lambda rot: {"rot": rot}  # noqa: E731
        rest = lambda: {  # noqa: E731
            "Root": H((0, 0, 0), (0, 0, 0)), "Head": S((0, 0, 0)),
            "Jaw": S((0, 0, 0)), "Organ1": S((0, 0, 0)),
            "Organ2": S((0, 0, 0)), "Organ3": S((0, 0, 0))}
        return [
            (1, rest()),
            (5, {"Root": H((0, -0.10, 0.05), (0, 0, 0)),
                 "Head": S((-12, 0, 0)), "Jaw": S((8, 0, 0)),
                 "Organ1": S((-8, 0, 0)), "Organ2": S((-8, 0, 0)),
                 "Organ3": S((-8, 0, 0))}),
            (9, {"Root": H((0, 0.42, -0.02), (0, 0, 0)),
                 "Head": S((18, 0, 0)), "Jaw": S((55, 0, 0)),
                 "Organ1": S((-28, 0, 0)), "Organ2": S((-28, 0, 0)),
                 "Organ3": S((-28, 0, 0))}),
            (15, {"Root": H((0, 0.40, 0.0), (0, 0, 0)),
                  "Head": S((16, 0, 0)), "Jaw": S((50, 0, 0)),
                  "Organ1": S((-22, 0, 0)), "Organ2": S((-22, 0, 0)),
                  "Organ3": S((-22, 0, 0))}),
            (30, rest()),
        ]

    # Scream — 36 f one-shot: jaw hangs, head trembles
    def scream_keys():
        keys = [(1, {"Root": {"loc": (0, 0, 0), "rot": (0, 0, 0)},
                     "Head": {"rot": (0, 0, 0)},
                     "Jaw": {"rot": (0, 0, 0)}})]
        for f in range(4, 33, 3):
            side = 7 if (f // 3) % 2 == 0 else -7
            keys.append((f, {
                "Root": {"loc": (0, 0, 0.008 * math.sin(7 * f))},
                "Head": {"rot": (-9, 2 * math.sin(f), side)},
                "Jaw": {"rot": (60 + 4 * math.sin(5 * f), 0, 0)}}))
        keys.append((36, {"Root": {"loc": (0, 0, 0), "rot": (0, 0, 0)},
                          "Head": {"rot": (0, 0, 0)},
                          "Jaw": {"rot": (0, 0, 0)}}))
        return keys

    bl.add_clip(arm, "Float", 96, float_)
    bl.add_clip(arm, "Lunge", 30, bl.pose_from_keys(lunge_keys()))
    bl.add_clip(arm, "Scream", 36, bl.pose_from_keys(scream_keys()))


def main():
    bl.clear_scene()
    objs = build_meshes()
    arm = build_rig(objs)
    add_clips(arm)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bl.export_fbx(OUT)
    bl.report("Krasue")


main()
print("BUILD KRASUE OK")
