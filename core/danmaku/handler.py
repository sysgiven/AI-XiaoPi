"""
弹幕消息处理器
接收弹幕消息，调用LLM生成回复，调用TTS合成语音，广播给所有设备
"""

import asyncio
import uuid
import queue
import threading
import re
from typing import Dict, Any
from datetime import datetime

from core.utils.dialogue import Message, Dialogue
from core.providers.tts.dto.dto import ContentType, TTSMessageDTO, SentenceType
from core.utils import textUtils
from core.utils.audioRateController import AudioRateController

TAG = __name__

# 全局表情符号正则模式（用于移除表情）
# 使用更保守的范围，避免误匹配中文等其他字符
EMOJI_PATTERN = re.compile(
    "["
    "\u2600-\u26FF"      # Miscellaneous Symbols
    "\u2700-\u27BF"      # Dingbats
    "\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F680-\U0001F6FF"  # Transport and Map Symbols
    "\U0001F700-\U0001F77F"  # Alchemical Symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "\U0001F1E0-\U0001F1FF"  # Flags
    "]+",
    flags=re.UNICODE
)


def remove_emojis(text: str) -> str:
    """
    移除文本中的所有表情符号，保留文字内容

    Args:
        text: 原始文本

    Returns:
        移除表情后的文本
    """
    if not text:
        return text

    # 第一步：移除表情符号主体
    result = EMOJI_PATTERN.sub('', text)

    # 第二步：移除孤立的变体选择器和零宽连接符
    # 这些字符通常与表情一起使用，单独出现时也应该移除
    result = re.sub(r'[\uFE00-\uFE0F\u200D]', '', result)

    return result.strip()


def is_pure_emoji_or_empty(text: str) -> bool:
    """
    检查文本是否为纯表情符号或空文本

    Args:
        text: 待检查的文本

    Returns:
        True if text is empty or contains only emojis, False otherwise
    """
    if not text or not text.strip():
        return True

    # 移除所有表情符号
    text_without_emoji = remove_emojis(text)

    # 如果移除表情后为空，说明是纯表情
    return len(text_without_emoji) == 0


