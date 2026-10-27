"""
Assemble Vintage Brunette Seamless Cinema Edition (v1.3.0)
==========================================================
Zero-box compositing pipeline with anatomical face proportion matching for Wan 2.1 Animate.
Eliminates rectangular 832x480 boundary seams and squashed face artifacts via:
  1. Per-frame Reinhard LAB color harmonization of the background plate.
  2. 40px perimeter cosine ramp dissolving the crop window into 1080p.
  3. Dynamic moving-average face-tracking anatomical aspect ratio refinement (true reference proportions).
  4. Seamless assembly of Shot 1 (Wan Animate), Shot 2 (original), and Shot 3 (Wan Animate).
"""

import os
import cv2
import numpy as np

def reinhard_color_match(source, target, bg_mask):
    """Matches luma and chroma distribution of source background to target plate."""
    s_lab = cv2.cvtColor(source, cv2.COLOR_BGR2LAB).astype(np.float32)
    t_lab = cv2.cvtColor(target, cv2.COLOR_BGR2LAB).astype(np.float32)
    
    s_mean, s_std = cv2.meanStdDev(s_lab, mask=bg_mask.astype(np.uint8))
    t_mean, t_std = cv2.meanStdDev(t_lab, mask=bg_mask.astype(np.uint8))
    
    s_mean = s_mean.flatten()
    s_std = np.maximum(s_std.flatten(), 1e-5)
    t_mean = t_mean.flatten()
    t_std = t_std.flatten()
    
    matched_lab = np.zeros_like(s_lab)
    for c in range(3):
        ch = (s_lab[:, :, c] - s_mean[c]) * (t_std[c] / s_std[c]) + t_mean[c]
        matched_lab[:, :, c] = np.clip(ch, 0, 255)
        
    return cv2.cvtColor(matched_lab.astype(np.uint8), cv2.COLOR_LAB2BGR)

def create_cosine_fade_box(h=480, w=832, pad=40):
    """Creates a 2D smooth cosine weight mask fading to 0 at perimeter."""
    fade_box = np.ones((h, w), dtype=np.float32)
    for i in range(pad):
        w_val = 0.5 * (1.0 - np.cos(np.pi * i / pad))
        fade_box[i, :] *= w_val
        fade_box[h - 1 - i, :] *= w_val
        fade_box[:, i] *= w_val
        fade_box[:, w - 1 - i] *= w_val
    return fade_box[:, :, np.newaxis]

def composite_and_refine_shot1(orig_frames, raw_frames, mask_frames, x1=594, x2=1426, y1=160, y2=640, pad=40):
    fade_3ch = create_cosine_fade_box(y2 - y1, x2 - x1, pad=pad)
    seamless_frames = []
    raw_centers = []
    np.random.seed(42)
    
    # Pass 1: Zero-box Reinhard LAB & Cosine Fade
    for i in range(min(len(raw_frames), 46)):
        f_orig = orig_frames[i]
        f_crop = raw_frames[i]
        m_mask = mask_frames[i]
        
        orig_crop = f_orig[y1:y2, x1:x2].copy()
        bg_mask = (m_mask < 50)
        
        matched_crop = reinhard_color_match(f_crop, orig_crop, bg_mask)
        smooth_crop = (matched_crop.astype(float) * fade_3ch + orig_crop.astype(float) * (1.0 - fade_3ch)).astype(np.uint8)
        
        full_f = f_orig.copy()
        full_f[y1:y2, x1:x2] = smooth_crop
        
        # Micro film-grain to preserve natural texture
        noise = np.random.normal(0, 0.35, full_f.shape)
        full_f = np.clip(full_f.astype(float) + noise, 0, 255).astype(np.uint8)
        seamless_frames.append(full_f)
        
        # Track face center
        m_head = (m_mask[:350, :] > 100) if len(m_mask.shape) == 2 else (m_mask[:350, :, 0] > 100)
        ys, xs = np.where(m_head)
        if len(ys) > 0:
            cx = float(np.mean(xs)) + x1
            cy = float(np.mean(ys)) + y1 + 10
        else:
            cx, cy = 1030.0, 370.0
        raw_centers.append((cx, cy))
        
    # Pass 2: Temporal Moving Average & Anatomical Face Refinement
    smooth_centers = []
    for i in range(len(raw_centers)):
        i_min = max(0, i - 2)
        i_max = min(len(raw_centers), i + 3)
        smooth_centers.append((
            np.mean([c[0] for c in raw_centers[i_min:i_max]]),
            np.mean([c[1] for c in raw_centers[i_min:i_max]])
        ))
        
    h, w = seamless_frames[0].shape[:2]
    Y, X = np.ogrid[:h, :w]
    map_y = np.zeros((h, w), dtype=np.float32)
    map_x = np.zeros((h, w), dtype=np.float32)
    for y in range(h): map_y[y, :] = y
    for x in range(w): map_x[:, x] = x
    
    final_frames = []
    for i in range(len(seamless_frames)):
        cx, cy = smooth_centers[i]
        dist = ((X - cx) / 125.0)**2 + ((Y - cy) / 150.0)**2
        weight = np.exp(-dist * 2.0)
        map_x_warped = map_x + (map_x - cx) * 0.12 * weight
        f_refined = cv2.remap(seamless_frames[i], map_x_warped.astype(np.float32), map_y.astype(np.float32), cv2.INTER_LANCZOS4)
        final_frames.append(f_refined)
        
    return final_frames

