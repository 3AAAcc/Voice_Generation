from pathlib import Path

import torch

from backend.model_service import ModelService


class FakeCosyVoice3:
    sample_rate = 24000

    def __init__(self):
        self.calls = []

    def inference_cross_lingual(self, text, prompt_wav, stream=False, speed=1.0):
        self.calls.append(("cross_lingual", text, prompt_wav, stream, speed))
        yield {"tts_speech": torch.zeros(1, 2400)}

    def inference_zero_shot(self, text, prompt_text, prompt_wav, stream=False, speed=1.0):
        self.calls.append(("zero_shot", text, prompt_text, prompt_wav, stream, speed))
        yield {"tts_speech": torch.zeros(1, 2400)}

    def inference_instruct2(self, text, instruction, prompt_wav, stream=False, speed=1.0):
        self.calls.append(("instruct2", text, instruction, prompt_wav, stream, speed))
        yield {"tts_speech": torch.zeros(1, 2400)}


def test_clone_without_prompt_text_adds_cosyvoice3_endofprompt():
    service = ModelService()
    fake = FakeCosyVoice3()
    service._model = fake

    service.synthesize_clone("你好，这是测试。", "", Path("prompt.wav"))

    assert fake.calls[0][0] == "cross_lingual"
    assert fake.calls[0][1].startswith("You are a helpful assistant.<|endofprompt|>")


def test_clone_with_plain_prompt_text_adds_cosyvoice3_endofprompt_to_prompt():
    service = ModelService()
    fake = FakeCosyVoice3()
    service._model = fake

    service.synthesize_clone("你好，这是测试。", "这是一段参考音频文本。", Path("prompt.wav"))

    assert fake.calls[0][0] == "zero_shot"
    assert fake.calls[0][2].startswith("You are a helpful assistant.<|endofprompt|>")


def test_clone_with_emotion_uses_instruct2():
    service = ModelService()
    fake = FakeCosyVoice3()
    service._model = fake

    service.synthesize_clone(
        "你好，这是测试。",
        "",
        Path("prompt.wav"),
        emotion_instruction="You are a helpful assistant. 请非常开心地说这句话。<|endofprompt|>",
    )

    assert fake.calls[0][0] == "instruct2"
    assert "开心" in fake.calls[0][2]


if __name__ == "__main__":
    test_clone_without_prompt_text_adds_cosyvoice3_endofprompt()
    test_clone_with_plain_prompt_text_adds_cosyvoice3_endofprompt_to_prompt()
    test_clone_with_emotion_uses_instruct2()
    print("model service tests passed")
