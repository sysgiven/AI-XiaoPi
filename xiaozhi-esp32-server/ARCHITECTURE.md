# 抖音直播弹幕AI服务器 - 架构设计文档

## 1. 项目概述

### 1.1 项目背景

基于 xiaozhi-esp32-server 开源项目进行二次开发，实现抖音直播弹幕接入AI服务器的功能。原项目支持硬件设备通过音频输入与AI交互，本项目改造为支持直播间弹幕文本输入，并将AI回复广播给所有连接的硬件设备。

### 1.2 核心目标

1. **弹幕采集**：实时采集抖音直播间弹幕消息
2. **AI处理**：使用LLM生成智能回复
3. **语音合成**：将文本回复转换为语音
4. **设备广播**：将语音广播到所有连接的硬件设备

### 1.3 技术选型

- **编程语言**: Python 3.10+
- **异步框架**: AsyncIO
- **通信协议**: WebSocket
- **LLM**: 智谱GLM、阿里通义千问等
- **TTS**: EdgeTTS、火山引擎等

## 2. 系统架构

### 2.1 整体架构

```
┌──────────────────────────────────────────────────────────────┐
│                     弹幕AI服务器                              │
│                                                               │
│  ┌─────────────────┐      ┌─────────────────┐               │
│  │ 弹幕采集模块     │ ────▶│ 消息处理模块     │               │
│  │ DouyinCollector │      │ DanmakuHandler  │               │
│  └─────────────────┘      └────────┬────────┘               │
│                                     │                         │
│                            ┌────────▼────────┐               │
│                            │   LLM处理       │               │
│                            └────────┬────────┘               │
│                                     │                         │
│                            ┌────────▼────────┐               │
│                            │   TTS合成       │               │
│                            └────────┬────────┘               │
│                                     │                         │
│                            ┌────────▼────────┐               │
│                            │  设备管理模块    │               │
│                            │ DeviceManager   │               │
│                            └────────┬────────┘               │
│                                     │                         │
└─────────────────────────────────────┼─────────────────────────┘
                                      │ WebSocket广播
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
              ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
              │  设备 1    │    │  设备 2    │    │  设备 N    │
              └───────────┘    └───────────┘    └───────────┘
```

### 2.2 模块设计

#### 2.2.1 弹幕采集模块 (douyin_collector.py)

**职责**：
- 连接到抖音直播间WebSocket
- 实时接收弹幕消息
- 解析消息格式
- 提供模拟模式用于测试

**关键类**：
- `DouyinDanmakuCollector`: 真实弹幕采集器
- `MockDouyinDanmakuCollector`: 模拟弹幕采集器

**关键方法**：
```python
async def connect() -> bool  # 建立连接
async def start()           # 开始采集
async def stop()            # 停止采集
async def _process_message() # 处理消息
```

#### 2.2.2 消息处理模块 (danmaku_handler.py)

**职责**：
- 接收弹幕消息队列
- 调用LLM生成回复
- 调用TTS合成语音
- 协调音频广播

**关键类**：
- `DanmakuHandler`: 消息处理器
- `DanmakuConnection`: 模拟连接（用于TTS回调）

**处理流程**：
```
弹幕消息 → 加入队列 → 调用LLM → 流式生成 → TTS合成 → 音频队列
```

#### 2.2.3 设备管理模块 (device_manager.py)

**职责**：
- 管理所有连接的设备
- 维护设备列表和状态
- 实现音频广播功能
- 处理设备连接/断开

**关键类**：
- `DeviceManager`: 设备管理器
- `DeviceInfo`: 设备信息数据类

**关键方法**：
```python
async def add_device()           # 添加设备
async def remove_device()        # 移除设备
async def broadcast_audio()      # 广播音频
async def cleanup_disconnected() # 清理断开设备
```

#### 2.2.4 主服务模块 (danmaku_service.py)

**职责**：
- 初始化所有组件
- 启动WebSocket服务器
- 协调各模块工作
- 处理生命周期管理

**关键类**：
- `DanmakuService`: 主服务类

**初始化流程**：
```
加载配置 → 初始化LLM/TTS → 创建设备管理器 → 创建消息处理器
→ 创建弹幕采集器 → 启动WebSocket服务器 → 启动所有任务
```

## 3. 数据流设计

### 3.1 弹幕处理流程

