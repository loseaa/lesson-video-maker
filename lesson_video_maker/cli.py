"""Run the independent preparation stages and publish a complete local bundle."""
import argparse
import fcntl
import hashlib
import json
import os
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from .assets import build_assets, load_layers
from . import bilibili, douyin
from .deck import write_deck
from .doubao import api_key, synthesize_scenes
from .html_deck import capture_html, stage_authoring, write_html_deck
from .media import staged_file
from .mux import mux_video
from .speech import synthesize
from .storyboard import SpeechEvent, Storyboard, load_storyboard
from .timeline import FPS, build_scene_timeline, build_timeline, load_timeline, write_audio, write_srt, write_timeline
from .video import write_cover, write_silent_video


class DurationMismatch(ValueError):
    pass


def _visual_key(story: Storyboard) -> str:
    content = [story.project["topic"], [asdict(scene) for scene in story.scenes]]
    events = []
    for event in story.events:
        if isinstance(event, SpeechEvent):
            events.append((event.id, event.scene_id, event.type, event.caption))
        else:
            events.append((event.id, event.scene_id, event.type, event.target))
    content.append(events)
    payload = json.dumps(content, ensure_ascii=False, sort_keys=True).encode("utf-8")
    assets_version = Path(__file__).with_name("assets.py").read_bytes()
    html_version = Path(__file__).with_name("deck.html").read_bytes()
    return hashlib.sha256(payload + assets_version + html_version).hexdigest()[:20]


def _prepare_visual(draft: Path, story: Storyboard, parent: Path) -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    directory = parent / _visual_key(story)
    manifest = directory / "layers.json"
    if manifest.is_file() and (directory / "slides.html").is_file():
        try:
            layers = load_layers(manifest)
        except (ValueError, TypeError, OSError):
            pass
        else:
            if {layer.scene_id for layer in layers} == {scene.id for scene in story.scenes}:
                return manifest
    with tempfile.TemporaryDirectory(prefix=".visual-", dir=parent) as temporary:
        candidate = Path(temporary) / "assets-build"
        build_assets(draft, candidate)
        if directory.exists():
            shutil.rmtree(directory)
        candidate.rename(directory)
    return manifest


def _post(story: Storyboard, duration: float) -> str:
    metadata = story.project["post"]
    tags = "、".join(metadata["tags"])
    lines = [f"# {metadata['title']}", "", metadata["description"], "", "## 投稿信息",
             "", f"- 时长 {duration:.1f} 秒", f"- 标签 {tags or '由投稿者填写'}",
             "- 投稿时选择 AI 生成合成标识", "", "## 资料来源", ""]
    for source in story.project["sources"]:
        title = source["title"].replace("[", "\\[").replace("]", "\\]")
        lines.append(f"- [{title}]({source['url']})")
    if not story.project["sources"]:
        lines.append("（剧本未列来源。）")
    return "\n".join(lines) + "\n"


def _require_new_output(output: Path) -> None:
    if os.path.lexists(output):
        raise ValueError(f"output already exists: {output}")


def _outside_target(total_frames: int, target_seconds: float) -> bool:
    target_frames = Decimal(str(target_seconds)) * FPS
    return abs(total_frames - target_frames) * 5 > target_frames


def _build_locked(source: Path, work: Path, output: Path, tts: str, authored: Path | None) -> float:
    draft = work / "draft" / "timeline.jsonl"
    if source != draft:
        with staged_file(draft) as scratch:
            scratch.write_bytes(source.read_bytes())
    story = load_storyboard(draft)
    kinds = {scene.kind for scene in story.scenes}
    if (authored is None and "html" in kinds) or (authored is not None and kinds != {"html"}):
        raise ValueError("--html-deck requires all scenes to use kind=html. HTML scenes require --html-deck.")
    key = api_key() if tts == "doubao" else None
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".lesson-video-maker-", dir=output.parent) as temporary:
        staged = Path(temporary) / "delivery"
        deck = staged / "deck"
        print(f"Preparing {tts} narration and visuals…", flush=True)
        with ThreadPoolExecutor(max_workers=2) as executor:
            if authored is None:
                visual = executor.submit(_prepare_visual, draft, story, work / "visual")
            else:
                visual = executor.submit(stage_authoring, authored, deck)
            if key is None:
                speech = executor.submit(synthesize, draft, work / "audio")
            else:
                speech = executor.submit(synthesize_scenes, draft, work / "audio", key)
            layers_path, tracks = visual.result(), speech.result()

        timeline_file = work / "timeline.jsonl"
        resolved = build_timeline(story, tracks) if key is None else build_scene_timeline(story, tracks)
        write_timeline(resolved, timeline_file)
        timeline = load_timeline(timeline_file)
        duration = timeline.total_frames / FPS
        if _outside_target(timeline.total_frames, story.target_seconds):
            raise DurationMismatch(f"actual duration {duration:.2f}s differs from target "
                                   f"{story.target_seconds:g}s by more than 20%; revise the storyboard")
        waveform = work / "narration.wav"
        write_audio(timeline, tracks, waveform)
        print(f"Rendering {timeline.total_frames} frames from the measured narration", flush=True)
        silent = work / "silent.mp4" if authored is None else Path(temporary) / "silent.mp4"
        if authored is None:
            write_deck(timeline_file, layers_path, waveform, deck)
            write_cover(layers_path, timeline_file, staged / "cover.png")
            write_silent_video(layers_path, timeline_file, silent)
        else:
            write_html_deck(timeline, waveform, deck)
            capture_html(deck, timeline.total_frames, staged / "cover.png", silent)
        write_srt(timeline, staged / "subtitles.srt")
        mux_video(silent, waveform, staged / "video.mp4")
        shutil.copyfile(timeline_file, staged / "timeline.jsonl")
        (staged / "post.md").write_text(_post(story, duration), encoding="utf-8")
        _require_new_output(output)
        staged.rename(output)
    return duration


