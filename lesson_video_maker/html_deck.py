"""Package authored HTML and capture the same player used for preview."""
import json
import re
import shutil
from html import escape
from pathlib import Path

from .media import run_command
from .timeline import FPS, Timeline

RUNTIME = Path(__file__).parent
AUTHOR_FILES = ("scenes.html", "scenes.css", "scenes.js")


def stage_authoring(source: Path, deck: Path) -> None:
    missing = [name for name in AUTHOR_FILES if not (source / name).is_file()]
    if missing:
        raise ValueError(f"HTML deck is missing {', '.join(missing)} in {source}")
    deck.mkdir(parents=True)
    for name in AUTHOR_FILES:
        shutil.copyfile(source / name, deck / name)
    if (source / "assets").is_dir():
        shutil.copytree(source / "assets", deck / "assets")


def write_html_deck(timeline: Timeline, audio: Path, deck: Path) -> None:
    title = timeline.rows[0]["topic"]
    data = json.dumps(timeline.player_data(), ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    html = (RUNTIME / "html_player.html").read_text(encoding="utf-8")
    values = {"TITLE": escape(title), "DATA": data, "SCENES": (deck / "scenes.html").read_text(encoding="utf-8")}
    (deck / "index.html").write_text(
        re.sub(r"\[\[(TITLE|DATA|SCENES)\]\]", lambda match: values[match[1]], html),
        encoding="utf-8",
    )
    for name in ("html_player.js", "html_player.css", "html_icons.css", "html_motion.js"):
        shutil.copyfile(RUNTIME / name, deck / name)
    shutil.copyfile(audio, deck / "narration.wav")


def capture_html(deck: Path, frames: int, cover: Path, silent: Path) -> None:
    run_command(["node", str(RUNTIME / "capture_html.cjs"), str(deck / "index.html"),
                 str(frames), str(cover), str(silent)], timeout=max(180, frames / FPS * 12))
