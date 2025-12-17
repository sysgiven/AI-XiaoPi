"""
基于 DouyinBarrageGrab 的抖音弹幕采集器
通过连接到 DouyinBarrageGrab 提供的 WebSocket 服务器获取弹幕数据

使用说明：
1. 下载并运行 DouyinBarrageGrab 程序：https://gitee.com/haodong108/dy-barrage-grab
2. 管理员身份启动 WssBarrageService.exe
3. 打开浏览器进入抖音直播间
4. 运行本采集器连接到 ws://127.0.0.1:8888

消息类型说明:
1 - 弹幕消息
2 - 点赞消息
3 - 进入直播间
4 - 关注消息
5 - 礼物消息
6 - 直播间统计
7 - 粉丝团消息
8 - 直播间分享
9 - 下播
"""

import asyncio
import json
import time
import logging
from typing import Callable, Optional, Dict, Any
import websockets
from enum import IntEnum


class MessageType(IntEnum):
    """弹幕消息类型枚举"""
    无 = 0
    弹幕消息 = 1
    点赞消息 = 2
    进入直播间 = 3
    关注消息 = 4
    礼物消息 = 5
    直播间统计 = 6
    粉丝团消息 = 7
    直播间分享 = 8
    下播 = 9


class Gender(IntEnum):
    """性别枚举"""
    未知 = 0
    男 = 1
    女 = 2

    @staticmethod
    def to_string(gender: int) -> str:
        """转换为中文字符串"""
        if gender == Gender.男:
            return "男"
        elif gender == Gender.女:
            return "女"
        else:
            return "未知"


