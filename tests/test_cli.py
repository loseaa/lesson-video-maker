import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from fixture import rows, write_rows
from lesson_video_maker import cli


class CLITest(unittest.TestCase):
    def test_branches_read_same_snapshot_and_recover(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = rows()
            data[0]['target_seconds'] = 3
            source = write_rows(root / 'script.jsonl', data)
            work, output = root / 'work', root / 'result'
            args = ['build', str(source), '--work-dir', str(work), '--output', str(output)]
            barrier = threading.Barrier(2)
            paths = []

            def visualize(story, path):
                paths.append(story)
                barrier.wait(5)
                return real_assets(story, path)

            def fail_speech(story, _):
                paths.append(story)
                barrier.wait(5)
                raise ValueError('simulated speech failure')

            real_assets = cli.build_assets
            with patch.object(cli, 'build_assets', side_effect=visualize), \
                 patch.object(cli, 'synthesize', side_effect=fail_speech):
                self.assertEqual(cli.main(args), 1)
            self.assertEqual(paths[0], paths[1])
            self.assertFalse(output.exists())
            self.assertTrue(list((work / 'visual').glob('*/layers.json')))
            with patch.object(cli, 'build_assets', side_effect=AssertionError('rebuild')):
                self.assertEqual(cli.main(args), 0)
            self.assertEqual({p.name for p in output.iterdir()},
                             {'timeline.jsonl', 'deck', 'video.mp4', 'subtitles.srt', 'cover.png', 'post.md'})
            self.assertEqual(cli.main(args), 1)

    def test_reports_duration_without_creating_final_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = write_rows(root / 'script.jsonl', rows())
            work, output = root / 'work', root / 'output'
            args = ['build', str(source), '--work-dir', str(work), '--output', str(output)]
            self.assertEqual(cli.main(args), 3)
            self.assertTrue((work / 'timeline.jsonl').is_file())
            self.assertFalse(output.exists())

    def test_exact_twenty_percent_edges_are_allowed(self):
        for frames in (72, 108):
            self.assertFalse(cli._outside_target(frames, 3))
        for frames in (71, 109):
            self.assertTrue(cli._outside_target(frames, 3))
