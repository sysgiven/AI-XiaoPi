# ESP32 音频播放故障排查指南

## 错误："Requested device not found"

这个错误表示ESP32无法初始化I2S音频输出设备。

---

## 🔍 原因分析

### 1. I2S配置错误

**可能原因**：
- I2S引脚配置与硬件不匹配
- I2S参数配置错误（采样率、位深度等）
- I2S驱动未正确安装

**检查方法**：
```cpp
// 检查I2S配置
i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = 16000,  // 必须与服务器匹配
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,  // 单声道
    .communication_format = I2S_COMM_FORMAT_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 1024,
    .use_apll = false,
    .tx_desc_auto_clear = true
};
```

### 2. 硬件连接问题

**常见问题**：
- 音频芯片（如MAX98357A）未正确连接
- I2S引脚接线错误
- 电源供应不足

**检查清单**：
- ✅ 音频芯片VCC连接到3.3V或5V（根据芯片规格）
- ✅ GND连接正确
- ✅ I2S引脚连接：
  - BCLK (Bit Clock)
  - LRC/WS (Word Select / Left-Right Clock)
  - DIN/DOUT (Data In/Out)

**xiaozhi-esp32 标准连接**：
```
ESP32           MAX98357A
GPIO26   -->    BCLK
GPIO25   -->    LRC
GPIO22   -->    DIN
3.3V     -->    VIN
GND      -->    GND
```

### 3. Opus解码器问题

**可能原因**：
- Opus解码器未初始化
- Opus库编译配置错误
- 内存不足无法创建解码器

**检查代码**：
```cpp
#include <opus.h>

OpusDecoder* opusDecoder;
int error;

// 初始化Opus解码器
// 采样率必须与服务器匹配（16000 Hz）
opusDecoder = opus_decoder_create(16000, 1, &error);

if (error != OPUS_OK) {
    Serial.printf("❌ Opus解码器初始化失败: %d\n", error);
    // 错误码：
    // OPUS_BAD_ARG (-1): 参数无效
    // OPUS_ALLOC_FAIL (-3): 内存分配失败
} else {
    Serial.println("✅ Opus解码器初始化成功");
}
```

---

## 🛠️ 解决方案

### 方案1：验证I2S配置

1. **检查引脚定义**：
```cpp
// 确认引脚定义与实际硬件匹配
#define I2S_BCLK 26
#define I2S_LRC  25
#define I2S_DOUT 22

i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_BCLK,
    .ws_io_num = I2S_LRC,
    .data_out_num = I2S_DOUT,
    .data_in_num = I2S_PIN_NO_CHANGE
};
```

2. **初始化I2S驱动**：
```cpp
esp_err_t err = i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
if (err != ESP_OK) {
    Serial.printf("❌ I2S驱动安装失败: %d\n", err);
    return false;
}

err = i2s_set_pin(I2S_NUM_0, &pin_config);
if (err != ESP_OK) {
    Serial.printf("❌ I2S引脚设置失败: %d\n", err);
    return false;
}

Serial.println("✅ I2S初始化成功");
```

### 方案2：简化音频播放测试

创建一个简单的测试程序，验证I2S是否工作：

```cpp
void testI2S() {
    Serial.println("测试I2S音频输出...");

    // 生成一个简单的正弦波
    int16_t samples[1024];
    for (int i = 0; i < 1024; i++) {
        samples[i] = (int16_t)(sin(2.0 * M_PI * i / 100.0) * 10000);
    }

    // 写入I2S
    size_t bytes_written;
    esp_err_t err = i2s_write(I2S_NUM_0, samples, sizeof(samples),
                              &bytes_written, portMAX_DELAY);

    if (err == ESP_OK && bytes_written == sizeof(samples)) {
        Serial.println("✅ I2S测试成功");
    } else {
        Serial.printf("❌ I2S测试失败: %d, 写入字节: %d/%d\n",
                     err, bytes_written, sizeof(samples));
    }
}
```

### 方案3：使用xiaozhi-esp32原固件

如果您使用的是自己编写的固件，建议先尝试xiaozhi-esp32官方固件：

1. **下载固件**：
```bash
git clone https://github.com/78/xiaozhi-esp32.git
```

2. **配置服务器地址**：
修改固件中的OTA服务器地址指向您的弹幕服务器

3. **烧录固件**：
使用Arduino IDE或PlatformIO烧录

### 方案4：检查内存

Opus解码器需要足够的内存（约20-40KB）：

