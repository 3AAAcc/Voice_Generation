# Voice Clone System Design

## Goal

Build an independent voice synthesis and cloning demo project under `Voice_clone/`, migrated from the useful CosyVoice assets in `CosyVoice-main/`. The system should provide a Python backend and a browser frontend for fixed voice demos, emotion and speed control, and voice cloning from uploaded or recorded audio.

## Selected UI

Use the left-navigation workspace layout.

The frontend will have a persistent sidebar with four sections:

- Fixed Voice: choose a built-in reference voice and a fixed sentence, then generate audio.
- Emotion and Speed: choose a fixed sentence, emotion, and speed value, then generate controlled audio.
- Voice Clone: upload or record a prompt audio clip, enter the matching prompt text, choose output text, and generate cloned speech.
- Results: show recent generated files with playable audio.

This layout keeps the three required features separated while still making the project feel like one coherent system.

## Model Strategy

Use the local CosyVoice3 model currently present at:

`CosyVoice-main/pretrained_models/Fun-CosyVoice3-0.5B`

Because this is a CosyVoice3 zero-shot/instruct model and not a CosyVoice SFT model with built-in speaker IDs such as `中文男` or `中文女`, fixed voices will be implemented as built-in reference audio presets. Each preset contains:

- a display name,
- a prompt audio file,
- prompt text when needed,
- a default instruction prompt for CosyVoice3.

The backend will call CosyVoice3 methods such as `inference_zero_shot`, `inference_cross_lingual`, and `inference_instruct2` rather than relying on unavailable SFT speakers.

## Project Boundary

`Voice_clone/` becomes the new independent project. It should contain the migrated runtime code, model files, assets, backend, frontend, docs, and generated outputs.

The original `CosyVoice-main/` directory is a source for migration only. After migration, the new project should not require imports or file references back into `CosyVoice-main/`.

## Backend Design

Use FastAPI as the backend.

Core responsibilities:

- load the CosyVoice model once at startup,
- expose preset metadata to the frontend,
- validate text, emotion, speed, and prompt audio inputs,
- convert uploaded or recorded audio into a model-friendly WAV format,
- run inference,
- save generated WAV files under `Voice_clone/outputs/`,
- return playable audio URLs.

Planned API surface:

- `GET /api/presets`
- `POST /api/tts/fixed`
- `POST /api/tts/control`
- `POST /api/tts/clone`
- `GET /outputs/{filename}`
- `GET /` for the frontend page

Audio preprocessing for clone inputs:

- accept browser upload/recording formats supported by the local audio stack,
- resample prompt audio to 16 kHz WAV for speech token and speaker embedding extraction,
- keep duration within CosyVoice's prompt limit of 30 seconds,
- write normalized prompt files under `Voice_clone/uploads/`.

## Frontend Design

Use a lightweight static frontend served by FastAPI. The first implementation can be plain HTML, CSS, and JavaScript to reduce dependency friction.

Expected behavior:

- sidebar navigation switches between feature panels,
- forms use fixed option lists where the assignment asks for fixed choices,
- generate buttons show loading state,
- audio output appears immediately after successful generation,
- errors from the backend are displayed clearly near the current panel,
- results list keeps recent generation history for the current browser session.

## Presets

Initial fixed sentences:

- "你好，欢迎使用语音合成与音色克隆演示系统。"
- "今天的阳光很好，我们一起完成这个有趣的语音项目。"
- "人工智能正在让声音交互变得更加自然。"

Initial emotions:

- neutral: neutral/default instruction
- happy: "请非常开心地说这句话。"
- sad: "请非常伤心地说这句话。"
- angry: "请非常生气地说这句话。"

Initial speed options:

- 0.8 slow
- 1.0 normal
- 1.2 fast
- 1.5 very fast

Initial fixed voices should be based on usable local files under `CosyVoice-main/asset/`, copied into `Voice_clone/assets/prompts/`.

## Error Handling

The backend should return structured JSON errors for:

- empty synthesis text,
- missing prompt audio for cloning,
- missing prompt text when the selected mode needs it,
- audio files longer than 30 seconds,
- unsupported or unreadable audio files,
- model inference failures.

The frontend should show these messages without losing the user's current inputs.

## Verification

Minimum verification:

- backend imports successfully,
- `/api/presets` returns the configured voices, sentences, emotions, and speeds,
- audio preprocessing can convert a sample asset,
- each synthesis endpoint can be called with representative form data,
- the frontend loads and can reach the backend.

Full audio inference depends on local model dependencies and available hardware, so verification should distinguish between import/API checks and actual model synthesis checks.

## Documentation

Maintain `Voice_clone/AGENTS.md` as the project memory for future coding sessions. It should document:

- project purpose,
- important directories,
- model and asset strategy,
- expected commands,
- implementation constraints,
- known limitations of using CosyVoice3 instead of SFT speaker IDs.
