import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fixture import rows, write_rows
from lesson_video_maker import cli
from lesson_video_maker.media import run_command
from lesson_video_maker.storyboard import load_storyboard


def html_rows():
    data = rows()
    data[0]["target_seconds"] = 3
    data[1].update(kind="html", nodes=[], edges=[])
    for row in data:
        if row["type"] in {"reveal", "travel"}:
            row.update(type="html_motion", target="shell")
    return data


class HTMLDeckTest(unittest.TestCase):
    def test_build_uses_custom_page_and_shared_timing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft = write_rows(root / "draft.jsonl", html_rows())
            authored, output = root / "authored", root / "delivery"
            authored.mkdir()
            (authored / "scenes.html").write_text(
                '<section data-scene="request"><div id="shell">'
                '<span class="tx-icon" data-glyph="file" aria-hidden="true"></span>测试</div></section>')
            (authored / "scenes.css").write_text('#shell { perspective: 700px }')
            (authored / "scenes.js").write_text('window.drawExplainerScene = ({motion}) => motion("show-arrow");')
            # Use the established encoder for a tiny stub; real Chrome capture is exercised separately.
            def capture(deck, frames, cover, silent):
                self.assertTrue((deck / "narration.wav").is_file())
                self.assertIn('data-scene="request"', (deck / "index.html").read_text())
                self.assertIn('"type": "html_motion"', (deck / "index.html").read_text())
                self.assertIn('href="html_icons.css"', (deck / "index.html").read_text())
                self.assertIn('[data-glyph="file"]', (deck / "html_icons.css").read_text())
                self.assertIn('src="html_motion.js"', (deck / "index.html").read_text())
                self.assertTrue((deck / "html_motion.js").is_file())
                self.assertEqual((deck / "scenes.css").read_text(), '#shell { perspective: 700px }')
                run_command(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                                 "color=black:s=320x180:r=30", "-frames:v", str(frames), "-c:v", "libx264", str(silent)])
                cover.write_bytes(b"cover")

            with patch.object(cli, "capture_html", side_effect=capture) as render:
                self.assertEqual(cli.main(["build", str(draft), "--work-dir", str(root / "work"), "--output",
                                           str(output), "--html-deck", str(authored)]), 0)
            render.assert_called_once()
            self.assertTrue((output / "video.mp4").is_file())
            self.assertTrue((output / "deck" / "index.html").is_file())

    def test_html_motion_only_belongs_to_html_scene(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = html_rows()
            self.assertEqual(load_storyboard(write_rows(root / "yes.jsonl", data)).scenes[0].kind, "html")
            data[3]["type"] = "reveal"
            with self.assertRaisesRegex(ValueError, "html_motion"):
                load_storyboard(write_rows(root / "no.jsonl", data))
