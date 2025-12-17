/**
 * 消息类型枚举
 */
const PackMsgType = {
    无: 0,
    弹幕消息: 1,
    点赞消息: 2,
    进直播间: 3,
    关注消息: 4,
    礼物消息: 5,
    直播间统计: 6,
    粉丝团消息: 7,
    直播间分享: 8,
    下播: 9
};

/**
 * 性别枚举
 */
const Gender = {
    未知: 0,
    男: 1,
    女: 2,
    
    /**
     * 将性别枚举转换为中文字符串
     * @param {number} gender - 性别枚举值
     * @returns {string} 性别的中文表示
     */
    toString(gender) {
        switch(gender) {
            case this.男:
                return "男";
            case this.女:
                return "女";
            default:
                return "妖";
        }
    }
};

/**
 * 粉丝团消息类型
 */
const FansclubType = {
    无: 0,
    粉丝团升级: 1,
    加入粉丝团: 2
};

/**
 * 直播间分享目标
 */
const ShareType = {
    未知: 0,
    微信: 1,
    朋友圈: 2,
    微博: 3,
    QQ空间: 4,
    QQ: 5,
    抖音好友: 112
};

/**
 * 观众的进入方式
 */
const EnterType = {
    正常进入: 0,
    通过分享进入: 6
};

/**
 * 粉丝团信息类
 */
class FansClubInfo {
    constructor(data = {}) {
        this.ClubName = data.ClubName || "";
        this.Level = data.Level || 0;
    }
}

/**
 * 用户信息类
 */
class MsgUser {
    constructor(data = {}) {
        this.Id = data.Id || 0;
        this.IsAdmin = data.IsAdmin || false;
        this.IsAnchor = data.IsAnchor || false;
        this.ShortId = data.ShortId || 0;
        this.DisplayId = data.DisplayId || "";
        this.Nickname = data.Nickname || "匿名用户";
        this.Level = data.Level || 0;
        this.PayLevel = data.PayLevel || 0;
        this.Gender = data.Gender || Gender.未知;
        this.HeadImgUrl = data.HeadImgUrl || "";
        this.SecUid = data.SecUid || "";
        this.FansClub = null;
        this.FollowerCount = data.FollowerCount || 0;
        this.FollowStatus = data.FollowStatus || 0;
        this.FollowingCount = data.FollowingCount || 0;
    }

    /**
     * 返回性别的中文表示
     * @returns {string} 性别的中文表示
     */
    genderToString() {
        return Gender.toString(this.Gender);
    }
}

/**
 * 直播间主播信息类
 */
class RoomAnchorInfo {
    constructor(data = {}) {
        this.UserId = data.UserId || "";
        this.SecUid = data.SecUid || "";
        this.Nickname = data.Nickname || "";
        this.HeadUrl = data.HeadUrl || "";
        this.FollowStatus = data.FollowStatus || 0;
    }
}

/**
 * 基础消息类
 */
class Msg {
    constructor(data = {}) {
        this.MsgId = data.MsgId || 0;
        this.User = new MsgUser();
        this.Owner = null;
        this.Content = data.Content || "";
        this.RoomId = data.RoomId || "";
        this.WebRoomId = data.WebRoomId || "";
        this.Appid = data.Appid || "";
    }
}

/**
 * 点赞消息类
 */
class LikeMsg extends Msg {
    constructor(data = {}) {
        super(data);
        this.Count = data.Count || 0;
        this.Total = data.Total || 0;
    }
}

/**
 * 礼物消息类
 */
class GiftMsg extends Msg {
    constructor(data = {}) {
        super(data);
        this.GiftId = data.GiftId || 0;
        this.GiftName = data.GiftName || "";
        this.GroupId = data.GroupId || 0;
        this.GiftCount = data.GiftCount || 0;
        this.RepeatCount = data.RepeatCount || 0;
        this.DiamondCount = data.DiamondCount || 0;  // 抖币价格
        this.Combo = data.Combo || false;  // 该礼物是否可连击
        this.ImgUrl = data.ImgUrl || "";  // 礼物图片地址
        this.ToUser = null;  // 送礼目标(连麦直播间有用)
        this.GiftValue = data.GiftValue || 0;  // 在原Python代码中使用的礼物价值字段
    }
}

/**
 * 进入直播间消息类
 */
class MemberMessage extends Msg {
    constructor(data = {}) {
        super(data);
        this.CurrentCount = data.CurrentCount || 0;
        this.EnterTipType = data.EnterTipType || 0;
    }
}

/**
 * 直播间统计消息类
 */
class UserSeqMsg extends Msg {
    constructor(data = {}) {
        super(data);
        this.OnlineUserCount = data.OnlineUserCount || 0;
        this.TotalUserCount = data.TotalUserCount || 0;
        this.TotalUserCountStr = data.TotalUserCountStr || "0";
        this.OnlineUserCountStr = data.OnlineUserCountStr || "0";
    }
}

/**
 * 粉丝团消息类
 */
class FansclubMsg extends Msg {
    constructor(data = {}) {
        super(data);
        this.Type = data.Type || 0;  // 粉丝团消息类型，升级1，加入2
        this.Level = data.Level || 0;  // 粉丝团等级
        this.FansClubName = data.FansClubName || "";  // 粉丝团名称
    }
}

/**
 * 直播间分享类
 */
class ShareMessage extends Msg {
    constructor(data = {}) {
        super(data);
        this.ShareType = data.ShareType || ShareType.未知;
    }
}

/**
 * 直播间统计数据类
 */
class LiveStats {
    constructor() {
        this.total_likes = 0;
        this.total_users = 0;
        this.male_users = 0;
        this.female_users = 0;
    }

    /**
     * 重置统计数据
     */
    reset() {
        this.total_likes = 0;
        this.total_users = 0;
        this.male_users = 0;
        this.female_users = 0;
    }
}

module.exports = {
    PackMsgType,
    Gender,
    FansclubType,
    ShareType,
    EnterType,
    FansClubInfo,
    MsgUser,
    RoomAnchorInfo,
    Msg,
    LikeMsg,
    GiftMsg,
    MemberMessage,
    UserSeqMsg,
    FansclubMsg,
    ShareMessage,
    LiveStats
};