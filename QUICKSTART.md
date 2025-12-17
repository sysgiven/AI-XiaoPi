# 快速入门指南 (Quick Start)

本指南将帮助你在 10 分钟内完成小皮AI直播服务器(XiaoPi)的部署和运行。

## 📋 前置准备

### 必需
- Python 3.8 或更高版本
- pip 包管理器
- 网络连接（用于安装依赖和调用云端API）

### 可选
- 抖音直播间（如果需要真实弹幕）
- ESP32硬件设备（如果需要物理输出）
- DouyinBarrageGrab 工具（如果使用代理模式）

## 🚀 5分钟快速启动（模拟模式）

如果你只是想快速体验项目，可以使用模拟模式：

### 1. 克隆项目
```bash
git clone <your-repo-url>
cd MyProject/xiaozhi-esp32-server/main/xiaozhi-server
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

编辑 `danmaku_config.yaml`，填入你的 API Key：

```yaml
LLM:
  ChatGLMLLM:
    api_key: your_api_key_here  # 在这里填入你的智谱AI密钥
```

> 💡 **获取免费API Key**: 访问 [智谱AI开放平台](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) 注册并获取免费的 glm-4-flash API Key

### 4. 启动服务

**Linux/macOS:**
```bash
./start_danmaku.sh
```

**Windows:**
```bash
python danmaku_app.py
```

### 5. 测试

服务启动后，你会看到类似输出：
```
==============================
抖音直播弹幕AI服务器
基于 xiaozhi-esp32-server 二次开发
==============================
WebSocket地址: ws://0.0.0.0:8001/danmaku/
使用模拟弹幕采集器
弹幕服务启动成功
```

在模拟模式下，服务器会自动生成测试弹幕，并进行处理。查看日志观察处理流程。

## 🎯 真实环境部署（代理模式）

如果你想接入真实的抖音直播弹幕，推荐使用代理模式：

### 步骤 1: 准备 DouyinBarrageGrab

1. 进入 DouyinBarrageGrab 目录
```bash
cd ../../../DouyinBarrageGrab
```

2. 启动弹幕抓取服务（具体步骤参考该目录的 README）

3. 确认服务运行在 `ws://127.0.0.1:8888`

### 步骤 2: 配置弹幕服务器

编辑 `danmaku_config.yaml`：

```yaml
danmaku:
  room_id: your_douyin_room_id  # 可选，抖音直播间ID

  # 关闭模拟模式
  use_mock: false

  # 启用代理模式
  use_proxy: true
  proxy_ws_url: "ws://127.0.0.1:8888"
```

### 步骤 3: 配置 LLM 和 TTS

#### 使用免费的 ChatGLM + Edge TTS（推荐新手）

```yaml
selected_module:
  LLM: ChatGLMLLM
  TTS: EdgeTTS

LLM:
  ChatGLMLLM:
    type: openai
    model_name: glm-4-flash
    api_key: your_glm_api_key  # 免费额度

TTS:
  EdgeTTS:
    type: edge
    voice: zh-CN-XiaoxiaoNeural  # 中文女声
```

#### 使用其他LLM（OpenAI, Gemini等）

```yaml
selected_module:
  LLM: OpenAILLM  # 或 GeminiLLM

LLM:
  OpenAILLM:
    type: openai
    model_name: gpt-4o-mini
    api_key: sk-your-openai-key
    url: https://api.openai.com/v1/
```

### 步骤 4: 启动服务

```bash
cd xiaozhi-esp32-server/main/xiaozhi-server
python danmaku_app.py
```

### 步骤 5: 打开抖音直播间

1. 在浏览器中打开你的抖音直播间
2. 在 DouyinBarrageGrab 界面中连接到该直播间
3. 发送测试弹幕，观察服务器日志

你应该能看到类似输出：
```
▶️  处理弹幕: 用户名: 你好
✅ LLM回复: 你好！我是小智，很高兴见到你！
🎬 Rate Controller后台任务已启动
🔊 音频包 #1: 1024 字节 → 1 个设备
```

## 🔌 连接硬件设备

如果你有 ESP32 硬件设备：

### 1. 配置设备

确保设备固件支持 WebSocket 连接，并配置连接地址：
```
ws://your-server-ip:8001/danmaku/?device-id=your-device-id
```

### 2. 测试连接

设备连接成功后，你会在日志中看到：
```
✅ 设备已连接: your-device-id (192.168.1.100)
✅ 已发送 hello 响应给设备: your-device-id
```

### 3. 测试音频播放

发送一条弹幕，观察：
- 服务器日志显示音频包发送
- 硬件设备播放语音

## ⚙️ 常用配置

### 调整 AI 角色

编辑 `danmaku_config.yaml` 中的 `prompt` 字段：

```yaml
prompt: |
  你是一个直播间的AI助手，名叫小智。
  [在这里自定义你的角色设定]
  - 回复要简短（50字以内）
  - 语气要活泼友好
```

### 调整流量控制

```yaml
danmaku:
  # 启用流量控制（推荐）
  flow_control_enabled: true

  # 策略选择
  flow_control_strategy: skip  # skip: 跳过模式（推荐）
                                # queue_limit: 队列限制模式

  # 队列大小（仅 queue_limit 模式）
  max_queue_size: 1
```

### 调整日志级别

```yaml
log:
  log_level: INFO  # DEBUG, INFO, WARNING, ERROR
```

## 🐛 常见问题

### 问题 1: 模块导入错误

**现象**: `ModuleNotFoundError: No module named 'xxx'`

**解决**:
```bash
pip install -r requirements.txt
```

### 问题 2: API Key 无效

**现象**: `Authentication failed` 或 `Invalid API key`

**解决**:
1. 检查 API Key 是否正确复制
2. 确认 API Key 有剩余额度
3. 检查网络连接

### 问题 3: 连接 DouyinBarrageGrab 失败

**现象**: `Failed to connect to proxy`

**解决**:
1. 确认 DouyinBarrageGrab 已启动
2. 检查端口配置（默认 8888）
3. 检查防火墙设置

### 问题 4: 音频不播放

**现象**: 日志显示处理成功但设备无声音

**解决**:
1. 检查设备是否正确连接
2. 查看日志中是否有 "🔊 音频包" 输出
3. 确认设备音量设置
4. 参考 `SENTENCE_ID_FIX.md` 文档

## 📚 下一步

- 📖 阅读 [README.md](README.md) 了解完整功能
- 🔧 查看 [配置说明](xiaozhi-esp32-server/main/xiaozhi-server/danmaku_config.yaml) 自定义配置
- 🏗️ 阅读 [架构文档](xiaozhi-esp32-server/main/xiaozhi-server/ARCHITECTURE.md) 了解工作原理
- 🤝 查看 [贡献指南](CONTRIBUTING.md) 参与项目开发

## 💬 获取帮助

如果你遇到问题：

1. 查看 [FAQ](#常见问题) 部分
2. 搜索 [GitHub Issues](https://github.com/your-repo/issues)
3. 提交新的 Issue 描述你的问题
4. 加入讨论群（如果有的话）

---

祝你使用愉快！ 🎉
