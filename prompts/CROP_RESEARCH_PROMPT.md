# Deep Research: Optimal Photo Cropping & Framing for Dating Profile Photos

Paste everything below the `---` line into ChatGPT Deep Research or Gemini Deep Research.

---

## What I Need

I'm building an app that analyzes dating profile photos and recommends the optimal crop (aspect ratio, framing, positioning). The app uses AI to detect what's in the photo (face visibility, scene type, etc.), then auto-crops based on data.

I need you to research and produce one thing: **a lookup table that maps photo scenarios to the highest-performing crop strategy, backed by evidence.**

## The Research

Search the web for data on how photo cropping, framing, aspect ratio, and composition affect dating app outcomes (matches, likes, messages, right-swipes). I need statistics, not opinions.

**Sources to find:**
- Tinder, Hinge, Bumble published photo guidelines and display dimensions
- How each dating app auto-crops uploaded photos (what gets cut off)
- Photofeeler data on framing and composition vs attractiveness ratings
- OkCupid / OkTrends research on photo composition
- Academic studies on facial positioning, eye-level framing, and first impressions
- Professional dating photographer recommendations on framing (The Match Artist, Hey Saturday, Vida Select)
- Photography composition research (rule of thirds, center-weighted, etc.) applied to portraits
- A/B test results comparing different crops of the same photo
- Instagram/social media engagement data by aspect ratio (transferable to dating apps)
- Any data on how much background context helps or hurts in dating photos

**What the research should answer:**
- **Aspect ratio**: Does 4:5 outperform 1:1 or 16:9? By how much? On which platforms?
- **Portrait vs landscape orientation**: What's the engagement difference?
- **Face positioning**: Center vs upper third vs rule of thirds — what performs best?
- **Framing tightness**: Tight headshot vs half-body vs full-body — which gets more matches?
- **Background context**: How much background helps (travel, activity) vs hurts (clutter, mess)?
- **Group photos**: How tight should you crop around yourself?
- **Platform auto-cropping**: What does Tinder/Hinge/Bumble cut off if the ratio is wrong?
- **Subject prominence**: What percentage of frame should the person occupy?
- **Negative space**: Does breathing room around the subject help or hurt?

## The Scenarios

For each of these photo types, I need the optimal crop strategy:

1. Close-up headshot, indoor (good lighting)
2. Close-up headshot, outdoor
3. Close-up headshot, poor lighting / dark
4. Half-body portrait (waist up), any setting
5. Full body shot, outdoor
6. Full body shot, indoor
7. Activity / action shot (hiking, sports, cooking, etc.)
8. Group / social photo (you + friends)
9. Travel / scenic location photo
10. Urban / city portrait
11. Nightlife / bar scene
12. Professional / formal photo
13. Photo with distracting / cluttered background
14. Landscape-oriented photo that needs reframing to portrait
15. Already well-framed photo that doesn't need cropping

## The Output I Need

Produce a table like this. Each row is a photo scenario. The crop column is your research-backed recommendation.

```
SCENARIO: [what the AI detects — e.g. "Close-up headshot, indoor"]
BEST ASPECT RATIO: [e.g. "4:5 (0.8)"]
FACE/SUBJECT POSITION: [center | face_upper_third | rule_of_thirds]
FRAMING: [how tight — percentage of padding around subject]
EVIDENCE: [specific data/study supporting this]
PLATFORM NOTES: [how Tinder/Hinge/Bumble handle this ratio]
AVOID: [what NOT to do with cropping in this scenario]
```

## Also Include

At the end, provide a **platform reference table**:

```
PLATFORM: Tinder
DISPLAY RATIO: 4:5 (640x800px)
AUTO-CROP BEHAVIOR: [what happens when you upload a landscape photo]
BEST PRACTICE: [what to upload for zero cropping loss]

PLATFORM: Hinge
...

PLATFORM: Bumble
...
```

## Rules

- **Every recommendation must cite data.** A study, a platform's published specs, a professional's documented advice. If no data exists, write "no direct data — inferred from [X]."
- **4:5 is likely the universal answer** for aspect ratio on dating apps, but prove it with data. If square (1:1) or another ratio wins in specific scenarios, say so.
- **Face positioning matters more than aspect ratio** for headshots — research this thoroughly.
- **Quantify the impact** wherever possible: "rule of thirds placement increases perceived attractiveness by X%" is better than "rule of thirds looks better."
- **Keep it actionable.** Someone should read a row and know exactly how to crop their photo.
