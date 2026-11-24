"""Create the same raster layers for browser playback and video export."""
import json
import math
import re
from dataclasses import asdict, dataclass
from functools import lru_cache
from html import escape
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .storyboard import Scene, SpeechEvent, load_storyboard

WIDTH, HEIGHT = 1920, 1080
MINT = "#74f4ce"
GOLD = "#ffc480"
PAPER = "#edf3fb"
MUTED = "#a1b1c7"
FONT = Path("/System/Library/Fonts/Hiragino Sans GB.ttc")
MONO = Path("/System/Library/Fonts/Menlo.ttc")
PALETTE = {"sequence": "调用时序", "flow": "信息流向", "code": "代码执行"}


@dataclass(frozen=True)
class Layer:
    file: str
    scene_id: str
    x: int
    y: int
    z: int
    mode: str = "base"
    event_id: str | None = None
    to_x: int | None = None
    to_y: int | None = None


@lru_cache(maxsize=36)
def font(size: int, bold=False, mono=False):
    if mono and MONO.exists():
        return ImageFont.truetype(str(MONO), size)
    path = FONT if FONT.exists() else Path("/System/Library/Fonts/STHeiti Medium.ttc")
    index = (2 if bold else 0) if path == FONT else 1
    return ImageFont.truetype(str(path), size, index=index)


def _width(draw, text, face):
    return draw.textlength(text, font=face)


def _fit(draw, text, limit, size, minimum, *, bold=False, mono=False):
    for point in range(size, minimum - 1, -2):
        face = font(point, bold, mono and text.isascii())
        if _width(draw, text, face) <= limit:
            return face
    raise ValueError(f"text is too wide: {text[:50]!r}")


def _draw_background(project, scene):
    image = Image.new("RGBA", (WIDTH, HEIGHT), "#0a1324")
    draw = ImageDraw.Draw(image, "RGBA")
    for y in range(HEIGHT):
        t = y / HEIGHT
        draw.line((0, y, WIDTH, y), fill=(int(12 + t * 8), int(21 + t * 11), int(39 + t * 15), 255))
    for x in range(90, WIDTH - 75, 32):
        for y in range(333, 883, 32):
            draw.point((x, y), fill=(64, 83, 111, 255))
    draw.line((104, 142, 1816, 142), fill="#334660", width=2)
    draw.rounded_rectangle((104, 80, 116, 116), radius=5, fill=MINT)
    topic = " ".join(project["topic"].split())
    topic_font = _fit(draw, topic, 1370, 40, 24, bold=True)
    draw.text((140, 97), topic, font=topic_font, fill=PAPER, anchor="lm")
    draw.text((1816, 97), PALETTE[scene.kind], font=font(28), fill=MINT, anchor="rm")
    title = " ".join(scene.title.split())
    draw.text((104, 230), title, font=_fit(draw, title, 1712, 76, 40, bold=True), fill=PAPER, anchor="lm")
    draw.line((104, 900, 1816, 900), fill="#40516a", width=2)
    return image


def _draw_card(label, width, height, accent):
    tile = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(tile)
    draw.rounded_rectangle((2, 2, width - 3, height - 3), radius=32, fill="#162740",
                           outline="#536885", width=2)
    draw.rounded_rectangle((32, 28, 91, 36), radius=4, fill=accent)
    primary, _, rest = label.partition("\n")
    rest = " ".join(rest.split())
    if rest:
        main_y, detail_y = int(height * .46), int(height * .73)
        draw.text((width / 2, detail_y), rest, font=_fit(draw, rest, width - 44, 30, 21),
                  fill=MUTED, anchor="mm")
    else:
        main_y = int(height * .58)
    draw.text((width / 2, main_y), primary, font=_fit(draw, primary, width - 46, 48, 26, bold=True),
              fill=PAPER, anchor="mm")
    return tile


