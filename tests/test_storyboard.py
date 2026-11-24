import tempfile
import unittest
from pathlib import Path

from fixture import rows, write_rows
from lesson_video_maker.storyboard import load_storyboard


class StoryboardTest(unittest.TestCase):
    def test_forward_anchor_and_text(self):
        with tempfile.TemporaryDirectory() as directory:
            story = load_storyboard(write_rows(Path(directory) / 'input.jsonl', rows()))
        self.assertEqual(story.target_seconds, 120)
        self.assertEqual(story.scenes[0].id, 'request')
        self.assertEqual(story.speech[0].text, '模型请求。')
        self.assertEqual(story.events[2].end_anchor.speak_id, 'result')

    def test_reports_line_for_duplicate_and_bad_anchor(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.jsonl'
            data = rows()
            data[4]['id'] = 'show-arrow'
            with self.assertRaisesRegex(ValueError, '5.*show-arrow'):
                load_storyboard(write_rows(path, data))
            data = rows()
            data[4]['end_anchor']['speak_id'] = 'missing'
            with self.assertRaisesRegex(ValueError, '5.*missing'):
                load_storyboard(write_rows(path, data))
            data = rows()
            data[4]['target'] = 'absent-edge'
            with self.assertRaisesRegex(ValueError, '5.*absent-edge'):
                load_storyboard(write_rows(path, data))
            write_rows(path, rows()[:1])
            with path.open('a', encoding='utf-8') as stream:
                stream.write('{"type":\n')
            with self.assertRaisesRegex(ValueError, '2'):
                load_storyboard(path)
