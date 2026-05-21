from fastapi.testclient import TestClient
import tempfile

import torch
import torchaudio

import backend.main as main


class FakeModelService:
    last_call = None

    def synthesize_fixed(self, text, voice, speed=1.0):
        self.last_call = ("fixed", text, voice["id"], speed)
        return "fixed_test.wav"

    def synthesize_control(self, text, voice, instruction, speed):
        self.last_call = ("control", text, voice["id"], instruction, speed)
        return "control_test.wav"

    def synthesize_clone(self, text, prompt_text, prompt_wav, speed=1.0, emotion_instruction=None):
        self.last_call = ("clone", text, prompt_text, str(prompt_wav), speed, emotion_instruction)
        return "clone_test.wav"


class FakeFastSpeech2Service:
    last_call = None

    def synthesize(self, text, speaker_id, controls):
        self.last_call = ("fastspeech2", text, speaker_id, controls.pitch, controls.energy, controls.duration)
        return "fastspeech2_test.wav"


class MissingAssetFastSpeech2Service:
    def synthesize(self, text, speaker_id, controls):
        raise main.FastSpeech2AssetError("FastSpeech2 AISHELL3 模型文件缺失，请下载 600000.pth.tar。")


def test_presets_endpoint():
    client = TestClient(main.app)
    response = client.get("/api/presets")

    assert response.status_code == 200
    assert "voices" in response.json()


def test_fixed_endpoint():
    fake = FakeModelService()
    main.model_service = fake
    client = TestClient(main.app)

    response = client.post(
        "/api/tts/fixed",
        json={"voice_id": "warm_female", "sentence_id": "welcome", "speed_id": "normal"},
    )

    assert response.status_code == 200
    assert response.json()["audio_url"] == "/outputs/fixed_test.wav"
    assert fake.last_call[0] == "fixed"


def test_fixed_endpoint_accepts_custom_text_and_emotion():
    fake = FakeModelService()
    main.model_service = fake
    client = TestClient(main.app)

    response = client.post(
        "/api/tts/fixed",
        json={
            "voice_id": "warm_female",
            "text": "这是一句用户自己输入的话。",
            "emotion_id": "happy",
            "speed_id": "fast",
        },
    )

    assert response.status_code == 200
    assert response.json()["audio_url"] == "/outputs/control_test.wav"
    assert fake.last_call[0] == "control"
    assert fake.last_call[1] == "这是一句用户自己输入的话。"


def test_control_endpoint():
    main.model_service = FakeModelService()
    client = TestClient(main.app)

    response = client.post(
        "/api/tts/control",
        json={
            "voice_id": "warm_female",
            "sentence_id": "welcome",
            "emotion_id": "happy",
            "speed_id": "fast",
        },
    )

    assert response.status_code == 200
    assert response.json()["audio_url"] == "/outputs/control_test.wav"


def test_clone_endpoint_accepts_audio_without_prompt_text():
    fake = FakeModelService()
    main.model_service = fake
    client = TestClient(main.app)

    with tempfile.NamedTemporaryFile(suffix=".wav") as sample:
        torchaudio.save(sample.name, torch.zeros(1, 4 * 16000), 16000)
        sample.seek(0)
        response = client.post(
            "/api/tts/clone",
            data={"text": "这是一句克隆测试。", "prompt_text": "", "speed": "1.0"},
            files={"prompt_audio": ("prompt.wav", sample.read(), "audio/wav")},
        )

    assert response.status_code == 200
    assert response.json()["audio_url"] == "/outputs/clone_test.wav"
    assert fake.last_call[0] == "clone"
    assert fake.last_call[2] == ""


def test_clone_endpoint_accepts_emotion():
    fake = FakeModelService()
    main.model_service = fake
    client = TestClient(main.app)

    with tempfile.NamedTemporaryFile(suffix=".wav") as sample:
        torchaudio.save(sample.name, torch.zeros(1, 4 * 16000), 16000)
        sample.seek(0)
        response = client.post(
            "/api/tts/clone",
            data={
                "text": "这是一句开心克隆测试。",
                "prompt_text": "",
                "speed": "1.0",
                "emotion_id": "happy",
            },
            files={"prompt_audio": ("prompt.wav", sample.read(), "audio/wav")},
        )

    assert response.status_code == 200
    assert fake.last_call[0] == "clone"
    assert "开心" in fake.last_call[5]


