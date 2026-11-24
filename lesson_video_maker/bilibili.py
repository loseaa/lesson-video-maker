"""Prepare and submit a single finished explainer through biliup's web interface."""
import fcntl
import json
import re
import subprocess
import tempfile
from pathlib import Path

from .media import run_command, staged_file

ANSI = re.compile(r"\x1b\[[\d;]*m")
BVID = re.compile(r"\bBV[0-9A-Za-z]{10}\b")
REPLY_BVID = re.compile(r'\bbvid"?\s*:\s*"?(BV[0-9A-Za-z]{10})\b')


def local_profile() -> dict:
    config = Path(__file__).with_name("bilibili-local.json")
    if not config.is_file():
        return {}
    values = json.loads(config.read_text(encoding="utf-8"))
    if not isinstance(values, dict) or not all(isinstance(values.get(key, ""), str)
                                               for key in ("executable", "cookie_file")):
        raise ValueError("无效的本机 B 站发布配置")
    return values


def plan(bundle: Path, tid: int, tid_v2: int) -> dict:
    root = bundle.resolve()
    video, cover = root / "video.mp4", root / "cover.png"
    for file in (video, cover):
        if not file.is_file() or not file.stat().st_size:
            raise ValueError(f"缺少成品文件 {file.name}")
    with (root / "timeline.jsonl").open(encoding="utf-8") as source:
        try:
            project = json.loads(next(line for line in source if line.strip()))
            post = project["post"]
            title, description, tags = post["title"], post["description"], post["tags"]
        except (StopIteration, KeyError, TypeError, json.JSONDecodeError) as error:
            raise ValueError("定稿 JSONL 缺少投稿资料") from error
    if (project.get("type") != "project" or not isinstance(title, str) or not title.strip()
            or not isinstance(description, str) or not isinstance(tags, list)
            or not all(isinstance(tag, str) and tag.strip() for tag in tags)):
        raise ValueError("定稿 JSONL 的投稿标题、简介或标签格式无效")
    if not (0 < tid <= 65535 and 0 < tid_v2 <= 4294967295):
        raise ValueError("B 站分区 ID 超出 biliup 支持范围")
    return {"title": title, "description": description, "tags": tags, "video": str(video),
            "cover": str(cover), "tid": tid, "tid_v2": tid_v2,
            "creation_statement": {"id": 1}, "submit": "web"}


def _call(command: list[str], timeout: float) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, timeout=timeout)
    except FileNotFoundError as error:
        raise ValueError("找不到 biliup。请安装项目官方版本或用 --biliup 指定可执行文件。") from error


def _find_title(response: subprocess.CompletedProcess, title: str, bvid: str | None = None) -> dict | None:
    if response.returncode:
        raise ValueError("B 站稿件列表查询失败。请检查扫码授权和网络。")
    for line in ANSI.sub("", response.stdout).splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3 and parts[1].strip() == title.strip() and BVID.fullmatch(parts[0].strip()):
            if bvid is None or parts[0].strip() == bvid:
                return {"bvid": parts[0].strip(), "status": parts[2].strip()}
    return None


def _save_attempt(path: Path, data: dict) -> None:
    with staged_file(path) as scratch:
        scratch.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")


def _submit_locked(metadata: dict, executable: str, credentials: Path, attempt: Path) -> dict:
    base = [executable, "--rust-log", "info", "-u", str(credentials.resolve())]
    list_args = base + ["list", "--max-pages", "3"]
    try:
        existing = _find_title(_call(list_args, 60), metadata["title"])
    except subprocess.TimeoutExpired as error:
        raise ValueError("B 站稿件列表查询超时，尚未开始投稿。") from error
    if existing:
        return {"result": "existing", **existing}
    if attempt.exists():
        saved = json.loads(attempt.read_text(encoding="utf-8"))
        saved_id = saved.get("bvid") if isinstance(saved, dict) else None
        if isinstance(saved_id, str) and BVID.fullmatch(saved_id):
            return {"result": "receipt", "bvid": saved_id, "status": "已有投稿回执，当前状态待查询"}
        raise ValueError("上一轮投稿状态未确认。请先核对稿件，再决定是否重试。")
    with tempfile.TemporaryDirectory(prefix="lesson-video-maker-cover-") as temporary:
        cover = Path(temporary) / "cover.jpg"
        run_command(["ffmpeg", "-v", "error", "-i", metadata["cover"], "-frames:v", "1", "-q:v", "2", str(cover)])
        args = base + ["upload", "--submit", metadata["submit"],
                       "--tid", str(metadata["tid"]), "--tid-v2", str(metadata["tid_v2"]),
                       "--title", metadata["title"], "--desc", metadata["description"],
                       "--tag", ",".join(metadata["tags"]), "--copyright", "1",
                       "--no-reprint", "1", "--cover", str(cover),
                       "--extra-fields", json.dumps({"creation_statement": metadata["creation_statement"]}),
                       metadata["video"]]
        # A crash or timeout after the request leaves a receipt check pending.
        _save_attempt(attempt, {"result": "pending", "title": metadata["title"]})
        returned_id = None
        try:
            result = _call(args, 900)
            for line in (result.stdout + "\n" + result.stderr).splitlines():
                match = REPLY_BVID.search(line)
                if match and "ResponseData" in line:
                    returned_id = match[1]
                    break
        except subprocess.TimeoutExpired:
            pass
    try:
        visible = _find_title(_call(list_args, 60), metadata["title"], returned_id)
    except (ValueError, subprocess.TimeoutExpired):
        visible = None
    if visible:
        receipt = {"result": "submitted", **visible}
    elif returned_id:
        receipt = {"result": "receipt", "bvid": returned_id, "status": "已取得投稿回执，审核状态待查询"}
    else:
        raise ValueError("投稿状态未确认。请先通过稿件列表核对结果再重试。")
    _save_attempt(attempt, receipt)
    return receipt


def publish(bundle: Path, executable: str, credentials: Path, tid: int, tid_v2: int) -> dict:
    if not credentials.is_file():
        raise ValueError("缺少 biliup 授权文件。先执行 biliup -u <文件路径> login 扫码。")
    metadata = plan(bundle, tid, tid_v2)
    with (bundle / "timeline.jsonl").open("rb") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("这个成品目录正在投稿") from error
        return _submit_locked(metadata, executable, credentials, bundle / ".bilibili-submission.json")
