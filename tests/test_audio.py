from pathlib import Path
import shutil
import subprocess

import torch
import torchaudio

from backend.audio import AudioValidationError, normalize_prompt_audio


def test_normalize_prompt_audio_writes_16k_mono_wav(tmp_path):
    source = tmp_path / "input.wav"
    waveform = torch.zeros(2, 4 * 32000)
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

    try:
        normalize_prompt_audio(source, tmp_path)
    except AudioValidationError:
        return
    raise AssertionError("Expected AudioValidationError for prompt audio longer than 30 seconds")


def make_encoded_audio(tmp_path, suffix):
    if shutil.which("ffmpeg") is None:
        return None

    wav_source = tmp_path / "input.wav"
    encoded_source = tmp_path / f"input{suffix}"
    waveform = torch.zeros(1, 4 * 16000)
    torchaudio.save(str(wav_source), waveform, 16000)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(wav_source),
            str(encoded_source),
        ],
        check=True,
    )
    return encoded_source


def test_normalize_prompt_audio_converts_m4a_to_16k_mono_wav(tmp_path):
    m4a_source = make_encoded_audio(tmp_path, ".m4a")
    if m4a_source is None:
        print("ffmpeg not found, skipping m4a conversion test")
        return

    output = normalize_prompt_audio(m4a_source, tmp_path)

    loaded, sample_rate = torchaudio.load(str(output))
    assert output.suffix == ".wav"
    assert sample_rate == 16000
    assert loaded.shape[0] == 1


def test_normalize_prompt_audio_converts_mp3_to_16k_mono_wav(tmp_path):
    mp3_source = make_encoded_audio(tmp_path, ".mp3")
    if mp3_source is None:
        print("ffmpeg not found, skipping mp3 conversion test")
        return

    output = normalize_prompt_audio(mp3_source, tmp_path)

    loaded, sample_rate = torchaudio.load(str(output))
    assert output.suffix == ".wav"
    assert sample_rate == 16000
    assert loaded.shape[0] == 1


def test_normalize_prompt_audio_rejects_too_short_audio(tmp_path):
    source = tmp_path / "short.wav"
    waveform = torch.zeros(1, 16000)
    torchaudio.save(str(source), waveform, 16000)

    try:
        normalize_prompt_audio(source, tmp_path)
    except AudioValidationError as exc:
        assert "至少需要" in str(exc)
        return
    raise AssertionError("Expected AudioValidationError for short prompt audio")


def test_normalize_prompt_audio_rejects_incompatible_file(tmp_path):
    source = tmp_path / "broken.mp3"
    source.write_text("not an audio file", encoding="utf-8")

    try:
        normalize_prompt_audio(source, tmp_path)
    except AudioValidationError as exc:
        assert "格式不兼容" in str(exc) or "文件损坏" in str(exc)
        return
    raise AssertionError("Expected AudioValidationError for incompatible audio")


if __name__ == "__main__":
    import tempfile

    class TmpPath:
        def __enter__(self):
            self._tmp = tempfile.TemporaryDirectory()
            return Path(self._tmp.name)

        def __exit__(self, exc_type, exc, tb):
            self._tmp.cleanup()

    with TmpPath() as path:
        test_normalize_prompt_audio_writes_16k_mono_wav(path)
    with TmpPath() as path:
        test_normalize_prompt_audio_rejects_over_30_seconds(path)
    with TmpPath() as path:
        test_normalize_prompt_audio_converts_m4a_to_16k_mono_wav(path)
    with TmpPath() as path:
        test_normalize_prompt_audio_converts_mp3_to_16k_mono_wav(path)
    with TmpPath() as path:
        test_normalize_prompt_audio_rejects_too_short_audio(path)
    with TmpPath() as path:
        test_normalize_prompt_audio_rejects_incompatible_file(path)
    print("audio tests passed")
