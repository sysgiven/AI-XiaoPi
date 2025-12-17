const { 
    MsgUser, FansClubInfo, Msg, LikeMsg, MemberMessage, UserSeqMsg, 
    Gender, GiftMsg, FansclubMsg, ShareMessage, RoomAnchorInfo, ShareType 
} = require('./entities');

/**
 * 消息解析器类
 */
class MessageParser {
    /**
     * 解析用户数据
     * @param {Object} userData - 用户数据对象
     * @returns {MsgUser} - 解析后的用户对象
     */
    static parseUser(userData) {
        const user = new MsgUser();
        if (!userData) {
            return user;
        }
        
        user.Id = userData.Id || 0;
        user.IsAdmin = userData.IsAdmin || false;
        user.IsAnchor = userData.IsAnchor || false;
        user.ShortId = userData.ShortId || 0;
        user.DisplayId = userData.DisplayId || "";
        user.Nickname = userData.Nickname || "匿名用户";
        user.Level = userData.Level || 0;
        user.PayLevel = userData.PayLevel || 0;
        user.Gender = userData.Gender || 0;
        user.HeadImgUrl = userData.HeadImgUrl || "";
        user.SecUid = userData.SecUid || "";
        user.FollowerCount = userData.FollowerCount || 0;
        user.FollowStatus = userData.FollowStatus || 0;
        user.FollowingCount = userData.FollowingCount || 0;
        
        // 解析粉丝团信息
        if (userData.FansClub) {
            const fansClubData = userData.FansClub;
            user.FansClub = new FansClubInfo({
                ClubName: fansClubData.ClubName || "",
                Level: fansClubData.Level || 0
            });
        }
        
        return user;
    }
    
    /**
     * 解析主播信息
     * @param {Object} ownerData - 主播数据对象
     * @returns {RoomAnchorInfo|null} - 解析后的主播信息对象或null
     */
    static parseAnchorInfo(ownerData) {
        if (!ownerData) {
            return null;
        }
        
        const owner = new RoomAnchorInfo({
            UserId: ownerData.UserId || "",
            SecUid: ownerData.SecUid || "",
            Nickname: ownerData.Nickname || "",
            HeadUrl: ownerData.HeadUrl || "",
            FollowStatus: ownerData.FollowStatus || 0
        });
        
        return owner;
    }
    
    /**
     * 解析通用消息字段
     * @param {Object} data - 消息数据对象
     * @param {Msg} msg - 消息对象
     * @returns {Msg} - 解析后的消息对象
     */
    static parseCommonMsgFields(data, msg) {
        msg.MsgId = data.MsgId || 0;
        msg.Content = data.Content || "";
        msg.RoomId = data.RoomId || "";
        msg.WebRoomId = data.WebRoomId || "";
        msg.Appid = data.Appid || "";
        
        // 解析用户数据
        if (data.User) {
            msg.User = MessageParser.parseUser(data.User);
        }
        
        // 解析主播数据，优先使用正确拼写的"Owner"
        if (data.Owner) {
            msg.Owner = MessageParser.parseAnchorInfo(data.Owner);
        } 
        // 如果没有"Owner"字段才考虑拼写错误的"Onwer"字段，并且确保不是字符串
        else if (data.Onwer && typeof data.Onwer !== 'string') {
            msg.Owner = MessageParser.parseAnchorInfo(data.Onwer);
        }
        
        return msg;
    }
    
    /**
     * 解析弹幕消息
     * @param {Object} data - 弹幕消息数据
     * @returns {Msg} - 解析后的弹幕消息对象
     */
    static parseDanmaku(data) {
        const msg = new Msg();
        return MessageParser.parseCommonMsgFields(data, msg);
    }
    
    /**
     * 解析点赞消息
     * @param {Object} data - 点赞消息数据
     * @returns {LikeMsg} - 解析后的点赞消息对象
     */
    static parseLike(data) {
        const likeMsg = new LikeMsg();
        MessageParser.parseCommonMsgFields(data, likeMsg);
        likeMsg.Count = data.Count || 0;
        likeMsg.Total = data.Total || 0;
        return likeMsg;
    }
    
    /**
     * 解析进入直播间消息
     * @param {Object} data - 进入直播间消息数据
     * @returns {MemberMessage} - 解析后的进入直播间消息对象
     */
    static parseMember(data) {
        const memberMsg = new MemberMessage();
        MessageParser.parseCommonMsgFields(data, memberMsg);
        memberMsg.CurrentCount = data.CurrentCount || 0;
        memberMsg.EnterTipType = data.EnterTipType || 0;
        return memberMsg;
    }
    
    /**
     * 解析礼物消息
     * @param {Object} data - 礼物消息数据
     * @returns {GiftMsg} - 解析后的礼物消息对象
     */
    static parseGift(data) {
        const giftMsg = new GiftMsg();
        MessageParser.parseCommonMsgFields(data, giftMsg);
        giftMsg.GiftId = data.GiftId || 0;
        giftMsg.GiftName = data.GiftName || "";
        giftMsg.GroupId = data.GroupId || 0;
        giftMsg.GiftCount = data.GiftCount || 0;
        giftMsg.RepeatCount = data.RepeatCount || 0;
        giftMsg.DiamondCount = data.DiamondCount || 0;
        giftMsg.GiftValue = data.GiftValue || 0;  // 兼容原有代码
        giftMsg.Combo = data.Combo || false;
        giftMsg.ImgUrl = data.ImgUrl || "";
        
        // 解析接收礼物的用户
        if (data.ToUser) {
            giftMsg.ToUser = MessageParser.parseUser(data.ToUser);
        }
        
        return giftMsg;
    }
    
    /**
     * 解析直播间统计消息
     * @param {Object} data - 直播间统计消息数据
     * @returns {UserSeqMsg} - 解析后的直播间统计消息对象
     */
    static parseStatistics(data) {
        const statsMsg = new UserSeqMsg();
        MessageParser.parseCommonMsgFields(data, statsMsg);
        statsMsg.OnlineUserCount = data.OnlineUserCount || 0;
        statsMsg.TotalUserCount = data.TotalUserCount || 0;
        statsMsg.TotalUserCountStr = data.TotalUserCountStr || "0";
        statsMsg.OnlineUserCountStr = data.OnlineUserCountStr || "0";
        return statsMsg;
    }
    
    /**
     * 解析粉丝团消息
     * @param {Object} data - 粉丝团消息数据
     * @returns {FansclubMsg} - 解析后的粉丝团消息对象
     */
    static parseFansclub(data) {
        const fansclubMsg = new FansclubMsg();
        MessageParser.parseCommonMsgFields(data, fansclubMsg);
        fansclubMsg.Type = data.Type || 0;
        fansclubMsg.Level = data.Level || 0;
        fansclubMsg.FansClubName = data.FansClubName || "";
        return fansclubMsg;
    }
    
    /**
     * 解析直播间分享消息
     * @param {Object} data - 直播间分享消息数据
     * @returns {ShareMessage} - 解析后的直播间分享消息对象
     */
    static parseShare(data) {
        const shareMsg = new ShareMessage();
        MessageParser.parseCommonMsgFields(data, shareMsg);
        shareMsg.ShareType = data.ShareType || ShareType.未知;
        return shareMsg;
    }
    
    /**
     * 解析关注消息
     * @param {Object} data - 关注消息数据
     * @returns {Msg} - 解析后的关注消息对象
     */
    static parseFollow(data) {
        const followMsg = new Msg();
        return MessageParser.parseCommonMsgFields(data, followMsg);
    }
}

module.exports = {
    MessageParser
};