def test_fastspeech2_endpoint():
    fake = FakeFastSpeech2Service()
    main.fastspeech2_service = fake
    client = TestClient(main.app)

    response = client.post(
        "/api/tts/fastspeech2",
        json={
            "text": "大家好",
            "speaker_id": 178,
            "emotion_id": "neutral",
            "pitch_control": 1.0,
            "energy_control": 1.0,
            "duration_control": 1.0,
        },
    )

    assert response.status_code == 200
    assert response.json()["audio_url"] == "/outputs/fastspeech2_test.wav"
    assert fake.last_call[2] == 178


def test_fastspeech2_endpoint_applies_emotion_defaults_when_controls_are_default():
    fake = FakeFastSpeech2Service()
    main.fastspeech2_service = fake
    client = TestClient(main.app)

    response = client.post(
        "/api/tts/fastspeech2",
        json={
            "text": "大家好",
            "speaker_id": 178,
            "emotion_id": "happy",
            "pitch_control": 1.0,
            "energy_control": 1.0,
            "duration_control": 1.0,
        },
    )

    assert response.status_code == 200
    assert fake.last_call[3] == 1.12
    assert fake.last_call[4] == 1.10
    assert fake.last_call[5] == 0.90


def test_fastspeech2_endpoint_rejects_unknown_speaker():
    main.fastspeech2_service = FakeFastSpeech2Service()
    client = TestClient(main.app)

    response = client.post(
        "/api/tts/fastspeech2",
        json={
            "text": "大家好",
            "speaker_id": 99999,
            "emotion_id": "neutral",
            "pitch_control": 1.0,
            "energy_control": 1.0,
            "duration_control": 1.0,
        },
    )

    assert response.status_code == 400
    assert "未知选项" in response.json()["detail"]


def test_compare_endpoint_returns_both_results():
    cosy = FakeModelService()
    fast = FakeFastSpeech2Service()
    main.model_service = cosy
    main.fastspeech2_service = fast
    client = TestClient(main.app)

    response = client.post(
        "/api/tts/compare",
        json={
            "text": "大家好",
            "cosyvoice_voice_id": "warm_female",
            "fastspeech2_speaker_id": 178,
            "emotion_id": "happy",
            "cosyvoice_speed_id": "normal",
            "pitch_control": 1.12,
            "energy_control": 1.1,
            "duration_control": 0.9,
        },
    )

    data = response.json()
    assert response.status_code == 200
    assert data["cosyvoice"]["audio_url"] == "/outputs/control_test.wav"
    assert data["fastspeech2"]["audio_url"] == "/outputs/fastspeech2_test.wav"


def test_compare_endpoint_returns_cosyvoice_when_fastspeech2_assets_missing():
    cosy = FakeModelService()
    main.model_service = cosy
    main.fastspeech2_service = MissingAssetFastSpeech2Service()
    client = TestClient(main.app)

    response = client.post(
        "/api/tts/compare",
        json={
            "text": "大家好",
            "cosyvoice_voice_id": "warm_female",
            "fastspeech2_speaker_id": 178,
            "emotion_id": "neutral",
            "cosyvoice_speed_id": "normal",
            "pitch_control": 1.0,
            "energy_control": 1.0,
            "duration_control": 1.0,
        },
    )

    data = response.json()
    assert response.status_code == 200
    assert data["cosyvoice"]["audio_url"] == "/outputs/fixed_test.wav"
    assert data["fastspeech2"] is None
    assert "FastSpeech2 AISHELL3" in data["fastspeech2_error"]


if __name__ == "__main__":
    test_presets_endpoint()
    test_fixed_endpoint()
    test_fixed_endpoint_accepts_custom_text_and_emotion()
    test_control_endpoint()
    test_clone_endpoint_accepts_audio_without_prompt_text()
    test_clone_endpoint_accepts_emotion()
    test_fastspeech2_endpoint()
    test_fastspeech2_endpoint_applies_emotion_defaults_when_controls_are_default()
    test_fastspeech2_endpoint_rejects_unknown_speaker()
    test_compare_endpoint_returns_both_results()
    test_compare_endpoint_returns_cosyvoice_when_fastspeech2_assets_missing()
    print("api tests passed")
