# Motion_Model — low-poly Thai ghost assets for Unity

Animated, low-poly Thai ghost 3D characters for a horror game in
Unity, built entirely on free tooling because buying animated horror
assets is the expensive path we're avoiding.

## Status

**v0.2 — scary pass complete (2026-10-27).** Both ghosts rebuilt per
the friend's reference: procedural grunge textures embedded in the
FBX (no external files), hair-covered face with a single pale eye,
torn-hem dress, bare feet, drooping fingers; Krasue as a full severed
head with staring eyes, teeth and organ trail. Remaining gate: the
friend's Unity import (`Docs/IMPORT_CHECKLIST.md`).

| Asset | Tris | Bones | Clips | Textures |
|---|---|---|---|---|
| Ghost_Woman.fbx | 2572 | 9 | Idle, Walk, Attack | 3 atlas PNGs (embedded) |
| Krasue.fbx | 4028 | 6 | Float, Lunge, Scream | 3 atlas PNGs (embedded) |

Previews: `assets/preview/*_front.png` + `*_close.png`.
History: v0.1 (flat-color, no textures) is tagged `v0.1`.

## The pipeline in one line

Reference → Blender (model, ≤15k tris, 512px atlas) → Mixamo (free
auto-rig + stock horror animations) → Cascadeur / FreeMoCap (custom
motion) → FBX → Unity (Humanoid / Mecanim) → packaged release.

## Repo layout

| Path | Purpose |
|---|---|
| `AGENTS.md` | Working rules + the commit & push style contract (read first) |
| `CHANGELOG.md` | Newest-first `YYYY-MM-DD — what` log of the work |
| `Docs/` | Long-form docs; `Docs/README.md` is the index |
| `assets/` | Source `.blend`, textures, FBX exports (arrives Phase 3, Git LFS) |

## Docs index

- [`Docs/README.md`](Docs/README.md) — documentation index
- [`Docs/RESEARCH_TOOLS.md`](Docs/RESEARCH_TOOLS.md) — free toolchain
  survey: roles, costs, links, licensing notes
- [`Docs/PLAN_NOTES.md`](Docs/PLAN_NOTES.md) — 7-phase plan, ghost
  shortlist, budget, risks, deferred ideas
- [`Docs/ARCHITECTURE.md`](Docs/ARCHITECTURE.md) — the asset pipeline,
  performance budgets, repo layout, decisions
- [`Docs/HOW_TO_RUN.md`](Docs/HOW_TO_RUN.md) — toolchain install
  (lands at Phase 2)
- [`Docs/HANDOFF.md`](Docs/HANDOFF.md) — pick-up-where-we-left-off notes
