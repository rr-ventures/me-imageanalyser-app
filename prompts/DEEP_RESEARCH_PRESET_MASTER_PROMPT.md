# Deep Research: Definitive Lightroom Preset Recommendations for Dating Profile Photos

Paste this entire prompt into ChatGPT Deep Research, Gemini Deep Research, or Perplexity Pro. Then let it run a full research cycle. Run it 2-3 times and combine the outputs using the CONDENSE_REPORTS_PROMPT.

---

## Context

I'm building a personal tool that analyzes dating profile photos with AI and recommends exactly which Adobe Lightroom preset to apply for maximum dating app performance (likes, matches, messages). The app extracts metadata from each photo, matches it against a lookup table, and tells me which preset to use.

I already have a working style library that picks between 6 broad edit styles (warm golden, bright airy, moody cinematic, nightlife contrast, black & white, true to life). What I need now is a **separate, more specific artifact** that maps photo scenarios directly to individual Lightroom presets — especially the Adaptive presets that use AI masking.

This artifact must be backed by real data, not opinions. Every recommendation must cite a study, a platform's published statistics, a professional photographer's documented findings, or at minimum say "no direct data — inferred from [X]."

## What I Need You To Research

### Part 1: Which Photo Qualities Actually Drive Dating App Outcomes?

Find hard data on how specific visual properties of photos affect dating app performance. I need numbers, not vibes.

**Search for data from these sources:**
- Photofeeler published research on attractiveness, trustworthiness, and competence ratings vs. photo properties
- Hinge Labs / Hinge data releases on which photo qualities drive likes and matches
- OkCupid / OkTrends published research on photo performance
- Bumble published data or photo research
- Tinder published research or photo guidelines
- Academic studies on visual attractiveness, first impressions, and photo editing in online dating contexts (search Google Scholar for "online dating photo editing," "profile photo attractiveness," "dating app image quality")
- Professional dating photographers with documented methodologies (The Match Artist, Hey Saturday, Vida Select, Look Better Online)
- A/B test results comparing edited vs. unedited dating photos
- Any data on over-editing penalties — at what point does editing start hurting results?

**Specific questions to answer with data:**
1. Warm tones vs. cool tones — which produces more matches? By what percentage? In which contexts?
2. Bright vs. dark photos — how much does brightness affect interaction rates? Is there a ceiling where too bright hurts?
3. Background blur (bokeh) — does it measurably increase engagement? When does fake bokeh hurt?
4. Skin smoothing / facial enhancement — does it help or hurt perceived authenticity? Where is the line?
5. High contrast vs. low contrast — what performs better? Does it depend on the setting?
6. Natural vs. stylized editing — where exactly is the "catfish" threshold?
7. Photo resolution / sharpness — does it affect swipe rates? What minimum resolution matters?
8. Color saturation — does increased saturation help or hurt? By how much?
9. Shadow lifting — does revealing detail in shadows improve face-visibility scores?
10. Does visual consistency across a profile (same editing style) affect engagement?
11. How much does the editing style interact with the photo CONTENT (e.g., warm edit on a warm scene vs. warm edit on a cool scene)?

### Part 2: Which Lightroom Presets Map To Those Winning Properties?

Now connect the research findings to specific Lightroom presets. I need you to figure out which presets produce the visual properties that the data says perform best.

**Adobe Lightroom Premium Built-In Presets (prioritize these):**

*Adaptive presets (AI masking — these are the highest-impact because they selectively edit only specific regions):*

- **Adaptive: Portrait** — Enhance Portrait, Glamour Portrait, Polished Portrait, Gritty Portrait, Smooth Facial Skin, Enhance Eyes, Whiten Teeth, Darken Eyebrows, Darken Beard, Texture Hair, Smooth Hair, Enhance Clothes
- **Adaptive: Sky** — Blue Drama, Dark Drama, Blue Pop, Blue Hour, Golden Hour, Neon Tropics, Storm Clouds, Sunrise, Sunset
- **Adaptive: Subject** — Pop, Warm Pop, Light, Warm Light, Balance Contrast, Soft, Cool Soft, Vibrant, Glow
- **Adaptive: Blur Background** — Subtle, Strong, Circle, Circle Swirl, Bubble, Bubble Swirl, Geometric, Geometric Swirl, Ring, Ring Swirl, Oval, Oval Swirl
- **Adaptive: Landscape** — Spring01, Spring02, Summer01, Summer02, Autumn01, Autumn02, Winter01, Winter02

*Non-adaptive presets:*

- **Portraits** — Deep Skin, Medium Skin, Light Skin, Black & White, Edgy, Group (each has sub-presets — please find the complete list)
- **Style** — Cinematic, Cinematic II, Futuristic, Vintage, Black & White (each has sub-presets)
- **Subject** — Lifestyle, Travel, Travel II, Urban Architecture, Concerts, Food, Landscape
- **Seasons** — Spring, Summer, Autumn, Winter
- **Recommended** (free tab) — find what's in there
- **Auto+** — Retro

*Also search for these popular third-party presets and include them only if they demonstrably outperform built-in options for specific scenarios:*

