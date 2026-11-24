"""Draw the resolved layers with Pillow and encode only the video stream."""
import math
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .assets import HEIGHT, WIDTH, Layer, load_layers
from .media import staged_file
from .timeline import FPS, SAMPLES_PER_FRAME, Timeline, load_timeline


@dataclass(frozen=True)
class LayerState:
    visible: bool
    opacity: float
    x: int
    y: int


def _state(frame: int, layer: Layer, timeline: Timeline) -> LayerState:
    x, y = layer.x, layer.y
    if layer.mode == "base":
        return LayerState(True, 1, x, y)
    event = timeline.events[layer.event_id]
    offset, length = frame - event.start_frame, event.end_frame - event.start_frame
    if offset < 0:
        return LayerState(False, 1, x, y)
    if layer.mode == "reveal":
        return LayerState(True, min(1, (offset + 1) / length), x, y)
    limit = (event.speech_samples + SAMPLES_PER_FRAME - 1) // SAMPLES_PER_FRAME \
        if layer.mode == "caption" else length
    if offset >= limit:
        return LayerState(False, 1, x, y)
    if layer.mode == "travel":
        progress = offset / (length - 1)
        x = math.floor(x + (layer.to_x - x) * progress + 0.5)
        y = math.floor(y + (layer.to_y - y) * progress + 0.5)
    return LayerState(True, 1, x, y)


def layer_state(frame: int, layer: Layer, timeline: Timeline) -> LayerState:
    for scene in timeline.scenes:
        if scene["id"] == layer.scene_id and scene["start_frame"] <= frame < scene["end_frame"]:
            return _state(frame, layer, timeline)
    return LayerState(False, 1, layer.x, layer.y)


def _open_layers(path: Path) -> dict[str, list[tuple[Layer, Image.Image]]]:
    groups = {}
    for layer in sorted(load_layers(path), key=lambda item: item.z):
        with Image.open(path.parent / layer.file) as sprite:
            groups.setdefault(layer.scene_id, []).append((layer, sprite.convert("RGBA")))
    return groups


def _frame(frame: int, layers, timeline: Timeline, *, hide_captions=False) -> Image.Image:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), "#0a1324")
    for layer, tile in layers:
        if hide_captions and layer.mode == "caption":
            continue
        state = _state(frame, layer, timeline)
        if not state.visible:
            continue
        if state.opacity < 1:
            sprite = tile.copy()
            opacity = state.opacity
            sprite.putalpha(tile.getchannel("A").point(lambda value: round(value * opacity)))
        else:
            sprite = tile
        canvas.alpha_composite(sprite, (state.x, state.y))
    return canvas.convert("RGB")


def write_silent_video(layers_path: Path, timeline_path: Path, dst: Path) -> None:
    timeline = load_timeline(timeline_path)
    groups = _open_layers(layers_path)
    with staged_file(dst) as scratch, tempfile.TemporaryFile() as log:
        command = ["ffmpeg", "-v", "error", "-f", "rawvideo", "-pixel_format", "rgb24",
                   "-video_size", f"{WIDTH}x{HEIGHT}", "-framerate", str(FPS), "-i", "pipe:0",
                   "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
                   str(scratch)]
        try:
            with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log) as encoder:
                try:
                    with encoder.stdin as stream:
                        for scene in timeline.scenes:
                            layers = groups[scene["id"]]
                            for frame in range(scene["start_frame"], scene["end_frame"]):
                                stream.write(_frame(frame, layers, timeline).tobytes())
                except BrokenPipeError:
                    if encoder.wait() == 0:
                        raise
                if encoder.wait() != 0:
                    log.seek(0)
                    raise ValueError(f"FFmpeg video encoding failed: {log.read().decode(errors='replace').strip()}")
        except FileNotFoundError as error:
            raise ValueError("required executable not found: ffmpeg") from error


def write_cover(layers_path: Path, timeline_path: Path, dst: Path) -> None:
    timeline = load_timeline(timeline_path)
    first = timeline.scenes[0]
    layers = _open_layers(layers_path)[first["id"]]
    frame = _frame(first["end_frame"] - 1, layers, timeline, hide_captions=True)
    with staged_file(dst) as scratch:
        frame.save(scratch, format="PNG")
