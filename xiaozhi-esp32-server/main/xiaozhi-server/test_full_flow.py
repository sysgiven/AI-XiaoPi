"""
完整流程测试脚本
测试从弹幕输入到音频输出的完整流程

使用方法:
    python test_full_flow.py

测试内容:
    1. 检查 DouyinBarrageGrab 连接状态
    2. 检查弹幕服务器状态
    3. 模拟设备连接
    4. 监控整个流程
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime


class FlowTester:
    """完整流程测试器"""

    def __init__(self):
        self.douyin_ws_url = "ws://127.0.0.1:8888"  # DouyinBarrageGrab
        self.server_ws_url = "ws://127.0.0.1:8001/danmaku/?device-id=test_device"
        self.stats = {
            'danmaku_received': 0,
            'audio_received': 0,
            'errors': 0
        }

    async def test_douyin_connection(self):
        """测试 DouyinBarrageGrab 连接"""
        print("🔍 测试 1/3: 检查 DouyinBarrageGrab 连接")
        print(f"   地址: {self.douyin_ws_url}")

        try:
            async with websockets.connect(
                self.douyin_ws_url,
                ping_interval=20,
                ping_timeout=5,
                close_timeout=3
            ) as ws:
                print("   ✅ DouyinBarrageGrab 连接正常")
                print("   提示: 确保浏览器已打开抖音直播间")
                return True
        except ConnectionRefusedError:
            print("   ❌ 连接被拒绝")
            print("   请确保:")
            print("      1. DouyinBarrageGrab (WssBarrageService.exe) 正在运行")
            print("      2. 以管理员身份启动")
            return False
        except Exception as e:
            print(f"   ❌ 连接失败: {e}")
            return False

    async def test_server_connection(self):
        """测试弹幕服务器连接"""
        print("\n🔍 测试 2/3: 检查弹幕AI服务器连接")
        print(f"   地址: {self.server_ws_url}")

        try:
            async with websockets.connect(
                self.server_ws_url,
                ping_interval=20,
                ping_timeout=5,
                close_timeout=3
            ) as ws:
                # 等待欢迎消息
                message = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(message)

                if data.get('type') == 'welcome':
                    print("   ✅ 弹幕AI服务器连接正常")
                    print(f"   设备ID: {data.get('device_id')}")
                    return True
                else:
                    print("   ⚠️  收到意外消息")
                    return False

        except ConnectionRefusedError:
            print("   ❌ 连接被拒绝")
            print("   请确保:")
            print("      1. danmaku_app.py 正在运行")
            print("      2. 配置文件正确")
            return False
        except asyncio.TimeoutError:
            print("   ❌ 等待欢迎消息超时")
            return False
        except Exception as e:
            print(f"   ❌ 连接失败: {e}")
            return False

    async def monitor_flow(self):
        """监控完整流程"""
        print("\n🔍 测试 3/3: 监控完整数据流程")
        print()
        print("正在连接...")

        try:
            # 同时连接两个服务器
            async with websockets.connect(self.douyin_ws_url) as douyin_ws, \
                       websockets.connect(self.server_ws_url) as server_ws:

                print("✅ 已连接到两个服务器")
                print()
                print("📊 实时监控:")
                print("-" * 60)

                # 创建两个监听任务
                douyin_task = asyncio.create_task(
                    self._monitor_douyin(douyin_ws)
                )
                server_task = asyncio.create_task(
                    self._monitor_server(server_ws)
                )

                # 运行30秒
                await asyncio.sleep(30)

                # 取消任务
                douyin_task.cancel()
                server_task.cancel()

                # 显示统计
                print()
                print("-" * 60)
                print("📈 统计结果:")
                print(f"   弹幕接收数: {self.stats['danmaku_received']}")
                print(f"   音频接收数: {self.stats['audio_received']}")
                print(f"   错误次数: {self.stats['errors']}")

                if self.stats['danmaku_received'] > 0 and self.stats['audio_received'] > 0:
                    print()
                    print("✅ 完整流程测试通过！")
                    print("   弹幕 → LLM → TTS → 音频下发 正常工作")
                elif self.stats['danmaku_received'] > 0:
                    print()
                    print("⚠️  接收到弹幕但没有音频输出")
                    print("   可能原因:")
                    print("      1. LLM 配置错误")
                    print("      2. TTS 配置错误")
                    print("      3. 检查日志文件 tmp/danmaku_server.log")
                else:
                    print()
                    print("⚠️  未接收到弹幕")
                    print("   请在抖音直播间发送弹幕测试")

        except Exception as e:
            print(f"❌ 监控出错: {e}")
            self.stats['errors'] += 1

    async def _monitor_douyin(self, ws):
        """监控 DouyinBarrageGrab 消息"""
        try:
            async for message in ws:
                try:
                    data = json.loads(message)
                    msg_type = data.get('Type', 0)

                    if msg_type == 1:  # 弹幕消息
                        self.stats['danmaku_received'] += 1
                        data_dict = json.loads(data.get('Data', '{}'))
                        username = data_dict.get('User', {}).get('Nickname', '未知')
                        content = data_dict.get('Content', '')

                        print(f"💬 [弹幕] {username}: {content}")

                except Exception as e:
                    self.stats['errors'] += 1

        except asyncio.CancelledError:
            pass

    async def _monitor_server(self, ws):
        """监控弹幕服务器消息"""
        try:
            async for message in ws:
                try:
                    if isinstance(message, bytes):
                        # 音频数据
                        self.stats['audio_received'] += 1
                        size_kb = len(message) / 1024
                        print(f"🔊 [音频] 大小: {size_kb:.2f} KB")

                except Exception as e:
                    self.stats['errors'] += 1

        except asyncio.CancelledError:
            pass

    async def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("弹幕AI服务器 - 完整流程测试")
        print("=" * 60)
        print()

        # 测试 1
        if not await self.test_douyin_connection():
            print("\n❌ DouyinBarrageGrab 未运行，无法继续测试")
            return

        # 测试 2
        if not await self.test_server_connection():
            print("\n❌ 弹幕AI服务器未运行，无法继续测试")
            return

        # 测试 3
        print("\n准备监控数据流程...")
        print("提示: 请在直播间发送弹幕以触发 AI 回复")
        print("监控时间: 30秒")
        print()
        await asyncio.sleep(2)

        await self.monitor_flow()


async def main():
    tester = FlowTester()
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n测试被中断")
    except Exception as e:
        print(f"\n测试出错: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已终止")
