const state = {
  presets: null,
  results: [],
};

const panels = {
  fixed: document.querySelector("#panel-fixed"),
  clone: document.querySelector("#panel-clone"),
  compare: document.querySelector("#panel-compare"),
  results: document.querySelector("#panel-results"),
};

const controlTokens = [
  { label: "换气", insert: "[breath]" },
  { label: "急促换气", insert: "[quick_breath]" },
  { label: "噪声", insert: "[noise]" },
  { label: "笑声", insert: "[laughter]" },
  { label: "咳嗽", insert: "[cough]" },
  { label: "咂舌", insert: "[clucking]" },
  { label: "口音", insert: "[accent]" },
  { label: "嘶声", insert: "[hissing]" },
  { label: "叹气", insert: "[sigh]" },
  { label: "人声噪音", insert: "[vocalized-noise]" },
  { label: "抿嘴", insert: "[lipsmack]" },
  { label: "嗯", insert: "[mn]" },
  { label: "强调", open: "<strong>", close: "</strong>" },
  { label: "笑着说", open: "<laughter>", close: "</laughter>" },
];

document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", () => showPanel(button.dataset.panel));
});

document.querySelector("#fixed-form").addEventListener("submit", submitFixed);
document.querySelector("#clone-form").addEventListener("submit", submitClone);
document.querySelector("#compare-form").addEventListener("submit", submitCompare);
document.querySelector("#fixed-sentence").addEventListener("change", fillFixedTextFromSelectedSentence);
document.querySelector("#compare-emotion").addEventListener("change", applyFastSpeech2EmotionPreset);
["pitch", "energy", "duration"].forEach((name) => {
  document.querySelector(`#compare-${name}`).addEventListener("input", updateFastSpeech2ControlOutputs);
});
renderTokenToolbars();

loadPresets();

async function loadPresets() {
  const status = document.querySelector("#preset-status");
  try {
    const response = await fetch("/api/presets");
    if (!response.ok) throw new Error("无法加载预设。");
    state.presets = await response.json();
    fillSelect(document.querySelector("#fixed-voice"), state.presets.voices, "label");
    fillSelect(document.querySelector("#fixed-sentence"), state.presets.sentences, "text");
    fillSelect(document.querySelector("#fixed-emotion"), state.presets.emotions, "label");
    fillSelect(document.querySelector("#clone-emotion"), state.presets.emotions, "label");
    fillSelect(document.querySelector("#fixed-speed"), state.presets.speeds, "label");
    fillSelect(document.querySelector("#compare-cosy-voice"), state.presets.voices, "label");
    fillSelect(document.querySelector("#compare-fast-speaker"), state.presets.fastspeech2.speakers, "label", "speaker_id");
    fillSelect(document.querySelector("#compare-emotion"), state.presets.emotions, "label");
    fillSelect(document.querySelector("#compare-cosy-speed"), state.presets.speeds, "label");
    fillFixedTextFromSelectedSentence();
    applyFastSpeech2EmotionPreset();
    status.textContent = "预设已加载";
  } catch (error) {
    status.textContent = "预设加载失败";
    showError("fixed", error.message);
  }
}

function fillSelect(select, items, labelKey, valueKey = "id") {
  select.innerHTML = "";
  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item[valueKey];
    option.textContent = item[labelKey];
    select.appendChild(option);
  });
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "生成失败。");
  return data;
}

async function submitFixed(event) {
  event.preventDefault();
  const button = event.submitter;
  setBusy(button, true);
  clearMessage("fixed");
  const text = document.querySelector("#fixed-text").value.trim();
  if (!text) {
    showError("fixed", "请输入要合成的说话内容。");
    setBusy(button, false);
    return;
  }
  try {
    showGenerating("fixed-output", "正在合成音频");
    const data = await postJson("/api/tts/fixed", {
      voice_id: document.querySelector("#fixed-voice").value,
      text,
      emotion_id: document.querySelector("#fixed-emotion").value,
      speed_id: document.querySelector("#fixed-speed").value,
    });
    renderAudio("fixed-output", "合成音频", data.audio_url);
    addResult("语音合成", data);
    showSuccess("fixed", "生成成功。");
  } catch (error) {
    showError("fixed", error.message);
    renderGenerationError("fixed-output", error.message);
  } finally {
    setBusy(button, false);
  }
}

