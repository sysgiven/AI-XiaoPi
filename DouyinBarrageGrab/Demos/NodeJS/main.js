/**
 * 抖音直播间消息处理脚本
 * 消息类型说明:
 * 1[普通弹幕]|2[点赞消息]|3[进入直播间]|4[关注消息]|5[礼物消息]|6[统计消息]|7[粉丝团消息]|8[直播间分享]|9[下播]
 * 
 * 全局统计变量:
 * Live_Total - 本场点赞数
 * Live_user  - 本场总观看人数
 * Live_man   - 本场男生人数
 * Live_woman - 本场女生人数
 */

const WebSocket = require('ws');
const chalk = require('chalk');
const { PackMsgType, Gender, LiveStats } = require('./entities');
const { MessageParser } = require('./parsers');

// 颜色定义
const COLOR_MAP = {
    [PackMsgType.弹幕消息]: chalk.cyan,       // 青色
    [PackMsgType.点赞消息]: chalk.yellow,     // 黄色
    [PackMsgType.进直播间]: chalk.green,      // 绿色
    [PackMsgType.关注消息]: chalk.magenta,    // 洋红色
    [PackMsgType.礼物消息]: chalk.red,        // 红色
    [PackMsgType.直播间统计]: chalk.blue,     // 蓝色
    [PackMsgType.粉丝团消息]: chalk.blue.bright, // 浅蓝色
    [PackMsgType.直播间分享]: chalk.magenta.bright, // 浅洋红色
    [PackMsgType.下播]: chalk.red,            // 红色
};

// 初始化统计对象
const liveStats = new LiveStats();

/**
 * 返回当前时间戳，格式：HH:MM:SS
 * @returns {string} 格式化的时间戳
 */
function getTimestamp() {
    const now = new Date();
    return now.toTimeString().split(' ')[0];
}

/**
 * 打印带颜色的消息
 * @param {number} msgType - 消息类型
 * @param {string} content - 消息内容
 * @param {string} [author="未知"] - 消息来源作者
 */
function printColoredMessage(msgType, content, author = "未知") {
    const colorFunc = COLOR_MAP[msgType] || chalk.white;
    const timestamp = getTimestamp();
    const authorStr = `[${author}]`; // 使用作者信息
    console.log(colorFunc(`${timestamp} ${authorStr} ${content}`));
}

/**
 * 统一获取消息所属的主播/房间信息
 * @param {Object} msg - 解析后的消息对象
 * @returns {string} 主播昵称或房间ID
 */
function getMsgOwner(msg) {
    if (msg && msg.Owner && msg.Owner.Nickname) {
        return msg.Owner.Nickname;
    } else if (msg && msg.WebRoomId) {
        return msg.WebRoomId;
    } else if (msg && msg.RoomId) {
        return msg.RoomId;
    }
    return "未知";
}

/**
 * 处理用户发送的弹幕消息
 * @param {Object} dataDict - 弹幕消息数据
 */
function handleDanmaku(dataDict) {
    const msg = MessageParser.parseDanmaku(dataDict);
    const genderStr = msg.User.genderToString();
    const content = `[弹幕消息] [${genderStr}] ${msg.User.Nickname}: ${msg.Content}`;
    const author = getMsgOwner(msg);
    printColoredMessage(PackMsgType.弹幕消息, content, author);
}

/**
 * 处理用户点赞消息并更新全局统计
 * @param {Object} dataDict - 点赞消息数据
 */
function handleDianzanku(dataDict) {
    const likeMsg = MessageParser.parseLike(dataDict);
    liveStats.total_likes = likeMsg.Total;
    const genderStr = likeMsg.User.genderToString();
    const content = `[点赞消息] [${genderStr}] ${likeMsg.User.Nickname} 为主播点了${likeMsg.Count}个赞, 总点赞${likeMsg.Total}`;
    const author = getMsgOwner(likeMsg);
    printColoredMessage(PackMsgType.点赞消息, content, author);
}

/**
 * 处理用户进入直播间的消息，并根据性别更新统计
 * @param {Object} dataDict - 进入直播间消息数据
 */
function handleUserentry(dataDict) {
    const memberMsg = MessageParser.parseMember(dataDict);
    
    // 根据性别更新全局计数
    if (memberMsg.User.Gender === Gender.男) {
        liveStats.male_users += 1;
    } else if (memberMsg.User.Gender === Gender.女) {
        liveStats.female_users += 1;
    }
    
    const genderStr = memberMsg.User.genderToString();
    const content = `[进直播间] [${genderStr}] ${memberMsg.User.Nickname} $来了 直播间人数:${memberMsg.CurrentCount}`;
    const author = getMsgOwner(memberMsg);
    printColoredMessage(PackMsgType.进直播间, content, author);
}

/**
 * 处理用户关注主播的消息
 * @param {Object} dataDict - 关注消息数据
 */
function handleFollow(dataDict) {
    try {
        const userNickname = dataDict.User?.Nickname || "匿名用户";
        const gender = dataDict.User?.Gender || 0;
        const genderStr = Gender.toString(gender);
        const content = `[关注消息] [${genderStr}] ${userNickname} 关注了主播`;
        const author = getMsgOwner(dataDict);
        printColoredMessage(PackMsgType.关注消息, content, author);
    } catch (e) {
        console.log(`处理关注消息出错: ${e.message}`);
    }
}

/**
 * 处理用户赠送礼物的消息
 * @param {Object} dataDict - 礼物消息数据
 */
