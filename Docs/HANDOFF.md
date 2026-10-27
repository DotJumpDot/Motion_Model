# Handoff

## Where we left off

2026-10-27 — **v0.1 asset package complete.** Both ghosts are built
by scripts, verified by round-trip, and committed:

- `assets/fbx/Ghost_Woman.fbx` — 1312 tris, 9 bones, clips
  Idle/Walk/Attack (Mae Nak style, hair-covered face, red eyes)
- `assets/fbx/Krasue.fbx` — 2828 tris, 6 bones, clips
  Float/Lunge/Scream (floating head + organ trail)
- Build system: `src/blender/` (headless Blender 5.2.3 LTS, see
  `Docs/HOW_TO_RUN.md`); previews in `assets/preview/`
- Unity glue: `src/unity/GhostAI.cs` (wander/chase/attack) +
  `Docs/IMPORT_CHECKLIST.md`

## Next step

**Friend runs `Docs/IMPORT_CHECKLIST.md` in Unity** — that is the one
remaining gate for tag `v0.1` (Generic rig, 3 clips per file, Loop
Time on Idle/Walk/Float, GhostAI on the prefab). Then iterate on the
friend's feedback: shape tweaks are one-line profile changes in the
build scripts.

## Gotchas

- Blender 5.2 slotted actions: `action.fcurves` is gone — use the
  `_action_fcurves()` helper in `blender_lib.py`.
- `bmesh.ops.spin` needs profile **edges** in `geom`, not just verts
  — loose verts sweep into nothing (this bit us once).
- FBX take names carry an `Armature|Armature|` prefix on import;
  rename clips in Unity (checklist step 4).
- Don't set the rig to Humanoid — there are no leg bones on the
  Ghost Woman; Generic is correct.
- Git Bash flattens inline heredoc commit messages — write the
  message to a file and `git commit -F <file>`.
- History note: the original `git init` + push (2026-10-26/27) never
  landed; the repo was re-initialized 2026-10-27 and pushed from
  commit 587139f onward.
