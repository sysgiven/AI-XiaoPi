"""
弹幕服务器OTA处理器
用于ESP32硬件的OTA验证和WebSocket配置下发
"""

import json
import time
from aiohttp import web
from config.logger import setup_logging
from core.utils.util import get_local_ip

TAG = __name__


class DanmakuOTAHandler:
    """弹幕服务器专用OTA处理器"""

    def __init__(self, config: dict):
        """
        初始化OTA处理器

        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = setup_logging()

        # 弹幕配置
        self.danmaku_config = config.get("danmaku", {})
        self.ws_port = self.danmaku_config.get("ws_port", 8001)

        # HTTP服务器配置
        server_config = config.get("server", {})
        self.timezone_offset = server_config.get("timezone_offset", 8)

    def _add_cors_headers(self, response: web.Response):
        """添加CORS头部"""
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, device-id, client-id"

    async def handle_get(self, request):
        """
        处理OTA GET请求（测试接口）

        Args:
            request: aiohttp请求对象
        """
        try:
            local_ip = get_local_ip()
            websocket_url = f"ws://{local_ip}:{self.ws_port}/danmaku/"
            message = f"弹幕服务器OTA接口运行正常\nWebSocket地址: {websocket_url}\n请在连接时添加 device-id 参数"
            response = web.Response(text=message, content_type="text/plain")
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"OTA GET请求异常: {e}")
            response = web.Response(text="OTA接口异常", content_type="text/plain")
        finally:
            self._add_cors_headers(response)
            return response

    async def handle_post(self, request):
        """
        处理OTA POST请求（ESP32硬件验证）

        ESP32会发送包含设备信息的POST请求，服务器返回：
        - 服务器时间和时区
        - 固件版本信息（可选）
        - WebSocket连接地址

        Args:
            request: aiohttp请求对象
        """
        try:
            # 获取请求数据
            data = await request.text()
            self.logger.bind(tag=TAG).debug(f"OTA请求方法: {request.method}")
            self.logger.bind(tag=TAG).debug(f"OTA请求头: {request.headers}")
            self.logger.bind(tag=TAG).debug(f"OTA请求数据: {data}")

            # 提取设备ID
            device_id = request.headers.get("device-id", "")
            if not device_id:
                self.logger.bind(tag=TAG).warning("OTA请求缺少device-id")
                raise ValueError("缺少device-id")

            self.logger.bind(tag=TAG).info(f"✅ OTA请求 - 设备ID: {device_id}")

            # 提取ClientID（可选）
            client_id = request.headers.get("client-id", "")
            if client_id:
                self.logger.bind(tag=TAG).info(f"   ClientID: {client_id}")

            # 解析请求数据
            try:
                data_json = json.loads(data) if data else {}
            except json.JSONDecodeError:
                self.logger.bind(tag=TAG).warning(f"无法解析OTA请求数据: {data}")
                data_json = {}

            # 获取本机IP
            local_ip = get_local_ip()

            # 构建响应数据
            return_json = {
                # 服务器时间信息
                "server_time": {
                    "timestamp": int(round(time.time() * 1000)),  # 毫秒时间戳
                    "timezone_offset": self.timezone_offset * 60,  # 分钟偏移
                },
                # 固件信息（使用客户端当前版本，表示无需更新）
                "firmware": {
                    "version": data_json.get("application", {}).get("version", "1.0.0"),
                    "url": "",  # 空URL表示无需更新
                },
                # WebSocket配置
                "websocket": {
                    "url": f"ws://{local_ip}:{self.ws_port}/danmaku/?device-id={device_id}",
                    "token": "",  # 弹幕服务器暂不需要token认证
                }
            }

            self.logger.bind(tag=TAG).info(f"📡 下发WebSocket配置: ws://{local_ip}:{self.ws_port}/danmaku/?device-id={device_id}")

            # 返回JSON响应
            response = web.Response(
                text=json.dumps(return_json, separators=(",", ":")),
                content_type="application/json"
            )

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"❌ OTA请求处理失败: {e}", exc_info=True)
            return_json = {
                "success": False,
                "message": f"OTA请求处理失败: {str(e)}"
            }
            response = web.Response(
                text=json.dumps(return_json, separators=(",", ":")),
                content_type="application/json",
                status=400
            )

        finally:
            self._add_cors_headers(response)
            return response

    async def handle_options(self, request):
        """
        处理OPTIONS请求（CORS预检）

        Args:
            request: aiohttp请求对象
        """
        response = web.Response(text="", status=200)
        self._add_cors_headers(response)
        return response