async function submitClone(event) {
  event.preventDefault();
  const button = event.submitter;
  const file = document.querySelector("#clone-audio").files[0];
  clearMessage("clone");
  if (!file) {
    showError("clone", "请先上传参考音频。");
    return;
  }

  const formData = new FormData();
  formData.append("prompt_audio", file);
  formData.append("prompt_text", document.querySelector("#clone-prompt-text").value.trim());
  formData.append("text", document.querySelector("#clone-text").value);
  formData.append("speed", document.querySelector("#clone-speed").value);
  formData.append("emotion_id", document.querySelector("#clone-emotion").value);

  setBusy(button, true);
  try {
    showGenerating("clone-output", "正在克隆音色");
    const response = await fetch("/api/tts/clone", { method: "POST", body: formData });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "生成失败。");
    renderAudio("clone-output", "克隆音频", data.audio_url);
    addResult("音色克隆", data);
    showSuccess("clone", "生成成功。");
  } catch (error) {
    showError("clone", error.message);
    renderGenerationError("clone-output", error.message);
  } finally {
    setBusy(button, false);
  }
}

function applyFastSpeech2EmotionPreset() {
  if (!state.presets) return;
  const emotionId = document.querySelector("#compare-emotion").value;
  const controls = state.presets.fastspeech2.emotion_controls;
  const preset = controls[emotionId] || controls.neutral;
  document.querySelector("#compare-pitch").value = preset.pitch;
  document.querySelector("#compare-energy").value = preset.energy;
  document.querySelector("#compare-duration").value = preset.duration;
  updateFastSpeech2ControlOutputs();
}

function updateFastSpeech2ControlOutputs() {
  ["pitch", "energy", "duration"].forEach((name) => {
    const value = Number(document.querySelector(`#compare-${name}`).value);
    document.querySelector(`#compare-${name}-value`).textContent = value.toFixed(2);
  });
}

async function submitCompare(event) {
  event.preventDefault();
  const button = event.submitter;
  clearMessage("compare");
  const text = document.querySelector("#compare-text").value.trim();
  if (!text) {
    showError("compare", "请输入要对比合成的文本。");
    return;
  }

  setBusy(button, true);
  try {
    showCompareGenerating();
    const data = await postJson("/api/tts/compare", {
      text,
      cosyvoice_voice_id: document.querySelector("#compare-cosy-voice").value,
      fastspeech2_speaker_id: Number(document.querySelector("#compare-fast-speaker").value),
      emotion_id: document.querySelector("#compare-emotion").value,
      cosyvoice_speed_id: document.querySelector("#compare-cosy-speed").value,
      pitch_control: Number(document.querySelector("#compare-pitch").value),
      energy_control: Number(document.querySelector("#compare-energy").value),
      duration_control: Number(document.querySelector("#compare-duration").value),
    });
    renderCompareResult(data);
    if (data.cosyvoice) addResult("CosyVoice3 对比", data.cosyvoice);
    if (data.fastspeech2) addResult("FastSpeech2 对比", data.fastspeech2);
    showSuccess("compare", "对比生成完成。");
  } catch (error) {
    showError("compare", error.message);
    renderGenerationError("compare-output", error.message);
  } finally {
    setBusy(button, false);
  }
}

function showCompareGenerating() {
  document.querySelector("#compare-output").innerHTML = `
    <div class="generation-card" role="status" aria-live="polite">
      <div class="generation-copy">
        <strong>正在生成对比音频</strong>
        <span>两个模型会依次推理，请稍等。</span>
      </div>
      <div class="generation-progress" aria-hidden="true"><span></span></div>
    </div>
  `;
}

function setText(selector, value) {
  const node = document.querySelector(selector);
  if (node) node.textContent = value;
}

function renderCompareResult(data) {
  document.querySelector("#compare-output").innerHTML = `
    <div class="compare-grid-output">
      <div class="compare-model" id="compare-cosy-output"></div>
      <div class="compare-model" id="compare-fast-output"></div>
    </div>
  `;
  if (data.cosyvoice) {
    renderAudio("compare-cosy-output", "CosyVoice3", data.cosyvoice.audio_url);
  }
  if (data.fastspeech2) {
    renderAudio("compare-fast-output", "FastSpeech2", data.fastspeech2.audio_url);
  } else {
    document.querySelector("#compare-fast-output").innerHTML = `
      <div class="generation-card error-card" role="alert">
        <div class="generation-copy">
          <strong>FastSpeech2 暂不可用</strong>
          <span id="compare-fast-error"></span>
        </div>
      </div>
    `;
    setText("#compare-fast-error", data.fastspeech2_error || "模型文件未准备完成。");
  }
}

