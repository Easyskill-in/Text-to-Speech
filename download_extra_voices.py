from huggingface_hub import hf_hub_download
import os

models_dir = "models"

voice_downloads = [
    ("en/en_US/lessac/low", "en_US-lessac-low"),
    ("en/en_US/lessac/high", "en_US-lessac-high"),
    ("en/en_US/amy/medium", "en_US-amy-medium"),
    ("en/en_US/libritts_r/medium", "en_US-libritts_r-medium"),
    ("hi/hi_IN/priyamvada/medium", "hi_IN-priyamvada-medium"),
]

for path_prefix, voice_name in voice_downloads:
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

print("\nAll downloads complete!")
