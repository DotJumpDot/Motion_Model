"""Build the Ghost Woman (Mae Nak style, v0.2) and export FBX.

Headless run:
    blender --background --python src/blender/build_ghost.py

Output: assets/fbx/Ghost_Woman.fbx — textured mesh + 9-bone rig +
clips Idle/Walk/Attack. v0.2: Sadako-style face-covering hair with a
narrow slit and one pale eye, torn-hem grubby dress, bare ankles and
feet, skinny drooping hands, procedural grunge textures.
Design spec: Docs/CONCEPT.md.
"""

import math
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_lib as bl  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TEXDIR = os.path.join(REPO, "assets", "textures")
OUT = os.path.join(REPO, "assets", "fbx", "Ghost_Woman.fbx")

# Hair covers everything except a narrow slit at the front (+Y)
SLIT_DEG = 18.0
OPEN = {"start_angle": (90 + SLIT_DEG / 2) * bl.DEG,
        "sweep": (360 - SLIT_DEG) * bl.DEG}


def build_textures():
    os.makedirs(TEXDIR, exist_ok=True)
    tex = {}
    # dirty faded dress fabric: stains, fold streaks, hem grime
    tex["gw_dress"] = bl.make_texture(
        "gw_dress", 1024, base=(0.42, 0.40, 0.37),
        blotch=(0.20, 0.17, 0.13), blotch_amount=0.7, blotch_seed=4,
        streak=((0.22, 0.20, 0.17), 24, 0.18), dirt_bottom=0.9, seed=2,
        out_dir=TEXDIR)
    # corpse skin: pale with grey-blue mottling and grime
    tex["gw_skin"] = bl.make_texture(
        "gw_skin", 1024, base=(0.58, 0.57, 0.58),
        blotch=(0.36, 0.39, 0.45), blotch_amount=0.75, blotch_seed=9,
        dirt_bottom=0.35, seed=7, out_dir=TEXDIR)
    # hair: dark with visible hanging strand streaks
    tex["gw_hair"] = bl.make_texture(
        "gw_hair", 512, base=(0.085, 0.075, 0.070),
        blotch=(0.17, 0.155, 0.145), blotch_amount=0.6, blotch_seed=5,
        streak=((0.26, 0.24, 0.22), 36, 1.4), seed=6, out_dir=TEXDIR)
    return tex


