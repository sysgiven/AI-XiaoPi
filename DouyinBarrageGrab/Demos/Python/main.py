import asyncio
import websockets
import json
import time
from datetime import datetime
from typing import Dict, Any
from colorama import init, Fore, Style
from entities import (
    PackMsgType, Gender, LiveStats, LikeMsg, MemberMessage, UserSeqMsg,
    GiftMsg, FansclubMsg, ShareMessage, ShareType
)
from parsers import MessageParser

'''
抖音直播间消息处理脚本
消息类型说明:
1[普通弹幕]|2[点赞消息]|3[进入直播间]|4[关注消息]|5[礼物消息]|6[统计消息]|7[粉丝团消息]|8[直播间分享]|9[下播]

全局统计变量:
Live_Total - 本场点赞数
Live_user  - 本场总观看人数
Live_man   - 本场男生人数
Live_woman - 本场女生人数
'''

# 初始化彩色输出
init(autoreset=True)

# 颜色定义
COLOR_MAP = {
    PackMsgType.弹幕消息: Fore.CYAN,       # 青色
    PackMsgType.点赞消息: Fore.YELLOW,     # 黄色
    PackMsgType.进直播间: Fore.GREEN,      # 绿色
    PackMsgType.关注消息: Fore.MAGENTA,    # 洋红色
    PackMsgType.礼物消息: Fore.RED,        # 红色
    PackMsgType.直播间统计: Fore.BLUE,     # 蓝色
    PackMsgType.粉丝团消息: Fore.LIGHTBLUE_EX, # 浅蓝色
    PackMsgType.直播间分享: Fore.LIGHTMAGENTA_EX, # 浅洋红色
    PackMsgType.下播: Fore.RED,            # 红色
}

# 初始化统计对象
live_stats = LiveStats()

def get_timestamp() -> str:
    """返回当前时间戳，格式：HH:MM:SS"""
    return datetime.now().strftime("%H:%M:%S")

def print_colored_message(msg_type: PackMsgType, content: str, author: str = "未知") -> None:
    """打印带颜色的消息"""
    color = COLOR_MAP.get(msg_type, Fore.WHITE)
    timestamp = get_timestamp()
    elapsed_time = "["+author+"]"
    print(f"{color}{timestamp} {elapsed_time} {content}{Style.RESET_ALL}")

def get_msg_owner(msg) -> str:
    """统一获取消息所属的主播/房间信息"""
    if hasattr(msg, 'Owner') and msg.Owner:
        return msg.Owner.Nickname
    elif hasattr(msg, 'WebRoomId') and msg.WebRoomId:
        return msg.WebRoomId
    elif hasattr(msg, 'RoomId') and msg.RoomId:
        return msg.RoomId
    return "未知"

# 处理函数：弹幕消息
def handle_danmaku(data_dict: Dict[str, Any]) -> None:
    """处理用户发送的弹幕消息"""
    msg = MessageParser.parse_danmaku(data_dict)
    gender_str = msg.User.gender_to_string()
    content = f"[弹幕消息] [{gender_str}] {msg.User.Nickname}: {msg.Content}"
    author = get_msg_owner(msg)
    print_colored_message(PackMsgType.弹幕消息, content, author)

# 处理函数：点赞消息
def handle_dianzanku(data_dict: Dict[str, Any]) -> None:
    """处理用户点赞消息并更新全局统计"""
    like_msg = MessageParser.parse_like(data_dict)
    live_stats.total_likes = like_msg.Total
    gender_str = like_msg.User.gender_to_string()
    content = f"[点赞消息] [{gender_str}] {like_msg.User.Nickname} 为主播点了{like_msg.Count}个赞, 总点赞{like_msg.Total}"
    author = get_msg_owner(like_msg)
    print_colored_message(PackMsgType.点赞消息, content, author)

# 处理函数：进入直播间
def handle_userentry(data_dict: Dict[str, Any]) -> None:
    """处理用户进入直播间的消息，并根据性别更新统计"""
    member_msg = MessageParser.parse_member(data_dict)
    
    # 根据性别更新全局计数
    if member_msg.User.Gender == Gender.男:
        live_stats.male_users += 1
    elif member_msg.User.Gender == Gender.女:
        live_stats.female_users += 1
    
    gender_str = member_msg.User.gender_to_string()
    content = f"[进直播间] [{gender_str}] {member_msg.User.Nickname} $来了 直播间人数:{member_msg.CurrentCount}"
    author = get_msg_owner(member_msg)
    print_colored_message(PackMsgType.进直播间, content, author)

# 处理函数：关注消息
def handle_follow(data_dict: Dict[str, Any]) -> None:
    """处理用户关注主播的消息"""
    follow_msg = MessageParser.parse_follow(data_dict)
    gender_str = follow_msg.User.gender_to_string()
    content = f"[关注消息] [{gender_str}] {follow_msg.User.Nickname} 关注了主播"
    author = get_msg_owner(follow_msg)
    print_colored_message(PackMsgType.关注消息, content, author)

# 处理函数：礼物消息
def handle_gift(data_dict: Dict[str, Any]) -> None:
    """处理用户赠送礼物的消息"""
    gift_msg = MessageParser.parse_gift(data_dict)
    gender_str = gift_msg.User.gender_to_string()
    
    # 使用DiamondCount或GiftValue作为礼物价值
    gift_value = gift_msg.DiamondCount or gift_msg.GiftValue
    
    content = f"[礼物消息] [{gender_str}] {gift_msg.User.Nickname} 送出了 {gift_msg.GiftCount}个{gift_msg.GiftName}, 价值{gift_value}抖币"
    author = get_msg_owner(gift_msg)
    print_colored_message(PackMsgType.礼物消息, content, author)

