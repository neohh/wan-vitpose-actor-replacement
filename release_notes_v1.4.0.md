# Release v1.4.0 — User Face+Hair Rect Wipe (Working Norm)

## Status
**Norm / working release.** Validated on Shot 1 with a short-hair glasses ref: shoulder-length ghost hair from the original plate is gone when the wipe rect fully covers the painted face+hair mask.

## What this fixes
Tight hair masks (and earlier rects truncated above the books) leave original curls on the shoulders outside the wipe. Those pixels never enter Wan Animate, so they stay forever.

**v1.4 recipe:** paint (or reuse) a face+hair mask → build a **padded AABB rect** from its widest points → temporal max-envelope → feed that rect as the Wan Animate wipe mask. No Y-cap above the shoulders.

## Deliverables
- `WanAnimate_Shot1_RefGlasses_UserRect_API.json` — ComfyUI API graph (ref + rect mask slots filled for the glasses test; swap slots for other faces).
- `build_user_facehair_rect_mask.py` — builds `shot1_crop_user_facehair_rect_mask_832x480.mp4` from a full-plate face+hair mask video.
- Defaults: crop `x 594:1426, y 160:640` (832×480 Shot 1 window), pad 32/24, envelope ±2 frames, snap to 8px. Asserts `max_outside == 0`.

## What is automatic vs not
| Automatic | You still provide |
|---|---|
| BBox + pad + temporal envelope from your mask | Face+hair mask video for **this** plate |
| Wan pose tracking on the driver | Face/identity ref image |
| Same JSON graph for other refs (swap image + prompts) | Crop window if the shot/framing changes |

Different faces: yes — swap the ref image (and prompts). Different scenes: yes for the graph, but the **mask must match that driver**, and `--crop` must match that shot’s Wan window (Shot 1 defaults are not universal).

## Quick use
```bash
python build_user_facehair_rect_mask.py "path/to/face_hair_mask.mp4" \
  -o shot1_crop_user_facehair_rect_mask_832x480.mp4

# Then load WanAnimate_Shot1_RefGlasses_UserRect_API.json in ComfyUI,
# set LoadImage → your ref, VHS mask → the rect mp4, queue.
```
