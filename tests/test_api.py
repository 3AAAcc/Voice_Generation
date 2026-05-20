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


if __name__ == "__main__":
    test_presets_endpoint()
    test_fixed_endpoint()
    test_fixed_endpoint_accepts_custom_text_and_emotion()
    test_control_endpoint()
    test_clone_endpoint_accepts_audio_without_prompt_text()
    test_clone_endpoint_accepts_emotion()
    print("api tests passed")
