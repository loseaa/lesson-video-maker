import tempfile
import unittest
from pathlib import Path

from fixture import rows, write_rows, write_wav
from lesson_video_maker.speech import audio_sample_count, synthesize


class SpeechTest(unittest.TestCase):
    def test_real_mac_voice_cache_and_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            data = rows()
            story = write_rows(folder / 'draft.jsonl', data)
            first = synthesize(story, folder / 'audio')
            stamp = first['call'].path.stat().st_mtime_ns
            data[5]['text'] = '应用完成执行，并且把工具结果返回给模型。'
            second = synthesize(write_rows(story, data), folder / 'audio')
            self.assertEqual(set(second), {'call', 'result'})
            self.assertEqual(second['call'].path.stat().st_mtime_ns, stamp)
            self.assertNotEqual(first['result'].path, second['result'].path)
            self.assertGreater(second['result'].sample_count, 0)
            with self.assertRaisesRegex(ValueError, 'empty'):
                audio_sample_count(write_wav(folder / 'empty.wav', 0))