# 处理函数：统计消息
def handle_statistics(data_dict: Dict[str, Any]) -> None:
    """处理直播间统计信息"""
    stats_msg = MessageParser.parse_statistics(data_dict)
    live_stats.total_users = int(stats_msg.TotalUserCount)
    content = f"[直播间统计] 当前直播间人数 {stats_msg.OnlineUserCountStr}, 累计直播间人数 {stats_msg.TotalUserCountStr}万"
    author = get_msg_owner(stats_msg)
    print_colored_message(PackMsgType.直播间统计, content, author)

# 处理函数：粉丝团消息
def handle_fansclub(data_dict: Dict[str, Any]) -> None:
    """处理粉丝团相关消息"""
    fansclub_msg = MessageParser.parse_fansclub(data_dict)
    gender_str = fansclub_msg.User.gender_to_string()
    
    if fansclub_msg.Type == 1:
        action = "升级了"
        content = f"[粉丝团消息] [{gender_str}] {fansclub_msg.User.Nickname} {action}{fansclub_msg.FansClubName}粉丝团到{fansclub_msg.Level}级"
    else:
        action = "加入了"
        content = f"[粉丝团消息] [{gender_str}] {fansclub_msg.User.Nickname} {action}{fansclub_msg.FansClubName}粉丝团"
    
    author = get_msg_owner(fansclub_msg)
    print_colored_message(PackMsgType.粉丝团消息, content, author)

# 处理函数：直播间分享
def handle_share(data_dict: Dict[str, Any]) -> None:
    """处理用户分享直播间的消息"""
    share_msg = MessageParser.parse_share(data_dict)
    gender_str = share_msg.User.gender_to_string()
    
    # 获取分享目标类型
    share_type_str = share_msg.ShareType.name if hasattr(share_msg.ShareType, 'name') else "未知平台"
    
    content = f"[直播间分享] [{gender_str}] {share_msg.User.Nickname} 分享了直播间到{share_type_str}"
    author = get_msg_owner(share_msg)
    print_colored_message(PackMsgType.直播间分享, content, author)

# 处理函数：直播结束
def handle_live_exit() -> None:
    """处理直播结束事件，显示并重置统计数据"""
    content = f"[下播] 直播结束：累计观看 {live_stats.total_users} 人，累计点赞 {live_stats.total_likes}，"\
            f"男生 {live_stats.male_users} 女生 {live_stats.female_users}"
    print_colored_message(PackMsgType.下播, content, "系统消息")
    live_stats.reset()
    print(f"直播统计数据已清空~")

async def process_message(message: str) -> None:
    """处理从WebSocket接收到的单条消息"""
    try:
        data = json.loads(message)
        
        if "Type" not in data:
            print("⚠️ 收到无效消息：缺少Type字段")
            return
            
        msg_type = PackMsgType(data['Type'])
        
        # 检查是否需要处理Data字段
        if msg_type == PackMsgType.下播:
            handle_live_exit()
            return
            
        if "Data" not in data:
            print(f"⚠️ 消息类型 {msg_type.name} 缺少Data字段")
            return
            
        try:
            data_dict = json.loads(data['Data'])
            
            # 消息处理映射表
            handlers = {
                PackMsgType.弹幕消息: handle_danmaku,
                PackMsgType.点赞消息: handle_dianzanku,
                PackMsgType.进直播间: handle_userentry,
                PackMsgType.关注消息: handle_follow,
                PackMsgType.礼物消息: handle_gift,
                PackMsgType.直播间统计: handle_statistics,
                PackMsgType.粉丝团消息: handle_fansclub,
                PackMsgType.直播间分享: handle_share,
            }
            
            # 分发消息到相应处理器
            if msg_type in handlers:
                handlers[msg_type](data_dict)
                
        except json.JSONDecodeError:
            print(f"⚠️ 无法解析Data字段内容：{data['Data'][:100]}...")
            
    except json.JSONDecodeError:
        print(f"⚠️ 无效的JSON格式: {message[:100]}...")
    except Exception as e:
        print(f"❌ 消息处理错误: {str(e)}")

async def connect_and_print() -> None:
    """连接到WebSocket服务器并处理接收到的消息"""
    uri = "ws://127.0.0.1:8888"
    
    while True:
        try:
            print(f"正在连接到服务器 {uri}...")
            async with websockets.connect(uri, ping_interval=None) as websocket:
                print(f"✅ 已成功连接到服务器 {uri}")
                
                while True:
                    message = await websocket.recv()
                    await process_message(message)
                    
        except websockets.exceptions.ConnectionClosed as e:
            print(f"⚠️ 与服务器的连接已关闭: {e}")
        except ConnectionRefusedError:
            print(f"❌ 无法连接到服务器 {uri}，5秒后重试...")
        except Exception as e:
            print(f"❌ 发生错误: {str(e)}")
        
        # 连接断开后等待重连
        await asyncio.sleep(5)
        print("正在尝试重新连接...")

# 程序入口
if __name__ == "__main__":
    print("启动抖音直播消息监听...")
    asyncio.run(connect_and_print())
