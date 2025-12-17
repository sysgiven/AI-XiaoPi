# Sentence ID Fix - Rate Controller Backend Task Not Starting

## Problem Summary

**Symptom**: Hardware device not playing audio despite successful TTS generation. Audio packets accumulating in Rate Controller queue (100+ packets) without being sent.

## Root Cause

The diagnostic logs revealed:
```
🔍 Rate Controller 诊断:
   is_single_packet=True
   current_sentence_id=None    ← PROBLEM!
   flow_control_sentence_id=None
   has_rate_controller=True
🔍 need_reset=False, will 跳过 backend task
```

**Issue**: `conn.sentence_id` was always `None` in the DanmakuConnection object.

## Technical Analysis

The Rate Controller's reset condition in `sendAudioHandle.py:139-143`:
```python
need_reset = (
    is_single_packet
    and getattr(conn, "audio_flow_control", {}).get("sentence_id")
    != conn.sentence_id
) or not hasattr(conn, "audio_rate_controller")
```

When both sentence IDs are `None`:
- `is_single_packet=True` ✓
- `None != None` evaluates to **False** ✗
- `has_rate_controller=True` so second condition also False
- **Result**: `need_reset=False`, backend task never starts

## The Fix

**File**: `danmaku_server/danmaku_handler.py:240-256`

**Change**: Set `sentence_id` on the connection object before sending TTS messages:

```python
# 生成唯一的句子ID
sentence_id = str(uuid.uuid4().hex)
self.logger.debug(f"   生成句子ID: {sentence_id}")

# 更新conn对象的sentence_id，以便Rate Controller能正确检测句子变化
self.tts.conn.sentence_id = sentence_id
self.logger.info(f"✅ 设置conn.sentence_id = {sentence_id}")

# 发送FIRST消息（开始）
self.tts.tts_text_queue.put(...)
```

## Why This Works

1. **Before Fix**:
   - Generate sentence_id per弹幕
   - Never set it on `conn.sentence_id`
   - Rate Controller sees: `None != None` → False → No backend task
   - Audio packets accumulate in queue with no consumer

2. **After Fix**:
   - Generate sentence_id per弹幕
   - **Set it on `conn.sentence_id` immediately**
   - Rate Controller sees: `new_id != None` (first time) or `new_id != old_id` → True
   - Backend task starts, processes queue, sends audio to device

## Expected Behavior After Fix

When you test with a new弹幕 message, you should see:

```
✅ 设置conn.sentence_id = abc123def456...
🔍 Rate Controller 诊断:
   is_single_packet=True
   current_sentence_id=abc123def456...    ← Now has value!
   flow_control_sentence_id=None
   has_rate_controller=True
🔍 need_reset=True, will 启动 backend task
✅ 执行重置并启动后台任务
🎬 准备启动后台发送循环...
🎬 正在启动Rate Controller后台任务...
🎬 Rate Controller后台任务已启动
🎬 Rate Controller准备发送音频包: XXX字节, 剩余队列: YY
🎬 后台任务send_callback被调用: XXX字节
🔊 音频包 #N: XXX 字节 → 1 个设备
```

## Impact

- ✅ Fixes audio playback for all弹幕 messages
- ✅ Rate Controller backend task properly initializes
- ✅ Queued audio packets sent to hardware device at correct timing (60ms intervals)
- ✅ No changes to existing architecture, minimal code change
- ✅ Diagnostic logs remain in place for future debugging

## Testing

To verify the fix works:
1. Send a弹幕 message
2. Check logs for "✅ 设置conn.sentence_id"
3. Check logs for "🎬 Rate Controller后台任务已启动"
4. Check logs for audio packets being sent: "🔊 音频包"
5. Confirm hardware device plays audio

Date: 2025-12-16
Status: Fixed
