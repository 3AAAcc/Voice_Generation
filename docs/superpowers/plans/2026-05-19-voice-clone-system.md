# Voice Clone System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independent FastAPI + browser frontend voice synthesis and voice cloning demo inside `Voice_clone/`.

**Architecture:** Move the required CosyVoice runtime, model, third-party code, and prompt assets into `Voice_clone/`, then wrap CosyVoice3 inference behind small backend services. Serve a static left-navigation workspace frontend from FastAPI and expose JSON/audio endpoints for fixed voices, emotion/speed control, and voice cloning.

**Tech Stack:** Python 3.10, FastAPI, Uvicorn, PyTorch/Torchaudio, CosyVoice3, plain HTML/CSS/JavaScript, pytest.

---

## File Structure

- `Voice_clone/AGENTS.md`: project conventions and important technical decisions.
- `Voice_clone/README.md`: user-facing setup, run, and feature guide.
- `Voice_clone/requirements.txt`: Python dependencies copied and trimmed from CosyVoice.
- `Voice_clone/backend/__init__.py`: backend package marker.
- `Voice_clone/backend/config.py`: paths, model directory, upload/output directory constants.
- `Voice_clone/backend/presets.py`: fixed voices, sentences, emotions, and speeds.
- `Voice_clone/backend/audio.py`: prompt audio validation and normalization.
- `Voice_clone/backend/model_service.py`: lazy CosyVoice model loading and synthesis methods.
- `Voice_clone/backend/schemas.py`: Pydantic response/request models where JSON requests are used.
- `Voice_clone/backend/main.py`: FastAPI app, routes, static file serving.
- `Voice_clone/frontend/index.html`: left-navigation workspace shell.
- `Voice_clone/frontend/styles.css`: responsive app styling.
- `Voice_clone/frontend/app.js`: frontend state, API calls, audio result rendering.
- `Voice_clone/tests/test_presets.py`: preset validation tests.
- `Voice_clone/tests/test_audio.py`: audio preprocessing tests with generated sample audio.
- `Voice_clone/tests/test_api.py`: FastAPI route tests with model service mocked.
- `Voice_clone/scripts/run_server.sh`: convenience script to start the app.
- `Voice_clone/uploads/.gitkeep`: keep upload directory present.
- `Voice_clone/outputs/.gitkeep`: keep output directory present.
- `Voice_clone/assets/prompts/`: copied built-in prompt audio.
- `Voice_clone/cosyvoice/`: copied runtime package.
- `Voice_clone/third_party/Matcha-TTS/`: copied third-party dependency.
- `Voice_clone/pretrained_models/Fun-CosyVoice3-0.5B/`: copied local model.

---

## Task 1: Migrate Runtime Assets And Create Skeleton

**Files:**
- Create: `Voice_clone/backend/__init__.py`
- Create: `Voice_clone/frontend/index.html`
- Create: `Voice_clone/frontend/styles.css`
- Create: `Voice_clone/frontend/app.js`
- Create: `Voice_clone/uploads/.gitkeep`
- Create: `Voice_clone/outputs/.gitkeep`
- Move: `CosyVoice-main/cosyvoice` to `Voice_clone/cosyvoice`
- Move: `CosyVoice-main/third_party/Matcha-TTS` to `Voice_clone/third_party/Matcha-TTS`
- Move: `CosyVoice-main/pretrained_models/Fun-CosyVoice3-0.5B` to `Voice_clone/pretrained_models/Fun-CosyVoice3-0.5B`
- Move selected prompt assets from `CosyVoice-main/asset` to `Voice_clone/assets/prompts`

- [ ] **Step 1: Create directories**

Run:

```bash
mkdir -p Voice_clone/backend Voice_clone/frontend Voice_clone/tests Voice_clone/scripts Voice_clone/uploads Voice_clone/outputs Voice_clone/assets/prompts Voice_clone/third_party Voice_clone/pretrained_models
```

Expected: directories exist.

- [ ] **Step 2: Move CosyVoice runtime**

Run:

```bash
mv CosyVoice-main/cosyvoice Voice_clone/cosyvoice
mv CosyVoice-main/third_party/Matcha-TTS Voice_clone/third_party/Matcha-TTS
mv CosyVoice-main/pretrained_models/Fun-CosyVoice3-0.5B Voice_clone/pretrained_models/Fun-CosyVoice3-0.5B
```

