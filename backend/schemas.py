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
