# 小皮AI直播机器人开源服务器 (XiaoPi)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

> 一个基于 xiaozhi-esp32-server 开发的直播弹幕AI交互服务器，让你的AI硬件设备能够实时响应直播间弹幕。

## 📖 项目简介

小皮AI直播机器人开源服务器(XiaoPi)是一个将直播弹幕与AI硬件语音交互结合的解决方案。它能够：

- 📺 实时接收直播间弹幕消息
- 🤖 使用大语言模型(LLM)生成智能回复
- 🔊 将回复转换为语音(TTS)
- 📡 发送到ESP32等硬件设备进行播放
- 🎯 支持串行化处理，避免弹幕堆积

## ✨ 核心功能

- **多种弹幕采集模式**
  - 模拟模式：用于开发测试
  - 代理模式：通过 DouyinBarrageGrab 获取真实弹幕（推荐）
  - 直连模式：直接连接（需自行实现）

- **智能流量控制**
  - 串行化处理：一次只处理一条弹幕
  - 自动忽略中间弹幕：只响应最新的弹幕
  - 防止音频堆积和播放混乱

- **灵活的AI配置**
  - 支持多种LLM提供商（OpenAI, ChatGLM, Gemini等）
  - 支持多种TTS引擎（Edge TTS, 阿里云等）
  - 可自定义AI角色和回复风格

- **硬件设备支持**
  - WebSocket连接管理
  - 设备自动发现和心跳检测
  - OTA固件更新接口

## 🚀 快速开始

### 环境要求

- Python 3.8+
- (可选) 直播间
- (可选) ESP32硬件设备

### 安装步骤

1. **克隆项目**
```bash
git clone <your-repo-url>
cd XiaoPi
```

2. **安装依赖**
```bash
cd xiaozhi-esp32-server/main/xiaozhi-server
pip install -r requirements.txt
```

3. **配置服务**

编辑 `danmaku_config.yaml` 文件：

```yaml
danmaku:
  # 填写你的直播间ID（如果使用真实弹幕）
  room_id: your_room_id

  # 工作模式选择
  use_mock: false      # 是否使用模拟数据
  use_proxy: true      # 是否使用 DouyinBarrageGrab 代理
  proxy_ws_url: "ws://127.0.0.1:8888"

# 配置你的LLM（这里使用智谱GLM-4-Flash）
LLM:
  ChatGLMLLM:
    api_key: your_api_key_here

# 配置你的TTS（这里使用免费的Edge TTS）
TTS:
  EdgeTTS:
    voice: zh-CN-XiaoxiaoNeural
```

4. **启动服务**

**Linux/macOS:**
```bash
./start_danmaku.sh
```

**Windows:**
```bash
start_danmaku.bat
```

或直接运行：
```bash
python danmaku_app.py
```

### 使用 DouyinBarrageGrab（推荐）

如果要获取真实的弹幕，需要先启动 DouyinBarrageGrab：

1. 进入 DouyinBarrageGrab 目录
2. 运行弹幕抓取服务（默认端口 8888）
3. 在浏览器中打开直播间并连接

详细说明请参考 `DouyinBarrageGrab` 目录下的 README。

## 📁 项目结构

```
XiaoPi/
├── xiaozhi-esp32-server/
│   └── main/
│       └── xiaozhi-server/
│           ├── danmaku_app.py              # 启动入口
│           ├── danmaku_config.yaml         # 配置文件
│           ├── start_danmaku.sh/bat        # 启动脚本
│           └── danmaku_server/             # 核心模块
│               ├── __init__.py
│               ├── danmaku_service.py      # 主服务
│               ├── danmaku_handler.py      # 弹幕处理器
│               ├── device_manager.py       # 设备管理
│               ├── douyin_collector.py     # 弹幕采集
│               ├── douyin_proxy_collector.py  # 代理模式采集
│               └── danmaku_ota_handler.py  # OTA更新处理
├── DouyinBarrageGrab/                      # 弹幕抓取工具
└── docs/                                   # 文档
```

## 🔧 工作原理

