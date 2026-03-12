# Production Artifacts

This folder contains the YAML artifacts that drive all recommendations.
Only files prefixed with `production_` are used by the app at runtime.

## The three production artifacts

| File | What it does |
|------|-------------|
| `production_filter_library.yml` | 6 broad editing styles with Lightroom presets and slider values. The style selector picks the best overall approach for each photo. |
| `production_preset_recommendations.yml` | 20 scenario-specific Lightroom Adaptive preset recommendations. The preset matcher picks the exact Adaptive preset to click in Lightroom. |
| `production_crop_recommendations.yml` | 11 scenario-specific crop recommendations with aspect ratios, focus points, and platform guidance. |

## How it works

1. **Gemini AI** looks at your photo and extracts 6 simple metadata fields
2. **The style selector** compares metadata against routing rules in the filter library
3. **The preset matcher** finds the best scenario-specific Adaptive preset
4. **The crop matcher** recommends 2-3 crop options with evidence

## The 6 metadata fields

| Field | Type | What it means |
|-------|------|--------------|
| `scene_type` | outdoor / indoor / urban / nightlife / unknown | Where was the photo taken? |
| `lighting` | natural_warm / natural_cool / golden_hour / artificial / mixed / unknown | What kind of light? |
| `photo_quality` | 0-10 | Overall quality score |
| `face_visible` | yes / partial / no | Can you see the face clearly? |
| `expression` | warm / neutral / serious / unknown | Person's expression/vibe |
| `color_quality` | good / flat / bad_mix / unknown | Are colors natural or weird? |

## The 6 styles

| Style | When it's used | Vibe |
|-------|---------------|------|
| `true_to_life_clean` | Default safe choice | Natural, authentic, minimal edit |
| `warm_golden` | Golden hour / sunset photos | Warm, sun-kissed, inviting |
| `bright_airy` | Flat or dull daylight photos | Light, fresh, lifted |
| `moody_cinematic` | Urban / architectural backgrounds | Cinematic, contrast, cool |
| `nightlife_contrast` | Bars, clubs, night photos | Punchy, color-corrected |
| `black_white` | Photos with bad/weird colors | Classic B&W rescue |

## Editing the artifacts

You can edit `production_filter_library.yml` to:
- Adjust which style is picked for which situation
- Change Lightroom slider values
- Update preset recommendations

The app re-reads the library when it starts, so just restart after editing.

## Gemini models

- **Analysis:** Gemini 3.1 Pro Preview (`gemini-3.1-pro-preview`)
- **Image Enhancement:** Nano Banana 2 (`gemini-3.1-flash-image-preview`)
