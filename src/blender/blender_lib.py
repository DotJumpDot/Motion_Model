"""Shared helpers for Motion_Model headless Blender build scripts.

Target: Blender 5.2 LTS. Everything here runs in background mode
(`blender --background --python script.py`) with no GPU and no
rendering — geometry, armature and keyframes only.

Conventions:
- Z is up, the character faces +Y, origin at ground center.
- Meshes are built in world coordinates; objects keep identity
  transforms, so mesh-local == world (skinning rules rely on this).
"""

import bmesh
import bpy
import math
import os

import numpy as np
from mathutils import Matrix, Vector

DEG = math.pi / 180.0
FPS = 30


# ---------------------------------------------------------------- scene

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def link(obj):
    bpy.context.scene.collection.objects.link(obj)


# ------------------------------------------------------------ materials

def flat_material(name, rgba, rough=0.9):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = rough
    return mat


def textured_material(name, img, rough=0.85):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    return mat


# ------------------------------------------------------------ textures

def _fbm(size, octaves, seed, wrap_u=True):
    """Tileable-in-u value-noise fBm, numpy, 0..1.

    octaves: list of (freq, weight); freq = grid cells across the
    texture. wrap_u makes horizontal seams invisible (cylindrical UVs).
    """
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float64) / size
    acc = np.zeros((size, size))
    for n, w in octaves:
        g = rng.random((n + 1, n + 1))
        if wrap_u:
            g[n, :] = g[0, :]
        if n > 1:
            g[:, n] = g[:, 0]
        gx, gy = xx * n, yy * n
        x0 = np.floor(gx).astype(int)
        y0 = np.floor(gy).astype(int)
        fx, fy = gx - x0, gy - y0
        x1 = np.minimum(x0 + 1, n)
        y1 = np.minimum(y0 + 1, n)
        a = g[y0, x0]
        b = g[y0, x1]
        c = g[y1, x0]
        d = g[y1, x1]
        acc += w * (a * (1 - fx) * (1 - fy) + b * fx * (1 - fy)
                    + c * (1 - fx) * fy + d * fx * fy)
    acc /= sum(w for _, w in octaves)
    return np.clip(acc, 0.0, 1.0)


def _streaks(size, freq, weight, seed):
    """Anisotropic noise: high frequency across u, smooth along v —
    reads as hanging strands on hair / fabric folds."""
    rng = np.random.default_rng(seed)
    n = freq
    g = rng.random((2, n + 1))
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float64) / size
    gx = xx * n
    x0 = np.floor(gx).astype(int)
    fx = gx - x0
    x1 = np.minimum(x0 + 1, n)
    row0 = g[0, x0] * (1 - fx) + g[0, x1] * fx
    row1 = g[1, x0] * (1 - fx) + g[1, x1] * fx
    # vertical blend: one smooth gradient across v (top->bottom drift)
    return weight * (row0 * (1 - yy * 0.3) + row1 * (yy * 0.3))


def make_texture(name, size, base, blotch=None, blotch_amount=0.5,
                 blotch_seed=1, streak=None, dirt_bottom=0.0, seed=3,
                 out_dir=None):
    """Procedural grunge atlas -> bpy image (saved + packed).

    base: (r, g, b) 0..1. blotch: (r, g, b) blended in by
    blotch_amount * fbm. streak: (color, freq, weight) vertical
    strands. dirt_bottom: darken toward v=0 (the hem).
    """
    n = _fbm(size, [(4, 1.0), (16, 0.5), (64, 0.25)], seed)
    col = np.ones((size, size, 3))
    for c in range(3):
        col[:, :, c] = base[c]
    if blotch is not None:
        k = np.clip((n - (1 - blotch_amount)) / max(blotch_amount, 1e-3),
                    0, 1)
        for c in range(3):
            col[:, :, c] = col[:, :, c] * (1 - k) + blotch[c] * k
    if streak is not None:
        s_color, s_freq, s_w = streak
        s = _streaks(size, s_freq, s_w, seed + 11) - 0.5 * s_w
        for c in range(3):
            col[:, :, c] = np.clip(
                col[:, :, c] * (1 + s) + s_color[c] * np.clip(s, 0, 1) * 2,
                0, 1)
    if dirt_bottom > 0:
        yy = np.mgrid[0:size, 0:size][0].astype(np.float64) / size
        k = np.clip(1 - yy * size / (size * 0.45), 0, 1) ** 1.5 \
            * dirt_bottom
        for c in range(3):
            col[:, :, c] *= (1 - k * 0.7)
    rgba = np.ones((size, size, 4))
    rgba[:, :, :3] = col
    img = bpy.data.images.new(name, size, size, alpha=False)
    img.pixels = rgba.ravel().tolist()
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        img.filepath_raw = os.path.join(out_dir, f"{name}.png")
        img.file_format = "PNG"
        img.save()
    img.pack()
    return img


# ---------------------------------------------------------------- mesh

def _obj_from_bmesh(bm, name, mat):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    link(obj)
    if mat is not None:
        obj.data.materials.append(mat)
    return obj


