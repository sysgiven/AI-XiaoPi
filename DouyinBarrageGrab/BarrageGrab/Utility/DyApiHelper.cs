using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using BarrageGrab.Modles;
using BarrageGrab.Modles.ProtoEntity;
using Newtonsoft.Json.Linq;
using Org.BouncyCastle.Asn1.Cmp;
using Org.BouncyCastle.Asn1.Crmf;

namespace BarrageGrab
{
    /// <summary>
    /// 抖音服务
    /// </summary>
    internal class DyApiHelper
    {
        /// <summary>
        /// 获取直播礼物列表
        /// </summary>
        /// <returns></returns>
        public static async Task<WebCastGiftPack> GetGifts()
        {
            var url = "https://live.douyin.com/webcast/gift/list/";
            var qparam = new Dictionary<string, string>()
            {
                {"device_platform","webapp"},
                {"aid","6383"},
            };

            var client = new HttpClient();
            client.DefaultRequestHeaders.Add("referer", "https://live.douyin.com/405518163654");
            client.DefaultRequestHeaders.Add("authority", "www.douyin.com");

            var builder = new UriBuilder(url);
            builder.Query = string.Join("&", qparam.Select(x => $"{x.Key}={x.Value}"));

            try
            {
                var response = await client.GetAsync(builder.Uri);
                if (!response.IsSuccessStatusCode)
                {
                    Logger.LogError($"响应失败: {response.StatusCode}");
                    return null;
                }
                var json = await response.Content.ReadAsStringAsync();
                var jobj = JObject.Parse(json);
                var data = jobj?["data"].ToObject<WebCastGiftPack>();
                return data;
            }
            catch (Exception ex)
            {
                Logger.LogError($"礼物信息从服务器请求失败: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// 获取房间信息，通过原生接口
        /// </summary>
        /// <param name="webRoomid">web直播间号</param>
        /// <param name="user">账号凭据</param>
        /// <param name="proxy">查询代理</param>
        /// <returns></returns>
        public static async Task<RoomInfo> GetRoomInfoForApi(string webRoomid, string cookie)
        {
            string url = "https://live.douyin.com/webcast/room/web/enter/";

            var client = new HttpClient();


            var uri = new UriBuilder(url);
            var dict = new Dictionary<string, string>();
            dict.Set("aid", "6383");
            dict.Set("live_id", "1");
            dict.Set("app_name", "douyin_web");
            dict.Set("device_platform", "web");
            dict.Set("language", "zh-CN");
            dict.Set("cookie_enabled", "true");
            dict.Set("enter_from", "page_refresh");
            dict.Set("web_rid", webRoomid);
            //dict.Set("room_id_str", roomid);
            dict.Set("enter_source", "");
            dict.Set("is_need_double_stream", "false");
            dict.Set("insert_task_id", "");
            dict.Set("live_reason", "");
            dict.Set("browser_language", "zh-CN");
            dict.Set("browser_platform", "Win32");
            dict.Set("browser_name", "Edge");
            dict.Foreach(f => uri.AddQueryParam(f.Key, f.Value));

            url = uri.Uri.ToString();

            var request = new HttpRequestMessage(HttpMethod.Get, url);
            request.Headers.Add("Accept", "application/json, text/plain, */*");
            request.Headers.Add("Cache-Control", "no-cache");
            request.Headers.Add("Referer", $"https://live.douyin.com/{webRoomid}");
            request.Headers.Add("Host", "live.douyin.com");
            request.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0");
            request.Headers.Add("Cookie", cookie);

            var rsp = await client.SendAsync(request);
            if (rsp == null || rsp.StatusCode != System.Net.HttpStatusCode.OK)
            {
                return null;
            }

            var buff = rsp.Content.ReadAsByteArrayAsync();
            var result = Encoding.UTF8.GetString(buff.Result);
            RoomInfo dto;
            var res = RoomInfo.TryParseRoomEnterResponse(result, out dto);
            int code = res.Item1;
            string msg = res.Item2;
            if (code == 0)
            {
                dto.LiveUrl = $"https://live.douyin.com/{webRoomid}";
                dto.WebRoomId = webRoomid;
                AppRuntime.RoomCaches.AddRoomInfoCache(dto);
                Logger.LogInfo($"{dto.Owner.Nickname ?? dto.WebRoomId ?? dto.RoomId} 的直播间信息已添加到缓存");
            }
            else
            {
                return null;
            }

            return dto;
        }
    }
}
