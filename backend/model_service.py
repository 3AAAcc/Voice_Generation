import sys
from pathlib import Path
from uuid import uuid4

import torchaudio

from backend.config import MODEL_DIR, OUTPUT_DIR, PROJECT_ROOT, PROMPT_DIR

MATCHA_DIR = PROJECT_ROOT / "third_party" / "Matcha-TTS"
if str(MATCHA_DIR) not in sys.path:
    sys.path.append(str(MATCHA_DIR))

from cosyvoice.cli.cosyvoice import AutoModel  # noqa: E402

COSYVOICE3_DEFAULT_PROMPT = "You are a helpful assistant.<|endofprompt|>"


def ensure_cosyvoice3_prompt(text: str) -> str:
    text = text.strip()
    if "<|endofprompt|>" in text:
        return text
    return f"{COSYVOICE3_DEFAULT_PROMPT}{text}"


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

    def synthesize_clone(
        self,
        text: str,
        prompt_text: str,
        prompt_wav: Path,
        speed: float = 1.0,
        emotion_instruction: str | None = None,
    ) -> str:
        prompt_text = prompt_text.strip()
        if emotion_instruction:
            return self._save_first_result(
                self.model.inference_instruct2(
                    text,
                    ensure_cosyvoice3_prompt(emotion_instruction),
                    str(prompt_wav),
                    stream=False,
                    speed=speed,
                ),
                "clone",
            )
        if not prompt_text:
            return self._save_first_result(
                self.model.inference_cross_lingual(
                    ensure_cosyvoice3_prompt(text),
                    str(prompt_wav),
                    stream=False,
                    speed=speed,
                ),
                "clone",
            )
        return self._save_first_result(
            self.model.inference_zero_shot(
                text,
                ensure_cosyvoice3_prompt(prompt_text),
                str(prompt_wav),
                stream=False,
                speed=speed,
            ),
            "clone",
        )


model_service = ModelService()
