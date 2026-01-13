<div align="center">
  <img src="assets/logo.png" width="200" height="200" alt="openCowork Logo">
  <h1>openCowork</h1>
  <p><strong>让 AI 真正成为你的数字化同事 | Making AI Your Digital Coworker</strong></p>

  <p>
    <a href="https://github.com/CHANGGELY/openCowork/stargazers"><img src="https://img.shields.io/github/stars/CHANGGELY/openCowork?style=for-the-badge&logo=github" alt="Stars"></a>
    <a href="https://github.com/CHANGGELY/openCowork/network/members"><img src="https://img.shields.io/github/forks/CHANGGELY/openCowork?style=for-the-badge&logo=github" alt="Forks"></a>
    <a href="LICENSE"><img src="https://img.shields.io/github/license/CHANGGELY/openCowork?style=for-the-badge" alt="License"></a>
    <img src="https://img.shields.io/badge/Python-3.14+-blue?style=for-the-badge&logo=python" alt="Python">
    <img src="https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js" alt="Next.js">
  </p>

  <p>
    <b>简体中文</b> | <a href="#english">English</a>
  </p>
</div>

---

## 🌟 什么是 openCowork？

**openCowork** 是一个开源的桌面 AI 代理框架。它打破了厂商锁定的限制，允许用户使用 **OpenAI (GPT-4o)**、**Google Gemini** 或 **Anthropic Claude** 的 API 直接控制自己的桌面电脑。

不同于官方的 Claude Desktop 限制，openCowork 旨在提供一个自由、可定制、且跨平台的解决方案，让 AI 能够“看见”你的屏幕并像人类一样操作鼠标和键盘。

### ✨ 核心特性

- 🖥️ **全自动控制**：AI 可以根据你的自然语言指令，自动执行截图、思考并操作电脑。
- 🤖 **模型自由**：支持所有主流的多模态 LLM (OpenAI GPT-4o, Gemini 2.0 Flash, Claude 3.5 Sonnet)。
- 🍎 **极致审美**：基于 Apple 设计风格的 UI，原生支持暗色模式。
- 🛡️ **安全第一**：提供 `Ctrl+Alt+Q` 全局紧急停止热键，安全性完全由你掌控。
- ⚡ **实时反馈**：通过 WebSocket 实现亚秒级日志同步。
- 🌐 **国际化**：原生支持中英文自由切换。

---

## 🚀 快速开始

### 1. 环境准备

- **Python**: 3.14+
- **Node.js**: 18+

### 2. 下载与安装

```bash
# 克隆仓库
git clone https://github.com/chuan/openCowork.git
cd openCowork

# 安装后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 安装前端
cd ../frontend
npm install
```

### 3. 运行项目

你需要打开两个终端窗口：

**终端 A (后端):**
```bash
cd backend
source venv/bin/activate
python main.py
```

**终端 B (前端):**
```bash
cd frontend
npm run dev
```

打开浏览器访问 [http://localhost:3000](http://localhost:3000) 即可开始。

---

## 🛠️ 技术架构

- **前端**: Next.js / Tailwind CSS / shadcn/ui / Framer Motion
- **后端**: FastAPI / WebSocket / Pydantic
- **控制引擎**: PyAutoGUI (输入) / MSS (截图) / Pynput (热键)

---

<h2 id="english">🌟 What is openCowork?</h2>

**openCowork** is an open-source desktop AI agent framework. It breaks vendor lock-in by allowing users to use **OpenAI (GPT-4o)**, **Google Gemini**, or **Anthropic Claude** APIs to control their desktop computers directly.

### ✨ Key Features

- 🖥️ **Full Automation**: AI executes screenshots, reasoning, and computer operations based on your natural language commands.
- 🤖 **Model Freedom**: Supports all major multimodal LLMs.
- 🍎 **Apple Aesthetics**: Premium UI with native Dark Mode support.
- 🛡️ **Safety First**: Global `Ctrl+Alt+Q` emergency stop hotkey.
- ⚡ **Real-time Feedback**: Sub-second log synchronization via WebSockets.

---

## 📜 许可证

本项目采用 [MIT](LICENSE) 许可证。

## 🤝 贡献

欢迎提交 PR 或 Issue！请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。
