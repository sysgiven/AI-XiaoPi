# 音频发送调试 - 找出音频数据丢失的位置

## 问题现状

**现象**：
- ✅ 语音生成成功（EdgeTTS成功生成音频）
- ✅ 设备已连接并保持稳定（添加了ping/pong心跳后）
- ❌ **硬件设备收不到音频数据**
- ❌ 没有看到 MockWebSocket 的 `🔊 音频包` 日志

## 排查过程

### 1. 确认TTS工作流程

```python
LLM回复片段 → 发送给TTS
 ↓
TTS文本队列 (tts_text_queue)
 ↓
tts_text_priority_thread 处理
 ↓
EdgeTTS生成音频 (text_to_speak)
 ↓
audio_bytes_to_data_stream() 转换为Opus包
 ↓
handle_opus() callback → tts_audio_queue
 ↓
_audio_play_priority_thread 从队列取出
 ↓
sendAudioMessage() → sendAudio()
 ↓
conn.websocket.send() → MockWebSocket.send()
 ↓
device_manager.broadcast_audio() → 硬件设备
```

### 2. 日志分析

**有的日志**（说明这些步骤正常）：
```log
✅ LLM回复: xxx
✅ 📝 已发送 N 段文本给TTS
✅ 语音生成成功: xxx，重试0次
✅ 发送第一段语音: xxx
✅ 发送音频消息: SentenceType.FIRST, xxx
```

**缺失的日志**（说明这些步骤没有执行）：
```log
❌ 🎵 开始转换音频: ... (应该在 audio_bytes_to_data_stream() 中打印)
❌ 推送数据到队列里面帧数～～ xxx (应该在 handle_opus() 中打印)
❌ 🔊 音频包 #N: xxx 字节 → N 个设备 (应该在 MockWebSocket.send() 中打印)
```

**结论**：音频数据在 `audio_bytes_to_data_stream()` 之前就丢失了，或者这个函数根本没有被调用！

### 3. 代码追踪

在 `base.py:85-117` 的 `to_tts_stream()` 方法中：

```python
if self.delete_audio_file:  # ← delete_audio=true，走这个分支
    while max_repeat_time > 0:
        try:
            # 生成音频二进制数据
            audio_bytes = asyncio.run(self.text_to_speak(text, None))

            if audio_bytes:
                # 放入FIRST消息（标记句子开始，无音频数据）
                self.tts_audio_queue.put((SentenceType.FIRST, None, text))

                # 转换音频数据为Opus包流
                audio_bytes_to_data_stream(
                    audio_bytes,
                    file_type=self.audio_file_type,  # ← EdgeTTS是"mp3"
                    is_opus=True,
                    callback=opus_handler,  # ← 应该调用handle_opus()
                )
                break
```

**关键问题**：`audio_bytes_to_data_stream()` 应该被调用，但日志中没有看到 `🎵 开始转换音频`！

### 4. 可能的原因

#### 原因A：audio_bytes 为空或None
```python
if audio_bytes:  # ← 如果为False，不会执行转换
    ...
```

但是日志显示"语音生成成功"，说明 `audio_bytes` 应该不为空。

#### 原因B：异常被吞掉
```python
except Exception as e:
    logger.bind(tag=TAG).warning(f"语音生成失败...")
    max_repeat_time -= 1
```

但是日志中没有"语音生成失败"的警告。

#### 原因C：线程问题
`tts_text_priority_thread` 是普通线程，调用 `asyncio.run()` 可能有问题？

#### 原因D：配置问题
- `self.delete_audio_file` 实际上是 False？
- `self.audio_file_type` 不是 "mp3"？

## 添加的调试日志

在 `util.py:audio_bytes_to_data_stream()` 中添加：
```python
logger.bind(tag="util").debug(f"🎵 开始转换音频: 格式={file_type}, 大小={len(audio_bytes) if audio_bytes else 0}字节, opus={is_opus}")
```

在 `util.py:pcm_to_data_stream()` 中添加：
```python
logger.bind(tag="util").debug(f"🎵 PCM转换完成: 共生成 {frame_count} 个Opus帧")
```

## 测试步骤

1. **重启服务器**：
   ```bash
   cd /c/Users/me/Documents/MyProject/xiaozhi-esp32-server/main/xiaozhi-server
   python danmaku_app.py
   ```

2. **连接ESP32设备**

3. **发送测试弹幕**（通过抖音直播间或DouyinBarrageGrab）

4. **观察日志输出**，重点看：
   - 是否出现 `🎵 开始转换音频`
   - 是否出现 `🎵 音频解码完成`
   - 是否出现 `🎵 PCM转换完成: 共生成 N 个Opus帧`
   - 是否出现 `推送数据到队列里面帧数～～`
   - 是否出现 `🔊 音频包`

## 预期结果

### 场景1：看到转换日志但没有Opus帧
```log
✅ 语音生成成功: 你好，重试0次
✅ 🎵 开始转换音频: 格式=mp3, 大小=12345字节, opus=True
✅ 🎵 音频解码完成: PCM数据大小=54321字节
✅ 🎵 PCM转换完成: 共生成 0 个Opus帧  ← 问题在编码
```
**结论**：Opus编码器有问题

### 场景2：看到Opus帧但没有推送到队列
```log
✅ 语音生成成功: 你好，重试0次
✅ 🎵 开始转换音频: 格式=mp3, 大小=12345字节, opus=True
✅ 🎵 音频解码完成: PCM数据大小=54321字节
✅ 🎵 PCM转换完成: 共生成 28 个Opus帧
❌ (没有"推送数据到队列里面帧数～～")  ← 问题在callback
```
**结论**：`opus_handler` (即 `handle_opus()`) 没有被正确传递或调用

### 场景3：推送到队列但没有发送
```log
✅ 语音生成成功: 你好，重试0次
✅ 🎵 开始转换音频: ...
✅ 🎵 PCM转换完成: 共生成 28 个Opus帧
✅ 推送数据到队列里面帧数～～ 160
✅ 推送数据到队列里面帧数～～ 162
... (28次)
✅ 发送第一段语音: 你好
✅ 发送音频消息: SentenceType.FIRST, 你好
❌ (没有"🔊 音频包")  ← 问题在WebSocket发送
```
**结论**：音频队列工作正常，但 `conn.websocket.send()` 没有调用到 MockWebSocket

### 场景4：根本没有转换日志
```log
✅ 语音生成成功: 你好，重试0次
❌ (没有"🎵 开始转换音频")  ← 问题在这之前
```
**结论**：`audio_bytes_to_data_stream()` 根本没有被调用，可能是：
- `audio_bytes` 为空（但EdgeTTS说成功了？）
- 走了其他代码分支
- 异常被吞掉了

## 后续排查

根据测试结果，确定问题位置后进一步调试。

---

创建日期：2025-12-16
状态：等待测试验证
