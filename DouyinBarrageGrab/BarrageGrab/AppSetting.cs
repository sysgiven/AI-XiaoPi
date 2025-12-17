using System;
using System.Collections.Generic;
using System.Configuration;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using BarrageGrab.Modles.JsonEntity;
using Newtonsoft.Json.Linq;
using static System.Configuration.ConfigurationManager;

namespace BarrageGrab
{
    internal class AppSetting
    {
        private static readonly AppSetting ins = new AppSetting();

        public static AppSetting Current { get { return ins; } }

        public AppSetting()
        {
            try
            {
                ProcessFilter = AppSettings["processFilter"].Trim().Split(',');
                WsProt = int.Parse(AppSettings["wsListenPort"]);
                PrintBarrage = AppSettings["printBarrage"].ToLower() == "true";
                ProxyPort = int.Parse(AppSettings["proxyPort"]);
                PrintFilter = Enum.GetValues(typeof(PackMsgType)).Cast<int>().Where(w => w > 0).ToArray();
                PushFilter = Enum.GetValues(typeof(PackMsgType)).Cast<int>().Where(w => w > 0).ToArray();
                LogFilter = Enum.GetValues(typeof(PackMsgType)).Cast<int>().Where(w => w > 0).ToArray();
                FilterHostName = bool.Parse(AppSettings["filterHostName"].Trim());
                HostNameFilter = AppSettings["hostNameFilter"].Trim().Split(',').Where(w => !string.IsNullOrWhiteSpace(w)).ToArray();
                UsedProxy = bool.Parse(AppSettings["sysProxy"].Trim());
                ListenAny = bool.Parse(AppSettings["listenAny"].Trim());
                UpstreamProxy = AppSettings["upstreamProxy"].Trim();
                HideConsole = bool.Parse(AppSettings["hideConsole"].Trim());
                BarrageLog = bool.Parse(AppSettings["barrageFileLog"].Trim());
                ShowWindow = bool.Parse(AppSettings["showWindow"].Trim());
                AutoPause = bool.Parse(AppSettings["autoPause"].Trim());
                ForcePolling = bool.Parse(AppSettings["forcePolling"].Trim());
                PollingInterval = int.Parse(AppSettings["pollingInterval"].Trim());
                DisableLivePageScriptCache = bool.Parse(AppSettings["disableLivePageScriptCache"].Trim());
                WebRoomIds = AppSettings["webRoomIds"].Trim().Split(',').Where(w => !string.IsNullOrWhiteSpace(w)).ToArray();
                LiveCompanPath = AppSettings["liveCompanPath"].Trim();
                LiveCompanHookSwitch = bool.Parse(AppSettings["liveCompanHookSwitch"].Trim());

                ConfigComPort();
                ConfigFilter();
            }
            catch (Exception ex)
            {
                Logger.PrintColor("配置文件读取失败,请检查配置文件是否正确");
                throw ex;
            }
        }