class DanmakuHandler:
    """弹幕消息处理器"""

    def __init__(
        self,
        config: Dict[str, Any],
        llm,
        tts,
        device_manager,
        logger=None
    ):
        """
        初始化弹幕处理器

        Args:
            config: 配置字典
            llm: 大语言模型实例
            tts: 语音合成实例
            device_manager: 设备管理器实例
            logger: 日志记录器
        """
        self.config = config
        self.llm = llm
        self.tts = tts
        self.device_manager = device_manager
        self.logger = logger

        # 对话管理
        self.dialogue = Dialogue()
        self.session_id = str(uuid.uuid4())

        # 系统提示词
        prompt = self.config.get("prompt", "你是一个友好的AI助手")
        self.dialogue.update_system_message(prompt)

        # 处理队列
        self.message_queue = asyncio.Queue()
        self.processing = False

        # 音频发送相关
        self.audio_send_lock = asyncio.Lock()

        # 弹幕流控配置
        danmaku_config = self.config.get("danmaku", {})
        self.flow_control_enabled = danmaku_config.get("flow_control_enabled", True)  # 是否启用流控
        self.flow_control_strategy = danmaku_config.get("flow_control_strategy", "skip")  # skip 或 queue_limit
        self.max_queue_size = danmaku_config.get("max_queue_size", 1)  # 队列最大长度

        # 当前处理状态
        self.is_speaking = False  # 是否正在处理弹幕和播放音频
        self.current_processing_danmaku = None  # 当前正在处理的弹幕

        self.logger.info("弹幕消息处理器初始化完成")
        if self.flow_control_enabled:
            self.logger.info(f"弹幕流控已启用，策略: {self.flow_control_strategy}, 队列大小: {self.max_queue_size}")

    async def start(self):
        """启动消息处理（串行化模式）"""
        self.processing = True
        self.logger.info("启动弹幕消息处理（串行模式）")

        # 串行化处理弹幕：一次只处理一条，等待音频播放完成后再处理下一条
        while self.processing:
            try:
                # 清空队列中的旧弹幕，只保留最新的
                latest_danmaku = None
                while True:
                    try:
                        latest_danmaku = self.message_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break

                # 如果没有弹幕，等待新弹幕
                if latest_danmaku is None:
                    try:
                        latest_danmaku = await asyncio.wait_for(
                            self.message_queue.get(),
                            timeout=1.0
                        )
                    except asyncio.TimeoutError:
                        continue

                # 处理弹幕消息（会阻塞直到音频播放完成）
                await self._process_danmaku(latest_danmaku)

            except Exception as e:
                self.logger.error(f"处理弹幕消息时出错: {e}")
                await asyncio.sleep(0.1)

    async def stop(self):
        """停止消息处理"""
        self.processing = False
        if self.tts:
            await self.tts.close()
        self.logger.info("停止弹幕消息处理")

    async def add_danmaku(self, danmaku: dict):
        """
        添加弹幕到处理队列（简化版：直接添加，由 start() 处理队列清理）

        Args:
            danmaku: 弹幕信息 {{"username": "用户名", "content": "弹幕内容"}}
        """
        username = danmaku.get('username', '观众')
        content = danmaku.get('content', '')

        await self.message_queue.put(danmaku)
        self.logger.debug(f"✅ 弹幕已加入队列: {username}: {content}")

    async def _process_danmaku(self, danmaku: dict):
        """
        处理单条弹幕消息（串行化：等待音频播放完成）

        Args:
            danmaku: 弹幕信息
        """
        try:
            username = danmaku.get('username', '观众')
            content = danmaku.get('content', '')

            if not content.strip():
                self.logger.debug(f"跳过空弹幕: {username}")
                return

            # 过滤纯表情符号的弹幕
            if is_pure_emoji_or_empty(content):
                self.logger.debug(f"⏭️  跳过纯表情弹幕: {username}: {content}")
                return

            self.logger.info(f"▶️  处理弹幕: {username}: {content}")

            # 生成唯一的句子ID
            sentence_id = str(uuid.uuid4().hex)
            self.logger.debug(f"   生成句子ID: {sentence_id}")

            # 更新conn对象的sentence_id，以便Rate Controller能正确检测句子变化
            old_sentence_id = getattr(self.tts.conn, 'sentence_id', None)
            self.tts.conn.sentence_id = sentence_id
            self.logger.debug(f"✅ 设置conn.sentence_id: {old_sentence_id} → {sentence_id}")

            # 发送FIRST消息（开始）
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=sentence_id,
                    sentence_type=SentenceType.FIRST,
                    content_type=ContentType.ACTION,
                )
            )
            self.logger.debug(f"   已发送FIRST消息到TTS队列")

            # 将弹幕内容添加到对话历史
            query = f"{username}说: {content}"
            self.dialogue.put(Message(role="user", content=query))

            # 调用LLM生成回复
            response_text = await self._call_llm(query, sentence_id)

            # 检查LLM回复是否有效（移除表情后）
            response_text_cleaned = remove_emojis(response_text)

            if not response_text or not response_text.strip():
                self.logger.warning(f"⚠️  LLM返回空内容，跳过此弹幕: {username}: {content}")
                return

            if not response_text_cleaned or not response_text_cleaned.strip():
                self.logger.warning(f"⚠️  LLM回复移除表情后为空，跳过TTS: {username} → {response_text}")
                # 仍然添加到对话历史
                self.dialogue.put(Message(role="assistant", content=response_text))
                return

            # 将回复添加到对话历史（保留原始内容，包括表情）
            self.dialogue.put(Message(role="assistant", content=response_text))

            # 发送LAST消息（结束）
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=sentence_id,
                    sentence_type=SentenceType.LAST,
                    content_type=ContentType.ACTION,
                )
            )
            self.logger.debug(f"   已发送LAST消息到TTS队列")

            # ✨ 关键：等待音频播放完成后再返回（串行化处理）
            self.logger.debug(f"⏳ 等待音频播放完成...")
            await self._wait_for_audio_completion()
            self.logger.info(f"✅ 弹幕处理完成: {username}")

        except Exception as e:
            self.logger.error(f"处理弹幕时出错: {e}", exc_info=True)

    async def _wait_for_audio_completion(self):
        """
        等待音频播放完成（使用 Rate Controller 的队列清空事件）
        """
        try:
            if hasattr(self.tts.conn, "audio_rate_controller") and self.tts.conn.audio_rate_controller:
                rate_controller = self.tts.conn.audio_rate_controller
                queue_len = len(rate_controller.queue)
                event_is_set = rate_controller.queue_empty_event.is_set()

                # 检查后台任务状态
                task_status = "无任务"
                if rate_controller.pending_send_task:
                    task = rate_controller.pending_send_task
                    if task.done():
                        task_status = f"已完成(异常={task.exception() if task.exception() else '无'})"
                    elif task.cancelled():
                        task_status = "已取消"
                    else:
                        task_status = "运行中"

                self.logger.debug(
                    f"   等待检查: 队列长度={queue_len}, "
                    f"事件状态={'已设置(无需等待)' if event_is_set else '未设置(需要等待)'}, "
                    f"后台任务={task_status}"
                )

                if queue_len > 0 or not event_is_set:
                    self.logger.debug(f"   开始等待音频队列清空...")
                    # 等待队列清空事件（带超时保护）
                    try:
                        await asyncio.wait_for(
                            rate_controller.queue_empty_event.wait(),
                            timeout=60.0  # 最多等待60秒
                        )
                        self.logger.debug("   ✓ 音频队列已清空")
                    except asyncio.TimeoutError:
                        # 超时后再次检查后台任务状态
                        task_status_after = "无任务"
                        if rate_controller.pending_send_task:
                            task = rate_controller.pending_send_task
                            if task.done():
                                exc = task.exception() if hasattr(task, 'exception') else None
                                task_status_after = f"已完成(异常={exc})"
                            elif task.cancelled():
                                task_status_after = "已取消"
                            else:
                                task_status_after = "运行中"

                        self.logger.error(
                            f"   ✗ 等待音频播放超时（60秒）！"
                            f"最终队列长度: {len(rate_controller.queue)}, "
                            f"后台任务状态: {task_status_after}"
                        )
                else:
                    self.logger.debug("   ✓ 音频队列已空，无需等待")
            else:
                self.logger.debug("   Rate Controller 不存在，等待0.5秒")
                await asyncio.sleep(0.5)
        except Exception as e:
            self.logger.error(f"等待音频完成时出错: {e}", exc_info=True)

    async def _call_llm(self, query: str, sentence_id: str) -> str:
        """
        调用LLM生成回复

        Args:
            query: 用户查询
            sentence_id: 句子ID

        Returns:
            LLM回复文本
        """
        try:
            self.logger.debug(f"调用LLM处理: {query}")

            # 获取对话历史
            dialogue = self.dialogue.get_llm_dialogue()

            # 调用LLM流式响应
            llm_responses = self.llm.response(self.session_id, dialogue)

            # 收集响应
            response_parts = []
            emotion_flag = True
            text_sent_count = 0

            for response in llm_responses:
                content = response

                # 提取情绪（仅首次）
                if emotion_flag and content and content.strip():
                    # 注意：这里需要在异步环境中运行，需要调整
                    # await textUtils.get_emotion(self, content)
                    emotion_flag = False

                if content and len(content) > 0:
                    response_parts.append(content)

                    # 移除表情符号后再发送给TTS（TTS无法处理表情）
                    content_for_tts = remove_emojis(content)

                    # 只有移除表情后仍有文字内容时才发送给TTS
                    if content_for_tts and content_for_tts.strip():
                        self.logger.debug(f"发送文本给TTS: {content_for_tts} (原文: {content})")
                        self.tts.tts_text_queue.put(
                            TTSMessageDTO(
                                sentence_id=sentence_id,
                                sentence_type=SentenceType.MIDDLE,
                                content_type=ContentType.TEXT,
                                content_detail=content_for_tts,
                            )
                        )
                        text_sent_count += 1
                    else:
                        self.logger.debug(f"跳过纯表情片段: {content}")

            # 合并完整回复
            full_response = "".join(response_parts)

            # 检查是否有有效内容
            if not full_response.strip():
                self.logger.warning("LLM 返回了空内容，跳过 TTS 处理")
                return ""

            self.logger.info(f"LLM回复: {full_response}")
            self.logger.debug(f"📝 已发送 {text_sent_count} 段文本给TTS")

            return full_response

        except Exception as e:
            self.logger.error(f"调用LLM时出错: {e}", exc_info=True)
            return ""


