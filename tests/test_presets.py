from backend.presets import get_presets


def test_presets_include_required_sections():
    data = get_presets()

    assert set(data) == {"voices", "sentences", "emotions", "speeds", "fastspeech2"}
    assert len(data["voices"]) >= 3
    assert len(data["sentences"]) >= 3
    assert {"id": "happy", "label": "开心"} in [
        {"id": item["id"], "label": item["label"]} for item in data["emotions"]
    ]
    assert len(data["fastspeech2"]["speakers"]) >= 4
    assert data["fastspeech2"]["emotion_controls"]["angry"]["energy"] > 1.0


def test_fastspeech2_control_ranges_are_present():
    data = get_presets()
    controls = data["fastspeech2"]["control_ranges"]

    assert controls["pitch"]["min"] == 0.5
    assert controls["pitch"]["max"] == 1.5
    assert controls["energy"]["min"] == 0.5
    assert controls["energy"]["max"] == 1.5
    assert controls["duration"]["min"] == 0.5
    assert controls["duration"]["max"] == 1.5


def test_voice_prompt_files_are_relative_names():
    data = get_presets()

    for voice in data["voices"]:
        assert voice["prompt_wav"].endswith(".wav")
        assert "/" not in voice["prompt_wav"]


if __name__ == "__main__":
    test_presets_include_required_sections()
    test_fastspeech2_control_ranges_are_present()
    test_voice_prompt_files_are_relative_names()
    print("preset tests passed")
