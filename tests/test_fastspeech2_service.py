from pathlib import Path

import numpy as np

from backend.config import FASTSPEECH2_ASSET_DIR, FASTSPEECH2_RUNTIME_DIR
from backend.fastspeech2_service import (
    FastSpeech2AssetError,
    FastSpeech2Controls,
    FastSpeech2Service,
)


def test_fastspeech2_runtime_paths_point_inside_project():
    project_root = Path(__file__).resolve().parents[1]

    assert FASTSPEECH2_RUNTIME_DIR == project_root / "third_party" / "FastSpeech2"
    assert FASTSPEECH2_ASSET_DIR == project_root / "pretrained_models" / "FastSpeech2-AISHELL3"


def test_control_values_are_clamped_to_supported_range():
    controls = FastSpeech2Controls(pitch=2.0, energy=0.1, duration=1.2).clamped()

    assert controls.pitch == 1.5
    assert controls.energy == 0.5
    assert controls.duration == 1.2


def test_missing_assets_raise_clear_error():
    temp_root = Path(__file__).resolve().parents[1] / "tests" / "_missing_fastspeech2_assets"
    service = FastSpeech2Service(runtime_dir=temp_root / "runtime", asset_dir=temp_root / "assets")

    try:
        service.validate_assets()
    except FastSpeech2AssetError as exc:
        assert "FastSpeech2 runtime" in str(exc)
    else:
        raise AssertionError("Expected FastSpeech2AssetError")


def test_service_has_runtime_lock_for_cwd_operations():
    service = FastSpeech2Service()

    assert service._runtime_lock is not None


def test_preprocess_text_resolves_runtime_relative_lexicon():
    service = FastSpeech2Service()
    try:
        sequence = service._preprocess_text("大家好")
    except FastSpeech2AssetError as exc:
        assert "依赖缺失" in str(exc)
        return

    assert sequence.shape[0] == 1
    assert sequence.shape[1] > 0


class FakeFastSpeech2Service(FastSpeech2Service):
    def validate_assets(self):
        return None

    def _synthesize_waveform(self, text, speaker_id, controls):
        assert text == "大家好"
        assert speaker_id == 178
        assert controls.pitch == 1.0
        return 22050, np.zeros(2205, dtype=np.int16)


def test_synthesize_saves_fastspeech2_wav():
    service = FakeFastSpeech2Service()
    filename = service.synthesize("大家好", speaker_id=178, controls=FastSpeech2Controls())

    assert filename.startswith("fastspeech2_")
    assert filename.endswith(".wav")
    assert (Path(__file__).resolve().parents[1] / "outputs" / filename).exists()


if __name__ == "__main__":
    test_fastspeech2_runtime_paths_point_inside_project()
    test_control_values_are_clamped_to_supported_range()
    test_missing_assets_raise_clear_error()
    test_service_has_runtime_lock_for_cwd_operations()
    test_preprocess_text_resolves_runtime_relative_lexicon()
    test_synthesize_saves_fastspeech2_wav()
    print("fastspeech2 service tests passed")
