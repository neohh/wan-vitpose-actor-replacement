"""
Masking Utilities for Character Replacement with Hair Preservation
"""
import cv2
import numpy as np


def generate_expanded_hair_mask(
    base_mask: np.ndarray,
    dilation_px: int = 35,
    clamp_y_bottom: int = None,
    clamp_y_top: int = None,
    feather_px: int = 15,
) -> np.ndarray:
    """
    Expands a character head/body mask to accommodate voluminous hairstyles
    (shaggy bob, curtain bangs, curls) while optionally clamping to protect
    props, hands, and authentic clothing.

    Args:
        base_mask: 2D uint8 mask (0 or 255) of shape (H, W).
        dilation_px: Morphological dilation radius in pixels.
        clamp_y_bottom: Y coordinate below which mask is zeroed (preserves books, hands).
        clamp_y_top: Optional top Y clamp.
        feather_px: Gaussian blur feather radius.

    Returns:
        Feathered float32 mask normalized to [0.0, 1.0].
    """
    m = base_mask.copy()
    if len(m.shape) == 3:
        m = cv2.cvtColor(m, cv2.COLOR_BGR2GRAY)

    _, m_bin = cv2.threshold(m, 127, 255, cv2.THRESH_BINARY)

    # Morphological dilation with elliptical kernel to naturally follow hair volume
    if dilation_px > 0:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (dilation_px, dilation_px)
        )
        m_dilated = cv2.dilate(m_bin, kernel, iterations=1)
    else:
        m_dilated = m_bin.copy()

    # Apply clamps to protect authentic scene elements (e.g. books, hands, desk)
    if clamp_y_bottom is not None and 0 <= clamp_y_bottom < m.shape[0]:
        m_dilated[clamp_y_bottom:, :] = 0
    if clamp_y_top is not None and 0 <= clamp_y_top < m.shape[0]:
        m_dilated[:clamp_y_top, :] = 0

    # Soft feathering on boundary
    if feather_px > 0:
        k_size = feather_px if feather_px % 2 == 1 else feather_px + 1
        m_smooth = cv2.GaussianBlur(
            m_dilated.astype(np.float32), (k_size, k_size), feather_px / 3.0
        )
    else:
        m_smooth = m_dilated.astype(np.float32)

    return np.clip(m_smooth / 255.0, 0.0, 1.0)


def create_inverted_face_oval_mask(
    mask: np.ndarray,
    radius_x: int = 50,
    radius_y: int = 70,
    tilt_angle_deg: float = -5.0,
    offset_y: int = 10,
    blur_kernel: int = 31,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Creates an inverted face oval mask where:
      - Face interior = 0.0 (Protected: keeps 100% razor-sharp AI generation detail)
      - Hair outer boundary & background = 1.0 (Allows low-denoise edge smoothing & background fusion)

    Args:
        mask: 2D float32 or uint8 mask to calculate head centroid.
        radius_x: Horizontal radius of face protection oval.
        radius_y: Vertical radius of face protection oval.
        tilt_angle_deg: Tilt angle of oval matching character pose.
        offset_y: Vertical shift from centroid towards nose/mouth.
        blur_kernel: Gaussian blur kernel size for smooth falloff.

    Returns:
        (inv_face_mask, face_oval) as float32 arrays in [0.0, 1.0].
    """
    h, w = mask.shape[:2]
    m_val = mask if mask.dtype == np.uint8 else (mask * 255).astype(np.uint8)

    ys, xs = np.where(m_val > 120)
    if len(ys) > 0:
        cy, cx = int(np.mean(ys)), int(np.mean(xs))
    else:
        cy, cx = h // 2, w // 2

    face_oval = np.zeros((h, w), dtype=np.float32)
    cv2.ellipse(
        face_oval,
        (cx, cy + offset_y),
        (radius_x, radius_y),
        tilt_angle_deg,
        0,
        360,
        1.0,
        -1,
    )

    k = blur_kernel if blur_kernel % 2 == 1 else blur_kernel + 1
    face_oval = cv2.GaussianBlur(face_oval, (k, k), k / 3.0)
    face_oval = np.clip(face_oval, 0.0, 1.0)

    inv_face_mask = 1.0 - face_oval
    return inv_face_mask, face_oval
