# Cinematic Colossal Realism Loop-Assisted Image Comparison

```yaml
loop_assisted_profile_use:
  profile_version: cinematic-colossal-realism-v0.1
  max_rounds_or_budget: "one baseline prompt, one basic TVG profile prompt, one advanced four-layer profile prompt, optional Images2 run"
  rounds_used: 0
  round_records:
    - round: 1
      change_type: prompt
      positive_value_hypothesis: "baseline ordinary expansion exposes what a prose-only prompt leaves underspecified"
      gate_result: freeze-with-review-bound-warning
      residual_failure_modes:
        - "weak human-scale anchoring"
        - "weak physical feedback"
    - round: 2
      change_type: profile
      positive_value_hypothesis: "basic profile adds scale and physical feedback"
      gate_result: freeze-with-review-bound-warning
      residual_failure_modes:
        - "less deterministic field and lint coverage"
    - round: 3
      change_type: profile
      positive_value_hypothesis: "advanced four-layer profile uses runtime support to improve reviewable surfaces"
      gate_result: freeze-with-review-bound-warning
      residual_failure_modes:
        - "generated image may still drift"
  runtime_rescue_cost: unknown
  final_artifact_path: "examples/loop-assisted-image-comparison.md"
  final_claim_ceiling: "Images2 output is loop-assisted production evidence for one run; it does not prove the profile is generally strong."
```

## Comparison Frame

Subject: `black tide dragon bone god`

Comparison target: baseline vs basic profile vs advanced four-layer profile.

Images2 output is loop-assisted production evidence. It does not prove the profile is
generally strong, and it does not prove future image models will preserve the same style.

## Prompt Packet A - Baseline Ordinary Expansion

A huge dragon-bone god rises from a black ocean, dark and cinematic, with mysterious
lighting, dramatic waves, ancient bones, and an epic atmosphere. The image should feel
realistic, detailed, and impressive.

## Prompt Packet B - Basic TVG Profile

A colossal dragon-bone deity appears in a black deep-sea current, partly hidden by
murky water and darkness. A small submersible and diver lights in the foreground provide
human scale, a broken shipwreck and trench wall sit in the midground, and the deity's
rib-like silhouette disappears into the distant water. Silt, loose cables, fish, and
light beams react to the moving current. Low witness viewpoint, restrained upward angle,
wide cinematic frame, deep blue-gray shadows, controlled highlights, realistic water
scatter, weathered bone texture.

## Prompt Packet C - Advanced Four-Layer Profile

Inside a small submersible looking through a scratched forward window, a black tide
pushes silt across the lamp beams as a dragon-bone god emerges only in fragments from
the deep-sea trench. The foreground holds instrument glow, a blurred observer shoulder,
and water marks on glass. The midground shows torn ship cables, broken mast ribs, and
fish suddenly turning away. In the background, a half-lit skull ridge and immense rib
arches cross the trench walls before vanishing beyond the frame. The camera stays low
and close to the witness position with medium telephoto compression, 2.39:1 widescreen
composition, layered dark exposure, submersible lamp scatter through turbid water,
stone-white bone, rusted gold sediment, near-black current shadows, fine film grain,
and imperfect lens-edge haze. Avoid plastic surface, weightless floating, blank clean
background, no environment contact, flat even lighting, poster centered subject,
missing human scale anchor, overly saturated color, and over-sharpened edges.

## Images2 Comparison Claim Ceiling

- This run can support one-run loop-assisted production observations.
- It cannot prove the profile is generally strong.
- It cannot prove future image models will preserve the same style.
- If generated images are stored, binary files should stay local or under ignored artifact paths unless explicitly requested.

## Images2 Run - 2026-07-01

Local ignored artifacts:

- `tests/artifacts/tvg_cinematic_colossal_a_baseline.png`
- `tests/artifacts/tvg_cinematic_colossal_b_basic.png`
- `tests/artifacts/tvg_cinematic_colossal_c_advanced.png`

Artifact storage note: these files match the repository's ignored `tests/artifacts/tvg_*.png`
pattern. They are local comparison evidence, not release-pack fixtures.

Observed one-run comparison:

- A / baseline produced a dramatic full-subject monster image. It carried spectacle,
  but witness position, human-scale anchoring, field pressure, and physical feedback
  were weak.
- B / basic profile improved the scene into a readable underwater scale relation with
  submersible, wreck, trench, and partial colossal form. It still leaned toward
  impressive skeletal ruins more than a witnessed divine presence.
- C / advanced four-layer profile made the witness position much harder to lose:
  window, instruments, observer shoulder, turbid light beams, cables, silt, and
  frame-overflowing subject fragments were all more inspectable.

