import fcntl
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from lesson_video_maker import douyin


class DouyinTest(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.bundle = Path(work.name)
        self.post = {"title": "晏子使楚" * 10, "description": "三道难题", "tags": ["小学语文", "课文讲解"]}
        row = {"type": "project", "post": self.post}
        (self.bundle / "timeline.jsonl").write_text(json.dumps(row), encoding="utf-8")
        (self.bundle / "video.mp4").write_bytes(b"video fixture")
        Image.new("RGB", (160, 90), "gold").save(self.bundle / "cover.png")
        self.runtime = {"executable": "sau", "workdir": self.bundle, "account": "creator"}

    def test_preview_uses_existing_bundle_without_running_sau(self):
        with patch.object(douyin, "_call") as call:
            preview = douyin.plan(self.bundle, None)
        self.assertEqual(preview["title"], self.post["title"][:29] + "…")
        self.assertEqual(preview["description"], self.post["description"])
        self.assertEqual(preview["tags"], self.post["tags"])
        self.assertEqual(preview["declaration"], "内容由AI生成")
        call.assert_not_called()

    def test_success_creates_receipt_and_keeps_cover_ratios(self):
        def sau(args, workdir, timeout):
            if args[2] == "upload-video":
                for flag, expected in (("--thumbnail-landscape", (1200, 900)),
                                       ("--thumbnail-portrait", (900, 1200))):
                    with Image.open(args[args.index(flag) + 1]) as cover:
                        self.assertEqual(cover.size, expected)
                self.assertIn("内容由AI生成", args)
                self.assertEqual(workdir, self.bundle)
                return subprocess.CompletedProcess(args, 0, "Douyin video upload submitted: video.mp4", "")
            return subprocess.CompletedProcess(args, 0, "valid", "")

        with patch.object(douyin, "_call", side_effect=sau) as call:
            receipt = douyin.publish(self.bundle, self.runtime, "晏子使楚")
            existing = douyin.publish(self.bundle, self.runtime, "晏子使楚")
        self.assertEqual(receipt["result"], "submitted")
        self.assertEqual(existing["result"], "existing")
        self.assertEqual(sum(item.args[0][2] == "upload-video" for item in call.call_args_list), 1)

    def test_uncertain_submission_is_not_retried(self):
        with patch.object(douyin, "_call", side_effect=[
            subprocess.CompletedProcess([], 0, "valid", ""),
            subprocess.TimeoutExpired("sau", 900),
        ]) as call:
            with self.assertRaisesRegex(ValueError, "状态未确认"):
                douyin.publish(self.bundle, self.runtime, None)
            with self.assertRaisesRegex(ValueError, "状态未确认"):
                douyin.publish(self.bundle, self.runtime, None)
        self.assertEqual(call.call_count, 2)

    def test_one_submission_at_a_time_per_browser_profile(self):
        busy = self.bundle / ".douyin-creator.lock"
        with busy.open("a") as profile_lock, patch.object(douyin, "_call") as call:
            fcntl.flock(profile_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(ValueError, "账号正在处理另一条投稿"):
                douyin.publish(self.bundle, self.runtime, None)
        call.assert_not_called()
