from pathlib import Path
import shutil
import subprocess
import tempfile
from uuid import uuid4

import torch
import torchaudio

from backend.config import MAX_PROMPT_SECONDS, MIN_PROMPT_SECONDS, PROMPT_SAMPLE_RATE


class AudioValidationError(ValueError):
    pass


def _convert_to_prompt_wav(source_path: Path) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise AudioValidationError("服务器未找到 ffmpeg，无法自动转换音频格式。")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        converted_path = Path(tmp.name)

    try:
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(source_path),
                "-vn",
                "-ac",
                "1",
                "-ar",
                str(PROMPT_SAMPLE_RATE),
                "-f",
                "wav",
                str(converted_path),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return converted_path
    except Exception as exc:
        converted_path.unlink(missing_ok=True)
        raise AudioValidationError("音频格式不兼容或文件损坏，请上传可播放的音频文件。") from exc


def normalize_prompt_audio(source_path: Path, output_dir: Path) -> Path:
    source_path = Path(source_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    converted_path = _convert_to_prompt_wav(source_path)
    try:
        waveform, sample_rate = torchaudio.load(str(converted_path))
    except Exception as exc:
        raise AudioValidationError("音频格式不兼容或文件损坏，请上传可播放的音频文件。") from exc
    finally:
        converted_path.unlink(missing_ok=True)

    duration = waveform.shape[1] / sample_rate
    if duration < MIN_PROMPT_SECONDS:
        raise AudioValidationError(f"参考音频至少需要 {MIN_PROMPT_SECONDS} 秒，请上传更长的人声音频。")
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
