"""Prepare and submit an explainer through a locally authorized sau account."""
import fcntl
import json
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

from .media import staged_file


def local_profile() -> dict:
    config = Path(__file__).with_name("douyin-local.json")
    if not config.is_file():
        raise ValueError("缺少本机抖音配置。先设置 sau 路径并扫码登录。")
    profile = json.loads(config.read_text(encoding="utf-8"))
    keys = ("executable", "workdir", "account")
    if not isinstance(profile, dict) or any(
        not isinstance(profile.get(key), str) or not profile[key] for key in keys
    ):
        raise ValueError("无效的本机抖音配置")
    return profile


def plan(bundle: Path, title: str | None) -> dict:
    bundle = bundle.resolve()
    video, cover = bundle / "video.mp4", bundle / "cover.png"
    for item in (video, cover):
        if not item.is_file() or not item.stat().st_size:
            raise ValueError(f"缺少成品文件 {item.name}")
    try:
        with (bundle / "timeline.jsonl").open(encoding="utf-8") as timeline:
            project = json.loads(next(line for line in timeline if line.strip()))
        post = project["post"]
        original_title, description, tags = post["title"], post["description"], post["tags"]
    except (StopIteration, KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("定稿 JSONL 缺少投稿资料") from error
    if (project.get("type") != "project" or not isinstance(original_title, str)
            or not isinstance(description, str) or not isinstance(tags, list)
            or not all(isinstance(tag, str) and tag.strip(" #,") for tag in tags)):
        raise ValueError("定稿 JSONL 的投稿标题、简介或话题格式无效")
    selected = (title if title is not None else original_title).strip()
    if not selected or title is not None and len(selected) > 30:
        raise ValueError("抖音投稿标题需要 1 至 30 个字")
    if len(selected) > 30:
        selected = selected[:29].rstrip() + "…"
    topics = list(dict.fromkeys(
        tag.strip().lstrip("#").replace(",", "，") for tag in tags
    ))
    return {"title": selected, "description": description, "tags": topics,
            "video": str(video), "cover": str(cover), "declaration": "内容由AI生成"}


def _call(args: list[str], workdir: Path, timeout: float) -> subprocess.CompletedProcess:
    return subprocess.run(
        args, cwd=workdir, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=None if args[2] == "upload-video" else subprocess.PIPE,
        encoding="utf-8", errors="replace", timeout=timeout, umask=0o077,
    )


def _cover(source: Path, size: tuple[int, int], output: Path) -> None:
    with Image.open(source) as raw:
        original = ImageOps.exif_transpose(raw).convert("RGB")
    backing = ImageOps.fit(original, size, method=Image.Resampling.LANCZOS)
    backing = backing.filter(ImageFilter.GaussianBlur(27))
    backing = Image.blend(backing, Image.new("RGB", size, "#172727"), .28)
    foreground = ImageOps.contain(original, size, Image.Resampling.LANCZOS)
    backing.paste(foreground, ((size[0] - foreground.width) // 2,
                              (size[1] - foreground.height) // 2))
    backing.save(output, format="JPEG", quality=91, optimize=True)


def _save_receipt(path: Path, value: dict) -> None:
    with staged_file(path) as candidate:
        candidate.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")


def publish(bundle: Path, runtime: dict, title: str | None) -> dict:
    metadata = plan(bundle, title)
    account = runtime["account"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", account):
        raise ValueError("抖音本地账号别名只能用字母、数字、连字符和下划线")
    workdir = Path(runtime["workdir"])
    base = [runtime["executable"], "douyin"]
    receipt = bundle / f".douyin-submission-{account}.json"
    account_lock = workdir / f".douyin-{account}.lock"
    with (bundle / "timeline.jsonl").open("rb") as lock, account_lock.open("a") as profile_lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("这个成品目录正在投稿") from error
        if receipt.exists():
            saved = json.loads(receipt.read_text(encoding="utf-8"))
            if saved.get("result") == "submitted":
                return {**saved, "result": "existing"}
            raise ValueError("上次抖音投稿状态未确认。先核对创作者中心作品列表。")

        try:
            fcntl.flock(profile_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("这个抖音账号正在处理另一条投稿") from error

        try:
            login = _call(base + ["check", "--account", account], workdir, 90)
        except subprocess.TimeoutExpired as error:
            raise ValueError("抖音登录检查超时，尚未开始投稿。") from error
        if login.returncode or "valid" not in login.stdout.splitlines():
            raise ValueError("抖音登录检查未通过。确认本机扫码登录态后再试。")

        with tempfile.TemporaryDirectory(prefix="lesson-video-maker-douyin-") as temp:
            landscape, portrait = Path(temp) / "cover-4x3.jpg", Path(temp) / "cover-3x4.jpg"
            source = Path(metadata["cover"])
            _cover(source, (1200, 900), landscape)
            _cover(source, (900, 1200), portrait)
            command = base + ["upload-video", "--account", account, "--file", metadata["video"],
                              "--title", metadata["title"], "--desc", metadata["description"],
                              "--tags", ",".join(metadata["tags"]),
                              "--thumbnail-landscape", str(landscape),
                              "--thumbnail-portrait", str(portrait),
                              "--declaration", metadata["declaration"], "--headed"]
            result = {"title": metadata["title"], "account": account}
            _save_receipt(receipt, {**result, "result": "pending"})
            try:
                submitted = _call(command, workdir, 720)
            except subprocess.TimeoutExpired as error:
                raise ValueError("抖音投稿状态未确认。先核对作品列表。") from error

        if submitted.returncode or not any(
            line.startswith("Douyin video upload submitted:") for line in submitted.stdout.splitlines()
        ):
            raise ValueError("抖音投稿状态未确认。先核对作品列表。")
        result.update(result="submitted", status="已进入作品管理，审核状态待查询")
        _save_receipt(receipt, result)
        return result
