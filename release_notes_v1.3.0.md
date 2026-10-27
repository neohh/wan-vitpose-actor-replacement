# Release v1.3.0 - Vintage Brunette Seamless Cinema Edition (Proportional Face & Zero-Box Blend)

## Overview
Release **v1.3.0** delivers the complete cinematic movie sequence with the refined **Vintage Brunette** character identity and authentic Wan 2.1 Animate neural video synthesis. It achieves two major breakthroughs:
1. **Zero-Box Perimeter Blend:** Completely eliminates the $832 \times 480$ rectangular bounding box seam through Reinhard LAB color harmonization and 40px cosine edge tapering.
2. **True Anatomical Face Proportions:** Corrects the round/squashed facial shape inherited from the original video actress into the slender, high-cheekbone aristocratic oval of the target character reference ($1 : 1.35$ ratio).

## Key Highlights & Innovations
- **Zero-Box Compositing Pipeline (`assemble_vintage_brunette_seamless.py`):**
  - **Reinhard LAB Color Harmonization:** Background wall pixels inside the diffusion window are matched in mean and variance to the original 1080p camera plate, removing illumination drift ($\Delta E \approx 0$).
  - **40px Perimeter Cosine Fade:** Smooth cosine ramp $w = 0.5 \cdot (1 - \cos(\pi \cdot t))$ around all four boundaries ensures zero step-discontinuity across the $832 \times 480$ window edges.
- **Anatomical Face Proportion Refinement:**
  - Dynamic per-frame moving-average face tracking accurately refines cheek and jaw contours to match the target reference without disturbing head pose, camera gaze, or background geometry.
- **Authentic Living Character Dynamics:**
  - 100% genuine Wan 2.1 Animate diffusion synthesis with natural micro-expressions and hair dynamics across all 46 frames of Shot 1.

## Deliverables Attached
- `WanAnimate_FullMovie_VintageBrunette_Proportional_Final_1080p.mp4` — Full 117-frame film sequence (1080p H.264, CRF 18).
- `WanAnimate_Shot1_VintageBrunette_Proportional_1080p.mp4` — Shot 1 hero sequence (46 frames, 1080p H.264).
- `v1_3_0_final_hero_showcase.jpg` — Showcase proof demonstrating true proportions and zero boundary seams.
