# 配置示例 (Configuration Examples)

本文档提供了各种使用场景下的配置示例，帮助你快速配置项目。

## 📋 目录

- [基础配置](#基础配置)
- [LLM配置示例](#llm配置示例)
- [TTS配置示例](#tts配置示例)
- [弹幕采集模式](#弹幕采集模式)
- [流量控制配置](#流量控制配置)
- [完整配置示例](#完整配置示例)

## 基础配置

### 最小配置（免费方案）

使用免费的 ChatGLM + Edge TTS：

```yaml
# danmaku_config.yaml

danmaku:
  use_mock: true  # 开发测试用
  use_proxy: false

selected_module:
  LLM: ChatGLMLLM
  TTS: EdgeTTS

LLM:
  ChatGLMLLM:
    type: openai
    model_name: glm-4-flash  # 免费模型
    url: https://open.bigmodel.cn/api/paas/v4/
    api_key: your_api_key_here

TTS:
  EdgeTTS:
    type: edge
    voice: zh-CN-XiaoxiaoNeural
    output_dir: tmp/

prompt: |
  你是一个直播间的AI助手，名叫小智。
  回复要简洁明快，每次回复控制在50字以内。
```

## LLM配置示例

### OpenAI GPT-4o-mini

```yaml
selected_module:
  LLM: OpenAILLM

LLM:
  OpenAILLM:
    type: openai
    model_name: gpt-4o-mini
    url: https://api.openai.com/v1/
    api_key: sk-your-api-key-here
```

### Google Gemini

```yaml
selected_module:
  LLM: GeminiLLM

LLM:
  GeminiLLM:
    type: gemini
    model_name: gemini-2.0-flash-exp
    api_key: your-gemini-api-key
```

### ChatGLM (智谱AI)

```yaml
selected_module:
  LLM: ChatGLMLLM

LLM:
  ChatGLMLLM:
    type: openai
    model_name: glm-4-flash  # 或 glm-4, glm-4-plus
    url: https://open.bigmodel.cn/api/paas/v4/
    api_key: your-zhipu-api-key
```

### Coze (扣子)

```yaml
selected_module:
  LLM: CozeLLM

LLM:
  CozeLLM:
    type: coze
    bot_id: your-bot-id
    api_key: your-coze-api-key
    base_url: https://api.coze.cn
```

### 本地 Ollama

```yaml
selected_module:
  LLM: OllamaLLM

LLM:
  OllamaLLM:
    type: ollama
    model_name: qwen2.5:7b  # 或其他模型
    url: http://localhost:11434
```

## TTS配置示例

### Edge TTS（免费，推荐）

```yaml
selected_module:
  TTS: EdgeTTS

TTS:
  EdgeTTS:
    type: edge
    voice: zh-CN-XiaoxiaoNeural  # 中文女声
    # 其他可选音色:
    # zh-CN-YunxiNeural       # 中文男声
    # zh-CN-XiaoyiNeural      # 中文女声（活泼）
    # zh-CN-YunyangNeural     # 中文男声（新闻播报）
    output_dir: tmp/
```

### 阿里云 TTS

```yaml
selected_module:
  TTS: AliyunTTS

TTS:
  AliyunTTS:
    type: aliyun
    appkey: your-appkey
    access_key_id: your-access-key-id
    access_key_secret: your-access-key-secret
    voice: xiaoyun  # 或其他音色
    format: wav
    sample_rate: 16000
```

### 豆包 TTS (火山引擎)

```yaml
selected_module:
  TTS: DoubaoTTS

TTS:
  DoubaoTTS:
    type: doubao
    api_key: your-doubao-api-key
    app_id: your-app-id
    voice_type: zh_female_qingxin  # 清新女声
```

### GPT-SoVITS (本地高质量TTS)

```yaml
selected_module:
  TTS: GPTSoVITSV3

TTS:
  GPTSoVITSV3:
    type: gpt_sovits_v3
    url: http://localhost:9880
    refer_wav_path: path/to/reference.wav
    prompt_text: "参考音频的文本"
    prompt_language: zh
```

## 弹幕采集模式

### 模式 1: 模拟模式（开发测试）

```yaml
danmaku:
  use_mock: true
  use_proxy: false

  # 模拟弹幕会自动生成测试消息
```

### 模式 2: 代理模式（推荐）

使用 DouyinBarrageGrab 获取真实弹幕：

```yaml
danmaku:
  room_id: your_room_id  # 可选

  use_mock: false
  use_proxy: true
  proxy_ws_url: "ws://127.0.0.1:8888"

  ws_host: 0.0.0.0
  ws_port: 8001
```

### 模式 3: 直连模式（需自行实现）

```yaml
danmaku:
  room_id: your_douyin_room_id

  use_mock: false
  use_proxy: false

  # 需要在 douyin_collector.py 中实现真实的抖音协议
```

## 流量控制配置

### 跳过模式（推荐，最流畅）

正在播放时直接丢弃新弹幕：

```yaml
danmaku:
  flow_control_enabled: true
  flow_control_strategy: skip
```

### 队列限制模式

限制待处理队列大小：

```yaml
danmaku:
  flow_control_enabled: true
  flow_control_strategy: queue_limit
  max_queue_size: 1  # 队列最多保留1条
```

### 关闭流量控制（不推荐）

处理所有弹幕，可能导致堆积：

```yaml
danmaku:
  flow_control_enabled: false
```

## 日志配置

### 开发调试（详细日志）

```yaml
log:
  log_level: DEBUG
  log_dir: tmp
  log_file: "danmaku_server_debug.log"
```

### 生产环境（简洁日志）

```yaml
log:
  log_level: INFO  # 或 WARNING
  log_dir: logs
  log_file: "danmaku_server.log"
```

## 角色提示词配置

### 直播间助手

```yaml
prompt: |
  你是一个直播间的AI助手，名叫小智。
  [核心特征]
  - 回复简洁明快，每次回复控制在50字以内
  - 语气活泼友好，适合直播间氛围
  - 对观众的问题给予及时回应
```

### 知识问答机器人

```yaml
prompt: |
  你是一个知识问答助手。
  [核心特征]
  - 准确回答观众的问题
  - 回答简明扼要，控制在100字以内
  - 如果不确定，诚实说明
  - 语气专业但友好
```

### 游戏主播助手

```yaml
prompt: |
  你是一个游戏直播间的AI助手，名叫小智。
  [核心特征]
  - 熟悉各类游戏
  - 能够解答游戏相关问题
  - 语气活泼，善用游戏术语
  - 回复控制在50字以内
```

## 完整配置示例

### 示例 1: 云端方案（免费）

适合：开发测试、个人使用

```yaml
# 弹幕配置
danmaku:
  room_id: test_room
  use_mock: true
  use_proxy: false
  flow_control_enabled: true
  flow_control_strategy: skip
  ws_host: 0.0.0.0
  ws_port: 8001

# 日志配置
log:
  log_level: INFO
  log_dir: tmp
  log_file: "danmaku_server.log"

# AI配置
selected_module:
  LLM: ChatGLMLLM
  TTS: EdgeTTS

prompt: |
  你是一个直播间的AI助手，名叫小智。
  回复要简洁明快，每次回复控制在50字以内。

# LLM
LLM:
  ChatGLMLLM:
    type: openai
    model_name: glm-4-flash
    url: https://open.bigmodel.cn/api/paas/v4/
    api_key: your_api_key_here

# TTS
TTS:
  EdgeTTS:
    type: edge
    voice: zh-CN-XiaoxiaoNeural
    output_dir: tmp/
```

### 示例 2: 生产环境（真实弹幕）

适合：真实直播场景

```yaml
# 弹幕配置
danmaku:
  room_id: your_douyin_room_id
  use_mock: false
  use_proxy: true
  proxy_ws_url: "ws://127.0.0.1:8888"
  flow_control_enabled: true
  flow_control_strategy: skip
  ws_host: 0.0.0.0
  ws_port: 8001

# 日志配置
log:
  log_level: INFO
  log_dir: logs
  log_file: "danmaku_server.log"

# AI配置
selected_module:
  LLM: OpenAILLM
  TTS: AliyunTTS

prompt: |
  你是一个专业的直播间AI助手。
  回复要准确、及时、友好。

# LLM
LLM:
  OpenAILLM:
    type: openai
    model_name: gpt-4o-mini
    url: https://api.openai.com/v1/
    api_key: sk-your-api-key

# TTS
TTS:
  AliyunTTS:
    type: aliyun
    appkey: your-appkey
    access_key_id: your-access-key-id
    access_key_secret: your-access-key-secret
    voice: xiaoyun
```

### 示例 3: 本地部署（完全离线）

适合：隐私要求高、网络受限场景

```yaml
# 弹幕配置
danmaku:
  use_mock: true  # 或配置代理模式
  flow_control_enabled: true
  flow_control_strategy: skip

# AI配置
selected_module:
  LLM: OllamaLLM
  TTS: GPTSoVITSV3

# 本地LLM
LLM:
  OllamaLLM:
    type: ollama
    model_name: qwen2.5:7b
    url: http://localhost:11434

# 本地TTS
TTS:
  GPTSoVITSV3:
    type: gpt_sovits_v3
    url: http://localhost:9880
    refer_wav_path: reference/voice.wav
    prompt_text: "参考音频文本"
```

## 🔍 配置验证

启动服务后，检查日志确认配置是否正确：

```
✅ LLM初始化成功: ChatGLMLLM
✅ TTS初始化成功: EdgeTTS
✅ 弹幕采集器初始化: 模拟模式
✅ WebSocket服务器已启动: ws://0.0.0.0:8001/danmaku/
```

## 📝 注意事项

1. **API Key 安全**: 不要将包含真实 API Key 的配置文件提交到 Git
2. **端口冲突**: 确保配置的端口未被占用
3. **网络访问**: 云端服务需要稳定的网络连接
4. **资源消耗**: 本地模型需要足够的 CPU/GPU 资源

## 🆘 获取帮助

如果配置遇到问题：
- 查看 [快速入门指南](QUICKSTART.md)
- 参考完整的 [danmaku_config.yaml](xiaozhi-esp32-server/main/xiaozhi-server/danmaku_config.yaml)
- 提交 [GitHub Issue](https://github.com/your-repo/issues)
