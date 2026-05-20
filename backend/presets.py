VOICES = [
    {
        "id": "warm_female",
        "label": "温柔女声",
        "prompt_wav": "zero_shot_prompt.wav",
        "prompt_text": "You are a helpful assistant.<|endofprompt|>希望你以后能够做的比我还好呦。",
    },
    {
        "id": "clear_male",
        "label": "清晰男声",
        "prompt_wav": "zhu_wenjun_16k.wav",
        "prompt_text": "You are a helpful assistant.<|endofprompt|>你好，欢迎使用语音克隆系统。",
    },
    {
        "id": "cartoon_angry",
        "label": "动画夸张声",
        "prompt_wav": "cartoon_angry_16k.wav",
        "prompt_text": "You are a helpful assistant.<|endofprompt|>你们干嘛呢！",
    },
]

SENTENCES = [
    {"id": "welcome", "text": "你好，欢迎使用语音合成与音色克隆演示系统。"},
    {"id": "sunny", "text": "今天的阳光很好，我们一起完成这个有趣的语音项目。"},
    {"id": "ai_voice", "text": "人工智能正在让声音交互变得更加自然。"},
    {"id": "en_welcome", "text": "Hello, welcome to the multilingual voice cloning demo."},
    {"id": "en_story", "text": "Today is a great day to build something creative with AI voices."},
    {"id": "en_assistant", "text": "This system can generate natural speech in different languages."},
    {"id": "en_mixed", "text": "Now let's try a short English sentence with a cloned voice."},
]

EMOTIONS = [
    {
        "id": "neutral",
        "label": "自然",
        "instruction": "You are a helpful assistant. 请自然地说这句话。<|endofprompt|>",
    },
    {
        "id": "happy",
        "label": "开心",
        "instruction": "You are a helpful assistant. 请非常开心地说这句话。<|endofprompt|>",
    },
    {
        "id": "sad",
        "label": "伤心",
        "instruction": "You are a helpful assistant. 请非常伤心地说这句话。<|endofprompt|>",
    },
    {
        "id": "angry",
        "label": "生气",
        "instruction": "You are a helpful assistant. 请非常生气地说这句话。<|endofprompt|>",
    },
]

SPEEDS = [
    {"id": "slow", "label": "慢速", "value": 0.8},
    {"id": "normal", "label": "正常", "value": 1.0},
    {"id": "fast", "label": "快速", "value": 1.2},
    {"id": "very_fast", "label": "很快", "value": 1.5},
]


def get_presets():
    return {
        "voices": VOICES,
        "sentences": SENTENCES,
        "emotions": EMOTIONS,
        "speeds": SPEEDS,
    }


def find_by_id(items, item_id):
    for item in items:
        if item["id"] == item_id:
            return item
    raise KeyError(item_id)