        /// <summary>
        /// 从JSON文件加载配置
        /// </summary>
        /// <param name="jsonFilePath">JSON配置文件路径</param>
        public void LoadFromJson(string jsonFilePath = null)
        {
            if(jsonFilePath==null) jsonFilePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "appConfig.json");
            try
            {
                if(!File.Exists(jsonFilePath))
                {
                    Logger.LogError($"配置文件不存在: {jsonFilePath}");
                    return;
                }

                // 读取JSON文件内容（保留注释）
                string jsonContent = File.ReadAllText(jsonFilePath);

                // 解析JSON（Newtonsoft.Json支持JSONC格式，会自动忽略注释）
                JObject config = JObject.Parse(jsonContent);

                // 从JSON读取应用配置
                var app = config["app"];

                // 常规配置
                var general = app["general"];
                HideConsole = general["hideConsole"]?.Value<bool>() ?? false;
                ShowWindow = general["showWindow"]?.Value<bool>() ?? false;               

                // 网络配置
                var network = app["network"];
                var proxy = network["proxy"];
                ProxyPort = proxy["port"]?.Value<int>() ?? 8827;
                UsedProxy = proxy["enabled"]?.Value<bool>() ?? true;
                UpstreamProxy = proxy["upstreamAddress"]?.Value<string>() ?? string.Empty;

                var websocket = network["websocket"];
                WsProt = websocket["listenPort"]?.Value<int>() ?? 8888;
                ListenAny = websocket["listenAny"]?.Value<bool>() ?? true;

                // 过滤配置
                var filtering = app["filtering"];
                string processFilterStr = filtering["processFilter"]?.Value<string>() ?? "直播伴侣,douyin,chrome,msedge,QQBrowser,360se,firefox,2345explorer,iexplore";
                ProcessFilter = processFilterStr.Split(',');
                FilterHostName = filtering["hostNameEnabled"]?.Value<bool>() ?? true;
                string hostNameFilterStr = filtering["hostNameList"]?.Value<string>() ?? string.Empty;
                HostNameFilter = !string.IsNullOrWhiteSpace(hostNameFilterStr)
                    ? hostNameFilterStr.Split(',').Where(w => !string.IsNullOrWhiteSpace(w)).ToArray()
                    : new string[0];
                string webRoomIdsStr = filtering["webRoomIds"]?.Value<string>() ?? string.Empty;
                WebRoomIds = !string.IsNullOrWhiteSpace(webRoomIdsStr)
                    ? webRoomIdsStr.Split(',').Where(w => !string.IsNullOrWhiteSpace(w)).ToArray()
                    : new string[0];

                // 弹幕配置
                var barrage = app["barrage"];
                PrintBarrage = barrage["printEnabled"]?.Value<bool>() ?? true;
                BarrageLog = barrage["barrageFileLog"]?.Value<bool>() ?? false;
                var polling = app["barrage"]["polling"];
                ForcePolling = polling["enabled"]?.Value<bool>() ?? false;
                PollingInterval = polling["interval"]?.Value<int>() ?? 3000;
                DisableLivePageScriptCache = polling["disableScriptCache"]?.Value<bool>() ?? false;

                // 设置默认过滤器
                PrintFilter = Enum.GetValues(typeof(PackMsgType)).Cast<int>().Where(w => w > 0).ToArray();
                PushFilter = Enum.GetValues(typeof(PackMsgType)).Cast<int>().Where(w => w > 0).ToArray();
                LogFilter = Enum.GetValues(typeof(PackMsgType)).Cast<int>().Where(w => w > 0).ToArray();

                string printFilterStr = barrage["printFilter"]?.Value<string>() ?? string.Empty;
                string pushFilterStr = barrage["pushFilter"]?.Value<string>() ?? string.Empty;
                string logFilterStr = barrage["logFilter"]?.Value<string>() ?? "1,2,4,5,6,7,8";

                // 解析过滤器
                if (!string.IsNullOrWhiteSpace(printFilterStr))
                {
                    PrintFilter = printFilterStr.Split(',').Select(x => int.Parse(x)).ToArray();
                }
                if (!string.IsNullOrWhiteSpace(pushFilterStr))
                {
                    PushFilter = pushFilterStr.Split(',').Select(x => int.Parse(x)).ToArray();
                }
                if (!string.IsNullOrWhiteSpace(logFilterStr))
                {
                    LogFilter = logFilterStr.Split(',').Select(x => int.Parse(x)).ToArray();
                }

                // 直播伴侣配置
                var liveCompanion = app["liveCompanion"];
                LiveCompanPath = liveCompanion["path"]?.Value<string>() ?? string.Empty;
                LiveCompanHookSwitch = liveCompanion["hookEnabled"]?.Value<bool>() ?? false;
                AutoPause = liveCompanion["autoPause"]?.Value<bool>() ?? true;                

                // COM端口配置
                var comPort = app["comPort"];
                string comPortStr = comPort["config"]?.Value<string>() ?? string.Empty;
                if (!string.IsNullOrWhiteSpace(comPortStr))
                {
                    try
                    {
                        var spit = comPortStr.Split(':');
                        ComPort = spit[0].Trim();
                        ComBaudRate = int.Parse(spit[1].Trim());
                        ComPortSwitch = true;
                    }
                    catch (Exception ex)
                    {
                        throw new Exception("串口配置格式错误，" + ex.Message, ex);
                    }
                }

                Logger.PrintColor("已从JSON配置文件加载设置");
            }
            catch (Exception ex)
            {
                Logger.PrintColor($"从JSON加载配置失败: {ex.Message}，将尝试从App.config加载");                
            }
        }

