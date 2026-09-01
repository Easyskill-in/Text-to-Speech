"""Download essential voice models for first-time setup."""
from huggingface_hub import hf_hub_download
import os

models_dir = "models"

essential_voices = [
    ("en/en_US/lessac/medium", "en_US-lessac-medium"),
    ("hi/hi_IN/pratham/medium", "hi_IN-pratham-medium"),
]

for path_prefix, voice_name in essential_voices:
    parts = path_prefix.split("/")
    target_dir = os.path.join(models_dir, *parts)
    os.makedirs(target_dir, exist_ok=True)

    model_file = os.path.join(target_dir, f"{voice_name}.onnx")
    if os.path.exists(model_file):
        print(f"Already exists: {voice_name}")
        continue

    print(f"Downloading {voice_name}...")
    try:
        hf_hub_download(
            repo_id="rhasspy/piper-voices",
            filename=f"{path_prefix}/{voice_name}.onnx",
            local_dir=models_dir,
        )
        hf_hub_download(
            repo_id="rhasspy/piper-voices",
            filename=f"{path_prefix}/{voice_name}.onnx.json",
            local_dir=models_dir,
        )
        print(f"  Done!")
    except Exception as e:
        print(f"  Error: {e}")

print("\nEssential models downloaded!")
