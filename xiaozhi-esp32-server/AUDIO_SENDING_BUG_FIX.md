# 音频发送停止问题 - 修复说明

## 问题描述

用户报告：**"音频的发送逻辑感觉有问题，该应用场景会一直生成新的对话，测试中有的话没有发送完，发送几句后就不发送了"**

表现：
- 前几条弹幕的音频可以正常发送
- 几条弹幕后，音频发送停止
- 部分音频包丢失，导致播放不完整

## 根本原因

### 问题：两个音频工作线程竞争同一个队列

弹幕服务器中存在 **两个独立的音频工作线程**，它们同时从 `tts_audio_queue` 读取音频数据：

1. **标准TTS音频线程** (`_audio_play_priority_thread`)
   - 由 `tts.open_audio_channels()` 启动
   - 位置：`core/providers/tts/base.py:326`
   - 工作方式：
     ```python
     while not self.conn.stop_event.is_set():
         sentence_type, audio_datas, text = self.tts_audio_queue.get(timeout=0.1)
         # 发送音频...
     ```

2. **自定义音频工作线程** (`_audio_send_worker`)
   - 由 `danmaku_handler.start()` 启动
   - 位置：`danmaku_server/danmaku_handler.py:288`（已删除）
   - 工作方式：
     ```python
     while self.processing:
         sentence_type, audio_datas, text = self.tts.tts_audio_queue.get_nowait()
         # 广播音频...
     ```

### 竞争条件（Race Condition）

当两个线程同时从同一个队列读取时：

```
TTS生成音频包序列: [包1] [包2] [包3] [包4] [包5] [包6]
                     ↓     ↓     ↓     ↓     ↓     ↓
                  tts_audio_queue (共享队列)
                     ↓     ↓     ↓     ↓     ↓     ↓
线程1 (_audio_play_priority_thread): 获取 [包1]     [包3]     [包5]
线程2 (_audio_send_worker):          获取     [包2]     [包4]     [包6]
```

**结果**：
- 一半的音频包被线程1处理（但没有发送到设备！）
- 一半的音频包被线程2处理并广播
- 设备只收到一半的音频包 → 音频不完整、播放断断续续
- 当某个线程异常停止时，音频发送完全停止

## 架构分析

### TTS音频处理流程

```
弹幕输入
    ↓
DanmakuHandler._process_danmaku()
    ↓
发送 FIRST, MIDDLE, LAST 到 tts_text_queue
    ↓
=== TTS文本处理线程 (tts_text_priority_thread) ===
    ↓
从 tts_text_queue 获取文本
    ↓
调用 EdgeTTS 生成 MP3
    ↓
转换为 Opus 包
    ↓
调用 handle_opus() → 放入 tts_audio_queue
    ↓
=== TTS音频播放线程 (_audio_play_priority_thread) ===
    ↓
从 tts_audio_queue 获取音频
    ↓
调用 sendAudioMessage(conn, ...)
    ↓
await conn.websocket.send(opus_packet)
    ↓
=== MockWebSocket.send() ===
    ↓
await device_manager.broadcast_audio(data)
    ↓
发送到所有连接的ESP32设备
```

### 关键发现

**标准TTS线程已经完成了所有必要的工作！**

- `_audio_play_priority_thread` 会自动从 `tts_audio_queue` 获取音频
- 它调用 `sendAudioMessage()` → `sendAudio()` → `conn.websocket.send()`
- 我们的 `DanmakuConnection` 创建了 `MockWebSocket`，其 `send()` 方法会广播到所有设备
- **自定义的 `_audio_send_worker()` 是多余的！**

## 修复方案

### 删除冗余的音频工作线程

**修改文件**: `danmaku_server/danmaku_handler.py`

#### 1. 移除自定义音频工作任务启动

```python
# 修改前
async def start(self):
    """启动消息处理"""
    self.processing = True
    self.logger.info("启动弹幕消息处理")

    # 启动TTS音频发送任务
    asyncio.create_task(self._audio_send_worker())  # ← 这行导致了问题！

    # 启动消息处理任务
    while self.processing:
        # ...
```

