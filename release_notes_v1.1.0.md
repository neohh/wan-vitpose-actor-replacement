## v1.1.0 — Two-Stage Precision Master Keyframing (1:1 Head Tilt, 3D Rotation & Mimicry)

### 🌟 What's New
- **Two-Stage Precision Master Keyframing (`create_master_keyframe.py`):**
  Eliminates the persistent diffusion "flattening" flaw where models re-center characters straight to the camera, flattening subtle 3D tilts and micro-expressions.
  - **Stage 1 (Geometric 3D Pose & Smile Anchor):** Uses landmark alignment to lock 100% of the actor's physical 3D head tilt (~12°), camera yaw, and subtle closed-mouth smile into the pixel grid.
  - **Stage 2 (Volumetric Hair & Likeness Transfer):** Inpaints the character's signature voluminous hairstyle, eye features, and skin texture without allowing diffusion to straighten the neck or alter the smile.
- **`core/master_keyframe.py`:** Core module implementing landmark geometric projection and prompt formulation.
- **Verified Demonstration:** Full 16:9 master keyframe with preserved antique books, live hand posture, Hogwarts Slytherin uniform, and golden window rim lighting.

### 📦 Release Assets Included:
- `perfect_master_keyframe_025_card.jpg` — 4-panel comparison card demonstrating 1:1 match with original actor's tilt & smile.
- `master_keyframe_025_1080p.jpg` — Full 1080p master scene keyframe.
