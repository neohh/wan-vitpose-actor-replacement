"""
Harmonization and Compositing Pipeline
Seamlessly blends AI-generated actor crop back into master cinematic footage.
"""
import cv2
import numpy as np


def color_match_background(
    crop_generated: np.ndarray,
    crop_original: np.ndarray,
    mask: np.ndarray,
    bg_threshold: float = 0.1,
) -> np.ndarray:
    """
    Matches color distribution (mean and standard deviation per channel)
    between generated crop and original footage in background regions.
    """
    gen = crop_generated.copy().astype(np.float32)
    orig = crop_original.astype(np.float32)

    bg_valid = mask < bg_threshold
    if np.sum(bg_valid) < 50:
        return crop_generated

    for c in range(3):
        mo = np.mean(orig[:, :, c][bg_valid])
        so = np.std(orig[:, :, c][bg_valid]) + 1e-5
        mr = np.mean(gen[:, :, c][bg_valid])
        sr = np.std(gen[:, :, c][bg_valid]) + 1e-5

        gen[:, :, c] = np.clip((gen[:, :, c] - mr) * (so / sr) + mo, 0.0, 255.0)

    return gen.astype(np.uint8)


def harmonize_and_composite(
    frame_orig: np.ndarray,
    frame_gen_crop: np.ndarray,
    mask_crop: np.ndarray,
    crop_box: tuple[int, int, int, int],
    inv_face_mask: np.ndarray = None,
    bilateral_d: int = 9,
    bilateral_sigma_color: float = 35.0,
    bilateral_sigma_space: float = 35.0,
) -> np.ndarray:
    """
    Composites the generated character crop back into the full frame with
    color-matching, soft alpha blending, and an edge-denoise pass protecting
    the face interior.

    Args:
        frame_orig: Full resolution original frame (e.g. 1920x1080).
        frame_gen_crop: Generated character crop (e.g. 832x480).
        mask_crop: 2D float32 mask [0.0, 1.0] in crop space.
        crop_box: (x1, y1, x2, y2) coordinates of the crop within frame_orig.
        inv_face_mask: 2D float32 [0.0, 1.0] protecting face (0=face, 1=perimeter).
        bilateral_d: Diameter of each pixel neighborhood for edge filter.
        bilateral_sigma_color: Filter sigma in the color space.
        bilateral_sigma_space: Filter sigma in the coordinate space.

    Returns:
        Full resolution frame with harmonized character replacement.
    """
    x1, y1, x2, y2 = crop_box
    orig_crop = frame_orig[y1:y2, x1:x2].copy()

    # 1. Color match background in crop
    gen_matched = color_match_background(frame_gen_crop, orig_crop, mask_crop)

    # 2. Base alpha blend
    m3 = np.repeat(mask_crop[:, :, np.newaxis], 3, axis=2)
    blended_crop = (
        gen_matched.astype(np.float32) * m3 + orig_crop.astype(np.float32) * (1.0 - m3)
    ).astype(np.uint8)

    # 3. Low-denoise edge pass with face protection
    if inv_face_mask is not None:
        smooth_crop = cv2.bilateralFilter(
            blended_crop, bilateral_d, bilateral_sigma_color, bilateral_sigma_space
        )
        inv_m3 = np.repeat(inv_face_mask[:, :, np.newaxis], 3, axis=2)

        # Apply smoothing ONLY on boundary (inv_face_mask * mask_crop)
        # Face interior (where inv_m3 == 0) remains 100% sharp
        weight_smooth = inv_m3 * m3
        final_crop = (
            smooth_crop.astype(np.float32) * weight_smooth
            + blended_crop.astype(np.float32) * (1.0 - weight_smooth)
        ).astype(np.uint8)
    else:
        final_crop = blended_crop

    # 4. Insert back into full frame
    frame_out = frame_orig.copy()
    frame_out[y1:y2, x1:x2] = final_crop
    return frame_out