Expected: migrated folders exist and `Voice_clone/pretrained_models/Fun-CosyVoice3-0.5B/cosyvoice3.yaml` exists.

- [ ] **Step 3: Move built-in prompt assets**

Run:

```bash
mv CosyVoice-main/asset/zero_shot_prompt.wav Voice_clone/assets/prompts/zero_shot_prompt.wav
mv CosyVoice-main/asset/cross_lingual_prompt.wav Voice_clone/assets/prompts/cross_lingual_prompt.wav
mv 'CosyVoice-main/asset/朱文骏_16k.wav' 'Voice_clone/assets/prompts/zhu_wenjun_16k.wav'
mv 'CosyVoice-main/asset/[海绵宝宝]我草，你们......，干嘛呢！_16k.wav' Voice_clone/assets/prompts/cartoon_angry_16k.wav
```

Expected: four prompt WAV files exist in `Voice_clone/assets/prompts/`.

- [ ] **Step 4: Add package and keep files**

Create:

```python
# Voice_clone/backend/__init__.py
```

Create empty files:

```text
Voice_clone/uploads/.gitkeep
Voice_clone/outputs/.gitkeep
```

- [ ] **Step 5: Check migration references**

Run:

```bash
rg -n "../CosyVoice-main|CosyVoice-main/" Voice_clone --glob '!docs/**' --glob '!AGENTS.md'
```

Expected: no matches.

---

## Task 2: Add Requirements And Runtime Config

**Files:**
- Create: `Voice_clone/requirements.txt`
- Create: `Voice_clone/backend/config.py`
- Create: `Voice_clone/README.md`

- [ ] **Step 1: Create requirements**

Use the CosyVoice dependency list, keeping FastAPI, audio, model, and frontend-serving dependencies:

```text
--extra-index-url https://download.pytorch.org/whl/cu121
conformer==0.3.2
diffusers==0.29.0
fastapi==0.115.6
gradio==5.4.0
hydra-core==1.3.2
HyperPyYAML==1.2.3
inflect==7.3.1
librosa==0.10.2
modelscope==1.20.0
networkx==3.1
numpy==1.26.4
omegaconf==2.3.0
onnx==1.16.0
onnxruntime==1.18.0
openai-whisper==20231117
protobuf==4.25
pydantic==2.7.0
pyworld==0.3.4
soundfile==0.12.1
torch==2.3.1
torchaudio==2.3.1
transformers==4.51.3
x-transformers==2.11.24
uvicorn==0.30.0
wetext==0.0.4
pytest==8.2.2
httpx==0.27.0
python-multipart==0.0.9
```

- [ ] **Step 2: Write config module**

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_ROOT / "pretrained_models" / "Fun-CosyVoice3-0.5B"
PROMPT_DIR = PROJECT_ROOT / "assets" / "prompts"
UPLOAD_DIR = PROJECT_ROOT / "uploads"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

MAX_PROMPT_SECONDS = 30
PROMPT_SAMPLE_RATE = 16000
OUTPUT_SAMPLE_RATE = 24000

for directory in (UPLOAD_DIR, OUTPUT_DIR):
    directory.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 3: Add README run instructions**

Include:

````markdown
# Voice Clone

Run from this directory:

```bash
pip install -r requirements.txt
uvicorn backend.main:app --host 127.0.0.1 --port 8010
```

Open `http://127.0.0.1:8010`.
````

- [ ] **Step 4: Verify config import**

Run:

```bash
cd Voice_clone && python -c "from backend.config import MODEL_DIR, PROMPT_DIR; print(MODEL_DIR.exists(), PROMPT_DIR.exists())"
```

Expected: `True True`.

---

## Task 3: Define Presets With Tests

**Files:**
- Create: `Voice_clone/backend/presets.py`
- Create: `Voice_clone/tests/test_presets.py`

- [ ] **Step 1: Write failing tests**

