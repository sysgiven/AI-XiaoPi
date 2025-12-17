#!/usr/bin/env python3
"""简单测试：验证正则表达式是否正确"""

import re

# 测试1：不使用原始字符串
pattern1 = re.compile(
    "[\U0001F600-\U0001F64F]+",
    flags=re.UNICODE
)

# 测试2：使用原始字符串
pattern2 = re.compile(
    r"[\U0001F600-\U0001F64F]+",
    flags=re.UNICODE
)

test_cases = [
    "你好",
    "😀",
    "hello",
    "你好😀",
]

print("测试1：不使用原始字符串")
for text in test_cases:
    result = pattern1.sub('', text)
    print(f"  '{text}' → '{result}'")

print("\n测试2：使用原始字符串")
for text in test_cases:
    result = pattern2.sub('', text)
    print(f"  '{text}' → '{result}'")

# 测试中文Unicode范围
print("\n中文Unicode范围检查：")
print(f"  '你' = U+{ord('你'):04X}")
print(f"  '好' = U+{ord('好'):04X}")
print(f"  '😀' = U+{ord('😀'):04X}")
print(f"  '哈' = U+{ord('哈'):04X}")
