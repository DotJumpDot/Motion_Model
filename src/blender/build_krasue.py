"""Build the Krasue (v0.2) and export FBX.

Headless run:
    blender --background --python src/blender/build_krasue.py

Output: assets/fbx/Krasue.fbx — floating head + trailing organs,
7-bone rig... 6 bones (Root non-deform + Head/Jaw/Organ1-3), clips
Float/Lunge/Scream. v0.2: teeth, dark staring eyes with pale irises,
procedural mottled/blood textures. Design spec: Docs/CONCEPT.md.
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_lib as bl  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TEXDIR = os.path.join(REPO, "assets", "textures")
OUT = os.path.join(REPO, "assets", "fbx", "Krasue.fbx")

# Hair is a CAP on top/back — the face stays fully exposed (severed
# head look), opening of 150 degrees centred at +Y
OPEN = {"start_angle": (90 + 75) * bl.DEG, "sweep": (360 - 150) * bl.DEG}


def build_textures():
    os.makedirs(TEXDIR, exist_ok=True)
    tex = {}
    # pallid warm skin with heavy bruise mottling
    tex["kr_skin"] = bl.make_texture(
        "kr_skin", 1024, base=(0.72, 0.65, 0.57),
        blotch=(0.34, 0.20, 0.19), blotch_amount=0.8, blotch_seed=13,
        dirt_bottom=0.35, seed=12, out_dir=TEXDIR)
    # hanging strands
    tex["kr_hair"] = bl.make_texture(
        "kr_hair", 512, base=(0.065, 0.055, 0.050),
        blotch=(0.13, 0.11, 0.10), blotch_amount=0.55, blotch_seed=15,
        streak=((0.22, 0.20, 0.185), 42, 1.1), seed=14, out_dir=TEXDIR)
    # wet organs: dark red with blackish veins
    tex["kr_organ"] = bl.make_texture(
        "kr_organ", 512, base=(0.40, 0.10, 0.09),
        blotch=(0.12, 0.025, 0.025), blotch_amount=0.85, blotch_seed=17,
        streak=((0.06, 0.012, 0.012), 40, 0.9), seed=16, out_dir=TEXDIR)
    return tex


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


def build_meshes(tex):
    mats = {
        "kr_skin": bl.textured_material("kr_skin", tex["kr_skin"],
                                         rough=0.6),
        "kr_hair": bl.textured_material("kr_hair", tex["kr_hair"],
                                        rough=0.55),
        "kr_organ": bl.textured_material("kr_organ", tex["kr_organ"],
                                         rough=0.35),
        "kr_dark": bl.flat_material("kr_dark",
                                    (0.02, 0.012, 0.012, 1.0), rough=0.4),
        "kr_iris": bl.flat_material("kr_iris",
                                    (0.68, 0.66, 0.60, 1.0), rough=0.15),
        "kr_tooth": bl.flat_material("kr_tooth",
                                     (0.72, 0.69, 0.58, 1.0), rough=0.35),
    }
    objs = {}
    objs["kr_head"] = h = bl.sphere(
        "kr_head", mats["kr_skin"], (0, 0.02, 1.66), 0.14,
        scale=(1.0, 1.05, 1.08), u=24, v=16)
    bl.shade_smooth(h)
    objs["kr_hair"] = hair = bl.lathe(
        "kr_hair", mats["kr_hair"],
        [(0.02, 1.83), (0.155, 1.80), (0.175, 1.70), (0.155, 1.60),
         (0.105, 1.545), (0.05, 1.525)],
        segments=24, force_outward=True, **OPEN)
    bl.shade_smooth(hair)

    # staring eyes on the exposed face: dark sockets, pale irises
    for side, x in (("L", 1), ("R", -1)):
        objs[f"kr_eye_{side}"] = e = bl.sphere(
            f"kr_eye_{side}", mats["kr_dark"],
            (0.055 * x, 0.145, 1.675), 0.032, u=10, v=8)
        bl.shade_smooth(e)
        objs[f"kr_iris_{side}"] = ir = bl.sphere(
            f"kr_iris_{side}", mats["kr_iris"],
            (0.047 * x, 0.170, 1.668), 0.013, u=8, v=6)
        bl.shade_smooth(ir)

    # gaping unhinged mouth (dark hollow) + jaw
    objs["kr_mouth"] = m = bl.sphere(
        "kr_mouth", mats["kr_dark"], (0, 0.140, 1.585), 0.060,
        scale=(1.0, 0.45, 1.0), u=12, v=10)
    bl.shade_smooth(m)
    objs["kr_jaw"] = j = bl.sphere(
        "kr_jaw", mats["kr_skin"], (0, 0.10, 1.502), 0.080,
        scale=(1.15, 1.05, 0.5), u=14, v=10)
    bl.shade_smooth(j)

    # teeth: two rows of small cones framing the mouth
    up, lo = [], []
    for ti in range(5):
        x = -0.044 + 0.022 * ti
        up.append(((x, 0.163, 1.618), (x, 0.160, 1.600)))
        lo.append(((x, 0.152, 1.546), (x, 0.154, 1.564)))

    def teeth_mesh(name, pairs, mat):
        import bmesh
        from mathutils import Matrix, Vector
        bm = bmesh.new()
        for start, end in pairs:
            d = Vector(end) - Vector(start)
            mid = (Vector(start) + Vector(end)) / 2
            mtx = Matrix.Translation(mid) @ \
                d.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
            bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True,
                                  segments=6, radius1=0.009, radius2=0.001,
                                  depth=d.length, matrix=mtx)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name, mesh)
        bl.link(obj)
        obj.data.materials.append(mat)
        return obj

    objs["kr_teeth_up"] = teeth_mesh("kr_teeth_up", up, mats["kr_tooth"])
    objs["kr_teeth_lo"] = teeth_mesh("kr_teeth_lo", lo, mats["kr_tooth"])

    # organ trail
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
    objs["kr_heart"] = hrt = bl.sphere(
        "kr_heart", mats["kr_organ"], (0.09, 0.02, 1.28), 0.07,
        scale=(0.85, 1.0, 1.15), u=12, v=10)
    bl.shade_smooth(hrt)
    objs["kr_stomach"] = st = bl.sphere(
        "kr_stomach", mats["kr_organ"], (-0.05, 0.00, 1.12), 0.06,
        scale=(1.1, 0.9, 0.8), u=12, v=10)
    bl.shade_smooth(st)
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
    for name in ("kr_head", "kr_hair", "kr_eye_L", "kr_eye_R",
                 "kr_iris_L", "kr_iris_R", "kr_mouth", "kr_teeth_up"):
        bl.parent_and_skin(objs[name], arm, head_rule)
    bl.parent_and_skin(objs["kr_jaw"], arm, [("Jaw", lambda c: True)])
    bl.parent_and_skin(objs["kr_teeth_lo"], arm,
                       [("Jaw", lambda c: True)])

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
                 "Head": S((18, 0, 0)), "Jaw": S((60, 0, 0)),
                 "Organ1": S((-28, 0, 0)), "Organ2": S((-28, 0, 0)),
                 "Organ3": S((-28, 0, 0))}),
            (15, {"Root": H((0, 0.40, 0.0), (0, 0, 0)),
                  "Head": S((16, 0, 0)), "Jaw": S((55, 0, 0)),
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
                "Jaw": {"rot": (62 + 4 * math.sin(5 * f), 0, 0)}}))
        keys.append((36, {"Root": {"loc": (0, 0, 0), "rot": (0, 0, 0)},
                          "Head": {"rot": (0, 0, 0)},
                          "Jaw": {"rot": (0, 0, 0)}}))
        return keys

    bl.add_clip(arm, "Float", 96, float_)
    bl.add_clip(arm, "Lunge", 30, bl.pose_from_keys(lunge_keys()))
    bl.add_clip(arm, "Scream", 36, bl.pose_from_keys(scream_keys()))


def main():
    bl.clear_scene()
    tex = build_textures()
    objs = build_meshes(tex)
    arm = build_rig(objs)
    add_clips(arm)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bl.export_fbx(OUT)
    bl.report("Krasue")


main()
print("BUILD KRASUE OK")
