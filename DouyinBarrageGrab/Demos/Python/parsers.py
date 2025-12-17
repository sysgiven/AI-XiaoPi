from typing import Dict, Any, Optional
from entities import (
    MsgUser, FansClubInfo, Msg, LikeMsg, MemberMessage, UserSeqMsg, 
    Gender, GiftMsg, FansclubMsg, ShareMessage, RoomAnchorInfo, ShareType
)

# 消息解析器
class MessageParser:
    @staticmethod
    def parse_user(user_data: Dict[str, Any]) -> MsgUser:
        """解析用户数据"""
        user = MsgUser()
        if not user_data:
            return user
            
        user.Id = user_data.get("Id", 0)
        user.IsAdmin = user_data.get("IsAdmin", False)
        user.IsAnchor = user_data.get("IsAnchor", False)
        user.ShortId = user_data.get("ShortId", 0)
        user.DisplayId = user_data.get("DisplayId", "")
        user.Nickname = user_data.get("Nickname", "匿名用户")
        user.Level = user_data.get("Level", 0)
        user.PayLevel = user_data.get("PayLevel", 0)
        user.Gender = Gender(user_data.get("Gender", 0))
        user.HeadImgUrl = user_data.get("HeadImgUrl", "")
        user.SecUid = user_data.get("SecUid", "")
        user.FollowerCount = user_data.get("FollowerCount", 0)
        user.FollowStatus = user_data.get("FollowStatus", 0)
        user.FollowingCount = user_data.get("FollowingCount", 0)
        
        # 解析粉丝团信息
        if "FansClub" in user_data and user_data["FansClub"]:
            fans_club_data = user_data["FansClub"]
            user.FansClub = FansClubInfo(
                ClubName=fans_club_data.get("ClubName", ""),
                Level=fans_club_data.get("Level", 0)
            )
            
        return user
    
    @staticmethod
    def parse_anchor_info(owner_data: Dict[str, Any]) -> Optional[RoomAnchorInfo]:
        """解析主播信息"""
        if not owner_data:
            return None
            
        owner = RoomAnchorInfo()
        owner.UserId = owner_data.get("UserId", "")
        owner.SecUid = owner_data.get("SecUid", "")
        owner.Nickname = owner_data.get("Nickname", "")
        owner.HeadUrl = owner_data.get("HeadUrl", "")
        owner.FollowStatus = owner_data.get("FollowStatus", 0)
        
        return owner
    
    @staticmethod
    def parse_common_msg_fields(data: Dict[str, Any], msg: Msg) -> Msg:
        """解析通用消息字段"""
        msg.MsgId = data.get("MsgId", 0)
        msg.Content = data.get("Content", "")
        msg.RoomId = data.get("RoomId", "")
        msg.WebRoomId = data.get("WebRoomId", "")
        msg.RoomTitle = data.get("RoomTitle", "")
        msg.IsAnonymous = data.get("IsAnonymous", False)
        msg.Appid = data.get("Appid", "")
        
        # 解析用户数据
        if "User" in data and data["User"]:
            msg.User = MessageParser.parse_user(data["User"])
        
        # 解析主播数据，优先使用正确拼写的"Owner"
        if "Owner" in data and data["Owner"]:
            msg.Owner = MessageParser.parse_anchor_info(data["Owner"])
        # 如果没有"Owner"字段才考虑拼写错误的"Onwer"字段，并且确保不是字符串
        elif "Onwer" in data and data["Onwer"] and not isinstance(data["Onwer"], str):
            msg.Owner = MessageParser.parse_anchor_info(data["Onwer"])
            
        return msg
    
    @staticmethod
    def parse_danmaku(data: Dict[str, Any]) -> Msg:
        """解析弹幕消息"""
        msg = Msg()
        return MessageParser.parse_common_msg_fields(data, msg)
    
    @staticmethod
    def parse_like(data: Dict[str, Any]) -> LikeMsg:
        """解析点赞消息"""
        like_msg = LikeMsg()
        MessageParser.parse_common_msg_fields(data, like_msg)
        like_msg.Count = data.get("Count", 0)
        like_msg.Total = data.get("Total", 0)
        return like_msg
    
    @staticmethod
    def parse_member(data: Dict[str, Any]) -> MemberMessage:
        """解析进入直播间消息"""
        member_msg = MemberMessage()
        MessageParser.parse_common_msg_fields(data, member_msg)
        member_msg.CurrentCount = data.get("CurrentCount", 0)
        member_msg.EnterTipType = data.get("EnterTipType", 0)
        return member_msg
    
    @staticmethod
    def parse_gift(data: Dict[str, Any]) -> GiftMsg:
        """解析礼物消息"""
        gift_msg = GiftMsg()
        MessageParser.parse_common_msg_fields(data, gift_msg)
        gift_msg.GiftId = data.get("GiftId", 0)
        gift_msg.GiftName = data.get("GiftName", "")
        gift_msg.GroupId = data.get("GroupId", 0)
        gift_msg.GiftCount = data.get("GiftCount", 0)
        gift_msg.RepeatCount = data.get("RepeatCount", 0)
        gift_msg.DiamondCount = data.get("DiamondCount", 0)
        gift_msg.GiftValue = data.get("GiftValue", 0)  # 兼容原有代码
        gift_msg.Combo = data.get("Combo", False)
        gift_msg.ImgUrl = data.get("ImgUrl", "")
        
        # 解析接收礼物的用户
        if "ToUser" in data and data["ToUser"]:
            gift_msg.ToUser = MessageParser.parse_user(data["ToUser"])
            
        return gift_msg
    
    @staticmethod
    def parse_statistics(data: Dict[str, Any]) -> UserSeqMsg:
        """解析直播间统计消息"""
        stats_msg = UserSeqMsg()
        MessageParser.parse_common_msg_fields(data, stats_msg)
        stats_msg.OnlineUserCount = data.get("OnlineUserCount", 0)
        stats_msg.TotalUserCount = data.get("TotalUserCount", 0)
        stats_msg.TotalUserCountStr = data.get("TotalUserCountStr", "0")
        stats_msg.OnlineUserCountStr = data.get("OnlineUserCountStr", "0")
        return stats_msg
    
    @staticmethod
    def parse_fansclub(data: Dict[str, Any]) -> FansclubMsg:
        """解析粉丝团消息"""
        fansclub_msg = FansclubMsg()
        MessageParser.parse_common_msg_fields(data, fansclub_msg)
        fansclub_msg.Type = data.get("Type", 0)
        fansclub_msg.Level = data.get("Level", 0)
        fansclub_msg.FansClubName = data.get("FansClubName", "")
        return fansclub_msg
    
    @staticmethod
    def parse_share(data: Dict[str, Any]) -> ShareMessage:
        """解析直播间分享消息"""
        share_msg = ShareMessage()
        MessageParser.parse_common_msg_fields(data, share_msg)
        share_msg.ShareType = ShareType(data.get("ShareType", 0))
        return share_msg
    
    @staticmethod
    def parse_follow(data: Dict[str, Any]) -> Msg:
        """解析关注消息"""
        follow_msg = Msg()
        return MessageParser.parse_common_msg_fields(data, follow_msg)
