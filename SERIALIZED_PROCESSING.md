# 弹幕串行化处理方案

## 📋 设计目标

模拟真实的人机对话流程：
1. 接收一条弹幕（相当于"人说话"）
2. LLM 生成回复
3. 转换为音频并发送到硬件
4. **等待硬件播放完成**
5. 再处理下一条弹幕
6. **中间到达的弹幕全部忽略**（只保留最新的）

---

## 🔧 核心改动

### 1. **串行化处理循环** (`danmaku_handler.py:142-173`)

```python
async def start(self):
    """启动消息处理（串行化模式）"""
    while self.processing:
        # 清空队列中的旧弹幕，只保留最新的
        latest_danmaku = None
        while True:
            try:
                latest_danmaku = self.message_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        # 如果没有弹幕，等待新弹幕
        if latest_danmaku is None:
            latest_danmaku = await asyncio.wait_for(
                self.message_queue.get(),
                timeout=1.0
            )

        # 处理弹幕消息（会阻塞直到音频播放完成）
        await self._process_danmaku(latest_danmaku)
```

**关键点**：
- ✅ 每次循环时清空队列，只保留最新弹幕
- ✅ `_process_danmaku()` 是阻塞的，直到音频播放完成才返回
- ✅ 这确保了严格的串行化：一次只处理一条弹幕

---

### 2. **简化弹幕添加逻辑** (`danmaku_handler.py:182-193`)

```python
async def add_danmaku(self, danmaku: dict):
    """直接添加弹幕到队列，由 start() 负责清理旧弹幕"""
    await self.message_queue.put(danmaku)
```

**移除了**：
- ❌ 复杂的流控检查（`is_speaking` 状态）
- ❌ 队列大小限制
- ❌ 跳过逻辑

**原因**：`start()` 循环已经负责清理旧弹幕，不需要在添加时做流控判断。

---

### 3. **等待音频播放完成** (`danmaku_handler.py:195-275`)

```python
async def _process_danmaku(self, danmaku: dict):
    """处理单条弹幕消息（串行化：等待音频播放完成）"""
    # ... 生成回复并发送 ...

    # 发送LAST消息（结束）
    self.tts.tts_text_queue.put(
        TTSMessageDTO(
            sentence_id=sentence_id,
            sentence_type=SentenceType.LAST,
            content_type=ContentType.ACTION,
        )
    )

    # ✨ 关键：等待音频播放完成后再返回（串行化处理）
    self.logger.info(f"⏳ 等待音频播放完成...")
    await self._wait_for_audio_completion()
    self.logger.info(f"✅ 弹幕处理完成: {username}")
```

**关键点**：
- ✅ 发送 LAST 消息后立即等待音频播放完成
- ✅ 只有音频播放完成后才返回，才能处理下一条弹幕

---

### 4. **音频完成等待机制** (`danmaku_handler.py:277-302`)

```python
async def _wait_for_audio_completion(self):
    """等待音频播放完成（使用 Rate Controller 的队列清空事件）"""
    if hasattr(self.tts.conn, "audio_rate_controller") and self.tts.conn.audio_rate_controller:
        rate_controller = self.tts.conn.audio_rate_controller
        queue_len = len(rate_controller.queue)
        if queue_len > 0:
            # 等待队列清空事件（带超时保护）
            await asyncio.wait_for(
                rate_controller.queue_empty_event.wait(),
                timeout=60.0  # 最多等待60秒
            )
    else:
        # 没有 Rate Controller，等待一小段时间确保音频发送完成
        await asyncio.sleep(0.5)
```

**机制**：
- ✅ 使用 `AudioRateController.queue_empty_event` 等待队列清空
- ✅ 60秒超时保护，防止无限等待
- ✅ 兼容性：如果没有 Rate Controller，fallback 到简单延迟

---

## 🎯 工作流程

### 原流程（有问题）
```
弹幕1 → LLM → TTS → 音频发送 (异步)
弹幕2 → LLM → TTS → 音频发送 (异步)  ← 问题：弹幕2可能在弹幕1音频还没播完时就开始
弹幕3 → ...
```

### 新流程（串行化）
```
弹幕1 → LLM → TTS → 音频发送 → 等待播放完成 ✓
                                                ↓
弹幕2 → LLM → TTS → 音频发送 → 等待播放完成 ✓
                                                ↓
弹幕3 → LLM → TTS → 音频发送 → 等待播放完成 ✓
```

### 弹幕高频到达时
```
弹幕1 正在处理...
弹幕2 进入队列
弹幕3 进入队列
弹幕4 进入队列

当弹幕1处理完成后：
  - 清空队列，只保留 弹幕4（最新）
  - 弹幕2、弹幕3 被丢弃
  - 开始处理 弹幕4
```

---

## ✅ 优势

1. **逻辑简单**：
   - 没有复杂的流控状态管理
   - 没有竞态条件
   - 代码清晰易维护

2. **完全串行化**：
   - 一次只处理一条弹幕
   - 音频不会重叠或混乱
   - 模拟真实对话体验

3. **自动忽略中间弹幕**：
   - 高频弹幕不会导致队列堆积
   - 只响应最新的弹幕
   - 用户体验更好

4. **兼容原项目架构**：
   - 复用原 xiaozhi-server 的 TTS 线程处理
   - 复用 Rate Controller 的音频流控
   - 只改变弹幕处理的调度逻辑

---

## 📊 关键日志输出

正常流程：
```
▶️  处理弹幕: 用户A: 你好
✅ 设置conn.sentence_id: None → abc123...
🎬 启动新的Rate Controller后台任务
Rate Controller 后台任务启动
🔊 音频包 #1, #20, #40...
⏳ 等待音频播放完成...
   音频队列已清空
✅ 弹幕处理完成: 用户A

▶️  处理弹幕: 用户B: 测试
✅ 设置conn.sentence_id: abc123... → def456...
🎬 启动新的Rate Controller后台任务
Rate Controller 后台任务启动
🔊 音频包 #1, #20, #40...
⏳ 等待音频播放完成...
   音频队列已清空
✅ 弹幕处理完成: 用户B
```

---

## 🔍 对比原 xiaozhi-server

| 特性 | 原项目 (connection.py) | 弹幕系统 (danmaku_handler.py) |
|------|----------------------|----------------------------|
| 输入源 | 语音（通过 WebSocket） | 弹幕文本 |
| 处理触发 | 语音结束时 (VAD) | 弹幕到达时 |
| 并发控制 | 单连接单会话，天然串行 | 手动实现串行化处理 |
| 流控方式 | 无需流控（用户说话自然是串行的） | 清空队列 + 等待音频完成 |
| LLM → TTS | `chat()` 方法，同步流式 | `_call_llm()` + 手动发送FIRST/LAST |
| 音频发送 | TTS 线程自动处理 | 同样使用 TTS 线程 + Rate Controller |
| 等待机制 | 无需等待（用户会等待回复） | 主动等待音频播放完成 |

---

## 📝 待测试

1. **正常流程**：
   - [ ] 发送一条弹幕，确认能正常播放音频
   - [ ] 发送第二条弹幕，确认在第一条播放完后才开始处理

2. **高频弹幕**：
   - [ ] 快速发送10条弹幕，确认只有最新的被处理

3. **边界情况**：
   - [ ] LLM 返回空内容
   - [ ] 纯表情弹幕
   - [ ] 音频播放超时（60秒）

---

**日期**: 2025-12-17
**状态**: ✅ 代码重写完成，待测试验证