def _force_outward_z(bm):
    """Point shell normals away from the Z axis (open lathes only)."""
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(Vector((c.x, c.y, 0.0))) < 0:
            f.normal_flip()


def _cyl_uv(bm, zmin, zmax):
    """Cylindrical UVs by vertex position (u = angle, v = height)."""
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for loop in f.loops:
            v = loop.vert
            loop[uv].uv = ((math.atan2(v.co.y, v.co.x) / (2 * math.pi))
                           + 0.5, (v.co.z - zmin) / max(zmax - zmin, 1e-6))


_lathe_uv = _cyl_uv  # same mapping; named alias for the lathe path


def displace_verts(obj, pred, fn):
    """Move verts matching pred(world==local co) by fn(co) -> new co."""
    for v in obj.data.vertices:
        if pred(v.co):
            v.co = fn(v.co)


def shade_smooth(obj, angle=40):
    for p in obj.data.polygons:
        p.use_smooth = True
    # 4.1+ replaced mesh auto-smooth with the operator below
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.shade_auto_smooth(angle=angle * DEG)
    except (AttributeError, TypeError):
        pass  # fall back to fully smooth; low-poly creases stay subtle
    obj.select_set(False)


def lathe(name, mat, profile, segments=16, start_angle=0.0,
          sweep=2 * math.pi, caps=(), force_outward=False):
    """Revolve a [(radius, z), ...] profile around the Z axis.

    start_angle positions where the profile begins (radians); a sweep
    below 2*pi leaves an opening — used for the hair curtains so the
    face shows through. caps: subset of {"top", "bottom"}.
    """
    bm = bmesh.new()
    a0 = start_angle
    verts = [bm.verts.new((r * math.cos(a0), r * math.sin(a0), z))
             for (r, z) in profile]
    bm.verts.index_update()
    # spin sweeps EDGES into the revolved faces — loose verts alone
    # produce no surface
    edges = [bm.edges.new((verts[i], verts[i + 1]))
             for i in range(len(verts) - 1)]
    bm.edges.index_update()
    bmesh.ops.spin(bm, geom=verts + edges, cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=sweep, steps=segments, use_duplicate=False,
                   use_merge=(sweep >= 2 * math.pi - 1e-6))
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    if caps:
        ring_z = {"bottom": profile[0][1], "top": profile[-1][1]}
        for which in caps:
            z = ring_z[which]
            ring = [v for v in bm.verts
                    if abs(v.co.z - z) < 1e-4 and v.co.length > 1e-4]
            ring.sort(key=lambda v: math.atan2(v.co.y, v.co.x))
            center = bm.verts.new((0.0, 0.0, z))
            n = len(ring)
            for i in range(n):
                a, b = ring[i], ring[(i + 1) % n]
                try:
                    # bottom faces point -Z, top faces point +Z
                    bm.faces.new((center, a, b) if which == "bottom"
                                 else (center, b, a))
                except ValueError:
                    pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if force_outward:
        _force_outward_z(bm)
    _lathe_uv(bm, profile[0][1], profile[-1][1])
    return _obj_from_bmesh(bm, name, mat)


def sphere(name, mat, loc, radius, scale=(1.0, 1.0, 1.0), u=16, v=12):
    bm = bmesh.new()
    m = Matrix.Translation(Vector(loc)) @ Matrix.Diagonal(
        Vector((*scale, 1.0)))
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v,
                              radius=radius, matrix=m, calc_uvs=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    zs = [v.co.z for v in bm.verts]
    _cyl_uv(bm, min(zs), max(zs))  # calc_uvs is unreliable in 5.x
    return _obj_from_bmesh(bm, name, mat)


def tube(name, mat, start, end, r_start, r_end, segments=8):
    """Tapered cylinder from start to end (r_start at the start end)."""
    d = Vector(end) - Vector(start)
    mid = (Vector(start) + Vector(end)) / 2
    m = Matrix.Translation(mid) @ \
        d.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                          segments=segments, radius1=r_start,
                          radius2=r_end, depth=d.length, matrix=m,
                          calc_uvs=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    zs = [v.co.z for v in bm.verts]
    _cyl_uv(bm, min(zs), max(zs))
    return _obj_from_bmesh(bm, name, mat)


# ------------------------------------------------------------ armature