```
1. 抖音直播间
   │
   │ WebSocket
   ▼
2. DouyinCollector (接收弹幕)
   │
   │ 回调函数
   ▼
3. DanmakuService (_on_danmaku_message)
   │
   │ 加入队列
   ▼
4. DanmakuHandler (异步处理队列)
   │
   │ 调用LLM
   ▼
5. LLM (生成回复文本，流式输出)
   │
   │ 文本片段
   ▼
6. TTS (合成语音，流式输出)
   │
   │ 音频数据
   ▼
7. DeviceManager (广播给所有设备)
   │
   │ WebSocket并发发送
   ▼
8. 硬件设备 (接收并播放)
```

### 3.2 设备连接流程

```
1. 设备发起WebSocket连接
   ws://server:8001/danmaku/?device-id=xxx
   │
   ▼
2. DanmakuService._handle_device_connection
   │
   │ 验证device-id
   ▼
3. DeviceManager.add_device
   │
   │ 保存设备信息
   ▼
4. 发送欢迎消息
   │
   ▼
5. 保持连接，等待音频广播
   │
   ▼
6. 设备断开时，DeviceManager.remove_device
```

## 4. 关键技术点

### 4.1 异步编程

使用 Python AsyncIO 框架实现全异步架构：

```python
# 并发处理多个任务
async def start(self):
    await asyncio.gather(
        self._start_websocket_server(),  # WebSocket服务器
        self.danmaku_handler.start(),    # 消息处理
        self.danmaku_collector.start(),  # 弹幕采集
        self._periodic_cleanup()          # 定期清理
    )
```

### 4.2 消息队列

使用 `asyncio.Queue` 实现消息队列：

```python
self.message_queue = asyncio.Queue()

# 生产者
await self.message_queue.put(danmaku)

# 消费者
danmaku = await self.message_queue.get()
```

### 4.3 并发广播

使用 `asyncio.gather` 并发发送给所有设备：

```python
tasks = [
    self._send_to_device(device_info, audio_data)
    for device_info in target_devices
]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

### 4.4 流式处理

LLM和TTS都采用流式处理，降低首字延迟：

```python
# LLM流式响应
for response in llm_responses:
    content = response
    # 立即发送给TTS
    self.tts.tts_text_queue.put(...)
```

## 5. 配置设计

### 5.1 配置文件结构

```yaml
danmaku:           # 弹幕服务配置
  room_id: ...     # 直播间ID
  use_mock: ...    # 是否使用模拟
  ws_host: ...     # WebSocket地址
  ws_port: ...     # WebSocket端口

log:               # 日志配置
  log_level: ...   # 日志级别
  log_file: ...    # 日志文件

prompt: ...        # AI角色提示词

selected_module:   # 选择的模块
  LLM: ...         # LLM模型
  TTS: ...         # TTS引擎

LLM:               # LLM配置
  ChatGLMLLM: ...  # 各个LLM的具体配置

TTS:               # TTS配置
  EdgeTTS: ...     # 各个TTS的具体配置
```

### 5.2 配置加载

复用原项目的配置加载机制：

```python
from config.settings import load_config
config = load_config()
```

## 6. 错误处理

### 6.1 异常类型

- `ConnectionError`: WebSocket连接失败
- `TTSException`: TTS合成失败
- `LLMError`: LLM调用失败

### 6.2 重试机制

弹幕采集器自动重连：

```python
reconnect_count = 0
max_reconnect_attempts = 10

while running and reconnect_count < max_reconnect_attempts:
    try:
        await self.connect()
        await self._listen()
    except Exception:
        reconnect_count += 1
        await asyncio.sleep(reconnect_delay)
```

### 6.3 容错处理

- LLM失败返回默认回复
- TTS失败跳过当前消息
- 设备断开自动清理
- 队列满时丢弃旧消息

## 7. 性能优化

### 7.1 异步并发

- 弹幕采集、消息处理、设备广播全异步
- 使用协程避免线程开销
- 并发处理多设备广播

### 7.2 队列缓冲

- 弹幕消息队列缓冲
- TTS音频队列缓冲
- 避免阻塞主流程

### 7.3 资源管理

- 定期清理断开设备
- 音频文件自动删除
- 队列大小限制

## 8. 扩展性设计

### 8.1 多平台支持

采用接口设计，易于扩展到其他平台：

```python
class DanmakuCollectorInterface:
    async def start(self): pass
    async def stop(self): pass

