# Handoff

## Where we left off

2026-10-28 — **v0.4: the Ghost Woman is now AI-generated.** After
"model quality not good" feedback, Option A went in end-to-end:

- Shape: Hunyuan3D-2mini-turbo (local RTX 5060, 24 s) from the
  friend's reference image → `tools/hunyuan3d/out/ghost_ai.glb`
- Texture: Blender projection bake of the reference onto the mesh
  (Hunyuan's own texgen blocked by CUDA-admin; documented in
  RESEARCH_TOOLS) → `assets/textures/gw_ai_bake.png`
- Rig: NEW 15-bone humanoid (real legs!), smooth 2-bone auto-skin,
  real walk gait; clips Idle/Walk/Attack hand-keyed as before
- `assets/fbx/Ghost_Woman.fbx`: 7999 tris, textured, embedded,
  faces -Y (= Unity +Z). Krasue untouched (v0.2, accepted).
- Pipeline scripts: `src/hunyuan3d/*.py` (versioned); ML toolchain
  in `tools/` (gitignored: venv, Hunyuan3D-2 repo, HF weights ~8 GB,
  CUDA 12.8 attempt)

## Next step

Friend imports `Docs/IMPORT_CHECKLIST.md` in Unity (Generic rig!).
Optional upgrade: run the CUDA 12.8 installer once as admin, compile
Hunyuan's texgen extensions → replace the projection bake with real
multiview AI texturing. Iterate palette/brightness via the bake
bright-contrast params in `rig_ghost.py`.

## Gotchas

- Blender 5.2: `Action.fcurves` is gone (slotted actions) — use
  `_action_fcurves()` in `blender_lib.py`.
- `bmesh.ops.spin` needs profile **edges** in `geom`, not just verts.
- `calc_uvs` on `create_uvsphere`/`create_cone` is unreliable in
  5.2 — `_cyl_uv()` assigns UVs by position instead.
- Textures are embedded in the FBX (`embed_textures=True,
  path_mode="COPY"`); the PNGs in `assets/textures/` are reference
  copies.
- FBX take names carry an `Armature|Armature|` prefix on import;
  rename clips in Unity (checklist step 4).
- Don't set the rig to Humanoid — no leg bones on the Ghost Woman;
  Generic is correct.
- Git Bash flattens inline heredoc commit messages — write the
  message to a file and `git commit -F <file>`.
- History note: the original `git init` + push (2026-10-26/27) never
  landed; the repo was re-initialized 2026-10-27 and pushed from
  commit 587139f onward. Tags: `v0.1` = flat-color first pass,
  `v0.2` = textured scary pass.
