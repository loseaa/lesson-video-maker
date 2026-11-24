"""Resolve speech-anchored events to an integer 30 fps timeline."""
import json
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .media import staged_file
from .speech import SAMPLE_RATE, AudioTrack, SceneTrack, audio_sample_count
from .storyboard import SpeechAnchor, SpeechEvent, Storyboard, load_storyboard

FPS = 30
SAMPLES_PER_FRAME = SAMPLE_RATE // FPS
MIN_SPEECH_FRAMES = 12
MIN_ACTION_FRAMES = 6


def _ceil_div(value: int, divisor: int) -> int:
    return (value + divisor - 1) // divisor


def _time(start: int, end: int) -> dict:
    return {"start_frame": start, "end_frame": end,
            "start_ms": start * 1000 // FPS, "end_ms": end * 1000 // FPS}


@dataclass(frozen=True)
class TimedEvent:
    row: dict

    @property
    def id(self) -> str:
        return self.row["id"]

    @property
    def start_frame(self) -> int:
        return self.row["start_frame"]

    @property
    def end_frame(self) -> int:
        return self.row["end_frame"]

    @property
    def planned_start_ms(self) -> int:
        return self.row["planned_start_ms"]

    @property
    def speech_samples(self) -> int:
        return self.row["speech_samples"]

    @property
    def audio_offset_samples(self) -> int:
        return self.row["audio_offset_samples"]


@dataclass(frozen=True)
class Timeline:
    rows: tuple[dict, ...]
    events: dict[str, TimedEvent]
    speech: tuple[TimedEvent, ...]
    scenes: tuple[dict, ...]
    total_frames: int

    def player_data(self) -> dict:
        return {"events": {key: item.row for key, item in self.events.items()},
                "fps": FPS, "scenes": self.scenes, "total_frames": self.total_frames}


def _local_speech(story: Storyboard, sample_counts: Mapping[str, int]):
    cursor, previous_end_ms = 0, 0
    times, samples, scene_starts = {}, {}, {}
    for speech in story.speech:
        count = sample_counts.get(speech.id)
        if type(count) is not int or count <= 0:
            raise ValueError(f"{speech.id}: missing or invalid speech sample count")
        cursor += _ceil_div((speech.planned_start_ms - previous_end_ms) * FPS, 1000)
        scene_starts.setdefault(speech.scene_id, cursor)
        end = cursor + max(_ceil_div(count, SAMPLES_PER_FRAME), MIN_SPEECH_FRAMES)
        times[speech.id] = _time(cursor, end)
        samples[speech.id] = {"speech_samples": count, "audio_offset_samples": cursor * SAMPLES_PER_FRAME}
        previous_end_ms, cursor = speech.planned_end_ms, end
    return times, samples, scene_starts, cursor


def _observed_speech(story: Storyboard, sample_counts: Mapping[str, int],
                     placements: Mapping[str, int], relative_offsets: Mapping[str, int]):
    times, samples, starts, scene_audio = {}, {}, {}, {}
    cursor, scene_id, previous_end_ms = 0, None, 0
    for speech in story.speech:
        if speech.scene_id != scene_id:
            scene_id = speech.scene_id
            length = placements.get(scene_id)
            if type(length) is not int or length <= 0:
                raise ValueError(f"{scene_id}: missing or invalid scene audio length")
            scene_frame = cursor + _ceil_div((speech.planned_start_ms - previous_end_ms) * FPS, 1000)
            scene_sample = scene_frame * SAMPLES_PER_FRAME
            starts[scene_id] = scene_frame
            scene_audio[scene_id] = {"scene_audio_samples": length,
                                     "scene_audio_offset_samples": scene_sample}
            cursor = scene_frame + _ceil_div(length, SAMPLES_PER_FRAME)
            previous_end = 0
        count, offset = sample_counts.get(speech.id), relative_offsets.get(speech.id)
        if (type(count) is not int or type(offset) is not int or count <= 0
                or offset < previous_end or offset + count > length):
            raise ValueError(f"{speech.id}: invalid measured speech range in scene {scene_id}")
        first = scene_sample + offset
        times[speech.id] = _time(first // SAMPLES_PER_FRAME, _ceil_div(first + count, SAMPLES_PER_FRAME))
        samples[speech.id] = {"speech_samples": count, "audio_offset_samples": first,
                              "scene_speech_start_sample": offset}
        previous_end, previous_end_ms = offset + count, speech.planned_end_ms
    return times, samples, starts, scene_audio, cursor


def _resolve(story: Storyboard, sample_counts: Mapping[str, int],
             placements: Mapping[str, int] | None = None,
             relative_offsets: Mapping[str, int] | None = None) -> Timeline:
    scene_audio = {}
    if placements is None:
        times, samples, scene_starts, cursor = _local_speech(story, sample_counts)
    else:
        times, samples, scene_starts, scene_audio, cursor = _observed_speech(
            story, sample_counts, placements, relative_offsets or {})

    def frame(anchor: SpeechAnchor) -> int:
        cue = times[anchor.speak_id]
        if anchor.point == "end":
            audio = samples[anchor.speak_id]
            return _ceil_div(audio["audio_offset_samples"] + audio["speech_samples"], SAMPLES_PER_FRAME)
        return cue["start_frame"]

    for event in story.events:
        if isinstance(event, SpeechEvent):
            continue
        first, last = frame(event.start_anchor), frame(event.end_anchor)
        if last - first < MIN_ACTION_FRAMES:
            raise ValueError(f"{event.id}: animation anchors at frames {first}, {last} need at least "
                             f"{MIN_ACTION_FRAMES} frames; revise the speech anchors or pauses")
        times[event.id] = _time(first, last)

    ordered_starts = [0] + [scene_starts[scene.id] for scene in story.scenes[1:]] + [cursor]
    scene_times = {scene.id: _time(ordered_starts[index], ordered_starts[index + 1])
                   for index, scene in enumerate(story.scenes)}
    resolved, resolved_scenes, events = [], [], {}
    for raw in story.rows:
        if raw["type"] == "project":
            row = dict(raw, fps=FPS, sample_rate=SAMPLE_RATE, audio_file="deck/narration.wav")
        elif raw["type"] == "scene":
            row = dict(raw, **scene_times[raw["id"]], **scene_audio.get(raw["id"], {}))
            resolved_scenes.append(row)
        else:
            row = dict(raw, **times[raw["id"]], **samples.get(raw["id"], {}))
            events[row["id"]] = TimedEvent(row)
        resolved.append(row)
    return Timeline(tuple(resolved), events, tuple(events[event.id] for event in story.speech),
                    tuple(resolved_scenes), cursor)


def build_timeline(story: Storyboard, tracks: Mapping[str, AudioTrack]) -> Timeline:
    return _resolve(story, {event_id: track.sample_count for event_id, track in tracks.items()})


def build_scene_timeline(story: Storyboard, tracks: Mapping[str, SceneTrack]) -> Timeline:
    spans = {key: span for track in tracks.values() for key, span in track.spans.items()}
    return _resolve(story, {key: end - start for key, (start, end) in spans.items()},
                    {key: track.sample_count for key, track in tracks.items()},
                    {key: start for key, (start, _) in spans.items()})


def write_timeline(timeline: Timeline, dst: Path) -> None:
    with staged_file(dst) as scratch:
        with scratch.open("w", encoding="utf-8") as stream:
            for row in timeline.rows:
                stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")


def load_timeline(path: Path) -> Timeline:
    story = load_storyboard(path)
    measured = any("scene_audio_samples" in row for row in story.rows)
    spoken = [row for row in story.rows if row["type"] == "speak"]
    timeline = _resolve(story, {row["id"]: row.get("speech_samples") for row in spoken},
                        {row["id"]: row.get("scene_audio_samples")
                         for row in story.rows if row["type"] == "scene"} if measured else None,
                        {row["id"]: row.get("scene_speech_start_sample") for row in spoken} if measured else None)
    for provided, calculated in zip(story.rows, timeline.rows):
        for key in ("fps", "sample_rate", "audio_file", "start_frame", "end_frame", "start_ms",
                    "end_ms", "speech_samples", "audio_offset_samples", "scene_audio_samples",
                    "scene_audio_offset_samples", "scene_speech_start_sample"):
            if key in calculated and (provided.get(key) != calculated[key]
                                      or type(provided.get(key)) is not type(calculated[key])):
                raise ValueError(f"{provided.get('id', provided['type'])}: inconsistent resolved {key}")
    return timeline


def _silence(stream: wave.Wave_write, samples: int) -> None:
    while samples > 0:
        count = min(samples, SAMPLE_RATE)
        stream.writeframesraw(b"\0\0" * count)
        samples -= count


def write_audio(timeline: Timeline, tracks: Mapping[str, AudioTrack], dst: Path) -> None:
    if "scene_audio_samples" in timeline.scenes[0]:
        segments = [(row["id"], row["scene_audio_offset_samples"], row["scene_audio_samples"])
                    for row in timeline.scenes]
    else:
        segments = [(event.id, event.audio_offset_samples, event.speech_samples) for event in timeline.speech]
    cursor = 0
    with staged_file(dst) as scratch:
        with wave.open(str(scratch), "wb") as out:
            out.setparams((1, 2, SAMPLE_RATE, 0, "NONE", "not compressed"))
            for segment_id, offset, count in segments:
                track = tracks[segment_id]
                if audio_sample_count(track.path) != count:
                    raise ValueError(f"{segment_id}: WAV length disagrees with the resolved timeline")
                _silence(out, offset - cursor)
                with wave.open(str(track.path), "rb") as voice:
                    out.writeframesraw(voice.readframes(count))
                cursor = offset + count
            _silence(out, timeline.total_frames * SAMPLES_PER_FRAME - cursor)


def _srt_time(milliseconds: int) -> str:
    second, ms = divmod(milliseconds, 1000)
    minute, second = divmod(second, 60)
    hour, minute = divmod(minute, 60)
    return f"{hour:02d}:{minute:02d}:{second:02d},{ms:03d}"


def write_srt(timeline: Timeline, dst: Path) -> None:
    with staged_file(dst) as scratch:
        with scratch.open("w", encoding="utf-8") as stream:
            for index, event in enumerate(timeline.speech, 1):
                start = event.audio_offset_samples * 1000 // SAMPLE_RATE
                end = (event.audio_offset_samples + event.speech_samples) * 1000 // SAMPLE_RATE
                caption = " ".join(event.row["caption"].split())
                stream.write(f"{index}\n{_srt_time(start)} --> {_srt_time(end)}\n{caption}\n\n")
