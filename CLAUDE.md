# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

openCowork 是一个开源的桌面 AI 代理框架，允许 AI 通过自然语言指令控制用户的桌面电脑。项目采用前后端分离架构，支持多种 LLM 提供商（OpenAI GPT-5.2、Google Gemini 3 pro、Anthropic Claude opus 4.5）。

## 核心命令

### 开发环境启动

需要同时运行两个终端：

**后端终端 (Terminal 1):**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py
```

**前端终端 (Terminal 2):**
```bash
cd frontend
npm run dev
```

访问 http://localhost:3000 使用应用。

### 常用命令

**前端 (frontend/):**
```bash
npm run dev      # 启动开发服务器
npm run build    # 构建生产版本
npm run start    # 启动生产服务器
npm run lint     # ESLint 检查
```

**后端 (backend/):**
```bash
python main.py   # 启动后端服务
```

**依赖安装:**
```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

## 架构说明

### 技术栈
- **前端**: Next.js 16.1.1 (React 19.2.3) + TypeScript + Tailwind CSS + shadcn/ui
- **后端**: FastAPI + Python 3.14+ + WebSocket
- **AI 控制**: PyAutoGUI (鼠标键盘) + MSS (截图) + Pynput (热键)

### 核心模块

**后端架构:**
- `main.py` - FastAPI 主入口，处理 HTTP API 和 WebSocket 连接
- `agent_loop.py` - Agent 核心循环：截图 → LLM 分析 → 执行操作
- `providers/` - LLM 提供商抽象层，统一接口支持多个 AI 服务
- `tools/` - 系统控制工具（屏幕截图、鼠标键盘操作）

**关键设计模式:**
1. **提供商抽象层**: `providers/base.py` 定义统一接口，新增 LLM 只需实现基类
2. **WebSocket 实时通信**: 用于向前端广播 Agent 执行日志
3. **全局热键**: `Ctrl+Alt+Q` 紧急停止，安全性保障

### 前后端通信

- **REST API**: 配置管理、任务控制
- **WebSocket**: 实时日志推送（亚秒级同步）
- **CORS**: 开发环境允许跨域，生产环境需限制

## 重要配置

### 环境要求
- Python: 3.14+
- Node.js: 18+

### 关键配置文件
- `frontend/next.config.ts` - 配置静态导出和 GitHub Pages 部署
- `frontend/tsconfig.json` - TypeScript 严格模式，路径别名 `@/*`
- `backend/requirements.txt` - Python 依赖，按功能分组

### 部署配置
- 前端静态导出到 `frontend/out/`
- GitHub Pages 自动部署 (`.github/workflows/deploy-pages.yaml`)
- Python CI 检查 (`.github/workflows/python-ci.yaml`)

## 开发注意事项

### 代码风格
- 使用中文命名和注释，降低理解门槛
- TypeSrcipt 严格模式，零容忍报错
- Python 使用 async/await 异步编程

### 安全机制
- 全局紧急停止: `Ctrl+Alt+Q`
- API 密钥通过环境变量管理
- 不在前端暴露敏感信息

### 调试技巧
- 后端日志使用 Loguru，支持彩色输出
- WebSocket 连接状态在控制台实时显示
- FastAPI 自动生成 API 文档 (http://localhost:8000/docs)