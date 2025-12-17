"""
调试音频文件
检查接收到的音频文件的实际内容
"""

import os
from pathlib import Path

def analyze_file(file_path):
    """分析文件内容"""
    print(f"\n{'='*60}")
    print(f"文件: {file_path}")
    print(f"{'='*60}")

    # 检查文件大小
    size = os.path.getsize(file_path)
    print(f"大小: {size} 字节 ({size/1024:.2f} KB)")

    # 读取文件头部
    with open(file_path, 'rb') as f:
        header = f.read(min(64, size))

    # 显示十六进制
    print(f"\n前 {len(header)} 字节 (十六进制):")
    hex_str = ' '.join(f'{b:02x}' for b in header[:32])
    print(f"  {hex_str}")

    # 显示 ASCII（如果可打印）
    print(f"\n前 {len(header)} 字节 (ASCII，仅可打印字符):")
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in header[:64])
    print(f"  {ascii_str}")

    # 检测文件类型
    print(f"\n文件类型检测:")

    # MP3 格式标识
    if header[:3] == b'ID3' or (header[0:2] == b'\xff\xfb') or (header[0:2] == b'\xff\xf3'):
        print("  ✅ 可能是 MP3 格式 (ID3 标签或 MPEG 帧头)")
        return "MP3"

    # Opus 格式标识（在 Ogg 容器中）
    elif header[:4] == b'OggS':
        print("  ✅ 可能是 Ogg 容器 (Opus 音频通常在 Ogg 中)")
        if b'OpusHead' in header:
            print("  ✅ 确认包含 Opus 音频流")
            return "Opus"
        return "Ogg"

    # WAV 格式
    elif header[:4] == b'RIFF' and header[8:12] == b'WAVE':
        print("  ✅ 可能是 WAV 格式")
        return "WAV"

    # JSON 格式（可能是错误消息）
    elif header[0:1] == b'{':
        print("  ⚠️  文件内容是 JSON (可能是错误消息)")
        try:
            import json
            content = header.decode('utf-8')
            data = json.loads(content)
            print(f"  JSON 内容: {data}")
        except:
            pass
        return "JSON"

    # 纯文本
    elif all(32 <= b < 127 or b in (9, 10, 13) for b in header[:32]):
        print("  ⚠️  文件内容是纯文本")
        print(f"  内容: {header[:100].decode('utf-8', errors='ignore')}")
        return "TEXT"

    else:
        print("  ❌ 未知格式")
        return "Unknown"


def main():
    print("="*60)
    print("音频文件调试工具")
    print("="*60)

    # 获取所有接收到的文件
    audio_dir = Path("received_audio")
    if not audio_dir.exists():
        print(f"❌ 目录不存在: {audio_dir}")
        return

    files = list(audio_dir.glob("*.*"))

    if not files:
        print(f"⚠️  目录中没有文件: {audio_dir}")
        return

    print(f"\n找到 {len(files)} 个文件\n")

    # 分析每个文件
    file_types = {}
    for file_path in sorted(files):
        file_type = analyze_file(str(file_path))
        file_types[file_type] = file_types.get(file_type, 0) + 1

    # 统计
    print("\n" + "="*60)
    print("统计结果")
    print("="*60)
    for file_type, count in sorted(file_types.items()):
        print(f"{file_type}: {count} 个文件")
    print()


if __name__ == "__main__":
    main()
