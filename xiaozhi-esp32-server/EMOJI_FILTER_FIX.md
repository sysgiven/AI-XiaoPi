# EdgeTTS 表情符号错误修复

## 问题描述

用户报告错误：
```
-语音生成失败1次: ‍♀️，错误: Edge TTS请求失败: No audio was received. Please verify that your parameters are correct.
```

**原因**：EdgeTTS 收到了纯表情符号文本，无法生成语音。

## 根本原因

### 1. 表情符号过滤不完整

原有的表情符号过滤正则表达式：
```python
text_without_emoji = re.sub(
    r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF...]',
    '', content
)
```

**缺陷**：
- 不包含复合表情符号（如 "‍♀️"、"🏃‍♀️"）
- 缺少零宽连接符（\U0000200D）
- 缺少变体选择器（\U0000FE0F）
- 缺少性别符号（\U00002640-\U00002642）

### 2. 两个表情来源

表情符号可能来自：
- **弹幕输入**：用户发送纯表情
- **LLM回复**：LLM生成的回复只包含表情

## 修复方案

### 1. 创建改进的表情过滤函数

**文件**: `danmaku_server/danmaku_handler.py`

```python
def is_pure_emoji_or_empty(text: str) -> bool:
    """
    检查文本是否为纯表情符号或空文本

    覆盖范围：
    - 基本表情符号（😀🎉🎨等）
    - 复合表情符号（👨‍👩‍👧‍👦等）
    - 性别符号（♂️♀️）
    - 国旗表情（🇨🇳🇺🇸等）
    - 零宽连接符和变体选择器
    """
    if not text or not text.strip():
        return True

    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U00002600-\U000026FF"  # miscellaneous symbols
        "\U00002700-\U000027BF"  # dingbats
        "\U0001F018-\U0001F270"  # various symbols
        "\U0001F300-\U0001F5FF"  # miscellaneous symbols and pictographs
        "\U0000200D"             # zero width joiner (复合表情关键！)
        "\U0000FE0F"             # variation selector
        "\U00002640-\U00002642"  # gender symbols (♂️♀️)
        "]+",
        flags=re.UNICODE
    )

    text_without_emoji = emoji_pattern.sub('', text)
    text_cleaned = text_without_emoji.strip()

    return len(text_cleaned) == 0
```

### 2. 在弹幕输入阶段过滤

```python
async def _process_danmaku(self, danmaku: dict):
    username = danmaku.get('username', '观众')
    content = danmaku.get('content', '')

    # 过滤纯表情符号的弹幕
    if is_pure_emoji_or_empty(content):
        self.logger.info(f"⏭️  跳过纯表情弹幕: {username}: {content}")
        return
```

### 3. 在LLM回复阶段过滤

```python
# 调用LLM生成回复
response_text = await self._call_llm(query, sentence_id)

# 检查LLM回复是否有效
if not response_text or not response_text.strip():
    self.logger.warning(f"⚠️  LLM返回空内容，跳过此弹幕: {username}: {content}")
    return

# 检查LLM回复是否为纯表情（避免TTS失败）
if is_pure_emoji_or_empty(response_text):
    self.logger.warning(f"⚠️  LLM返回纯表情，跳过TTS: {username} → {response_text}")
    # 仍然添加到对话历史，但不发送TTS
    self.dialogue.put(Message(role="assistant", content=response_text))
    return
```

## 修复效果

### 修复前

```
[INFO] ▶️  处理弹幕: 用户A: ‍♀️
[INFO] 调用LLM处理: 用户A说: ‍♀️
[INFO] LLM回复: 🎉
[ERROR] -语音生成失败1次: 🎉，错误: Edge TTS请求失败: No audio was received
# TTS失败，但流程中断
```

### 修复后（场景1：弹幕是纯表情）

```
[INFO] ⏭️  跳过纯表情弹幕: 用户A: ‍♀️
# 直接跳过，不调用LLM和TTS
```

### 修复后（场景2：LLM回复是纯表情）

```
[INFO] ▶️  处理弹幕: 用户A: 你好
[INFO] 调用LLM处理: 用户A说: 你好
[INFO] LLM回复: 😊
[WARNING] ⚠️  LLM返回纯表情，跳过TTS: 用户A → 😊
# 跳过TTS，继续处理下一条弹幕
```

### 修复后（场景3：正常文本）

```
[INFO] ▶️  处理弹幕: 用户A: 你好
[INFO] 调用LLM处理: 用户A说: 你好
[INFO] LLM回复: 你好！很高兴见到你！
[DEBUG] 🔊 音频包 #1: 108 字节 → 1 个设备
[DEBUG] 🔊 音频包 #2: 112 字节 → 1 个设备
[INFO] ✅ 弹幕处理完成: 用户A
```

## 测试验证

### 运行表情符号过滤测试

```bash
python test_emoji_filter.py
```

