import json
import wave
from pathlib import Path


def rows():
    return [
        {"type": "project", "schema_version": 1, "topic": "工具调用", "audience": "开发者",
         "post": {"title": "工具调用", "description": "图解", "tags": ["AI"]}, "sources": []},
        {"type": "scene", "id": "request", "title": "一次请求", "kind": "sequence",
         "nodes": [{"id": "model", "label": "模型"}, {"id": "app", "label": "应用"}],
         "edges": [{"id": "edge", "from": "model", "to": "app", "label": "请求"},
                   {"id": "back", "from": "app", "to": "model", "label": "返回"}],
         "code_lines": []},
        {"type": "speak", "id": "call", "scene_id": "request", "planned_start_ms": 0,
         "planned_end_ms": 2000, "text": "模型请求。", "caption": "模型请求", "source_ids": []},
        {"type": "reveal", "id": "show-arrow", "scene_id": "request", "target": "edge",
         "planned_start_ms": 0, "planned_end_ms": 2000,
         "start_anchor": {"speak_id": "call", "point": "start"},
         "end_anchor": {"speak_id": "call", "point": "end"}},
        {"type": "travel", "id": "move-request", "scene_id": "request", "target": "edge",
         "planned_start_ms": 0, "planned_end_ms": 2000,
         "start_anchor": {"speak_id": "call", "point": "start"},
         "end_anchor": {"speak_id": "result", "point": "start"}},
        {"type": "speak", "id": "result", "scene_id": "request", "planned_start_ms": 2000,
         "planned_end_ms": 5000, "text": "应用返回结果。", "caption": "应用返回结果", "source_ids": []},
        {"type": "travel", "id": "move-result", "scene_id": "request", "target": "back",
         "planned_start_ms": 2000, "planned_end_ms": 5000,
         "start_anchor": {"speak_id": "result", "point": "start"},
         "end_anchor": {"speak_id": "result", "point": "end"}},
    ]


def write_rows(path: Path, data):
    path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in data), encoding='utf-8')
    return path


def write_wav(path: Path, samples: int):
    with wave.open(str(path), 'wb') as out:
        out.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
        out.writeframes(b'\0\0' * samples)
    return path
