# Voice Clone

This project is an independent FastAPI and browser frontend demo built from the useful CosyVoice runtime, model, and assets that were migrated into this directory.

## Features

- Voice synthesis with several built-in reference voices.
- Custom speech text with optional fixed demo sentences for quick filling.
- Emotion and speed control on the main synthesis page.
- Voice cloning from uploaded or recorded prompt audio.
- Left-navigation browser workspace.

## Model Note

The local model is `pretrained_models/Fun-CosyVoice3-0.5B`.

CosyVoice3 does not expose the older SFT speaker list such as `中文男` or `中文女`, so this project implements fixed voices with local prompt audio presets and CosyVoice3 zero-shot/instruct inference.

## Run

Run from this directory:

```bash
conda activate cosyvoice
pip install -r requirements.txt
uvicorn backend.main:app --host 127.0.0.1 --port 8010
```

Open:

```text
http://127.0.0.1:8010
```

## Audio Input

For voice cloning, prompt audio should be 3 to 30 seconds long. The backend sends every uploaded prompt file through `ffmpeg`, so any format that `ffmpeg` can decode is automatically converted to mono 16 kHz WAV before CosyVoice receives it. If `ffmpeg` cannot decode the file, the API returns a format-incompatible or damaged-file error. The prompt transcript is optional: when provided, the backend uses zero-shot synthesis; when left empty, it uses cross-lingual cloning from the audio only.

## Convenience Script

From the project root:

```bash
./scripts/run_server.sh
```

The script uses the existing `cosyvoice` conda environment when `conda` is available.

## Project Layout

- `backend/`: FastAPI routes, model service, presets, audio preprocessing.
- `frontend/`: static left-navigation workspace UI.
- `cosyvoice/`: migrated CosyVoice runtime package.
- `third_party/Matcha-TTS/`: required CosyVoice dependency.
- `pretrained_models/Fun-CosyVoice3-0.5B/`: local CosyVoice3 model.
- `assets/prompts/`: built-in prompt audio used as fixed voices.
- `uploads/`: normalized user prompt audio.
- `outputs/`: generated WAV files.

## Storage Note

The project is intended to own the migrated model and runtime files directly. Avoid copying the model again; use `mv` when moving assets into this project.