        /// <summary>
        /// 从启动参数加载配置
        /// </summary>
        /// <param name="args">命令行参数数组</param>
        public void LoadFromCommand(string[] args)
        {
            if (args == null || args.Length == 0)
            {
                return;
            }

            Logger.PrintColor("正在从命令行参数加载配置...");

            try
            {
                for (int i = 0; i < args.Length; i++)
                {
                    string arg = args[i].ToLower().Trim();

                    // 如果参数以-或--开头，则为命令行开关
                    if (arg.StartsWith("-") || arg.StartsWith("--"))
                    {
                        string paramName = arg.TrimStart('-');
                        string paramValue = string.Empty;
                        bool switchDef = false;

                        // 检查下一个参数是否是值（不是以-开头）
                        if (i + 1 < args.Length && !(args[i + 1].StartsWith("-") || args[i + 1].StartsWith("--")))
                        {
                            paramValue = args[i + 1];
                            i++; // 跳过已处理的值参数
                        }
                        else
                        {
                            // 对于布尔开关，没有值意味着true
                            paramValue = "?";
                            switchDef = true;
                        }

                        // 根据参数名称设置相应的配置
                        switch (paramName)
                        {
                            // 网络相关配置
                            case "port":
                            case "wsport":
                            case "ws-port":
                                if (int.TryParse(paramValue, out int wsPort))
                                {
                                    WsProt = wsPort;
                                    Logger.PrintColor($"WebSocket端口设置为: {wsPort}");
                                }
                                break;

                            case "proxy-port":
                            case "proxyport":
                                if (int.TryParse(paramValue, out int proxyPort))
                                {
                                    ProxyPort = proxyPort;
                                    Logger.PrintColor($"代理端口设置为: {proxyPort}");
                                }
                                break;

                            case "upstream":
                            case "upstream-proxy":
                                UpstreamProxy = paramValue;
                                Logger.PrintColor($"上游代理设置为: {paramValue}");
                                break;

                            case "listen-any":
                            case "listenany":
                                if (switchDef) break;
                                ListenAny = ParseBool(paramValue);
                                Logger.PrintColor($"监听任意IP设置为: {ListenAny}");
                                break;

                            case "sysproxy":
                            case "sys-proxy":
                                if (switchDef) break;
                                UsedProxy = ParseBool(paramValue);
                                Logger.PrintColor($"系统代理设置为: {UsedProxy}");
                                break;

                            // 过滤相关配置
                            case "process-filter":
                            case "processfilter":
                                ProcessFilter = paramValue.Split(',');
                                Logger.PrintColor($"进程过滤器设置为: {paramValue}");
                                break;

                            case "hostname-filter":
                            case "hostnamefilter":
                                HostNameFilter = paramValue.Split(',').Where(w => !string.IsNullOrWhiteSpace(w)).ToArray();
                                Logger.PrintColor($"域名过滤器设置为: {paramValue}");
                                break;

                            case "filter-hostname":
                            case "filterhostname":
                                if (switchDef) break;
                                FilterHostName = ParseBool(paramValue);
                                Logger.PrintColor($"是否启用域名过滤设置为: {FilterHostName}");
                                break;

                            case "room-ids":
                            case "roomids":
                                WebRoomIds = paramValue.Split(',').Where(w => !string.IsNullOrWhiteSpace(w)).ToArray();
                                Logger.PrintColor($"房间ID过滤器设置为: {paramValue}");
                                break;

                            // 弹幕相关配置
                            case "print":
                            case "print-barrage":
                                if (switchDef) break;
                                PrintBarrage = ParseBool(paramValue);
                                Logger.PrintColor($"控制台打印弹幕设置为: {PrintBarrage}");
                                break;

                            case "print-filter":
                            case "printfilter":
                                if (!string.IsNullOrWhiteSpace(paramValue))
                                {
                                    PrintFilter = paramValue.Split(',').Select(x => int.Parse(x)).ToArray();
                                    Logger.PrintColor($"控制台打印过滤器设置为: {paramValue}");
                                }
                                break;

                            case "push-filter":
                            case "pushfilter":
                                if (!string.IsNullOrWhiteSpace(paramValue))
                                {
                                    PushFilter = paramValue.Split(',').Select(x => int.Parse(x)).ToArray();
                                    Logger.PrintColor($"推送过滤器设置为: {paramValue}");
                                }
                                break;

                            case "log-filter":
                            case "logfilter":
                                if (!string.IsNullOrWhiteSpace(paramValue))
                                {
                                    LogFilter = paramValue.Split(',').Select(x => int.Parse(x)).ToArray();
                                    Logger.PrintColor($"日志过滤器设置为: {paramValue}");
                                }
                                break;

                            case "barrage-log":
                            case "barragelog":
                                if (switchDef) break;
                                BarrageLog = ParseBool(paramValue);
                                Logger.PrintColor($"弹幕文件日志设置为: {BarrageLog}");
                                break;

                            // 显示和控制台相关
                            case "hide-console":
                            case "hideconsole":
                                if (switchDef) break;
                                HideConsole = ParseBool(paramValue);
                                Logger.PrintColor($"隐藏控制台设置为: {HideConsole}");
                                break;

                            case "show-window":
                            case "showwindow":
                                if (switchDef) break;
                                ShowWindow = ParseBool(paramValue);
                                Logger.PrintColor($"显示窗体设置为: {ShowWindow}");
                                break;

                            // 轮询相关配置
                            case "force-polling":
                            case "forcepolling":
                                if (switchDef) break;
                                ForcePolling = ParseBool(paramValue);
                                Logger.PrintColor($"强制轮询模式设置为: {ForcePolling}");
                                break;

                            case "polling-interval":
                            case "pollinginterval":
                                if (int.TryParse(paramValue, out int interval))
                                {
                                    PollingInterval = interval;
                                    Logger.PrintColor($"轮询间隔设置为: {interval}ms");
                                }
                                break;

                            case "disable-cache":
                            case "disablecache":
                                if (switchDef) break;
                                DisableLivePageScriptCache = ParseBool(paramValue);
                                Logger.PrintColor($"禁用脚本缓存设置为: {DisableLivePageScriptCache}");
                                break;

                            // 直播伴侣相关
                            case "auto-pause":
                            case "autopause":
                                if (switchDef) break;
                                AutoPause = ParseBool(paramValue);
                                Logger.PrintColor($"自动暂停设置为: {AutoPause}");
                                break;

                            case "livecompan-path":
                            case "livecompanpath":
                                LiveCompanPath = paramValue;
                                Logger.PrintColor($"直播伴侣路径设置为: {paramValue}");
                                break;

                            case "livecompan-hook":
                            case "livecompanhook":
                                if (switchDef) break;
                                LiveCompanHookSwitch = ParseBool(paramValue);
                                Logger.PrintColor($"直播伴侣Hook开关设置为: {LiveCompanHookSwitch}");
                                break;

                            // COM端口相关
                            case "com":
                            case "comport":
                                if (!string.IsNullOrWhiteSpace(paramValue))
                                {
                                    try
                                    {
                                        var parts = paramValue.Split(':');
                                        if (parts.Length == 2)
                                        {
                                            ComPort = parts[0].Trim();
                                            ComBaudRate = int.Parse(parts[1].Trim());
                                            ComPortSwitch = true;
                                            Logger.PrintColor($"COM端口设置为: {ComPort} 波特率: {ComBaudRate}");
                                        }
                                    }
                                    catch (Exception ex)
                                    {
                                        Logger.LogError($"COM端口配置格式错误: {ex.Message}");
                                    }
                                }
                                break;

                            // 配置文件相关
                            case "config":
                            case "jsonconfig":
                                try
                                {
                                    if (File.Exists(paramValue))
                                    {
                                        LoadFromJson();
                                        Logger.PrintColor($"已从JSON配置文件加载配置: {paramValue}");
                                    }
                                    else
                                    {
                                        Logger.LogError($"指定的配置文件不存在: {paramValue}");
                                    }
                                }
                                catch (Exception ex)
                                {
                                    Logger.LogError($"加载JSON配置文件失败: {ex.Message}");
                                }
                                break;

                            default:
                                Logger.LogWarn($"未知的命令行参数: {arg}");
                                break;
                        }
                    }
                }

                Logger.PrintColor("命令行参数配置加载完成");
            }
            catch (Exception ex)
            {
                Logger.LogError($"命令行参数解析错误: {ex.Message}");
            }
        }

