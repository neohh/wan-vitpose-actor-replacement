## v1.0.0 — Cinematic Character Replacement with ViTPose Wholebody Tracking & Wan 2.1 Animate

### 🌟 Highlights
- **ViTPose Wholebody Skeleton Tracking:** Anchors character head tilt (~12°), eye-level, 1.0x scale, and walking posture directly to the live actor, solving the bobblehead / 0° passport-look problem.
- **Expanded Hair & Anatomy Masking:** Dynamically dilates mask (+35px ellipse) to capture full hair volume (shaggy bob, curtain bangs, curls) while strictly clamping to preserve authentic props (books, hands, clothing).
- **Inverted Face-Oval Harmonizer (`inv_face_mask`):** Protects the face interior with 100% sharpness while performing edge-modulated bilateral smoothing on the hair and collar perimeter.
- **Production CLI & ComfyUI API Template:** Includes `replace_actor.py`, `queue_wan_job.py`, and multi-shot timeline assembly.

### 📦 Included Assets
- `wan_vitpose_shot1_1080p_demo.mp4` — Master 1080p demonstration render of Shot 1.
- `vitpose_comparison_card_f25.jpg` — 3-panel comparison card (original vs. tracked vs. final).
- `vitpose_lowdenoise_hero_f25_1080p.jpg` — 1080p hero frame.
