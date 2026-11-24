'use strict';

function frameAtTime(seconds, totalFrames, fps = 30) {
  // Local WAV seeks can be rounded to microseconds by the browser.
  const halfAudioSample = 0.5 / 48000;
  return Math.min(totalFrames - 1, Math.max(0, Math.floor((seconds + halfAudioSample) * fps)));
}

function layerState(frame, layer, timeline) {
  const state = { visible: false, opacity: 1, x: layer.x, y: layer.y };
  const scene = timeline.scenes.find(item => item.id === layer.scene_id);
  if (!scene || frame < scene.start_frame || frame >= scene.end_frame) return state;
  if (layer.mode === 'base') return { ...state, visible: true };
  const event = timeline.events[layer.event_id];
  if (frame < event.start_frame) return state;
  const offset = frame - event.start_frame;
  const length = event.end_frame - event.start_frame;
  if (layer.mode === 'reveal') {
    return { ...state, visible: true, opacity: Math.min(1, (offset + 1) / length) };
  }
  const end = layer.mode === 'caption' ? Math.ceil(event.speech_samples / 1600) : length;
  if (offset >= end) return state;
  if (layer.mode !== 'travel') return { ...state, visible: true };
  const progress = offset / (length - 1);
  return {
    visible: true,
    opacity: 1,
    x: Math.floor(layer.x + (layer.to_x - layer.x) * progress + .5),
    y: Math.floor(layer.y + (layer.to_y - layer.y) * progress + .5)
  };
}

function loadImage(path) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('画面文件无法读取 ' + path));
    img.src = path;
  });
}

function formatTime(seconds) {
  const whole = Math.max(0, Math.floor(seconds));
  return Math.floor(whole / 60) + ':' + String(whole % 60).padStart(2, '0');
}

async function startDeck() {
  const timeline = JSON.parse(document.getElementById('timeline-data').textContent);
  const audio = document.querySelector('audio');
  const canvas = document.querySelector('canvas');
  const ctx = canvas.getContext('2d');
  const buttons = [...document.querySelectorAll('.chapter')];
  const play = document.getElementById('play');
  const next = document.getElementById('next');
  const previous = document.getElementById('previous');
  const seek = document.getElementById('seek');
  const status = document.getElementById('status');
  const time = document.getElementById('time');
  const caption = document.getElementById('caption');
  const duration = timeline.total_frames / timeline.fps;
  const layers = [...timeline.layers].sort((a, b) => a.z - b.z);
  const imageList = await Promise.all(layers.map(layer => loadImage(layer.file)));
  let sceneIndex = 0;
  let lastFrame = -1;
  let animation = null;
  seek.max = String(duration);

  function paint(seconds) {
    const frame = frameAtTime(seconds, timeline.total_frames, timeline.fps);
    const position = timeline.scenes.findIndex(scene => frame >= scene.start_frame && frame < scene.end_frame);
    if (position < 0) return;
    seek.value = String(seconds);
    time.value = formatTime(seconds);
    if (lastFrame === frame) return;
    lastFrame = frame;
    sceneIndex = position;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    let spokenCaption = '';
    for (const [index, layer] of layers.entries()) {
      const state = layerState(frame, layer, timeline);
      if (!state.visible) continue;
      ctx.globalAlpha = state.opacity;
      ctx.drawImage(imageList[index], state.x, state.y);
      if (layer.mode === 'caption') spokenCaption = timeline.events[layer.event_id].caption;
    }
    ctx.globalAlpha = 1;
    if (caption.textContent !== spokenCaption) caption.textContent = spokenCaption;
    for (const [index, button] of buttons.entries()) {
      button.setAttribute('aria-current', String(index === sceneIndex));
    }
    canvas.setAttribute('aria-label', timeline.scenes[sceneIndex].title);
    previous.disabled = sceneIndex === 0;
    next.disabled = sceneIndex === timeline.scenes.length - 1;
  }

  function seekTo(seconds) {
    audio.currentTime = seconds;
    paint(seconds);
  }

  function tick() {
    paint(audio.currentTime);
    animation = audio.paused ? null : requestAnimationFrame(tick);
  }

  function select(index) {
    if (index < 0 || index >= timeline.scenes.length) return;
    audio.pause();
    seekTo(timeline.scenes[index].start_frame / timeline.fps);
  }

  audio.addEventListener('play', () => {
    play.textContent = '暂停';
    if (animation === null) tick();
  });
  audio.addEventListener('pause', () => {
    play.textContent = audio.ended ? '从头播放' : '播放旁白';
    if (animation !== null) cancelAnimationFrame(animation);
    animation = null;
    paint(audio.currentTime);
  });
  audio.addEventListener('ended', () => {
    play.textContent = '从头播放';
    paint(duration);
  });
  audio.addEventListener('seeked', () => paint(audio.currentTime));
  audio.addEventListener('error', () => {
    status.hidden = false;
    status.textContent = '旁白无法播放。请确认演示目录中的 narration.wav 可用。';
  });
  play.addEventListener('click', async () => {
    if (!audio.paused) {
      audio.pause();
      return;
    }
    if (audio.ended) seekTo(0);
    try {
      await audio.play();
    } catch (error) {
      status.hidden = false;
      status.textContent = '浏览器无法播放旁白。' + error.message;
    }
  });
  seek.addEventListener('input', () => seekTo(Number(seek.value)));
  next.addEventListener('click', () => select(sceneIndex + 1));
  previous.addEventListener('click', () => select(sceneIndex - 1));
  for (const [index, button] of buttons.entries()) {
    button.addEventListener('click', () => select(index));
  }
  document.addEventListener('keydown', event => {
    if (event.target instanceof HTMLInputElement || event.altKey || event.metaKey || event.ctrlKey) return;
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      select(sceneIndex + (event.key === 'ArrowRight' ? 1 : -1));
    }
  });
  paint(0);
  play.disabled = false;
}

if (typeof module !== 'undefined') module.exports = { frameAtTime, layerState };
if (typeof document !== 'undefined') {
  startDeck().catch(error => {
    const status = document.getElementById('status');
    status.hidden = false;
    status.textContent = error.message;
  });
}