def build_meshes(tex):
    mats = {
        "gw_dress": bl.textured_material("gw_dress", tex["gw_dress"],
                                         rough=0.92),
        "gw_skin": bl.textured_material("gw_skin", tex["gw_skin"],
                                        rough=0.65),
        "gw_hair": bl.textured_material("gw_hair", tex["gw_hair"],
                                        rough=0.55),
        "gw_shadow": bl.flat_material("gw_shadow",
                                      (0.015, 0.013, 0.012, 1.0)),
        "gw_eye": bl.flat_material("gw_eye",
                                   (0.02, 0.015, 0.015, 1.0), rough=0.3),
        "gw_iris": bl.flat_material("gw_iris",
                                    (0.62, 0.60, 0.55, 1.0), rough=0.2),
    }
    objs = {}

    # Slim gathered-waist dress; the top tapers into a NECK ring that
    # pokes up inside the head sphere, so head and body read as one
    hem = 0.27
    objs["gw_dress"] = d = bl.lathe(
        "gw_dress", mats["gw_dress"],
        [(0.03, hem), (0.24, hem + 0.02), (0.235, hem + 0.28),
         (0.215, hem + 0.55), (0.165, hem + 0.90), (0.13, 1.17),
         (0.145, 1.27), (0.115, 1.36), (0.065, 1.43), (0.058, 1.465)],
        segments=24)  # no top cap: the opening hides inside the head
    rng = np.random.default_rng(11)
    jit = rng.uniform(0.88, 1.14, 64)

    def torn(c):
        return c.z < hem + 0.035

    def tear(c):
        i = int(abs(c.x * 173 + c.y * 61) * 100) % 64
        r = math.hypot(c.x, c.y) * jit[i]
        return (c.x * r / max(math.hypot(c.x, c.y), 1e-6),
                c.y * r / max(math.hypot(c.x, c.y), 1e-6),
                c.z + (jit[(i + 7) % 64] - 1.0) * 0.05)

    bl.displace_verts(d, torn, tear)
    bl.shade_smooth(d)

    # Head: slim, slightly forward (hunch)
    objs["gw_head"] = h = bl.sphere(
        "gw_head", mats["gw_skin"], (0, 0.03, 1.55), 0.125,
        scale=(0.88, 0.95, 1.10), u=24, v=16)
    bl.shade_smooth(h)

    # Hair: bob-cut curtain hugging the head, ending AT the
    # shoulders (no slab over the chest), narrow crevice slit; two
    # side panels fall over the chest edges like the reference
    objs["gw_hair"] = hair = bl.lathe(
        "gw_hair", mats["gw_hair"],
        [(0.02, 1.72), (0.14, 1.69), (0.165, 1.55), (0.16, 1.38),
         (0.15, 1.22), (0.145, 1.10)],
        segments=24, force_outward=True, **OPEN)
    bl.shade_smooth(hair)
    for side, ang in (("L", 115), ("R", 65)):
        objs[f"gw_hairside_{side}"] = hs = bl.lathe(
            f"gw_hairside_{side}", mats["gw_hair"],
            [(0.148, 1.32), (0.160, 1.20), (0.170, 1.06),
             (0.176, 0.94), (0.170, 0.90)],
            segments=8, start_angle=ang * bl.DEG, sweep=60 * bl.DEG,
            force_outward=True)
        bl.shade_smooth(hs)

    # Single pale eye peeking through the slit (socket + iris)
    objs["gw_eye"] = e = bl.sphere(
        "gw_eye", mats["gw_eye"], (0.0, 0.140, 1.548), 0.030,
        u=10, v=8)
    bl.shade_smooth(e)
    objs["gw_iris"] = i = bl.sphere(
        "gw_iris", mats["gw_iris"], (0.0, 0.157, 1.550), 0.014,
        u=8, v=6)
    bl.shade_smooth(i)

    # Shadow gap under the hem + bare feet (weighted to Hips)
    for side, x in (("L", 1), ("R", -1)):
        objs[f"gw_ankle_{side}"] = a = bl.tube(
            f"gw_ankle_{side}", mats["gw_shadow"],
            (0.085 * x, 0.01, hem), (0.08 * x, 0.01, 0.07), 0.034, 0.030)
        bl.shade_smooth(a)
        objs[f"gw_foot_{side}"] = f = bl.sphere(
            f"gw_foot_{side}", mats["gw_skin"],
            (0.08 * x, 0.045, 0.045), 0.042,
            scale=(0.70, 1.55, 0.50), u=10, v=8)
        bl.shade_smooth(f)

    # Arms: skinny, hanging slightly out from the dress, hands drooped
    for side, x in (("L", 1), ("R", -1)):
        sh = (0.145 * x, 0.02, 1.34)
        el = (0.155 * x, 0.06, 1.10)
        wr = (0.150 * x, 0.11, 0.90)
        tip = (0.142 * x, 0.16, 0.80)
        # extend each segment ~2 cm past the joint so the caps
        # overlap instead of leaving elbow gaps
        up_end = tuple(a + (b - a) * 0.12 for a, b in zip(sh, el))
        fo_end = tuple(a + (b - a) * 0.12 for a, b in zip(el, wr))
        fo_start = tuple(a + (b - a) * -0.10 for a, b in zip(el, wr))
        ha_start = tuple(a + (b - a) * -0.12 for a, b in zip(wr, tip))
        objs[f"gw_upperarm_{side}"] = ua = bl.tube(
            f"gw_upperarm_{side}", mats["gw_skin"], sh, up_end, 0.046,
            0.036)
        objs[f"gw_forearm_{side}"] = fa = bl.tube(
            f"gw_forearm_{side}", mats["gw_skin"], fo_start, fo_end,
            0.034, 0.026)
        objs[f"gw_hand_{side}"] = ha = bl.sphere(
            f"gw_hand_{side}", mats["gw_skin"],
            ((wr[0] + tip[0]) / 2, (wr[1] + tip[1]) / 2,
             (wr[2] + tip[2]) / 2), 0.034,
            scale=(0.8, 1.15, 1.35), u=10, v=8)
        for o in (ua, fa, ha):
            bl.shade_smooth(o)
        # three spindly fingers, static on the hand
        for fi in range(3):
            fx = (0.132 + 0.020 * fi) * x
            objs[f"gw_finger_{side}{fi}"] = fg = bl.tube(
                f"gw_finger_{side}{fi}", mats["gw_skin"],
                (fx, 0.145, 0.83), (fx - 0.004 * x, 0.195 - 0.02 * fi,
                                    0.745 - 0.01 * fi),
                0.011, 0.005, segments=6)
            bl.shade_smooth(fg)

        # short sleeve overlapping the dress shoulder
        objs[f"gw_sleeve_{side}"] = sv = bl.tube(
            f"gw_sleeve_{side}", mats["gw_dress"],
            (0.135 * x, 0.02, 1.35), (0.150 * x, 0.045, 1.21),
            0.072, 0.058, segments=12)
        bl.shade_smooth(sv)
    return objs


