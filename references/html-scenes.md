# HTML 分镜与动效

## 设计每一幕

为每一幕写下一句可观察的事实，再选能演示它的构图和动作。用同一套字体、色彩和数据连接整片，交替使用不同的页面结构。

- 讲规则或分支时，做出能操作的界面状态、条件表、终端或审批弹窗。让关键数字、异常或结果进入观众的视线，再停留到足够读清。
- 讲量变时，直接让计数、条形、曲线、表格单元格跟随口播更新。先建立对照基线，再展示变化。
- 讲空间结构、层级或移动时，用 CSS `perspective`、`transform-style: preserve-3d`、Canvas 或 WebGL。镜头推进、拆层、透明剖面或光照变化需要指向当前解释的部件。对焦以后保持方向和标签可读。把著作权清晰的本地素材放入 `assets/`。
- 讲请求或因果时，显示被传递的具体内容。逐字输入、游标、选区、结果弹出和局部放大都可以表现转折。只有方向和关系本身重要时才画连接线。
- 同一时刻以一个主要变化带视线。其余画面作为上下文保持稳定。在章节之间改变构图、尺度或光线，避免每个对象都用相同的渐显。动效完成时留下能看懂的证据。

在审看中使用真实导出的帧。对照每个关键口播前后的画面，检查凝视点和阅读时间、可读的 3D 标签、可解释的动画终态，以及小尺寸预览中的字幕区域。

## 让图标承载含义

给观众需要快速识别的对象一个可追踪的轮廓，例如文件、源服务器和本地缓存。同一份文件从空间画面切到表格时保留图标和文件名，使观众自然连接这两幕。等待、验证成功之类的状态用形状加短标签表达，颜色辅助识别。一个状态变化可让对应图标跟着口播出现或高亮。缩小预览时，主对象、状态符号和字幕应分得清。

播放器内置线性图标。把图标放在可读标签旁，按需要用 `--tx-icon-size` 和 `--tx-icon-color` 设置尺寸和颜色，默认继承周围文字。已有文字说明时加 `aria-hidden="true"`。

| `data-glyph` | 含义 |
| --- | --- |
| `server` | 服务器、服务端 |
| `cache` | 本地缓存或收纳槽 |
| `file` | 文件或文档 |
| `clock` | 有效期、等待 |
| `network` | 网络请求 |
| `terminal` | 终端或协议记录 |
| `check` | 已通过、已确认 |

```html
<span class="tx-icon" data-glyph="file" aria-hidden="true"></span>
<span>style.css</span>
```

专题需要其他符号时，在场景样式或本地素材中加入。优先给观众要追踪的对象配图标，让大数字和关键动作保有视觉优先级。

## 让平滑动效跟随讲述

先安排画面进场、重点出现、证据停留、交给下一个重点四个阶段。元素移动可以在到位前减速；退出可平移并淡出。视觉重点在讲到它的那个短句出现，轻微放大或提亮，随后回到稳定状态。连续两个重点交接时，让前一个淡下去。避免长句开头就播放句尾才解释的动画。

播放器预加载 `window.explainerMotion`。用 `phase(progress, start, end)` 从一段口播中取进场或退出所在的进度区间，`easeOut` 平滑到位，`easeInOut` 平滑起止。 `focus(progress)` 从 0 升到 1，停留后归零。 `pose(element, { x, y, opacity, scale })` 设置当前帧的平移、可见度和缩放，保留场景原有的旋转等 `transform`。示例中元素在说出关键句时移入并提亮。

```js
const { phase, easeOut, focus, pose } = window.explainerMotion;
const p = motion("show-confirmation").progress;
const entered = easeOut(phase(p, 0, .25));
const emphasis = focus(phase(p, .18, 1));
pose(element, { y: 24 * (1 - entered), opacity: entered, scale: 1 + .05 * emphasis });
```

审看时对照相应的口播，检查强调前一帧、强调峰值、证据稳定和退出前后的画面。由 JS 逐帧更新的属性直接写当前值，避免叠加 CSS `transition`。连续播放和往回拖动应该得到相同位置、透明度和强调状态。

## 与播放器接入

`--html-deck` 指向含以下文件的目录。包含文件名和资源路径均可直接在离线浏览器打开。

- `scenes.html` 是 HTML 片段。每幕用一个直属于舞台的 `<section data-scene="id">`，与 JSONL 的 `kind: "html"` 场景一一对应。舞台空间为 1600×900。每幕自己定义构图和背景，底部约 110 像素用于字幕。动作目标放在所属场景内，DOM `id` 在整个文件中唯一。Canvas 是合法目标。
- `scenes.css` 定义实际页面，不需要复制任何通用的卡片布局。可自由使用 Grid、Flexbox、透视、遮罩、渐变和媒体布局。在纯三维结构的关键部件旁保留正视标签。
- `scenes.js` 定义 `window.drawExplainerScene(context)`。每次调用根据当前帧重新设定 DOM 样式、Canvas 内容或相机姿态。任意帧直接跳转都应给出相同状态。DOM 使用插值，Canvas 每帧从输入重绘。如需等待图片解码或 3D 初始化，把对应 Promise 赋给 `window.explainerAssetsReady`，播放器会等待它。离线打开使用 `file://`，模型可用 CSS、程序几何或写入本地脚本的模型数据。用相对路径引用图片；把第三方依赖打包到本地脚本中。
- 可选 `assets/` 包含相对路径引用的本地素材。网页预览和视频导出一起打包。

`context` 提供 `scene`（场景 ID）、`root`（当前场景 DOM）、`frame`、`time`、`sceneTime` 和 `motion(id)`。时间单位为秒。传入 JSONL 动作 ID 得到 `{ progress, started, active }`。在开始前 `progress` 为 0，在结束后为 1。用它推进显示数值或镜头，关键帧之间可自行缓动或分段编排。动画时钟来自播放器。以 `Date.now()`、自由运行的 CSS 动画、网络请求或累加次数驱动的效果无法稳定跳帧。

```html
<section data-scene="lookup">
  <div class="space"><div id="cache-layer">浏览器缓存</div></div>
</section>
```

```css
.space { perspective: 950px; }
#cache-layer { transform-style: preserve-3d; }
```

```js
window.drawExplainerScene = ({ scene, root, motion }) => {
  if (scene !== "lookup") return;
  const p = motion("reveal-layer").progress;
  const layer = root.querySelector("#cache-layer");
  layer.style.transform = "translateZ(" + 140 * p + "px) rotateY(" + (12 - 24 * p) + "deg)";
  layer.style.opacity = String(0.25 + 0.75 * p);
};
```

JSONL 动作的 `id` 填 `reveal-layer`，`target` 填 `cache-layer`。安装的默认浏览器是 macOS Google Chrome，其他可执行路径通过 `LESSON_VIDEO_MAKER_CHROME` 指定。导出使用隔离的浏览器进程，展示内容按已测得的音频帧渲染。
