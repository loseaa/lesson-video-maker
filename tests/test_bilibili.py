import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lesson_video_maker import bilibili


class BilibiliTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.title = "消息处理成功了，为什么还会重投？"
        content = {"type": "project", "post": {"title": self.title,
                   "description": "用一个事件讲重投", "tags": ["消息队列", "RabbitMQ"]}}
        (self.root / "timeline.jsonl").write_text(json.dumps(content, ensure_ascii=False) + "\n", encoding="utf-8")
        for filename in ("video.mp4", "cover.png", "cookies.json"):
            (self.root / filename).write_bytes(b"fixture")
        self.cookie = self.root / "cookies.json"

    def test_existing_title_stops_before_upload(self):
        result = subprocess.CompletedProcess([], 0, f"BV1X9ySzsExQ\t{self.title}\t\x1b[92m开放浏览\x1b[0m\n", "")
        with patch.object(bilibili, "_call", return_value=result) as call:
            receipt = bilibili.publish(self.root, "biliup", self.cookie, 231, 1012)
        self.assertEqual(receipt["result"], "existing")
        self.assertEqual(receipt["status"], "开放浏览")
        self.assertEqual(call.call_count, 1)
        self.assertIn("list", call.call_args.args[0])

    def test_web_submission_preserves_local_cover_and_ai_statement(self):
        empty = subprocess.CompletedProcess([], 0, "", "")
        sent = subprocess.CompletedProcess([], 0, "ResponseData { bvid: BV1X9ySzsExQ }", "")
        seen = subprocess.CompletedProcess([], 0, f"BV1X9ySzsExQ\t{self.title}\t审核中\n", "")
        with patch.object(bilibili, "_call", side_effect=[empty, sent, seen]) as call, \
             patch.object(bilibili, "run_command"):
            receipt = bilibili.publish(self.root, "biliup", self.cookie, 231, 1012)
        args = call.call_args_list[1].args[0]
        self.assertEqual(receipt["status"], "审核中")
        self.assertEqual(args[args.index("--submit") + 1], "web")
        self.assertEqual(args[args.index("--tid-v2") + 1], "1012")
        self.assertEqual(json.loads(args[args.index("--extra-fields") + 1]), {"creation_statement": {"id": 1}})
        self.assertEqual(Path(args[args.index("--cover") + 1]).suffix, ".jpg")

    def test_lost_submission_response_is_not_retried(self):
        empty = subprocess.CompletedProcess([], 0, "", "")
        uncertain = subprocess.CompletedProcess([], 1, "private provider data", "")
        with patch.object(bilibili, "_call", side_effect=[empty, uncertain, empty, empty]) as call, \
             patch.object(bilibili, "run_command"):
            with self.assertRaisesRegex(ValueError, "状态未确认"):
                bilibili.publish(self.root, "biliup", self.cookie, 231, 1012)
            with self.assertRaisesRegex(ValueError, "上一轮投稿状态未确认"):
                bilibili.publish(self.root, "biliup", self.cookie, 231, 1012)
        self.assertEqual(sum("upload" in item.args[0] for item in call.call_args_list), 1)
