"""
弹幕AI服务器启动入口
"""

import sys
import asyncio
import signal
import os
from config.config_loader import read_config, get_project_dir
from config.logger import setup_logging
from danmaku_server.danmaku_service import DanmakuService


logger = setup_logging()
TAG = __name__


async def wait_for_exit() -> None:
    """
    阻塞直到收到 Ctrl-C / SIGTERM。
    - Unix: 使用 add_signal_handler
    - Windows: 依赖 KeyboardInterrupt
    """
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    if sys.platform != "win32":  # Unix / macOS
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
        await stop_event.wait()
    else:
        # Windows：await一个永远pending的fut，
        # 让 KeyboardInterrupt 冒泡到 asyncio.run
        try:
            await asyncio.Future()
        except KeyboardInterrupt:
            pass


async def main():
    """主函数"""
    try:
        logger.info("=" * 60)
        logger.info("抖音直播弹幕AI服务器")
        logger.info("基于 xiaozhi-esp32-server 二次开发")
        logger.info("=" * 60)

        # 加载弹幕专用配置文件
        danmaku_config_path = get_project_dir() + "danmaku_config.yaml"

        if not os.path.exists(danmaku_config_path):
            logger.error(f"找不到配置文件: {danmaku_config_path}")
            logger.error("请确保 danmaku_config.yaml 文件存在于项目根目录")
            return

        logger.info(f"加载配置文件: {danmaku_config_path}")
        config = read_config(danmaku_config_path)

        # 创建并启动弹幕服务
        danmaku_service = DanmakuService(config)
        service_task = asyncio.create_task(danmaku_service.start())

        # 等待退出信号
        await wait_for_exit()

        # 停止服务
        logger.info("收到退出信号，正在关闭服务...")
        await danmaku_service.stop()

        # 取消服务任务
        service_task.cancel()
        try:
            await service_task
        except asyncio.CancelledError:
            pass

        logger.info("服务已关闭，程序退出")

    except KeyboardInterrupt:
        logger.info("手动中断，程序终止")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("手动中断，程序终止。")
