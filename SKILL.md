---
name: lesson-video-maker
description: Use when the user wants to turn a lesson, concept, or teaching brief into a narrated animated video. Covers technical explainers, school lessons, and other educational topics, with an animated HTML deck, synchronized captions and MP4, and optional publishing to Bilibili or Douyin.
---

# 动画教学视频制作

根据题目设计原生 HTML 动画，用豆包语音合成 2.0 配音。HTML 预览和 MP4 共用实测口播时间轴。同一个浏览器逐帧渲染 MP4，所以 DOM、CSS 3D、Canvas 和 WebGL 的效果可以出现在成片里。

1. 提取题目、受众和时长。未指定时长时以 120 秒为目标。用与题目相符的一手资料核实内容，例如课文原文、官方文档或标准。选一个例子、情境或问题贯穿全片。
2. 读 [HTML 分镜与动效](references/html-scenes.md) 和 [JSONL 格式](references/storyboard.md)。每幕先确定观众要看到哪个变化、眼睛从哪里移到哪里、最后看清什么证据，再为这一幕做专用画面。给关键对象和状态配易辨认的小图标。同一对象跨幕沿用同一图形，变化时用状态符号和短标签提示。随内容切换构图，可以让收银界面、日志、动态图表、3D 结构或产品操作承担叙事。技术结构有深度、层级或空间路径时，可用 3D 剖面、分层、遮挡或镜头推进。
3. 将口播和动效写入草稿 `timeline.jsonl`。把每页重点词或短句放在独立口播段开头，并让放大、高亮或数据变化绑定到这段。元素用带缓动的移入、淡入、移出或淡出交接。重点先出现、再轻放大或提亮，留出阅读时间。用 `html_motion` 记录动作，JS 根据实测口播时间逐帧绘制。用本机 Chrome、Node.js 22+、Python 3.10+、Pillow 10+、FFmpeg 和 ffprobe。
4. 首次配音按 [豆包配音设置](references/doubao-tts.md) 存入 API Key。用户明确要免 Key 时用 `--tts say`。将脚本、工作目录和输出的绝对路径填入命令。

   ```sh
   sh /absolute/lesson-video-maker/render.sh build /absolute/draft/timeline.jsonl \
     --html-deck /absolute/draft/visuals --work-dir /absolute/work/video-job \
     --output /absolute/outputs/video --tts doubao
   ```

5. 抽看开场、一处机制变化、结尾验证的前后帧。关键内容出现时，先让动效或明暗差把注意力带过去，然后稳定下来给观众读。缩小画面检查关键图标是否仍能分清，以及它们会不会抢过主要数据和动作。检查字幕和 3D 镜头彼此留出空间，并验证跳转章节后的画面状态。需要改画面时复用工作目录的旁白缓存。
6. 核对 HTML、MP4、SRT、JSONL、封面和投稿文案并交付。用户授权 B 站投稿时用 [biliup 接口投稿](references/bilibili-publish.md)，读取生成目录里的稿件资料，复用本机扫码授权。按接口返回的稿件状态报告结果。

用户明确授权抖音投稿时，按 [抖音免 Key 投稿](references/douyin-publish.md) 使用本机 `sau` 登录态。核对作品管理页上的真实状态。
