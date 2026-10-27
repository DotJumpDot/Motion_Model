# How to run

The "app" is the build: scripts that run headless Blender and emit
FBX. Windows-first (Git Bash + PowerShell).

## Prerequisites

- Blender 4.x/5.x on PATH or at its default install location —
  installed via `winget install --id=BlenderFoundation.Blender -e`
  (pin the exact version in `PLAN_NOTES.md`).
- No other dependencies.

## Setup

```bash
# nothing to install beyond Blender itself
```

## Build the assets

```bash
# from the repo root (adjust the blender path if not on PATH)
blender --background --python src/blender/build_ghost.py
blender --background --python src/blender/build_krasue.py

# verify (re-imports both FBX, prints tri/bone/clip/bbox numbers)
blender --background --python src/blender/verify_fbx.py
```

Each build script writes its FBX to `assets/fbx/`. Expected: no
errors on stderr, and `verify_fbx.py` prints the budget numbers from
`Docs/ARCHITECTURE.md`.

## Verify

- Build gate: both build scripts exit clean; `verify_fbx.py` reports
  tris ≤ 5000 per character, the expected bone and clip counts, and
  sensible bounding boxes (~1.75 m Ghost Woman, ~1.9 m Krasue incl.
  trailing organs).
- Unity gate (friend's machine): `Docs/IMPORT_CHECKLIST.md` — model
  upright at human scale, materials auto-created, all clips present
  and loopable.
