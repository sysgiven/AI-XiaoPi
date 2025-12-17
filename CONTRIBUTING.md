# 贡献指南 (Contributing Guide)

感谢你对小皮AI直播服务器(XiaoPi)项目的关注！我们欢迎任何形式的贡献。

## 📝 贡献方式

你可以通过以下方式为项目做出贡献：

- 🐛 报告 Bug
- 💡 提出新功能建议
- 📖 改进文档
- 🔧 提交代码修复或新功能
- ⭐ 给项目一个 Star
- 📣 分享项目给其他人

## 🐛 报告问题

如果你发现了 Bug，请通过 GitHub Issues 提交问题报告。好的问题报告应该包含：

### Bug 报告模板

```markdown
**问题描述**
简明扼要地描述问题是什么。

**复现步骤**
1. 执行步骤 '...'
2. 点击 '...'
3. 滚动到 '...'
4. 看到错误

**期望行为**
清晰简洁地描述你期望发生什么。

**实际行为**
清晰简洁地描述实际发生了什么。

**截图/日志**
如果适用，添加截图或日志来帮助解释你的问题。

**环境信息**
- OS: [例如 Windows 11, Ubuntu 22.04]
- Python 版本: [例如 3.10.5]
- 项目版本: [例如 v1.0.0]
- 配置信息: [例如使用的 LLM/TTS 提供商]

**附加信息**
其他任何有助于解决问题的信息。
```

## 💡 功能建议

我们欢迎新功能的建议！请通过 GitHub Issues 提交功能请求：

### 功能请求模板

```markdown
**功能描述**
清晰简洁地描述你想要的功能。

**使用场景**
描述这个功能将解决什么问题或改善什么体验。

**建议的实现方案**
如果你有想法，可以描述一下如何实现这个功能。

**替代方案**
描述你考虑过的其他替代方案。

**附加信息**
其他任何相关的信息或截图。
```

## 🔧 代码贡献

### 开发环境设置

1. Fork 这个项目
2. Clone 你 Fork 的仓库
```bash
git clone https://github.com/your-username/danmaku-ai-server.git
cd danmaku-ai-server
```

3. 创建开发分支
```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

4. 安装依赖
```bash
cd xiaozhi-esp32-server/main/xiaozhi-server
pip install -r requirements.txt
```

5. 进行你的修改

6. 测试你的修改
```bash
# 运行项目确保没有破坏现有功能
python danmaku_app.py
```

### 代码规范

为了保持代码质量和一致性，请遵循以下规范：

#### Python 代码风格

- 遵循 [PEP 8](https://pep8.org/) 代码规范
- 使用 4 个空格进行缩进（不使用 Tab）
- 每行代码不超过 120 个字符
- 函数和类使用 docstring 注释
- 变量和函数命名使用小写加下划线（snake_case）
- 类命名使用大驼峰（PascalCase）

#### 注释规范

```python
def process_danmaku(danmaku: dict) -> bool:
    """
    处理单条弹幕消息

    Args:
        danmaku: 弹幕信息字典，包含 username, content 等字段

    Returns:
        bool: 处理成功返回 True，否则返回 False

    Raises:
        ValueError: 当 danmaku 格式不正确时
    """
    pass
```

#### 日志规范

使用适当的日志级别：
- `logger.debug()`: 详细的调试信息
- `logger.info()`: 关键流程信息
- `logger.warning()`: 警告信息
- `logger.error()`: 错误信息

```python
self.logger.info(f"✅ 处理弹幕: {username}: {content}")
self.logger.warning(f"⚠️  弹幕队列已满，丢弃消息")
self.logger.error(f"❌ LLM调用失败: {error}")
```

### 提交规范

我们使用语义化的提交信息格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 代码重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建或辅助工具的变动

#### 示例

```
feat(danmaku): 添加弹幕过滤功能

- 添加关键词过滤
- 添加用户黑名单
- 添加弹幕长度限制

Closes #123
```

```
fix(audio): 修复音频播放延迟问题

修复了 Rate Controller 未正确初始化导致的音频播放延迟问题

Fixes #456
```

### Pull Request 流程

1. 确保代码符合规范
2. 更新相关文档
3. 提交 Pull Request
4. 在 PR 描述中清晰说明：
   - 这个 PR 解决了什么问题
   - 做了哪些改动
   - 如何测试
   - 是否有破坏性变更

#### PR 模板

```markdown
## 变更说明
简要描述这个 PR 做了什么。

## 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 性能优化
- [ ] 代码重构
- [ ] 其他（请说明）

## 测试
描述你如何测试这些变更。

## 相关 Issue
Closes #(issue编号)

## 截图（如果适用）
添加截图来展示变更效果。

## 检查清单
- [ ] 代码符合项目规范
- [ ] 已添加必要的注释
- [ ] 已更新相关文档
- [ ] 已测试变更功能
- [ ] 无破坏性变更（或已在文档中说明）
```

## 📖 文档贡献

文档和代码一样重要！你可以：

- 修正文档中的错误
- 添加使用示例
- 翻译文档到其他语言
- 改进文档的清晰度

文档位置：
- 主文档：`README.md`
- 配置说明：`danmaku_config.yaml`（注释）
- 技术文档：`docs/` 目录

## 🎯 开发优先级

当前我们特别欢迎以下方面的贡献：

- [ ] 更多的弹幕源支持（B站、快手等）
- [ ] 更多的LLM提供商支持
- [ ] 更多的TTS引擎支持
- [ ] 性能优化
- [ ] 单元测试
- [ ] 文档改进
- [ ] 使用示例和教程

## ❓ 有疑问？

如果你在贡献过程中有任何疑问：

- 查看现有的 Issues 和 Pull Requests
- 提交新的 Issue 询问
- 加入讨论群（如果有的话）

## 📜 行为准则

参与本项目即表示你同意遵守以下准则：

- 尊重所有参与者
- 友好交流，建设性反馈
- 专注于对项目最有利的方面
- 展现同理心

## 🙏 感谢

感谢每一位贡献者！你们的参与让这个项目变得更好。

---

再次感谢你的贡献！ 🎉