def build_armature(name, bones):
    """bones: list of (bone_name, parent_name|None, head, tail, deform).

    Returns the armature object; callers then parent+skin meshes and
    add clips. Runs edit mode ops — works headless.
    """
    arm_data = bpy.data.armatures.new(name)
    arm_obj = bpy.data.objects.new(name, arm_data)
    link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = arm_data.edit_bones
    created = {}
    for bname, _parent, head, tail, deform in bones:
        eb = ebs.new(bname)
        eb.head, eb.tail, eb.roll = head, tail, 0.0
        eb.use_deform = deform
        created[bname] = eb
    for bname, parent, *_ in bones:
        if parent:
            created[bname].parent = created[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def parent_to(obj, arm_obj):
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm_obj
    obj.parent = arm_obj


def add_group_rule(obj, bname, pred):
    """Add a vertex group for `bname` with verts matching pred (weight 1).

    First-match-wins style is the caller's job: pass disjoint
    predicates or check obj.vertex_groups before adding.
    """
    vg = obj.vertex_groups.get(bname) or \
        obj.vertex_groups.new(name=bname)
    idxs = [v.index for v in obj.data.vertices if pred(v.co)]
    if idxs:
        vg.add(idxs, 1.0, "REPLACE")


def parent_and_skin(obj, arm_obj, rules):
    """rules: list of (bone_name, predicate(local_co) -> bool).

    First matching rule wins with weight 1.0 — low-poly nearest-rule
    skinning; the predicates are explicit per mesh.
    """
    parent_to(obj, arm_obj)
    for bname, pred in rules:
        add_group_rule(obj, bname, pred)


# ----------------------------------------------------------- animation

def _lerp(a, b, t):
    return a + (b - a) * t


def pose_from_keys(keys):
    """Build pose_at(frame) from [(frame, {bone: {'loc','rot'}}), ...].

    Linear interpolation between keyframes; before the first key and
    after the last the nearest key's pose holds (loops are written
    with first == last explicitly).
    rot is degrees (rx, ry, rz), loc is meters; None omits the channel.
    """
    frames = [k[0] for k in keys]
    poses = [k[1] for k in keys]

    def pose_at(f):
        if f <= frames[0]:
            return poses[0]
        if f >= frames[-1]:
            return poses[-1]
        for i in range(len(frames) - 1):
            if frames[i] <= f <= frames[i + 1]:
                t = (f - frames[i]) / (frames[i + 1] - frames[i])
                a, b = poses[i], poses[i + 1]
                out = {}
                for bone in set(a) | set(b):
                    entry = {}
                    for chan in ("loc", "rot"):
                        va = a.get(bone, {}).get(chan)
                        vb = b.get(bone, {}).get(chan)
                        if va is not None and vb is not None:
                            entry[chan] = tuple(
                                _lerp(va[j], vb[j], t) for j in range(3))
                        else:
                            entry[chan] = va if va is not None else vb
                    out[bone] = entry
                return out
        return poses[-1]

    return pose_at


def _action_fcurves(act):
    """Yield all fcurves of an action — slotted actions (4.4+) first,
    legacy flat actions as fallback."""
    if hasattr(act, "layers"):
        for layer in act.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    yield from bag.fcurves
    elif hasattr(act, "fcurves"):
        yield from act.fcurves


def add_clip(arm_obj, name, frame_count, pose_at, linear=True):
    """Sample pose_at over 1..frame_count as keys on the armature.

    Creates a fake-user action named `name` (becomes the Unity clip
    via FBX takes). Pose bones use XYZ euler; untouched bones rest.
    """
    if arm_obj.animation_data is None:
        arm_obj.animation_data_create()
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm_obj.animation_data.action = act
    pbones = arm_obj.pose.bones
    for pb in pbones:
        pb.rotation_mode = "XYZ"
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
    for f in range(1, frame_count + 1):
        for bname, entry in pose_at(f).items():
            pb = pbones.get(bname)
            if pb is None:
                continue
            if entry.get("loc") is not None:
                pb.location = entry["loc"]
                pb.keyframe_insert("location", frame=f)
            if entry.get("rot") is not None:
                pb.rotation_euler = tuple(r * DEG for r in entry["rot"])
                pb.keyframe_insert("rotation_euler", frame=f)
    if linear:
        for fc in _action_fcurves(act):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    arm_obj.animation_data.action = None
    return act


# --------------------------------------------------------------- export

def export_fbx(path):
    kw = dict(
        filepath=path,
        object_types={"ARMATURE", "MESH"},
        use_selection=False,
        bake_anim=True,
        bake_anim_use_all_actions=True,
        bake_anim_use_nla_strips=False,
        bake_anim_simplify_factor=0.0,
        add_leaf_bones=False,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_NONE",
        path_mode="COPY",
        embed_textures=True,
        mesh_smooth_type="OFF",
    )
    try:
        bpy.ops.export_scene.fbx(**kw)
    except TypeError:
        # drop params that may not exist in this Blender version
        for k in ("embed_textures", "mesh_smooth_type",
                  "bake_anim_use_nla_strips",
                  "bake_anim_simplify_factor"):
            kw.pop(k, None)
        kw["path_mode"] = "AUTO"
        bpy.ops.export_scene.fbx(**kw)


def report(label):
    """Print tri/vert/material totals for the log."""
    tris = verts = 0
    mats = set()
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            verts += len(obj.data.vertices)
            tris += sum(len(p.vertices) - 2 for p in obj.data.polygons)
            mats.update(m.name if m else "-" for m in obj.data.materials)
    arms = [o.name for o in bpy.data.objects if o.type == "ARMATURE"]
    clips = [a.name for a in bpy.data.actions]
    print(f"REPORT {label}: tris={tris} verts={verts} "
          f"materials={sorted(mats)} armatures={arms} clips={clips}")
