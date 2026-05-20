from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_ROOT / "pretrained_models" / "Fun-CosyVoice3-0.5B"
PROMPT_DIR = PROJECT_ROOT / "assets" / "prompts"
UPLOAD_DIR = PROJECT_ROOT / "uploads"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

MAX_PROMPT_SECONDS = 30
MIN_PROMPT_SECONDS = 3
PROMPT_SAMPLE_RATE = 16000
OUTPUT_SAMPLE_RATE = 24000

for directory in (UPLOAD_DIR, OUTPUT_DIR):
    directory.mkdir(parents=True, exist_ok=True)
