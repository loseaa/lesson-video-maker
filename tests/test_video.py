import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from fixture import rows, write_rows, write_wav
from lesson_video_maker.assets import build_assets, load_layers
from lesson_video_maker.deck import write_deck
from lesson_video_maker.mux import mux_video
from lesson_video_maker.speech import AudioTrack
from lesson_video_maker.storyboard import load_storyboard
from lesson_video_maker.timeline import build_timeline, write_audio, write_timeline
from lesson_video_maker.video import write_cover, write_silent_video


def inspect(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(path)
    ]))['streams']


def video_hash(path):
    return subprocess.check_output([
        'ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:v:0',
        '-c:v', 'copy', '-f', 'hash', '-hash', 'sha256', '-'
    ])


class VideoTest(unittest.TestCase):
    def test_assets_player_render_and_mux(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            data = rows()
            data[0]['topic'] = '测试 </script>'
            source = write_rows(folder / 'draft.jsonl', data)
            layers_path = build_assets(source, folder / 'visual')
            events = {(layer.event_id, layer.mode) for layer in load_layers(layers_path)}
            self.assertIn(('move-request', 'travel'), events)
            self.assertIn(('move-result', 'travel'), events)
            tracks = {event: AudioTrack(write_wav(folder / (event + '.wav'), 16000), 16000)
                      for event in ('call', 'result')}
            timing = build_timeline(load_storyboard(source), tracks)
            timeline_path = folder / 'timeline.jsonl'
            audio_path = folder / 'narration.wav'
            write_timeline(timing, timeline_path)
            write_audio(timing, tracks, audio_path)
            deck = write_deck(timeline_path, layers_path, audio_path, folder / 'deck')
            self.assertTrue((deck.parent / 'narration.wav').is_file())
            self.assertIn('\\u003c/script>', deck.read_text())
            silent = folder / 'silent.mp4'
            write_silent_video(layers_path, timeline_path, silent)
            video, = inspect(silent)
            self.assertEqual((video['width'], video['height'], video['r_frame_rate']), (1920, 1080, '30/1'))
            self.assertEqual(int(video['nb_frames']), timing.total_frames)
            cover = folder / 'cover.png'
            write_cover(layers_path, timeline_path, cover)
            with Image.open(cover) as image:
                self.assertEqual(image.size, (1920, 1080))
            final = folder / 'final.mp4'
            mux_video(silent, audio_path, final)
            self.assertEqual([stream['codec_name'] for stream in inspect(final)], ['h264', 'aac'])
            self.assertEqual(video_hash(silent), video_hash(final))
            with self.assertRaisesRegex(ValueError, 'duration'):
                mux_video(silent, write_wav(folder / 'too-long.wav', 96000), folder / 'bad.mp4')
            self.assertFalse((folder / 'bad.mp4').exists())