        /// <summary>
        /// 解析布尔值字符串
        /// </summary>
        private bool ParseBool(string value)
        {
            if (string.IsNullOrWhiteSpace(value))
                return false;

            value = value.ToLower().Trim();

            return value == "true" || value == "1" || value == "yes" || value == "y" || value == "on";
        }

        //com串口设置
        private void ConfigComPort()
        {
            var comPort = AppSettings["comPort"];
            if (!comPort.IsNullOrWhiteSpace())
            {
                try
                {
                    var spit = comPort.Split(':');
                    ComPort = spit[0].Trim();
                    ComBaudRate = int.Parse(spit[1].Trim());
                    ComPortSwitch = true;
                }
                catch (Exception ex)
                {
                    throw new Exception("串口配置格式错误，" + ex.Message, ex);
                }
            }
        }

        //各种过滤器设置
        private void ConfigFilter()
        {
            var printFilter = AppSettings["printFilter"].Trim().ToLower();
            var pushFilter = AppSettings["pushFilter"].Trim().ToLower();
            var logFilter = AppSettings["logFilter"].Trim().ToLower();
            if (!string.IsNullOrWhiteSpace(printFilter))
            {
                if (string.IsNullOrWhiteSpace(printFilter)) PrintFilter = new int[0];
                else PrintFilter = printFilter.Split(',').Select(x => int.Parse(x)).ToArray();
            }
            if (!string.IsNullOrWhiteSpace(pushFilter))
            {
                if (string.IsNullOrWhiteSpace(pushFilter)) PushFilter = new int[0];
                else PushFilter = pushFilter.Split(',').Select(x => int.Parse(x)).ToArray();
            }
            if (!string.IsNullOrWhiteSpace(logFilter))
            {
                if (string.IsNullOrWhiteSpace(logFilter)) LogFilter = new int[0];
                else LogFilter = logFilter.Split(',').Select(x => int.Parse(x)).ToArray();
            }
        }

