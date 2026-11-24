"""Mux one synchronized video and audio track into a delivery MP4."""
import json
import math
from pathlib import Path

from .media import run_command, staged_file
from .timeline import FPS


def inspect_streams(path: Path) -> list[dict]:
    return json.loads(run_command(["ffprobe", "-v", "error", "-show_streams", "-of", "json",
                                   str(path)]))["streams"]


def _duration(stream: dict, path: Path) -> float:
    try:
        seconds = float(stream["duration"])
    except (KeyError, ValueError) as error:
        raise ValueError(f"{path.name}: stream duration is unavailable") from error
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError(f"{path.name}: invalid stream duration")
    return seconds


def mux_video(silent_video_path: Path, audio_path: Path, dst: Path) -> None:
    video_streams, audio_streams = inspect_streams(silent_video_path), inspect_streams(audio_path)
    if len(video_streams) != 1 or video_streams[0].get("codec_name") != "h264":
        raise ValueError(f"{silent_video_path.name}: expected only one H.264 video stream")
    if len(audio_streams) != 1 or audio_streams[0].get("codec_type") != "audio":
        raise ValueError(f"{audio_path.name}: expected only one audio stream")
    video_time = _duration(video_streams[0], silent_video_path)
    audio_time = _duration(audio_streams[0], audio_path)
    if abs(video_time - audio_time) > (1 / FPS + 1e-6):
        raise ValueError(f"duration mismatch: video {video_time:.3f}s, audio {audio_time:.3f}s")
    with staged_file(dst) as scratch:
        run_command(["ffmpeg", "-v", "error", "-i", str(silent_video_path), "-i", str(audio_path),
                     "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
                     "-b:a", "128k", "-movflags", "+faststart", str(scratch)])
        streams = inspect_streams(scratch)
        if [stream["codec_name"] for stream in streams] != ["h264", "aac"]:
            raise ValueError("muxed output does not contain one H.264 stream and one AAC stream")
