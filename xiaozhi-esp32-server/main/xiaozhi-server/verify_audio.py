"""
验证 Opus 音频文件
使用 ffprobe 检查音频文件信息，并可选转换为 MP3 格式

使用方法:
    python verify_audio.py
    python verify_audio.py --convert  # 转换所有文件为 MP3
"""

import subprocess
import os
import sys
import json
from pathlib import Path


def check_ffmpeg():
    """检查 ffmpeg 和 ffprobe 是否已安装"""
    try:
        subprocess.run(['ffprobe', '-version'],
                      capture_output=True, check=True)
        subprocess.run(['ffmpeg', '-version'],
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def verify_opus_file(file_path):
    """
    验证 Opus 文件

    Args:
        file_path: 文件路径

    Returns:
        dict: 文件信息，如果文件无效则返回 None
    """
    try:
        # 使用 ffprobe 获取文件信息
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)

        # 提取关键信息
        if 'streams' in info and len(info['streams']) > 0:
            stream = info['streams'][0]
            format_info = info.get('format', {})

            return {
                'valid': True,
                'codec': stream.get('codec_name'),
                'sample_rate': stream.get('sample_rate'),
                'channels': stream.get('channels'),
                'duration': float(format_info.get('duration', 0)),
                'size': int(format_info.get('size', 0)),
                'bit_rate': format_info.get('bit_rate')
            }
        else:
            return {'valid': False, 'error': '无法解析音频流'}

    except subprocess.CalledProcessError as e:
        return {'valid': False, 'error': f'ffprobe 错误: {e}'}
    except json.JSONDecodeError:
        return {'valid': False, 'error': 'JSON 解析失败'}
    except Exception as e:
        return {'valid': False, 'error': str(e)}


def convert_to_mp3(opus_file, output_file=None):
    """
    将 Opus 文件转换为 MP3

    Args:
        opus_file: 输入的 Opus 文件
        output_file: 输出的 MP3 文件（可选）

    Returns:
        bool: 是否转换成功
    """
    try:
        if output_file is None:
            output_file = opus_file.replace('.opus', '.mp3')

        cmd = [
            'ffmpeg',
            '-i', opus_file,
            '-codec:a', 'libmp3lame',
            '-qscale:a', '2',  # 高质量
            '-y',  # 覆盖已存在的文件
            output_file
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and os.path.exists(output_file):
            return True, output_file
        else:
            return False, result.stderr

    except Exception as e:
        return False, str(e)


def main():
    """主函数"""
    print("=" * 60)
    print("Opus 音频文件验证工具")
    print("=" * 60)
    print()

    # 检查 ffmpeg
    if not check_ffmpeg():
        print("❌ 未检测到 ffmpeg/ffprobe")
        print()
        print("请先安装 ffmpeg:")
        print("  Windows: 下载 https://ffmpeg.org/download.html")
        print("           或使用: winget install ffmpeg")
        print("  macOS:   brew install ffmpeg")
        print("  Linux:   sudo apt install ffmpeg")
        print()
        sys.exit(1)

    print("✅ ffmpeg/ffprobe 已安装")
    print()

    # 获取所有 opus 文件
    audio_dir = Path("received_audio")
    if not audio_dir.exists():
        print(f"❌ 目录不存在: {audio_dir}")
        sys.exit(1)

    opus_files = list(audio_dir.glob("*.opus"))

    if not opus_files:
        print(f"⚠️  未找到 .opus 文件在: {audio_dir}")
        sys.exit(0)

    print(f"📁 找到 {len(opus_files)} 个 Opus 文件")
    print()

    # 检查是否需要转换
    convert = '--convert' in sys.argv or '-c' in sys.argv

    # 验证每个文件
    valid_count = 0
    invalid_count = 0
    converted_count = 0

    for i, file_path in enumerate(sorted(opus_files), 1):
        print(f"[{i}/{len(opus_files)}] {file_path.name}")

        # 验证文件
        info = verify_opus_file(str(file_path))

        if info['valid']:
            valid_count += 1
            print(f"  ✅ 有效的 Opus 文件")
            print(f"  编解码器: {info['codec']}")
            print(f"  采样率: {info['sample_rate']} Hz")
            print(f"  声道数: {info['channels']}")
            print(f"  时长: {info['duration']:.2f} 秒")
            print(f"  大小: {info['size']} 字节 ({info['size']/1024:.2f} KB)")
            if info['bit_rate']:
                print(f"  比特率: {int(info['bit_rate'])/1000:.1f} kbps")

            # 转换为 MP3
            if convert:
                print(f"  🔄 转换为 MP3...")
                success, result = convert_to_mp3(str(file_path))
                if success:
                    print(f"  ✅ 已转换: {result}")
                    converted_count += 1
                else:
                    print(f"  ❌ 转换失败: {result}")
        else:
            invalid_count += 1
            print(f"  ❌ 无效文件: {info.get('error', '未知错误')}")

        print()

    # 统计
    print("=" * 60)
    print("验证完成")
    print("=" * 60)
    print(f"总文件数: {len(opus_files)}")
    print(f"有效文件: {valid_count}")
    print(f"无效文件: {invalid_count}")
    if convert:
        print(f"已转换: {converted_count}")
    print()

    if not convert and valid_count > 0:
        print("💡 提示: 使用 'python verify_audio.py --convert' 转换为 MP3 格式")
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已中断")
        sys.exit(0)
