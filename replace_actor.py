#!/usr/bin/env python3
"""
Wan-ViTPose Actor Replacement Pipeline (CLI)

Replaces an actor/character in cinematic video with a target reference identity:
1. ViTPose wholebody skeleton tracking (anchors head tilt, scale, and body posture 1:1).
2. Expanded hair & anatomy masking (dilates mask to accommodate curls/shaggy hair, clamps bottom to preserve props).
3. Wan 2.1 Animate video diffusion inpainting.
4. Edge harmonization with an inverted face-oval mask (keeps face 100% sharp, smooths hair/collar boundary).
"""

import os
import sys
import json
import argparse
import cv2
import numpy as np

from core.masking import generate_expanded_hair_mask, create_inverted_face_oval_mask
from core.harmonize import harmonize_and_composite
from core.comfy_client import ComfyClient


def process_video_pipeline(
    input_video: str,
    raw_gen_video: str,
    mask_video: str,
    output_video: str,
    crop_box: tuple[int, int, int, int],
    clamp_bottom: int = None,
    dilation_px: int = 35,
    face_radius: tuple[int, int] = (50, 70),
    bilateral_sigma: float = 35.0,
):
    print("=" * 70)
    print("Wan-ViTPose Actor Replacement: Harmonization & Assembly Pass")
    print("=" * 70)

    # 1. Open video readers
    cap_orig = cv2.VideoCapture(input_video)
    cap_raw = cv2.VideoCapture(raw_gen_video)
    cap_mask = cv2.VideoCapture(mask_video)

    fps = cap_orig.get(cv2.CAP_PROP_FPS) or 24.0
    w_orig = int(cap_orig.get(cv2.CAP_PROP_FRAME_WIDTH))
    h_orig = int(cap_orig.get(cv2.CAP_PROP_FRAME_HEIGHT))
    n_raw = int(cap_raw.get(cv2.CAP_PROP_FRAME_COUNT))

    x1, y1, x2, y2 = crop_box
    w_crop, h_crop = x2 - x1, y2 - y1

    print(f"Input footage: {input_video} ({w_orig}x{h_orig} @ {fps} fps)")
    print(f"Generated crop: {raw_gen_video} ({w_crop}x{h_crop}, {n_raw} frames)")
    print(f"Crop box: x=[{x1}:{x2}], y=[{y1}:{y2}]")
    if clamp_bottom is not None:
        print(f"Prop protection clamp: below y={clamp_bottom} in crop")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    vw = cv2.VideoWriter(output_video, fourcc, fps, (w_orig, h_orig))

    frame_idx = 0
    while True:
        ret_orig, f_orig = cap_orig.read()
        ret_raw, f_raw = cap_raw.read()
        ret_m, f_mask = cap_mask.read()

        if not ret_orig or not ret_raw or not ret_m:
            break

        # Extract & prepare mask
        m_2d = f_mask[:, :, 0]
        # Expand hair mask if not already expanded
        m_float = generate_expanded_hair_mask(
            m_2d, dilation_px=dilation_px, clamp_y_bottom=clamp_bottom, feather_px=15
        )

        # Build inverted face oval protection mask
        inv_face_mask, _ = create_inverted_face_oval_mask(
            m_float, radius_x=face_radius[0], radius_y=face_radius[1], offset_y=10
        )

        # Harmonize and composite back into original frame
        f_out = harmonize_and_composite(
            frame_orig=f_orig,
            frame_gen_crop=f_raw,
            mask_crop=m_float,
            crop_box=crop_box,
            inv_face_mask=inv_face_mask,
            bilateral_d=9,
            bilateral_sigma_color=bilateral_sigma,
            bilateral_sigma_space=bilateral_sigma,
        )

        vw.write(f_out)
        frame_idx += 1
        if frame_idx % 10 == 0 or frame_idx == n_raw:
            print(f"  Processed frame {frame_idx}/{n_raw}...")

    cap_orig.release()
    cap_raw.release()
    cap_mask.release()
    vw.release()

    print(f"Successfully rendered {frame_idx} frames to {output_video}!")


def main():
    parser = argparse.ArgumentParser(
        description="Wan-ViTPose Actor Replacement Pipeline"
    )
    parser.add_argument(
        "--input", required=True, help="Path to original source video"
    )
    parser.add_argument(
        "--raw-gen",
        required=True,
        help="Path to raw Wan 2.1 generated crop video (e.g. from ComfyUI)",
    )
    parser.add_argument(
        "--mask",
        required=True,
        help="Path to actor head/body mask video in crop space",
    )
    parser.add_argument(
        "--output", required=True, help="Target output video path (1080p)"
    )
    parser.add_argument(
        "--crop-box",
        nargs=4,
        type=int,
        required=True,
        metavar=("X1", "Y1", "X2", "Y2"),
        help="Bounding coordinates of crop in source footage: x1 y1 x2 y2",
    )
    parser.add_argument(
        "--clamp-bottom",
        type=int,
        default=None,
        help="Y coordinate inside crop to clamp mask (preserves held books, hands, props)",
    )
    parser.add_argument(
        "--hair-dilate",
        type=int,
        default=35,
        help="Hair expansion dilation radius (default: 35)",
    )
    parser.add_argument(
        "--face-rx",
        type=int,
        default=50,
        help="Horizontal face protection radius (default: 50)",
    )
    parser.add_argument(
        "--face-ry",
        type=int,
        default=70,
        help="Vertical face protection radius (default: 70)",
    )

    args = parser.parse_args()

    process_video_pipeline(
        input_video=args.input,
        raw_gen_video=args.raw_gen,
        mask_video=args.mask,
        output_video=args.output,
        crop_box=tuple(args.crop_box),
        clamp_bottom=args.clamp_bottom,
        dilation_px=args.hair_dilate,
        face_radius=(args.face_rx, args.face_ry),
    )


if __name__ == "__main__":
    main()
