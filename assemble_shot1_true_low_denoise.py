import cv2
import numpy as np
import subprocess
import glob
import os
import sys

def main():
    raw_mp4 = "/opt/comfyui/output/WanAnimate_Shot1_TrueLowDenoise_Raw832x480_00001.mp4"
    print(f"Opening raw diffusion output: {raw_mp4}")
    cap_diff = cv2.VideoCapture(raw_mp4)
    diff_frames = []
    while True:
        ret, frame = cap_diff.read()
        if not ret:
            break
        diff_frames.append(frame)
    cap_diff.release()
    print(f"Loaded {len(diff_frames)} diffusion frames.")

    orig_path = "/opt/comfyui/input/0048-0164.mp4"
    cap_orig = cv2.VideoCapture(orig_path)
    orig_frames = []
    while True:
        ret, frame = cap_orig.read()
        if not ret:
            break
        orig_frames.append(frame)
    cap_orig.release()
    print(f"Loaded {len(orig_frames)} original frames.")

    # Shot 1 coordinates: [160:640, 594:1426]
    crop_x1, crop_x2 = 594, 1426
    crop_y1, crop_y2 = 160, 640
    cw, ch = (crop_x2 - crop_x1), (crop_y2 - crop_y1)

    # 6-pixel soft edge feather for outer boundary of the 832x480 box against Hogwarts wall
    feather = np.ones((ch, cw), dtype=np.float32)
    border_px = 6
    for b in range(border_px):
        alpha = b / float(border_px)
        feather[b, :] = np.minimum(feather[b, :], alpha)
        feather[ch - 1 - b, :] = np.minimum(feather[ch - 1 - b, :], alpha)
        feather[:, b] = np.minimum(feather[:, b], alpha)
        feather[:, cw - 1 - b] = np.minimum(feather[:, cw - 1 - b], alpha)
    feather = feather[:, :, np.newaxis]

    # Composite Shot 1 (frames 000-045, 46 frames)
    shot1_composite_frames = []
    for i in range(46):
        orig_f = orig_frames[i].copy()
        diff_f = diff_frames[min(i, len(diff_frames) - 1)]
        diff_resized = cv2.resize(diff_f, (cw, ch), interpolation=cv2.INTER_LANCZOS4)
        
        orig_crop = orig_f[crop_y1:crop_y2, crop_x1:crop_x2].astype(np.float32)
        blended_crop = (diff_resized.astype(np.float32) * feather + 
                        orig_crop * (1.0 - feather))
        orig_f[crop_y1:crop_y2, crop_x1:crop_x2] = np.clip(blended_crop, 0, 255).astype(np.uint8)
        shot1_composite_frames.append(orig_f)

    # Load Shot 3 approved Alpha 2 frames
    shot3_path = "/opt/comfyui/input/WanAnimate_Shot3_Alpha2_1080p_h264.mp4"
    cap_s3 = cv2.VideoCapture(shot3_path)
    s3_frames = []
    while True:
        ret, frame = cap_s3.read()
        if not ret:
            break
        s3_frames.append(frame)
    cap_s3.release()
    print(f"Loaded {len(s3_frames)} Shot 3 Alpha 2 frames.")

    # Assemble full movie:
    # Shot 1: 000 to 045 (46 frames)
    # Shot 2: 046 to 081 (36 frames, 100% untouched original camera footage)
    # Shot 3: 082 to 116 (35 frames, approved Alpha 2 render)
    full_movie_frames = []
    full_movie_frames.extend(shot1_composite_frames)
    full_movie_frames.extend(orig_frames[46:82])
    full_movie_frames.extend(s3_frames[:35])

    print(f"Total movie frames: {len(full_movie_frames)} (Shot 1: {len(shot1_composite_frames)}, Shot 2: {len(orig_frames[46:82])}, Shot 3: {len(s3_frames[:35])})")

    # Write Shot 1 1080p raw
    shot1_raw_path = "/opt/comfyui/output/shot1_true_low_denoise_1080p_raw.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    vw1 = cv2.VideoWriter(shot1_raw_path, fourcc, 24.0, (1920, 1080))
    for f in shot1_composite_frames:
        vw1.write(f)
    vw1.release()

    # Write Full Movie raw
    full_raw_path = "/opt/comfyui/output/full_movie_true_low_denoise_raw.mp4"
    vw_full = cv2.VideoWriter(full_raw_path, fourcc, 24.0, (1920, 1080))
    for f in full_movie_frames:
        vw_full.write(f)
    vw_full.release()

    # Transcode Shot 1 to H.264
    shot1_final_mp4 = "/opt/comfyui/output/WanAnimate_Shot1_TrueLowDenoise_1080p_h264.mp4"
    cmd1 = [
        "ffmpeg", "-y", "-i", shot1_raw_path,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        "-movflags", "+faststart", shot1_final_mp4
    ]
    subprocess.run(cmd1, check=True)

    # Transcode Full Movie to H.264
    full_final_mp4 = "/opt/comfyui/output/WanAnimate_FullMovie_TrueLowDenoise_1080p_h264.mp4"
    cmd_full = [
        "ffmpeg", "-y", "-i", full_raw_path,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        "-movflags", "+faststart", full_final_mp4
    ]
    subprocess.run(cmd_full, check=True)
    print("Transcoding completed successfully!")

    # Generate 4-panel comparison card for frame 025
    # Panel 1: Original frame 025 (Actor)
    # Panel 2: Pre-blended frame 025 with bilateral filter cut line
    # Panel 3: Diffusion seam mask frame 025 (Face interior protected, seam diffused)
    # Panel 4: True Low-Denoise Diffusion Result frame 025 (Seamlessly integrated)
    f25_orig = orig_frames[25]
    f25_shot1 = shot1_composite_frames[25]
    
    # Load pre-blended frame 025
    cap_pb = cv2.VideoCapture("/opt/comfyui/input/shot1_crop_preblended_832x480.mp4")
    for _ in range(26):
        ret, f_pb = cap_pb.read()
    cap_pb.release()

    # Load diffusion seam mask frame 025
    cap_msk = cv2.VideoCapture("/opt/comfyui/input/shot1_crop_diffusion_seam_mask_832x480.mp4")
    for _ in range(26):
        ret, f_msk = cap_msk.read()
    cap_msk.release()

    # Focus crop around head and neck: y: 140 to 620 (height 480), x: 740 to 1280 (width 540)
    # In full frame coordinates:
    crop_head_orig = f25_orig[140:620, 740:1280]
    crop_head_final = f25_shot1[140:620, 740:1280]

    # Map pre-blended and mask to full frame crop coordinates
    # diff crop is at [y: 160:640, x: 594:1426]
    # So relative to diff crop: y is (140-160)=0:460, x is (740-594)=146 : (1280-594)=686
    # Let's place f_pb and f_msk in full frame coordinate system for exact pixel matching:
    full_pb = f25_orig.copy()
    full_pb[crop_y1:crop_y2, crop_x1:crop_x2] = f_pb
    crop_head_pb = full_pb[140:620, 740:1280]

    full_msk = np.zeros_like(f25_orig)
    full_msk[crop_y1:crop_y2, crop_x1:crop_x2] = f_msk
    crop_head_msk = full_msk[140:620, 740:1280]

    # Create 4-panel card (2x2 grid, each 540x480 -> 1080x960)
    def add_label(img, text, subtext=""):
        res = img.copy()
        overlay = res.copy()
        cv2.rectangle(overlay, (0, 0), (res.shape[1], 55), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.75, res, 0.25, 0, res)
        cv2.putText(res, text, (15, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        if subtext:
            cv2.putText(res, subtext, (15, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 220, 255), 1, cv2.LINE_AA)
        return res

    p1 = add_label(crop_head_orig, "1. Original Actor (Frame 025)", "12 deg tilt, closed smile, authentic books")
    p2 = add_label(crop_head_pb, "2. Previous Paste (Before Diffusion)", "Visible cut seam on neck & hair border")
    p3 = add_label(crop_head_msk, "3. Inverted Face-Oval Diffusion Mask", "Black = 0% noise (protected) | White = 0.28 denoise")
    p4 = add_label(crop_head_final, "4. True Low-Denoise Diffusion (Wan 2.1)", "Hair strands & collar physically fused into scene")

    top_row = np.hstack([p1, p2])
    bot_row = np.hstack([p3, p4])
    card = np.vstack([top_row, bot_row])

    card_path = "/opt/comfyui/output/shot1_true_low_denoise_comparison_card.jpg"
    cv2.imwrite(card_path, card)
    cv2.imwrite("/opt/comfyui/output/shot1_f025_true_low_denoise_closeup.jpg", crop_head_final)
    print("Saved comparison card and closeups to ComfyUI output!")

if __name__ == "__main__":
    main()
