const test = require('node:test');
const assert = require('node:assert/strict');
const { frameAtTime, layerState } = require('../lesson_video_maker/player.js');

test('seeking uses actual frames and hides an unreached cue', () => {
  const timeline = {
    scenes: [{ id: 'scene', start_frame: 0, end_frame: 76 }],
    events: { arrow: { start_frame: 31, end_frame: 60 } },
  };
  const arrow = { scene_id: 'scene', event_id: 'arrow', mode: 'reveal', x: 0, y: 0 };
  assert.equal(frameAtTime(1.04, 76), 31);
  assert.equal(layerState(31, arrow, timeline).visible, true);
  assert.equal(layerState(30, arrow, timeline).visible, false);
  assert.equal(layerState(60, arrow, timeline).opacity, 1);
});

test('a seek rounded to microseconds still selects the chapter frame', () => {
  assert.equal(frameAtTime(12.333333, 601), 370);
  assert.equal(frameAtTime(12.33, 601), 369);
});