```
┌─────────────┐
│ 直播间   │
└──────┬──────┘
       │ 弹幕消息
       ▼
┌─────────────────────┐
│ DouyinBarrageGrab   │ (可选代理)
└──────┬──────────────┘
       │ WebSocket
       ▼
┌─────────────────────┐
│ Danmaku Collector   │ 弹幕采集器
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Danmaku Handler     │ 弹幕处理器
│  - 串行化处理        │
│  - 流量控制          │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ LLM                 │ 生成回复
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ TTS                 │ 转换为语音
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Device Manager      │ 设备管理
└──────┬──────────────┘
       │ WebSocket
       ▼
┌─────────────────────┐
│ ESP32 硬件设备       │ 播放语音
└─────────────────────┘
```

## 📝 配置说明

### 弹幕流量控制

在弹幕密集的直播间，建议启用流量控制：

```yaml
danmaku:
  flow_control_enabled: true
  flow_control_strategy: skip  # 推荐：跳过模式
```

- `skip`: 正在播放时直接丢弃新弹幕（推荐，体验最流畅）
- `queue_limit`: 限制待处理队列大小

### AI角色配置

在 `danmaku_config.yaml` 中自定义AI角色：

```yaml
prompt: |
  你是一个直播间的AI助手，名叫小皮。
  回复简洁明快，每次回复控制在50字以内。
  语气活泼友好，适合直播间氛围。
```

### LLM提供商

支持多种LLM提供商，配置示例：

```yaml
selected_module:
  LLM: ChatGLMLLM  # 或 OpenAILLM, GeminiLLM 等

LLM:
  ChatGLMLLM:
    type: openai
    model_name: glm-4-flash  # 免费模型
    api_key: your_api_key
```

### TTS引擎

支持多种TTS引擎，配置示例：

```yaml
selected_module:
  TTS: EdgeTTS  # 或 AliyunTTS, DoubaoTTS 等

TTS:
  EdgeTTS:
    type: edge
    voice: zh-CN-XiaoxiaoNeural  # 中文女声
```

## 🐛 故障排除

### 音频不播放

如果硬件设备不播放音频：
1. 检查设备是否正确连接（WebSocket日志）
2. 查看 Rate Controller 是否启动
3. 确认 `sentence_id` 正确设置（详见 `SENTENCE_ID_FIX.md`）

### 弹幕处理延迟

如果弹幕处理延迟或堆积：
1. 启用流量控制：`flow_control_enabled: true`
2. 使用跳过模式：`flow_control_strategy: skip`
3. 检查 LLM/TTS 响应时间

### DouyinBarrageGrab 连接失败

1. 确认 DouyinBarrageGrab 已启动
2. 检查 WebSocket 地址配置
3. 查看防火墙设置

## 📚 文档

- [架构说明](xiaozhi-esp32-server/main/xiaozhi-server/ARCHITECTURE.md) - 了解项目架构
- [弹幕接入指南](xiaozhi-esp32-server/main/xiaozhi-server/DOUYIN_BARRAGE_SETUP.md) - 配置弹幕
- [串行化处理方案](SERIALIZED_PROCESSING.md) - 了解弹幕处理机制
- [Sentence ID 修复说明](SENTENCE_ID_FIX.md) - 音频播放问题修复

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

在提交 PR 前，请确保：
- 代码符合项目风格
- 添加必要的注释
- 更新相关文档

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

## 🙏 致谢

- [xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) - ESP32硬件端开源项目
- [xiaozhi-esp32-server](https://github.com/xinnan-tech/xiaozhi-esp32-server) - 后端服务基础框架
- [DouyinBarrageGrab](https://github.com/IsoaSFlus/DouyinBarrageGrab) - 弹幕抓取
- 所有贡献者和用户

## 📮 联系方式

如有问题或建议，欢迎通过以下方式联系：
- 微信 px11360
- 提交 GitHub Issue
- 发送邮件至：[sysgiven@gmail.com]
- 加入讨论群：添加微信后拉群
---

⭐ 如果这个项目对你有帮助，欢迎给个 Star！
