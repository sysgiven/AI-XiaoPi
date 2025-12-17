# 硬件设备连接指南

本文档介绍如何将硬件设备（如 ESP32）连接到弹幕AI服务器，接收 AI 生成的语音回复。

## 📋 目录

- [连接流程](#连接流程)
- [OTA验证流程](#ota验证流程)
- [WebSocket 协议](#websocket-协议)
- [测试工具](#测试工具)
- [ESP32 示例代码](#esp32-示例代码)
- [Python 客户端示例](#python-客户端示例)
- [故障排查](#故障排查)

---

## 🔄 连接流程

```
┌─────────────────────────────────────────────────┐
│              完整数据流程                        │
└─────────────────────────────────────────────────┘

1. 弹幕输入
   观众在抖音直播间发送弹幕: "你好小智"
   ↓

2. 弹幕采集
   DouyinBarrageGrab 捕获弹幕
   ↓

3. 服务器处理
   xiaozhi-server:
   - 接收弹幕文本
   - 调用 LLM 生成回复: "你好！很高兴见到你！"
   - 调用 TTS 合成语音（Opus 格式）
   ↓

4. 音频广播
   服务器通过 WebSocket 广播音频到所有设备
   ↓

5. 设备接收
   硬件设备:
   - 接收音频数据（二进制）
   - 解码播放
```

---

## 🔐 OTA验证流程

**重要**: ESP32 硬件在连接 WebSocket 之前，需要先进行 OTA 验证以获取服务器配置。

### OTA 验证步骤

```
ESP32 启动
   ↓
1. 发送 HTTP POST 请求到 OTA 接口
   地址: http://服务器IP:8003/xiaozhi/ota/
   请求头:
     - device-id: 设备唯一ID（如MAC地址）
     - client-id: 客户端ID（可选）
   请求体:
     {
       "application": {
         "version": "1.0.0"
       },
       "device": {
         "model": "xiaozhi-esp32"
       }
     }
   ↓

2. 服务器返回配置信息
   响应体:
     {
       "server_time": {
         "timestamp": 1234567890123,
         "timezone_offset": 480
       },
       "firmware": {
         "version": "1.0.0",
         "url": ""
       },
       "websocket": {
         "url": "ws://192.168.1.100:8001/danmaku/?device-id=xxx",
         "token": ""
       }
     }
   ↓

3. ESP32 解析响应，获取 WebSocket 地址
   ↓

4. 连接到 WebSocket 服务器
   ws://192.168.1.100:8001/danmaku/?device-id=xxx
   ↓

5. 接收音频数据并播放
```

### OTA 接口说明

**接口地址**: `http://服务器IP:8003/xiaozhi/ota/`

**请求方法**: `POST`

**请求头**:
- `device-id`: 设备唯一标识符（**必需**）
- `client-id`: 客户端标识符（可选）
- `Content-Type`: `application/json`

**请求体示例**:
```json
{
  "application": {
    "version": "1.0.0"
  },
  "device": {
    "model": "xiaozhi-esp32"
  }
}
```

**响应示例**:
```json
{
  "server_time": {
    "timestamp": 1734345678000,
    "timezone_offset": 480
  },
  "firmware": {
    "version": "1.0.0",
    "url": ""
  },
  "websocket": {
    "url": "ws://192.168.1.100:8001/danmaku/?device-id=esp32_001",
    "token": ""
  }
}
```

**字段说明**:
- `server_time.timestamp`: 服务器当前时间（毫秒时间戳）
- `server_time.timezone_offset`: 时区偏移（分钟，东八区为480）
- `firmware.version`: 固件版本号
- `firmware.url`: 固件下载地址（空表示无需更新）
- `websocket.url`: WebSocket 连接地址（**重要**）
- `websocket.token`: 认证令牌（弹幕服务器暂不需要）

---

## 🌐 WebSocket 协议

### 连接地址

```
ws://服务器IP:8001/danmaku/?device-id=设备唯一ID
```

**参数说明：**
- `服务器IP`: 运行 danmaku_app.py 的服务器IP
  - 本地测试: `127.0.0.1`
  - 局域网: 如 `192.168.1.100`
- `device-id`: 设备唯一标识符
  - 必须提供
  - 建议使用硬件 MAC 地址或序列号

**示例：**
```
ws://127.0.0.1:8001/danmaku/?device-id=esp32_001
ws://192.168.1.100:8001/danmaku/?device-id=xiaozhi_device_001
```

### 消息格式

#### 1. 服务器 → 设备：欢迎消息

连接成功后，服务器会发送欢迎消息（JSON文本）：

```json
{
  "type": "welcome",
  "message": "已连接到弹幕AI服务器",
  "device_id": "esp32_001",
  "timestamp": 1234567890.123
}
```

#### 2. 服务器 → 设备：音频数据

AI 回复时，服务器会发送音频数据（二进制）：

```
[二进制数据]
格式: 原始 Opus 编码包（Raw Opus packets）
编码: Opus 音频编码
大小: 通常每包 80-120 字节
```

**音频格式详细信息：**
- **编码格式**: Opus（高效语音编解码器）
- **数据格式**: 原始 Opus 编码包（**无 Ogg 容器包装**）
- **采样率**: 16000 Hz
- **声道**: 单声道
- **帧时长**: 通常 20ms 或 60ms
- **比特率**: 可变（VBR）

**重要说明：**
- 服务器发送的是**原始 Opus 编码包**，不是完整的 .opus 文件
- 这些包**没有 Ogg 容器**包装，无法直接保存为 .opus 文件播放
- 硬件设备需要**直接解码这些 Opus 包**并播放
- 这与 xiaozhi-esp32 原有固件的音频格式**完全兼容**

---

## 🧪 测试工具

### 1. 模拟设备客户端

运行测试客户端验证连接和音频接收：

```bash
cd xiaozhi-esp32-server/main/xiaozhi-server
python test_device_client.py
```

**功能：**
- ✅ 连接到服务器
- ✅ 接收欢迎消息
- ✅ 接收并保存音频数据到 `received_audio/` 目录
- ✅ 自动重连

**输出示例：**
```
============================================================
弹幕AI服务器 - 硬件设备模拟客户端
============================================================

设备ID: test_device_001
服务器: ws://127.0.0.1:8001/danmaku/

正在连接到服务器: ws://127.0.0.1:8001/danmaku/?device-id=test_device_001
✅ 已连接到服务器
📩 收到欢迎消息:
   设备ID: test_device_001
   消息: 已连接到弹幕AI服务器
   时间戳: 1234567890.123

🎧 等待接收音频数据...
   (在抖音直播间发送弹幕即可触发 AI 回复)

🔊 收到音频数据 #1:
   大小: 15234 字节 (14.88 KB)
   已保存: received_audio/audio_20250116_153045_1.opus
```

### 2. 完整流程测试

测试从弹幕到音频的完整流程：

```bash
python test_full_flow.py
```

**测试内容：**
1. ✅ 检查 DouyinBarrageGrab 连接
2. ✅ 检查弹幕服务器连接
3. ✅ 监控 30 秒，统计弹幕和音频接收情况

---

## 🔧 ESP32 示例代码

以下是 ESP32 (Arduino) 连接示例：

### 完整连接示例（含OTA验证）

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <WebSocketsClient.h>

// WiFi 配置
const char* ssid = "你的WiFi名称";
const char* password = "你的WiFi密码";

// 服务器配置
const char* serverIP = "192.168.1.100";  // 服务器IP
const char* deviceId = "esp32_001";      // 设备ID（建议使用MAC地址）

// WebSocket 客户端
WebSocketsClient webSocket;
String websocketUrl = "";

void setup() {
  Serial.begin(115200);

  // 连接 WiFi
  Serial.println("连接 WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi 已连接");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  // 步骤1: OTA 验证，获取 WebSocket 地址
  if (performOTACheck()) {
    Serial.println("✅ OTA 验证成功");

    // 步骤2: 连接 WebSocket
    connectWebSocket();
  } else {
    Serial.println("❌ OTA 验证失败，无法连接");
  }
}

void loop() {
  webSocket.loop();
}

/**
 * 执行 OTA 验证，获取 WebSocket 配置
 */
bool performOTACheck() {
  Serial.println("发送 OTA 验证请求...");

  HTTPClient http;
  String otaUrl = "http://" + String(serverIP) + ":8003/xiaozhi/ota/";

  http.begin(otaUrl);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("device-id", deviceId);
  http.addHeader("client-id", WiFi.macAddress());  // 使用MAC地址作为client-id

  // 构建请求体
  StaticJsonDocument<256> requestDoc;
  requestDoc["application"]["version"] = "1.0.0";
  requestDoc["device"]["model"] = "xiaozhi-esp32";

  String requestBody;
  serializeJson(requestDoc, requestBody);

  Serial.println("请求体: " + requestBody);

  // 发送 POST 请求
  int httpCode = http.POST(requestBody);

  if (httpCode == HTTP_CODE_OK) {
    String response = http.getString();
    Serial.println("OTA 响应: " + response);

    // 解析响应
    StaticJsonDocument<512> responseDoc;
    DeserializationError error = deserializeJson(responseDoc, response);

    if (error) {
      Serial.print("❌ JSON 解析失败: ");
      Serial.println(error.c_str());
      http.end();
      return false;
    }

    // 提取 WebSocket 地址
    const char* wsUrl = responseDoc["websocket"]["url"];
    if (wsUrl) {
      websocketUrl = String(wsUrl);
      Serial.println("WebSocket 地址: " + websocketUrl);
      http.end();
      return true;
    } else {
      Serial.println("❌ 响应中没有 websocket 地址");
      http.end();
      return false;
    }
  } else {
    Serial.print("❌ HTTP 请求失败，错误码: ");
    Serial.println(httpCode);
    http.end();
    return false;
  }
}

/**
 * 连接到 WebSocket 服务器
 */
void connectWebSocket() {
  if (websocketUrl.length() == 0) {
    Serial.println("❌ WebSocket 地址为空");
    return;
  }

  // 解析 URL: ws://192.168.1.100:8001/danmaku/?device-id=esp32_001
  // 提取 host, port, path

  Serial.println("连接到 WebSocket: " + websocketUrl);

  // 简化版：直接使用固定端口和路径
  String path = "/danmaku/?device-id=" + String(deviceId);
  webSocket.begin(serverIP, 8001, path);
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);

  Serial.println("WebSocket 连接已初始化");
}

/**
 * WebSocket 事件处理
 */
void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
  switch(type) {
    case WStype_DISCONNECTED:
      Serial.println("❌ WebSocket 已断开");
      break;

    case WStype_CONNECTED:
      Serial.println("✅ WebSocket 已连接");
      break;

    case WStype_TEXT:
      // 文本消息（欢迎消息）
      Serial.print("📩 收到文本: ");
      Serial.println((char*)payload);
      break;

    case WStype_BIN:
      // 二进制消息（音频数据）
      Serial.print("🔊 收到音频: ");
      Serial.print(length);
      Serial.println(" 字节");

      // 处理音频数据
      handleAudioData(payload, length);
      break;
  }
}

/**
 * 处理音频数据
 */
void handleAudioData(uint8_t* data, size_t length) {
  // TODO: 解码 Opus 音频并播放
  // 需要使用 Opus 解码库

  // 示例：发送到 I2S 音频输出
  // size_t bytes_written;
  // i2s_write(I2S_NUM_0, data, length, &bytes_written, portMAX_DELAY);
}
```

### 简化示例（直接连接，跳过OTA）

如果您已经知道 WebSocket 地址，可以跳过 OTA 验证直接连接：

```cpp
#include <WiFi.h>
#include <WebSocketsClient.h>

// WiFi 配置
const char* ssid = "你的WiFi名称";
const char* password = "你的WiFi密码";

// 服务器配置
const char* serverIP = "192.168.1.100";  // 服务器IP
const uint16_t serverPort = 8001;        // 服务器端口
const char* deviceId = "esp32_001";      // 设备ID

// WebSocket 客户端
WebSocketsClient webSocket;

void setup() {
  Serial.begin(115200);

  // 连接 WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi 已连接");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  // 连接 WebSocket
  String url = "/danmaku/?device-id=" + String(deviceId);
  webSocket.begin(serverIP, serverPort, url);
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);
}

void loop() {
  webSocket.loop();
}

void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
  switch(type) {
    case WStype_DISCONNECTED:
      Serial.println("❌ WebSocket 已断开");
      break;

    case WStype_CONNECTED:
      Serial.println("✅ WebSocket 已连接");
      break;

    case WStype_TEXT:
      // 文本消息（欢迎消息）
      Serial.print("📩 收到文本: ");
      Serial.println((char*)payload);
      break;

    case WStype_BIN:
      // 二进制消息（音频数据）
      Serial.print("🔊 收到音频: ");
      Serial.print(length);
      Serial.println(" 字节");

      // 处理音频数据
      handleAudioData(payload, length);
      break;
  }
}

void handleAudioData(uint8_t* data, size_t length) {
  // TODO: 解码 Opus 音频并播放
  // 需要使用 Opus 解码库

  // 示例：保存到 SD 卡
  // File audioFile = SD.open("/audio.opus", FILE_WRITE);
  // audioFile.write(data, length);
  // audioFile.close();

  // 示例：发送到 I2S 音频输出
  // i2s_write(I2S_NUM_0, data, length, &bytes_written, portMAX_DELAY);
}
```

### 完整示例（带音频播放）

```cpp
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <driver/i2s.h>
#include <opus.h>  // 需要 Opus 解码库

// I2S 配置
#define I2S_BCLK 26
#define I2S_LRC  25
#define I2S_DOUT 22

WebSocketsClient webSocket;
OpusDecoder* opusDecoder;

void setupAudio() {
  // 初始化 I2S
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = 24000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 1024,
    .use_apll = false,
    .tx_desc_auto_clear = true
  };

  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);

  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_BCLK,
    .ws_io_num = I2S_LRC,
    .data_out_num = I2S_DOUT,
    .data_in_num = I2S_PIN_NO_CHANGE
  };

  i2s_set_pin(I2S_NUM_0, &pin_config);

  // 初始化 Opus 解码器
  int error;
  opusDecoder = opus_decoder_create(24000, 1, &error);
  if (error != OPUS_OK) {
    Serial.println("❌ Opus 解码器初始化失败");
  }
}

