from enum import Enum, IntEnum
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field

# 枚举类型定义
class PackMsgType(IntEnum):
    """消息类型枚举"""
    无 = 0
    弹幕消息 = 1
    点赞消息 = 2
    进直播间 = 3
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
    
    def to_string(self) -> str:
        """将性别枚举转换为中文字符串"""
        if self == Gender.男:
            return "男"
        elif self == Gender.女:
            return "女"
        else:
            return "妖"

class FansclubType(IntEnum):
    """粉丝团消息类型"""
    无 = 0
    粉丝团升级 = 1
    加入粉丝团 = 2

class ShareType(IntEnum):
    """直播间分享目标"""
    未知 = 0
    微信 = 1
    朋友圈 = 2
    微博 = 3
    QQ空间 = 4
    QQ = 5
    抖音好友 = 112

class EnterType(IntEnum):
    """观众的进入方式"""
    正常进入 = 0
    通过分享进入 = 6

# 数据类定义
@dataclass
class FansClubInfo:
    """粉丝团信息"""
    ClubName: str = ""
    Level: int = 0

@dataclass
class MsgUser:
    """用户信息"""
    Id: int = 0
    IsAdmin: bool = False
    IsAnchor: bool = False
    ShortId: int = 0
    DisplayId: str = ""
    Nickname: str = "匿名用户"
    Level: int = 0
    PayLevel: int = 0
    Gender: Gender = Gender.未知
    HeadImgUrl: str = ""
    SecUid: str = ""
    FansClub: Optional[FansClubInfo] = None
    FollowerCount: int = 0
    FollowStatus: int = 0
    FollowingCount: int = 0
    
    def gender_to_string(self) -> str:
        """返回性别的中文表示"""
        return Gender(self.Gender).to_string()

@dataclass
class RoomAnchorInfo:
    """直播间主播信息"""
    UserId: str = ""
    SecUid: str = ""
    Nickname: str = ""
    HeadUrl: str = ""
    FollowStatus: int = 0

@dataclass
class Msg:
    """基础消息类"""
    MsgId: int = 0
    User: MsgUser = field(default_factory=MsgUser)
    Owner: Optional[RoomAnchorInfo] = None  # 修正字段名称
    Content: str = ""
    RoomId: str = ""
    WebRoomId: str = ""
    RoomTitle: str = ""
    IsAnonymous: bool = False
    Appid: str = ""

@dataclass
class LikeMsg(Msg):
    """点赞消息"""
    Count: int = 0
    Total: int = 0

@dataclass
class GiftMsg(Msg):
    """礼物消息"""
    GiftId: int = 0
    GiftName: str = ""
    GroupId: int = 0
    GiftCount: int = 0
    RepeatCount: int = 0
    DiamondCount: int = 0  # 抖币价格
    Combo: bool = False  # 该礼物是否可连击
    ImgUrl: str = ""  # 礼物图片地址
    ToUser: Optional[MsgUser] = None  # 送礼目标(连麦直播间有用)
    GiftValue: int = 0  # 在原Python代码中使用的礼物价值字段

@dataclass
class MemberMessage(Msg):
    """进入直播间消息"""
    CurrentCount: int = 0
    EnterTipType: int = 0

@dataclass
class UserSeqMsg(Msg):
    """直播间统计消息"""
    OnlineUserCount: int = 0
    TotalUserCount: int = 0
    TotalUserCountStr: str = "0"
    OnlineUserCountStr: str = "0"

@dataclass
class FansclubMsg(Msg):
    """粉丝团消息"""
    Type: int = 0  # 粉丝团消息类型，升级1，加入2
    Level: int = 0  # 粉丝团等级
    FansClubName: str = ""  # 粉丝团名称

@dataclass
class ShareMessage(Msg):
    """直播间分享"""
    ShareType: ShareType = ShareType.未知

# 全局统计数据类
@dataclass
class LiveStats:
    """直播间统计数据"""
    total_likes: int = 0
    total_users: int = 0
    male_users: int = 0
    female_users: int = 0
    
    def reset(self) -> None:
        """重置统计数据"""
        self.total_likes = 0
        self.total_users = 0
        self.male_users = 0
        self.female_users = 0