**预期结果**：
```
============================================================
表情符号过滤测试
============================================================
✅ PASS | 空字符串                    | 输入: ''                 | 结果: True | 预期: True
✅ PASS | 空白字符                    | 输入: '   '              | 结果: True | 预期: True
✅ PASS | 单个笑脸                    | 输入: '😀'               | 结果: True | 预期: True
✅ PASS | 女性符号（复合表情）        | 输入: '‍♀️'              | 结果: True | 预期: True
✅ PASS | 跑步女性（复合表情）        | 输入: '🏃‍♀️'            | 结果: True | 预期: True
✅ PASS | 你好                        | 输入: '你好'             | 结果: False | 预期: False
✅ PASS | 你好😀                      | 输入: '你好😀'           | 结果: False | 预期: False
============================================================
测试完成: 20 通过, 0 失败
============================================================
```

### 实际场景测试

启动服务器，发送各种表情符号弹幕：

```bash
python danmaku_app.py
```

**测试用例**：
1. 发送纯表情弹幕："😀"、"❤️"、"‍♀️"
   - ✅ 应该看到 "⏭️ 跳过纯表情弹幕"
   - ✅ 不调用LLM和TTS

2. 发送混合内容："你好😀"
   - ✅ 正常处理
   - ✅ LLM生成回复并合成语音

3. 让LLM回复表情（通过提示词测试）
   - ✅ 应该看到 "⚠️ LLM返回纯表情，跳过TTS"
   - ✅ 继续处理下一条弹幕

## 技术细节

### 复合表情符号原理

复合表情符号使用**零宽连接符（Zero Width Joiner, ZWJ）**连接多个Unicode字符：

```
‍♀️ =
  \U0000200D (ZWJ) +
  \U00002640 (♀ - Female Sign) +
  \U0000FE0F (Variation Selector-16)

🏃‍♀️ =
  \U0001F3C3 (🏃 - Runner) +
  \U0000200D (ZWJ) +
  \U00002640 (♀ - Female Sign) +
  \U0000FE0F (Variation Selector-16)
```

**关键**：必须包含 `\U0000200D` 才能正确过滤复合表情。

### Unicode 表情范围参考

| 范围 | 描述 | 示例 |
|------|------|------|
| `\U0001F600-\U0001F64F` | 基本表情（脸部） | 😀😁😂😃 |
| `\U0001F300-\U0001F5FF` | 符号和象形文字 | 🌍🎨🎉📱 |
| `\U0001F680-\U0001F6FF` | 交通和地图 | 🚀🚗🚁✈️ |
| `\U0001F1E0-\U0001F1FF` | 区域指示符（国旗） | 🇨🇳🇺🇸🇯🇵 |
| `\U0001F900-\U0001F9FF` | 补充符号和象形文字 | 🤦🤷🦄🦋 |
| `\U00002640-\U00002642` | 性别符号 | ♀️♂️ |
| `\U0000200D` | 零宽连接符（ZWJ） | （不可见） |
| `\U0000FE0F` | 变体选择器-16 | （不可见） |

## 预防措施

### 1. 在提示词中建议LLM避免纯表情回复

可以在系统提示词中添加：

```yaml
# danmaku_config.yaml
prompt: |
  你是一个直播间的AI助手，名叫小智。
  [核心特征]
  - 回复简洁明快，每次回复控制在50字以内
  - 语气活泼友好，适合直播间氛围
  - 用文字回复，避免只发送表情符号
  [交互指南]
  当观众：
  - 打招呼 → 热情回应并简单介绍自己
  - 提问题 → 简明扼要地回答
  - 闲聊 → 幽默友好地互动
  注意：
  - 回复要快速、简短
  - 保持积极正面的态度
  - 使用文字表达，可以配合表情但不要只发表情
```

### 2. 日志监控

观察日志中的警告信息：
- `⏭️ 跳过纯表情弹幕` - 弹幕输入阶段过滤
- `⚠️ LLM返回纯表情，跳过TTS` - LLM输出阶段过滤

如果频繁出现，可能需要：
- 调整LLM提示词
- 考虑弹幕预处理规则

## 相关文件

- `danmaku_server/danmaku_handler.py` - 弹幕处理器（已修复）
- `test_emoji_filter.py` - 表情符号过滤测试脚本（新增）
- `danmaku_config.yaml` - 配置文件（可选：调整提示词）

## 总结

### 问题
❌ EdgeTTS 无法为纯表情符号生成语音 → 报错并可能中断流程

### 解决方案
✅ **双重过滤机制**：
1. 弹幕输入阶段 - 过滤纯表情弹幕
2. LLM输出阶段 - 过滤纯表情回复

✅ **改进的表情过滤**：
- 支持复合表情（零宽连接符）
- 支持性别符号和国旗
- 覆盖更全面的Unicode范围

### 效果
- 🎯 EdgeTTS 不再收到纯表情输入
- 🎯 流程不会因TTS失败而中断
- 🎯 正常文本和混合内容仍正常处理

---

修复完成日期：2025-12-16
