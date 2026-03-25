<!-- markdownlint-disable MD024 -->
<!-- markdownlint-disable MD025 -->
<!-- markdownlint-disable MD033 -->
<!-- markdownlint-disable MD034 -->
<!-- markdownlint-disable MD041 -->
# ChangeLog

# 2026/03/26 v1.0.0

首个发行版，基础功能已可用。
by @DBJD-CR & @openai-codex[bot] & @roomote & @gemini-code-assist[bot] & @sourcery-ai[bot] & @kilo-code-bot [bot]in #1

## 🚀 What's Changed

### ✨ New Features (新功能)

- 支持通过向 bot 发送指令查询 Live Dashboard 当前设备状态。
- 提供指令：`/视奸`，并支持别名：`/live`、`/dashboard`、`/设备状态`、`/状态面板`。
- 打通上游请求链路，可拉取并解析 `/api/current` 数据。
- 支持在 AstrBot 的 WebUI 中进行可视化配置，包括黑白名单、可选鉴权 token、超时时间、展示字段开关等配置。
- 支持状态文案渲染：在线/离线、电量、音乐、最后上报时间等信息。
- 增加设备关键词黑白名单过滤（当前按 `device_name` 匹配）。
- 增加群组/用户黑名单拦截（基于 `session_id` / `sender_id`）。
- 增加信息黑名单替换：`show_app_name`、`show_display_title` 命中敏感词时可替换为统一文案。
- 增加发送策略：设备数较多时使用合并转发，减少长文刷屏。
- 支持 LLM 通过自然语言调用该插件。

### ♻️ Refactor (重构)

- 项目结构采用分层设计：入口层、服务层、工具层。
- 请求逻辑、渲染逻辑、配置解析逻辑拆分为独立模块，维护更清晰。
- 包结构补齐 `__init__.py`，统一相对导入，降低路径相关问题。
- 更全面准确和丰富有趣的消息文案展示。

### 🐛 Bug Fixes (修复)

- 修复插件扫描/加载兼容性问题，确保 AstrBot 启动后可识别。
- 修复全量文本与引用回复一起发出的问题。
- 修复应用黑白名单时设备数计算错误的问题。
- 修复一些 AI 审核从鸡蛋里挑的骨头 by @DBJD-CR in #2

### 📚 Documentation (文档)

- 完成首版 README：包含安装、配置、命令、示例输出与架构说明等。
- 更新目录结构与系统架构图，补充更多章节资源。
- 添加 CODE_OF_CONDUCT，CHANGELOG 与 CONTRIBUTING。
- 添加 Issue & PR 模板。

### 🔧 Chore (杂项)

- 补充依赖声明文件 [`requirements.txt`](requirements.txt)。
- 优化注释可读性，统一中文注释风格（专有名词除外）。
- 调整日志输出策略，降低 INFO 噪音并保留关键链路日志。
- GitHub 工作流全家桶。

---

## ❤️ New Contributors

- @DBJD-CR made their first contribution in #1
- @openai-codex[bot] made their first contribution in #1
- @roomote made their first contribution in #1
- @gemini-code-assist[bot] made their first contribution in #1
- @sourcery-ai[bot] made their first contribution in #1
- @kilo-code-bot [bot] made their first contribution in #1

---

<details>
<summary>点击查看历史更新内容</summary>

暂无历史更新内容

</details>
