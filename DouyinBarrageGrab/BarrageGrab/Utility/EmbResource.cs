using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;

namespace BarrageGrab
{
    /// <summary>
    /// 资源文件
    /// </summary>
    public static class EmbResource
    {
        static Dictionary<string,string> cache = new Dictionary<string, string>();

        /// <summary>
        /// 获取 嵌入式资源文件内容
        /// </summary>
        /// <param name="fileName"></param>
        /// <returns></returns>
        /// <exception cref="Exception"></exception>
        public static string GetFileContent(string fileName)
        {
            if(cache.ContainsKey(fileName))
            {
                return cache[fileName];
            }

            Assembly assembly = Assembly.GetExecutingAssembly();
            //读取嵌入式资源文件
            var resourceName = assembly.GetManifestResourceNames().FirstOrDefault(s => s.EndsWith(fileName));
            if (resourceName == null)
            {
                throw new Exception($"{fileName} 嵌入式资源不存在");
            }

            using (Stream stream = assembly.GetManifestResourceStream(resourceName))
            {
                using (StreamReader reader = new StreamReader(stream,Encoding.UTF8))
                {
                    var text = reader.ReadToEnd();
                    cache.Add(fileName, text);
                    return text;
                }
            }
        }
    }
}