- Mastin Labs (Portra 160, Portra 400, Portra 800, Fuji 400H, Ilford HP5)
- VSCO Film presets
- RNI All Films
- Peter McKinnon presets
- Tribe Archipelago (LXC, LXCN, Meridian)
- FilterGrade top portrait presets
- Any others frequently recommended by professional dating photographers

**For each preset you recommend, explain:**
1. What visual properties it produces (warmth, contrast, saturation, brightness, etc.)
2. Why those properties map to the research findings
3. What photo scenarios it works best for
4. What scenarios it would hurt

### Part 3: Scenario-to-Preset Mapping

My app detects these 6 metadata fields for each photo:

```
scene_type: outdoor | indoor | urban | nightlife | unknown
lighting: natural_warm | natural_cool | golden_hour | artificial | mixed | unknown
photo_quality: 0-10 (integer)
face_visible: yes | partial | no
expression: warm | neutral | serious | unknown
color_quality: good | flat | bad_mix | unknown
```

**Map each of the following scenarios to one specific best preset, with evidence:**

- Outdoor portrait, golden hour lighting, clear face, good colors
- Outdoor portrait, flat overcast daylight, face visible, flat colors
- Outdoor portrait, harsh midday sun, face in partial shadow
- Indoor portrait, natural window light, face visible
- Indoor portrait, artificial warm light, face visible
- Indoor portrait, mixed fluorescent lighting, face visible
- Urban/city background portrait, daytime
- Urban/city background portrait, night with artificial light
- Nightlife/bar/club scene, mixed colored lighting
- Beach or water scene, warm light
- Hiking/nature/sports activity shot
- Group/social photo, well-lit
- Group/social photo, low light/artificial
- Full body/outfit shot, outdoor
- Full body/outfit shot, indoor
- Professional/formal dressed-up photo
- Travel location scenic photo with person
- Close-up headshot, good lighting, high quality
- Close-up headshot, poor lighting or low quality
- Photo with bad/mixed unfixable colors
- Photo that is too dark or underexposed
- Photo with distracting busy background
- Face partially in shadow
- Visible skin blemishes or uneven skin

**For EACH scenario, provide:**
1. The single best Lightroom preset (exact name and path in Lightroom, e.g., "Premium > Adaptive: Subject > Warm Pop")
2. An optional second preset to stack (or null if stacking would be excessive)
3. Specific evidence for why this preset is best for this scenario (cite the data)
4. Which presets to avoid in this scenario and why

### Part 4: Danger Zones

List the 5-8 presets that are most likely to make a dating profile photo look fake, over-edited, or untrustworthy. For each one, specify:
- What goes wrong
- When it's actually safe to use (if ever)

## Rules For The Research

- **Cite specific data points.** "Warm tones perform better" is not enough. "Warm tones increase attractiveness ratings by 25-40% on Photofeeler (2019 dataset)" is what I need. If the data doesn't specify a number, say so.
- **If no direct data exists for a claim**, write "No direct data — inferred from [X]" and explain the inference chain.
- **Prefer built-in Adobe presets** over third-party. Most Lightroom Premium users have all the built-in presets immediately available. Only recommend third-party if the evidence shows they meaningfully outperform.
- **Weight Adaptive presets heavily.** These use AI masking to edit only specific regions (face, subject, sky, background). They are almost certainly the highest-impact presets because they can fix problems selectively without affecting the rest of the image. Analyze their specific advantages.
- **Be critical of your own recommendations.** For each scenario, ask yourself: "Would this preset make the photo look fake or over-edited?" If there's a risk, say so.
- **Don't conflate correlation with causation.** If a study found that "photos with warm tones get more likes," that might be because warm-tone photos tend to be outdoor golden-hour photos (which are inherently more attractive contexts), not because warm tones themselves cause attraction. Call out these confounds.
- **Consider the stacking question carefully.** When you recommend stacking two presets, explain why the combination is better than either alone, and flag any risk of over-processing.

## Output Format

Structure your output as:

### Research Findings
For each of the 11 questions in Part 1, provide the data you found with sources cited.

### Preset Analysis
For each recommended preset, explain what it does and why the research supports it.

### Scenario Mapping Table
For each of the 24 scenarios, provide:
```
SCENARIO: [description]
CONDITIONS: [which metadata field values trigger this]
BEST PRESET: [exact Lightroom path]
ALSO APPLY: [second preset or "none"]
EVIDENCE: [specific data with source]
AVOID: [what not to use and why]
CONFIDENCE: [high / medium / low — based on strength of evidence]
```

### Danger Zones
List of 5-8 presets with risks and safe-usage notes.

### Gaps and Caveats
List any scenarios where the evidence is weak, conflicting, or missing. Be honest about what you couldn't find.

---

## Important Notes

- I am optimizing for AUTHENTICITY FIRST. The research should weight natural, trustworthy-looking edits over dramatic effects. Recommendations that risk looking "filtered" should be flagged as such.
- This is for personal use, not a commercial product. I want genuinely better photos, not marketing copy.
- I will run this prompt multiple times and merge the results, so be as thorough as possible in a single run. More data is better.
- If you find conflicting evidence between sources, include both and explain the conflict rather than picking one.
