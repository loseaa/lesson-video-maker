import base64
import json
import os
import tempfile
import unittest
import wave
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from fixture import rows, write_rows, write_wav
from lesson_video_maker import cli, doubao
from lesson_video_maker.speech import SceneTrack
from lesson_video_maker.storyboard import load_storyboard
from lesson_video_maker.timeline import build_scene_timeline, load_timeline, write_timeline


PCM = b"\x34\x12" * 48000 + b"\x78\x56" * 96000


def _word(text, start, end):
    return {"word": text, "startTime": start, "endTime": end}


def _stream():
    packets = [
        {"code": 0, "data": base64.b64encode(PCM[:96000]).decode()},
        {"code": 0, "sentence": {"words": [_word("模型", 0.10, 0.35), _word("请求？", 0.35, 0.75)]}},
        {"code": 0, "data": base64.b64encode(PCM[96000:]).decode()},
        {"code": 0, "sentence": {"words": [_word("应用", 1.25, 1.55), _word("返回结果。", 1.55, 2.6)]}},
        {"code": 20000000, "data": None},
    ]
    return BytesIO(b"".join(json.dumps(item).encode() + b"\n" for item in packets))


class DoubaoTest(unittest.TestCase):
    def test_cli_matches_actual_pauses_and_preserves_scene_audio(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"DOUBAO_TTS_API_KEY": "test-key"}):
            root = Path(directory)
            draft = rows()
            draft[0]["target_seconds"] = 3
            draft[2]["text"] = "模型请求？"
            source = write_rows(root / "draft.jsonl", draft)
            work, output = root / "work", root / "output"
            args = ["build", str(source), "--work-dir", str(work), "--output", str(output), "--tts", "doubao"]
            with patch.object(doubao, "urlopen", return_value=_stream()) as request:
                self.assertEqual(cli.main(args), 0)
            request.assert_called_once()
            sent = request.call_args.args[0]
            self.assertEqual(sent.full_url, "https://openspeech.bytedance.com/api/v3/tts/unidirectional")
            self.assertEqual(sent.get_header("X-api-key"), "test-key")
            self.assertEqual(sent.get_header("X-api-resource-id"), "seed-tts-2.0")
            data = json.loads(sent.data)["req_params"]
            self.assertEqual(data["text"], "模型请求？ 应用返回结果。")
            self.assertEqual(data["speaker"], "zh_male_yuanboxiaoshu_uranus_bigtts")
            self.assertEqual(data["audio_params"], {"format": "pcm", "sample_rate": 48000,
                                                    "speech_rate": -4, "loudness_rate": 0,
                                                    "enable_subtitle": True})
            additions = json.loads(data["additions"])
            self.assertIn("问句", additions["context_texts"][0])
            self.assertFalse(additions["aigc_watermark"])
            timeline = load_timeline(output / "timeline.jsonl")
            self.assertEqual(timeline.events["move-request"].end_frame, 37)
            self.assertEqual(timeline.speech[1].audio_offset_samples, 60000)
            self.assertEqual(timeline.total_frames, 90)
            with wave.open(str(output / "deck" / "narration.wav"), "rb") as voice:
                self.assertEqual(voice.readframes(voice.getnframes()), PCM)
            self.assertIn("00:00:01,250 --> 00:00:02,600", (output / "subtitles.srt").read_text())
            self.assertTrue((output / "video.mp4").is_file())
            with patch.object(doubao, "urlopen", side_effect=AssertionError("cached")):
                tracks = doubao.synthesize_scenes(source, work / "audio", "test-key")
                self.assertEqual(tracks["request"].spans["result"], (60000, 124800))

    def test_incomplete_stream_and_missing_alignment_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft = rows()
            source = write_rows(root / "draft.jsonl", draft)
            packets = [json.loads(line) for line in _stream()]
            for sample, message in ((packets[:-1], "流未正常结束"), (packets[:-2] + packets[-1:], "result")):
                stream = BytesIO(b"".join(json.dumps(item).encode() + b"\n" for item in sample))
                with patch.object(doubao, "urlopen", return_value=stream):
                    with self.assertRaisesRegex(ValueError, message):
                        doubao.synthesize_scenes(source, root / "audio", "test-key")
            self.assertFalse(list((root / "audio").glob("*.wav")))

    def test_next_scene_starts_after_previous_pcm_and_authored_gap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft = rows()
            draft[5]["planned_start_ms"] = 2600
            draft[4]["planned_end_ms"] = 2600
            draft[6]["planned_start_ms"] = 2600
            draft.append(dict(draft[1], id="second"))
            draft.append(dict(draft[5], id="later", scene_id="second",
                              planned_start_ms=5200, planned_end_ms=6200))
            story = load_storyboard(write_rows(root / "draft.jsonl", draft))
            tracks = {
                "request": SceneTrack(write_wav(root / "one.wav", 144000), 144000,
                                      {"call": (4800, 36000), "result": (60000, 124800)}),
                "second": SceneTrack(write_wav(root / "two.wav", 48000), 48000,
                                     {"later": (9600, 36000)}),
            }
            timeline = build_scene_timeline(story, tracks)
            self.assertEqual(timeline.speech[1].audio_offset_samples, 60000)
            self.assertEqual(timeline.scenes[1]["scene_audio_offset_samples"], 153600)
            self.assertEqual(timeline.speech[2].audio_offset_samples, 163200)
            self.assertEqual(timeline.total_frames, 126)
            result = root / "resolved.jsonl"
            write_timeline(timeline, result)
            self.assertEqual(load_timeline(result).rows, timeline.rows)

    def test_keychain_lookup_and_missing_key(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(doubao, "run_command") as command:
            command.return_value = " stored-key\n"
            self.assertEqual(doubao.api_key(), "stored-key")
            self.assertIn("lesson-video-maker.doubao-tts", command.call_args.args[0])
            command.side_effect = [ValueError("new entry missing"), "existing-key\n"]
            self.assertEqual(doubao.api_key(), "existing-key")
            self.assertIn("tech-explainer.doubao-tts", command.call_args.args[0])
            command.side_effect = ValueError("keychain unavailable")
            with self.assertRaisesRegex(ValueError, "DOUBAO_TTS_API_KEY"):
                doubao.api_key()