        public void Save()
        {
            Configuration config = ConfigurationManager.OpenExeConfiguration(ConfigurationUserLevel.None);

            config.AppSettings.Settings["wsListenPort"].Value = WsProt.ToString();
            config.AppSettings.Settings["printBarrage"].Value = PrintBarrage.ToString().ToLower();
            config.AppSettings.Settings["printFilter"].Value = string.Join("", PrintFilter);
            config.AppSettings.Settings["pushFilter"].Value = string.Join("", PushFilter);
            config.AppSettings.Settings["logFilter"].Value = string.Join("", LogFilter);
            config.AppSettings.Settings["upstreamProxy"].Value = UpstreamProxy;
            config.AppSettings.Settings["listenAny"].Value = ListenAny.ToString().ToLower();
            config.AppSettings.Settings["hideConsole"].Value = HideConsole.ToString().ToLower();
            config.AppSettings.Settings["barrageFileLog"].Value = HideConsole.ToString().ToLower();

            config.Save(ConfigurationSaveMode.Modified);
            ConfigurationManager.RefreshSection(config.AppSettings.SectionInformation.Name);
        }

        /// <summary>
        /// 弹幕颜色映射
        /// </summary>
        public Dictionary<PackMsgType, Tuple<ConsoleColor, Color>> ColorMap = new Dictionary<PackMsgType, Tuple<ConsoleColor, Color>>()
        {
            { PackMsgType.弹幕消息, Tuple.Create(ConsoleColor.White, Color.White) },
            { PackMsgType.点赞消息, Tuple.Create(ConsoleColor.Cyan, Color.Cyan) },
            { PackMsgType.进直播间, Tuple.Create(ConsoleColor.Green, Color.Green) },
            { PackMsgType.关注消息, Tuple.Create(ConsoleColor.Yellow, Color.Yellow) },
            { PackMsgType.礼物消息, Tuple.Create(ConsoleColor.Red, Color.Red) },
            { PackMsgType.直播间统计, Tuple.Create(ConsoleColor.Magenta, Color.Magenta) },
            { PackMsgType.粉丝团消息, Tuple.Create(ConsoleColor.Blue, Color.Blue) },
            { PackMsgType.直播间分享, Tuple.Create(ConsoleColor.DarkBlue, Color.DarkBlue) },
            { PackMsgType.下播, Tuple.Create(ConsoleColor.DarkCyan, Color.DarkCyan) }
        };

