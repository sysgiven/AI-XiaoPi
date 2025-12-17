import json
import time
import asyncio
from core.utils import textUtils
from core.utils.util import audio_to_data
from core.providers.tts.dto.dto import SentenceType
from core.utils.audioRateController import AudioRateController

TAG = __name__


async def sendAudioMessage(conn, sentenceType, audios, text):
    if conn.tts.tts_audio_first_sentence:
        conn.logger.bind(tag=TAG).info(f"发送第一段语音: {text}")
        conn.tts.tts_audio_first_sentence = False
        await send_tts_message(conn, "start", None)

    if sentenceType == SentenceType.FIRST:
        # 同一句子的后续消息加入流控队列，其他情况立即发送
        if (
            hasattr(conn, "audio_rate_controller")
            and conn.audio_rate_controller
            and getattr(conn, "audio_flow_control", {}).get("sentence_id")
            == conn.sentence_id
        ):
            conn.audio_rate_controller.add_message(
                lambda: send_tts_message(conn, "sentence_start", text)
            )
        else:
            # 新句子或流控器未初始化，立即发送
            await send_tts_message(conn, "sentence_start", text)

    await sendAudio(conn, audios)
    # 发送句子开始消息
    if sentenceType is not SentenceType.MIDDLE:
        conn.logger.bind(tag=TAG).debug(f"发送音频消息: {sentenceType}, {text}")

    # 发送结束消息（如果是最后一个文本）
    if sentenceType == SentenceType.LAST:
        await send_tts_message(conn, "stop", None)
        conn.client_is_speaking = False
        if conn.close_after_chat:
            await conn.close()


async def _wait_for_audio_completion(conn):
    """
    等待音频队列清空

    Args:
        conn: 连接对象
    """
    if hasattr(conn, "audio_rate_controller") and conn.audio_rate_controller:
        rate_controller = conn.audio_rate_controller
        conn.logger.bind(tag=TAG).debug(
            f"等待音频发送完成，队列中还有 {len(rate_controller.queue)} 个包"
        )
        await rate_controller.queue_empty_event.wait()
        conn.logger.bind(tag=TAG).debug("音频发送完成")


async def _send_to_mqtt_gateway(conn, opus_packet, timestamp, sequence):
    """
    发送带16字节头部的opus数据包给mqtt_gateway
    Args:
        conn: 连接对象
        opus_packet: opus数据包
        timestamp: 时间戳
        sequence: 序列号
    """
    # 为opus数据包添加16字节头部
    header = bytearray(16)
    header[0] = 1  # type
    header[2:4] = len(opus_packet).to_bytes(2, "big")  # payload length
    header[4:8] = sequence.to_bytes(4, "big")  # sequence
    header[8:12] = timestamp.to_bytes(4, "big")  # 时间戳
    header[12:16] = len(opus_packet).to_bytes(4, "big")  # opus长度

    # 发送包含头部的完整数据包
    complete_packet = bytes(header) + opus_packet
    await conn.websocket.send(complete_packet)


async def sendAudio(conn, audios, frame_duration=60):
    """
    发送音频包，使用 AudioRateController 进行精确的流量控制

    Args:
        conn: 连接对象
        audios: 单个opus包(bytes) 或 opus包列表
        frame_duration: 帧时长（毫秒），默认60ms
    """
    if audios is None or len(audios) == 0:
        return

    send_delay = conn.config.get("tts_audio_send_delay", -1) / 1000.0
    is_single_packet = isinstance(audios, bytes)

    # 初始化或获取 RateController
    rate_controller, flow_control = _get_or_create_rate_controller(
        conn, frame_duration, is_single_packet
    )

    # 统一转换为列表处理
    audio_list = [audios] if is_single_packet else audios

    # 发送音频包
    await _send_audio_with_rate_control(
        conn, audio_list, rate_controller, flow_control, send_delay
    )


def _get_or_create_rate_controller(conn, frame_duration, is_single_packet):
    """
    获取或创建 RateController 和 flow_control

    Args:
        conn: 连接对象
        frame_duration: 帧时长
        is_single_packet: 是否单包模式（True: TTS流式单包, False: 批量包）

    Returns:
        (rate_controller, flow_control)
    """
    # 判断是否需要重置：单包模式且 sentence_id 变化，或者控制器不存在
    need_reset = (
        is_single_packet
        and getattr(conn, "audio_flow_control", {}).get("sentence_id")
        != conn.sentence_id
    ) or not hasattr(conn, "audio_rate_controller")

    # 诊断日志：仅在需要重置时输出（调试级别）
    if need_reset:
        conn.logger.bind(tag=TAG).debug(
            f"Rate Controller 重置: current_sentence_id={conn.sentence_id}, "
            f"flow_control_sentence_id={getattr(conn, 'audio_flow_control', {}).get('sentence_id')}"
        )

    if need_reset:
        conn.logger.bind(tag=TAG).debug(f"🎬 启动新的Rate Controller后台任务（sentence_id={conn.sentence_id}）")
        # 创建或获取 rate_controller
        if not hasattr(conn, "audio_rate_controller"):
            conn.audio_rate_controller = AudioRateController(frame_duration)
            conn.logger.bind(tag=TAG).debug(f"   创建新的 AudioRateController")
        else:
            conn.logger.bind(tag=TAG).debug(f"   重置现有的 AudioRateController")
            conn.audio_rate_controller.reset()

        # 初始化 flow_control
        conn.audio_flow_control = {
            "packet_count": 0,
            "sequence": 0,
            "sentence_id": conn.sentence_id,
        }
        conn.logger.bind(tag=TAG).debug(f"   初始化 flow_control: sentence_id={conn.sentence_id}")

        # 启动后台发送循环
        _start_background_sender(
            conn, conn.audio_rate_controller, conn.audio_flow_control
        )
    else:
        conn.logger.bind(tag=TAG).debug(
            f"复用现有 Rate Controller (队列长度: {len(conn.audio_rate_controller.queue)}, "
            f"sentence_id={conn.sentence_id})"
        )

    return conn.audio_rate_controller, conn.audio_flow_control


