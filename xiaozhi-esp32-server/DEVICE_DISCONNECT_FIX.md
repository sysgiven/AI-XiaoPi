# 硬件设备频繁断线问题修复

## 问题描述

用户报告：**硬件设备不播放音频了**

查看日志发现设备 (e4:b0:63:ca:a7:24) 每10-15秒频繁断开和重连：

```log
2025-12-16 22:53:14 - 设备已连接: e4:b0:63:ca:a7:24 (192.168.31.209), 当前设备数: 1
2025-12-16 22:53:56 - 设备已断开: e4:b0:63:ca:a7:24, 剩余设备数: 0
2025-12-16 22:53:56 - 设备已连接: e4:b0:63:ca:a7:24 (192.168.31.209), 当前设备数: 1
2025-12-16 22:54:07 - 设备已断开: e4:b0:63:ca:a7:24, 剩余设备数: 0
2025-12-16 22:54:07 - 设备已连接: e4:b0:63:ca:a7:24 (192.168.31.209), 当前设备数: 1
2025-12-16 22:54:19 - 设备已断开: e4:b0:63:ca:a7:24, 剩余设备数: 0
```

**影响**：
- 音频数据生成正常
- TTS工作正常
- 但设备频繁断线导致音频播放中断
- 当设备断开时，音频包无法发送 → 播放不完整

## 根本原因

WebSocket服务器**缺少ping/pong心跳配置**，导致连接因超时而被关闭。

### 代码分析

在 `danmaku_service.py:199-203`，WebSocket服务器创建时没有配置心跳参数：

```python
# ❌ 原代码 - 没有心跳配置
server = await websockets.serve(
    self._handle_device_connection,
    self.ws_host,
    self.ws_port
)
```

对比项目中其他正常工作的WebSocket连接（如 `test_device_client.py:87-88`，`douyin_proxy_collector.py:109-111`）：

```python
# ✅ 正确配置
async with websockets.connect(
    url,
    ping_interval=20,   # 每20秒发送ping
    ping_timeout=10,    # 等待pong响应10秒
    close_timeout=5     # 关闭时等待5秒
) as ws:
    ...
```

**分析**：
- WebSocket默认行为可能会因为长时间无数据传输而断开连接
- ESP32设备连接后只接收数据，不主动发送数据
- 服务器端没有ping/pong心跳机制，无法检测连接活性
- 导致连接因"假死"而被操作系统或中间网络设备断开

## 修复方案

在 `danmaku_service.py` 的WebSocket服务器配置中添加ping/pong心跳参数：

```python
# ✅ 修复后的代码
# 创建WebSocket服务器（配置ping/pong心跳以保持连接）
server = await websockets.serve(
    self._handle_device_connection,
    self.ws_host,
    self.ws_port,
    ping_interval=20,  # 每20秒发送ping
    ping_timeout=10,   # 等待pong响应10秒
    close_timeout=5    # 关闭连接时等待5秒
)
```

### 参数说明

- **`ping_interval=20`**：服务器每20秒向客户端发送一个ping消息
- **`ping_timeout=10`**：如果10秒内没有收到客户端的pong响应，认为连接断开
- **`close_timeout=5`**：关闭连接时，等待5秒让最后的数据传输完成

### 工作原理

1. 服务器每20秒发送ping帧到ESP32设备
2. ESP32设备自动响应pong帧（WebSocket协议标准行为）
3. 服务器收到pong响应，确认连接活跃
4. 如果10秒内未收到pong（设备真正断开或网络故障），服务器主动关闭连接并清理资源

## 预期效果

修复后，设备连接应该保持稳定：

```log
✅ 预期日志：
2025-12-16 22:53:14 - 设备已连接: e4:b0:63:ca:a7:24 (192.168.31.209), 当前设备数: 1
[音频正常播放，连接保持稳定，不再频繁断开重连]
```

### 验证方法

1. 重启服务器：
   ```bash
   python danmaku_app.py
   ```

2. 连接ESP32设备

3. 发送弹幕触发音频播放

4. 观察日志：
   - 应该不再出现频繁的"设备已断开"/"设备已连接"循环
   - 音频应该完整播放，不被中断
   - 连接应该保持稳定，除非设备真正断电或网络故障

## 相关文件

- `danmaku_server/danmaku_service.py:198-206` - WebSocket服务器配置（已修复）
- `danmaku_server/device_manager.py` - 设备连接管理（无需修改）
- `test_device_client.py:87-88` - 测试客户端配置参考

## 技术背景

### WebSocket Ping/Pong机制

WebSocket协议定义了ping/pong帧用于保活（RFC 6455）：

- **Ping帧**：由一端发送，用于检测连接活性
- **Pong帧**：接收到ping后必须响应pong
- **自动处理**：大多数WebSocket库自动处理ping/pong，应用层无需关心

### 为什么需要心跳？

1. **检测"僵尸连接"**：连接看似正常，但实际已断开（网络故障、设备故障等）
2. **保持连接活跃**：防止中间网络设备（路由器、防火墙）因超时而断开"空闲"连接
3. **及时清理资源**：快速发现真正断开的连接，释放服务器资源

### ESP32 WebSocket客户端

ESP32的WebSocket库（如Arduino WebSocket库）通常自动处理pong响应：
- 收到ping帧 → 自动发送pong帧
- 应用代码无需手动处理
- 符合WebSocket协议标准

## 总结

### 问题
❌ WebSocket服务器缺少心跳配置 → 连接超时 → 设备频繁断开 → 音频播放中断

### 根本原因
- 服务器与ESP32设备之间没有定期的数据交换
- 缺少连接活性检测机制
- 连接被误判为"空闲"而断开

### 解决方案
✅ **添加ping/pong心跳配置**：
- 服务器每20秒主动ping
- ESP32自动响应pong
- 保持连接活跃，及时检测断开

### 效果
- 🎯 设备连接保持稳定
- 🎯 音频完整播放，不被中断
- 🎯 及时发现真正的断线情况
- 🎯 提升整体系统可靠性

---

修复完成日期：2025-12-16
问题类型：WebSocket连接稳定性
修复版本：v1.0