def build(source: Path, work: Path, output: Path, tts: str = "say", html_deck: Path | None = None) -> float:
    if tts not in {"say", "doubao"}:
        raise ValueError(f"unknown narration provider {tts!r}")
    source, work = source.resolve(), work.resolve()
    # Preserve dangling symlinks at the output path as well as existing files.
    output = output.parent.resolve() / output.name
    _require_new_output(output)
    if output == work or output in work.parents or source == work / "timeline.jsonl":
        raise ValueError("choose distinct source, work, and final-output locations")
    work.mkdir(parents=True, exist_ok=True)
    with (work / ".build.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError(f"a build is running in {work}") from error
        return _build_locked(source, work, output, tts, html_deck.resolve() if html_deck else None)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a narrated animated lesson video")
    commands = parser.add_subparsers(dest="command", required=True)
    render = commands.add_parser("build")
    render.add_argument("timeline", type=Path)
    render.add_argument("--work-dir", required=True, type=Path)
    render.add_argument("--output", required=True, type=Path)
    render.add_argument("--tts", choices=("say", "doubao"), default="say")
    render.add_argument("--html-deck", type=Path, help="directory containing custom scenes.html/css/js")
    post = commands.add_parser("publish-bilibili", help="submit a finished bundle through biliup")
    post.add_argument("bundle", type=Path)
    post.add_argument("--biliup")
    post.add_argument("--cookie-file", type=Path)
    post.add_argument("--tid", type=int, default=231)
    post.add_argument("--tid-v2", type=int, default=1012)
    post.add_argument("--dry-run", action="store_true", help="print metadata without contacting Bilibili")
    douyin_post = commands.add_parser("publish-douyin", help="submit a finished bundle through sau")
    douyin_post.add_argument("bundle", type=Path)
    douyin_post.add_argument("--title", help="override the title sent to Douyin")
    douyin_post.add_argument("--account", help="override the locally authorized account alias")
    douyin_post.add_argument("--dry-run", action="store_true", help="print metadata without contacting Douyin")
    args = parser.parse_args(argv)
    try:
        if args.command == "publish-douyin":
            if args.dry_run:
                result = douyin.plan(args.bundle, args.title)
            else:
                profile = douyin.local_profile()
                if args.account:
                    profile["account"] = args.account
                result = douyin.publish(args.bundle, profile, args.title)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.command == "publish-bilibili":
            if args.dry_run:
                result = bilibili.plan(args.bundle, args.tid, args.tid_v2)
            else:
                profile = bilibili.local_profile()
                executable = args.biliup or os.environ.get("BILIUP_BIN") or profile.get("executable") or "biliup"
                credentials = args.cookie_file or os.environ.get("BILIUP_COOKIE_FILE") or profile.get("cookie_file")
                if not credentials:
                    raise ValueError("use --cookie-file or set BILIUP_COOKIE_FILE")
                result = bilibili.publish(args.bundle, executable, Path(credentials), args.tid, args.tid_v2)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        seconds = build(args.timeline, args.work_dir, args.output, args.tts, args.html_deck)
    except DurationMismatch as error:
        print(str(error), file=sys.stderr)
        return 3
    except (ValueError, OSError, EOFError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"Built {seconds:.2f}s — {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