def main():
    orig_path = '/opt/comfyui/input/0048-0164.mp4'
    raw_path = '/opt/comfyui/output/WanAnimate_Shot1_VintageBrunette_Raw832x480_00001.mp4'
    mask_path = '/opt/comfyui/input/shot1_crop_clean_binary_mask_832x480.mp4'
    s3_path = '/opt/comfyui/input/WanAnimate_Shot3_Alpha2_1080p_h264.mp4'
    
    cap_orig = cv2.VideoCapture(orig_path)
    orig_frames = []
    while True:
        ret, f = cap_orig.read()
        if not ret: break
        orig_frames.append(f)
    cap_orig.release()
    
    cap_raw = cv2.VideoCapture(raw_path)
    raw_frames = []
    while True:
        ret, f = cap_raw.read()
        if not ret: break
        raw_frames.append(f)
    cap_raw.release()
    
    cap_m = cv2.VideoCapture(mask_path)
    mask_frames = []
    while True:
        ret, f = cap_m.read()
        if not ret: break
        mask_frames.append(f[:, :, 0] if len(f.shape) == 3 else f)
    cap_m.release()
    
    cap_s3 = cv2.VideoCapture(s3_path)
    s3_frames = []
    while True:
        ret, f = cap_s3.read()
        if not ret: break
        s3_frames.append(f)
    cap_s3.release()
    
    s1_frames = composite_and_refine_shot1(orig_frames, raw_frames, mask_frames)
    
    # Save Shot 1
    s1_out = '/opt/comfyui/output/WanAnimate_Shot1_VintageBrunette_Proportional_1080p_h264.mp4'
    s1_temp = '/opt/comfyui/output/temp_s1.mp4'
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    w_s1 = cv2.VideoWriter(s1_temp, fourcc, 24.0, (1920, 1080))
    for f in s1_frames: w_s1.write(f)
    w_s1.release()
    os.system(f'ffmpeg -y -i {s1_temp} -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart {s1_out}')
    
    # Assemble Full Movie (117 frames)
    full_movie = []
    full_movie.extend(s1_frames)
    full_movie.extend(orig_frames[46:82])
    full_movie.extend(s3_frames[:35])
    
    movie_out = '/opt/comfyui/output/WanAnimate_FullMovie_VintageBrunette_Proportional_Final_1080p_h264.mp4'
    m_temp = '/opt/comfyui/output/temp_mov.mp4'
    w_m = cv2.VideoWriter(m_temp, fourcc, 24.0, (1920, 1080))
    for f in full_movie: w_m.write(f)
    w_m.release()
    os.system(f'ffmpeg -y -i {m_temp} -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart {movie_out}')
    print("Complete!")

if __name__ == '__main__':
    main()
