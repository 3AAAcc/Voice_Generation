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
