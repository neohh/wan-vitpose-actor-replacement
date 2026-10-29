#!/usr/bin/env python3
"""Build a padded axis-aligned rect wipe-mask from a user face+hair mask video.

Takes a B/W (or near-B/W) mask of face+hair — typically painted on the full
1080p plate — crops the Wan Animate window, expands each frame's bbox with
padding + a temporal max-envelope, and writes an 832x480 rect mask MP4.

This is the v1.4 recipe: wipe the entire original hair silhouette so a shorter
ref haircut does not leave shoulder-length ghosts outside a tight hair mask.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def snap8(v: float, mx: int) -> int:
    return max(0, min(mx, (int(round(v)) // 8) * 8))


def build_rect_mask(
    src_mask: Path,
    out_rect: Path,
    *,
    crop: tuple[int, int, int, int] = (594, 1426, 160, 640),
    frames: int = 49,
    pad_x: int = 32,
    pad_y: int = 24,
    envelope: int = 2,
    fps: float = 24.0,
    out_crop_mask: Path | None = None,
) -> dict:
    x1, x2, y1, y2 = crop
    tw, th = x2 - x1, y2 - y1
    assert (tw, th) == (832, 480), f"expected 832x480 crop, got {tw}x{th}"

    cap = cv2.VideoCapture(str(src_mask))
    if not cap.isOpened():
        raise SystemExit(f"cannot open mask: {src_mask}")

    boxes: list[list[int] | None] = []
    crops: list[np.ndarray] = []
    wr_c = None
    if out_crop_mask is not None:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        wr_c = cv2.VideoWriter(str(out_crop_mask), fourcc, fps, (tw, th), False)

    for _ in range(frames):
        ok, fr = cap.read()
        if not ok:
            break
        m = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY) if fr.ndim == 3 else fr
        m = m[y1:y2, x1:x2]
        if m.shape != (th, tw):
            m = cv2.resize(m, (tw, th), interpolation=cv2.INTER_NEAREST)
        crops.append(m)
        if wr_c is not None:
            wr_c.write(m)
        ys, xs = np.where(m > 127)
        if len(xs) == 0:
            boxes.append(None)
            continue
        boxes.append(
            [
                max(0, int(xs.min()) - pad_x),
                max(0, int(ys.min()) - pad_y),
                min(tw, int(xs.max()) + pad_x + 1),
                min(th, int(ys.max()) + pad_y + 1),
            ]
        )
    cap.release()
    if wr_c is not None:
        wr_c.release()

    if not boxes:
        raise SystemExit("no frames read from mask video")

    last = None
    for i, b in enumerate(boxes):
        if b is None and last is not None:
            boxes[i] = last[:]
        elif b is not None:
            last = b[:]
    for i in range(len(boxes)):
        if boxes[i] is None:
            for j in range(i + 1, len(boxes)):
                if boxes[j] is not None:
                    boxes[i] = boxes[j][:]
                    break
    if any(b is None for b in boxes):
        raise SystemExit("mask has empty frames with no neighbors to fill")

    arr = np.array(boxes, dtype=np.float32)
    env = arr.copy()
    for i in range(len(arr)):
        a = max(0, i - envelope)
        b = min(len(arr), i + envelope + 1)
        env[i, 0] = arr[a:b, 0].min()
        env[i, 1] = arr[a:b, 1].min()
        env[i, 2] = arr[a:b, 2].max()
        env[i, 3] = arr[a:b, 3].max()

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    wr = cv2.VideoWriter(str(out_rect), fourcc, fps, (tw, th), False)
    outs = []
    areas = []
    for i in range(len(env)):
        x0, y0, x1b, y1b = [snap8(v, lim) for v, lim in zip(env[i], [tw, th, tw, th])]
        rx0, ry0, rx1, ry1 = boxes[i]
        x0 = min(x0, snap8(rx0, tw))
        y0 = min(y0, snap8(ry0, th))
        x1b = max(x1b, min(tw, ((rx1 + 7) // 8) * 8))
        y1b = max(y1b, min(th, ((ry1 + 7) // 8) * 8))
        if x1b <= x0:
            x1b = min(tw, x0 + 8)
        if y1b <= y0:
            y1b = min(th, y0 + 8)
        rect = np.zeros((th, tw), np.uint8)
        rect[y0:y1b, x0:x1b] = 255
        wr.write(rect)
        areas.append((x1b - x0) * (y1b - y0))
        outs.append(int(((crops[i] > 127) & (rect == 0)).sum()))
    wr.release()

    stats = {
        "frames": len(env),
        "mean_frac": float(np.mean(areas)) / (tw * th),
        "max_outside": int(max(outs)),
        "sum_outside": int(sum(outs)),
        "out_rect": str(out_rect),
    }
    return stats


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("src_mask", type=Path, help="Full-plate face+hair mask video (e.g. 1920x1080)")
    p.add_argument(
        "-o",
        "--out-rect",
        type=Path,
        default=Path("shot1_crop_user_facehair_rect_mask_832x480.mp4"),
    )
    p.add_argument("--out-crop-mask", type=Path, default=None)
    p.add_argument("--crop", type=int, nargs=4, metavar=("X1", "X2", "Y1", "Y2"), default=[594, 1426, 160, 640])
    p.add_argument("--frames", type=int, default=49)
    p.add_argument("--pad-x", type=int, default=32)
    p.add_argument("--pad-y", type=int, default=24)
    p.add_argument("--envelope", type=int, default=2)
    args = p.parse_args()

    stats = build_rect_mask(
        args.src_mask,
        args.out_rect,
        crop=tuple(args.crop),
        frames=args.frames,
        pad_x=args.pad_x,
        pad_y=args.pad_y,
        envelope=args.envelope,
        out_crop_mask=args.out_crop_mask,
    )
    print(stats)
    if stats["max_outside"] != 0:
        raise SystemExit("rect does not fully cover source mask — increase pad or check crop")


if __name__ == "__main__":
    main()
