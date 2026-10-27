# Changelog

One line per meaningful change, newest first. Format:
`YYYY-MM-DD — what`. A bigger pass may take a short indented bullet
list under its date line. Entries mirror the commit log; commits
themselves follow the style in `AGENTS.md`.

- 2026-10-28 — **v0.6: real Hunyuan AI texturing unlocked** (user ran
  the CUDA 12.8.1 + VS Build Tools installers as admin): compiled
  custom_rasterizer + mesh_processor with nvcc 12.8 + MSVC 14.44
  (patched rasterizer.h — torch 2.11's compiled_autograd.h is not
  nvcc-clean; HF-cache symlinks need Developer Mode → predownload
  paint weights as real files, HY3DGEN_MODELS override). Pipeline
  order fixed: decimate first (export_8k.py), paint second
  (gen_texture.py) — painting then decimating scrambles the xatlas
  UVs. rig_ghost.py now prefers ghost_ai_tex_8k.glb (painted face,
  corpse skin on arms/feet, grubby dress, black hair flow; ~24k verts
  from UV splits, 7998 tris) with the v0.5 projection bake kept as
  fallback; gw_ai_paint.png saved to assets/textures. FBX 3.5 MB
  embedded. RESEARCH_TOOLS unblocked note + IMPORT_CHECKLIST v0.6
  numbers.
- 2026-10-28 — **v0.5: Ghost Woman secondary motion + real texture**
  (user: "look cool, add hair/cloth sway + texture"): 11 new bones
  (HairB_1..3 back-drape whip, HairL/R_1..2 front curtains, Robe_F/B/L/R
  hem flutter — 26 total) keyed with lagged sway into Idle/Walk and
  trailing-whip keys into Attack; per-vertex hair/skin/robe classifier
  (depth-vs-photo + frontmost-cell rules, `classify_probe.py`) drives
  both skinning gates and the texture bake; bake v2 mixes black
  streak-atlas hair (projection UV keeps strands vertical), pale
  corpse skin on face/hands/feet, photo-front/fabric-back robe —
  fixes the gray "clay" look; skinning gates stop arm bones stealing
  skirt verts (cloth no longer dangles off the hands at the lunge);
  optional `src/unity/JiggleBone.cs` spring-damper for Unity-side
  physics flutter; IMPORT_CHECKLIST updated (26 bones, jiggle setup).
  CUDA 12.8.1 + VS Build Tools install started for the Hunyuan texgen
  upgrade (user runs the admin prompts) — targeted as v0.6.
- 2026-10-28 — **v0.4: Ghost Woman rebuilt via local AI** (user
  approved Option A): Hunyuan3D-2mini-turbo shape gen from the
  friend's reference image (24 s on RTX 5060; transformers pinned to
  4.48.3 — 5.x breaks the DINOv2 conditioner), Blender decimate to
  7999 tris, NEW 15-bone rig with real legs + walk gait + smooth
  2-bone auto-skinning (fixes skirt-hem tearing), projection bake of
  the reference onto the mesh (Hunyuan texgen blocked: CUDA 12.8
  side-by-side install needs admin; pip nvcc wheel lacks nvcc.exe on
  Windows) with procedural-fabric back blend, FBX re-exported with
  embedded 1024 texture. Pipeline scripts versioned in
  `src/hunyuan3d/`; toolchain gitignored under `tools/`. Krasue
  unchanged. License flag recorded (Tencent Hunyuan Community).
- 2026-10-27 — v0.3 ghost cohesion pass (friend feedback: parts
  looked disconnected): hair bob-cut ends at shoulders (no chest
  slab) + side panels rotated to overlap the slit edges, dress top
  tapers into a neck ring inside the head sphere (no gap), sleeves
  overlap the dress shoulder, arm segments extended ~2 cm past each
  joint to kill elbow gaps. AI 3D-gen research added to
  RESEARCH_TOOLS (Hunyuan3D-2mini fits this RTX 5060 8GB; Tripo/
  Meshy API-key option; procedural kept as fallback).
- 2026-10-27 — v0.2 docs: CONCEPT rewritten to the v0.2 designs
  (slit hair + single eye + torn hem + feet; exposed severed-head
  Krasue), ARCHITECTURE budgets with built numbers + texture-embed
  and LFS-revisit decisions, IMPORT_CHECKLIST known-good numbers +
  embedded-texture note, HANDOFF updated (new gotchas: calc_uvs,
  embed_textures; v0.1/v0.2 tag history), README status table,
  PLAN_NOTES done line.
