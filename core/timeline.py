"""
Timeline Assembler for Multi-Shot Sequences
Stitches replaced actor shots and untouched camera footage seamlessly.
"""
import cv2
from typing import List, Dict, Any


def assemble_timeline(
    shot_definitions: List[Dict[str, Any]],
    output_path: str,
    fps: float = 24.0,
    resolution: tuple[int, int] = (1920, 1080),
) -> int:
    """
    Assembles a complete multi-shot movie timeline from arbitrary shot sources.

    Args:
        shot_definitions: List of dicts, each specifying:
            - 'video_path': path to shot video file
            - 'start_frame': int (inclusive)
            - 'end_frame': int (inclusive, or None for all remaining)
        output_path: Target video file path.
        fps: Target frame rate.
        resolution: Target (width, height).

    Returns:
        Total frames written.
    """
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    vw = cv2.VideoWriter(output_path, fourcc, fps, resolution)

    total_frames = 0
    for shot_idx, shot in enumerate(shot_definitions):
        path = shot["video_path"]
        start_f = shot.get("start_frame", 0)
        end_f = shot.get("end_frame", None)

        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Cannot open shot video: {path}")

        curr_f = 0
        shot_frames = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if curr_f >= start_f:
                if end_f is not None and curr_f > end_f:
                    break

                if (frame.shape[1], frame.shape[0]) != resolution:
                    frame = cv2.resize(frame, resolution)

                vw.write(frame)
                shot_frames += 1
                total_frames += 1

            curr_f += 1

        cap.release()
        print(f"Shot {shot_idx + 1} ({path}): appended {shot_frames} frames.")

    vw.release()
    print(f"Total timeline frames written: {total_frames} -> {output_path}")
    return total_frames