        /// <summary>
        /// 使用系统代理
        /// </summary>
        public bool UsedProxy { get; private set; } = true;

        /// <summary>
        /// 过滤的进程
        /// </summary>
        public string[] ProcessFilter { get; private set; }

        /// <summary>
        /// 端口号
        /// </summary>
        public int WsProt { get; set; } = 8888;

        /// <summary>
        /// true:监听在0.0.0.0，接受任意Ip连接，false:监听在127.0.0.1，仅接受本机连接
        /// </summary>
        public bool ListenAny { get; set; } = true;

        /// <summary>
        /// 控制台打印消息开关
        /// </summary>
        public bool PrintBarrage { get; set; }

        /// <summary>
        /// 代理端口
        /// </summary>
        public int ProxyPort { get; private set; } = 8827;

        /// <summary>
        /// 控制台输出过滤器
        /// </summary>
        public int[] PrintFilter { get; set; }

        /// <summary>
        /// 推送弹幕过滤器
        /// </summary>
        public int[] PushFilter { get; set; }

        /// <summary>
        /// 弹幕日志过滤器
        /// </summary>
        public int[] LogFilter { get; set; }

        /// <summary>
        /// 监听的房间号
        /// </summary>
        public string[] WebRoomIds { get; private set; } = new string[0];

        /// <summary>
        /// 使用域名过滤
        /// </summary>
        public bool FilterHostName { get; private set; } = true;

        /// <summary>
        /// 域名白名单列表
        /// </summary>
        public string[] HostNameFilter { get; private set; } = new string[0];

        /// <summary>
        /// 上游代理地址
        /// </summary>
        public string UpstreamProxy { get; set; }

        /// <summary>
        /// 隐藏控制台
        /// </summary>
        public bool HideConsole { get; set; }

        /// <summary>
        /// 弹幕日志
        /// </summary>
        public bool BarrageLog { get; set; } = false;

        /// <summary>
        /// 显示窗体
        /// </summary>
        public bool ShowWindow { get; private set; } = false;

        /// <summary>
        /// 进入直播间自动暂停播放
        /// </summary>
        public bool AutoPause { get; private set; } = false;

        /// <summary>
        /// 强制启用轮询模式获取弹幕(仅对浏览器和客户端生效)
        /// </summary>
        public bool ForcePolling { get; private set; } = false;

        /// <summary>
        /// 控制轮询间隔
        /// </summary>
        public int PollingInterval { get; private set; } = 1000;

        /// <summary>
        /// 禁用直播页面脚本缓存
        /// </summary>
        public bool DisableLivePageScriptCache { get; private set; } = true;

        /// <summary>
        /// 配置的串口
        /// </summary>
        public string ComPort { get; set; } = string.Empty;

        /// <summary>
        /// 波特率
        /// </summary>
        public int ComBaudRate { get; set; } = 9600;

        /// <summary>
        /// 是否启用串口过滤器脚本
        /// </summary>
        public bool ComPortSwitch { get; set; } = false;

        /// <summary>
        /// 直播伴侣文件位置
        /// </summary>
        public string LiveCompanPath { get; set; } = string.Empty;

        /// <summary>
        /// hook直播伴侣代理开关
        /// </summary>
        public bool LiveCompanHookSwitch { get; set; } = true;
    }
}