def _start_background_sender(conn, rate_controller, flow_control):
    """
    启动后台发送循环任务

    Args:
        conn: 连接对象
        rate_controller: 速率控制器
        flow_control: 流控状态
    """

    async def send_callback(packet):
        # 检查是否应该中止
        if conn.client_abort:
            raise asyncio.CancelledError("客户端已中止")

        conn.last_activity_time = time.time() * 1000
        await _do_send_audio(conn, packet, flow_control)
        conn.client_is_speaking = True

    # 使用 start_sending 启动后台循环
    task = rate_controller.start_sending(send_callback)


async def _send_audio_with_rate_control(
    conn, audio_list, rate_controller, flow_control, send_delay
):
    """
    使用 rate_controller 发送音频包

    Args:
        conn: 连接对象
        audio_list: 音频包列表
        rate_controller: 速率控制器
        flow_control: 流控状态
        send_delay: 固定延迟（秒），-1表示使用动态流控
    """
    pre_buffer_count = 5

    for packet in audio_list:
        if conn.client_abort:
            return

        conn.last_activity_time = time.time() * 1000

        # 预缓冲：前5个包直接发送
        if flow_control["packet_count"] < pre_buffer_count:
            conn.logger.bind(tag=TAG).debug(f"预缓冲发送 #{flow_control['packet_count']+1}")
            await _do_send_audio(conn, packet, flow_control)
            conn.client_is_speaking = True
        elif send_delay > 0:
            # 固定延迟模式
            conn.logger.bind(tag=TAG).debug(f"固定延迟发送 #{flow_control['packet_count']+1}")
            await asyncio.sleep(send_delay)
            await _do_send_audio(conn, packet, flow_control)
            conn.client_is_speaking = True
        else:
            # 动态流控模式：仅添加到队列，由后台循环负责发送
            conn.logger.bind(tag=TAG).debug(f"添加到队列 #{flow_control['packet_count']+1}")
            rate_controller.add_audio(packet)


async def _do_send_audio(conn, opus_packet, flow_control):
    """
    执行实际的音频发送
    """
    packet_index = flow_control.get("packet_count", 0)
    sequence = flow_control.get("sequence", 0)

    if conn.conn_from_mqtt_gateway:
        # 计算时间戳（基于播放位置）
        start_time = time.time()
        timestamp = int(start_time * 1000) % (2**32)
        await _send_to_mqtt_gateway(conn, opus_packet, timestamp, sequence)
    else:
        # 直接发送opus数据包
        await conn.websocket.send(opus_packet)

    # 更新流控状态
    flow_control["packet_count"] = packet_index + 1
    flow_control["sequence"] = sequence + 1


async def send_tts_message(conn, state, text=None):
    """发送 TTS 状态消息"""
    if text is None and state == "sentence_start":
        return
    message = {"type": "tts", "state": state, "session_id": conn.session_id}
    if text is not None:
        message["text"] = textUtils.check_emoji(text)

    # TTS播放结束
    if state == "stop":
        # 播放提示音
        tts_notify = conn.config.get("enable_stop_tts_notify", False)
        if tts_notify:
            stop_tts_notify_voice = conn.config.get(
                "stop_tts_notify_voice", "config/assets/tts_notify.mp3"
            )
            audios = await audio_to_data(stop_tts_notify_voice, is_opus=True)
            await sendAudio(conn, audios)
        # 等待所有音频包发送完成
        await _wait_for_audio_completion(conn)
        # 清除服务端讲话状态
        conn.clearSpeakStatus()

    # 发送消息到客户端
    await conn.websocket.send(json.dumps(message))


async def send_stt_message(conn, text):
    """发送 STT 状态消息"""
    end_prompt_str = conn.config.get("end_prompt", {}).get("prompt")
    if end_prompt_str and end_prompt_str == text:
        await send_tts_message(conn, "start")
        return

    # 解析JSON格式，提取实际的用户说话内容
    display_text = text
    try:
        # 尝试解析JSON格式
        if text.strip().startswith("{") and text.strip().endswith("}"):
            parsed_data = json.loads(text)
            if isinstance(parsed_data, dict) and "content" in parsed_data:
                # 如果是包含说话人信息的JSON格式，只显示content部分
                display_text = parsed_data["content"]
                # 保存说话人信息到conn对象
                if "speaker" in parsed_data:
                    conn.current_speaker = parsed_data["speaker"]
    except (json.JSONDecodeError, TypeError):
        # 如果不是JSON格式，直接使用原始文本
        display_text = text
    stt_text = textUtils.get_string_no_punctuation_or_emoji(display_text)
    await conn.websocket.send(
        json.dumps({"type": "stt", "text": stt_text, "session_id": conn.session_id})
    )
    await send_tts_message(conn, "start")