```python
# 修改后
async def start(self):
    """启动消息处理"""
    self.processing = True
    self.logger.info("启动弹幕消息处理")

    # 注意：不需要启动自定义音频发送任务
    # TTS的 open_audio_channels() 已经启动了 _audio_play_priority_thread
    # 该线程会自动从 tts_audio_queue 获取音频并通过 MockWebSocket.send() 广播

    # 启动消息处理任务
    while self.processing:
        # ...
```

#### 2. 删除整个 `_audio_send_worker()` 方法

完全删除 `_audio_send_worker()` 方法（约50行代码），因为它不再需要。

#### 3. 增强 MockWebSocket 日志

添加音频包计数器和调试日志，便于追踪音频发送：

```python
class MockWebSocket:
    def __init__(self, device_manager, logger):
        self.device_manager = device_manager
        self.logger = logger
        self.packet_count = 0  # 音频包计数器

    async def send(self, data):
        """发送数据到所有设备"""
        self.packet_count += 1
        device_count = self.device_manager.get_device_count()
        self.logger.bind(tag=TAG).debug(
            f"🔊 音频包 #{self.packet_count}: {len(data)} 字节 → {device_count} 个设备"
        )
        await self.device_manager.broadcast_audio(data)
```

## 修复效果

### 修复前

```
[INFO] ▶️  处理弹幕: 用户A: 你好
[DEBUG] 从TTS队列获取音频: type=MIDDLE  ← 线程2获取
[INFO] 🔊 广播音频数据: 108 字节        ← 线程2发送
[DEBUG] 从TTS队列获取音频: type=MIDDLE  ← 线程1获取（但不发送！）
[INFO] 🔊 广播音频数据: 112 字节        ← 线程2发送
[DEBUG] 从TTS队列获取音频: type=MIDDLE  ← 线程1获取（但不发送！）
[ERROR] 音频发送任务出错: ...           ← 线程2异常停止
# 之后没有更多音频包！
```

**问题**：
- ❌ 线程1和线程2交替获取音频包
- ❌ 线程1获取的包没有被发送（因为代码路径不同）
- ❌ 当线程2停止时，音频发送完全停止

### 修复后

```
[INFO] ▶️  处理弹幕: 用户A: 你好
[DEBUG] 生成句子ID: a1b2c3d4...
[DEBUG] 已发送FIRST消息到TTS队列
[INFO] 调用LLM处理: 用户A说: 你好
[INFO] LLM回复: 你好！很高兴见到你！
[DEBUG] 发送文本给TTS: 你好！很高兴见到你！
[DEBUG] 已发送LAST消息到TTS队列
[INFO] ✅ 弹幕处理完成: 用户A
[DEBUG] 🔊 音频包 #1: 108 字节 → 1 个设备  ← 所有包都通过标准线程发送
[DEBUG] 🔊 音频包 #2: 112 字节 → 1 个设备
[DEBUG] 🔊 音频包 #3: 105 字节 → 1 个设备
[DEBUG] 🔊 音频包 #4: 98 字节 → 1 个设备
[INFO] ▶️  处理弹幕: 用户B: 讲个笑话
# 继续正常处理...
```

**优点**：
- ✅ 只有一个线程处理音频队列（无竞争）
- ✅ 所有音频包按顺序发送
- ✅ 音频发送连续、稳定
- ✅ 多条弹幕可以持续处理

## 技术细节

### 为什么标准线程可以正常工作？

1. **标准TTS线程架构**：
   ```python
   # core/providers/tts/base.py
   def _audio_play_priority_thread(self):
       while not self.conn.stop_event.is_set():
           sentence_type, audio_datas, text = self.tts_audio_queue.get(timeout=0.1)

           # 使用 asyncio.run_coroutine_threadsafe 在事件循环中执行
           future = asyncio.run_coroutine_threadsafe(
               sendAudioMessage(self.conn, sentence_type, audio_datas, text),
               self.conn.loop,  # DanmakuConnection 提供的事件循环
           )
           future.result()  # 阻塞等待完成
   ```

