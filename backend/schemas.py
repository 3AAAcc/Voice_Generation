from pydantic import BaseModel


class FixedRequest(BaseModel):
    voice_id: str
    sentence_id: str | None = None
    text: str | None = None
    emotion_id: str = "neutral"
    speed_id: str = "normal"


class ControlRequest(BaseModel):
    voice_id: str
    sentence_id: str
    emotion_id: str
    speed_id: str


class AudioResponse(BaseModel):
    audio_url: str
    filename: str


class FastSpeech2Request(BaseModel):
    text: str
    speaker_id: int
    emotion_id: str = "neutral"
    pitch_control: float = 1.0
    energy_control: float = 1.0
    duration_control: float = 1.0


class CompareRequest(BaseModel):
    text: str
    cosyvoice_voice_id: str
    fastspeech2_speaker_id: int
    emotion_id: str = "neutral"
    cosyvoice_speed_id: str = "normal"
    pitch_control: float = 1.0
    energy_control: float = 1.0
    duration_control: float = 1.0
