# Architecture

This repo is an **asset pipeline** driven by scripts. As of v0.4 it
has two stages:

1. **AI generation** (`src/hunyuan3d/`, runs once per revision): the
   Ghost Woman's shape comes from Hunyuan3D-2mini (local, RTX 5060)
   given the friend's reference image; texture is a Blender
   projection bake of that image onto the mesh.
2. **Rig/animation/export** (`src/blender/` + `tools/hunyuan3d/
   rig_ghost.py`): decimate to 8k tris, 15-bone rig, smooth 2-bone
   auto-skinning, hand-keyed clips, FBX with embedded texture.

Krasue remains fully script-built (v0.2 pipeline: lathe/sphere
primitives + procedural atlases). The heavy ML toolchain (venv,
Hunyuan3D repo, model weights, CUDA 12.8) lives in `tools/` and is
gitignored — the versioned scripts document and reproduce it.

## Pipeline (data flow)

```
src/blender/build_ghost.py    src/blender/build_krasue.py
        |                              |
        v                              v
  headless blender --background --python <script>
        |                              |
        v                              v
  assets/fbx/Ghost_Woman.fbx     assets/fbx/Krasue.fbx
  (mesh + 9-bone rig + Idle/Walk/Attack)  (mesh + 6-bone rig + Float/Lunge/Scream)
        |                              |
        v                              v
       src/blender/verify_fbx.py  (re-imports both FBX,
        prints tri/bone/clip/bbox numbers = the release gate)
        |
        v
  Unity (friend's machine, IMPORT_CHECKLIST.md):
  Rig = Generic -> Animator -> GhostAI.cs state machine
```

No Mixamo, no Cascadeur, no mocap (dropped at v2 scope, see
PLAN_NOTES). The rigs are small (11 and 7 bones) and the clips are
hand-keyed in the scripts — stiffness/twitch reads as horror.

## Design decisions baked into the models

- **Hair covers the face** (Ghost Woman): the iconic Thai-ghost look
  and zero face modeling. Red eye spheres peek from the shadow.
- **Skirt hides the legs** (Ghost Woman): no leg bones, walk is a
  hip-driven shuffle. The dress is a lathe (spun profile), ~16
  segments.
- **Krasue organs are curve tubes**: a few bezier curves with bevel
  depth converted to mesh, skinned to 3 hanging bones for sway.
- **Flat-color materials, no texture atlas**: 4–5 materials per
  character (skin, hair, dress/organs, eyes). Unity auto-creates them
  on FBX import — no texture pipeline to maintain. Draw calls = a
  handful, irrelevant at indie scale.
- **Origin at ground center, in-place animations**: Unity's AI script
  moves the transform; clips contain no root translation except a
  small attack lunge (±0.15 m).

## Performance budgets (the contract with the game)

- Ghost Woman ≤ 8,000 tris (built v0.4: 7999), 15 bones (with real
  legs). Krasue ≤ 5,000 tris (built v0.2: 4028), 6 bones.
- Ghost: 1 material, 1024 projection-baked texture, embedded in FBX.
  Krasue: 6 materials, 3 atlases, embedded.
- Clips sampled at 30 fps; loopable: Idle/Walk (Ghost), Float (Krasue).

## Repo layout

- `src/blender/` — build + verify scripts (the source of truth)
- `src/unity/GhostAI.cs` — drop-in indie AI: wander/chase/attack
- `assets/fbx/` — generated FBX exports (versioned)
- `Docs/IMPORT_CHECKLIST.md` — Unity import steps (release-time gate)

## Decisions

- **2026-10-27 — v0.2 scary pass, textures replace flat colors**:
  friend's reference (grubby Sadako-style ghost) drove the redesign —
  face-covering hair with a narrow slit + one pale eye, torn hem,
  bare feet, fingers; Krasue rebuilt as an exposed severed head with
  staring eyes + teeth. Atlas textures generated procedurally
  (numpy fBm noise) and embedded via FBX `embed_textures`; UVs are
  cylindrical/positional (calc_uvs proved unreliable in Blender 5.x).
- **2026-10-27 — v2 scope: script-driven, no external rig/anim
  services**: user asked for indie scale without mocap; scripts make
  the models reproducible and reviewable as text.
- **2026-10-27 — Generic rig, not Humanoid**: the Ghost Woman has no
  legs, so Unity's Humanoid avatar mapping can't complete; Generic
  needs no mapping and our clips are native to our own bone names
  anyway.
- **2026-10-27 — flat materials over vertex colors/atlas**: Unity's
  standard shaders ignore vertex colors by default; per-material flat
  colors import with zero extra shader work.
- **2026-10-27 — commit FBX without Git LFS, revisited at v0.2**:
  v0.1 assets were tens of KB; v0.2's embedded textures grew them to
  1.4–1.9 MB. Still acceptable for a 2-asset repo on plain git
  (history cost grows only on regeneration). Flip to LFS if assets
  multiply or any single file approaches ~10 MB.
- **2026-10-27 — FBX for exports** (not Unity's direct `.blend`
  import): stable across Unity versions and needed for clean clip
  export.
