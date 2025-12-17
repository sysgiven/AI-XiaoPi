using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;
using BarrageGrab.Modles.JsonEntity;
using NLog;

namespace BarrageGrab
{
    public static class Logger
    {
        private static NLog.Config.ISetupBuilder builder;

        private static NLog.Logger logger;

        static Logger()
        {
            Assembly assembly = Assembly.GetExecutingAssembly();
            //读取嵌入式资源文件
            var resourceName = assembly.GetManifestResourceNames().FirstOrDefault(s => s.EndsWith("nlog.config"));
            if (resourceName == null)
            {
                throw new Exception("nlog.config 嵌入式资源不存在");
            }

            builder = LogManager.Setup().LoadConfigurationFromAssemblyResource(assembly, resourceName);
            logger = builder.GetLogger("*");
        }

        public static void PrintColor(string message, ConsoleColor foreground = ConsoleColor.White)
        {                      
            var color = Console.ForegroundColor;
            Console.ForegroundColor = foreground;
            Console.WriteLine(message);
            Console.ForegroundColor = color;
        }

        // 记录日志方法
        public static void LogTrace(string message)
        {
            logger.Trace(message);
        }

        public static void LogDebug(string message)
        {
            logger.Debug(message);
        }

        public static void LogInfo(string message)
        {
            logger.Info(message);
        }

        public static void LogWarn(string message)
        {
            logger.Warn(message);
        }

        public static void LogError(string message)
        {
            var color = Console.ForegroundColor;
            logger.Error(message);
        }

        public static void LogError(Exception ex, string message)
        {
            var color = Console.ForegroundColor;
            logger.Error(ex, message);
        }

        public static void LogFatal(string message)
        {
            var color = Console.ForegroundColor;
            logger.Fatal(message);
        }

        public static void LogFatal(Exception ex, string message)
        {
            var color = Console.ForegroundColor;
            logger.Fatal(ex, message);
        }

        /// <summary>
        /// 写入弹幕日志
        /// </summary>
        /// <param name="type">弹幕类型</param>
        /// <param name="msg">弹幕内容</param>
        public static void LogBarrage(PackMsgType type, Msg msg)
        {
            if (!AppSetting.Current.BarrageLog) return;
            if (type == PackMsgType.无) return;
            if (AppSetting.Current.LogFilter.Any() && !AppSetting.Current.LogFilter.Contains(type.GetHashCode())) return;

            try
            {
                var dir = Path.Combine(AppContext.BaseDirectory, "logs", "弹幕日志");
                var room = AppRuntime.RoomCaches.GetCachedWebRoomInfo(msg.RoomId.ToString());
                if (room == null) return;
                var date = DateTime.Now.ToString("yyyy年MM月dd日直播");
                var nickName = SafePathString(room?.Owner?.Nickname ?? "-1");
                dir = Path.Combine(dir, $"({room.WebRoomId}){nickName}", date, "场次" + msg.RoomId.ToString());
                if (!Directory.Exists(dir))
                {
                    Directory.CreateDirectory(dir);
                }
                var path = Path.Combine(dir, type + ".txt");
                if (!File.Exists(path))
                {
                    File.Create(path).Close();
                }
                var writer = new StreamWriter(path, true, Encoding.UTF8);
                var line = LogText(msg, type);
                writer.WriteLine(line);
                writer.Close();
            }
            catch (Exception ex)
            {
                LogWarn("弹幕日志写入失败，" + ex.Message);
                return;
            }
        }

        /// <summary>
        /// 将字符串中的特殊字符转换为'?'，使其安全用于文件路径
        /// </summary>
        /// <param name="input">输入字符串</param>
        /// <returns>处理后的安全字符串</returns>
        public static string SafePathString(string input)
        {
            //在文件系统中，以下字符通常不允许用于文件名：\ / : * ? " < > |
            if (string.IsNullOrEmpty(input))
                return input;

            // 文件系统中不允许的字符
            char[] invalidChars = Path.GetInvalidFileNameChars().Concat(Path.GetInvalidPathChars()).Distinct().ToArray();

            StringBuilder result = new StringBuilder(input.Length);
            foreach (char c in input)
            {
                result.Append(invalidChars.Contains(c) ? '？' : c);
            }

            return result.ToString();
        }



        private static string LogText(Msg msg, PackMsgType barType)
        {
            var rinfo = AppRuntime.RoomCaches.GetCachedWebRoomInfo(msg.RoomId.ToString());
            var text = $"{DateTime.Now.ToString("HH:mm:ss")} [{barType}]";

            if (msg.User != null)
            {
                text += $" [{msg.User?.GenderToString()}] ";
            }

            ConsoleColor color = AppSetting.Current.ColorMap[barType].Item1;
            var append = msg.Content;
            switch (barType)
            {
                case PackMsgType.弹幕消息: append = $"{msg?.User?.Nickname}: {msg.Content}"; break;
                case PackMsgType.下播: append = $"直播已结束"; break;
                default: break;
            }

            text += append;
            return text;
        }

        /// <summary>
        /// 写入弹幕抓包日志
        /// </summary>
        /// <param name="group">分组名</param>
        /// <param name="name">包名</param>
        /// <param name="buff">数据内容</param>
        /// <param name="maxCount">分组下最大存储包数量</param>
        public static void LogBarragePack(string group, string name, byte[] buff, int maxCount = 5)
        {
            if (buff.Length <= 10) return;
            if (group.IsNullOrWhiteSpace()) return;
            if (name.IsNullOrWhiteSpace()) return;
            var filename = name + ".bin";
            var dir = Path.Combine(AppContext.BaseDirectory, "logs", "弹幕包解析", group);
            var fullPath = Path.Combine(dir, filename);

            try
            {
                //获取该文件在该目录下的数量
                var fiels = Directory.GetFiles(dir, filename);
                var count = fiels.Length;
                if (count > 0)
                {
                    filename = $"{name}({count}).bin";
                    fullPath = Path.Combine(dir, filename);
                }
                File.WriteAllBytes(fullPath, buff);

                if (++count > maxCount)
                {
                    //删除最早的文件
                    var first = fiels.Select(s => new FileInfo(s)).OrderBy(o => o.CreationTime).FirstOrDefault();
                    File.Delete(first.FullName);
                }
            }
            catch (Exception ex)
            {
                Logger.LogWarn("写入包日志时失败，错误信息:" + ex.Message);
            }
        }
    }
}
