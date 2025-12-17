#!/usr/bin/env python3
"""
表情符号过滤测试脚本
测试 is_pure_emoji_or_empty() 和 remove_emojis() 函数
"""

import re

# 全局表情符号正则模式（与 danmaku_handler.py 相同）
EMOJI_PATTERN = re.compile(
    "["
    "\u2600-\u26FF"      # Miscellaneous Symbols
    "\u2700-\u27BF"      # Dingbats
    "\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F680-\U0001F6FF"  # Transport and Map Symbols
    "\U0001F700-\U0001F77F"  # Alchemical Symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "\U0001F1E0-\U0001F1FF"  # Flags
    "]+",
    flags=re.UNICODE
)


def remove_emojis(text: str) -> str:
    """移除文本中的所有表情符号"""
    if not text:
        return text

    # 第一步：移除表情符号主体
    result = EMOJI_PATTERN.sub('', text)

    # 第二步：移除孤立的变体选择器和零宽连接符
    result = re.sub(r'[\uFE00-\uFE0F\u200D]', '', result)

    return result.strip()


def is_pure_emoji_or_empty(text: str) -> bool:
    """检查文本是否为纯表情符号或空文本"""
    if not text or not text.strip():
        return True
    text_without_emoji = remove_emojis(text)
    return len(text_without_emoji) == 0


def test_emoji_filter():
    """测试各种输入"""

    test_cases = [
        # (输入, 预期is_pure结果, 预期remove结果, 描述)
        ("", True, "", "空字符串"),
        ("   ", True, "", "空白字符"),
        ("😀", True, "", "单个笑脸"),
        ("😀😀😀", True, "", "多个笑脸"),
        ("👋", True, "", "挥手"),
        ("❤️", True, "", "红心"),
        ("‍♀️", True, "", "女性符号（复合表情）"),
        ("🏃‍♀️", True, "", "跑步女性（复合表情）"),
        ("🏋️‍♂️", True, "", "举重男性"),
        ("👨‍👩‍👧‍👦", True, "", "家庭表情"),
        ("🇨🇳", True, "", "中国国旗"),
        ("♂️", True, "", "男性符号"),
        ("♀️", True, "", "女性符号"),
        ("⚽", True, "", "足球"),
        ("你好", False, "你好", "纯文字"),
        ("你好😀", False, "你好", "文字+表情"),
        ("😀你好", False, "你好", "表情+文字"),
        ("你😀好", False, "你好", "文字中间有表情"),
        ("hello", False, "hello", "英文"),
        ("123", False, "123", "数字"),
        ("你好！", False, "你好！", "中文+标点"),
        ("好的，宸哥，这首《会开花的云》很有意境，让我们一起享受音乐的美吧！🎶🌥️", False, "好的，宸哥，这首《会开花的云》很有意境，让我们一起享受音乐的美吧！", "实际场景测试"),
        ("哈哈，Nn老兄，欢迎来直播间！我是小智，你的健身小助手，一起加油变帅吧！🏋️‍♂️👍", False, "哈哈，Nn老兄，欢迎来直播间！我是小智，你的健身小助手，一起加油变帅吧！", "实际场景测试2"),
    ]

    print("=" * 80)
    print("表情符号过滤测试")
    print("=" * 80)

    # 首先测试中文是否被正确保留
    print("\n🔍 关键测试：中文字符处理")
    test_text = "你好"
    result = remove_emojis(test_text)
    print(f"  输入: '{test_text}'")
    print(f"  输出: '{result}'")
    print(f"  状态: {'✅ 正常' if result == test_text else '❌ 中文被错误移除！'}")

    test_text2 = "哈哈，Nn老兄"
    result2 = remove_emojis(test_text2)
    print(f"  输入: '{test_text2}'")
    print(f"  输出: '{result2}'")
    print(f"  状态: {'✅ 正常' if result2 == test_text2 else '❌ 中文被错误移除！'}")

    print("\n" + "=" * 80)

    passed = 0
    failed = 0

    for text, expected_pure, expected_removed, description in test_cases:
        is_pure_result = is_pure_emoji_or_empty(text)
        removed_result = remove_emojis(text)

        is_pure_ok = (is_pure_result == expected_pure)
        removed_ok = (removed_result == expected_removed)
        all_ok = is_pure_ok and removed_ok

        status = "✅ PASS" if all_ok else "❌ FAIL"

        if all_ok:
            passed += 1
        else:
            failed += 1

        # 格式化输出
        text_repr = repr(text) if len(text) < 30 else repr(text[:27] + "...")
        print(f"\n{status} | {description}")
        print(f"  输入: {text_repr}")
        print(f"  is_pure: {is_pure_result} (预期: {expected_pure}) {'✓' if is_pure_ok else '✗'}")
        print(f"  去除表情: {repr(removed_result[:30] + '...' if len(removed_result) > 30 else removed_result)} (预期: {repr(expected_removed[:30] + '...' if len(expected_removed) > 30 else expected_removed)}) {'✓' if removed_ok else '✗'}")

    print("=" * 80)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    success = test_emoji_filter()
    exit(0 if success else 1)
