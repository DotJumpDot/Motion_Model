# Architecture

This repo is an **asset pipeline** driven by scripts. It produces
low-poly rigged+animated Thai ghost characters (FBX) for Unity using
one tool: Blender, run headless. The scripts are the source of truth;
the FBX files are build output (committed for the friend's
convenience).

## Pipeline (data flow)

```
src/blender/build_ghost.py    src/blender/build_krasue.py
        |                              |
        v                              v
  headless blender --background --python <script>
        |                              |
        v                              v
  assets/fbx/Ghost_Woman.fbx     assets/fbx/Krasue.fbx
  (mesh + 11-bone rig + Idle/Walk/Attack)  (mesh + 7-bone rig + Float/Lunge/Scream)
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

- Ghost Woman ≤ 5,000 tris, 11 bones. Krasue ≤ 5,000 tris, 7 bones.
- ≤ 5 materials per character. No textures.
- Clips sampled at 30 fps; loopable: Idle/Walk (Ghost), Float (Krasue).

## Repo layout

- `src/blender/` — build + verify scripts (the source of truth)
- `src/unity/GhostAI.cs` — drop-in indie AI: wander/chase/attack
- `assets/fbx/` — generated FBX exports (versioned)
- `Docs/IMPORT_CHECKLIST.md` — Unity import steps (release-time gate)

## Decisions

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
- **2026-10-27 — commit FBX without Git LFS**: at ≤5k tris the FBX
  files are tens of KB; LFS adds setup friction for the friend.
  Revisit at >1 MB per asset.
- **2026-10-27 — FBX for exports** (not Unity's direct `.blend`
  import): stable across Unity versions and needed for clean clip
  export.
