# Condense Two Research Reports into a Single App Artifact

Paste this prompt into ChatGPT or Gemini, then paste both research reports below it.

---

## Your Task

I have two research reports about which Adobe Lightroom presets perform best for dating profile photos. They were generated from the same research prompt but may have different findings, conflicting recommendations, or complementary data.

I need you to merge them into **one structured YAML artifact** that my app will load directly. The app uses this artifact to match AI-detected photo metadata to the best Lightroom preset recommendation.

## How the App Works

1. **AI analyzes a photo** and returns exactly these 6 metadata fields:

```
scene_type: outdoor | indoor | urban | nightlife | unknown
lighting: natural_warm | natural_cool | golden_hour | artificial | mixed | unknown
photo_quality: 0-10 (integer)
face_visible: yes | partial | no
expression: warm | neutral | serious | unknown
color_quality: good | flat | bad_mix | unknown
```

2. **The app loads your YAML artifact** and scores each scenario's `conditions` against the metadata. The scenario with the most matching conditions wins.

3. **The app displays** the preset name, path, evidence, also-apply, and avoid to the user.

## Merging Rules

When the two reports disagree on which preset is best for a scenario:
- **Pick the one with stronger evidence** (specific stats > general claims > opinions).
- **If evidence is equal**, prefer the Adobe built-in Adaptive preset over third-party or non-Adaptive presets (because Adaptive presets use AI masking and are more impactful).
- **If both recommend different presets and both have good evidence**, use the one with the broader applicability as `preset.name` and put the other in `preset.also_apply`.
- **Combine the evidence** from both reports into a single `evidence` string. Cite both sources.
- **Union the avoid lists** — if either report says to avoid something, include it.

When the two reports agree, combine their evidence for a stronger justification.

If one report covers scenarios the other doesn't, include all unique scenarios from both.

## Target: 15-25 scenarios max

Don't create 50+ scenarios. Merge similar ones. The matching algorithm picks the most specific match, so:
- A scenario with 4 conditions will beat one with 2 conditions for the same photo.
- A scenario with 0 conditions is a fallback (never matches by specificity).
- Keep scenarios distinct — don't have two scenarios with identical conditions.

## Output Format

Output **only** the YAML below. No explanation, no markdown fences around it, no commentary. Just raw YAML that I will save directly as a `.yml` file.

```yaml
artifact_name: lightroom_preset_recommendations_v1
artifact_type: scenario_to_preset_lookup
status: research_backed
last_updated: "YYYY-MM-DD"
sources:
  - "source 1 description"
  - "source 2 description"

scenarios:
  - id: short_snake_case_id
    name: "Human-readable scenario name"
    conditions:
      scene_type: outdoor
      lighting: golden_hour
      face_visible: [yes, partial]
    preset:
      name: "Exact Preset Name"
      path: "Premium > Category > Preset Name"
      also_apply: "Premium > Category > Second Preset"
      evidence: "Specific stats and citations from the research. Combine findings from both reports."
      avoid: "Preset names to avoid and why, in one sentence"

  - id: next_scenario
    name: "..."
    conditions:
      # conditions use the exact metadata field names and values listed above
      # use a list for multiple acceptable values: [yes, partial]
      # omit a field to not filter on it
      # for photo_quality ranges, use a list: [0, 1, 2, 3, 4, 5]
    preset:
      name: "..."
      path: "..."
      also_apply: null
      evidence: "..."
      avoid: "..."

danger_zones:
  - preset: "Preset Name"
    risk: "What can go wrong"
    safe_usage: "When it's actually OK to use"
```

## Conditions Reference

Each condition key must be one of the 6 metadata fields. Values must match exactly:

| Field | Possible Values |
|-------|----------------|
| `scene_type` | `outdoor`, `indoor`, `urban`, `nightlife`, `unknown` |
| `lighting` | `natural_warm`, `natural_cool`, `golden_hour`, `artificial`, `mixed`, `unknown` |
| `photo_quality` | `0` through `10` (use a list for ranges, e.g. `[0, 1, 2, 3, 4, 5]`) |
| `face_visible` | `yes`, `partial`, `no` |
| `expression` | `warm`, `neutral`, `serious`, `unknown` |
| `color_quality` | `good`, `flat`, `bad_mix`, `unknown` |

Use a **list** when multiple values should match: `face_visible: [yes, partial]`

Omit a field entirely if it doesn't matter for that scenario.

## Token Optimization

This artifact is loaded into memory once and used for lookups. Optimize for:
- **Concise evidence strings** — cite the stat and source, skip filler words. Aim for 1-2 sentences max.
- **No duplicate information** — if two scenarios have the same `avoid`, that's fine, but don't repeat long explanations.
- **Short `also_apply`** — just the path string, or `null` if not needed.
- **Danger zones** — keep to 5-8 entries max. Only the presets that genuinely risk making photos look fake.

## Quality Checklist

Before outputting, verify:
- [ ] Every `conditions` key is one of the 6 metadata fields
- [ ] Every `conditions` value is from the allowed values listed above
- [ ] Every `preset.path` uses the format `Premium > Category > Preset Name`
- [ ] Every `evidence` field cites at least one specific data point
- [ ] No two scenarios have identical `conditions`
- [ ] `id` fields are unique snake_case
- [ ] `also_apply` is either a path string or `null`
- [ ] Total scenarios: 15-25
- [ ] Total danger_zones: 5-8
- [ ] Output is valid YAML (no tabs, consistent indentation)

---

## PASTE RESEARCH REPORT 1 BELOW:

[paste report 1 here]

## PASTE RESEARCH REPORT 2 BELOW:

[paste report 2 here]