void handleAudioData(uint8_t* data, size_t length) {
  // 解码 Opus 数据
  int16_t pcmData[4096];
  int frameSize = opus_decode(opusDecoder, data, length, pcmData, 4096, 0);

  if (frameSize > 0) {
    // 播放 PCM 数据
    size_t bytes_written;
    i2s_write(I2S_NUM_0, pcmData, frameSize * 2, &bytes_written, portMAX_DELAY);
    Serial.printf("🔊 播放音频: %d 帧\n", frameSize);
  } else {
    Serial.println("❌ Opus 解码失败");
  }
}
```

---

## 🐍 Python 客户端示例

### 基础示例

```python
import asyncio
import websockets

async def connect_to_server():
    uri = "ws://127.0.0.1:8001/danmaku/?device-id=python_client_001"

    async with websockets.connect(uri) as websocket:
        print("✅ 已连接到服务器")

        async for message in websocket:
            if isinstance(message, str):
                # 文本消息
                print(f"📩 收到文本: {message}")
            elif isinstance(message, bytes):
                # 音频数据
                print(f"🔊 收到音频: {len(message)} 字节")

                # 保存音频
                with open("audio.opus", "wb") as f:
                    f.write(message)

asyncio.run(connect_to_server())
```

### 带音频播放示例

```python
import asyncio
import websockets
import subprocess
import tempfile
import os

