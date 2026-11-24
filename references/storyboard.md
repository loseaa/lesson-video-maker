# JSONL 剧本与渲染

每行一个有效 JSON 对象，UTF-8 编码。项目首行是 `project`，每幕由一条 `scene` 定义。每条口播或动画是一个单独操作。按场景与播放顺序列口播，允许动画引用后面的口播行。各标识使用小写英文、数字和连字符，首字符为字母。重复的操作 ID、越场景引用、交叠口播和顺序错误会报行号。

- `project` 带 `schema_version: 1`、`topic`、`audience`、可选 `target_seconds`、`post` 和 `sources`。投稿对象有 `title`、`description`、字符串数组 `tags`。来源数组每项有 `id`、`title`、HTTP 或 HTTPS `url`。
- `scene` 带 `id`、`title`、`kind`。时序 `sequence` 和数据流 `flow` 用 `nodes` 与 `edges`。节点有 `id`、`label`，标签可用一个换行分隔名称与简短说明。边有 `id`、`from`、`to` 和可选 `label`，双向调用分别写两条边。每幕最多四个节点或六条边，密集内容拆幕。代码 `code` 用 `code_lines`，每行有 `id` 与 `text`，每幕最多八行。
- `speak` 写 `id`、`scene_id`、`planned_start_ms`、`planned_end_ms`、`text`、`caption`、`source_ids`。用 `text` 写实际读法，用 `caption` 保留技术术语写法。计划用整数毫秒。豆包保留场景内原始停顿，场景之间按计划留白。Tingting 把相邻口播计划区间的空档转成静音。
- `reveal` 揭示节点、箭头或代码行，完成后在当前场景保留。 `travel` 沿指定边移动。 `highlight` 高亮指定代码行。除共同的 ID、场景和计划边界外，需要 `target`、`start_anchor`、`end_anchor`。锚点对象包含 `speak_id` 和 `point`，只能取 `start` 或 `end`。动作两端的计划毫秒必须等于引用短句的相应计划边界。实际动作帧从真实口播边界计算。
- 豆包用字幕时间戳定位每条口播的开始和结尾，整场 WAV 直接进入成片。Tingting 的每句至少保留 12 帧槽位，句末动画锚点取实测音频末尾。每个动画至少 6 帧。成片默认 1920×1080、30 fps。HTML 用浏览器的 WAV 播放时钟显示同一套图层。

## 自定义 HTML 场景

新视频默认用 [HTML 分镜](html-scenes.md)。场景设 `kind: "html"`，把视觉元素写在 `scenes.html`。增加 `type: "html_motion"` 动作，填写 `id`、`scene_id`、`target`、两端的计划毫秒和口播锚点。使用口播 ID 的 `start` 或 `end`；实际帧由口播时间决定。 `target` 是该幕内 DOM 元素 ID。运行时通过 `motion(动作 ID)` 读取进度。每个关键揭示、计数、转场或相机移动用自己的动作行。

使用 `--html-deck` 时本片各幕统一声明 `kind: "html"`，场景的布局与风格由各自的 HTML/CSS 决定。下面的卡片、代码和箭头示例适合维护旧剧本。

## 从可见的变化出发

先选一个可以贯穿短片的请求、错误或操作，带着同一组值走完过程。分镜中标明观众在口播前后分别看到什么。具体的输入、输出来回出现时保留相同名称和数值，让观众容易追踪。

- **对照输入与结果。** 用 `flow` 卡片并列展示预期与实际，`edges` 可以为空。用 `reveal` 在口播提及时显示差值、错误或结果。比如购物车应收 100 元，实际只收 90 元。
- **展示证据。** 用 `code` 呈现简短的请求、代码、终端输出或测试记录。用 `reveal` 让输出随叙述出现，用 `highlight` 标出读者该看的断言、分支或报错。先放影响判断的行，再按需要补上下文。
- **表现条件和状态。** 用 `flow` 并排呈现可交付、达到上限、等待审批等不同结果，在说到相应条件时逐个揭示。跨幕可以保留同一变量或卡片的位置，并更新其显示值，表现状态随操作改变。
- **追踪传递。** 需要说明谁发请求、谁执行、谁收到返回时，用 `sequence` 加 `travel`，并在边上标明传递的实际内容。返回结果与发出请求放在各自的口播节拍上。

渲染器支持渐显、沿边移动和按行高亮。需要替换显示值时可切到下一幕并保持布局，在画面切换处对齐口播。讲解不需要的参与者、连线、装饰动画和画面上的重复文案可以省略。

下面的例子用两张卡片显示缓存写入，无需连线。完整短片按实际目标填时长。

```jsonl
{"type":"project","schema_version":1,"topic":"缓存如何避免重复查询","audience":"开发者","target_seconds":20,"post":{"title":"缓存","description":"同一个请求只查询一次数据库","tags":["缓存"]},"sources":[]}
{"type":"scene","id":"miss","title":"第一次查询，留下结果","kind":"flow","nodes":[{"id":"query","label":"查询商品 A\n缓存未命中"},{"id":"entry","label":"缓存已写入\n100 元 · 已查库 1 次"}],"edges":[]}
{"type":"speak","id":"query-db","scene_id":"miss","planned_start_ms":0,"planned_end_ms":2700,"text":"第一次查询商品，缓存里还没有。","caption":"第一次查询，缓存未命中","source_ids":[]}
{"type":"speak","id":"store","scene_id":"miss","planned_start_ms":2700,"planned_end_ms":5400,"text":"数据库返回一百元，把价格存入缓存。","caption":"把价格 100 元写入缓存","source_ids":[]}
{"type":"reveal","id":"show-entry","scene_id":"miss","target":"entry","planned_start_ms":2700,"planned_end_ms":5400,"start_anchor":{"speak_id":"store","point":"start"},"end_anchor":{"speak_id":"store","point":"end"}}
```

定稿附加实际帧、毫秒、样本数和偏移。编辑草稿后重跑可复用未改变的旁白和图层。最终目录包含 `deck/index.html`，浏览器可直接打开整个目录中的入口。单独传输 HTML 项目时，把 `deck` 连同它的音频和图层一起打包。