function addResult(kind, response) {
  state.results.unshift({
    id: crypto.randomUUID(),
    kind,
    filename: response.filename,
    audio_url: response.audio_url,
    time: new Date().toLocaleTimeString(),
  });
  renderResults();
}

function renderResults() {
  const list = document.querySelector("#result-list");
  if (state.results.length === 0) {
    list.innerHTML = '<p class="empty">还没有生成结果。</p>';
    return;
  }
  list.innerHTML = state.results
    .map(
      (item) => `
        <article class="result-item">
          <div class="custom-player" data-audio-id="result-${item.id}">
            <div class="player-topline">
              <strong>${item.kind} - ${item.time}</strong>
              <span class="player-state">${item.filename}</span>
            </div>
            <div class="player-controls">
              <button class="player-button" type="button" aria-label="播放或暂停">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path class="play-icon" d="M8 5v14l11-7z"></path>
                  <path class="pause-icon" d="M7 5h4v14H7zM13 5h4v14h-4z"></path>
                </svg>
              </button>
              <span class="player-time current">0:00</span>
              <input class="player-progress" type="range" min="0" max="100" value="0" aria-label="音频播放进度">
              <span class="player-time duration">0:00</span>
            </div>
            <audio id="result-${item.id}" preload="metadata" src="${item.audio_url}"></audio>
          </div>
        </article>
      `
    )
    .join("");
  list.querySelectorAll(".custom-player").forEach(setupCustomPlayer);
}

function renderAudio(targetId, title, audioUrl) {
  const id = `audio-${crypto.randomUUID()}`;
  document.querySelector(`#${targetId}`).innerHTML = `
    <div class="custom-player" data-audio-id="${id}">
      <div class="player-topline">
        <strong>${title}</strong>
        <span class="player-state">Ready</span>
      </div>
      <div class="player-controls">
        <button class="player-button" type="button" aria-label="播放或暂停">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path class="play-icon" d="M8 5v14l11-7z"></path>
            <path class="pause-icon" d="M7 5h4v14H7zM13 5h4v14h-4z"></path>
          </svg>
        </button>
        <span class="player-time current">0:00</span>
        <input class="player-progress" type="range" min="0" max="100" value="0" aria-label="音频播放进度">
        <span class="player-time duration">0:00</span>
      </div>
      <audio id="${id}" preload="metadata" src="${audioUrl}"></audio>
    </div>
  `;
  setupCustomPlayer(document.querySelector(`#${targetId} .custom-player`), { autoplay: true });
}

function showGenerating(targetId, title) {
  document.querySelector(`#${targetId}`).innerHTML = `
    <div class="generation-card" role="status" aria-live="polite">
      <div class="generation-copy">
        <strong>${title}</strong>
        <span>模型加载、音频转换和推理会依次进行，请稍等。</span>
      </div>
      <div class="generation-visual" aria-hidden="true">
        <span></span><span></span><span></span><span></span><span></span><span></span>
        <span></span><span></span><span></span><span></span>
      </div>
      <div class="generation-progress" aria-hidden="true"><span></span></div>
    </div>
  `;
}

function renderGenerationError(targetId, message) {
  document.querySelector(`#${targetId}`).innerHTML = `
    <div class="generation-card error-card" role="alert">
      <div class="generation-copy">
        <strong>生成失败</strong>
        <span id="${targetId}-error-message"></span>
      </div>
    </div>
  `;
  setText(`#${targetId}-error-message`, message);
}

function renderTokenToolbars() {
  document.querySelectorAll(".token-toolbar").forEach((toolbar) => {
    toolbar.innerHTML = "";
    controlTokens.forEach((token) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "token-button";
      button.textContent = token.label;
      button.title = token.open ? `${token.open}${token.close}` : token.insert;
      button.addEventListener("click", () => {
        const textarea = document.querySelector(`#${toolbar.dataset.target}`);
        insertControlToken(textarea, token);
      });
      toolbar.appendChild(button);
    });
  });
}

