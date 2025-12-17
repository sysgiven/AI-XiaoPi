#!/usr/bin/env python3
"""
日志过滤工具 - 提取关键诊断信息
使用方法：python filter_logs.py
"""

import sys

# 关键日志标记
KEY_PATTERNS = [
    "▶️  处理弹幕",           # 弹幕开始处理
    "✅ 设置conn.sentence_id",  # sentence_id 设置
    "🔍 流控检查",             # 流控检查
    "⏭️  正在播放",           # 流控跳过
    "🔄 重置弹幕处理状态",      # 状态重置
    "🔍 Rate Controller 诊断", # Rate Controller 状态
    "🔍 need_reset",          # 是否重置判断
    "✅ 执行重置",             # 执行重置
    "⏭️  跳过重置",           # 跳过重置
    "🎬 准备启动",             # 后台任务启动
    "🎬 Rate Controller后台任务已启动",  # 后台任务运行
    "🎬 Rate Controller后台任务被取消",  # 后台任务取消
    "🔊 音频包",               # 音频包发送
    "ERROR",                   # 错误信息
    "Exception",               # 异常
]

def filter_logs():
    """从标准输入读取日志并过滤关键行"""
    print("=" * 80)
    print("关键日志过滤器 - 等待日志输入...")
    print("提示：将日志文件内容粘贴到此窗口，然后按 Ctrl+Z (Windows) 或 Ctrl+D (Linux/Mac)")
    print("=" * 80)
    print()

    line_count = 0
    matched_count = 0

    for line in sys.stdin:
        line_count += 1
        line_stripped = line.strip()

        # 检查是否包含关键模式
        for pattern in KEY_PATTERNS:
            if pattern in line_stripped:
                matched_count += 1
                print(line_stripped)
                break

    print()
    print("=" * 80)
    print(f"处理完成：共检查 {line_count} 行，匹配 {matched_count} 行关键日志")
    print("=" * 80)

if __name__ == "__main__":
    try:
        filter_logs()
    except KeyboardInterrupt:
        print("\n\n中断")
        sys.exit(0)
