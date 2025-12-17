# 快速开始指南

## 5分钟快速体验

### 步骤 1: 配置 API Key

编辑 `danmaku_config.yaml` 文件，配置你的LLM API密钥：

```yaml
LLM:
  ChatGLMLLM:
    api_key: "在这里填入你的智谱API密钥"
```

**如何获取智谱API密钥**：
1. 访问 https://bigmodel.cn
2. 注册/登录账号
3. 进入控制台 → API密钥
4. 创建新密钥并复制

**注意**：智谱的 glm-4-flash 模型是完全免费的！

### 步骤 2: 安装依赖

```bash
cd xiaozhi-esp32-server/main/xiaozhi-server
pip install -r requirements.txt
```

### 步骤 3: 启动服务

**Windows:**
```bash
start_danmaku.bat
```

**Linux/macOS:**
```bash
chmod +x start_danmaku.sh
./start_danmaku.sh
```

**或直接运行：**
```bash
python danmaku_app.py
```

### 步骤 4: 测试连接

在新终端运行测试客户端：

```bash
python test_client.py
```

你会看到：
1. ✓ 连接成功的提示
2. 📨 收到欢迎消息
3. 🔊 每隔一段时间收到音频数据（模拟弹幕触发的AI回复）

## 配置选项

### 使用模拟数据（默认）

```yaml
danmaku:
  use_mock: true
```

系统会自动生成模拟弹幕，适合开发测试。

### 使用真实抖音弹幕

```yaml
danmaku:
  use_mock: false
  room_id: "你的抖音直播间ID"
```

**注意**：真实模式需要额外开发抖音协议接入，请参考文档。

### 更换TTS引擎

**EdgeTTS (默认，免费)**
```yaml
selected_module:
  TTS: EdgeTTS

TTS:
  EdgeTTS:
    voice: zh-CN-XiaoxiaoNeural
```

**火山引擎 (更好的音质)**
```yaml
selected_module:
  TTS: DoubaoTTS

TTS:
  DoubaoTTS:
    appid: "你的appid"
    access_token: "你的token"
    voice: BV001_streaming
```

### 自定义AI角色

编辑 `danmaku_config.yaml` 中的 prompt：

```yaml
prompt: |
  你是一个幽默风趣的主播助手。
  每次回复不超过30字。
  语气活泼，适合直播间氛围。
```

## 常见问题

### Q: 启动报错 "ModuleNotFoundError"

```bash
pip install -r requirements.txt
```

### Q: LLM调用失败

检查：
1. API Key是否正确
2. 网络是否能访问LLM服务
3. 查看日志 `tmp/danmaku_server.log`

### Q: 没有收到音频

检查：
1. TTS配置是否正确
2. `tmp/` 目录是否有音频文件生成
3. 测试客户端是否正确连接

## 下一步

- 📖 阅读 [完整文档](./DANMAKU_README.md)
- 🏗️ 查看 [架构设计](./ARCHITECTURE.md)
- 🔧 自定义配置
- 🚀 接入真实直播间

## 技术支持

- 查看项目 Issues
- 参考原项目文档: https://github.com/xinnan-tech/xiaozhi-esp32-server
