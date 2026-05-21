const assert = require("assert");
const fs = require("fs");
const path = require("path");

const source = fs.readFileSync(path.join(__dirname, "..", "frontend", "app.js"), "utf8");

function extractFunction(name) {
  const start = source.indexOf(`function ${name}`);
  assert.notStrictEqual(start, -1, `${name} should exist`);
  const paramsStart = source.indexOf("(", start);
  let paramsDepth = 0;
  let paramsEnd = -1;
  for (let index = paramsStart; index < source.length; index += 1) {
    if (source[index] === "(") paramsDepth += 1;
    if (source[index] === ")") paramsDepth -= 1;
    if (paramsDepth === 0) {
      paramsEnd = index;
      break;
    }
  }
  const bodyStart = source.indexOf("{", paramsEnd);
  let depth = 0;
  for (let index = bodyStart; index < source.length; index += 1) {
    if (source[index] === "{") depth += 1;
    if (source[index] === "}") depth -= 1;
    if (depth === 0) return source.slice(start, index + 1);
  }
  throw new Error(`Could not extract ${name}`);
}

eval(`${extractFunction("formatTime")}\n${extractFunction("pauseOtherAudio")}\n${extractFunction("setupCustomPlayer")}`);

function createFakePlayer({ paused = true } = {}) {
  const listeners = {};
  const classNames = new Set();
  const audio = {
    paused,
    duration: 10,
    currentTime: 0,
    playCalls: 0,
    pauseCalls: 0,
    addEventListener(event, handler) {
      listeners[`audio:${event}`] = handler;
    },
    play() {
      this.playCalls += 1;
      this.paused = false;
      return Promise.resolve();
    },
    pause() {
      this.pauseCalls += 1;
      this.paused = true;
    },
  };
  const button = {
    addEventListener(event, handler) {
      listeners[`button:${event}`] = handler;
    },
  };
  const progress = {
    value: 0,
    style: {
      setProperty(name, value) {
        progress[name] = value;
      },
    },
    addEventListener(event, handler) {
      listeners[`progress:${event}`] = handler;
    },
  };
  const current = { textContent: "" };
  const duration = { textContent: "" };
  const playerState = { textContent: "" };

  return {
    audio,
    listeners,
    classList: {
      add(name) {
        classNames.add(name);
      },
      remove(name) {
        classNames.delete(name);
      },
      contains(name) {
        return classNames.has(name);
      },
    },
    querySelector(selector) {
      return {
        audio,
        ".player-button": button,
        ".player-progress": progress,
        ".current": current,
        ".duration": duration,
        ".player-state": playerState,
      }[selector];
    },
  };
}

function testPlayerDoesNotAutoplayWhenInitializedForHistory() {
  const player = createFakePlayer();
  global.document = { querySelectorAll: () => [player.audio] };
  setupCustomPlayer(player);
  assert.strictEqual(player.audio.playCalls, 0);
}

function testGeneratedPlayerAutoplaysAndPausesOtherAudio() {
  const oldPlayer = createFakePlayer({ paused: false });
  const newPlayer = createFakePlayer();
  global.document = { querySelectorAll: () => [oldPlayer.audio, newPlayer.audio] };

  setupCustomPlayer(newPlayer, { autoplay: true });

  assert.strictEqual(newPlayer.audio.playCalls, 1);
  assert.strictEqual(oldPlayer.audio.pauseCalls, 1);
}

testPlayerDoesNotAutoplayWhenInitializedForHistory();
testGeneratedPlayerAutoplaysAndPausesOtherAudio();

function testComparisonFunctionsExist() {
  assert(source.includes("function submitCompare"));
  assert(source.includes("function applyFastSpeech2EmotionPreset"));
  assert(source.includes("function renderCompareResult"));
}

testComparisonFunctionsExist();
console.log("frontend player tests passed");
