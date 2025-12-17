"""
模拟硬件设备的测试客户端
用于测试弹幕AI服务器的音频下发功能

运行方法:
    python test_device_client.py

功能:
    - 连接到弹幕服务器
    - 接收欢迎消息
    - 接收并保存音频数据
    - 可选：播放音频（需要安装 pygame）
"""

import asyncio
import websockets
import json
import sys
import os
import time
from datetime import datetime


class TestDeviceClient:
    """测试设备客户端"""

    def __init__(
        self,
        server_url: str = "ws://127.0.0.1:8001/danmaku/",
        device_id: str = "test_device_001",
        save_audio: bool = True,
        play_audio: bool = False
    ):
        """
        初始化测试客户端

        Args:
            server_url: 服务器地址
            device_id: 设备ID
            save_audio: 是否保存接收到的音频
            play_audio: 是否播放音频（需要安装pygame）
        """
        self.server_url = f"{server_url}?device-id={device_id}"
        self.device_id = device_id
        self.save_audio = save_audio
        self.play_audio = play_audio
        self.websocket = None
        self.running = False
        self.audio_count = 0
        self.sentence_count = 0  # 句子计数器

        # 音频缓存（用于合并同一句话的音频包）
        self.current_audio_buffer = []
        self.is_receiving_audio = False
        self.last_audio_time = None

        # 创建音频保存目录
        if self.save_audio:
            self.audio_dir = "received_audio"
            os.makedirs(self.audio_dir, exist_ok=True)

        # 初始化音频播放器
        if self.play_audio:
            try:
                import pygame
                # 尝试初始化音频设备，如果失败则禁用播放
                try:
                    pygame.mixer.init()
                    self.pygame = pygame
                    print("✅ 音频播放功能已启用")
                except pygame.error as e:
                    print(f"⚠️  音频设备初始化失败: {e}")
                    print("   原因可能是系统没有可用的音频输出设备")
                    print("   音频数据仍会保存到文件，只是无法实时播放")
                    self.play_audio = False
            except ImportError:
                print("⚠️  未安装 pygame，无法播放音频")
                print("   安装方法: pip install pygame")
                self.play_audio = False

    async def connect(self):
        """连接到服务器"""
        try:
            print(f"正在连接到服务器: {self.server_url}")
            self.websocket = await websockets.connect(
                self.server_url,
                ping_interval=20,
                ping_timeout=10
            )
            print(f"✅ 已连接到服务器")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

    async def start(self):
        """启动客户端"""
        self.running = True

        # 启动音频保存任务
        asyncio.create_task(self._audio_save_worker())

        while self.running:
            try:
                if await self.connect():
                    await self._listen()
            except websockets.exceptions.ConnectionClosed:
                print("⚠️  连接已关闭，5秒后重连...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"❌ 运行出错: {e}")
                await asyncio.sleep(5)

    async def _listen(self):
        """监听服务器消息"""
        try:
            async for message in self.websocket:
                await self._process_message(message)

        except websockets.exceptions.ConnectionClosed:
            print("连接已关闭")
            raise
        except Exception as e:
            print(f"监听消息时出错: {e}")
            raise

    async def _process_message(self, message):
        """
        处理接收到的消息

        Args:
            message: 服务器消息（可能是文本或二进制）
        """
        try:
            # 判断消息类型
            if isinstance(message, str):
                # 文本消息（JSON）
                await self._handle_text_message(message)
            elif isinstance(message, bytes):
                # 二进制消息（音频数据）
                await self._handle_audio_message(message)
            else:
                print(f"⚠️  未知消息类型: {type(message)}")

        except Exception as e:
            print(f"处理消息时出错: {e}")

    async def _handle_text_message(self, message: str):
        """
        处理文本消息

        Args:
            message: JSON文本消息
        """
        try:
            data = json.loads(message)
            msg_type = data.get('type', 'unknown')

            if msg_type == 'welcome':
                print(f"📩 收到欢迎消息:")
                print(f"   设备ID: {data.get('device_id')}")
                print(f"   消息: {data.get('message')}")
                print(f"   时间戳: {data.get('timestamp')}")
                print()
                print("🎧 等待接收音频数据...")
                print("   (在抖音直播间发送弹幕即可触发 AI 回复)")
                print()
            elif msg_type == 'tts':
                # TTS 状态消息
                state = data.get('state')
                text = data.get('text', '')

                if state == 'start':
                    print(f"🎤 TTS 开始")
                    self.is_receiving_audio = True
                    self.current_audio_buffer = []
                elif state == 'sentence_start':
                    print(f"📝 TTS 句子: {text}")
                elif state == 'stop':
                    print(f"🛑 TTS 结束")
                    # 保存当前缓冲的音频
                    await self._save_buffered_audio()
            else:
                print(f"📩 收到消息: {data}")

        except json.JSONDecodeError:
            print(f"📩 收到文本: {message}")

    async def _handle_audio_message(self, audio_data: bytes):
        """
        处理音频消息

        Args:
            audio_data: 音频二进制数据
        """
        try:
            self.audio_count += 1
            audio_size = len(audio_data)

            print(f"🔊 收到音频包 #{self.audio_count}: {audio_size} 字节 ({audio_size/1024:.2f} KB)")

            # 添加到缓冲区
            self.current_audio_buffer.append(audio_data)
            self.last_audio_time = time.time()

        except Exception as e:
            print(f"处理音频时出错: {e}")

    async def _audio_save_worker(self):
        """
        后台任务：定期检查音频缓冲区
        如果1秒内没有新数据，则认为句子结束，保存音频
        """
        while self.running:
            try:
                await asyncio.sleep(0.5)  # 每0.5秒检查一次

                if (
                    len(self.current_audio_buffer) > 0
                    and self.last_audio_time is not None
                    and time.time() - self.last_audio_time > 1.0  # 1秒内没有新数据
                ):
                    # 保存缓冲的音频
                    await self._save_buffered_audio()

            except Exception as e:
                print(f"音频保存任务出错: {e}")

    async def _save_buffered_audio(self):
        """
        保存缓冲的音频包（合并成一个文件）
        """
        if len(self.current_audio_buffer) == 0:
            return

        try:
            # 合并所有音频包
            merged_audio = b''.join(self.current_audio_buffer)
            total_size = len(merged_audio)
            packet_count = len(self.current_audio_buffer)

            self.sentence_count += 1

            print()
            print(f"💾 保存完整音频 (句子 #{self.sentence_count}):")
            print(f"   总大小: {total_size} 字节 ({total_size/1024:.2f} KB)")
            print(f"   音频包数: {packet_count}")

            # 调试：显示前16字节
            if len(merged_audio) >= 16:
                header_hex = ' '.join(f'{b:02x}' for b in merged_audio[:16])
                print(f"   前16字节(hex): {header_hex}")

            # 保存合并后的音频
            if self.save_audio:
                filename = self._save_audio(merged_audio, self.sentence_count)
                print(f"   已保存: {filename}")

                # 播放音频
                if self.play_audio:
                    self._play_audio(filename)

            print()

            # 清空缓冲区
            self.current_audio_buffer = []
            self.last_audio_time = None
            self.is_receiving_audio = False

        except Exception as e:
            print(f"保存缓冲音频时出错: {e}")

    def _save_audio(self, audio_data: bytes, sentence_num: int = None) -> str:
        """
        保存音频到文件

        Args:
            audio_data: 音频数据
            sentence_num: 句子编号（可选）

        Returns:
            保存的文件名
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 检测音频格式
        file_ext = self._detect_audio_format(audio_data)

        if sentence_num is not None:
            filename = os.path.join(
                self.audio_dir,
                f"sentence_{sentence_num}_{timestamp}.{file_ext}"
            )
        else:
            filename = os.path.join(
                self.audio_dir,
                f"audio_{timestamp}_{self.audio_count}.{file_ext}"
            )

        with open(filename, 'wb') as f:
            f.write(audio_data)

        return filename

    def _detect_audio_format(self, data: bytes) -> str:
        """
        检测音频数据格式

        Args:
            data: 音频数据

        Returns:
            文件扩展名
        """
        if len(data) < 4:
            return "bin"

        # MP3 格式检测
        if data[:3] == b'ID3' or data[0:2] == b'\xff\xfb' or data[0:2] == b'\xff\xf3':
            return "mp3"

        # Ogg/Opus 格式检测（带容器）
        if data[:4] == b'OggS':
            return "opus"

        # WAV 格式检测
        if data[:4] == b'RIFF' and len(data) >= 12 and data[8:12] == b'WAVE':
            return "wav"

        # 原始 Opus 包（无容器）- xiaozhi-server 的标准格式
        # Opus 包通常以特定字节开头，但没有固定的文件头
        # 如果都不匹配，很可能是原始 Opus 编码数据
        # 保存为 .opus.raw 供硬件设备使用
        return "opus.raw"

    def _play_audio(self, filename: str):
        """
        播放音频文件

        Args:
            filename: 音频文件路径
        """
        try:
            # 注意：pygame 可能不支持 opus 格式
            # 需要转换为 mp3 或 wav 格式
            print(f"   ▶️  播放音频（需要支持的格式）")
            # self.pygame.mixer.music.load(filename)
            # self.pygame.mixer.music.play()
        except Exception as e:
            print(f"   播放失败: {e}")

    async def stop(self):
        """停止客户端"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
        print("客户端已停止")


async def main():
    """主函数"""
    print("=" * 60)
    print("弹幕AI服务器 - 硬件设备模拟客户端")
    print("=" * 60)
    print()

    # 配置参数
    server_url = "ws://127.0.0.1:8001/danmaku/"
    device_id = "test_device_001"

    # 创建客户端
    client = TestDeviceClient(
        server_url=server_url,
        device_id=device_id,
        save_audio=True,   # 保存音频
        play_audio=False   # 不播放音频（可选）
    )

    print(f"设备ID: {device_id}")
    print(f"服务器: {server_url}")
    print()

    try:
        await client.start()
    except KeyboardInterrupt:
        print("\n收到中断信号，正在停止...")
        await client.stop()
    except Exception as e:
        print(f"运行出错: {e}")
        await client.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已终止")
