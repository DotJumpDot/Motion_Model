# Research — the free toolchain

Survey date: 2026-10-27. Goal: an animated, low-poly Thai ghost 3D
character for Unity at ~0 budget (buying animated horror assets is the
problem we're engineering around).

**Verdict up front:** a fully free, proven pipeline exists —
Blender (model) → Mixamo (rig + stock animations) → Cascadeur /
FreeMoCap (custom motion) → FBX → Unity. Paid tools are optional
accelerators, not requirements. No free ready-made Thai ghost model
(Krasue / Nang Nak) was found on Sketchfab or itch.io as of the survey
date, so building (or remixing a CC0 base) is the way.

## Core stack — all free

| Tool | Role | Cost | Links | Notes |
|---|---|---|---|---|
| Blender | Model, UV, texture, rigging, animation, FBX export | Free | [blender.org](https://www.blender.org) | The hub — everything passes through it. |
| Mixamo | Auto-rigging + stock animation library | Free w/ Adobe account | [mixamo.com](https://www.mixamo.com) | Still free in 2026; Adobe states the auto-rigger and animation library stay free. Exports "FBX Binary for Unity". Auto-rig needs a near-human-proportioned mesh in T/A-pose. |
| Cascadeur | AI-assisted keyframe animation, physics, mocap cleanup | Basic plan free | [cascadeur.com](https://cascadeur.com) | Current line 2026.x. Best tool for custom horror moves (twitch, lunge, unnatural poses). Re-check free-tier commercial limits before release. |
| FreeMoCap | Markerless mocap from 1+ webcams → Blender | Free, open source | [repo](https://github.com/freemocap/freemocap) · [Blender add-on](https://github.com/freemocap/freemocap_blender_addon) · [site](https://freemocap.org) | Act the ghost's moves on camera yourself. Webcam-only capture is usable for blocking but jittery for finals — plan to clean keys in Blender/Cascadeur. |

## Optional accelerators — free tiers

| Tool | Role | Links | Notes |
|---|---|---|---|
| Tripo | Image/text → 3D base mesh | [studio.tripo3d.ai](https://studio.tripo3d.ai/workspace/generate) | "Smart Mesh" targets game-ready low-poly output; monthly free credits. AI meshes usually still need decimate/retopo in Blender. |
| Meshy | Image/text → 3D + textures | [meshy.ai](https://www.meshy.ai) | Praised for texture quality. Same retopo caveat. |
| Sketchfab | Reference + CC0 remix bases | [CC0 horror character](https://sketchfab.com/3d-models/cc0-horror-game-character-d14367977cf5461fa1855e3bbfb57d48) · [ghost tag](https://sketchfab.com/tags/ghost) | Nothing Thai-ghost specific free; a CC0 female ghost can be remixed into a Mae Nak silhouette. |
| Unity Personal | Target engine | [unity.com](https://unity.com) | Free below the revenue threshold. |

## How-to pointers — the exact bridge steps

- Blender → Unity export checklist (scale, axes, bones):
  [Cinevva guide](https://app.cinevva.com/guides/blender-to-unity-export-checklist),
  [Blender StackExchange thread](https://blender.stackexchange.com/questions/279419/how-to-get-a-rigged-character-from-blender-fbx-unity)
- Video walkthroughs:
  [Rigged characters to Unity/Unreal](https://www.youtube.com/watch?v=27woi8FsgAU),
  [Blender animation → Unity](https://www.youtube.com/watch?v=uWexElqDcaA),
  [Rigify rig → Unity](https://www.youtube.com/watch?v=vrN9duEoA6g)
- Unity side: import FBX → Rig tab → **Humanoid** so Mecanim
  retargeting works. The classic failure is leaving the rig Generic or
  exporting un-baked animation.

## Licensing notes — read before shipping

- **Mixamo**: auto-rig and animations are free for commercial games,
  no royalties.
- **CC0 assets**: no attribution required (credit is courteous).
- **Folklore**: Krasue, Mae Nak, Pret are folklore — free to use. Do
  not clone one specific film's exact costume/makeup design; keep the
  design generic-folklore to stay clear of a studio's protected
  expression.
- **FreeMoCap**: open source; your captured motion data is yours.
  Check the repo license before redistributing the software itself.
- **Cascadeur / Tripo / Meshy free tiers**: re-check each ToS for
  commercial-use limits at release time — free tiers change.