class DouyinProxyCollector:
    """
    抖音弹幕代理采集器

    连接到 DouyinBarrageGrab 提供的 WebSocket 服务器
    接收并解析弹幕数据
    """

    def __init__(
        self,
        on_message_callback: Callable,
        ws_url: str = "ws://127.0.0.1:8888",
        logger=None
    ):
        """
        初始化代理采集器

        Args:
            on_message_callback: 收到弹幕消息时的回调函数
            ws_url: DouyinBarrageGrab 的 WebSocket 地址
            logger: 日志记录器
        """
        self.on_message_callback = on_message_callback
        self.ws_url = ws_url
        self.logger = logger or logging.getLogger(__name__)
        self.websocket = None
        self.running = False
        self.reconnect_delay = 5  # 重连延迟(秒)
        self.max_reconnect_attempts = 100  # 最大重连次数

        # 统计信息
        self.stats = {
            'total_messages': 0,
            'danmaku_count': 0,
            'like_count': 0,
            'gift_count': 0,
            'follow_count': 0,
            'enter_count': 0,
        }

    async def connect(self) -> bool:
        """连接到 DouyinBarrageGrab WebSocket 服务器"""
        try:
            self.logger.debug(f"正在连接到 DouyinBarrageGrab 服务器: {self.ws_url}")

            # 使用默认的 ping/pong 配置，保证能收到弹幕数据
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5
            )

            self.logger.debug(f"✅ 成功连接到 DouyinBarrageGrab 服务器")
            return True

        except ConnectionRefusedError:
            self.logger.error("❌ 连接被拒绝！请确保 DouyinBarrageGrab 程序正在运行")
            return False
        except Exception as e:
            self.logger.error(f"❌ 连接失败: {e}")
            return False

    async def start(self):
        """启动弹幕采集"""
        self.running = True
        reconnect_count = 0
        is_first_connection = True  # 标记是否首次连接

        # 首次启动时显示提示信息
        self.logger.info("请确保：")
        self.logger.info("1. DouyinBarrageGrab 程序正在运行")
        self.logger.info("2. 浏览器已打开抖音直播间")

        while self.running and reconnect_count < self.max_reconnect_attempts:
            try:
                if await self.connect():
                    # 只在首次连接成功时显示 INFO 日志
                    if is_first_connection:
                        self.logger.info(f"✅ 成功连接到 DouyinBarrageGrab 服务器")
                        is_first_connection = False
                    else:
                        # 重连成功，显示 INFO 日志确认
                        self.logger.info(f"♻️  已重新连接到 DouyinBarrageGrab 服务器")

                    reconnect_count = 0  # 连接成功，重置重连计数
                    await self._listen()
                else:
                    reconnect_count += 1
                    if reconnect_count < self.max_reconnect_attempts:
                        self.logger.warning(
                            f"⚠️  {self.reconnect_delay}秒后重试连接 "
                            f"({reconnect_count}/{self.max_reconnect_attempts})"
                        )
                        await asyncio.sleep(self.reconnect_delay)

            except websockets.exceptions.ConnectionClosed:
                self.logger.debug("⚠️  连接已关闭，准备重连...")
                reconnect_count += 1
                if reconnect_count < self.max_reconnect_attempts:
                    await asyncio.sleep(self.reconnect_delay)

            except Exception as e:
                self.logger.error(f"❌ 弹幕采集出错: {e}")
                reconnect_count += 1
                if reconnect_count < self.max_reconnect_attempts:
                    await asyncio.sleep(self.reconnect_delay)

        if reconnect_count >= self.max_reconnect_attempts:
            self.logger.error("❌ 达到最大重连次数，停止采集")

    async def _listen(self):
        """监听 WebSocket 消息"""
        try:
            self.logger.info(f"📡 开始监听 WebSocket 消息...")
            message_count = 0
            danmaku_count = 0  # 弹幕计数
            last_danmaku_time = time.time()  # 最后收到弹幕的时间
            warned_no_danmaku = False  # 是否已警告过没有弹幕

            async for message in self.websocket:
                if not self.running:
                    break

                message_count += 1

                # 尝试解析消息类型
                try:
                    data = json.loads(message)
                    msg_type = data.get("Type", "unknown")
                    if msg_type == MessageType.弹幕:
                        danmaku_count += 1
                        last_danmaku_time = time.time()
                        warned_no_danmaku = False  # 重置警告标志
                except:
                    pass

                # 每收到10条消息记录一次（确认正在接收）
                if message_count % 10 == 0:
                    self.logger.info(f"📊 已接收 {message_count} 条消息（其中弹幕 {danmaku_count} 条）")

                # 检查是否长时间没有弹幕（60秒）
                if not warned_no_danmaku and (time.time() - last_danmaku_time) > 60:
                    self.logger.warning(
                        f"⚠️  已经 60 秒没有收到弹幕消息了！\n"
                        f"   建议：重启 DouyinBarrageGrab 程序以恢复弹幕推送"
                    )
                    warned_no_danmaku = True

                await self._process_message(message)

            self.logger.info(f"📡 消息循环结束，总计接收 {message_count} 条消息（其中弹幕 {danmaku_count} 条）")

        except websockets.exceptions.ConnectionClosed as e:
            self.logger.debug(
                f"WebSocket 连接已关闭 - "
                f"关闭代码: {e.code}, 原因: {e.reason or '无'}"
            )
            raise
        except Exception as e:
            self.logger.error(f"监听消息时出错: {e}")
            raise

    async def _process_message(self, message: str):
        """
        处理收到的消息

        Args:
            message: WebSocket 消息（JSON字符串）
        """
        try:
            # 解析 JSON 消息
            data = json.loads(message)

            # 检查消息类型
            if "Type" not in data:
                self.logger.warning("⚠️  收到无效消息：缺少Type字段")
                return

            msg_type = data["Type"]
            self.stats['total_messages'] += 1

            # 处理下播消息（特殊处理，没有Data字段）
            if msg_type == MessageType.下播:
                await self._handle_live_exit()
                return

            # 检查是否有 Data 字段
            if "Data" not in data:
                self.logger.warning(f"⚠️  消息类型 {msg_type} 缺少Data字段")
                return

            # 解析 Data 字段（也是JSON字符串）
            try:
                data_dict = json.loads(data["Data"])
            except json.JSONDecodeError:
                self.logger.error(f"无法解析Data字段: {data['Data'][:100]}...")
                return

            # 根据消息类型处理
            if msg_type == MessageType.弹幕消息:
                await self._handle_danmaku(data_dict)
            elif msg_type == MessageType.点赞消息:
                await self._handle_like(data_dict)
            elif msg_type == MessageType.进入直播间:
                await self._handle_enter(data_dict)
            elif msg_type == MessageType.关注消息:
                await self._handle_follow(data_dict)
            elif msg_type == MessageType.礼物消息:
                await self._handle_gift(data_dict)
            elif msg_type == MessageType.直播间统计:
                await self._handle_statistics(data_dict)
            elif msg_type == MessageType.粉丝团消息:
                await self._handle_fansclub(data_dict)
            elif msg_type == MessageType.直播间分享:
                await self._handle_share(data_dict)
            else:
                self.logger.debug(f"未处理的消息类型: {msg_type}")

        except json.JSONDecodeError:
            self.logger.error(f"无效的JSON格式: {message[:100]}...")
        except Exception as e:
            self.logger.error(f"处理消息时出错: {e}", exc_info=True)

    async def _handle_danmaku(self, data: dict):
        """
        处理弹幕消息

        Args:
            data: 弹幕数据字典
        """
        try:
            self.stats['danmaku_count'] += 1

            # 提取用户信息
            user = data.get('User', {})
            username = user.get('Nickname', '匿名用户')
            gender = user.get('Gender', 0)
            gender_str = Gender.to_string(gender)

            # 提取弹幕内容
            content = data.get('Content', '')

            # 提取主播信息
            owner = data.get('Owner') or data.get('Onwer', {})  # 兼容拼写错误
            room_name = owner.get('Nickname', '') if isinstance(owner, dict) else ''

            # 记录日志（改为DEBUG级别，因为弹幕消息非常频繁）
            self.logger.debug(f"💬 [{room_name}] [{gender_str}] {username}: {content}")

            # 转换为标准格式并回调
            danmaku_info = {
                'type': 'danmaku',
                'username': username,
                'content': content,
                'timestamp': 0,
                'gender': gender,
                'gender_str': gender_str,
                'user_info': user,
                'room_info': owner,
                'raw_data': data
            }

            await self.on_message_callback(danmaku_info)

        except Exception as e:
            self.logger.error(f"处理弹幕消息失败: {e}")

    async def _handle_like(self, data: dict):
        """处理点赞消息"""
        try:
            self.stats['like_count'] += 1

            user = data.get('User', {})
            username = user.get('Nickname', '匿名用户')
            count = data.get('Count', 0)
            total = data.get('Total', 0)

            self.logger.debug(f"👍 {username} 点赞 {count} 次，总点赞 {total}")

        except Exception as e:
            self.logger.error(f"处理点赞消息失败: {e}")

    async def _handle_enter(self, data: dict):
        """处理进入直播间消息"""
        try:
            self.stats['enter_count'] += 1

            user = data.get('User', {})
            username = user.get('Nickname', '匿名用户')
            current_count = data.get('CurrentCount', 0)

            self.logger.debug(f"👋 {username} 进入直播间，当前人数: {current_count}")

        except Exception as e:
            self.logger.error(f"处理进入直播间消息失败: {e}")

    async def _handle_follow(self, data: dict):
        """处理关注消息"""
        try:
            self.stats['follow_count'] += 1

            user = data.get('User', {})
            username = user.get('Nickname', '匿名用户')

            self.logger.debug(f"❤️  {username} 关注了主播")

        except Exception as e:
            self.logger.error(f"处理关注消息失败: {e}")

    async def _handle_gift(self, data: dict):
        """处理礼物消息"""
        try:
            self.stats['gift_count'] += 1

            user = data.get('User', {})
            username = user.get('Nickname', '匿名用户')
            gift_name = data.get('GiftName', '未知礼物')
            gift_count = data.get('GiftCount', 1)
            gift_value = data.get('DiamondCount', 0)  # 抖币价格

            self.logger.debug(
                f"🎁 {username} 送出 {gift_count}个{gift_name}，价值 {gift_value} 抖币"
            )

        except Exception as e:
            self.logger.error(f"处理礼物消息失败: {e}")

    async def _handle_statistics(self, data: dict):
        """处理直播间统计消息"""
        try:
            online_count = data.get('OnlineUserCountStr', '0')
            total_count = data.get('TotalUserCountStr', '0')

            self.logger.debug(f"📊 在线人数: {online_count}，累计观看: {total_count}万")

        except Exception as e:
            self.logger.error(f"处理统计消息失败: {e}")

    async def _handle_fansclub(self, data: dict):
        """处理粉丝团消息"""
        try:
            user = data.get('User', {})
            username = user.get('Nickname', '匿名用户')
            club_name = data.get('FansClubName', '')

            self.logger.debug(f"⭐ {username} 加入了 {club_name} 粉丝团")

        except Exception as e:
            self.logger.error(f"处理粉丝团消息失败: {e}")

    async def _handle_share(self, data: dict):
        """处理直播间分享消息"""
        try:
            user = data.get('User', {})
            username = user.get('Nickname', '匿名用户')

            self.logger.debug(f"📤 {username} 分享了直播间")

        except Exception as e:
            self.logger.error(f"处理分享消息失败: {e}")

    async def _handle_live_exit(self):
        """处理下播消息"""
        try:
            self.logger.info("📺 直播结束")
            self.logger.debug(f"统计信息: {self.stats}")

            # 重置统计
            self.stats = {
                'total_messages': 0,
                'danmaku_count': 0,
                'like_count': 0,
                'gift_count': 0,
                'follow_count': 0,
                'enter_count': 0,
            }

        except Exception as e:
            self.logger.error(f"处理下播消息失败: {e}")

    async def stop(self):
        """停止弹幕采集"""
        self.running = False
        if self.websocket:
            try:
                await self.websocket.close()
                self.logger.debug("弹幕采集器已停止")
            except Exception as e:
                self.logger.error(f"关闭WebSocket时出错: {e}")

    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.stats.copy()