- 2026-10-27 — v0.2 assets regenerated: `Ghost_Woman.fbx` (2572
  tris, 9 bones, 6 materials with 3 embedded atlases, bbox
  0.48×0.50×1.70 m) + `Krasue.fbx` (4028 tris, 6 bones, 6 materials
  with 3 embedded atlases, bbox 0.35×0.36×0.94 m); texture PNG
  reference copies in `assets/textures/`; previews now 4 PNGs
  (front + face close-up per character); `verify_fbx.py` re-import
  green (tris/bones/clips/bbox within budget).
- 2026-10-27 — v0.2 scary pass: `blender_lib` gained procedural
  texture atlas generation (numpy fBm + anisotropic strand noise,
  packed+saved PNGs), textured materials, positional cylindrical UVs
  (`_cyl_uv`; `calc_uvs` unreliable in 5.2), `displace_verts`,
  smooth shading, FBX `embed_textures`. Ghost Woman redesigned per
  friend reference: hair slit + ONE pale eye, torn hem, bare
  ankles/feet, drooping fingers, sleeves, darker grubbier palette,
  head-twitch in Idle. Krasue rebuilt as exposed severed head:
  staring sockets with off-center pale irises, two teeth rows,
  wider mouth, bruise-mottled skin, veined wet organs.
- 2026-10-27 — Packaging docs: new `Docs/IMPORT_CHECKLIST.md` (Unity
  import steps, Generic-rig note, animator wiring, GhostAI setup,
  known-good round-trip numbers); HANDOFF rewritten to built state,
  README status table, PLAN_NOTES phase table marked done + 9/6-bone
  counts corrected, ARCHITECTURE budgets updated with built numbers;
  .gitignore + `*.blend1`.
- 2026-10-27 — Generated assets: `assets/fbx/Ghost_Woman.fbx` (1312
  tris, 9 bones, 3 clips, ~424 KB) + `assets/fbx/Krasue.fbx` (2828
  tris, 6 bones, 3 clips, ~352 KB) via headless Blender 5.2.3 LTS;
  Workbench previews in `assets/preview/`; verified by FBX re-import
  (`verify_fbx.py`) — tris/bones/clips/bbox within budget.
- 2026-10-27 — Build system: `src/blender/blender_lib.py` (lathe/
  sphere/tube mesh builders, armature + nearest-rule skinning,
  keyframe clip engine with Blender 5.2 slotted-action compat, FBX
  export) + `build_ghost.py` / `build_krasue.py` (both characters:
  meshes, 9- and 6-bone rigs, Idle/Walk/Attack and Float/Lunge/Scream
  clips) + `verify_fbx.py` round-trip gate + `render_check.py` CPU
  preview renderer; `src/unity/GhostAI.cs` wander/chase/attack
  controller (no NavMesh dependency).
- 2026-10-27 — Plan v2 (indie scope): mocap/Cascadeur/Mixamo dropped
  from core pipeline; everything rebuilt as headless Blender scripts
  (`Docs/PLAN_NOTES.md` phases table + status, `Docs/ARCHITECTURE.md`
  rewritten script-driven incl. Generic-rig decision, `Docs/
  RESEARCH_TOOLS.md` marked used vs optional, `Docs/HOW_TO_RUN.md`
  now real build commands, new `Docs/CONCEPT.md` for both ghosts,
  docs index updated); Blender 5.2.3 LTS installed via winget.
- 2026-10-27 — Kickoff research + plan: `Docs/RESEARCH_TOOLS.md`
  (free toolchain survey — Blender, Mixamo, Cascadeur, FreeMoCap,
  Tripo/Meshy, licensing), `Docs/PLAN_NOTES.md` (7-phase plan, ghost
  shortlist, budget, risks), `Docs/ARCHITECTURE.md` (pipeline, perf
  budgets, repo layout, decisions), `Docs/HOW_TO_RUN.md` stubbed for
  Phase 2, `Docs/HANDOFF.md` started, Docs index updated.
- 2026-10-27 — Project identity: AGENTS.md "What this repo is" filled
  in (Thai ghost assets for Unity on a free Blender/Mixamo/Cascadeur/
  FreeMoCap pipeline); README rewritten from template to the real
  project (title, status, pipeline summary, docs index).
- 2026-10-26 — Base project scaffold: README, AGENTS.md (house rules +
  commit & push style contract), CHANGELOG, `Docs/` starter set (index,
  architecture, how-to-run, plan notes, handoff), .gitignore; initial
  commit made in the house style via `git commit -F`.
