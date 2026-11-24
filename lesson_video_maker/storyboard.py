"""Read and validate the editable JSONL storyboard."""
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


ID = re.compile(r"[a-z][a-z0-9-]{0,47}")
VISUAL_TYPES = {"reveal", "travel", "highlight", "html_motion"}
TYPES = {"project", "scene", "speak"} | VISUAL_TYPES


@dataclass(frozen=True)
class SpeechAnchor:
    speak_id: str
    point: str


@dataclass(frozen=True)
class Event:
    id: str
    type: str
    scene_id: str
    planned_start_ms: int
    planned_end_ms: int


@dataclass(frozen=True)
class SpeechEvent(Event):
    text: str
    caption: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class VisualEvent(Event):
    start_anchor: SpeechAnchor
    end_anchor: SpeechAnchor
    target: str


@dataclass(frozen=True)
class Scene:
    id: str
    title: str
    kind: str
    nodes: tuple[dict, ...]
    edges: tuple[dict, ...]
    code_lines: tuple[dict, ...]


@dataclass(frozen=True)
class Storyboard:
    project: dict
    scenes: tuple[Scene, ...]
    events: tuple[Event, ...]
    speech: tuple[SpeechEvent, ...]
    rows: tuple[dict, ...]

    @property
    def target_seconds(self) -> float:
        return self.project.get("target_seconds", 120)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _id(value) -> str:
    _require(isinstance(value, str) and bool(ID.fullmatch(value)), f"invalid ID {value!r}")
    return value