class DanmakuConnection:
    """
    模拟的连接处理器
    用于TTS回调
    """

    def __init__(self, device_manager, logger, config=None):
        self.device_manager = device_manager
        self.logger = logger

        # 创建模拟的 websocket 对象
        self.websocket = self._create_mock_websocket()

        # TTS 需要的属性
        self.stop_event = threading.Event()  # 停止事件
        self.client_abort = False  # 是否中断
        self.loop = asyncio.get_event_loop()  # 事件循环
        self.max_output_size = 0  # 最大输出大小（0表示不限制）
        self.headers = {"device-id": "broadcast"}  # 模拟请求头
        self.audio_format = "opus"  # 音频格式（使用 Opus 编码，与硬件设备兼容）
        self.tts = None  # TTS 实例（稍后设置）
        self.client_is_speaking = False  # 是否正在说话
        self.close_after_chat = False  # 对话后是否关闭
        self.sentence_id = None  # 句子ID
        self.config = config if config else {}  # 配置信息
        self.conn_from_mqtt_gateway = False  # 是否来自 MQTT 网关
        self.read_config_from_api = False  # 是否从 API 读取配置
        self.session_id = str(uuid.uuid4())  # 会话ID

        # 音频速率控制相关
        self.audio_rate_controller = AudioRateController(frame_duration=60)  # 音频速率控制器（60ms帧时长）
        self.audio_flow_control = {  # 音频流控制状态（初始化必要的键）
            "packet_count": 0,
            "sequence": 0,
            "sentence_id": None
        }
        self.last_activity_time = 0  # 最后活动时间
        self.current_speaker = None  # 当前说话人

    def _create_mock_websocket(self):
        """创建模拟的 WebSocket 对象"""
        class MockWebSocket:
            def __init__(self, device_manager, logger):
                self.device_manager = device_manager
                self.logger = logger
                self.packet_count = 0  # 音频包计数器

            async def send(self, data):
                """发送数据到所有设备"""
                device_count = self.device_manager.get_device_count()

                # 检测数据类型
                try:
                    # 尝试解析为JSON
                    if isinstance(data, (str, bytes)):
                        data_bytes = data.encode('utf-8') if isinstance(data, str) else data
                        data_str = data_bytes.decode('utf-8')
                        import json
                        json_obj = json.loads(data_str)

                        # 🚫 只过滤 stop 消息，避免硬件进入聆听状态
                        # start 和 sentence_start 消息需要保留，硬件需要它们来开始播放
                        if json_obj.get('type') == 'tts' and json_obj.get('state') == 'stop':
                            self.logger.bind(tag=TAG).debug(
                                f"🚫 过滤 TTS stop 消息（避免硬件进入聆听状态）"
                            )
                            return  # 不发送给设备

                        # 其他JSON消息正常发送（包括 start 和 sentence_start）
                        self.logger.bind(tag=TAG).debug(
                            f"📨 发送控制消息: {json_obj} → {device_count} 个设备"
                        )
                    else:
                        raise ValueError("Not JSON")
                except:
                    # 音频数据
                    self.packet_count += 1
                    if self.packet_count <= 5 or self.packet_count % 50 == 0:
                        self.logger.bind(tag=TAG).debug(
                            f"🔊 音频包 #{self.packet_count}: {len(data)} 字节 → {device_count} 个设备"
                        )

                await self.device_manager.broadcast_audio(data)

        return MockWebSocket(self.device_manager, self.logger)

    def set_tts(self, tts):
        """设置 TTS 实例"""
        self.tts = tts

    def clearSpeakStatus(self):
        """清除服务端讲话状态"""
        self.client_is_speaking = False
        if self.audio_rate_controller:
            self.audio_rate_controller.reset()

    async def send(self, data):
        """发送数据（广播到所有设备）"""
        await self.device_manager.broadcast_audio(data)

    async def close(self):
        """关闭连接（广播模式下不做任何操作）"""
        pass
