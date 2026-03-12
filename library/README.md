# Style Library

This folder contains the YAML library that drives all style decisions.

## How it works

1. **Gemini AI** looks at your photo and extracts 6 simple metadata fields
2. **The selector** compares that metadata against the routing rules in the YAML file
3. **The app** returns the top 2 styles with Lightroom presets and Facetune checklists

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

## Editing the library

You can edit `dating_profile_filter_library_v2.yml` to:
- Adjust which style is picked for which situation
- Change Lightroom slider values
- Update preset recommendations
- Modify Facetune checklists

The app re-reads the library when it starts, so just restart after editing.
