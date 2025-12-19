"""
测试客户端
用于测试弹幕AI服务器的设备连接和音频接收功能
"""

import asyncio
import websockets
import sys


async def test_client(server_url: str, device_id: str):
    """
    测试客户端

    Args:
        server_url: 服务器WebSocket地址
        device_id: 设备ID
    """
    print(f"正在连接到服务器: {server_url}")
    print(f"设备ID: {device_id}")

    try:
        # 连接到服务器
        async with websockets.connect(
            f"{server_url}?device-id={device_id}",
            ping_interval=20,
            ping_timeout=10
        ) as websocket:
            print("✓ 连接成功！")

            # 接收消息
            async for message in websocket:
                if isinstance(message, str):
                    print(f"📨 收到文本消息: {message}")
                elif isinstance(message, bytes):
                    print(f"🔊 收到音频数据: {len(message)} 字节")
                    # 这里可以添加音频保存或播放逻辑

    except websockets.exceptions.ConnectionClosed:
        print("✗ 连接已关闭")
    except Exception as e:
        print(f"✗ 错误: {e}")


async def main():
    """主函数"""
    # 默认配置
    server_url = "ws://localhost:8001/danmaku/"
    device_id = "test_device_001"

    # 从命令行参数获取配置
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    if len(sys.argv) > 2:
        device_id = sys.argv[2]

    print("=" * 50)
    print("弹幕AI服务器 - 测试客户端")
    print("=" * 50)

    # 运行测试客户端
    await test_client(server_url, device_id)


if __name__ == "__main__":
    print("""
使用方法:
  python test_client.py [服务器地址] [设备ID]

示例:
  python test_client.py ws://localhost:8001/danmaku/ device001
  python test_client.py ws://192.168.1.100:8001/danmaku/ device002

如不提供参数，将使用默认配置连接到本地服务器
""")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n手动中断，程序退出")
