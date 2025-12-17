using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using HtmlAgilityPack;
using IWshRuntimeLibrary;
using Microsoft.Win32;
using Newtonsoft.Json;
using File = System.IO.File;

namespace BarrageGrab
{
    public static class LiveCompanHelper
    {
        /// <summary>
        /// 获取抖音直播伴侣的exe路径
        /// </summary>
        /// <returns></returns>
        public static string GetExePath()
        {
            string appName = "直播伴侣";
            appName = Path.GetFileNameWithoutExtension(appName);
            string exePath = "";

            //从卸载列表中查找
            try
            {
                // 打开注册表中的卸载信息节点
                RegistryKey uninstallNode = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall");

                if (uninstallNode != null)
                {
                    // 遍历所有的子键（每个子键代表一个已安装的程序的卸载信息）
                    foreach (string subKeyName in uninstallNode.GetSubKeyNames())
                    {
                        RegistryKey subKey = uninstallNode.OpenSubKey(subKeyName);
                        var displayName = subKey?.GetValue("DisplayName")?.ToString() ?? "";

                        if (!displayName.Contains(appName)) continue;
                        string uninstallString = subKey?.GetValue("UninstallString")?.ToString();
                        if (uninstallString.IsNullOrWhiteSpace()) continue;

                        //"D:\Program Files (x86)\webcast_mate\Uninstall 直播伴侣.exe" /allusers
                        //正则取出""中间的内容
                        var match = Regex.Match(uninstallString, "\"(.+?)\"");
                        if (match.Success)
                        {
                            string uninstallPath = match.Groups[1].Value;
                            string dir = Path.GetDirectoryName(uninstallPath);
                            string exe = Path.Combine(dir, $"{appName}.exe");
                            if (File.Exists(exe))
                            {
                                exePath = exe;
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                // 发生异常时，可能是注册表访问出错，记录错误信息
                Logger.LogError(ex, $"Error checking for Live Companion installation path: {ex.Message}");
            }

            //从 C:\ProgramData\Microsoft\Windows\Start Menu\Programs 中查找
            string startMenuPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonStartMenu), "Programs");
            var findFiles = Directory.GetFiles(startMenuPath, $"{appName}.lnk", SearchOption.AllDirectories);
            if (findFiles.Length > 0)
            {
                exePath = GetShortcutTarget(findFiles[0]);
            }

            var fileName = Path.GetFileName(exePath);

            //判断是否是 版本选择器
            if (fileName.Contains("Launcher"))
            {
                var dir = Path.GetDirectoryName(exePath);
                //读取目录下 launcher_config.json
                var launcherConfigPath = Path.Combine(dir, "launcher_config.json");
                if (!File.Exists(launcherConfigPath))
                {
                    throw new Exception("未找到直播伴侣版本选择器的 launcher_config.json 文件");
                }
                var json = File.ReadAllText(launcherConfigPath, Encoding.UTF8);
                var jobj = JsonConvert.DeserializeObject<dynamic>(json);
                string curPath = jobj.cur_path;
                exePath = Path.Combine(dir, curPath, "直播伴侣.exe");
            }

            // 如果没有找到相关信息，则返回空字符串
            return exePath;
        }

        /// <summary>
        /// 获取 .lnk 文件的目标路径
        /// </summary>
        /// <param name="shortcutPath">快捷方式文件路径</param>
        /// <returns>目标路径</returns>
        private static string GetShortcutTarget(string shortcutPath)
        {
            if (string.IsNullOrEmpty(shortcutPath))
            {
                throw new ArgumentException("快捷方式路径不能为空", nameof(shortcutPath));
            }

            var processStartInfo = new ProcessStartInfo
            {
                FileName = "powershell",
                Arguments = $"-command \"$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('{shortcutPath}'); $Shortcut.TargetPath\"",
                RedirectStandardOutput = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            try
            {
                using (var process = Process.Start(processStartInfo))
                {
                    if (process == null)
                    {
                        throw new InvalidOperationException("无法启动 PowerShell 进程");
                    }

                    using (var reader = process.StandardOutput)
                    {
                        string result = reader.ReadToEnd();
                        process.WaitForExit();
                        return result.Trim();
                    }
                }
            }
            catch (Exception ex)
            {
                throw new Exception($"powershell 获取快捷方式目标路径失败，错误信息:{ex.Message}", ex);
            }
        }

        /// <summary>
        /// 初始化直播伴侣环境
        /// </summary>
        public static void SwitchSetup()
        {
            if (!AppSetting.Current.LiveCompanHookSwitch) return;
            var exePath = GetExePath();
            if (string.IsNullOrEmpty(exePath))
            {
                Logger.LogWarn("未找到直播伴侣.exe文件，跳过环境设置");
                return;
            }

            //设置index.js
            var indexJsPath = Path.Combine(Path.GetDirectoryName(exePath), "resources", "app", "index.js");
            Logger.LogInfo($"正在配置 " + indexJsPath);

            if (!File.Exists(indexJsPath))
            {
                throw new Exception("未找到直播伴侣的index.js文件");
            }
            var indexJs = File.ReadAllText(indexJsPath, Encoding.UTF8);

            CheckBackFile(indexJsPath);
            var newjs = SetIndexJsContent(indexJs);
            if (newjs != indexJs && !newjs.IsNullOrWhiteSpace())
            {
                File.WriteAllText(indexJsPath, newjs);
            }

            Logger.LogInfo("直播伴侣环境初始化完成");
        }

        //获取Ink快捷方式的目标路径
        private static string GetInkTargetPath(string shortcutPath)
        {
            // 创建 Windows Script Host 对象
            WshShell shell = new WshShell();

            // 使用 IWshShortcut 接口加载 .ink 文件
            IWshShortcut shortcut = (IWshShortcut)shell.CreateShortcut(shortcutPath);

            // 获取目标路径
            string targetPath = shortcut.TargetPath;

            return targetPath;
        }

        //检测备份文件
        private static void CheckBackFile(string filePath)
        {
            if (!File.Exists(filePath)) return;

            var bakPath = filePath + ".bak";
            if (!File.Exists(bakPath))
            {
                //拷贝一份备份
                File.Copy(filePath, bakPath);
                Logger.LogInfo($"已备份 {filePath} -> {bakPath}");
            }
        }

        //设置index.js内容
        private static string SetIndexJsContent(string content)
        {
            //检测注入代理
            var mineProxyHost = $"127.0.0.1:{AppSetting.Current.ProxyPort},direct://";
            SetSwitch("proxy-server", mineProxyHost, ref content);

            //移除文件损坏检测校验
            var checkReg = new Regex(@"if\(\w{1,2}\(\w\),!\w\.ok\)");
            if (checkReg.IsMatch(content))
            {
                content = checkReg.Replace(content, "if(false)");
                Logger.LogInfo($"直播伴侣文件改动检测点1已拦截");
            }


            checkReg = new Regex(@"if\(\(0,\w.integrityCheckReport\)\(\w\),!\w\.ok\)");
            if (checkReg.IsMatch(content))
            {
                content = checkReg.Replace(content, "if(false)");
                Logger.LogInfo($"直播伴侣文件改动检测点2已拦截");
            }

            return content;
        }

        //添加 electron 启动参数
        private static void SetSwitch(string name, string value, ref string content)
        {
            if (name.IsNullOrWhiteSpace()) return;

            //检测注入
            var proxyReg = new Regex($@"(?<varname>\w+)\.commandLine\.appendSwitch\(""{name}"",""(?<value>[^""]*)""\)");
            var proxyMatch = proxyReg.Match(content);
            //检测到已经存在配置，则更新参数值
            if (proxyMatch.Success)
            {
                var matchValue = proxyMatch.Groups["value"].Value;
                if (value != matchValue)
                {
                    content = proxyReg.Replace(content, $@"${{varname}}.commandLine.appendSwitch(""{name}"",""{value}"")");
                    Logger.LogInfo($"直播伴侣成功覆盖启动参数  [{name}] = [{value}]");
                }
            }
            //否则添加新的配置
            else
            {
                var nosandboxReg = new Regex(@"(?<varname>\w+)\.commandLine\.appendSwitch\(""no-sandbox""\)");
                var match = nosandboxReg.Match(content);
                if (match.Success)
                {
                    var newvalue = $@"{match.Groups["varname"].ToString()}.commandLine.appendSwitch(""{name}"",""{value}""),";
                    content = content.Insert(match.Index, newvalue);
                    Logger.LogInfo($"直播伴侣成功添加启动参数  [{name}] = [{value}]");
                }
            }
        }

        private static void SetInnerText(HtmlNode node, string text)
        {
            node.InnerHtml = "";
            var textNode = node.OwnerDocument.CreateTextNode(text);
            node.AppendChild(textNode);
        }
    }
}