```python
from backend.presets import get_presets


def test_presets_include_required_sections():
    data = get_presets()
    assert set(data) == {"voices", "sentences", "emotions", "speeds"}
    assert len(data["voices"]) >= 3
    assert len(data["sentences"]) >= 3
    assert {"id": "happy", "label": "开心"} in [
        {"id": item["id"], "label": item["label"]} for item in data["emotions"]
    ]


def test_voice_prompt_files_are_relative_names():
    data = get_presets()
    for voice in data["voices"]:
        assert voice["prompt_wav"].endswith(".wav")
        assert "/" not in voice["prompt_wav"]
```

- [ ] **Step 2: Run tests and see failure**

Run:

```bash
cd Voice_clone && pytest tests/test_presets.py -v
```

Expected: FAIL because `backend.presets` does not exist.

- [ ] **Step 3: Implement presets**

```python
VOICES = [
    {
        "id": "warm_female",
        "label": "温柔女声",
        "prompt_wav": "zero_shot_prompt.wav",
        "prompt_text": "You are a helpful assistant.<|endofprompt|>希望你以后能够做的比我还好呦。",
    },
    {
        "id": "clear_male",
        "label": "清晰男声",
        "prompt_wav": "zhu_wenjun_16k.wav",
        "prompt_text": "You are a helpful assistant.<|endofprompt|>你好，欢迎使用语音克隆系统。",
    },
    {
        "id": "cartoon_angry",
        "label": "动画夸张声",
        "prompt_wav": "cartoon_angry_16k.wav",
        "prompt_text": "You are a helpful assistant.<|endofprompt|>你们干嘛呢！",
    },
]

SENTENCES = [
    {"id": "welcome", "text": "你好，欢迎使用语音合成与音色克隆演示系统。"},
    {"id": "sunny", "text": "今天的阳光很好，我们一起完成这个有趣的语音项目。"},
    {"id": "ai_voice", "text": "人工智能正在让声音交互变得更加自然。"},
]

EMOTIONS = [
    {"id": "neutral", "label": "自然", "instruction": "You are a helpful assistant. 请自然地说这句话。<|endofprompt|>"},
    {"id": "happy", "label": "开心", "instruction": "You are a helpful assistant. 请非常开心地说这句话。<|endofprompt|>"},
    {"id": "sad", "label": "伤心", "instruction": "You are a helpful assistant. 请非常伤心地说这句话。<|endofprompt|>"},
    {"id": "angry", "label": "生气", "instruction": "You are a helpful assistant. 请非常生气地说这句话。<|endofprompt|>"},
]

SPEEDS = [
    {"id": "slow", "label": "慢速", "value": 0.8},
    {"id": "normal", "label": "正常", "value": 1.0},
    {"id": "fast", "label": "快速", "value": 1.2},
    {"id": "very_fast", "label": "很快", "value": 1.5},
]


def get_presets():
    return {
        "voices": VOICES,
        "sentences": SENTENCES,
        "emotions": EMOTIONS,
        "speeds": SPEEDS,
    }


def find_by_id(items, item_id):
    for item in items:
        if item["id"] == item_id:
            return item
    raise KeyError(item_id)
```

- [ ] **Step 4: Run tests**

Run:

```bash
cd Voice_clone && pytest tests/test_presets.py -v
```

Expected: PASS.

---

## Task 4: Add Audio Preprocessing

**Files:**
- Create: `Voice_clone/backend/audio.py`
- Create: `Voice_clone/tests/test_audio.py`

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path

import pytest
import torch
import torchaudio

from backend.audio import AudioValidationError, normalize_prompt_audio


def test_normalize_prompt_audio_writes_16k_mono_wav(tmp_path):
    source = tmp_path / "input.wav"
    waveform = torch.zeros(2, 32000)
    torchaudio.save(str(source), waveform, 32000)

    output = normalize_prompt_audio(source, tmp_path)

    loaded, sample_rate = torchaudio.load(str(output))
    assert output.suffix == ".wav"
    assert sample_rate == 16000
    assert loaded.shape[0] == 1


def test_normalize_prompt_audio_rejects_over_30_seconds(tmp_path):
    source = tmp_path / "long.wav"
    waveform = torch.zeros(1, 31 * 16000)
    torchaudio.save(str(source), waveform, 16000)

    with pytest.raises(AudioValidationError):
        normalize_prompt_audio(source, tmp_path)