def _caption(text: str):
    clean = " ".join(text.split())
    tile = Image.new("RGBA", (1670, 135))
    draw = ImageDraw.Draw(tile)
    face = _fit(draw, clean, 1560, 48, 32, bold=True)
    panel_width = max(330, math.ceil(_width(draw, clean, face)) + 105)
    left = (tile.width - panel_width) // 2
    draw.rounded_rectangle((left, 21, left + panel_width, 112), radius=30, fill="#080f1e",
                           outline="#405775", width=2)
    draw.text((835, 66), clean, font=face, fill=PAPER, anchor="mm")
    return tile


def _arrow(start, end, label, label_y):
    x1, y = start
    x2, _ = end
    direction = 1 if x2 > x1 else -1
    stroke = MINT if direction == 1 else GOLD
    image = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    draw.line((x1, y, x2, y), fill=stroke, width=5)
    draw.polygon([(x2, y), (x2 - direction * 24, y - 13), (x2 - direction * 24, y + 13)], fill=stroke)
    if label.strip():
        clean = " ".join(label.split())
        face = _fit(draw, clean, 420, 29, 21)
        mid = (x1 + x2) // 2
        draw.text((mid, label_y), clean, fill=stroke, anchor="mm", font=face, stroke_width=6,
                  stroke_fill="#132039")
    bounds = image.getbbox()
    return image.crop(bounds), bounds[0], bounds[1]


def _packet(is_return):
    image = Image.new("RGBA", (56, 56))
    draw = ImageDraw.Draw(image)
    draw.ellipse((3, 3, 52, 52), fill="#174335" if not is_return else "#533717")
    draw.ellipse((11, 11, 44, 44), fill=GOLD if is_return else MINT, outline="#fbffff", width=3)
    draw.ellipse((22, 20, 32, 30), fill="#fbffff")
    return image


