const test = require("node:test");
const assert = require("node:assert/strict");
require("../lesson_video_maker/html_motion.js");

const { phase, easeOut, easeInOut, focus, pose } = globalThis.explainerMotion;

test("eases entries and returns focus to its resting state after the cue", () => {
  assert.equal(phase(.1, .2, .6), 0);
  assert.equal(phase(.7, .2, .6), 1);
  assert.equal(easeOut(0), 0);
  assert.ok(easeOut(.5) > .5);
  assert.equal(easeInOut(.5), .5);
  assert.equal(focus(0), 0);
  assert.equal(focus(.45), 1);
  assert.equal(focus(1), 0);
});

test("recomputes the same pose after seeking backwards", () => {
  const el = { style: { transform: "rotateY(12deg)" } };
  pose(el, { x: 20, opacity: .5, scale: 1.05 });
  const paused = { ...el.style };
  pose(el, { opacity: 0 });
  pose(el, { x: 20, opacity: .5, scale: 1.05 });
  assert.deepEqual(el.style, paused);
  assert.equal(el.style.transform, "rotateY(12deg)");
});
