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
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


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
        if payload.text and payload.text.strip():
            text = payload.text.strip()
        elif payload.sentence_id:
            text = find_by_id(SENTENCES, payload.sentence_id)["text"]
        else:
            raise HTTPException(status_code=400, detail="请输入要合成的文本。")
        emotion = find_by_id(EMOTIONS, payload.emotion_id)
        speed = find_by_id(SPEEDS, payload.speed_id)["value"]
        if emotion["id"] == "neutral":
            filename = model_service.synthesize_fixed(text, voice, speed)
        else:
            filename = model_service.synthesize_control(text, voice, emotion["instruction"], speed)
        return audio_response(filename)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"未知选项: {exc.args[0]}") from exc
    except HTTPException:
        raise
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
    prompt_text: str = Form(""),
    speed: float = Form(1.0),
    emotion_id: str = Form("neutral"),
    prompt_audio: UploadFile = File(...),
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="请输入要合成的文本。")

    suffix = Path(prompt_audio.filename or "prompt.wav").suffix or ".wav"
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await prompt_audio.read())
        tmp_path = Path(tmp.name)

    try:
        normalized = normalize_prompt_audio(tmp_path, UPLOAD_DIR)
        emotion = find_by_id(EMOTIONS, emotion_id)
        emotion_instruction = None if emotion["id"] == "neutral" else emotion["instruction"]
        filename = model_service.synthesize_clone(
            text,
            prompt_text,
            normalized,
            speed,
            emotion_instruction=emotion_instruction,
        )
        return audio_response(filename)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"未知选项: {exc.args[0]}") from exc
    except AudioValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        tmp_path.unlink(missing_ok=True)
