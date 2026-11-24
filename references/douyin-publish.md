# 抖音免 Key 投稿

已安装的 `sau` 通过抖音创作者中心提交视频。首次用抖音 App 扫码，之后由本机的 `sau` 管理和复用登录态。发布时如抖音要求短信验证，按当前创作者中心窗口提示操作。[sau 抖音命令](https://github.com/dreammis/social-auto-upload/blob/v1.0.0-skills.2/docs/CLI.md#抖音-cli-子命令)

## 连接账号

按 [social-auto-upload 安装指南](https://github.com/dreammis/social-auto-upload/blob/v1.0.0-skills.2/docs/install.md) 安装独立的 `sau` 运行环境。用 `sau douyin upload-video --help` 确认有 `--thumbnail-landscape`、`--thumbnail-portrait`、`--declaration` 和 `--headed`。

在 `sau` 工作目录执行：

```sh
umask 077
/absolute/sau douyin login --account creator --headed
/absolute/sau douyin check --account creator
```

本机 `lesson_video_maker/douyin-local.json` 保存三个配置字段。`executable` 为 `sau` 绝对路径，`workdir` 为 `sau` 工作目录，`account` 为扫码使用的本地别名。该配置及登录凭据随本机安装使用。

## 从成品目录投稿

```sh
sh /absolute/lesson-video-maker/render.sh publish-douyin /absolute/outputs/video --dry-run
sh /absolute/lesson-video-maker/render.sh publish-douyin /absolute/outputs/video
```

预检显示视频路径、标题、简介、话题和 AI 声明。使用 `--title` 调整抖音标题，用 `--account` 选择已登录账号。真实投稿需要用户对目标作品和抖音账号的明确授权。

上传读取 `video.mp4`、`cover.png` 和定稿 `timeline.jsonl`。保留成片画幅，用原封面生成 4:3 和 3:4 两版，并选择「内容由AI生成」。如有短信验证，请在打开的抖音窗口完成。浏览器会话和验证窗口由本机的 `sau` 版本管理。[抖音 AI 标识说明](https://trust.douyin.com/article/15868)

投稿回执保存在成品目录里的 `.douyin-submission-<账号别名>.json`。命令打开作品管理后，核对本次作品的标题和状态。状态不明时，先查作品管理页或账号主页，确认结果后再决定是否重试。