Review-bound conclusion:

The advanced four-layer profile produced the strongest prompt-to-image control in this
single run. This is loop-assisted production evidence only. It supports further profile
iteration, not a claim that the profile is mature or generally stronger than the
external skill.

## Four-Way Migration Comparison - 2026-07-01

The earlier A/B/C comparison tested baseline, basic profile, and advanced profile
package prompt control. It did not directly compare against the external skill behavior
or TVG pressure settings. This section records the cleaner four-way comparison.

Subject: `黑潮里的龙骨神`

Compared variants:

1. `A Direct`: the terse subject is sent directly to Images2.
2. `B Original SKILL`: the subject is expanded using the external skill's runtime habits.
3. `C TVG P2`: the current TVG profile package uses ordinary pressure 2 behavior.
4. `D TVG P5`: the current TVG profile package uses higher pressure 5 behavior.

Local ignored artifacts:

- `tests/artifacts/tvg_cinematic_fourway_a_direct.png`
- `tests/artifacts/tvg_cinematic_fourway_b_original_skill.png`
- `tests/artifacts/tvg_cinematic_fourway_c_tvg_p2.png`
- `tests/artifacts/tvg_cinematic_fourway_d_tvg_p5.png`
- `tests/artifacts/tvg_cinematic_fourway_contact_sheet.png`

Artifact storage note: these files match the repository's ignored `tests/artifacts/tvg_*.png`
pattern. They are local visual comparison evidence, not release-pack fixtures.

### Four-Way Prompt Packets

`A Direct`:

```text
黑潮里的龙骨神
```

`B Original SKILL`:

```text
【最终提示词】
黑潮里的龙骨神出现在深海峡谷与沉船残骸之间，庞大的龙形骨骸像古老神明一样横跨整片海底空间，头骨只从浑浊黑色水流后方露出一部分，巨大的肋骨和脊椎延伸到画框之外，被海雾、泥沙和黑潮吞没。前景是小型潜水器舷窗、探照灯光锥和一名潜水员的微小轮廓，中景的沉船桅杆、断裂缆绳和海底岩壁被黑潮推动，远景的龙骨神遮蔽峡谷尽头，让水体变暗。黑潮推起泥沙，缆绳被水流拉紧，鱼群突然散开，探照灯照到骨面时在浑浊水中形成真实散射。镜头位于潜水器窗口后方的低处，轻微仰拍，中长焦压缩潜水器、沉船和巨大龙骨之间的距离，2.39:1 宽银幕构图。光线来自潜水器探照灯、远处微弱冷色天光和骨缝中极淡的暗金反光，整体为低饱和深蓝灰、石灰白、铁锈暗金与近黑色阴影。真实电影机拍摄，大格式电影摄影质感，自然高动态范围曝光，暗部保留层次，高光不过度溢出，细腻水体透视，轻微胶片颗粒，镜头边缘有水雾和细小划痕，超清电影画面，神话现实主义，物理可信。

【负面约束】
避免廉价特效感、塑料表面、过度光滑、漂浮无重量感、干净空白背景、主体与环境没有接触、过亮轮廓边缘、不自然比例、过度锐化、均匀平光、海报式摆拍、主体完整居中平铺、没有人类尺度参照、天空或水体过于干净明亮、颜色过度鲜艳、材质过度完美。
```

`C TVG P2`:

```text
黑潮里的龙骨神. A cinematic image prompt packet should show a witnessed deep-sea colossus, not a poster. A small submersible window and instrument glow sit in the foreground as human-scale anchor; a damaged shipwreck, cut cables, silt cloud, and trench wall sit in the midground; the dragon-bone god is only partly visible in the background, with a half-lit skull ridge and rib arcs disappearing into black water beyond the frame. Physical feedback: silt scatters through lamp beams, cables pull taut, fish turn away, and the black current bends the light. Camera: low witness position from inside the submersible, restrained upward angle, medium telephoto compression, wide cinematic composition. Lighting: submersible lamps through turbid dark water, layered blue-gray shadows, controlled highlights, weathered bone texture, fine grain.
```

`D TVG P5`:

