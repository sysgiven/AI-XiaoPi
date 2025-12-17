"""
测试 EdgeTTS 输出格式
"""

import asyncio
import edge_tts

async def test_edge_tts():
    """测试 EdgeTTS 生成的音频格式"""

    text = "你好，这是一个测试"
    voice = "zh-CN-XiaoxiaoNeural"

    print("正在生成音频...")

    # 创建 Communicate 对象
    communicate = edge_tts.Communicate(text, voice=voice)

    # 收集音频数据
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]

    print(f"✅ 音频生成完成")
    print(f"总大小: {len(audio_data)} 字节 ({len(audio_data)/1024:.2f} KB)")

    # 检查文件头
    if len(audio_data) >= 16:
        header_hex = ' '.join(f'{b:02x}' for b in audio_data[:16])
        print(f"前16字节(hex): {header_hex}")

        # 判断格式
        if audio_data[:3] == b'ID3':
            print("✅ 格式: MP3 (ID3 标签)")
        elif audio_data[0:2] == b'\xff\xfb' or audio_data[0:2] == b'\xff\xf3':
            print("✅ 格式: MP3 (MPEG 帧)")
        elif audio_data[:4] == b'RIFF':
            print("格式: WAV")
        elif audio_data[:4] == b'OggS':
            print("格式: Ogg")
        else:
            print("❌ 格式: 未知")

    # 保存到文件
    output_file = "test_edge_output.bin"
    with open(output_file, 'wb') as f:
        f.write(audio_data)

    print(f"已保存到: {output_file}")
    print()
    print("请使用以下命令检查文件:")
    print(f"  ffprobe {output_file}")
    print()

if __name__ == "__main__":
    asyncio.run(test_edge_tts())