```

- [ ] **Step 2: Run tests and see failure**

Run:

```bash
cd Voice_clone && pytest tests/test_audio.py -v
```

Expected: FAIL because `backend.audio` does not exist.

- [ ] **Step 3: Implement audio module**

```python
from pathlib import Path
from uuid import uuid4

import torch
import torchaudio

from backend.config import MAX_PROMPT_SECONDS, PROMPT_SAMPLE_RATE


class AudioValidationError(ValueError):
    pass


def normalize_prompt_audio(source_path: Path, output_dir: Path) -> Path:
    source_path = Path(source_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        waveform, sample_rate = torchaudio.load(str(source_path))
    except Exception as exc:
        raise AudioValidationError("无法读取音频文件，请上传常见格式的音频。") from exc

    duration = waveform.shape[1] / sample_rate
    if duration > MAX_PROMPT_SECONDS:
        raise AudioValidationError("参考音频不能超过 30 秒。")

    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)

    if sample_rate != PROMPT_SAMPLE_RATE:
        waveform = torchaudio.functional.resample(waveform, sample_rate, PROMPT_SAMPLE_RATE)

    waveform = torch.clamp(waveform, -1.0, 1.0)
    output_path = output_dir / f"prompt_{uuid4().hex}.wav"
    torchaudio.save(str(output_path), waveform, PROMPT_SAMPLE_RATE)
    return output_path
```

- [ ] **Step 4: Run tests**

Run:

```bash
cd Voice_clone && pytest tests/test_audio.py -v
```

Expected: PASS.

---

## Task 5: Implement Model Service

**Files:**
- Create: `Voice_clone/backend/model_service.py`

- [ ] **Step 1: Add model service with lazy loading**

```python
import sys
from pathlib import Path
from uuid import uuid4

import torchaudio

from backend.config import MODEL_DIR, OUTPUT_DIR, PROJECT_ROOT, PROMPT_DIR

MATCHA_DIR = PROJECT_ROOT / "third_party" / "Matcha-TTS"
if str(MATCHA_DIR) not in sys.path:
    sys.path.append(str(MATCHA_DIR))

from cosyvoice.cli.cosyvoice import AutoModel  # noqa: E402


class ModelService:
    def __init__(self):
        self._model = None

    @property
    def model(self):
        if self._model is None:
            self._model = AutoModel(model_dir=str(MODEL_DIR))
        return self._model

    def _save_first_result(self, generator, prefix: str) -> str:
        for result in generator:
            filename = f"{prefix}_{uuid4().hex}.wav"
            output_path = OUTPUT_DIR / filename
            torchaudio.save(str(output_path), result["tts_speech"], self.model.sample_rate)
            return filename
        raise RuntimeError("模型没有返回音频。")

    def synthesize_fixed(self, text: str, voice: dict, speed: float = 1.0) -> str:
        prompt_wav = PROMPT_DIR / voice["prompt_wav"]
        return self._save_first_result(
            self.model.inference_zero_shot(
                text,
                voice["prompt_text"],
                str(prompt_wav),
                stream=False,
                speed=speed,
            ),
            "fixed",
        )

    def synthesize_control(self, text: str, voice: dict, instruction: str, speed: float) -> str:
        prompt_wav = PROMPT_DIR / voice["prompt_wav"]
        return self._save_first_result(
            self.model.inference_instruct2(
                text,
                instruction,
                str(prompt_wav),
                stream=False,
                speed=speed,
            ),
            "control",
        )

    def synthesize_clone(self, text: str, prompt_text: str, prompt_wav: Path, speed: float = 1.0) -> str:
        return self._save_first_result(
            self.model.inference_zero_shot(
                text,
                prompt_text,
                str(prompt_wav),
                stream=False,
                speed=speed,
            ),
            "clone",
        )


model_service = ModelService()
```

- [ ] **Step 2: Verify imports without loading model**

Run:

```bash
cd Voice_clone && python -c "from backend.model_service import model_service; print(model_service._model is None)"
```

Expected: `True`.

---

## Task 6: Add FastAPI Routes With Mocked Tests

**Files:**
- Create: `Voice_clone/backend/main.py`
- Create: `Voice_clone/backend/schemas.py`
- Create: `Voice_clone/tests/test_api.py`

- [ ] **Step 1: Write API tests**

```python
from fastapi.testclient import TestClient

