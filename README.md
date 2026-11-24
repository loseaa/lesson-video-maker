# Lesson Video Maker · 动画教学视频制作

把一段自然语言需求变成一支带口播的动画教学视频。可以讲 MySQL 的 B+ 树，也可以讲《晏子使楚》这样的课文。Codex 根据受众和时长编写口播及分镜，渲染器把 HTML 动效对齐到实际配音，再导出 1080p MP4。

## 在 Codex 中使用

登录有仓库访问权的 GitHub CLI 账户后，可以把私有仓库克隆到个人 Skill 目录。工作区内使用时，把目标目录改为 `.agents/skills/lesson-video-maker`。安装后开启一个新的 Codex 对话。[Codex Skill 安装位置](https://developers.openai.com/api/reference/cli)

```sh
mkdir -p ~/.agents/skills
git -c credential.helper= -c 'credential.helper=!gh auth git-credential' clone \
  https://github.com/loseaa/lesson-video-maker.git ~/.agents/skills/lesson-video-maker
```

macOS 需要 Python 3.10+、Node.js 22+、Google Chrome、FFmpeg 和 ffprobe。在仓库或 Skill 根目录运行以下命令，使用同一个 Python 环境安装 Pillow 并启动 `render.sh`。

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

在 Codex 中试试这些提示词。

> 用 $lesson-video-maker 做一支五分钟视频，给刚学 SQL 的同学讲 MySQL 的 B+ 树索引。

> 用 $lesson-video-maker 把《晏子使楚》做成一支三分钟动画，讲给小学高年级的同学听。

推荐使用豆包语音合成 2.0，密钥在本机配置。免 Key 时用 macOS 的 `say` 配音，选择中文语音 Tingting。覆盖 Chrome 路径用 `LESSON_VIDEO_MAKER_CHROME`。[豆包配音设置](references/doubao-tts.md)

## 从已有剧本渲染

在仓库根目录运行下方命令，按 [JSONL 格式](references/storyboard.md) 和 [HTML 分镜约定](references/html-scenes.md) 准备剧本及动画。重复渲染可以复用工作目录里的旁白缓存，每次提供一个新的输出目录。

```sh
sh ./render.sh build /path/to/timeline.jsonl \
  --html-deck /path/to/scenes \
  --work-dir /path/to/work \
  --output /path/to/delivery \
  --tts say
```

成品包括 `video.mp4`、可离线播放和跳章的 `deck/index.html`、`subtitles.srt`、带实测时间的 `timeline.jsonl`、`cover.png` 和 `post.md`。分享 HTML 课件时请保留整个 `deck/` 目录。

## 投稿

按需配置 [B 站投稿](references/bilibili-publish.md) 或 [抖音投稿](references/douyin-publish.md)。两者分别依赖单独安装的 `biliup` 和 `sau`，并复用本机已授权的登录态。本机路径、登录凭据和个人浏览器配置单独保存。

```sh
sh ./render.sh publish-bilibili /path/to/delivery --dry-run
sh ./render.sh publish-douyin /path/to/delivery --dry-run
```

确认标题、简介、话题和目标账号后，去掉 `--dry-run` 提交。

## 运行测试

```sh
python -B -m unittest discover -s tests
node --test tests/*.test.cjs
```