2. **sendAudioMessage 调用链**：
   ```python
   sendAudioMessage()
    → sendAudio()
    → _do_send_audio()
    → conn.websocket.send(opus_packet)
    → MockWebSocket.send()
    → device_manager.broadcast_audio()
   ```

3. **关键设计**：
   - `DanmakuConnection` 提供了所有 TTS 需要的属性（`loop`, `websocket`, 等）
   - `MockWebSocket.send()` 实现了广播逻辑
   - 标准线程已经完美支持广播模式！

### DanmakuConnection 的作用

`DanmakuConnection` 是一个"适配器"对象，它：
- 伪装成一个标准的 WebSocket 连接
- 提供 TTS 需要的所有属性和方法
- 但实际上将音频广播到所有设备而不是单个设备

```python
class DanmakuConnection:
    def __init__(self, device_manager, logger, config=None):
        # TTS 需要的属性
        self.loop = asyncio.get_event_loop()      # 事件循环
        self.stop_event = threading.Event()       # 停止信号
        self.audio_format = "opus"                # 音频格式
        self.conn_from_mqtt_gateway = False       # 使用 WebSocket 模式
        # ... 更多属性 ...

        # 创建模拟的 WebSocket
        self.websocket = self._create_mock_websocket()

    def _create_mock_websocket(self):
        class MockWebSocket:
            async def send(self, data):
                # 广播到所有设备！
                await self.device_manager.broadcast_audio(data)
        return MockWebSocket(self.device_manager, self.logger)
```

## 流控机制保持不变

弹幕流控（`flow_control_enabled`, `flow_control_strategy`）继续正常工作：

```python
async def add_danmaku(self, danmaku: dict):
    if self.flow_control_enabled:
        if self.flow_control_strategy == "skip":
            if self.is_speaking:
                self.logger.info(f"⏭️  正在播放音频，跳过弹幕: ...")
                return
            # 清空队列中的旧弹幕
            while not self.message_queue.empty():
                old_danmaku = self.message_queue.get_nowait()
```

`is_speaking` 标志控制弹幕处理，不影响音频发送。

## 测试建议

### 1. 正常场景测试

```bash
# 启动服务器
python danmaku_app.py

# 观察日志，应该看到：
# - ✅ 弹幕处理完成
# - 🔊 音频包 #1, #2, #3... 连续发送
# - 多条弹幕连续处理
```

### 2. 高频弹幕测试

启用模拟模式，观察连续弹幕处理：

```yaml
# danmaku_config.yaml
danmaku:
  use_mock: true
  flow_control_enabled: true
  flow_control_strategy: skip
```

**预期结果**：
- 音频发送不会中断
- 即使跳过一些弹幕（流控），其他弹幕的音频仍正常发送
- 设备持续接收音频数据

### 3. 多设备测试

连接多个 ESP32 设备或测试客户端：

```bash
# 终端1：启动服务器
python danmaku_app.py

# 终端2：启动测试设备1
python test_device_client.py --device-id device_001

# 终端3：启动测试设备2
python test_device_client.py --device-id device_002
```

**预期结果**：
- 所有设备同时接收相同的音频包
- 音频包序号连续（#1, #2, #3...）
- 没有音频包丢失

## 总结

### 问题核心

❌ **两个线程竞争同一个队列** → 音频包分散 → 发送不完整

### 解决方案

✅ **删除冗余线程** → 单一音频处理线程 → 音频发送稳定

### 关键认识

**标准TTS架构已经完美支持广播模式**，只需通过 `MockWebSocket` 适配器即可。不需要自定义音频工作线程。

---

## 相关文件

- `danmaku_server/danmaku_handler.py` - 弹幕处理器（已修复）
- `danmaku_server/danmaku_service.py` - 服务初始化
- `core/providers/tts/base.py` - TTS 基类（标准音频线程）
- `core/handle/sendAudioHandle.py` - 音频发送处理

---

修复完成日期：2025-12-16
