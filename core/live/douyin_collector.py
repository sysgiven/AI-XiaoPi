"""
抖音直播弹幕采集器
使用WebSocket连接抖音直播间，实时获取弹幕消息
"""

import asyncio
import json
import logging
from typing import Callable, Optional
import websockets
import ssl


class DouyinDanmakuCollector:
    """抖音直播弹幕采集器"""

    def __init__(self, room_id: str, on_message_callback: Callable, logger=None):
        """
        初始化弹幕采集器

        Args:
            room_id: 抖音直播间ID
            on_message_callback: 收到弹幕消息时的回调函数
            logger: 日志记录器
        """
        self.room_id = room_id
        self.on_message_callback = on_message_callback
        self.logger = logger or logging.getLogger(__name__)
        self.websocket = None
        self.running = False
        self.reconnect_delay = 5  # 重连延迟(秒)
        self.max_reconnect_attempts = 10  # 最大重连次数

    async def connect(self):
        """连接到抖音直播间WebSocket"""
        try:
            # 注意：这里需要根据实际的抖音直播WebSocket协议进行调整
            # 以下是示例代码，实际使用时需要替换为真实的WebSocket地址
            ws_url = f"wss://webcast.amemv.com/webcast/im/push/v2/?room_id={self.room_id}"

            # 创建SSL上下文（如果需要）
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            self.websocket = await websockets.connect(
                ws_url,
                ssl=ssl_context,
                ping_interval=20,
                ping_timeout=10
            )

            self.logger.debug(f"成功连接到抖音直播间: {self.room_id}")
            return True

        except Exception as e:
            self.logger.error(f"连接抖音直播间失败: {e}")
            return False

    async def start(self):
        """启动弹幕采集"""
        self.running = True
        reconnect_count = 0

        while self.running and reconnect_count < self.max_reconnect_attempts:
            try:
                if await self.connect():
                    reconnect_count = 0  # 连接成功，重置重连计数
                    await self._listen()
                else:
                    reconnect_count += 1
                    self.logger.warning(f"连接失败，{self.reconnect_delay}秒后重试 ({reconnect_count}/{self.max_reconnect_attempts})")
                    await asyncio.sleep(self.reconnect_delay)

            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("连接已关闭，准备重连...")
                reconnect_count += 1
                await asyncio.sleep(self.reconnect_delay)

            except Exception as e:
                self.logger.error(f"弹幕采集出错: {e}")
                reconnect_count += 1
                await asyncio.sleep(self.reconnect_delay)

        if reconnect_count >= self.max_reconnect_attempts:
            self.logger.error("达到最大重连次数，停止采集")

    async def _listen(self):
        """监听WebSocket消息"""
        try:
            async for message in self.websocket:
                if not self.running:
                    break

                await self._process_message(message)

        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket连接已关闭")
            raise
        except Exception as e:
            self.logger.error(f"监听消息时出错: {e}")
            raise

    async def _process_message(self, message):
        """
        处理收到的消息

        这里需要根据抖音直播间的实际协议格式进行解析
        以下是示例代码
        """
        try:
            # 解析消息
            if isinstance(message, bytes):
                # 如果是二进制消息，需要解码
                message = message.decode('utf-8', errors='ignore')

            # 尝试解析为JSON
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                # 如果不是JSON格式，直接作为文本处理
                data = {"type": "text", "content": message}

            # 提取弹幕内容
            danmaku_info = self._extract_danmaku_info(data)

            if danmaku_info:
                # 调用回调函数
                await self.on_message_callback(danmaku_info)

        except Exception as e:
            self.logger.error(f"处理消息时出错: {e}")

    def _extract_danmaku_info(self, data: dict) -> Optional[dict]:
        """
        从消息数据中提取弹幕信息

        Args:
            data: 消息数据

        Returns:
            弹幕信息字典，包含username和content字段
        """
        try:
            # 根据实际的抖音协议调整这里的字段
            # 以下是示例结构
            if data.get('type') == 'chat':
                return {
                    'username': data.get('user', {}).get('nickname', '匿名用户'),
                    'content': data.get('content', ''),
                    'timestamp': data.get('timestamp', 0)
                }
            elif data.get('type') == 'text':
                # 简单文本消息
                return {
                    'username': '观众',
                    'content': data.get('content', ''),
                    'timestamp': 0
                }
            return None

        except Exception as e:
            self.logger.error(f"提取弹幕信息时出错: {e}")
            return None

    async def stop(self):
        """停止弹幕采集"""
        self.running = False
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                self.logger.error(f"关闭WebSocket时出错: {e}")


class MockDouyinDanmakuCollector:
    """
    模拟抖音弹幕采集器（用于测试）

    由于实际接入抖音直播需要逆向工程和认证，
    这里提供一个模拟版本用于测试和演示
    """

    def __init__(self, room_id: str, on_message_callback: Callable, logger=None):
        self.room_id = room_id
        self.on_message_callback = on_message_callback
        self.logger = logger or logging.getLogger(__name__)
        self.running = False

        # 模拟弹幕数据
        self.mock_messages = [
            {"username": "用户A", "content": "你好小智"},
            {"username": "用户B", "content": "今天天气怎么样"},
            {"username": "用户C", "content": "给我讲个笑话"},
            {"username": "用户D", "content": "介绍一下你自己"},
            {"username": "用户E", "content": "播放一首歌"},
        ]
        self.current_index = 0

    async def start(self):
        """启动模拟弹幕采集"""
        self.running = True
        self.logger.debug(f"启动模拟弹幕采集器 - 直播间ID: {self.room_id}")

        while self.running:
            # 每10秒发送一条模拟弹幕
            await asyncio.sleep(10)

            if not self.running:
                break

            # 循环发送模拟弹幕
            message = self.mock_messages[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.mock_messages)

            self.logger.debug(f"模拟弹幕: {message['username']}: {message['content']}")
            await self.on_message_callback(message)

    async def stop(self):
        """停止模拟采集"""
        self.running = False
        self.logger.debug("停止模拟弹幕采集器")