```text
黑潮里的龙骨神, produced through a high-pressure TVG cinematic colossal realism profile pass. The final image must feel like a real submersible crew accidentally witnessing a divine fossil presence that is too large to fully understand.

Scene: inside a cramped research submersible at the edge of a deep-sea trench during a black underwater current. Foreground: scratched curved observation window, dim instrument panels, a blurred observer shoulder, condensation and water streaks on glass, tiny lamp reflections. Midground: broken shipwreck ribs, torn cables pulled taut by the current, a diver-sized work light almost swallowed by silt, small fish turning sharply away, sediment rolling across the seafloor. Background: the dragon-bone god appears only in impossible fragments, a half-lit skull ridge behind the wreck, rib arches crossing both trench walls, a suggestion of one dark eye socket or shrine-like hollow in the skull, the rest of the body vanishing beyond the window frame and into black water. Physical feedback: black tide pushes silt laterally through all lamp beams, cables vibrate, ship fragments tremble, fish scatter, light cones shear and fade, the trench seems compressed by the scale of the bone god. Camera: low witness position from inside the submersible, medium telephoto compression, 2.39:1 widescreen, no full-body reveal, no centered poster pose. Lighting: credible submersible lamps and weak cold water glow, restrained dark-gold sediment glints in bone cracks, layered shadows, controlled highlights, turbid water scatter, fine film grain, lens-edge haze. Palette: near-black current, deep blue-gray, stone-white bone, rusted gold sediment, muted green instrument light.
```

### Four-Way Observations

- `A Direct` produced a dramatic full-body monster image. It had strong spectacle but weak
  witness framing, weak profile boundary, and little field discipline.
- `B Original SKILL` produced the strongest single-pass cinematic framing against this
  subject. It locked submersible-window viewpoint, scale layers, and underwater pressure
  with little runtime overhead.
- `C TVG P2` was close to the desired profile shape and preserved witness-scale control,
  but its pressure level made it more conservative and less mythically forceful than the
  original skill.
- `D TVG P5` produced the clearest profile-package signature: foreground instruments,
  witness position, cables, silt direction, frame overflow, partial deity fragments, and
  reviewable physical feedback. It is more controlled than `C`, and closer to surpassing
  `B` on auditability, but not obviously superior to `B` on immediate cinematic punch.

Review-bound conclusion:

The original skill remains very strong for first-shot prompt production. The current TVG
profile package at pressure 5 is the best Mindthus-shaped version because it creates a
more auditable visual contract while approaching the original skill's image quality. This
single Images2 run does not prove that TVG P5 is generally stronger than the original
skill.

## Beijing Black Dragon Pressure Comparison - 2026-07-01

Subject: `中国黑龙盘踞在京城上空，压迫感极强`

Compared variants:

1. `Original SKILL`: external skill behavior sample expansion.
2. `TVG P2`: current profile with ordinary pressure.
3. `TVG P4`: current profile with stronger pressure.
4. `TVG P5`: current profile with highest pressure.

Local ignored artifacts:

- `tests/artifacts/tvg_beijing_black_dragon_original_skill.png`
- `tests/artifacts/tvg_beijing_black_dragon_tvg_p2.png`
- `tests/artifacts/tvg_beijing_black_dragon_tvg_p4.png`
- `tests/artifacts/tvg_beijing_black_dragon_tvg_p5.png`
- `tests/artifacts/tvg_beijing_black_dragon_tuned_p4.png`
- `tests/artifacts/tvg_beijing_black_dragon_tuned_p4_v2.png`
- `tests/artifacts/tvg_beijing_black_dragon_contact_sheet.png`
- `tests/artifacts/tvg_beijing_black_dragon_tuned_v2_contact_sheet.png`

Observed one-run comparison:

- `Original SKILL` produced the strongest result in this run. It won on immediate
  cinematic punch because the dragon head, storm aperture, city, palace edge, rain,
  and witnesses formed one decisive threat image.
- `TVG P2` preserved scale and scene readability, but it was too conservative for
  "压迫感极强"; the prompt contract was correct but the first read was less forceful.
- `TVG P4` moved closer to the right balance, with clearer dragon readability and
  stronger overhead pressure than P2, while retaining witness and city anchors.
- `TVG P5` produced the strongest profile signature, but some of its extra field
  discipline competed with the primary threat image.

Tuning implication:

The profile should not copy the external skill wording. It should abstract the winning
behavior as a profile surface: a decisive pressure frame. High-pressure TVG should still
keep witness scale, physical feedback, partial visibility, and runtime-support
boundaries, but it needs one dominant near-overhead subject fragment that lands before
secondary detail.

Follow-up tuning result:

Adding decisive-pressure-frame support and a narrow upper-third focal guardrail moved
the TVG P4 image closer to the original skill: the dragon head became a clearer
near-overhead threat while witness scale, palace wall, city lights, rain, and traffic
remained visible. The original skill still had the strongest one-shot directorly punch
in this run because its storm aperture, head placement, and contrast formed a cleaner
primary image. The tuned TVG profile reduced the gap without claiming superiority.

This remains one-run loop-assisted production evidence, not proof that the external
skill is generally better or that the tuned profile is generally mature.