import backend.main as main


class FakeModelService:
    def synthesize_fixed(self, text, voice, speed=1.0):
        return "fixed_test.wav"

    def synthesize_control(self, text, voice, instruction, speed):
        return "control_test.wav"

    def synthesize_clone(self, text, prompt_text, prompt_wav, speed=1.0):
        return "clone_test.wav"


def test_presets_endpoint():
    client = TestClient(main.app)
    response = client.get("/api/presets")
    assert response.status_code == 200
    assert "voices" in response.json()


def test_fixed_endpoint(monkeypatch):
    monkeypatch.setattr(main, "model_service", FakeModelService())
    client = TestClient(main.app)
    response = client.post(
        "/api/tts/fixed",
        json={"voice_id": "warm_female", "sentence_id": "welcome", "speed_id": "normal"},
    )
    assert response.status_code == 200
    assert response.json()["audio_url"] == "/outputs/fixed_test.wav"


def test_control_endpoint(monkeypatch):
    monkeypatch.setattr(main, "model_service", FakeModelService())
    client = TestClient(main.app)
    response = client.post(
        "/api/tts/control",
        json={
            "voice_id": "warm_female",
            "sentence_id": "welcome",
            "emotion_id": "happy",
            "speed_id": "fast",
        },
    )
    assert response.status_code == 200
    assert response.json()["audio_url"] == "/outputs/control_test.wav"
```

- [ ] **Step 2: Implement schemas**

```python
from pydantic import BaseModel


class FixedRequest(BaseModel):
    voice_id: str
    sentence_id: str
    speed_id: str = "normal"


class ControlRequest(BaseModel):
    voice_id: str
    sentence_id: str
    emotion_id: str
    speed_id: str


class AudioResponse(BaseModel):
    audio_url: str
    filename: str
```

- [ ] **Step 3: Implement FastAPI app**

```python
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.audio import AudioValidationError, normalize_prompt_audio
from backend.config import FRONTEND_DIR, OUTPUT_DIR, UPLOAD_DIR
from backend.model_service import model_service
from backend.presets import EMOTIONS, SENTENCES, SPEEDS, VOICES, find_by_id, get_presets
from backend.schemas import AudioResponse, ControlRequest, FixedRequest

app = FastAPI(title="Voice Clone")
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")


def audio_response(filename: str) -> AudioResponse:
    return AudioResponse(filename=filename, audio_url=f"/outputs/{filename}")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/presets")
def presets():
    return get_presets()


@app.post("/api/tts/fixed", response_model=AudioResponse)
def tts_fixed(payload: FixedRequest):
    try:
        voice = find_by_id(VOICES, payload.voice_id)
        sentence = find_by_id(SENTENCES, payload.sentence_id)
        speed = find_by_id(SPEEDS, payload.speed_id)["value"]
        return audio_response(model_service.synthesize_fixed(sentence["text"], voice, speed))
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"未知选项: {exc.args[0]}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/tts/control", response_model=AudioResponse)
def tts_control(payload: ControlRequest):
    try:
        voice = find_by_id(VOICES, payload.voice_id)
        sentence = find_by_id(SENTENCES, payload.sentence_id)
        emotion = find_by_id(EMOTIONS, payload.emotion_id)
        speed = find_by_id(SPEEDS, payload.speed_id)["value"]
        filename = model_service.synthesize_control(sentence["text"], voice, emotion["instruction"], speed)
        return audio_response(filename)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"未知选项: {exc.args[0]}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/tts/clone", response_model=AudioResponse)
async def tts_clone(
    text: str = Form(...),
    prompt_text: str = Form(...),
    speed: float = Form(1.0),
    prompt_audio: UploadFile = File(...),
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="请输入要合成的文本。")
    if not prompt_text.strip():
        raise HTTPException(status_code=400, detail="请输入参考音频对应的文本。")
    suffix = Path(prompt_audio.filename or "prompt.wav").suffix or ".wav"
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await prompt_audio.read())
        tmp_path = Path(tmp.name)
    try:
        normalized = normalize_prompt_audio(tmp_path, UPLOAD_DIR)
        filename = model_service.synthesize_clone(text, prompt_text, normalized, speed)
        return audio_response(filename)
    except AudioValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        tmp_path.unlink(missing_ok=True)