async def connect_and_play():
    uri = "ws://127.0.0.1:8001/danmaku/?device-id=python_client_002"

    async with websockets.connect(uri) as websocket:
        print("✅ 已连接到服务器")

        # 用于收集同一句话的所有 Opus 包
        audio_buffer = []

        async for message in websocket:
            if isinstance(message, bytes):
                # 收集 Opus 包
                audio_buffer.append(message)

            elif isinstance(message, str):
                # 可能是 TTS 状态消息
                import json
                try:
                    data = json.loads(message)
                    if data.get('type') == 'tts' and data.get('state') == 'stop':
                        # TTS 结束，播放收集到的音频
                        if audio_buffer:
                            print(f"🔊 收到完整音频: {len(audio_buffer)} 个包")

                            # 合并所有 Opus 包
                            merged_audio = b''.join(audio_buffer)

                            # 保存为原始 Opus 文件
                            with tempfile.NamedTemporaryFile(suffix='.opus.raw', delete=False) as f:
                                f.write(merged_audio)
                                temp_file = f.name

                            # 使用 ffmpeg 转换并播放
                            # 注意：原始 Opus 需要指定参数
                            subprocess.run([
                                'ffmpeg', '-f', 's16le',  # 输入格式
                                '-ar', '16000',  # 采样率
                                '-ac', '1',  # 声道数
                                '-i', temp_file,
                                '-f', 'mp3',  # 输出格式
                                'temp.mp3'
                            ])

                            # 播放
                            subprocess.run(['ffplay', '-nodisp', '-autoexit', 'temp.mp3'])

                            # 清理
                            os.remove(temp_file)
                            os.remove('temp.mp3')
                            audio_buffer = []

                except json.JSONDecodeError:
                    pass

