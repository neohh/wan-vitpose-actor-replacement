import json
import urllib.request
import urllib.parse
import time
import os
import sys

def queue_prompt(prompt_workflow):
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data, headers={'Content-Type': 'application/json'})
    try:
        response = urllib.request.urlopen(req)
        res_data = json.loads(response.read().decode('utf-8'))
        return res_data
    except urllib.error.HTTPError as e:
        print("HTTPError:", e.code, e.read().decode('utf-8'))
        raise e

def check_history(prompt_id):
    url = f"http://127.0.0.1:8188/history/{prompt_id}"
    try:
        req = urllib.request.Request(url)
        res = urllib.request.urlopen(req)
        return json.loads(res.read().decode('utf-8'))
    except Exception as e:
        return {}

def main():
    base_api = r"Z:\Work\Scripts and Addons\AI_Mask\WanAnimate_Shot1_TrueSeam_NeckCollar_Polish_API.json"
    with open(base_api, "r", encoding="utf-8") as f:
        api = json.load(f)

    # 1. Video input: Pre-blended master composite (Option 2 head + 1:1 original body & books)
    api["1"]["inputs"]["video"] = "shot1_crop_preblended_832x480.mp4"

    # 2. Mask video: Inverted face-oval diffusion seam mask (face interior protected at 0, boundary exposed at 1.0)
    api["2"]["inputs"]["video"] = "shot1_crop_diffusion_seam_mask_832x480.mp4"

    # 6. Reference image: Master face ref clean 512
    api["6"]["inputs"]["image"] = "master_face_ref_clean_512.png"

    # 18. Cached prompt
    api["18"]["inputs"]["positive_prompt"] = (
        "A young woman with a layered dark brown wavy shaggy bob haircut, textured feathered bangs, curtain bangs, "
        "soft hooded hazel eyes, subtle closed-mouth smile, lifting lip corners, gentle expression, straight slender nose, "
        "natural pale closed lips, porcelain skin, wearing a dark green Hogwarts uniform, crisp white collared shirt, "
        "striped tie, warm candlelight Hogwarts hallway. Cinematic film still, photorealistic."
    )
    api["18"]["inputs"]["negative_prompt"] = (
        "blonde hair, blonde eyebrows, light hair, long hair, open mouth, parted lips, showing teeth, talking, speaking, "
        "laughing, grinning, smiling wide, oversaturated, orange skin, deep nasolabial folds, red lipstick, makeup, "
        "neon glow, blown out white highlights, doll, plastic skin, airbrushed, round chubby face, cartoon, blurry, "
        "low quality, artifacts, distorted proportions, alien eyes, deformed skull, seams, harsh border, bad blending"
    )

    # 19. WanVideoSampler: denoise_strength = 0.28, steps = 12, add_noise_to_samples = True
    api["19"]["inputs"]["denoise_strength"] = 0.28
    api["19"]["inputs"]["steps"] = 12
    api["19"]["inputs"]["add_noise_to_samples"] = True
    api["19"]["inputs"]["seed"] = 105

    # 21. VHS_VideoCombine filename prefix
    api["21"]["inputs"]["filename_prefix"] = "WanAnimate_Shot1_TrueLowDenoise_Raw832x480"

    out_json = r"Z:\Work\Scripts and Addons\AI_Mask\WanAnimate_Shot1_TrueLowDenoise_API.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(api, f, indent=2, ensure_ascii=False)
    print("Saved workflow to:", out_json)

    # Queue to ComfyUI
    print("Submitting prompt to ComfyUI...")
    res = queue_prompt(api)
    prompt_id = res.get("prompt_id")
    print(f"Queued successfully! Prompt ID: {prompt_id}")

    # Wait for completion
    print("Waiting for Wan 2.1 low-denoise diffusion pass to complete...")
    start_time = time.time()
    while True:
        history = check_history(prompt_id)
        if prompt_id in history:
            print(f"Generation completed in {time.time() - start_time:.1f} seconds!")
            outputs = history[prompt_id].get("outputs", {})
            for node_id, out in outputs.items():
                print(f"Node {node_id} outputs:", out)
            break
        
        # Check queue status
        try:
            req = urllib.request.Request("http://127.0.0.1:8188/queue")
            q_res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
            executing = q_res.get("queue_running", [])
            pending = q_res.get("queue_pending", [])
            print(f"[{time.time() - start_time:4.0f}s] Running: {len(executing)}, Pending: {len(pending)}")
        except Exception:
            pass

        time.sleep(5)

if __name__ == "__main__":
    main()
