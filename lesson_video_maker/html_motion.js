"use strict";

(function exposeMotion() {
  const clamp = value => Math.min(1, Math.max(0, value));

  function phase(progress, start = 0, end = 1) {
    if (!(start < end)) throw new RangeError("Motion phase needs start < end");
    return clamp((progress - start) / (end - start));
  }

  function easeOut(progress) {
    return 1 - (1 - clamp(progress)) ** 3;
  }

  function easeInOut(progress) {
    const p = clamp(progress);
    return p * p * (3 - 2 * p);
  }

  function focus(progress) {
    return easeInOut(phase(progress, 0, .18)) * (1 - easeInOut(phase(progress, .72, 1)));
  }

  function pose(element, { x = 0, y = 0, opacity = 1, scale = 1 } = {}) {
    element.style.translate = x + "px " + y + "px";
    element.style.opacity = String(clamp(opacity));
    element.style.scale = String(scale);
  }

  globalThis.explainerMotion = Object.freeze({ phase, easeOut, easeInOut, focus, pose });
})();
