"""Build the Ghost Woman (Mae Nak style, v0.1) and export FBX.

Headless run:
    blender --background --python src/blender/build_ghost.py

Output: assets/fbx/Ghost_Woman.fbx — mesh + 11-bone rig + clips
Idle/Walk/Attack. See Docs/CONCEPT.md for the design spec.
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_lib as bl  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
OUT = os.path.join(REPO, "assets", "fbx", "Ghost_Woman.fbx")

# Palette from Docs/CONCEPT.md
SKIN = (0.910, 0.902, 0.874, 1.0)   # corpse pale   #E8E6DF
DRESS = (0.855, 0.835, 0.788, 1.0)  # faded white   #DAD5C9
HAIR = (0.078, 0.063, 0.055, 1.0)   # near black    #14100E
EYES = (0.478, 0.055, 0.071, 1.0)   # blood red     #7A0E12


def build_meshes():
    mats = {
        "gw_skin": bl.flat_material("gw_skin", SKIN),
        "gw_dress": bl.flat_material("gw_dress", DRESS),
        "gw_hair": bl.flat_material("gw_hair", HAIR),
        "gw_eyes": bl.flat_material("gw_eyes", EYES, rough=0.4),
    }
    # Hair curtain: 270-degree sweep, opening centred on +Y (the face)
    OPEN = {"start_angle": 135 * bl.DEG, "sweep": 270 * bl.DEG}

    objs = {}
    objs["gw_dress"] = bl.lathe(
        "gw_dress", mats["gw_dress"],
        [(0.04, 0.00), (0.46, 0.02), (0.43, 0.30), (0.33, 0.62),
         (0.23, 0.95), (0.17, 1.18), (0.20, 1.32), (0.15, 1.42),
         (0.10, 1.50)],
        segments=16, caps=("bottom", "top"))
    objs["gw_head"] = bl.sphere(
        "gw_head", mats["gw_skin"], (0, 0.01, 1.60), 0.13,
        scale=(0.95, 1.0, 1.15))
    objs["gw_hair"] = bl.lathe(
        "gw_hair", mats["gw_hair"],
        [(0.02, 1.80), (0.16, 1.75), (0.20, 1.58), (0.19, 1.34),
         (0.165, 1.05), (0.14, 0.90)],
        segments=24, force_outward=True, **OPEN)
    for side, x in (("L", 1), ("R", -1)):
        objs[f"gw_eye_{side}"] = bl.sphere(
            f"gw_eye_{side}", mats["gw_eyes"],
            (0.05 * x, 0.125, 1.575), 0.026, u=8, v=6)
        objs[f"gw_upperarm_{side}"] = bl.tube(
            f"gw_upperarm_{side}", mats["gw_skin"],
            (0.13 * x, 0.02, 1.38), (0.24 * x, 0.30, 1.20),
            0.060, 0.050)
        objs[f"gw_forearm_{side}"] = bl.tube(
            f"gw_forearm_{side}", mats["gw_skin"],
            (0.24 * x, 0.30, 1.20), (0.28 * x, 0.52, 1.08),
            0.048, 0.038)
        objs[f"gw_hand_{side}"] = bl.sphere(
            f"gw_hand_{side}", mats["gw_skin"],
            ((0.28 + 0.295) / 2 * x, (0.52 + 0.65) / 2, (1.08 + 1.03) / 2),
            0.045, scale=(0.85, 1.5, 0.7), u=8, v=6)
    return objs


def build_rig(objs):
    bones = [
        ("Hips", None, (0, 0, 0.92), (0, 0, 1.06), True),
        ("Spine", "Hips", (0, 0, 1.06), (0, 0, 1.38), True),
        ("Head", "Spine", (0, 0, 1.38), (0, 0, 1.62), True),
        ("UpperArm_L", "Spine", (0.13, 0.02, 1.38),
         (0.24, 0.30, 1.20), True),
        ("Forearm_L", "UpperArm_L", (0.24, 0.30, 1.20),
         (0.28, 0.52, 1.08), True),
        ("Hand_L", "Forearm_L", (0.28, 0.52, 1.08),
         (0.295, 0.65, 1.03), True),
        ("UpperArm_R", "Spine", (-0.13, 0.02, 1.38),
         (-0.24, 0.30, 1.20), True),
        ("Forearm_R", "UpperArm_R", (-0.24, 0.30, 1.20),
         (-0.28, 0.52, 1.08), True),
        ("Hand_R", "Forearm_R", (-0.28, 0.52, 1.08),
         (-0.295, 0.65, 1.03), True),
    ]
    arm = bl.build_armature("GhostWoman_Armature", bones)

    bl.parent_and_skin(objs["gw_dress"], arm, [("Spine", lambda c: True)])
    head_rule = [("Head", lambda c: True)]
    for k in ("gw_head", "gw_hair", "gw_eye_L", "gw_eye_R"):
        bl.parent_and_skin(objs[k], arm, head_rule)
    for side in ("L", "R"):
        bl.parent_and_skin(objs[f"gw_upperarm_{side}"], arm,
                           [(f"UpperArm_{side}", lambda c: True)])
        bl.parent_and_skin(objs[f"gw_forearm_{side}"], arm,
                           [(f"Forearm_{side}", lambda c: True)])
        bl.parent_and_skin(objs[f"gw_hand_{side}"], arm,
                           [(f"Hand_{side}", lambda c: True)])
    return arm


def add_clips(arm):
    # Idle — 96 f (3.2 s) loop: wrong-breathing sway
    def idle(f):
        t = 2 * math.pi * (f - 1) / 96
        return {
            "Hips": {"loc": (0, 0, 0.012 * math.sin(t))},
            "Spine": {"rot": (0, 2.5 * math.sin(t), 0)},
            "Head": {"rot": (2 * math.sin(2 * t), 0, 3 * math.sin(t))},
            "UpperArm_L": {"rot": (4 * math.sin(t), 0, 0)},
            "UpperArm_R": {"rot": (4 * math.sin(t + math.pi), 0, 0)},
            "Forearm_L": {"rot": (3 * math.sin(t + math.pi / 2), 0, 0)},
            "Forearm_R": {"rot":
                          (3 * math.sin(t + math.pi / 2 + math.pi), 0, 0)},
        }

    # Walk — 48 f (1.6 s) loop: hip-driven shuffle, no feet
    def walk(f):
        t = 2 * math.pi * (f - 1) / 48
        return {
            "Hips": {"loc": (0, 0, 0.018 * (1 - math.cos(2 * t)))},
            "Spine": {"rot": (6 + 2 * math.sin(2 * t), 3 * math.sin(t), 0)},
            "Head": {"rot": (-4, 0, 4 * math.sin(t))},
            "UpperArm_L": {"rot": (5 + 10 * math.sin(t),
                                   0, 2 * math.sin(t))},
            "UpperArm_R": {"rot": (5 + 10 * math.sin(t + math.pi),
                                   0, 2 * math.sin(t + math.pi))},
            "Forearm_L": {"rot": (10 + 5 * math.sin(t + 0.8), 0, 0)},
            "Forearm_R": {"rot":
                          (10 + 5 * math.sin(t + 0.8 + math.pi), 0, 0)},
        }

    # Attack — 36 f (1.2 s) one-shot: arms snap up, lunge, recover
    def attack_keys():
        H = lambda loc, rot: {"loc": loc, "rot": rot}  # noqa: E731
        S = lambda rot: {"rot": rot}  # noqa: E731
        keys = [
            (1, {"Hips": H((0, 0, 0), (0, 0, 0)), "Spine": S((0, 0, 0)),
                 "Head": S((0, 0, 0)),
                 "UpperArm_L": S((0, 0, 0)), "UpperArm_R": S((0, 0, 0)),
                 "Forearm_L": S((0, 0, 0)), "Forearm_R": S((0, 0, 0))}),
            (6, {"Hips": H((0, 0, 0.03), (0, 0, 0)), "Spine": S((-8, 0, 0)),
                 "Head": S((0, 0, -6)),
                 "UpperArm_L": S((95, 0, 0)), "UpperArm_R": S((95, 0, 0)),
                 "Forearm_L": S((20, 0, 0)), "Forearm_R": S((20, 0, 0))}),
            (14, {"Hips": H((0, 0.15, 0.01), (0, 0, 0)),
                  "Spine": S((18, 0, 0)), "Head": S((12, 0, 0)),
                  "UpperArm_L": S((-25, 0, -10)),
                  "UpperArm_R": S((-25, 0, 10)),
                  "Forearm_L": S((-15, 0, 0)), "Forearm_R": S((-15, 0, 0))}),
            (22, {"Hips": H((0, 0.16, 0.005), (0, 0, 0)),
                  "Spine": S((16, 0, 2)), "Head": S((10, 0, 3)),
                  "UpperArm_L": S((-20, 0, -10)),
                  "UpperArm_R": S((-20, 0, 10)),
                  "Forearm_L": S((-10, 0, 0)), "Forearm_R": S((-10, 0, 0))}),
            (36, {"Hips": H((0, 0, 0), (0, 0, 0)), "Spine": S((0, 0, 0)),
                  "Head": S((0, 0, 0)),
                  "UpperArm_L": S((0, 0, 0)), "UpperArm_R": S((0, 0, 0)),
                  "Forearm_L": S((0, 0, 0)), "Forearm_R": S((0, 0, 0))}),
        ]
        return keys

    bl.add_clip(arm, "Idle", 96, idle)
    bl.add_clip(arm, "Walk", 48, walk)
    bl.add_clip(arm, "Attack", 36, bl.pose_from_keys(attack_keys()))


def main():
    bl.clear_scene()
    objs = build_meshes()
    arm = build_rig(objs)
    add_clips(arm)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bl.export_fbx(OUT)
    bl.report("GhostWoman")


main()
print("BUILD GHOST OK")
