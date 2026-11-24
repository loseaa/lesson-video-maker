"use strict";

(async function initialize() {
  try {
    const get = id => document.getElementById(id);
    const timeline = JSON.parse(get("explainer-timing").textContent);
    const viewport = get("explainer-viewport");
    const stage = get("explainer-stage");
    const audio = get("explainer-audio");
    const caption = get("explainer-caption");
    const progress = get("explainer-seek");
    const play = get("explainer-play");
    const timeLabel = get("explainer-time");
    const chapters = get("explainer-chapters");
    const capture = new URLSearchParams(location.search).has("capture");
    const regions = [...stage.querySelectorAll(":scope > [data-scene]")];
    const byScene = new Map(regions.map(region => [region.dataset.scene, region]));
    const events = Object.values(timeline.events);
    const spoken = events.filter(event => event.type === "speak");
    const duration = timeline.total_frames / timeline.fps;
    const draw = window.drawExplainerScene;

    if (regions.length !== timeline.scenes.length || byScene.size !== regions.length ||
        timeline.scenes.some(scene => !byScene.has(scene.id))) {
      throw Error("scenes.html needs one direct scene section per scene id in timeline.jsonl");
    }
    if (typeof draw !== "function") throw Error("scenes.js must define window.drawExplainerScene");
    for (const event of events.filter(event => event.type === "html_motion")) {
      const target = get(event.target);
      if (!target || !byScene.get(event.scene_id).contains(target)) {
        throw Error(event.id + ": missing target #" + event.target + " inside scene " + event.scene_id);
      }
    }

    document.body.classList.toggle("explainer-capture", capture);
    await window.explainerAssetsReady;
    const toTime = seconds => {
      const n = Math.floor(seconds);
      return Math.floor(n / 60) + ":" + String(n % 60).padStart(2, "0");
    };

    function fit() {
      stage.style.transform = "scale(" + (viewport.clientWidth / 1600) + ")";
    }

    let shown;
    let lastFrame = -1;
    function render(rawFrame) {
      if (!Number.isFinite(rawFrame)) throw Error("Invalid presentation frame");
      const frame = Math.min(timeline.total_frames - 1, Math.max(0, Math.floor(rawFrame)));
      const scene = timeline.scenes.find(s => frame >= s.start_frame && frame < s.end_frame);
      if (frame === lastFrame) return scene.id;
      const region = byScene.get(scene.id);
      if (shown !== region) {
        for (const item of regions) item.hidden = item !== region;
        shown = region;
      }
      const motion = id => {
        const event = timeline.events[id];
        if (!event || event.type !== "html_motion") throw Error("Unknown HTML motion " + id);
        const progress = Math.min(1, Math.max(0,
          (frame - event.start_frame) / (event.end_frame - event.start_frame - 1)));
        return { progress, started: frame >= event.start_frame, active: frame >= event.start_frame && frame < event.end_frame };
      };
      draw({ scene: scene.id, root: region, frame, time: frame / timeline.fps,
             sceneTime: (frame - scene.start_frame) / timeline.fps, motion });
      const sample = frame * 48000 / timeline.fps;
      const cue = spoken.find(item => sample + .5 >= item.audio_offset_samples &&
        sample + .5 < item.audio_offset_samples + item.speech_samples);
      caption.textContent = cue?.caption ?? "";
      if (!capture) {
        progress.value = frame / timeline.fps;
        timeLabel.textContent = toTime(frame / timeline.fps) + " / " + toTime(duration);
        for (const button of chapters.children) {
          button.setAttribute("aria-current", button.dataset.scene === scene.id ? "step" : "false");
        }
      }
      lastFrame = frame;
      return scene.id;
    }

    const fromAudio = seconds => render((seconds + .5 / 48000) * timeline.fps);
    const seek = seconds => {
      if (audio.readyState) audio.currentTime = seconds;
      fromAudio(seconds);
    };
    if (!capture) {
      progress.max = duration;
      timeline.scenes.forEach((scene, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = String(index + 1) + " · " + scene.title;
        button.dataset.scene = scene.id;
        button.addEventListener("click", () => seek(scene.start_frame / timeline.fps));
        chapters.append(button);
      });
      progress.addEventListener("input", () => seek(Number(progress.value)));
      play.addEventListener("click", () => {
        if (audio.paused) {
          if (audio.ended) seek(0);
          audio.play().catch(() => { timeLabel.textContent = "音频无法播放"; });
        } else audio.pause();
      });
      let raf = null;
      const tick = () => {
        raf = null;
        fromAudio(audio.currentTime);
        if (!audio.paused) raf = requestAnimationFrame(tick);
      };
      audio.addEventListener("play", () => {
        play.textContent = "暂停";
        if (raf === null) tick();
      });
      audio.addEventListener("pause", () => {
        if (raf !== null) cancelAnimationFrame(raf);
        raf = null;
        play.textContent = "播放";
        fromAudio(audio.currentTime);
      });
      audio.addEventListener("seeked", () => fromAudio(audio.currentTime));
      audio.addEventListener("ended", () => { play.textContent = "重播"; fromAudio(duration); });
    }
    fit();
    new ResizeObserver(fit).observe(viewport);
    render(0);
    window.renderExplainerFrame = render;
    window.explainerCoverFrame = Math.max(0, Math.floor(timeline.scenes[0].end_frame * .6));
  } catch (error) {
    window.explainerError = error.message;
    document.getElementById("explainer-time").textContent = error.message;
  }
})();
