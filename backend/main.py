from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.audio import AudioValidationError, normalize_prompt_audio
from backend.config import FRONTEND_DIR, OUTPUT_DIR, UPLOAD_DIR
from backend.fastspeech2_service import FastSpeech2AssetError, FastSpeech2Controls, fastspeech2_service
from backend.model_service import model_service
from backend.presets import (
    EMOTIONS,
    FASTSPEECH2_EMOTION_CONTROLS,
    FASTSPEECH2_SPEAKERS,
    SENTENCES,
    SPEEDS,
    VOICES,
    find_by_id,
    get_presets,
)
from backend.schemas import AudioResponse, CompareRequest, ControlRequest, FastSpeech2Request, FixedRequest

app = FastAPI(title="Voice Clone")
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


def audio_response(filename: str) -> AudioResponse:
    return AudioResponse(filename=filename, audio_url=f"/outputs/{filename}")


def audio_payload(filename: str, engine: str, metadata: dict | None = None):
    return {
        "filename": filename,
        "audio_url": f"/outputs/{filename}",
        "engine": engine,
        "metadata": metadata or {},
    }


def find_fastspeech2_speaker(speaker_id: int) -> dict:
    for speaker in FASTSPEECH2_SPEAKERS:
        if speaker["speaker_id"] == speaker_id:
            return speaker
    raise KeyError(speaker_id)


def fastspeech2_controls_from_payload(payload) -> FastSpeech2Controls:
    preset = FASTSPEECH2_EMOTION_CONTROLS.get(payload.emotion_id)
    if preset is None:
        raise KeyError(payload.emotion_id)
    use_payload_defaults = (
        payload.pitch_control == 1.0
        and payload.energy_control == 1.0
        and payload.duration_control == 1.0
        and payload.emotion_id != "neutral"
    )
    if use_payload_defaults:
        return FastSpeech2Controls(preset["pitch"], preset["energy"], preset["duration"]).clamped()
    return FastSpeech2Controls(payload.pitch_control, payload.energy_control, payload.duration_control).clamped()


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


@app.post("/api/tts/fastspeech2")
def tts_fastspeech2(payload: FastSpeech2Request):
    try:
        find_fastspeech2_speaker(payload.speaker_id)
        controls = fastspeech2_controls_from_payload(payload)
        filename = fastspeech2_service.synthesize(payload.text, payload.speaker_id, controls)
        return audio_payload(
            filename,
            "FastSpeech2",
            {
                "speaker_id": payload.speaker_id,
                "emotion_id": payload.emotion_id,
                "pitch": controls.pitch,
                "energy": controls.energy,
                "duration": controls.duration,
            },
        )
    except (FastSpeech2AssetError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"未知选项: {exc.args[0]}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/tts/compare")
def tts_compare(payload: CompareRequest):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="请输入要合成的文本。")

    try:
        voice = find_by_id(VOICES, payload.cosyvoice_voice_id)
        find_fastspeech2_speaker(payload.fastspeech2_speaker_id)
        emotion = find_by_id(EMOTIONS, payload.emotion_id)
        speed = find_by_id(SPEEDS, payload.cosyvoice_speed_id)["value"]
        controls = fastspeech2_controls_from_payload(payload)

        if emotion["id"] == "neutral":
            cosy_filename = model_service.synthesize_fixed(payload.text, voice, speed)
        else:
            cosy_filename = model_service.synthesize_control(payload.text, voice, emotion["instruction"], speed)

        result = {
            "cosyvoice": audio_payload(
                cosy_filename,
                "CosyVoice3",
                {"voice_id": voice["id"], "emotion_id": emotion["id"], "speed": speed},
            ),
            "fastspeech2": None,
        }
        try:
            fast_filename = fastspeech2_service.synthesize(payload.text, payload.fastspeech2_speaker_id, controls)
            result["fastspeech2"] = audio_payload(
                fast_filename,
                "FastSpeech2",
                {
                    "speaker_id": payload.fastspeech2_speaker_id,
                    "emotion_id": emotion["id"],
                    "pitch": controls.pitch,
                    "energy": controls.energy,
                    "duration": controls.duration,
                },
            )
        except (FastSpeech2AssetError, ValueError, RuntimeError) as exc:
            result["fastspeech2_error"] = str(exc)
        return result
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