def _diagram(scene: Scene, add):
    amount = len(scene.nodes)
    if amount > 4 or len(scene.edges) > 6:
        raise ValueError("split diagrams with more than four participants or six edges")
    sequence = scene.kind == "sequence"
    width = {1: 530, 2: 500, 3: 428, 4: 350}[amount]
    height = 155 if sequence else 244
    centers = {}
    for i, node in enumerate(scene.nodes):
        x = 960 if amount == 1 else round(104 + (1712 - width) * i / (amount - 1) + width / 2)
        centers[node["id"]] = x
        add(_draw_card(node["label"], width, height, MINT if i % 2 == 0 else GOLD),
            node["id"], x - width // 2, 330 if sequence else 383, 5, element=True)
        if sequence:
            line = Image.new("RGBA", (4, 388))
            pen = ImageDraw.Draw(line)
            for y in range(0, line.height, 16):
                pen.line((1, y, 1, min(y + 8, line.height - 1)), fill="#7788a4", width=2)
            add(line, "lifeline-" + node["id"], x - 2, 487, 1)
    routes = {}
    lane_counts = {}
    for i, edge in enumerate(scene.edges):
        src, dst = centers[edge["from"]], centers[edge["to"]]
        direction = 1 if dst > src else -1
        lane = tuple(sorted((src, dst)))
        pair_index = lane_counts.get(lane, 0)
        lane_counts[lane] = pair_index + 1
        if sequence:
            first, last = src + direction * 10, dst - direction * 10
            y = 522 + i * 59
            label_y = y + 24
        else:
            first = src + direction * (width // 2 + 11)
            last = dst - direction * (width // 2 + 12)
            if abs(dst - src) > (1712 - width) / max(1, amount - 1) + 2:
                first, last = src, dst
                y = 723 + i * 27
                label_y = y - 24
            else:
                y = 491 + pair_index * 31
                label_y = 669 + pair_index * 37
        card, left, top = _arrow((first, y), (last, y), edge.get("label", ""), label_y)
        add(card, edge["id"], left, top, 3, element=True)
        routes[edge["id"]] = (first, last, y)
    return routes


def _code(scene: Scene, add):
    if len(scene.code_lines) > 8:
        raise ValueError("split code scenes with more than eight lines")
    panel = Image.new("RGBA", (1680, 532))
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle((1, 1, 1678, 530), radius=30, fill="#111f34", outline="#526480", width=2)
    add(panel, "code-panel", 120, 326, 1)
    coordinates = {}
    for idx, line in enumerate(scene.code_lines):
        row = Image.new("RGBA", (1590, 59))
        draw = ImageDraw.Draw(row)
        draw.text((25, 30), f"{idx + 1:02d}", font=font(28, mono=True), fill=MUTED, anchor="lm")
        label = line["text"].expandtabs(4)
        face = _fit(draw, label, 1450, 39, 28, mono=True)
        draw.text((90, 30), label, font=face, fill=PAPER, anchor="lm")
        start = (165, 346 + idx * 60)
        add(row, line["id"], *start, 5, element=True)
        coordinates[line["id"]] = start
    return coordinates


def _build_scene(scene, story, directory):
    events = [event for event in story.events if event.scene_id == scene.id]
    reveals = {event.target: event.id for event in events if event.type == "reveal"}
    layers = []

    def add(image, name, x, y, z, *, element=False, mode="base", event_id=None, to=None):
        if element and name in reveals:
            mode, event_id = "reveal", reveals[name]
        file = f"assets/{scene.id}-{len(layers):03d}.png"
        image.save(directory / file)
        destination = to if to is not None else (None, None)
        layers.append(Layer(file, scene.id, x, y, z, mode, event_id, *destination))

    try:
        add(_draw_background(story.project, scene), "backdrop", 0, 0, 0)
        placement = _code(scene, add) if scene.kind == "code" else _diagram(scene, add)
        for event in events:
            if isinstance(event, SpeechEvent):
                add(_caption(event.caption), event.id, 125, 910, 12, mode="caption", event_id=event.id)
            elif event.type == "travel":
                first, last, y = placement[event.target]
                add(_packet(last < first), event.id, first - 28, y - 28, 9, mode="travel",
                    event_id=event.id, to=(last - 28, y - 28))
            elif event.type == "highlight":
                x, y = placement[event.target]
                tile = Image.new("RGBA", (1590, 59))
                pen = ImageDraw.Draw(tile)
                pen.rounded_rectangle((1, 1, 1587, 57), radius=12, fill="#234a46", outline=MINT, width=2)
                add(tile, event.id, x, y, 4, mode="highlight", event_id=event.id)
    except ValueError as error:
        raise ValueError(f"scene {scene.id}: {error}") from error
    return layers


def build_assets(timeline_path: Path, visual_dir: Path) -> Path:
    story = load_storyboard(timeline_path)
    (visual_dir / "assets").mkdir(parents=True, exist_ok=True)
    layers = [layer for scene in story.scenes for layer in _build_scene(scene, story, visual_dir)]
    base = Path(__file__).with_name("deck.html").read_text(encoding="utf-8")
    options = "".join(f'<button class="chapter" type="button" data-scene="{scene.id}">'
                      f'{escape(scene.title)}</button>' for scene in story.scenes)
    (visual_dir / "slides.html").write_text(base.replace("[[SCENE_BUTTONS]]", options), encoding="utf-8")
    path = visual_dir / "layers.json"
    path.write_text(json.dumps([asdict(layer) for layer in layers], ensure_ascii=False), encoding="utf-8")
    return path


def load_layers(path: Path) -> list[Layer]:
    layers = [Layer(**entry) for entry in json.loads(path.read_text(encoding="utf-8"))]
    for layer in layers:
        if not re.fullmatch(r"assets/[a-z][a-z0-9-]*-\d+\.png", layer.file):
            raise ValueError(f"invalid layer path {layer.file!r}")
        if not (path.parent / layer.file).is_file():
            raise ValueError(f"missing layer {layer.file}")
    return layers
