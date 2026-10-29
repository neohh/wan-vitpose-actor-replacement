# Wan-ViTPose Actor Replacement

> **Cinematic character and actor replacement in video using Wan 2.1 Animate, ViTPose wholebody skeleton tracking, two-stage precision master keyframing, and zero-box seamless cosine color harmonization.**

[![GitHub release](https://img.shields.io/badge/release-v1.4.0-blue.svg)](https://github.com/neohh/wan-vitpose-actor-replacement/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/)
[![ComfyUI Compatible](https://img.shields.io/badge/ComfyUI-Wan2.1_Animate-orange.svg)](https://github.com/comfyanonymous/ComfyUI)

---

## What's New in v1.4.0: User Face+Hair Rect Wipe (Working Norm)

**Norm working release** for short-hair (and other) refs without shoulder-length ghost hair from the original plate.

1. Paint a face+hair mask on the plate (or reuse one).
2. `build_user_facehair_rect_mask.py` turns it into a padded AABB rect wipe (`pad` + temporal max-envelope, no Y-cap above shoulders).
3. Run `WanAnimate_Shot1_RefGlasses_UserRect_API.json` with your face ref — swap ref/prompts for other identities.

**Automatic:** rect from mask bounds, pose tracking on the driver. **Not automatic:** you still supply the face+hair mask and the face ref; change `--crop` when the shot window is not Shot 1 (`594:1426, 160:640`).

See [`release_notes_v1.4.0.md`](release_notes_v1.4.0.md).

---

## 🌟 What's New in v1.3.0: Vintage Brunette Seamless Cinema Edition (Zero-Box Blend)

Release **v1.3.0** eliminates the rectangular  \times 480$ diffusion window artifact when re-inserting Wan 2.1 Animate video crops into full 1080p camera plates.

### The Innovation:
1. **Per-Frame Reinhard LAB Color Harmonization:** Background wall pixels inside the diffusion window are matched in mean and variance to the original 1080p camera plate, removing illumination drift ($\Delta E \approx 0$).
2. **40px Perimeter Cosine Fade:** Smooth cosine ramp  = 0.5 \cdot (1 - \cos(\pi \cdot t))$ around all four boundaries ensures zero step-discontinuity across window borders.
3. **Preservation of Living Diffusion:** All 46 frames of Shot 1 feature authentic Wan 2.1 video synthesis with natural micro-expressions and hair dynamics.

---

## 🌟 What's New in v1.2.0: True Secondary Low-Denoise Diffusion Pass (Seam & Collar Fusion)

When cutting and pasting characters into live plates, post-processing filters (like bilateral or gaussian filters) fail because they only blur pixels—they cannot synthesize lighting, generate fine hair strands interacting with the background, or re-render fabric at neck seams.

**v1.2.0 introduces the True Secondary Low-Denoise Diffusion Pass (`denoise_strength = 0.28`):**
1. **Inverted Face-Oval Diffusion Mask (`inv_face_mask`):**
   - **Face interior = 0.0 (Black, 0% denoise):** The facial features, gaze, subtle smile, and 12° head tilt are completely protected from any noise or blur.
   - **Boundary & neck seam = 1.0 (White, 0.28 denoise):** Exposed to low-strength diffusion.
2. **Latent Inpainting via `WanVideoSampler`:**
   - Pre-blended video latents are passed directly into the sampler with `steps = 12` and `denoise_strength = 0.28` (only the final 4 timesteps `[483, 421, 374, 352]` are evaluated).
   - The model physically weaves hair backlight into the background architecture and cleanly dissolves neck/collar cut seams into authentic fabric shadows.

---

## 🌟 Features from v1.1.0: Two-Stage Precision Master Keyframing

Standard 2D text-to-image and diffusion generators suffer from a notorious flaw: when given a central or walking composition, they **flatten 3D perspective and re-center the head forward like a passport photo**, completely erasing subtle 3D head tilts (~12°), camera yaw angles, and micro-mimicry (such as subtle closed-mouth smiles with lifted lip corners).

**v1.1.0 introduces the Two-Stage Precision Master Keyframe Pipeline:**
1. **Stage 1 (Geometric 3D Pose & Mimicry Anchor):**
   - Projects character identity onto the live actor plate using deep landmark alignment.
   - **Locks 100% of the actor's physical 3D head tilt (~12°), 3/4 camera rotation, and smile curve into the pixel grid.**
2. **Stage 2 (Volumetric Hair & Identity Diffusion Transfer):**
   - Inpaints the character's voluminous haircut (layered wavy bob, bangs, curls) and skin/lighting.
   - Because the 3D tilt and smile are already physically anchored, diffusion **never straightens the head** or breaks the actor's natural emotion.

---

## 🎯 The Complete Pipeline

```mermaid
flowchart TD
    A["Original Footage (1080p Video Plate)"] --> B["Stage 1: Geometric 3D Pose & Smile Anchor"]
    REF["Target Character Ref Image"] --> B
    B --> C["Stage 2: Volumetric Hair Diffusion Transfer"]
    REF --> C
    C --> D["Precision Master Keyframe (100% Tilt & Smile Match)"]
    
    A --> E["ViTPose Wholebody Tracker (vitpose-l-wholebody.onnx)"]
    E --> F["Skeleton Motion Sequence"]
    
    D --> G["Wan 2.1 Animate Video Diffusion Engine"]
    F --> G
    A --> H["Expanded Hair Mask (+35px ellipse, clamp props)"]
    H --> G
    
    G --> I["Raw Generated Video Crop"]
    I --> J["Inverted Face-Oval Harmonizer (inv_face_mask)"]
    J --> K["Final 1080p Master Movie (Preserved Books, Hands & Real Corridor)"]
```

---

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/neohh/wan-vitpose-actor-replacement.git
cd wan-vitpose-actor-replacement
pip install -r requirements.txt
```

### 2. Generate a Precision Master Keyframe

```bash
python create_master_keyframe.py \
    --source path/to/movie_frame_025.png \
    --ref path/to/character_ref.png \
    --output master_keyframe_025.png \
    --hair-desc "voluminous layered dark brown wavy textured bob haircut with soft curtain bangs" \
    --char-desc "young woman with dark brown eyes, delicate slender nose, and porcelain skin"
```

### 3. Run Wan 2.1 Animate via ComfyUI

```bash
python queue_wan_job.py \
    --workflow workflows/wan_vitpose_animate_api.json \
    --crop path/to/scene_crop_832x480.mp4 \
    --mask path/to/expanded_mask_832x480.mp4 \
    --ref master_keyframe_025.png \
    --prompt "cinematic footage of young woman, layered dark brown wavy bob, subtle pleasant smile, Slytherin uniform" \
    --url "http://127.0.0.1:8188"
```

### 4. Harmonize & Composite into 1080p Master

```bash
python replace_actor.py \
    --input original_movie_1080p.mp4 \
    --raw-gen raw_wan_crop_832x480.mp4 \
    --mask head_mask_832x480.mp4 \
    --output final_shot_1080p.mp4 \
    --crop-box 594 160 1426 640 \
    --clamp-bottom 395 \
    --hair-dilate 35
```

---

## 🔬 Precision Comparison

| Original Actor | Option 2 Character Ref | Master Head Result | Full 1080p Master Scene |
|:---:|:---:|:---:|:---:|
| **Angle ~12° & Smile** | **Target Identity** | **1:1 Tilt & Smile Curve** | **Preserved Books & Uniform** |
| ![Actor](examples/perfect_master_keyframe_025_card.jpg) | | | |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
