import os
import re
import sys
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import numpy as np
import torch
import yaml
from scipy.io import wavfile

from backend.config import (
    FASTSPEECH2_ASSET_DIR,
    FASTSPEECH2_RUNTIME_DIR,
    OUTPUT_DIR,
)


class FastSpeech2AssetError(RuntimeError):
    pass


@dataclass
class FastSpeech2Controls:
    pitch: float = 1.0
    energy: float = 1.0
    duration: float = 1.0

    def clamped(self):
        return FastSpeech2Controls(
            pitch=min(1.5, max(0.5, self.pitch)),
            energy=min(1.5, max(0.5, self.energy)),
            duration=min(1.5, max(0.5, self.duration)),
        )


class FastSpeech2Service:
    def __init__(
        self,
        runtime_dir: Path = FASTSPEECH2_RUNTIME_DIR,
        asset_dir: Path = FASTSPEECH2_ASSET_DIR,
    ):
        self.runtime_dir = Path(runtime_dir)
        self.asset_dir = Path(asset_dir)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model = None
        self._vocoder = None
        self._configs = None
        self._modules_loaded = False
        self._runtime_lock = threading.RLock()

    @property
    def ckpt_path(self):
        return self.asset_dir / "ckpt" / "600000.pth.tar"

    @property
    def hifigan_path(self):
        return self.asset_dir / "hifigan" / "generator_universal.pth.tar"

    def validate_assets(self):
        if not self.runtime_dir.exists():
            raise FastSpeech2AssetError("FastSpeech2 runtime 未准备完成，请确认 third_party/FastSpeech2 已迁移。")
        if not (self.runtime_dir / "model" / "fastspeech2.py").exists():
            raise FastSpeech2AssetError("FastSpeech2 runtime 缺少 model/fastspeech2.py。")
        if not (self.runtime_dir / "lexicon" / "pinyin-lexicon-r.txt").exists():
            raise FastSpeech2AssetError("FastSpeech2 runtime 缺少中文拼音词典。")
        if not self.ckpt_path.exists():
            raise FastSpeech2AssetError("FastSpeech2 AISHELL3 模型文件缺失，请下载 600000.pth.tar。")
        if not self.hifigan_path.exists():
            raise FastSpeech2AssetError("FastSpeech2 HiFi-GAN vocoder 缺失，请解压 generator_universal.pth.tar。")

    def _load_runtime_modules(self):
        if self._modules_loaded:
            return
        if str(self.runtime_dir) not in sys.path:
            sys.path.insert(0, str(self.runtime_dir))
        self._modules_loaded = True

    @contextmanager
    def _runtime_cwd(self):
        with self._runtime_lock:
            old_cwd = Path.cwd()
            os.chdir(self.runtime_dir)
            try:
                yield
            finally:
                os.chdir(old_cwd)

    def _load_configs(self):
        if self._configs is not None:
            return self._configs

        with open(self.runtime_dir / "config" / "AISHELL3" / "preprocess.yaml", "r") as file:
            preprocess_config = yaml.load(file, Loader=yaml.FullLoader)
        with open(self.runtime_dir / "config" / "AISHELL3" / "model.yaml", "r") as file:
            model_config = yaml.load(file, Loader=yaml.FullLoader)
        with open(self.runtime_dir / "config" / "AISHELL3" / "train.yaml", "r") as file:
            train_config = yaml.load(file, Loader=yaml.FullLoader)

        train_config["path"]["ckpt_path"] = str(self.asset_dir / "ckpt")
        train_config["path"]["result_path"] = str(OUTPUT_DIR)
        self._configs = (preprocess_config, model_config, train_config)
        return self._configs

    def _read_lexicon(self, lex_path):
        lexicon = {}
        with open(lex_path, "r") as file:
            for line in file:
                parts = re.split(r"\s+", line.strip("\n"))
                if parts and parts[0]:
                    lexicon[parts[0].lower()] = parts[1:]
        return lexicon

    def _load_model_and_vocoder(self):
        if self._model is not None and self._vocoder is not None:
            return

        self.validate_assets()
        self._load_runtime_modules()
        with self._runtime_cwd():
            from utils.model import get_model, get_vocoder

            configs = self._load_configs()

            class Args:
                restore_step = 600000

            runtime_vocoder = self.runtime_dir / "hifigan" / "generator_universal.pth.tar"
            if not runtime_vocoder.exists():
                runtime_vocoder.symlink_to(self.hifigan_path)
            self._model = get_model(Args(), configs, self.device, train=False)
            self._vocoder = get_vocoder(configs[1], self.device)

    def _preprocess_text(self, text):
        self._load_runtime_modules()
        try:
            from text import text_to_sequence
        except ModuleNotFoundError as exc:
            raise FastSpeech2AssetError(f"FastSpeech2 依赖缺失: {exc.name}，请先安装 FastSpeech2 requirements。") from exc
        try:
            from pypinyin import Style, pinyin
        except ModuleNotFoundError as exc:
            raise FastSpeech2AssetError("FastSpeech2 依赖缺失: pypinyin，请先安装 FastSpeech2 requirements。") from exc

        preprocess_config = self._load_configs()[0]
        language = preprocess_config["preprocessing"]["text"]["language"]
        if language != "zh":
            raise ValueError("当前 FastSpeech2 集成只支持 AISHELL3 中文模型。")
        lexicon_path = self.runtime_dir / preprocess_config["path"]["lexicon_path"]
        lexicon = self._read_lexicon(lexicon_path)
        phones = []
        pinyins = [
            item[0]
            for item in pinyin(
                text,
                style=Style.TONE3,
                strict=False,
                neutral_tone_with_five=True,
            )
        ]
        for item in pinyins:
            if item in lexicon:
                phones += lexicon[item]
            else:
                phones.append("sp")
        phones = "{" + " ".join(phones) + "}"
        sequence = text_to_sequence(phones, preprocess_config["preprocessing"]["text"]["text_cleaners"])
        return np.array([sequence])

    def _synthesize_waveform(self, text, speaker_id, controls):
        with self._runtime_lock:
            self._load_model_and_vocoder()
            self._load_runtime_modules()
            from utils.model import vocoder_infer
            from utils.tools import to_device

            controls = controls.clamped()
            texts = self._preprocess_text(text)
            text_lens = np.array([len(texts[0])])
            batch = (
                [text[:100]],
                [text],
                np.array([speaker_id]),
                texts,
                text_lens,
                max(text_lens),
            )
            batch = to_device(batch, self.device)

            with torch.no_grad(), self._runtime_cwd():
                output = self._model(
                    *(batch[2:]),
                    p_control=controls.pitch,
                    e_control=controls.energy,
                    d_control=controls.duration,
                )
                mel_predictions = output[1].transpose(1, 2)
                lengths = output[9] * self._load_configs()[0]["preprocessing"]["stft"]["hop_length"]
                wav = vocoder_infer(
                    mel_predictions,
                    self._vocoder,
                    self._load_configs()[1],
                    self._load_configs()[0],
                    lengths=lengths,
                )[0]

            sample_rate = self._load_configs()[0]["preprocessing"]["audio"]["sampling_rate"]
            return sample_rate, wav

    def synthesize(self, text: str, speaker_id: int, controls: FastSpeech2Controls) -> str:
        text = text.strip()
        if not text:
            raise ValueError("请输入要合成的文本。")

        controls = controls.clamped()
        sample_rate, wav = self._synthesize_waveform(text, speaker_id, controls)
        filename = f"fastspeech2_{uuid4().hex}.wav"
        wavfile.write(str(OUTPUT_DIR / filename), sample_rate, wav)
        return filename


fastspeech2_service = FastSpeech2Service()