def build_rig(objs):
    bones = [
        ("Hips", None, (0, 0, 0.80), (0, 0, 0.95), True),
        ("Spine", "Hips", (0, 0, 0.95), (0, 0, 1.24), True),
        ("Head", "Spine", (0, 0, 1.24), (0, 0, 1.48), True),
        ("UpperArm_L", "Spine", (0.145, 0.02, 1.34),
         (0.155, 0.06, 1.10), True),
        ("Forearm_L", "UpperArm_L", (0.155, 0.06, 1.10),
         (0.150, 0.11, 0.90), True),
        ("Hand_L", "Forearm_L", (0.150, 0.11, 0.90),
         (0.142, 0.16, 0.80), True),
        ("UpperArm_R", "Spine", (-0.145, 0.02, 1.34),
         (-0.155, 0.06, 1.10), True),
        ("Forearm_R", "UpperArm_R", (-0.155, 0.06, 1.10),
         (-0.150, 0.11, 0.90), True),
        ("Hand_R", "Forearm_R", (-0.150, 0.11, 0.90),
         (-0.142, 0.16, 0.80), True),
    ]
    arm = bl.build_armature("GhostWoman_Armature", bones)

    bl.parent_and_skin(objs["gw_dress"], arm, [("Spine", lambda c: True)])
    head_rule = [("Head", lambda c: True)]
    for k in ("gw_head", "gw_hair", "gw_hairside_L", "gw_hairside_R",
              "gw_eye", "gw_iris"):
        bl.parent_and_skin(objs[k], arm, head_rule)
    hips_rule = [("Hips", lambda c: True)]
    for side in ("L", "R"):
        bl.parent_and_skin(objs[f"gw_ankle_{side}"], arm, hips_rule)
        bl.parent_and_skin(objs[f"gw_foot_{side}"], arm, hips_rule)
        bl.parent_and_skin(objs[f"gw_upperarm_{side}"], arm,
                           [(f"UpperArm_{side}", lambda c: True)])
        bl.parent_and_skin(objs[f"gw_forearm_{side}"], arm,
                           [(f"Forearm_{side}", lambda c: True)])
        bl.parent_and_skin(objs[f"gw_hand_{side}"], arm,
                           [(f"Hand_{side}", lambda c: True)])
        for fi in range(3):
            bl.parent_and_skin(objs[f"gw_finger_{side}{fi}"], arm,
                               [(f"Hand_{side}", lambda c: True)])
        bl.parent_and_skin(objs[f"gw_sleeve_{side}"], arm,
                           [(f"UpperArm_{side}", lambda c: True)])
    return arm


