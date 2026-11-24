"""Package browser playback with local assets and frozen timing."""
import json
import re
import shutil
from dataclasses import asdict
from html import escape
from pathlib import Path

from .assets import load_layers
from .timeline import load_timeline


def write_deck(timeline_path: Path, layers_path: Path, audio_path: Path, deck_dir: Path) -> Path:
    timeline = load_timeline(timeline_path)
    layers = load_layers(layers_path)
    deck_dir.mkdir(parents=True, exist_ok=True)
    (deck_dir / "assets").mkdir(exist_ok=True)
    for layer in layers:
        shutil.copyfile(layers_path.parent / layer.file, deck_dir / layer.file)
    shutil.copyfile(audio_path, deck_dir / "narration.wav")
    for asset in ("deck.css", "player.js"):
        shutil.copyfile(Path(__file__).with_name(asset), deck_dir / asset)
    title = timeline.rows[0]["topic"]
    data = dict(timeline.player_data(), layers=[asdict(layer) for layer in layers], topic=title)
    data_json = json.dumps(data, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    template = (layers_path.parent / "slides.html").read_text(encoding="utf-8")
    values = {"TITLE": escape(title), "DATA": data_json}
    output = deck_dir / "index.html"
    output.write_text(re.sub(r"\[\[(TITLE|DATA)\]\]", lambda match: values[match[1]], template),
                      encoding="utf-8")
    return output
