"""
ComfyUI API Client for Automated Workflow Execution
"""
import json
import urllib.request
import urllib.error
import time
from typing import Any, Dict


class ComfyClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8188"):
        self.base_url = base_url.rstrip("/")

    def queue_prompt(self, workflow_prompt: Dict[str, Any]) -> str:
        """Queues a prompt workflow and returns the prompt_id."""
        url = f"{self.base_url}/prompt"
        payload = json.dumps({"prompt": workflow_prompt}).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res.get("prompt_id")
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            raise RuntimeError(f"ComfyUI HTTP {e.code}: {err_msg}") from e

    def wait_for_completion(
        self, prompt_id: str, poll_interval: float = 5.0, timeout: float = 1800.0
    ) -> Dict[str, Any]:
        """Polls ComfyUI history until the generation completes or times out."""
        start_time = time.time()
        history_url = f"{self.base_url}/history/{prompt_id}"

        print(f"Waiting for ComfyUI execution (prompt: {prompt_id})...")
        while time.time() - start_time < timeout:
            try:
                with urllib.request.urlopen(history_url) as resp:
                    history = json.loads(resp.read().decode("utf-8"))
                    if prompt_id in history:
                        elapsed = time.time() - start_time
                        print(f"Execution completed in {elapsed:.1f}s!")
                        return history[prompt_id]
            except Exception:
                pass

            elapsed = int(time.time() - start_time)
            print(f"[{elapsed}s] Processing in ComfyUI...")
            time.sleep(poll_interval)

        raise TimeoutError(f"ComfyUI execution exceeded timeout of {timeout}s.")
