# Architecture

This repo is not software — it is an **asset pipeline**. It produces
low-poly rigged+animated Thai ghost characters (FBX + texture atlas)
for Unity, on a free toolchain. Hub tool: Blender. Rig + stock
animations: Mixamo. Custom motion: Cascadeur / FreeMoCap. Target:
Unity Humanoid / Mecanim.

## Pipeline (data flow)

```
reference board (film stills, temple murals, AI concept sketches)
   |
   v
Blender: blockout -> detail -> UV -> single 512px atlas texture
   |  (v0.1 full-body ghost; v0.2 Krasue = head + organs)
   v
Mixamo: upload T-pose FBX -> auto-rig -> download rigged FBX
   |
   v
animation sources (pick per clip):
   Mixamo library  |  Cascadeur (custom, physics-aided)
                   |  FreeMoCap webcam session -> Blender add-on
   |
   v
Blender: import anims onto rig -> bake (visual keying) ->
   export FBX (baked animation, applied transforms)
   |
   v
Unity: import -> Rig = Humanoid -> Mecanim retarget ->
   Animator controller -> ghost polish (alpha-flicker shader,
   point light, audio, jump-scare trigger)
   |
   v
release: FBX + PNG atlas + prefab + Docs/IMPORT_CHECKLIST.md
```

The Krasue rig (v0.2) skips Mixamo: a light manual rig in Blender
(neck, jaw, spine/organ chain, ~10 bones) is smaller and faster than an
auto-generated humanoid skeleton.

## Performance budgets (the contract with the game)

- Character mesh **≤ 15,000 tris** (mobile-safe target ≤ 10k; Krasue
  ≤ 5k).
- **≤ 75 bones** per character (Krasue ~10). Mixamo's default skeleton
  fits; disable finger detail when uploading.
- **1 material, 1 draw call** per character: a single 512×512 atlas
  (256 if mobile matters).
- Animation clips sampled at **30 fps**, loopable idle/float.

## Repo layout (from Phase 3)

- `assets/blend/` — source `.blend` per character (the source of truth)
- `assets/textures/` — atlas PNG + working files
- `assets/fbx/` — Unity-bound exports only (generated, but versioned
  for the friend's convenience)
- `Docs/IMPORT_CHECKLIST.md` — release-time Unity import steps

Git LFS tracks `*.blend`, `*.fbx`, `*.png` before the first binary
lands.

## Decisions

- **2026-10-27 — Mixamo over manual Rigify for v0.1**: free,
  automatic, Unity-proven; a manual rig buys nothing until Mixamo
  demonstrably fails.
- **2026-10-27 — Mae Nak first, Krasue second**: full-body proves the
  whole pipeline fastest; Krasue is the perf-cheapest signature asset.
- **2026-10-27 — single 512px atlas**: one draw call, small memory,
  plenty for horror silhouettes read mostly in low light.
- **2026-10-27 — FBX for production exports** (not Unity's direct
  `.blend` import): stable across Unity versions and required for
  clean Humanoid retargeting + baked clips.
