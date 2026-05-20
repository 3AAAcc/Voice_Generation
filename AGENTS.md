# Voice_clone Project Notes

## Purpose

This directory contains the independent voice synthesis and voice cloning project migrated from `../CosyVoice-main`.

The required system features are:

- voice synthesis with several selectable built-in voices,
- custom speech text plus fixed sentences for quick filling,
- emotion and speed control on the main synthesis page,
- voice cloning from uploaded or recorded prompt audio,
- browser frontend with Python backend.

Current project path after the directory rename:

`/Users/aaacc/Documents/语音处理/语音大作业/Voice_clone`

## Important Decision

The local model is CosyVoice3:

`pretrained_models/Fun-CosyVoice3-0.5B`

CosyVoice3 does not provide the old SFT built-in speaker list such as `中文男` or `中文女`. Therefore, this project treats selected local prompt audio files as built-in voices and uses zero-shot or instruct-style CosyVoice3 inference to generate speech.

CosyVoice3 input text or prompt text must contain `<|endofprompt|>`. `backend/model_service.py` handles this with `COSYVOICE3_DEFAULT_PROMPT`, so do not remove that normalization unless the model path changes to a non-CosyVoice3 model.

## Expected Project Structure

- `backend/`: FastAPI backend, model service, preset config, audio preprocessing.
- `frontend/`: static HTML/CSS/JS workspace UI.
- `cosyvoice/`: migrated CosyVoice runtime package.
- `third_party/Matcha-TTS/`: required CosyVoice dependency.
- `pretrained_models/Fun-CosyVoice3-0.5B/`: local model files.
- `assets/prompts/`: built-in reference voices and sample prompt audio.
- `uploads/`: normalized user prompt audio files.
- `outputs/`: generated WAV files served by the backend.
- `docs/`: design and implementation notes.

## Current Feature Behavior

- The main synthesis page combines built-in voice, fixed/custom text, emotion, and speed controls.
- Fixed sentence samples are stored in `backend/presets.py` as `SENTENCES`; this list includes Chinese and English examples.
- Control-token shortcut buttons are rendered by `frontend/app.js` from `controlTokens`.
- Voice cloning accepts a prompt audio upload plus optional prompt transcript.
- Prompt transcript can be left empty. In that case, backend cloning uses the audio-only/cross-lingual path.
- Clone emotion support is available through the clone page's emotion dropdown.
- Generated audio auto-plays only for the newly generated main result. Historical result players must not auto-play.
- Before any audio starts playing, `pauseOtherAudio()` pauses other playing audio elements to avoid overlapping playback.
- The frontend is intentionally static HTML/CSS/JS; no npm build step is required.

## Audio Handling

- Prompt audio must be 3 to 30 seconds long. These values are in `backend/config.py`.
- Every uploaded prompt file is converted by `ffmpeg` before validation/inference.
- Conversion target is mono 16 kHz WAV, suitable for CosyVoice prompt input.
- Any format `ffmpeg` can decode should work, including common `wav`, `mp3`, `m4a`, and similar audio files.
- If `ffmpeg` is missing, decoding fails, or the file is damaged/incompatible, return a clear user-facing validation error.
- Keep generated/normalized files under `uploads/` and `outputs/`.

## Development Rules

- Do not import from `../CosyVoice-main` after migration is complete.
- Do not copy the 9GB model again. Use `mv` for any remaining migration work.
- Keep generated files in `uploads/` and `outputs/`.
- Do not remove or edit the source repository unless the user explicitly asks.
- Treat model inference as expensive; load the model once at backend startup.
- Use the existing `cosyvoice` conda environment for local commands.
- Keep frontend changes compatible with plain browser JavaScript.
- When changing playback behavior, update `tests/test_frontend_player.js`.
- When changing preset/API/model/audio behavior, update the relevant script tests in `tests/`.

## Backend API

- `GET /api/presets`
- `POST /api/tts/fixed`
- `POST /api/tts/control`
- `POST /api/tts/clone`
- `GET /outputs/{filename}`
- `GET /`

## Commands

From `Voice_clone/`:

```bash
./scripts/run_server.sh
```

Equivalent direct command:

```bash
conda run --no-capture-output -n cosyvoice uvicorn backend.main:app --host 127.0.0.1 --port 8010
```

Open:

```text
http://127.0.0.1:8010
```

Lightweight verification without pytest:

```bash
node --check frontend/app.js
node --check tests/test_frontend_player.js
node tests/test_frontend_player.js
PYTHONPATH=. conda run -n cosyvoice python tests/test_model_service.py
PYTHONPATH=. conda run -n cosyvoice python tests/test_api.py
PYTHONPATH=. conda run -n cosyvoice python tests/test_audio.py
PYTHONPATH=. conda run -n cosyvoice python tests/test_presets.py
```

## UI Direction

Use the left-navigation workspace layout:

- Voice Synthesis
- Voice Clone
- Results

The current UI is a dark audio-workbench style interface with animated background layers, generated-state progress animation, and a custom audio player.

Avoid reintroducing nested cards, landing-page style hero layouts, or a separate emotion page. The user asked to keep emotion/speed controls on the main synthesis page and clone page.

## Known Pitfalls

- Do not assume CosyVoice3 exposes old SFT speaker names. Built-in voices are prompt-audio presets.
- Do not require prompt transcript for cloning; it is optional by design.
- Do not pass user audio directly to the model without conversion/validation.
- Do not auto-play every historical player when rendering results; this previously caused overlapping playback.
- Do not add another model copy under this project unless the user explicitly approves storage use.
- The conda environment is named `cosyvoice`; package installation is usually not needed.
- `pytest` may not be installed. The test files are executable Python/Node scripts.

## Notes For Future Agents

The design spec for the initial build is:

`docs/superpowers/specs/2026-05-19-voice-clone-system-design.md`

Before changing architecture, read that spec and update this file if the project conventions change.

Most recent implementation details worth preserving:

- `backend/audio.py`: ffmpeg conversion and 3-30 second validation.
- `backend/model_service.py`: CosyVoice3 prompt marker handling and inference routing.
- `backend/presets.py`: built-in voice prompts, bilingual sentence samples, emotions, and speeds.
- `frontend/app.js`: token insertion, generation progress UI, result history, and single-audio playback logic.
- `tests/test_frontend_player.js`: regression coverage for no autoplay in history and pausing other audio before autoplay.
```