# Deep Research: Which Lightroom Preset Performs Best for Each Dating Photo Scenario?

Paste everything below into ChatGPT Deep Research or Gemini Deep Research.

---

## What I Need

I'm building an app that analyzes dating profile photos and recommends the single best Adobe Lightroom preset to apply. The app uses AI to detect what's in the photo (lighting, scene, face visibility, etc.), then picks the optimal preset based on data.

I need you to research and produce one thing: **a lookup table that maps photo scenarios to the highest-performing Lightroom preset, backed by evidence.**

## The Research

Search the web for data on how specific photo edits affect dating app outcomes (matches, likes, messages, right-swipes). I need statistics, not opinions.

**Sources to find:**
- Photofeeler published data on attractiveness/trustworthiness ratings vs photo qualities
- Hinge data releases on which photos get the most likes
- OkCupid / OkTrends research on photo performance
- Bumble, Tinder published data or photo guidelines
- Academic studies on visual attractiveness, first impressions, and photo editing in online dating (Google Scholar)
- Professional dating photographer recommendations (The Match Artist, Hey Saturday, Vida Select)
- A/B test results comparing edited vs unedited dating photos
- Any data on over-editing penalties (when editing starts hurting results)

**What the research should answer:**
- Warm tones vs cool tones — which gets more matches? By how much?
- Bright vs dark photos — which performs better? Data?
- Background blur — does it measurably increase engagement?
- Skin smoothing / face enhancement — does it help or hurt authenticity?
- High contrast vs low contrast — what performs?
- Natural vs stylized editing — where's the line?
- Does photo quality/resolution affect swipe rates?

## The Lightroom Presets

Here is an incomplete list of the presets available in Adobe Lightroom (cloud, Premium subscription). I need you to figure out which ones map to the scenarios that perform best. 
Also need you to try and go through online and find all the adobe lightroom presets that are available and also popular third party ones that a dating photographer might use. The goal is to figure out exactly which presets are most popular and the 'best' for this specific use case, so that way we have a list of presets that the AI can select from in this app we are building and be able to justfiy why its the best one. But we dont want 100s of filters, maybe 10-20 max that it can choose from to apply to a photo to make it objectively better to use on dating apps

**Adaptive: Portrait** (AI face masking) — Enhance Portrait, Glamour Portrait, Polished Portrait, Gritty Portrait, Smooth Facial Skin, Enhance Eyes, Whiten Teeth, Darken Eyebrows, Darken Beard, Texture Hair, Smooth Hair, Enhance Clothes

**Adaptive: Sky** (AI sky masking) — Blue Drama, Dark Drama, Blue Pop, Blue Hour, Golden Hour, Neon Tropics, Storm Clouds, Sunrise, Sunset

**Adaptive: Subject** (AI subject masking) — Pop, Warm Pop, Light, Warm Light, Balance Contrast, Soft, Cool Soft, Vibrant, Glow

**Adaptive: Landscape** — Spring01, Spring02, Summer01, Summer02, Autumn01, Autumn02, Winter01, Winter02

**Adaptive: Blur Background** — Subtle, Strong, Circle, Circle Swirl, Bubble, Bubble Swirl, Geometric, Geometric Swirl, Ring, Ring Swirl, Oval, Oval Swirl

**Portraits:** Deep Skin, Medium Skin, Light Skin, Black & White, Edgy, Group (each has sub-presets — find the full list)

**Style:** Cinematic, Cinematic II, Futuristic, Vintage, Black & White (each has sub-presets)

**Subject:** Lifestyle, Travel, Travel II, Urban Architecture, Concerts, Food, Landscape

**Seasons:** Spring, Summer, Autumn, Winter

**Auto+:** Retro

Also search for what's in the free **Recommended** tab.

Additionally, search for the most popular **third-party** Lightroom presets for portrait photography (Mastin Labs, VSCO, RNI Films, Peter McKinnon, Tribe Archipelago, and whatever else comes up on FilterGrade, Creative Market, Etsy). Include these as alternatives where they outperform the built-in options.

## The Output I Need

Produce a table like this. Each row is a photo scenario the app might detect. The preset column is your research-backed recommendation. The evidence column cites the specific data.

```
SCENARIO: [what the AI detects in the photo]
BEST PRESET: [single Lightroom preset to apply]
ALSO APPLY (if needed): [optional second preset, only if clearly beneficial]
EVIDENCE: [specific data/study supporting this choice]
AVOID: [presets that would hurt in this scenario]
```

**Cover at least these scenarios:**

- Outdoor portrait, golden hour lighting
- Outdoor portrait, flat/overcast daylight
- Outdoor portrait, harsh midday sun
- Indoor portrait, natural window light
- Indoor portrait, artificial/warm light
- Indoor portrait, mixed/fluorescent light
- Urban/city background, daytime
- Urban/city background, night
- Nightlife/bar/club scene, mixed colored lighting
- Beach/water scene
- Hiking/nature activity shot
- Group/social photo, well-lit
- Group/social photo, low light
- Full body/outfit shot, outdoor
- Full body/outfit shot, indoor
- Professional/formal setting
- Travel location scenic photo
- Close-up headshot, good lighting
- Close-up headshot, poor lighting
- Photo with bad/mixed colors that need rescuing
- Photo that's too dark / underexposed
- Photo with distracting busy background
- Photo where face is partially in shadow
- Photo with visible skin blemishes or uneven skin

For each scenario, tell me:
1. The single best preset (with the exact Lightroom path)
2. Why, with specific data
3. What NOT to use

## Rules

- **Every recommendation must cite data.** A study, a platform's published stats, a professional photographer's documented recommendation. If no data exists for a claim, write "no direct data — inferred from [X]."
- **Prefer built-in Adobe presets** over paid third-party ones. Most users have Lightroom Premium already.
- **Flag danger zones clearly.** Which presets risk looking fake? Where's the "catfish" line?
- **The Adaptive presets use AI masking** — they selectively edit only the face, skin, eyes, background, or sky. These are probably the highest-impact presets. Weight your analysis accordingly.
- **Keep it actionable.** Someone should be able to read a row, open Lightroom, find the preset, and apply it. Done.
