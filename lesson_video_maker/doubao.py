"""Synthesize one scene per request using Doubao Speech Synthesis 2.0."""
import base64
import binascii
import hashlib
import json
import os
import shutil
import tempfile
import unicodedata
import wave
from getpass import getuser
from http.client import HTTPException
from itertools import groupby
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .media import run_command
from .speech import SAMPLE_RATE, SceneTrack, audio_sample_count
from .storyboard import SpeechEvent, load_storyboard

ENDPOINT = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
KEYCHAIN_SERVICE = "lesson-video-maker.doubao-tts"
LEGACY_KEYCHAIN_SERVICE = "tech-explainer.doubao-tts"
KEY_VARIABLE = "DOUBAO_TTS_API_KEY"


def api_key() -> str:
    key = os.environ.get(KEY_VARIABLE, "").strip()
    if key:
        return key
    for service in (KEYCHAIN_SERVICE, LEGACY_KEYCHAIN_SERVICE):
        try:
            key = run_command(["/usr/bin/security", "find-generic-password", "-a", getuser(),
                               "-s", service, "-w"], timeout=30).strip()
        except ValueError:
            continue
        if key:
            return key
    raise ValueError(f"豆包配音缺少 API Key。请设置 {KEY_VARIABLE} 或添加钥匙串项目 {KEYCHAIN_SERVICE}。")


def _request_audio(payload: bytes, resource_id: str, key: str) -> tuple[bytes, list[dict]]:
    request = Request(ENDPOINT, data=payload, headers={
        "Content-Type": "application/json",
        "X-Api-Resource-Id": resource_id,
    })
    request.add_unredirected_header("X-Api-Key", key)
    pcm = bytearray()
    words = []
    finished = False
    try:
        with urlopen(request, timeout=90) as response:
            for line in response:
                if not line.strip():
                    continue
                packet = json.loads(line)
                code = packet["code"]
                if code == 20000000:
                    finished = True
                    break
                if code != 0:
                    status = str(code) if type(code) is int else "unknown"
                    raise ValueError(f"豆包语音错误码 {status}。请检查模型开通状态、额度和音色。")
                if packet.get("data"):
                    pcm.extend(base64.b64decode(packet["data"], validate=True))
                if packet.get("sentence"):
                    words.extend(packet["sentence"]["words"])
    except HTTPError as error:
        error.close()
        raise ValueError(f"豆包 HTTP {error.code}。请检查 API Key、项目和模型服务权限。") from None
    except (URLError, TimeoutError, HTTPException) as error:
        raise ValueError("豆包语音连接失败。请检查网络后重试。") from error
    except (KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError, binascii.Error):
        raise ValueError("豆包语音返回的数据格式无效。") from None
    if not finished:
        raise ValueError("豆包音频流未正常结束。")
    if not pcm or len(pcm) % 2:
        raise ValueError("豆包返回的 PCM 音频为空或不完整。")
    return bytes(pcm), words


def _normalized(text: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFKC", text).casefold() if char.isalnum())


def _sample(value: float, count: int) -> int:
    if type(value) not in (int, float) or not 0 <= value <= (count + 0.5) / SAMPLE_RATE:
        raise ValueError("豆包语音时间戳无效。")
    return round(value * SAMPLE_RATE)


def _align(events: list[SpeechEvent], words: list[dict], count: int) -> dict[str, tuple[int, int]]:
    if not isinstance(words, list):
        raise ValueError("豆包语音字幕格式无效。")
    tokens = []
    for word in words:
        if not isinstance(word, dict) or not isinstance(word.get("word"), str):
            raise ValueError("豆包语音字幕词条格式无效。")
        token = _normalized(word["word"])
        if token:
            tokens.append((token, _sample(word.get("startTime"), count), _sample(word.get("endTime"), count)))

    spans = {}
    index, previous_end = 0, 0
    for event in events:
        remaining = _normalized(event.text)
        if not remaining or index == len(tokens):
            raise ValueError(f"speak {event.id}: 缺少可对齐的豆包时间戳。")
        start = tokens[index][1]
        while remaining:
            if index == len(tokens) or not remaining.startswith(tokens[index][0]):
                raise ValueError(f"speak {event.id}: 豆包字幕与口播稿不匹配。请在 text 中写出实际读法。")
            token, first, end = tokens[index]
            if not previous_end <= first < end <= count:
                raise ValueError(f"speak {event.id}: 豆包时间戳超出音频范围或顺序有误。")
            remaining = remaining[len(token):]
            previous_end = end
            index += 1
        spans[event.id] = (start, previous_end)
    if index != len(tokens):
        raise ValueError("豆包返回了未匹配到剧本的字幕。")
    return spans


def synthesize_scenes(timeline_path: Path, audio_dir: Path, key: str) -> dict[str, SceneTrack]:
    story = load_storyboard(timeline_path)
    defaults = json.loads(Path(__file__).with_name("doubao_defaults.json").read_text(encoding="utf-8"))
    audio_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for scene_id, group in groupby(story.speech, key=lambda event: event.scene_id):
        events = list(group)
        params = {
            "text": " ".join(event.text.strip() for event in events),
            "speaker": defaults["speaker"],
            "audio_params": {"format": "pcm", "sample_rate": SAMPLE_RATE,
                             "speech_rate": defaults["speech_rate"], "loudness_rate": defaults["loudness_rate"],
                             "enable_subtitle": True},
            "additions": json.dumps({"context_texts": [defaults["style"]], "aigc_watermark": False},
                                    ensure_ascii=False),
        }
        # Retain the service request identity so existing narration caches are reusable.
        payload = json.dumps({"user": {"uid": "tech-explainer"}, "req_params": params}, ensure_ascii=False).encode()
        resource = defaults["resource_id"]
        digest = hashlib.sha256(b"doubao-pcm16-v1\0" + resource.encode() + b"\0" + payload).hexdigest()[:20]
        folder = audio_dir / f"doubao-{scene_id}-{digest}"
        try:
            path = folder / "speech.wav"
            try:
                count = audio_sample_count(path)
                words = json.loads((folder / "words.json").read_text(encoding="utf-8"))
                spans = _align(events, words, count)
            except (OSError, ValueError):
                pcm, words = _request_audio(payload, resource, key)
                count = len(pcm) // 2
                spans = _align(events, words, count)
                with tempfile.TemporaryDirectory(prefix=".doubao-", dir=audio_dir) as temp:
                    cached = Path(temp) / "scene"
                    cached.mkdir()
                    with wave.open(str(cached / "speech.wav"), "wb") as audio:
                        audio.setparams((1, 2, SAMPLE_RATE, 0, "NONE", "not compressed"))
                        audio.writeframes(pcm)
                    (cached / "words.json").write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
                    if folder.exists():
                        shutil.rmtree(folder)
                    cached.rename(folder)
        except ValueError as error:
            raise ValueError(f"scene {scene_id}: {error}") from error
        result[scene_id] = SceneTrack(path, count, spans)
    return result
