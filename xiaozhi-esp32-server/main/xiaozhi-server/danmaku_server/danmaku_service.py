"""
弹幕服务主模块
整合弹幕采集、消息处理和设备管理
"""

import asyncio
import websockets
from typing import Dict, Any
from urllib.parse import parse_qs, urlparse
from aiohttp import web

from config.logger import setup_logging
from config.settings import load_config
from core.utils.modules_initialize import initialize_modules
from danmaku_server.douyin_collector import DouyinDanmakuCollector, MockDouyinDanmakuCollector
from danmaku_server.douyin_proxy_collector import DouyinProxyCollector
from danmaku_server.danmaku_handler import DanmakuHandler, DanmakuConnection
from danmaku_server.device_manager import DeviceManager
from danmaku_server.danmaku_ota_handler import DanmakuOTAHandler


TAG = __name__


class DanmakuService:
    """弹幕服务"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化弹幕服务

        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = setup_logging()

        # 获取弹幕配置
        self.danmaku_config = config.get("danmaku", {})
        self.room_id = self.danmaku_config.get("room_id", "test_room")
        self.use_mock = self.danmaku_config.get("use_mock", True)  # 是否使用模拟数据
        self.use_proxy = self.danmaku_config.get("use_proxy", False)  # 是否使用 DouyinBarrageGrab 代理
        self.proxy_ws_url = self.danmaku_config.get("proxy_ws_url", "ws://127.0.0.1:8888")  # DouyinBarrageGrab 地址

        # WebSocket服务器配置
        self.ws_host = self.danmaku_config.get("ws_host", "0.0.0.0")
        self.ws_port = self.danmaku_config.get("ws_port", 8001)

        # HTTP服务器配置（用于OTA接口）
        self.http_host = self.danmaku_config.get("http_host", "0.0.0.0")
        self.http_port = self.danmaku_config.get("http_port", 8003)

        # 初始化组件
        self.device_manager = None
        self.danmaku_handler = None
        self.danmaku_collector = None
        self.llm = None
        self.tts = None
        self.ota_handler = None

        # 服务器
        self.ws_server = None
        self.http_server = None

    async def initialize(self):
        """初始化服务组件"""
        try:
            self.logger.info("初始化弹幕服务组件...")

            # 初始化LLM、TTS等模块
            modules = initialize_modules(
                self.logger,
                self.config,
                False,  # VAD
                False,  # ASR
                True,   # LLM
                True,   # TTS
                False,  # Memory
                False,  # Intent
            )

            self.llm = modules.get("llm")
            self.tts = modules.get("tts")

            if not self.llm:
                raise RuntimeError("LLM初始化失败")
            if not self.tts:
                raise RuntimeError("TTS初始化失败")

            # 初始化设备管理器
            self.device_manager = DeviceManager(logger=self.logger)

            # 初始化弹幕处理器
            self.danmaku_handler = DanmakuHandler(
                config=self.config,
                llm=self.llm,
                tts=self.tts,
                device_manager=self.device_manager,
                logger=self.logger
            )

            # 打开TTS音频通道（使用模拟连接）
            mock_connection = DanmakuConnection(self.device_manager, self.logger, self.config)
            mock_connection.set_tts(self.tts)  # 设置 TTS 实例

            # 调试：确认音频格式设置
            self.logger.debug(f"✅ DanmakuConnection 音频格式: {mock_connection.audio_format}")

            await self.tts.open_audio_channels(mock_connection)

            # 初始化弹幕采集器
            if self.use_mock:
                self.logger.debug("使用模拟弹幕采集器")
                self.danmaku_collector = MockDouyinDanmakuCollector(
                    room_id=self.room_id,
                    on_message_callback=self._on_danmaku_message,
                    logger=self.logger
                )
            elif self.use_proxy:
                self.logger.info("使用 DouyinBarrageGrab 代理采集器")
                self.logger.debug(f"代理地址: {self.proxy_ws_url}")
                self.danmaku_collector = DouyinProxyCollector(
                    on_message_callback=self._on_danmaku_message,
                    ws_url=self.proxy_ws_url,
                    logger=self.logger
                )
            else:
                self.logger.info("使用真实抖音弹幕采集器（需要自行实现协议）")
                self.danmaku_collector = DouyinDanmakuCollector(
                    room_id=self.room_id,
                    on_message_callback=self._on_danmaku_message,
                    logger=self.logger
                )

            # 初始化OTA处理器（用于ESP32硬件连接验证）
            self.ota_handler = DanmakuOTAHandler(config=self.config)

            self.logger.info("弹幕服务组件初始化完成")

        except Exception as e:
            self.logger.error(f"初始化弹幕服务失败: {e}")
            raise

    async def _on_danmaku_message(self, danmaku: dict):
        """
        弹幕消息回调

        Args:
            danmaku: 弹幕信息
        """
        # 将弹幕添加到处理队列
        await self.danmaku_handler.add_danmaku(danmaku)

    async def start(self):
        """启动弹幕服务"""
        try:
            self.logger.info("启动弹幕服务...")

            # 初始化组件
            await self.initialize()

            # 启动WebSocket服务器（用于设备连接）
            asyncio.create_task(self._start_websocket_server())

            # 启动HTTP服务器（用于OTA接口）
            asyncio.create_task(self._start_http_server())

            # 启动弹幕处理器
            asyncio.create_task(self.danmaku_handler.start())

            # 启动弹幕采集器
            asyncio.create_task(self.danmaku_collector.start())

            # 定期清理断开的设备
            asyncio.create_task(self._periodic_cleanup())

            self.logger.info("弹幕服务启动成功")
            self.logger.info(f"WebSocket地址: ws://{self.ws_host}:{self.ws_port}/danmaku/")
            self.logger.info(f"HTTP OTA接口: http://{self.http_host}:{self.http_port}/xiaozhi/ota/")
            self.logger.debug(f"直播间ID: {self.room_id}")
            self.logger.debug(f"模拟模式: {self.use_mock}")
            self.logger.debug(f"代理模式: {self.use_proxy}")
            if self.use_proxy:
                self.logger.debug(f"DouyinBarrageGrab 地址: {self.proxy_ws_url}")

            # 保持服务运行
            await asyncio.Future()

        except Exception as e:
            self.logger.error(f"启动弹幕服务失败: {e}")
            raise

    async def _start_websocket_server(self):
        """启动WebSocket服务器"""
        try:
            self.logger.debug(f"正在启动WebSocket服务器: {self.ws_host}:{self.ws_port}")

            # 创建WebSocket服务器（配置ping/pong心跳以保持连接）
            server = await websockets.serve(
                self._handle_device_connection,
                self.ws_host,
                self.ws_port,
                ping_interval=20,  # 每20秒发送ping
                ping_timeout=10,   # 等待pong响应10秒
                close_timeout=5    # 关闭连接时等待5秒
            )

            self.logger.info(f"✅ WebSocket服务器已启动: ws://{self.ws_host}:{self.ws_port}/danmaku/")

            # 保持服务器运行
            await asyncio.Future()

        except Exception as e:
            self.logger.error(f"❌ 启动WebSocket服务器失败: {e}", exc_info=True)
            raise

    async def _handle_device_connection(self, websocket):
        """
        处理设备WebSocket连接

        Args:
            websocket: WebSocket连接
        """
        device_id = None

        try:
            # 从请求头或URL参数获取device_id
            headers = dict(websocket.request.headers)
            device_id = headers.get("device-id")

            if not device_id:
                # 尝试从URL路径获取
                # websocket.request.path 包含完整路径，如 "/danmaku/?device-id=xxx"
                path = websocket.request.path
                parsed_url = urlparse(path)
                query_params = parse_qs(parsed_url.query)
                if "device-id" in query_params:
                    device_id = query_params["device-id"][0]

            if not device_id:
                self.logger.warning("设备连接缺少device-id")
                await websocket.send("缺少device-id参数")
                await websocket.close()
                return

            # 获取客户端IP
            client_ip = websocket.remote_address[0]

            # 添加到设备管理器
            await self.device_manager.add_device(device_id, websocket, client_ip)

            # 发送标准的 hello 响应消息（与硬件协议兼容）
            import json
            hello_response = {
                "type": "hello",
                "version": 1,
                "transport": "websocket",
                "session_id": device_id,  # 使用 device_id 作为 session_id
                "audio_params": {
                    "format": "opus",
                    "sample_rate": 16000,
                    "channels": 1,
                    "frame_duration": 60
                }
            }
            await websocket.send(json.dumps(hello_response, ensure_ascii=False))
            self.logger.info(f"✅ 已发送 hello 响应给设备: {device_id}")

            # 保持连接
            async for message in websocket:
                # 这里可以处理设备发来的消息（如果需要）
                self.logger.debug(f"收到设备消息: {device_id}: {message}")

        except websockets.exceptions.ConnectionClosed:
            self.logger.debug(f"设备断开连接: {device_id}")

        except Exception as e:
            self.logger.error(f"处理设备连接时出错: {e}")

        finally:
            # 移除设备
            if device_id:
                await self.device_manager.remove_device(device_id)

    async def _start_http_server(self):
        """启动HTTP服务器（用于OTA接口）"""
        try:
            self.logger.debug(f"正在启动HTTP服务器: {self.http_host}:{self.http_port}")

            # 创建HTTP应用
            app = web.Application()

            # 添加OTA路由
            app.add_routes([
                web.get("/xiaozhi/ota/", self.ota_handler.handle_get),
                web.post("/xiaozhi/ota/", self.ota_handler.handle_post),
                web.options("/xiaozhi/ota/", self.ota_handler.handle_options),
            ])

            # 启动HTTP服务器
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, self.http_host, self.http_port)
            await site.start()

            self.logger.info(f"✅ HTTP服务器已启动: http://{self.http_host}:{self.http_port}/xiaozhi/ota/")

            # 保持服务器运行
            await asyncio.Future()

        except Exception as e:
            self.logger.error(f"❌ 启动HTTP服务器失败: {e}", exc_info=True)
            raise

    async def _periodic_cleanup(self):
        """定期清理断开的设备"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟清理一次
                await self.device_manager.cleanup_disconnected_devices()
            except Exception as e:
                self.logger.error(f"清理设备时出错: {e}")

    async def stop(self):
        """停止弹幕服务"""
        try:
            self.logger.info("停止弹幕服务...")

            # 停止弹幕采集器
            if self.danmaku_collector:
                await self.danmaku_collector.stop()

            # 停止弹幕处理器
            if self.danmaku_handler:
                await self.danmaku_handler.stop()

            self.logger.info("弹幕服务已停止")

        except Exception as e:
            self.logger.error(f"停止弹幕服务时出错: {e}")