def add_clips(arm):
    # Idle — 96 f (3.2 s) loop: wrong-breathing sway + a head twitch
    def idle(f):
        t = 2 * math.pi * (f - 1) / 96
        head = {"rot": (2 * math.sin(2 * t), 0, 3 * math.sin(t))}
        if 45 <= f <= 52:  # glitch snap
            k = 14 if f <= 47 else (8 if f <= 49 else
                                    (4 if f <= 51 else 0))
            head["rot"] = (head["rot"][0], head["rot"][1],
                           3 * math.sin(t) + k)
        return {
            "Hips": {"loc": (0, 0, 0.010 * math.sin(t))},
            "Spine": {"rot": (0, 2.5 * math.sin(t), 0)},
            "Head": head,
            "UpperArm_L": {"rot": (3 * math.sin(t), 0, 0)},
            "UpperArm_R": {"rot": (3 * math.sin(t + math.pi), 0, 0)},
            "Forearm_L": {"rot": (4 * math.sin(t + math.pi / 2), 0, 0)},
            "Forearm_R": {"rot":
                          (4 * math.sin(t + math.pi / 2 + math.pi), 0, 0)},
        }

    # Walk — 48 f (1.6 s) loop: slow dragging shuffle
    def walk(f):
        t = 2 * math.pi * (f - 1) / 48
        return {
            "Hips": {"loc": (0, 0, 0.010 * (1 - math.cos(2 * t)))},
            "Spine": {"rot": (7 + 2 * math.sin(2 * t), 3 * math.sin(t),
                              0)},
            "Head": {"rot": (-5, 0, 4 * math.sin(t))},
            "UpperArm_L": {"rot": (5 + 7 * math.sin(t),
                                   0, 2 * math.sin(t))},
            "UpperArm_R": {"rot": (5 + 7 * math.sin(t + math.pi),
                                   0, 2 * math.sin(t + math.pi))},
            "Forearm_L": {"rot": (8 + 4 * math.sin(t + 0.8), 0, 0)},
            "Forearm_R": {"rot":
                          (8 + 4 * math.sin(t + 0.8 + math.pi), 0, 0)},
        }

    # Attack — 36 f (1.2 s) one-shot: arms snap up from hanging,
    # lunge forward, snap back
    def attack_keys():
        H = lambda loc, rot: {"loc": loc, "rot": rot}  # noqa: E731
        S = lambda rot: {"rot": rot}  # noqa: E731
        rest = lambda: {  # noqa: E731
            "Hips": H((0, 0, 0), (0, 0, 0)), "Spine": S((0, 0, 0)),
            "Head": S((0, 0, 0)),
            "UpperArm_L": S((0, 0, 0)), "UpperArm_R": S((0, 0, 0)),
            "Forearm_L": S((0, 0, 0)), "Forearm_R": S((0, 0, 0))}
        return [
            (1, rest()),
            (7, {"Hips": H((0, 0, 0.025), (0, 0, 0)),
                 "Spine": S((-9, 0, 0)), "Head": S((0, 0, -7)),
                 "UpperArm_L": S((118, 0, 0)), "UpperArm_R": S((118, 0, 0)),
                 "Forearm_L": S((30, 0, 0)), "Forearm_R": S((30, 0, 0))}),
            (14, {"Hips": H((0, 0.17, 0.01), (0, 0, 0)),
                  "Spine": S((20, 0, 0)), "Head": S((14, 0, 0)),
                  "UpperArm_L": S((-30, 0, -14)),
                  "UpperArm_R": S((-30, 0, 14)),
                  "Forearm_L": S((-18, 0, 0)), "Forearm_R": S((-18, 0, 0))}),
            (22, {"Hips": H((0, 0.18, 0.004), (0, 0, 0)),
                  "Spine": S((17, 0, 2)), "Head": S((11, 0, 4)),
                  "UpperArm_L": S((-24, 0, -14)),
                  "UpperArm_R": S((-24, 0, 14)),
                  "Forearm_L": S((-12, 0, 0)), "Forearm_R": S((-12, 0, 0))}),
            (36, rest()),
        ]

    bl.add_clip(arm, "Idle", 96, idle)
    bl.add_clip(arm, "Walk", 48, walk)
    bl.add_clip(arm, "Attack", 36, bl.pose_from_keys(attack_keys()))


def main():
    bl.clear_scene()
    tex = build_textures()
    objs = build_meshes(tex)
    arm = build_rig(objs)
    add_clips(arm)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bl.export_fbx(OUT)
    bl.report("GhostWoman")


main()
print("BUILD GHOST OK")