```cpp
void checkMemory() {
    Serial.printf("空闲堆内存: %d bytes\n", ESP.getFreeHeap());
    Serial.printf("最大可分配块: %d bytes\n", ESP.getMaxAllocHeap());

    // Opus解码器大约需要20-40KB
    if (ESP.getFreeHeap() < 50000) {
        Serial.println("⚠️  内存不足，可能影响Opus解码器初始化");
    }
}
```

### 方案5：逐步调试

创建一个调试版本的音频处理函数：

```cpp
void handleAudioData(uint8_t* data, size_t length) {
    Serial.printf("🔊 收到音频数据: %d 字节\n", length);

    // 步骤1：检查数据
    if (data == NULL || length == 0) {
        Serial.println("❌ 音频数据为空");
        return;
    }
    Serial.printf("✅ 数据有效，前4字节: %02X %02X %02X %02X\n",
                 data[0], data[1], data[2], data[3]);

    // 步骤2：检查解码器
    if (opusDecoder == NULL) {
        Serial.println("❌ Opus解码器未初始化");
        return;
    }
    Serial.println("✅ Opus解码器已就绪");

    // 步骤3：解码
    int16_t pcmData[4096];
    int frameSize = opus_decode(opusDecoder, data, length, pcmData, 4096, 0);

    if (frameSize < 0) {
        Serial.printf("❌ Opus解码失败，错误码: %d\n", frameSize);
        // 错误码：
        // OPUS_BAD_ARG (-1): 参数无效
        // OPUS_INVALID_PACKET (-4): 无效的Opus包
        // OPUS_ALLOC_FAIL (-3): 内存分配失败
        return;
    }
    Serial.printf("✅ 解码成功，PCM帧数: %d\n", frameSize);

    // 步骤4：写入I2S
    size_t bytes_written;
    esp_err_t err = i2s_write(I2S_NUM_0, pcmData, frameSize * 2,
                              &bytes_written, portMAX_DELAY);

    if (err != ESP_OK) {
        Serial.printf("❌ I2S写入失败，错误码: %d\n", err);
        return;
    }

    if (bytes_written != frameSize * 2) {
        Serial.printf("⚠️  I2S写入不完整: %d/%d 字节\n",
                     bytes_written, frameSize * 2);
    } else {
        Serial.printf("✅ 音频播放成功: %d 帧\n", frameSize);
    }
}
```

---

## 📊 常见错误码参考

### Opus错误码
| 错误码 | 常量 | 含义 | 解决方法 |
|--------|------|------|----------|
| -1 | OPUS_BAD_ARG | 参数无效 | 检查采样率、声道数配置 |
| -3 | OPUS_ALLOC_FAIL | 内存分配失败 | 增加可用内存或减少其他内存占用 |
| -4 | OPUS_INVALID_PACKET | 无效的Opus包 | 检查服务器音频格式配置 |

### I2S错误码
| 错误码 | 常量 | 含义 | 解决方法 |
|--------|------|------|----------|
| 0x102 | ESP_ERR_INVALID_ARG | 参数无效 | 检查I2S配置参数 |
| 0x103 | ESP_ERR_INVALID_STATE | 状态无效 | 确保I2S已正确初始化 |
| 0x105 | ESP_ERR_NOT_FOUND | 设备未找到 | 检查硬件连接和引脚配置 |

---

## 🔬 最小可用示例

这是一个最简化的ESP32音频接收和播放示例：

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <WebSocketsClient.h>
#include <driver/i2s.h>
#include <opus.h>

// WiFi配置
const char* ssid = "你的WiFi";
const char* password = "你的密码";
const char* serverIP = "192.168.1.100";
const char* deviceId = "esp32_001";

// I2S引脚（根据实际硬件修改）
#define I2S_BCLK 26
#define I2S_LRC  25
#define I2S_DOUT 22

WebSocketsClient webSocket;
OpusDecoder* opusDecoder = NULL;

void setup() {
    Serial.begin(115200);

    // 1. 连接WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\n✅ WiFi已连接");

    // 2. 初始化I2S
    if (!initI2S()) {
        Serial.println("❌ I2S初始化失败，程序停止");
        while(1) delay(1000);
    }

    // 3. 初始化Opus解码器
    if (!initOpus()) {
        Serial.println("❌ Opus初始化失败，程序停止");
        while(1) delay(1000);
    }

    // 4. OTA验证
    if (!performOTA()) {
        Serial.println("❌ OTA验证失败，程序停止");
        while(1) delay(1000);
    }

    // 5. 连接WebSocket
    String path = "/danmaku/?device-id=" + String(deviceId);
    webSocket.begin(serverIP, 8001, path);
    webSocket.onEvent(webSocketEvent);
    webSocket.setReconnectInterval(5000);
}

void loop() {
    webSocket.loop();
}

