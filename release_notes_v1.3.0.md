# Release v1.3.0 - Vintage Brunette Seamless Cinema Edition (Zero-Box Blend)

## Overview
Release **v1.3.0** delivers the complete movie sequence with the refined **Vintage Brunette** master keyframe and authentic Wan 2.1 Animate neural video synthesis, completely eliminating the $832 \times 480$ rectangular bounding box seam through color harmonization and perimeter cosine blending.

## Key Highlights & Innovations
1. **Refined Master Keyframe (Frame 025):**
   - Precise head tilt and gaze aligned to camera right.
   - Clean facial aesthetics (no modern accessories, natural blush, emerald drop earrings).
   - Authentic antique leather-bound books and Slytherin school uniform intact.
2. **Pure Wan 2.1 Animate Diffusion:**
   - 46 frames of living character animation with dynamic facial micro-expressions and authentic hair physics.
3. **Zero-Box Compositing Pipeline (`assemble_vintage_brunette_seamless.py`):**
   - **Reinhard LAB Color Harmonization:** Background wall pixels inside the diffusion window are matched in mean and variance to the original 1080p camera plate, removing illumination drift ($\Delta E \approx 0$).
   - **40px Perimeter Cosine Fade:** Smooth cosine ramp $w = 0.5 \cdot (1 - \cos(\pi \cdot t))$ around all four boundaries ensures zero step-discontinuity across the $832 \times 480$ window edges.
   - **No Edge-Cutting:** Avoids tight silhouette cutouts that ruin translucent hair strands.

## Deliverables Attached
- `WanAnimate_FullMovie_VintageBrunette_Seamless_Final_1080p.mp4` — Full 117-frame film sequence (1080p H.264).
- `WanAnimate_Shot1_VintageBrunette_Seamless_1080p.mp4` — Shot 1 hero sequence (46 frames, 1080p H.264).
- `seamless_vintage_vs_old_box.jpg` — Side-by-side comparison proof demonstrating zero boundary seam.