function handleGift(dataDict) {
    try {
        const userNickname = dataDict.User?.Nickname || "匿名用户";
        const gender = dataDict.User?.Gender || 0;
        const genderStr = Gender.toString(gender);
        const giftName = dataDict.GiftName || "未知礼物";
        const giftCount = dataDict.GiftCount || 1;
        const giftValue = dataDict.GiftValue || 0;
        const content = `[礼物消息] [${genderStr}] ${userNickname} 送出了 ${giftCount}个${giftName}, 价值${giftValue}抖币`;
        const author = getMsgOwner(dataDict);
        printColoredMessage(PackMsgType.礼物消息, content, author);
    } catch (e) {
        console.log(`处理礼物消息出错: ${e.message}`);
    }
}

/**
 * 处理直播间统计信息
 * @param {Object} dataDict - 统计消息数据
 */
function handleStatistics(dataDict) {
    const statsMsg = MessageParser.parseStatistics(dataDict);
    liveStats.total_users = parseInt(statsMsg.TotalUserCount);
    const content = `[直播间统计] 当前直播间人数 ${statsMsg.OnlineUserCountStr}, 累计直播间人数 ${statsMsg.TotalUserCountStr}万`;
    const author = getMsgOwner(statsMsg);
    printColoredMessage(PackMsgType.直播间统计, content, author);
}

/**
 * 处理粉丝团相关消息
 * @param {Object} dataDict - 粉丝团消息数据
 */
function handleFansclub(dataDict) {
    try {
        const userNickname = dataDict.User?.Nickname || "匿名用户";
        const gender = dataDict.User?.Gender || 0;
        const genderStr = Gender.toString(gender);
        const clubName = dataDict.FansClubName || "";
        const content = `[粉丝团消息] [${genderStr}] ${userNickname} 加入了${clubName}粉丝团`;
        const author = getMsgOwner(dataDict);
        printColoredMessage(PackMsgType.粉丝团消息, content, author);
    } catch (e) {
        console.log(`处理粉丝团消息出错: ${e.message}`);
    }
}

/**
 * 处理用户分享直播间的消息
 * @param {Object} dataDict - 分享消息数据
 */
function handleShare(dataDict) {
    try {
        const userNickname = dataDict.User?.Nickname || "匿名用户";
        const gender = dataDict.User?.Gender || 0;
        const genderStr = Gender.toString(gender);
        const content = `[直播间分享] [${genderStr}] ${userNickname} 分享了直播间`;
        const author = getMsgOwner(dataDict);
        printColoredMessage(PackMsgType.直播间分享, content, author);
    } catch (e) {
        console.log(`处理分享消息出错: ${e.message}`);
    }
}

/**
 * 处理直播结束事件，显示并重置统计数据
 */
function handleLiveExit() {
    const content = `[下播] 直播结束：累计观看 ${liveStats.total_users} 人，累计点赞 ${liveStats.total_likes}，` +
                  `男生 ${liveStats.male_users} 女生 ${liveStats.female_users}`;
    printColoredMessage(PackMsgType.下播, content, "系统消息");
    liveStats.reset();
    console.log(`直播统计数据已清空~`);
}

/**
 * 处理从WebSocket接收到的单条消息
 * @param {string} message - WebSocket接收到的消息
 */
function processMessage(message) {
    try {
        const data = JSON.parse(message);
        
        if (!("Type" in data)) {
            console.log("⚠️ 收到无效消息：缺少Type字段");
            return;
        }
            
        const msgType = data.Type;
        
        // 检查是否需要处理Data字段
        if (msgType === PackMsgType.下播) {
            handleLiveExit();
            return;
        }
            
        if (!("Data" in data)) {
            console.log(`⚠️ 消息类型 ${Object.keys(PackMsgType).find(key => PackMsgType[key] === msgType)} 缺少Data字段`);
            return;
        }
            
        try {
            const dataDict = JSON.parse(data.Data);
            
            // 消息处理映射表
            const handlers = {
                [PackMsgType.弹幕消息]: handleDanmaku,
                [PackMsgType.点赞消息]: handleDianzanku,
                [PackMsgType.进直播间]: handleUserentry,
                [PackMsgType.关注消息]: handleFollow,
                [PackMsgType.礼物消息]: handleGift,
                [PackMsgType.直播间统计]: handleStatistics,
                [PackMsgType.粉丝团消息]: handleFansclub,
                [PackMsgType.直播间分享]: handleShare,
            };
            
            // 分发消息到相应处理器
            if (handlers[msgType]) {
                handlers[msgType](dataDict);
            }
                
        } catch (e) {
            if (e instanceof SyntaxError) {
                console.log(`⚠️ 无法解析Data字段内容：${data.Data.substring(0, 100)}...`);
            } else {
                throw e;
            }
        }
            
    } catch (e) {
        if (e instanceof SyntaxError) {
            console.log(`⚠️ 无效的JSON格式: ${message.substring(0, 100)}...`);
        } else {
            console.log(`❌ 消息处理错误: ${e.message}`);
        }
    }
}

/**
 * 连接到WebSocket服务器并处理接收到的消息
 */
function connectAndPrint() {
    const uri = "ws://127.0.0.1:8888";
    let reconnectInterval = 5000; // 重连间隔，单位毫秒
    
    console.log(`正在连接到服务器 ${uri}...`);
    
    function connect() {
        const ws = new WebSocket(uri);
        
        ws.on('open', function open() {
            console.log(`✅ 已成功连接到服务器 ${uri}`);
        });
        
        ws.on('message', function incoming(message) {
            processMessage(message.toString());
        });
        
        ws.on('close', function close() {
            console.log(`⚠️ 与服务器的连接已关闭`);
            console.log(`正在尝试重新连接...`);
            setTimeout(connect, reconnectInterval);
        });
        
        ws.on('error', function error(err) {
            console.log(`❌ 发生错误: ${err.message}`);
            // 错误处理由 close 事件处理重连
        });
    }
    
    connect();
}

// 程序入口
console.log("启动抖音直播消息监听...");
connectAndPrint();