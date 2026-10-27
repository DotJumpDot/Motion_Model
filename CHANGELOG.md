# Changelog

One line per meaningful change, newest first. Format:
`YYYY-MM-DD — what`. A bigger pass may take a short indented bullet
list under its date line. Entries mirror the commit log; commits
themselves follow the style in `AGENTS.md`.

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
