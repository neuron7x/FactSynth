"""Minimal Python SDK example."""

import os
import requests  # type: ignore[import-untyped]

API = os.getenv("FACTSYNTH_API", "http://localhost:8000")

def generate(prompt: str, max_tokens: int = 128):
    r = requests.post(f"{API}/v1/generate", json={"prompt": prompt, "max_tokens": max_tokens}, timeout=60)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    print(generate("hello world"))