bool initI2S() {
    Serial.println("初始化I2S...");

    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate = 16000,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = 1024,
        .use_apll = false,
        .tx_desc_auto_clear = true
    };

    esp_err_t err = i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
    if (err != ESP_OK) {
        Serial.printf("I2S驱动安装失败: %d\n", err);
        return false;
    }

    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_BCLK,
        .ws_io_num = I2S_LRC,
        .data_out_num = I2S_DOUT,
        .data_in_num = I2S_PIN_NO_CHANGE
    };

    err = i2s_set_pin(I2S_NUM_0, &pin_config);
    if (err != ESP_OK) {
        Serial.printf("I2S引脚设置失败: %d\n", err);
        return false;
    }

    Serial.println("✅ I2S初始化成功");
    return true;
}

bool initOpus() {
    Serial.println("初始化Opus解码器...");
    Serial.printf("可用内存: %d bytes\n", ESP.getFreeHeap());

    int error;
    opusDecoder = opus_decoder_create(16000, 1, &error);

    if (error != OPUS_OK || opusDecoder == NULL) {
        Serial.printf("Opus解码器创建失败: %d\n", error);
        return false;
    }

    Serial.println("✅ Opus解码器初始化成功");
    return true;
}

bool performOTA() {
    Serial.println("执行OTA验证...");

    HTTPClient http;
    String otaUrl = "http://" + String(serverIP) + ":8003/xiaozhi/ota/";

    http.begin(otaUrl);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("device-id", deviceId);
    http.addHeader("client-id", WiFi.macAddress());

    StaticJsonDocument<256> requestDoc;
    requestDoc["application"]["version"] = "1.0.0";
    requestDoc["device"]["model"] = "xiaozhi-esp32";

    String requestBody;
    serializeJson(requestDoc, requestBody);

    int httpCode = http.POST(requestBody);
    http.end();

    if (httpCode == 200) {
        Serial.println("✅ OTA验证成功");
        return true;
    } else {
        Serial.printf("OTA验证失败: %d\n", httpCode);
        return false;
    }
}

void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
    switch(type) {
        case WStype_CONNECTED:
            Serial.println("✅ WebSocket已连接");
            break;

        case WStype_DISCONNECTED:
            Serial.println("❌ WebSocket已断开");
            break;

        case WStype_TEXT:
            Serial.printf("📩 收到文本: %s\n", (char*)payload);
            break;

        case WStype_BIN:
            handleAudioData(payload, length);
            break;
    }
}

void handleAudioData(uint8_t* data, size_t length) {
    // 解码Opus
    int16_t pcmData[4096];
    int frameSize = opus_decode(opusDecoder, data, length, pcmData, 4096, 0);

    if (frameSize > 0) {
        // 播放
        size_t bytes_written;
        i2s_write(I2S_NUM_0, pcmData, frameSize * 2, &bytes_written, portMAX_DELAY);
        Serial.printf("🔊 播放: %d 帧\n", frameSize);
    } else {
        Serial.printf("❌ 解码失败: %d\n", frameSize);
    }
}
```

---

## 📝 检查清单

使用此检查清单逐步排查问题：

- [ ] **硬件连接**
  - [ ] 音频芯片供电正常（3.3V或5V）
  - [ ] GND连接正确
  - [ ] I2S三根信号线连接正确（BCLK, LRC, DIN）
  - [ ] 扬声器或耳机已连接

- [ ] **I2S配置**
  - [ ] 引脚号与硬件匹配
  - [ ] 采样率设置为16000 Hz
  - [ ] 声道设置为单声道
  - [ ] I2S驱动成功安装

- [ ] **Opus解码器**
  - [ ] Opus库已正确编译和链接
  - [ ] 解码器初始化成功
  - [ ] 有足够的可用内存（>50KB）

- [ ] **网络连接**
  - [ ] WiFi连接成功
  - [ ] OTA验证通过
  - [ ] WebSocket连接成功
  - [ ] 能收到音频数据

- [ ] **音频数据**
  - [ ] 服务器发送的是原始Opus格式
  - [ ] 数据包大小正常（80-120字节左右）
  - [ ] 数据包内容有效（不是空包）

---

## 💡 推荐调试流程

1. **第一步**：使用串口监视器查看启动日志，确认每个步骤的成功/失败状态
2. **第二步**：运行I2S测试程序（正弦波测试），验证硬件连接
3. **第三步**：单独测试Opus解码器（使用预录制的Opus文件）
4. **第四步**：连接到弹幕服务器，接收真实音频数据

---

如有问题，请提供：
1. ESP32启动日志（完整的串口输出）
2. 硬件型号和音频芯片型号
3. I2S引脚配置
4. 固件版本信息