```

- [ ] **Step 4: Run API tests**

Run:

```bash
cd Voice_clone && pytest tests/test_api.py -v
```

Expected: PASS without loading the real model.

---

## Task 7: Build Frontend Workspace

**Files:**
- Modify: `Voice_clone/frontend/index.html`
- Modify: `Voice_clone/frontend/styles.css`
- Modify: `Voice_clone/frontend/app.js`

- [ ] **Step 1: Implement HTML shell**

Create a sidebar with buttons for `fixed`, `control`, `clone`, and `results`; create matching panels with selects, upload input, and audio result areas.

- [ ] **Step 2: Implement CSS**

Use a compact workbench style:

- fixed sidebar width,
- responsive single-column mobile layout,
- clear form labels,
- visible loading and error states,
- audio players under each panel.

- [ ] **Step 3: Implement JavaScript**

Required functions:

```javascript
async function loadPresets() {}
function fillSelect(select, items, labelKey, valueKey = "id") {}
async function postJson(url, body) {}
async function submitFixed() {}
async function submitControl() {}
async function submitClone() {}
function addResult(kind, response) {}
function showPanel(name) {}
function showError(panel, message) {}
```

- [ ] **Step 4: Verify static files are served**

Run:

```bash
cd Voice_clone && python -c "from backend.config import FRONTEND_DIR; print((FRONTEND_DIR / 'index.html').exists())"
```

Expected: `True`.

---

## Task 8: Add Run Script And Documentation

**Files:**
- Create: `Voice_clone/scripts/run_server.sh`
- Modify: `Voice_clone/README.md`
- Modify: `Voice_clone/AGENTS.md`

- [ ] **Step 1: Add run script**

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uvicorn backend.main:app --host 127.0.0.1 --port 8010
```

- [ ] **Step 2: Make script executable**

Run:

```bash
chmod +x Voice_clone/scripts/run_server.sh
```

- [ ] **Step 3: Update README**

Document:

- dependency installation,
- starting the app,
- opening `http://127.0.0.1:8010`,
- fixed voice implementation using prompt audio,
- clone prompt audio limit of 30 seconds.

- [ ] **Step 4: Update AGENTS**

Add the final startup command and any changed file conventions.

---

## Task 9: Verification

**Files:**
- No new files unless fixes are needed.

- [ ] **Step 1: Run unit tests**

Run:

```bash
cd Voice_clone && pytest -v
```

Expected: all tests pass.

- [ ] **Step 2: Run import smoke test**

Run:

```bash
cd Voice_clone && python -c "from backend.main import app; print(app.title)"
```

Expected: `Voice Clone`.

- [ ] **Step 3: Start backend**

Run:

```bash
cd Voice_clone && uvicorn backend.main:app --host 127.0.0.1 --port 8010
```

Expected: server starts. If dependencies are missing, install them before retrying.

- [ ] **Step 4: Check presets endpoint**

Run in another terminal:

```bash
curl http://127.0.0.1:8010/api/presets
```

Expected: JSON with `voices`, `sentences`, `emotions`, and `speeds`.

- [ ] **Step 5: Open frontend in browser**

Navigate to:

```text
http://127.0.0.1:8010
```

Expected: left-navigation workspace loads and selects are populated.

- [ ] **Step 6: Optional real synthesis check**

Call one endpoint from the frontend. Expected: first run may take time while the model loads; after success, a WAV file appears under `Voice_clone/outputs/` and plays in the browser.

If real synthesis fails due to missing installed dependencies or hardware limitations, record the exact dependency error in `README.md` or the final response.

---

## Self-Review

- Spec coverage: fixed voice demo, emotion/speed control, voice cloning, FastAPI backend, frontend workspace, model migration, and documentation are all covered.
- Placeholder scan: no incomplete placeholder steps remain.
- Type consistency: request fields in tests match `schemas.py`; preset IDs match route lookups.
- Known environment issue: the current parent directory is not a git repository, so this plan does not require commit steps.
