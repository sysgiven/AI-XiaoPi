# 🤖 AI-XiaoPi (小皮 AI 直播机器人)

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-yellow.svg)
![Docker](https://img.shields.io/badge/docker-supported-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20Mac-lightgrey)

**全球首个开源“硬件+软件”一体化 AI 直播机器人解决方案**

[快速开始](#-快速开始) | [硬件清单](#-硬件清单-bom) | [核心特性](#-核心特性) | [加入社区](#-联系与交流)

</div>

---

## 📖 项目介绍

**AI-XiaoPi** 是一个开源的 AI 直播助手项目，旨在为直播间提供智能化的语音互动能力。与市面上昂贵的 SaaS 服务不同，AI-XiaoPi 允许你**私有化部署**，拥有完全的数据控制权，并且**一次性硬件投入，无后续月租**。

它不仅仅是一个软件+硬件机器人，更是一套打通了 **ESP32 硬件终端**、**直播弹幕获取**、**大模型(LLM)** 和 **语音合成(TTS)** 的完整链路。

> **适用场景：** 24小时无人直播、智能客服答疑、游戏主播辅助、娱乐整活。

## ✨ 核心特性

我们采用模块化插件架构，支持市面上主流的 AI 服务，你可以像搭积木一样自由组合。

| 模块 | 功能描述 | 支持列表 (已实现) |
| :--- | :--- | :--- |
| 🧠 **LLM 大模型** | 智能大脑，处理弹幕并生成回复 | ✅ **OpenAI (GPT-3.5/4)**<br>✅ **ChatGLM (智谱 AI)**<br>✅ **DeepSeek (深度求索)**<br>✅ **Ollama (本地私有模型)**<br>✅ **FastGPT / Dify / Coze (知识库支持)**<br>✅ **Gemini / Xinference** |
| 🗣️ **TTS 语音** | 将文字回复转换为真人语音 | ✅ **Edge TTS (微软免费，强烈推荐)**<br>✅ **阿里云 TTS**<br>✅ **GPT-SoVITS (克隆音色)**<br>✅ **豆包 / 火山引擎**<br>✅ **讯飞星火** |
| 👂 **弹幕监听** | 实时获取直播间互动数据 | ✅ **抖音 (Douyin)** via DouyinBarrageGrab<br>🚧 **Bilibili** (开发中)<br>🚧 **快手/TikTok** (计划中) |
| 🤖 **硬件控制** | 软硬结合，实体机器人动作交互 | ✅ **ESP32 舵机控制**<br>✅ **LCD 表情显示**<br>✅ **WS2812 氛围灯效** |

## 🛠 硬件清单 (BOM)

如果你想体验“实体机器人”的乐趣，建议购买以下配件（成本约 ¥100-200）。
**注：没有硬件也可以使用“纯软件模式”运行！**

1.  **主控板：** ESP32-S3 开发板 (推荐 N16R8 版本)
2.  **音频模块：** MAX98357 I2S 功放模块
3.  **麦克风：** INMP441 全向麦克风
4.  **扬声器：** 4Ω 3W 小喇叭
5.  **外壳：** 3D 打印模型 (STL 文件位于 doc/3d_models 目录)

*(详细接线图请参考 docs/HARDWARE_SETUP.md)*

## 🚀 快速开始

### 方式一：Docker 一键部署 (推荐)

适合小白用户，无需配置复杂的 Python 环境。

1.  **克隆项目**
    `
    git clone https://github.com/sysgiven/AI-XiaoPi.git
    cd AI-XiaoPi/xiaozhi-esp32-server/main/xiaozhi-server
    `

2.  **修改配置**
    复制 config_example.yaml 为 config.yaml，填入你的 API Key。
    `
    cp config_example.yaml config.yaml
    # 编辑 config.yaml，填入你的 LLM 和 TTS 配置
    `

3.  **启动服务**
    `
    docker-compose up -d
    `

### 方式二：源码部署 (开发者)

1.  **环境准备**
    确保安装 Python 3.10+。
    `
    cd xiaozhi-esp32-server/main/xiaozhi-server
    pip install -r requirements.txt
    `

2.  **启动应用**
    `
    # Windows
    start_danmaku.bat
    
    # Linux/Mac
    sh start_danmaku.sh
    `

## ⚙️ 配置指南 (config.yaml)

目前支持通过简单的配置文件切换不同模型。

`yaml
# 示例：使用 DeepSeek + 免费 EdgeTTS

# 选择使用的模块
selected_module:
  LLM: OpenAI      # 使用 OpenAI 兼容协议连接 DeepSeek
  TTS: EdgeTTS     # 使用微软免费语音

# LLM 详细配置
LLM:
  OpenAI:
    base_url: "https://api.deepseek.com/v1"
    api_key: "sk-xxxxxxxxxxxx"
    model_name: "deepseek-chat"

# TTS 详细配置
TTS:
  EdgeTTS:
    voice: "zh-CN-XiaoxiaoNeural"  # 晓晓（甜美主要音色）
`
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


## 🔌 插件开发

想要接入新的大模型？本项目采用插件化架构，添加新功能非常简单！
只需在 core/providers/llm 下创建一个新文件，继承 BaseLLMProvider 类即可。

欢迎提交 PR 贡献你的插件！

## 🗓️ 路线图 (Roadmap)

- [x] 发布 v1.0 核心功能 (LLM+TTS+直播流)
- [x] 支持 Docker 部署
- [ ] **v1.1:** 增加 Web 管理后台 (可视化配置)
- [ ] **v1.2:** 支持 Bilibili 直播间
- [ ] **v1.3:** 增加“数字人”视频推流功能

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

## 🙏 致谢

- [xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) - ESP32硬件端开源项目
- [xiaozhi-esp32-server](https://github.com/xinnan-tech/xiaozhi-esp32-server) - 后端服务基础框架
- [DouyinBarrageGrab](https://github.com/IsoaSFlus/DouyinBarrageGrab) - 弹幕抓取
- 所有贡献者和用户

## 🤝 联系与交流

- **Issue:** 有 Bug 或建议请直接提 Issue。
- **微信:** px11360
- **Email:** sysgiven@gmail.com

---

**如果这个项目对你有帮助，请给一个 ⭐️ Star！你的支持是我们更新的动力！**

