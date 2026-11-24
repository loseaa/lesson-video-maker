"""Synthesize UTF-8 speech with macOS say and cache normalized WAVs."""
import hashlib
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path

from .media import run_command, staged_file
from .storyboard import load_storyboard

SAMPLE_RATE = 48000


@dataclass(frozen=True)
class AudioTrack:
    path: Path
    sample_count: int


@dataclass(frozen=True)
class SceneTrack(AudioTrack):
    spans: dict[str, tuple[int, int]]


def audio_sample_count(path: Path) -> int:
    try:
        with wave.open(str(path), "rb") as stream:
            if (stream.getnchannels(), stream.getsampwidth(), stream.getframerate()) != (1, 2, SAMPLE_RATE):
                raise ValueError(f"{path.name}: expected mono 48 kHz PCM16")
            frames = stream.getnframes()
            if frames <= 0 or len(stream.readframes(frames)) != frames * 2:
                raise ValueError(f"{path.name}: empty or truncated WAV")
            return frames
    except (wave.Error, EOFError) as error:
        raise ValueError(f"{path.name}: invalid WAV") from error


def synthesize(timeline_path: Path, audio_dir: Path, voice: str = "Tingting") -> dict[str, AudioTrack]:
    story = load_storyboard(timeline_path)
    audio_dir.mkdir(parents=True, exist_ok=True)
    tracks = {}
    for event in story.speech:
        digest = hashlib.sha256(("say-pcm16-v1\0" + voice + "\0" + event.text).encode()).hexdigest()[:20]
        destination = audio_dir / f"{event.id}-{digest}.wav"
        if destination.is_file():
            try:
                tracks[event.id] = AudioTrack(destination, audio_sample_count(destination))
            except ValueError:
                pass
            else:
                continue
        try:
            with tempfile.TemporaryDirectory(prefix=f".{event.id}-", dir=audio_dir) as temp:
                text_path, aiff = Path(temp) / "text.txt", Path(temp) / "speech.aiff"
                text_path.write_text(event.text, encoding="utf-8")
                run_command(["/usr/bin/say", "-v", voice, "-f", str(text_path), "-o", str(aiff)])
                with staged_file(destination) as wav:
                    run_command(["ffmpeg", "-v", "error", "-i", str(aiff), "-ac", "1",
                                 "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(wav)])
                    frames = audio_sample_count(wav)
        except ValueError as error:
            raise ValueError(f"speak {event.id}: {error}") from error
        tracks[event.id] = AudioTrack(destination, frames)
    return tracks
