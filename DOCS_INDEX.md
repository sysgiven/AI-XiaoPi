# 项目文档索引 (Documentation Index)

欢迎查阅小皮AI直播服务器(XiaoPi)的文档！本文档将帮助你快速找到需要的信息。

## 📖 快速导航

### 入门文档
- [README.md](README.md) - 项目介绍和完整指南
- [QUICKSTART.md](QUICKSTART.md) - 10分钟快速上手
- [CONFIG_EXAMPLES.md](CONFIG_EXAMPLES.md) - 配置示例大全

### 开发文档
- [CONTRIBUTING.md](CONTRIBUTING.md) - 贡献指南
- [CHANGELOG.md](CHANGELOG.md) - 版本更新日志
- [LICENSE](LICENSE) - MIT 开源协议

### 技术文档
- [SERIALIZED_PROCESSING.md](SERIALIZED_PROCESSING.md) - 串行化处理机制详解
- [SENTENCE_ID_FIX.md](SENTENCE_ID_FIX.md) - 音频播放问题修复说明

## 📋 文档详情

### README.md
**适合人群**: 所有用户

主项目文档，包含：
- 项目简介和核心功能
- 完整的安装和配置指南
- 工作原理图解
- 故障排除指南
- 联系方式

**何时阅读**: 首次了解项目或需要完整参考时

---

### QUICKSTART.md
**适合人群**: 新手用户

快速入门指南，包含：
- 5分钟模拟模式启动
- 真实环境部署步骤
- 硬件设备连接指南
- 常见问题解答

**何时阅读**: 第一次部署项目时

---

### CONFIG_EXAMPLES.md
**适合人群**: 所有用户

配置示例大全，包含：
- 各种LLM提供商配置（OpenAI、ChatGLM、Gemini等）
- 各种TTS引擎配置（Edge TTS、阿里云等）
- 弹幕采集模式配置
- 流量控制配置
- 完整配置示例

**何时阅读**: 需要配置或调整 LLM/TTS 时

---

### CONTRIBUTING.md
**适合人群**: 开发者、贡献者

贡献指南，包含：
- 贡献方式说明
- 开发环境设置
- 代码规范
- 提交规范
- Pull Request 流程

**何时阅读**: 想要为项目贡献代码或报告问题时

---

### CHANGELOG.md
**适合人群**: 所有用户

版本更新日志，包含：
- 版本历史
- 新功能说明
- Bug修复记录
- 已知问题

**何时阅读**: 查看版本更新内容或了解已知问题时

---

### SERIALIZED_PROCESSING.md
**适合人群**: 开发者、技术爱好者

串行化处理机制技术文档，包含：
- 设计目标和动机
- 核心实现细节
- 工作流程图解
- 与原项目的对比

**何时阅读**: 想深入了解弹幕处理机制时

---

### SENTENCE_ID_FIX.md
**适合人群**: 遇到音频播放问题的用户、开发者

音频播放问题修复文档，包含：
- 问题症状描述
- 根本原因分析
- 修复方案说明
- 测试验证方法

**何时阅读**: 遇到音频不播放问题时

---

## 🎯 按使用场景查找

### 场景 1: 我是新手，想快速体验项目
1. [QUICKSTART.md](QUICKSTART.md) - 按照"5分钟快速启动"操作
2. [CONFIG_EXAMPLES.md](CONFIG_EXAMPLES.md) - 查看"最小配置"

### 场景 2: 我想部署到生产环境
1. [QUICKSTART.md](QUICKSTART.md) - 查看"真实环境部署"部分
2. [CONFIG_EXAMPLES.md](CONFIG_EXAMPLES.md) - 查看"生产环境配置"
3. [README.md](README.md) - 查看"故障排除"部分

### 场景 3: 我想更换 LLM 或 TTS 提供商
1. [CONFIG_EXAMPLES.md](CONFIG_EXAMPLES.md) - 查看对应的配置示例
2. [README.md](README.md) - 查看"配置说明"部分

### 场景 4: 我遇到了问题
1. [README.md](README.md) - 查看"故障排除"部分
2. [QUICKSTART.md](QUICKSTART.md) - 查看"常见问题"部分
3. [SENTENCE_ID_FIX.md](SENTENCE_ID_FIX.md) - 如果是音频播放问题
4. 提交 [GitHub Issue](https://github.com/your-repo/issues)

### 场景 5: 我想贡献代码
1. [CONTRIBUTING.md](CONTRIBUTING.md) - 了解贡献流程
2. [SERIALIZED_PROCESSING.md](SERIALIZED_PROCESSING.md) - 了解核心机制
3. [README.md](README.md) - 了解项目架构

### 场景 6: 我想了解项目更新
1. [CHANGELOG.md](CHANGELOG.md) - 查看版本更新历史
2. [README.md](README.md) - 查看最新功能说明

## 📚 原项目文档

本项目基于 xiaozhi-esp32-server 开发，以下是原项目的相关文档：

### 位置: `xiaozhi-esp32-server/main/xiaozhi-server/`

- `ARCHITECTURE.md` - 原项目架构说明
- `DANMAKU_README.md` - 弹幕功能早期文档
- `DOUYIN_BARRAGE_SETUP.md` - 抖音弹幕接入指南
- `FILE_LIST.md` - 文件列表说明
- `PROJECT_SUMMARY.md` - 项目概览
- `QUICKSTART.md` - 原项目快速开始
- 其他技术文档...

## 🔍 按主题查找

### 配置相关
- [CONFIG_EXAMPLES.md](CONFIG_EXAMPLES.md) - 配置示例
- [README.md](README.md) - 配置说明章节
- `danmaku_config.yaml` - 配置文件（带注释）

### 部署相关
- [QUICKSTART.md](QUICKSTART.md) - 快速部署
- [README.md](README.md) - 完整部署指南
- `requirements.txt` - 依赖列表

### 开发相关
- [CONTRIBUTING.md](CONTRIBUTING.md) - 开发指南
- [SERIALIZED_PROCESSING.md](SERIALIZED_PROCESSING.md) - 核心机制
- [CHANGELOG.md](CHANGELOG.md) - 版本历史

### 问题排查
- [README.md](README.md) - 故障排除章节
- [QUICKSTART.md](QUICKSTART.md) - 常见问题
- [SENTENCE_ID_FIX.md](SENTENCE_ID_FIX.md) - 音频问题

## 💡 文档贡献

发现文档问题或有改进建议？

1. 查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献流程
2. 提交 Issue 或 Pull Request
3. 文档改进和代码改进一样重要！

## 🆘 获取帮助

如果文档中没有找到你需要的信息：

1. 搜索 [GitHub Issues](https://github.com/your-repo/issues)
2. 提交新的 Issue
3. 加入讨论群（如果有）

---

**提示**: 建议先阅读 [README.md](README.md) 和 [QUICKSTART.md](QUICKSTART.md)，可以解决大部分问题！
