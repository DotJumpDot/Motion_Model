# Unity import checklist

Steps for the friend's Unity project (2022 LTS or newer). Tested
numbers come from the Blender round-trip (see CHANGELOG); this page
is the release-time gate — tick it off on the Unity machine.

## 1. Import

1. Copy `assets/fbx/Ghost_Woman.fbx` and `assets/fbx/Krasue.fbx`
   into `Assets/Models/`.
2. Select each FBX → **Model** tab: expect Scale Factor 1 and
   Read/Write off. The model should stand upright, ~1.75 m tall
   (Ghost) / head at ~1.8 m with organs trailing to ~0.9 m (Krasue).
3. **Rig** tab: Animation Type **Generic**, Avatar = auto-generated.
   (NOT Humanoid — the Ghost Woman has no leg bones, Humanoid
   mapping would fail.)
4. **Animation** tab: you should see 3 clips per file:
   - Ghost Woman: `Idle` (96 f), `Walk` (48 f), `Attack` (36 f)
   - Krasue: `Float` (96 f), `Lunge` (30 f), `Scream` (36 f)
   Take names may carry an `Armature|Armature|` prefix — rename the
   clips to the short names. Tick **Loop Time** on `Idle`, `Walk`,
   `Float`. Leave `Attack`/`Lunge`/`Scream` one-shot.
5. Materials auto-generate from the FBX (4–5 flat colors per
   character). Optional polish: set the eye material's emission to
   the same red for a glow.

## 2. Animator controller

Per ghost: one controller with states Idle/Float, Walk, Attack/Lunge,
Scream (wire the clips from that FBX).

- Parameters: `bool Walking`, `trigger Attack`.
- Transitions: `Idle ⇄ Walk` on `Walking`; `Idle → Attack` and
  `Walk → Attack` on `Attack`; `Attack → Idle` with Exit Time ~100%
  (clips are non-looping).

## 3. Drop the AI on it

1. Add the FBX prefab to a scene, add a **CapsuleCollider** (ground
   needs a collider) and `src/unity/GhostAI.cs`.
2. Player GameObject tagged `Player`. Tune `detectRange`,
   `chaseSpeed`, `attackRange` to taste — defaults are slow-creep.
3. Press Play: ghost idles/wanders, chases inside 10 m, attacks
   inside 1.6 m with cooldown.

## Known-good numbers (v0.4 AI ghost, 2026-10-28)

- Ghost_Woman.fbx: **7999 tris, 15 bones** (with legs — Generic rig
  required, do NOT use Humanoid: bone names are custom), 1 material
  with a 1024 texture **embedded in the FBX**, bbox ~0.64 × 0.42 ×
  1.96 m, character faces **-Y in Blender = +Z in Unity** with
  default export settings. Clips: Idle(96f)/Walk(48f)/Attack(36f);
  tick Loop Time on Idle+Walk.
- Krasue.fbx: 4028 tris, 6 bones, 6 materials (3 atlases, embedded),
  bbox 0.35 × 0.36 × 0.94 m (head occupies z 0.9–1.85). Clips:
  Float(96f)/Lunge(30f)/Scream(36f); Loop on Float.
- Ghost walk has real leg motion now (thigh/shin/foot bones); the
  AI mesh's dress hem is soft-skinned so it sways with the stride.
- If any material shows pink: Standard/URP Lit + reassign the
  embedded texture.
