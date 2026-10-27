# Plan notes

Phase plan + version pins + deferred ideas. Update as phases complete;
completed phases get their CHANGELOG line on the day they land.

## Current phase

**Phase 1 — pick the ghost + reference board.** Friend signs off on
one ghost for v0.1 (recommendation: Mae Nak style full-body) and the
follow-up signature asset (recommendation: Krasue).

## The plan (v1, written 2026-10-27)

Each phase has a "done when" gate. Nothing starts before the gate
before it passes.

| # | Phase | Deliverable | Done when |
|---|---|---|---|
| 1 | Ghost pick + reference | One-page concept: chosen ghost, 10–20 reference images, silhouette, palette, 3 signature moves | Friend signs off |
| 2 | Toolchain install | Blender + Unity + free accounts (Adobe/Mixamo, Cascadeur, optional Tripo); HOW_TO_RUN filled with pinned versions | A cube FBX exported from Blender appears correct in a fresh Unity scene |
| 3 | v0.1 full-body ghost | Blender model ≤15k tris, single 512px texture atlas, T-pose | Renders in Blender lookdev without broken shading |
| 4 | Rig + stock anims | Mixamo-rigged FBX + 3–5 clips (idle sway, walk, crawl/lunge) | Clips play in Unity on a Humanoid avatar |
| 5 | v0.2 Krasue | Head + trailing organs ≤5k tris, ~10-bone rig, float/turn/lunge clips | Plays in Unity next to v0.1 at 60 fps |
| 6 | Custom horror anims | 2+ custom clips via Cascadeur (optional FreeMoCap webcam session for blocking) | Clips in Unity; verdict "actually scary" |
| 7 | Package | FBX + textures + Unity prefab + `Docs/IMPORT_CHECKLIST.md`; tag `v0.1` | A fresh Unity project imports the package clean |

## Ghost shortlist — why the cheap options are cheap

| Ghost | Look | Why it's cheap to build |
|---|---|---|
| Mae Nak style | Full body, long sinh skirt, long black hair | The skirt hides the legs — the walk cycle is nearly free, and Mixamo auto-rigs the rest. Fastest path to a working pipeline. |
| Krasue | Floating head + trailing glowing entrails | No limbs, no walk cycle at all; ~10 bones; ≤5k tris. The signature Thai horror asset and the cheapest performance-wise. |
| Pret | Very tall, gaunt | Simple stretched body — but extreme proportions can break Mixamo auto-rigging. Deferred. |

**Order recommendation:** v0.1 = Mae Nak style (proves the whole
pipeline fastest via Mixamo), v0.2 = Krasue (the signature asset).

## Budget

0 THB core path — every tool in the core stack is free. Paid only if a
wall is hit: Tripo/Meshy credits for AI base meshes, Cascadeur Pro if
free-tier limits bite. Any spend needs a CHANGELOG line and a reason.

## Risks

| Risk | Mitigation |
|---|---|
| AI-generated base mesh too dense for low-poly | Decimate/retopo in Blender, or model from scratch — AI path is optional |
| Mixamo rig fails on extreme proportions | Keep v0.1 near-human; Pret deferred for this reason |
| Webcam-only mocap too jittery | Use FreeMoCap for blocking only; clean keys by hand or in Cascadeur |
| Binary assets bloat the repo | Enable Git LFS (`.blend`, `.fbx`, `.png`) **before** the first Phase 3 asset commit |
| Free-tier terms shift under us | Re-check ToS at release time (see RESEARCH_TOOLS licensing notes) |

## Done

- 2026-10-27 — Phase 0: repo linked to GitHub, research + plan written
  (this doc set). No assets, no installs yet.

## Version pins

- To pin at Phase 2 install time (exact versions land here + in
  HOW_TO_RUN): Blender LTS, Unity LTS, Cascadeur, FreeMoCap, optional
  Tripo/Meshy tier.

## Deferred / ideas

- Git LFS setup — before the first binary asset lands (Phase 3).
- Unity demo scene in-repo — only after v0.1 imports clean (Phase 7
  optional).
- Pret (tall hungry ghost) as a third character.
- Rigify manual rig instead of Mixamo — only if Mixamo proportions
  fail.
- Rokoko Video / other AI video-mocap services — revisit if FreeMoCap
  quality is insufficient.
