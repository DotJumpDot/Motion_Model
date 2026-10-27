# Motion_Model — low-poly Thai ghost assets for Unity

Animated, low-poly Thai ghost 3D characters for a horror game in
Unity, built entirely on free tooling because buying animated horror
assets is the expensive path we're avoiding.

## Status

**v0.1 asset package built (2026-10-27).** Both ghosts are generated
by headless-Blender scripts and committed as FBX with rigs and
hand-keyed clips. Remaining gate: the friend's Unity import
(`Docs/IMPORT_CHECKLIST.md`), then tag `v0.1`.

| Asset | Tris | Bones | Clips |
|---|---|---|---|
| Ghost_Woman.fbx | 1312 | 9 | Idle, Walk, Attack |
| Krasue.fbx | 2828 | 6 | Float, Lunge, Scream |

Previews: `assets/preview/*.png`.

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
