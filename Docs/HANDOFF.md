# Handoff

## Where we left off

2026-10-27 — **v0.2 asset package complete (scary pass).** After the
friend's feedback ("too plain, want mature scary + textures"), both
ghosts were rebuilt per their reference image:

- `assets/fbx/Ghost_Woman.fbx` — 2572 tris, 9 bones, clips
  Idle/Walk/Attack. Hair-covered face with a narrow slit + ONE pale
  eye, torn-hem grubby dress, bare feet, drooping fingers, head
  twitch in Idle. 3 procedural texture atlases embedded in the FBX.
- `assets/fbx/Krasue.fbx` — 4028 tris, 6 bones, clips
  Float/Lunge/Scream. Full severed-head look: exposed mottled face,
  staring dark sockets with off-center pale irises, two rows of
  teeth, veined organ trail. 3 atlases embedded.
- Build system: `src/blender/` (headless Blender 5.2.3 LTS, see
  `Docs/HOW_TO_RUN.md`); previews in `assets/preview/` (front +
  face close-up per character); texture PNGs in `assets/textures/`.
- Unity glue unchanged: `src/unity/GhostAI.cs` +
  `Docs/IMPORT_CHECKLIST.md` (materials arrive textured).

## Next step

**Friend runs `Docs/IMPORT_CHECKLIST.md` in Unity** — then iterate:
palette/darkness tweaks are one-line texture-param changes in the
build scripts; shape tweaks are profile edits.

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
