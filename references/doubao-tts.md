# 豆包语音合成 2.0

## 开通服务和保存密钥

1. 登录火山引擎的新版豆包语音控制台。切到要使用的项目，在「开通管理」里开通「豆包语音合成模型 2.0」。
2. 在同一项目的「API 管理」页面创建 API Key 并复制。Key 的项目需要与模型开通项目一致。[豆包语音控制台指引](https://docs.volcengine.com/docs/doubao-voice/console-guidance?lang=zh)
3. 在 macOS 终端运行以下命令，在密码提示处粘贴 Key 后回车。后续调用会从钥匙串读取。也可以由运行环境提供 `DOUBAO_TTS_API_KEY`，环境变量优先。

   ```sh
   /usr/bin/security add-generic-password -U -a "$(id -un)" -s lesson-video-maker.doubao-tts -w
   ```

Key 只在本机密码提示中输入。使用新版控制台的豆包语音项目 Key 作为 `X-Api-Key`。升级后也会读取原 Skill 已保存的钥匙串项目。

## 配音参数

- 使用 `seed-tts-2.0` 的 HTTP Chunked V3 接口。默认音色为渊博小叔 2.0，`zh_male_yuanboxiaoshu_uranus_bigtts`，支持自然语言语气指令。[官方接口](https://docs.volcengine.com/docs/doubao-voice/http-chunked-sse-unidirectional-streaming-v3?lang=zh) · [官方音色列表](https://docs.volcengine.com/docs/doubao-voice/tone-list-3?lang=zh)
- 语速 `-4`，音量 `0`，48 kHz PCM，开启字词字幕时间戳。使用接口默认的无结尾音频节奏标识设置。发布前按制品的投稿文案选择 AI 生成合成标识。[接口参数](https://docs.volcengine.com/docs/doubao-voice/http-chunked-sse-unidirectional-streaming-v3?lang=zh)
- 每场发送一段稿件。默认风格让问句自然上扬，问后短停，重点轻微重读。写清疑问和转折的位置。版本号、公式、缩写或符号可在 `text` 用念出的写法，在 `caption` 保留原样。把音色、语速和风格指令集中在 `lesson_video_maker/doubao_defaults.json`。
- HTML 动画和字幕使用实测口播时间，场景内保留模型生成的原始停顿。对时失败会指出对应场景或口播。成功的场景音频和时间戳会缓存到工作目录。
