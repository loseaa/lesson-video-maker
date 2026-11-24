import json
import tempfile
import unittest
import wave
from pathlib import Path

from fixture import rows, write_rows, write_wav
from lesson_video_maker.speech import AudioTrack
from lesson_video_maker.storyboard import load_storyboard
from lesson_video_maker.timeline import build_timeline, load_timeline, write_audio, write_srt, write_timeline


class TimelineTest(unittest.TestCase):
    def test_joins_frames_and_rejects_tampered_offsets(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            path = write_rows(folder / 'draft.jsonl', rows())
            original = path.read_bytes()
            story = load_storyboard(path)
            tracks = {
                'call': AudioTrack(write_wav(folder / 'call.wav', 48001), 48001),
                'result': AudioTrack(write_wav(folder / 'result.wav', 72000), 72000),
            }
            timeline = build_timeline(story, tracks)
            dst = folder / 'resolved.jsonl'
            write_timeline(timeline, dst)
            self.assertEqual(path.read_bytes(), original)
            resolved = load_timeline(dst)
            self.assertEqual([(s.start_frame, s.end_frame) for s in resolved.speech], [(0, 31), (31, 76)])
            self.assertEqual(resolved.speech[1].audio_offset_samples, 49600)
            self.assertEqual(resolved.events['move-request'].end_frame, 31)
            write_audio(resolved, tracks, folder / 'narration.wav')
            with wave.open(str(folder / 'narration.wav')) as result:
                self.assertEqual(result.getnframes(), 76 * 1600)
            write_srt(resolved, folder / 'captions.srt')
            self.assertIn('00:00:01,033 -->', (folder / 'captions.srt').read_text())
            altered = list(map(json.loads, dst.read_text().splitlines()))
            altered[5]['audio_offset_samples'] += 1600
            with self.assertRaisesRegex(ValueError, 'result'):
                load_timeline(write_rows(dst, altered))

    def test_action_follows_actual_rate_and_gap(self):
        with tempfile.TemporaryDirectory() as directory:
            data = rows()
            for row in data:
                if row.get('id') in {'result', 'move-result'}:
                    row['planned_start_ms'] += 200
                    row['planned_end_ms'] += 200
                if row.get('id') == 'move-request':
                    row['planned_end_ms'] += 200
            story = load_storyboard(write_rows(Path(directory) / 'draft.jsonl', data))
            for samples, frame in [(19200, 18), (48001, 37), (72000, 51)]:
                tracks = {'call': AudioTrack(Path('unused'), samples), 'result': AudioTrack(Path('unused'), 72000)}
                resolved = build_timeline(story, tracks)
                self.assertEqual(resolved.speech[1].start_frame, frame)
                self.assertEqual(resolved.events['move-request'].end_frame, frame)
            with self.assertRaisesRegex(ValueError, 'show-arrow'):
                build_timeline(story, {'call': AudioTrack(Path('unused'), 3200), 'result': tracks['result']})
