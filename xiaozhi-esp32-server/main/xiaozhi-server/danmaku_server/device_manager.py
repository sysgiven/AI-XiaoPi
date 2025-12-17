"""
设备管理器
管理所有连接的硬件设备，支持音频广播功能
"""

import asyncio
import json
from typing import Dict, Set
from dataclasses import dataclass
from datetime import datetime
import websockets


@dataclass
class DeviceInfo:
    """设备信息"""
    device_id: str
    websocket: websockets.WebSocketServerProtocol
    connected_at: datetime
    client_ip: str


class DeviceManager:
    """设备管理器"""

    def __init__(self, logger=None):
        """
        初始化设备管理器

        Args:
            logger: 日志记录器
        """
        self.logger = logger
        self.devices: Dict[str, DeviceInfo] = {}  # device_id -> DeviceInfo
        self.device_lock = asyncio.Lock()

    async def add_device(self, device_id: str, websocket: websockets.WebSocketServerProtocol, client_ip: str):
        """
        添加设备

        Args:
            device_id: 设备ID
            websocket: WebSocket连接
            client_ip: 客户端IP
        """
        async with self.device_lock:
            device_info = DeviceInfo(
                device_id=device_id,
                websocket=websocket,
                connected_at=datetime.now(),
                client_ip=client_ip
            )
            self.devices[device_id] = device_info
            self.logger.debug(f"设备已连接: {device_id} ({client_ip}), 当前设备数: {len(self.devices)}")

    async def remove_device(self, device_id: str):
        """
        移除设备

        Args:
            device_id: 设备ID
        """
        async with self.device_lock:
            if device_id in self.devices:
                device_info = self.devices.pop(device_id)
                self.logger.debug(f"设备已断开: {device_id}, 剩余设备数: {len(self.devices)}")
                try:
                    await device_info.websocket.close()
                except Exception as e:
                    self.logger.error(f"关闭设备连接时出错: {e}")

    async def broadcast_audio(self, audio_data: bytes, exclude_devices: Set[str] = None):
        """
        向所有设备广播音频数据

        Args:
            audio_data: 音频数据
            exclude_devices: 需要排除的设备ID集合
        """
        if exclude_devices is None:
            exclude_devices = set()

        async with self.device_lock:
            # 获取需要发送的设备列表
            target_devices = [
                device_info for device_id, device_info in self.devices.items()
                if device_id not in exclude_devices
            ]

        if not target_devices:
            self.logger.warning(f"⚠️  没有可用的设备接收广播（当前设备数: {len(self.devices)}）")
            return

        self.logger.debug(f"准备广播音频: {len(audio_data)} 字节 → {len(target_devices)} 个设备")

        # 并发发送给所有设备
        tasks = []
        for device_info in target_devices:
            task = self._send_to_device(device_info, audio_data)
            tasks.append(task)

        # 等待所有发送完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 统计发送结果
        success_count = sum(1 for r in results if r is True)
        failed_count = len(results) - success_count

        if failed_count > 0:
            self.logger.warning(f"音频广播完成: 成功 {success_count}, 失败 {failed_count}")
        else:
            self.logger.debug(f"音频广播完成: 成功 {success_count}")

    async def _send_to_device(self, device_info: DeviceInfo, data: bytes) -> bool:
        """
        发送数据到单个设备

        Args:
            device_info: 设备信息
            data: 要发送的数据

        Returns:
            是否发送成功
        """
        try:
            await device_info.websocket.send(data)
            return True
        except websockets.exceptions.ConnectionClosed as e:
            self.logger.warning(f"❌ 设备连接已关闭: {device_info.device_id}, 原因: {e}")
            # 标记设备为待移除（在下次清理时移除）
            asyncio.create_task(self.remove_device(device_info.device_id))
            return False
        except Exception as e:
            self.logger.error(f"❌ 发送数据到设备 {device_info.device_id} 时出错: {e}")
            return False

    async def broadcast_message(self, message: dict, exclude_devices: Set[str] = None):
        """
        向所有设备广播JSON消息

        Args:
            message: 消息字典
            exclude_devices: 需要排除的设备ID集合
        """
        try:
            message_json = json.dumps(message, ensure_ascii=False)
            message_bytes = message_json.encode('utf-8')
            await self.broadcast_audio(message_bytes, exclude_devices)
        except Exception as e:
            self.logger.error(f"广播消息时出错: {e}")

    def get_device_count(self) -> int:
        """获取当前连接的设备数量"""
        return len(self.devices)

    def get_device_list(self) -> list:
        """获取设备列表"""
        return [
            {
                "device_id": device_id,
                "client_ip": device_info.client_ip,
                "connected_at": device_info.connected_at.isoformat()
            }
            for device_id, device_info in self.devices.items()
        ]

    async def cleanup_disconnected_devices(self):
        """清理断开连接的设备"""
        async with self.device_lock:
            disconnected_devices = []

            for device_id, device_info in self.devices.items():
                try:
                    # 检查连接状态 - websockets 库的正确方法
                    # ServerConnection 对象使用 state 属性，而不是 closed
                    ws = device_info.websocket

                    # 检查是否已关闭：closed 为 True 或 state 为 CLOSED
                    is_closed = False
                    if hasattr(ws, 'closed'):
                        is_closed = ws.closed
                    elif hasattr(ws, 'state'):
                        # websockets.protocol.State.CLOSED 的值
                        from websockets.protocol import State
                        is_closed = ws.state == State.CLOSED

                    if is_closed:
                        # 尝试获取关闭信息
                        close_code = getattr(ws, 'close_code', None)
                        close_reason = getattr(ws, 'close_reason', None)
                        self.logger.warning(
                            f"检测到设备 {device_id} 的 WebSocket 已关闭，"
                            f"关闭代码: {close_code}, "
                            f"关闭原因: {close_reason}"
                        )
                        disconnected_devices.append(device_id)
                except Exception as e:
                    self.logger.error(f"检查设备 {device_id} 连接状态时出错: {e}")
                    # 不要因为检查出错就移除设备，可能只是属性访问问题
                    # disconnected_devices.append(device_id)

            # 移除断开的设备
            for device_id in disconnected_devices:
                self.devices.pop(device_id, None)
                self.logger.debug(f"清理断开的设备: {device_id}")

            if disconnected_devices:
                self.logger.info(f"清理完成，移除 {len(disconnected_devices)} 个设备")