asyncio.run(connect_and_play())
```

**说明：**
- 原始 Opus 包需要使用专门的解码器
- 测试时可以使用 ffmpeg 转换成其他格式播放
- 实际硬件设备应该使用 Opus 解码库直接解码

---

## 🔍 故障排查

### 问题 1: 无法连接到服务器

**症状：** 连接被拒绝

**解决方法：**
1. ✅ 确认 danmaku_app.py 正在运行
2. ✅ 检查服务器 IP 和端口是否正确
3. ✅ 检查防火墙设置：
   ```bash
   # Windows
   netsh advfirewall firewall add rule name="Danmaku Server" dir=in action=allow protocol=TCP localport=8001

   # Linux
   sudo ufw allow 8001/tcp
   ```
4. ✅ 测试端口是否开放：
   ```bash
   telnet 服务器IP 8001
   ```

### 问题 2: 连接成功但收不到音频

**症状：** 收到欢迎消息，但没有音频数据

**解决方法：**
1. ✅ 确认 DouyinBarrageGrab 正在运行并有弹幕流
2. ✅ 在直播间发送弹幕触发 AI 回复
3. ✅ 检查服务器日志：
   ```bash
   tail -f tmp/danmaku_server.log
   ```
4. ✅ 确认 LLM 和 TTS 配置正确
5. ✅ 运行测试脚本：
   ```bash
   python test_full_flow.py
   ```

### 问题 3: 音频无法播放

**症状：** 接收到音频但播放失败

**可能原因：**
- Opus 格式不支持
- 解码器未正确初始化
- 音频输出设备未配置

**解决方法：**
1. ✅ 确认支持 Opus 格式
2. ✅ 使用 ffmpeg 转换格式：
   ```bash
   ffmpeg -i audio.opus audio.mp3
   ```
3. ✅ 检查音频内容：
   ```bash
   ffprobe audio.opus
   ```

### 问题 4: 连接频繁断开

**症状：** 设备连接不稳定

**解决方法：**
1. ✅ 启用 WebSocket 心跳（ping/pong）
2. ✅ 实现自动重连机制
3. ✅ 检查网络稳定性
4. ✅ 增加超时时间配置

---

## 📊 性能建议

### 网络要求

- **带宽**: 至少 100 Kbps（每个设备）
- **延迟**: < 200ms
- **协议**: WebSocket over TCP

### 设备要求

- **处理器**: ESP32 或更高
- **RAM**: 至少 512KB
- **存储**: 至少 4MB Flash
- **音频输出**: I2S / DAC

### 优化建议

1. **音频缓冲**: 使用缓冲队列避免播放卡顿
2. **错误恢复**: 实现音频丢包恢复机制
3. **资源管理**: 及时释放解码器资源
4. **并发限制**: 服务器端限制最大连接数

---

## 🔗 相关资源

### 库和工具

- **ESP32 WebSocket**: https://github.com/Links2004/arduinoWebSockets
- **Opus 编解码器**: https://opus-codec.org/
- **FFmpeg**: https://ffmpeg.org/

### 文档

- **WebSocket 协议**: https://datatracker.ietf.org/doc/html/rfc6455
- **Opus 格式**: https://opus-codec.org/docs/

---

## 📝 常见问题

**Q: 可以同时连接多个设备吗？**
A: 可以。服务器支持多设备并发连接，会将音频广播到所有连接的设备。

**Q: 音频是什么格式？**
A: 默认是 Opus 格式，可以在 TTS 配置中修改。

**Q: 如何修改音频质量？**
A: 在 danmaku_config.yaml 中配置 TTS 参数，如采样率、比特率等。

**Q: ESP32 内存不够怎么办？**
A: 使用流式解码，分块处理音频数据，避免一次性加载完整音频。

**Q: 可以用其他语言开发客户端吗？**
A: 可以。只要支持 WebSocket 协议即可，如 JavaScript、Java、C# 等。

---

**祝您开发顺利！** 🎉

如有问题，请查看日志文件或运行测试脚本诊断问题。