class DouyinCollector(DanmakuCollectorInterface): ...
class BilibiliCollector(DanmakuCollectorInterface): ...
class KuaishouCollector(DanmakuCollectorInterface): ...
```

### 8.2 插件机制

可以添加弹幕过滤、关键词识别等插件：

```python
class DanmakuPlugin:
    async def process(self, danmaku: dict) -> bool:
        """返回True表示继续处理，False表示过滤掉"""
        pass

# 敏感词过滤插件
class SensitiveWordFilter(DanmakuPlugin): ...

# 关键词识别插件
class KeywordDetector(DanmakuPlugin): ...
```

### 8.3 存储扩展

可以添加数据库存储弹幕和对话历史：

```python
class StorageInterface:
    async def save_danmaku(self, danmaku: dict): pass
    async def save_response(self, response: dict): pass

class MySQLStorage(StorageInterface): ...
class MongoDBStorage(StorageInterface): ...
```

## 9. 安全性考虑

### 9.1 输入验证

- 验证device-id格式
- 限制弹幕长度
- 敏感词过滤

### 9.2 访问控制

- 可选的设备认证
- IP白名单
- 连接数限制

### 9.3 资源限制

- WebSocket连接数限制
- 队列大小限制
- 请求频率限制

## 10. 监控与日志

### 10.1 日志级别

- DEBUG: 详细调试信息
- INFO: 常规操作信息
- WARNING: 警告信息
- ERROR: 错误信息

### 10.2 关键指标

- 弹幕接收速率
- LLM响应时间
- TTS合成时间
- 设备连接数
- 消息队列长度

### 10.3 日志格式

```
[时间][模块][标签]-级别-消息
```

示例：
```
[250116 10:30:45][DANMAKU][danmaku_service]-INFO-弹幕服务启动成功
```

## 11. 测试策略

### 11.1 单元测试

- 各模块独立测试
- Mock外部依赖
- 覆盖核心功能

### 11.2 集成测试

- 端到端流程测试
- 使用模拟数据
- 验证各模块协作

### 11.3 压力测试

- 高并发弹幕测试
- 多设备连接测试
- 长时间运行测试

## 12. 部署架构

### 12.1 单机部署

```
┌────────────────────────┐
│   服务器 (1台)          │
│  ┌──────────────────┐  │
│  │ 弹幕AI服务        │  │
│  │  - 弹幕采集       │  │
│  │  - LLM处理       │  │
│  │  - TTS合成       │  │
│  │  - 设备管理       │  │
│  └──────────────────┘  │
└────────────────────────┘
         │
         │ WebSocket
         │
    ┌────┴────┐
    │         │
  设备1     设备2
```

### 12.2 分布式部署

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 弹幕采集节点 │    │ 处理节点1    │    │ 处理节点2    │
│ (采集弹幕)   │───▶│ (LLM+TTS)   │    │ (LLM+TTS)   │
└─────────────┘    └──────┬──────┘    └──────┬──────┘
                          │                   │
                          │    消息队列        │
                          │   (Redis/RabbitMQ) │
                          │                   │
                   ┌──────┴───────────────────┴──────┐
                   │       设备管理节点                │
                   │      (WebSocket服务器)           │
                   └──────┬───────────────────┬──────┘
                          │                   │
                      设备1               设备2...
```

## 13. 未来改进方向

### 13.1 功能增强

- [ ] Web管理后台
- [ ] 弹幕数据统计
- [ ] 多直播间支持
- [ ] 自动回复规则配置
- [ ] 弹幕情感分析

### 13.2 性能优化

- [ ] 使用GPU加速TTS
- [ ] 引入缓存机制
- [ ] 负载均衡
- [ ] CDN音频分发

### 13.3 平台扩展

- [ ] B站直播支持
- [ ] 快手直播支持
- [ ] YouTube直播支持
- [ ] Twitch支持

## 14. 总结

本项目通过模块化设计，实现了弹幕到AI语音的完整流程：

1. **解耦设计**：各模块职责清晰，易于维护
2. **异步架构**：高并发性能，低资源占用
3. **可扩展性**：易于添加新平台和新功能
4. **高可用性**：完善的错误处理和重试机制

通过复用 xiaozhi-esp32-server 的核心能力（LLM、TTS），快速实现了直播弹幕AI互动功能。
