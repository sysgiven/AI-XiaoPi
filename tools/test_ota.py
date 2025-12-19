"""
测试OTA接口
模拟ESP32发送OTA验证请求，获取WebSocket配置
"""

import requests
import json


def test_ota_interface(server_host="127.0.0.1", server_port=8003, device_id="test_esp32_001"):
    """
    测试OTA接口

    Args:
        server_host: 服务器地址
        server_port: HTTP服务器端口
        device_id: 设备ID
    """
    print("=" * 60)
    print("OTA 接口测试")
    print("=" * 60)
    print()

    # OTA 接口地址
    ota_url = f"http://{server_host}:{server_port}/xiaozhi/ota/"
    print(f"OTA 接口: {ota_url}")
    print(f"设备 ID: {device_id}")
    print()

    # 构建请求
    headers = {
        "device-id": device_id,
        "client-id": "test_client_001",
        "Content-Type": "application/json"
    }

    request_data = {
        "application": {
            "version": "1.0.0"
        },
        "device": {
            "model": "xiaozhi-esp32"
        }
    }

    print("发送 OTA 验证请求...")
    print(f"请求头: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    print(f"请求体: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    print()

    try:
        # 发送 POST 请求
        response = requests.post(
            ota_url,
            headers=headers,
            json=request_data,
            timeout=5
        )

        print(f"响应状态码: {response.status_code}")
        print()

        if response.status_code == 200:
            # 解析响应
            response_data = response.json()
            print("✅ OTA 验证成功!")
            print()
            print("响应数据:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            print()

            # 提取 WebSocket 地址
            if "websocket" in response_data:
                ws_url = response_data["websocket"].get("url", "")
                ws_token = response_data["websocket"].get("token", "")

                print("=" * 60)
                print("WebSocket 连接信息:")
                print("=" * 60)
                print(f"地址: {ws_url}")
                if ws_token:
                    print(f"令牌: {ws_token}")
                else:
                    print("令牌: (无需认证)")
                print()
                print("✅ ESP32 应该使用以上 WebSocket 地址进行连接")
            else:
                print("⚠️  响应中没有 websocket 配置")

            # 显示服务器时间
            if "server_time" in response_data:
                timestamp = response_data["server_time"].get("timestamp", 0)
                timezone_offset = response_data["server_time"].get("timezone_offset", 0)
                print()
                print("服务器时间:")
                print(f"  时间戳: {timestamp} ms")
                print(f"  时区偏移: {timezone_offset} 分钟")

            # 显示固件信息
            if "firmware" in response_data:
                version = response_data["firmware"].get("version", "")
                url = response_data["firmware"].get("url", "")
                print()
                print("固件信息:")
                print(f"  版本: {version}")
                if url:
                    print(f"  下载地址: {url}")
                else:
                    print(f"  下载地址: (无需更新)")

        else:
            print(f"❌ OTA 验证失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ 连接失败")
        print(f"请确保弹幕服务器正在运行，并且 HTTP 服务器监听在 {server_host}:{server_port}")
        print()
        print("启动服务器:")
        print("  cd xiaozhi-esp32-server/main/xiaozhi-server")
        print("  python danmaku_app.py")

    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        print("服务器响应时间过长，请检查服务器状态")

    except Exception as e:
        print(f"❌ 测试失败: {e}")


def test_ota_get(server_host="127.0.0.1", server_port=8003):
    """
    测试 OTA GET 接口（测试接口）

    Args:
        server_host: 服务器地址
        server_port: HTTP服务器端口
    """
    print()
    print("=" * 60)
    print("OTA GET 接口测试（测试接口）")
    print("=" * 60)
    print()

    ota_url = f"http://{server_host}:{server_port}/xiaozhi/ota/"
    print(f"OTA 接口: {ota_url}")
    print()

    try:
        response = requests.get(ota_url, timeout=5)

        if response.status_code == 200:
            print("✅ GET 请求成功")
            print(f"响应内容:\n{response.text}")
        else:
            print(f"❌ GET 请求失败，状态码: {response.status_code}")

    except Exception as e:
        print(f"❌ GET 请求失败: {e}")


if __name__ == "__main__":
    # 配置参数（根据实际情况修改）
    SERVER_HOST = "127.0.0.1"  # 服务器IP
    HTTP_PORT = 8003            # HTTP服务器端口
    DEVICE_ID = "test_esp32_001"  # 测试设备ID

    # 测试 GET 接口
    test_ota_get(SERVER_HOST, HTTP_PORT)

    # 测试 POST 接口（OTA验证）
    test_ota_interface(SERVER_HOST, HTTP_PORT, DEVICE_ID)

    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)