# 工厂函数
def create_douyin_proxy_collector(
    on_message_callback: Callable,
    ws_url: str = "ws://127.0.0.1:8888",
    logger=None
) -> DouyinProxyCollector:
    """
    创建抖音代理采集器

    Args:
        on_message_callback: 回调函数
        ws_url: DouyinBarrageGrab WebSocket 地址
        logger: 日志记录器

    Returns:
        采集器实例
    """
    return DouyinProxyCollector(
        on_message_callback,
        ws_url,
        logger
    )


# 示例使用
async def example_callback(danmaku: dict):
    """示例回调函数"""
    print(f"收到弹幕: {danmaku['username']}: {danmaku['content']}")


async def main():
    """测试主函数"""
    import sys

    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    # 创建采集器
    collector = create_douyin_proxy_collector(
        on_message_callback=example_callback,
        logger=logger
    )

    logger.info("=" * 60)
    logger.info("抖音弹幕采集器 - 基于 DouyinBarrageGrab")
    logger.info("=" * 60)
    logger.info("使用前准备：")
    logger.info("1. 下载 DouyinBarrageGrab: https://gitee.com/haodong108/dy-barrage-grab")
    logger.info("2. 管理员身份启动 WssBarrageService.exe")
    logger.info("3. 打开浏览器进入抖音直播间")
    logger.info("4. 观察本程序是否收到弹幕")
    logger.info("=" * 60)

    try:
        # 启动采集
        await collector.start()
    except KeyboardInterrupt:
        logger.info("\n收到中断信号，正在停止...")
        await collector.stop()
    except Exception as e:
        logger.error(f"运行出错: {e}", exc_info=True)
        await collector.stop()


if __name__ == "__main__":
    asyncio.run(main())
