# Condense Crop/Framing Research into an App Artifact

Paste this prompt into ChatGPT or Gemini, then paste your research report(s) below it.

---

## Your Task

I have research about how cropping, framing, and aspect ratios affect dating profile photo performance. I need you to turn this into a single structured YAML artifact that my app loads to recommend the optimal crop for each photo.

## How the App Works

1. **AI analyzes a photo** and returns these metadata fields:

```
scene_type: outdoor | indoor | urban | nightlife | unknown
lighting: natural_warm | natural_cool | golden_hour | artificial | mixed | unknown
photo_quality: 0-10
face_visible: yes | partial | no
expression: warm | neutral | serious | unknown
color_quality: good | flat | bad_mix | unknown
```

2. **The app also knows** the photo's pixel dimensions (width x height).

3. **The app loads your YAML** and matches metadata conditions to the best crop scenario. It then calculates exact crop coordinates from the recommendation.

4. **The user sees** an "Auto Crop" button. Clicking it applies the recommended crop. They can also manually crop or revert.

## What Each Crop Recommendation Contains

For each scenario, the artifact specifies:
- **aspect_ratio**: width/height as a decimal (e.g. 0.8 = 4:5 portrait, 1.0 = square)
- **aspect_label**: human-readable label ("4:5", "1:1", etc.)
- **focus**: where to anchor the crop — `center`, `face_upper_third`, or `rule_of_thirds`
- **padding_pct**: how much breathing room around the subject (percentage)
- **evidence**: research-backed reason for this crop
- **platform_note**: how specific dating apps handle this ratio

## Output Format

Output **only** raw YAML. No markdown fences, no commentary. I will save this directly as a `.yml` file.

```yaml
artifact_name: crop_recommendations_v1
artifact_type: scenario_to_crop_lookup
status: research_backed
last_updated: "YYYY-MM-DD"
sources:
  - "source description"

scenarios:
  - id: short_snake_case_id
    name: "Human-readable scenario name"
    conditions:
      face_visible: yes
      scene_type: indoor
    crop:
      aspect_ratio: 0.8
      aspect_label: "4:5"
      focus: face_upper_third
      padding_pct: 15
      evidence: "Concise research-backed reason. Cite stats."
      platform_note: "How Tinder/Hinge/Bumble handle this."

  - id: next_scenario
    name: "..."
    conditions:
      # Use exact metadata field names and values from the table above
      # Use lists for multiple values: [yes, partial]
      # Omit fields that don't matter for this scenario
    crop:
      aspect_ratio: 0.8
      aspect_label: "4:5"
      focus: center
      padding_pct: 10
      evidence: "..."
      platform_note: "..."

platform_requirements:
  - platform: Tinder
    display_ratio: "4:5 (640x800)"
    notes: "How this platform handles photos"
  - platform: Hinge
    display_ratio: "..."
    notes: "..."
```

## Key Questions the Research Should Answer

Map your research findings to these decisions:

1. **What aspect ratio performs best on each dating platform?** (Tinder, Hinge, Bumble, etc.)
2. **Does framing (tight vs wide) affect match rates?** Data?
3. **Where should the face be positioned?** Center, upper third, rule of thirds?
4. **How much background context helps vs hurts?** By scenario (headshot vs travel vs activity)
5. **Does cropping out background clutter improve results?** Evidence?
6. **Landscape vs portrait orientation** — what percentage difference in engagement?
7. **What about square (1:1)?** When is it better than 4:5?

## Conditions Reference

| Field | Possible Values |
|-------|----------------|
| `scene_type` | `outdoor`, `indoor`, `urban`, `nightlife`, `unknown` |
| `lighting` | `natural_warm`, `natural_cool`, `golden_hour`, `artificial`, `mixed`, `unknown` |
| `photo_quality` | `0` through `10` |
| `face_visible` | `yes`, `partial`, `no` |
| `expression` | `warm`, `neutral`, `serious`, `unknown` |
| `color_quality` | `good`, `flat`, `bad_mix`, `unknown` |

## Rules

- **10-15 scenarios max.** Merge similar ones. The matching picks the most specific match.
- **Every evidence field must cite data.** If no direct data, write "inferred from [X]."
- **aspect_ratio must be a decimal** — width divided by height (0.8 for 4:5, 1.0 for 1:1, 0.5625 for 9:16)
- **focus must be one of:** `center`, `face_upper_third`, `rule_of_thirds`
- **padding_pct is 0-30** — percentage of extra space around the subject
- **The last scenario should have empty conditions `{}`** as a fallback
- **Include platform_requirements** at the bottom with how each major dating app handles aspect ratios

## Quality Checklist

- [ ] Every `conditions` key is a valid metadata field
- [ ] Every `conditions` value is from the allowed values
- [ ] `id` fields are unique snake_case
- [ ] `aspect_ratio` is a decimal number
- [ ] `focus` is one of the three allowed values
- [ ] Evidence cites at least one data point per scenario
- [ ] 10-15 scenarios total
- [ ] Last scenario has `conditions: {}` as fallback
- [ ] Valid YAML (no tabs, consistent 2-space indentation)

---

## PASTE RESEARCH REPORT(S) BELOW:

[paste here]
