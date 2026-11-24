# B 站接口投稿

使用 biliup 的 Web 投稿接口，适合个人创作账号。命令读取成品目录里的 `video.mp4`、`cover.png` 和 `timeline.jsonl`，取出标题、简介和标签。封面在本机转为 JPEG，接口请求携带「含 AI 生成内容」创作声明。授权投稿时运行该命令。

## 一次性授权

获取 [biliup 官方发布包](https://github.com/biliup/biliup/releases/latest)，在本机私有目录创建自己的登录文件，使用 B 站 App 扫码并确认。之后复用授权文件。

```sh
umask 077
/absolute/biliup -u /absolute/private/cookies.json login
```

授权文件单独保存在本机。已连接账号的本机 Skill 可在 `lesson_video_maker/bilibili-local.json` 记录可执行文件路径和授权文件路径，字段为 `executable` 与 `cookie_file`。也可通过 `--biliup` 和 `--cookie-file` 或环境变量 `BILIUP_BIN` 和 `BILIUP_COOKIE_FILE` 覆盖本机配置。[biliup 命令参考](https://doc.biliup.rs/guide/configs/config.html)

## 预检和提交

```sh
sh /absolute/lesson-video-maker/render.sh publish-bilibili /absolute/outputs/video --dry-run

sh /absolute/lesson-video-maker/render.sh publish-bilibili /absolute/outputs/video
```

预检打印本地投稿资料。真实投稿先通过接口检查近期同名稿件，找到后返回现有 BV 号和状态。接口已发出但回执不明确时，先用 `biliup list` 核对稿件，再决定是否重试。成品目录中的本地回执用于记住已有尝试。

默认用旧版计算机技术分区 231、新版科技数码分区 1012。可以通过 `--tid` 和 `--tid-v2` 指定其他已核实分区。自制投稿采用禁止转载配置。状态以 B 站接口为准，审核中和开放浏览分别报告。[B 站创作声明公告](https://www.bilibili.com/opus/1106496554576904197)
