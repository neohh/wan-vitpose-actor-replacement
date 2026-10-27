#!/usr/bin/env python3
"""
Queue Wan 2.1 Animate Job via ComfyUI API
"""
import sys
import os
import json
import argparse
from core.comfy_client import ComfyClient


def queue_wan_job(
    workflow_template: str,
    crop_video: str,
    mask_video: str,
    ref_image: str,
    prompt_text: str,
    output_prefix: str = "WanAnimate_ActorSwap",
    comfy_url: str = "http://127.0.0.1:8188",
):
    with open(workflow_template, "r", encoding="utf-8") as f:
        wf = json.load(f)

    # Inject dynamic inputs into standard node classes
    for node_id, node in wf.items():
        c_type = node.get("class_type")
        inputs = node.get("inputs", {})

        if c_type == "VHS_LoadVideo":
            # Match crop or mask loader by filename or node position
            if "crop" in str(inputs.get("video", "")).lower():
                inputs["video"] = crop_video
            elif "mask" in str(inputs.get("video", "")).lower():
                inputs["video"] = mask_video

        elif c_type == "LoadImage":
            inputs["image"] = ref_image

        elif c_type == "CLIPTextEncode" and prompt_text:
            inputs["text"] = prompt_text

        elif c_type == "VHS_VideoCombine":
            inputs["filename_prefix"] = output_prefix

    client = ComfyClient(base_url=comfy_url)
    print(f"Queuing Wan 2.1 Animate job to ComfyUI at {comfy_url}...")
    prompt_id = client.queue_prompt(wf)
    print(f"Workflow queued successfully! Prompt ID: {prompt_id}")
    history = client.wait_for_completion(prompt_id)
    print("Done! Outputs:", history.get("outputs", {}))
    return history


def main():
    parser = argparse.ArgumentParser(
        description="Queue Wan 2.1 Animate job with ViTPose skeleton"
    )
    parser.add_argument(
        "--workflow",
        default="workflows/wan_vitpose_animate_api.json",
        help="Path to ComfyUI workflow JSON",
    )
    parser.add_argument(
        "--crop", required=True, help="Input cropped video filename"
    )
    parser.add_argument(
        "--mask", required=True, help="Input expanded mask video filename"
    )
    parser.add_argument(
        "--ref", required=True, help="Character reference image filename"
    )
    parser.add_argument(
        "--prompt",
        default="cinematic footage of a young woman, natural expression, highly detailed",
        help="Text prompt",
    )
    parser.add_argument(
        "--url", default="http://127.0.0.1:8188", help="ComfyUI URL"
    )

    args = parser.parse_args()
    queue_wan_job(
        args.workflow, args.crop, args.mask, args.ref, args.prompt, comfy_url=args.url
    )


if __name__ == "__main__":
    main()