def _text(value, name: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{name} must be nonempty text")
    return value


def _list(value, name: str) -> list:
    _require(isinstance(value, list), f"{name} must be an array")
    return value


def _object(value, name: str) -> dict:
    _require(isinstance(value, dict), f"{name} must be an object")
    return value


def _unique(value: str, existing) -> None:
    _require(value not in existing, f"duplicate ID {value!r}")


def _project(row: dict) -> set[str]:
    _require(type(row.get("schema_version")) is int and row["schema_version"] == 1, "schema_version must be 1")
    _text(row.get("topic"), "topic")
    _text(row.get("audience"), "audience")
    duration = row.get("target_seconds", 120)
    _require(type(duration) in (int, float) and 0 < duration < math.inf,
             "target_seconds must be positive and finite")
    post = _object(row.get("post"), "post")
    _text(post.get("title"), "post.title")
    _text(post.get("description"), "post.description")
    for tag in _list(post.get("tags"), "post.tags"):
        _text(tag, "tag")
    sources = set()
    for entry in _list(row.get("sources"), "sources"):
        source = _object(entry, "source")
        source_id = _id(source.get("id"))
        _unique(source_id, sources)
        url = urlsplit(_text(source.get("url"), "source.url"))
        _require(url.scheme in {"http", "https"} and bool(url.hostname), "source URL must be HTTP(S)")
        _text(source.get("title"), "source.title")
        sources.add(source_id)
    return sources


def _scene(row: dict) -> Scene:
    scene_id = _id(row.get("id"))
    title = _text(row.get("title"), "scene.title")
    kind = row.get("kind")
    _require(kind in ("sequence", "flow", "code", "html"), f"invalid scene kind {kind!r}")
    nodes = _list(row.get("nodes", []), "nodes")
    edges = _list(row.get("edges", []), "edges")
    code = _list(row.get("code_lines", []), "code_lines")
    seen, node_ids = set(), set()
    for entries, label in ((nodes, "node"), (edges, "edge"), (code, "code line")):
        for entry in entries:
            entry = _object(entry, label)
            element_id = _id(entry.get("id"))
            _unique(element_id, seen)
            seen.add(element_id)
            if label == "node":
                _text(entry.get("label"), "node.label")
                node_ids.add(element_id)
            elif label == "edge":
                start, end = _id(entry.get("from")), _id(entry.get("to"))
                _require(start in node_ids and end in node_ids and start != end,
                         f"edge {element_id} must join two distinct nodes")
                _require(isinstance(entry.get("label", ""), str), "edge.label must be text")
            else:
                _require(isinstance(entry.get("text"), str) and "\n" not in entry["text"],
                         "code line must contain a single line of text")
    if kind == "html":
        _require(not nodes and not edges and not code, "an HTML scene uses markup for its visual elements")
    elif kind == "code":
        _require(bool(code) and not nodes and not edges, "code scene requires code_lines only")
    else:
        _require(bool(nodes) and not code, "diagram scene requires nodes")
    return Scene(scene_id, title, kind, tuple(nodes), tuple(edges), tuple(code))


def _anchor(value) -> SpeechAnchor:
    item = _object(value, "speech anchor")
    point = item.get("point")
    _require(point in ("start", "end"), f"invalid anchor point {point!r}")
    return SpeechAnchor(_id(item.get("speak_id")), point)


def _event(row: dict, sources: set[str]) -> Event:
    start, end = row.get("planned_start_ms"), row.get("planned_end_ms")
    _require(type(start) is int and type(end) is int and 0 <= start < end,
             "expected 0 <= planned_start_ms < planned_end_ms (integer milliseconds)")
    fields = (_id(row.get("id")), row["type"], _id(row.get("scene_id")), start, end)
    if row["type"] == "speak":
        source_ids = tuple(_id(item) for item in _list(row.get("source_ids"), "source_ids"))
        _require(set(source_ids) <= sources, "source_ids contains unknown sources")
        return SpeechEvent(*fields, _text(row.get("text"), "text"),
                           _text(row.get("caption"), "caption"), source_ids)
    return VisualEvent(*fields, _anchor(row.get("start_anchor")), _anchor(row.get("end_anchor")),
                       _id(row.get("target")))


def load_storyboard(path: Path) -> Storyboard:
    rows, scenes, events = [], {}, {}
    event_lines = {}
    project = None
    sources = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = _object(json.loads(line), "JSONL row")
            row_type = row.get("type")
            _require(isinstance(row_type, str) and row_type in TYPES, f"invalid row type {row_type!r}")
            if project is None:
                _require(row_type == "project", "first object must be a project")
                project = row
                sources = _project(row)
            elif row_type == "scene":
                scene = _scene(row)
                _unique(scene.id, scenes)
                scenes[scene.id] = scene
            elif row_type == "project":
                raise ValueError("duplicate project")
            else:
                event = _event(row, sources)
                _unique(event.id, events)
                events[event.id] = event
                event_lines[event.id] = line_number
            rows.append(row)
        except ValueError as error:
            raise ValueError(f"line {line_number}: {error}") from error
    _require(project is not None and bool(scenes), "storyboard requires a project and at least one scene")
    speech, reveals = [], set()
    scene_positions = {scene_id: position for position, scene_id in enumerate(scenes)}
    for event in events.values():
        try:
            _require(event.scene_id in scenes, f"unknown scene {event.scene_id}")
            scene = scenes[event.scene_id]
            if isinstance(event, SpeechEvent):
                if speech:
                    previous = speech[-1]
                    _require(event.planned_start_ms >= previous.planned_end_ms, "overlapping or unordered speech")
                    _require(scene_positions[event.scene_id] >= scene_positions[previous.scene_id],
                             "speech must follow scene declaration order")
                speech.append(event)
                continue
            for anchor, planned in ((event.start_anchor, event.planned_start_ms),
                                    (event.end_anchor, event.planned_end_ms)):
                spoken = events.get(anchor.speak_id)
                _require(isinstance(spoken, SpeechEvent) and spoken.scene_id == event.scene_id,
                         f"anchor {anchor.speak_id!r} must reference speech in scene {event.scene_id!r}")
                expected = spoken.planned_start_ms if anchor.point == "start" else spoken.planned_end_ms
                _require(planned == expected, f"planned time disagrees with anchor {anchor.speak_id!r}")
            if scene.kind == "html":
                _require(event.type == "html_motion", "an HTML scene uses html_motion actions")
                continue
            _require(event.type != "html_motion", "html_motion requires an HTML scene")
            targets = {"travel": scene.edges, "highlight": scene.code_lines,
                       "reveal": scene.nodes + scene.edges + scene.code_lines}
            _require(any(item["id"] == event.target for item in targets[event.type]),
                     f"unknown {event.type} target {event.target!r} in scene {event.scene_id!r}")
            if event.type == "reveal":
                _require((event.scene_id, event.target) not in reveals, f"duplicate reveal of {event.target!r}")
                reveals.add((event.scene_id, event.target))
        except ValueError as error:
            raise ValueError(f"line {event_lines[event.id]} ({event.id}): {error}") from error
    missing = set(scenes) - {event.scene_id for event in speech}
    _require(not missing, f"scene has no speech: {', '.join(sorted(missing))}")
    return Storyboard(project, tuple(scenes.values()), tuple(events.values()), tuple(speech), tuple(rows))