function insertControlToken(textarea, token) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const before = textarea.value.slice(0, start);
  const selected = textarea.value.slice(start, end);
  const after = textarea.value.slice(end);

  if (token.open && token.close) {
    textarea.value = `${before}${token.open}${selected}${token.close}${after}`;
    const cursorStart = start + token.open.length;
    const cursorEnd = cursorStart + selected.length;
    textarea.focus();
    textarea.setSelectionRange(cursorStart, cursorEnd);
    return;
  }

  textarea.value = `${before}${token.insert}${after}`;
  const cursor = start + token.insert.length;
  textarea.focus();
  textarea.setSelectionRange(cursor, cursor);
}

function fillFixedTextFromSelectedSentence() {
  if (!state.presets) return;
  const sentenceId = document.querySelector("#fixed-sentence").value;
  const sentence = state.presets.sentences.find((item) => item.id === sentenceId);
  if (sentence) {
    document.querySelector("#fixed-text").value = sentence.text;
  }
}

function setupCustomPlayer(player, options = {}) {
  const audio = player.querySelector("audio");
  const button = player.querySelector(".player-button");
  const progress = player.querySelector(".player-progress");
  const current = player.querySelector(".current");
  const duration = player.querySelector(".duration");
  const state = player.querySelector(".player-state");
  const { autoplay = false } = options;

  const updateProgressFill = () => {
    progress.style.setProperty("--progress", `${progress.value}%`);
  };

  button.addEventListener("click", async () => {
    if (audio.paused) {
      pauseOtherAudio(audio);
      await audio.play();
    } else {
      audio.pause();
    }
  });

  audio.addEventListener("loadedmetadata", () => {
    duration.textContent = formatTime(audio.duration);
    updateProgressFill();
  });

  audio.addEventListener("play", () => {
    player.classList.add("is-playing");
    state.textContent = "Playing";
  });

  audio.addEventListener("pause", () => {
    player.classList.remove("is-playing");
    state.textContent = "Paused";
  });

  audio.addEventListener("ended", () => {
    player.classList.remove("is-playing");
    state.textContent = "Complete";
    progress.value = 100;
    updateProgressFill();
  });

  audio.addEventListener("timeupdate", () => {
    if (!Number.isFinite(audio.duration) || audio.duration === 0) return;
    const value = (audio.currentTime / audio.duration) * 100;
    progress.value = value;
    current.textContent = formatTime(audio.currentTime);
    updateProgressFill();
  });

  progress.addEventListener("input", () => {
    if (!Number.isFinite(audio.duration) || audio.duration === 0) return;
    audio.currentTime = (Number(progress.value) / 100) * audio.duration;
    updateProgressFill();
  });

  if (autoplay) {
    pauseOtherAudio(audio);
    audio.play().catch(() => {
      state.textContent = "Ready";
    });
  }
}

function pauseOtherAudio(currentAudio) {
  document.querySelectorAll("audio").forEach((audio) => {
    if (audio !== currentAudio && !audio.paused) {
      audio.pause();
    }
  });
}

function formatTime(seconds) {
  if (!Number.isFinite(seconds)) return "0:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60).toString().padStart(2, "0");
  return `${mins}:${secs}`;
}

function showPanel(name) {
  Object.entries(panels).forEach(([key, panel]) => {
    panel.classList.toggle("active", key === name);
  });
  document.querySelectorAll(".nav-item").forEach((button) => {
    button.classList.toggle("active", button.dataset.panel === name);
  });
}

function showError(panel, message) {
  const node = document.querySelector(`#${panel}-message`);
  node.textContent = message;
  node.className = "message error";
}

function showSuccess(panel, message) {
  const node = document.querySelector(`#${panel}-message`);
  node.textContent = message;
  node.className = "message success";
}

function clearMessage(panel) {
  const node = document.querySelector(`#${panel}-message`);
  node.textContent = "";
  node.className = "message";
}

function setBusy(button, busy) {
  button.disabled = busy;
  button.dataset.originalText ||= button.textContent;
  button.textContent = busy ? "生成中..." : button.dataset.originalText;
}
