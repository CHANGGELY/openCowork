"""
============================================
openCowork 后端主入口
============================================
这个文件是整个后端服务的"大门"。

当你运行 `python main.py` 时，它会启动一个 Web 服务器（FastAPI + Uvicorn），
前端（网页界面）就可以通过 HTTP 请求和 WebSocket 和这个后端通信。

主要功能：
1. 接收来自前端的用户消息
2. 启动 Agent 循环（截图 → 发给 LLM → 执行操作）
3. 通过 WebSocket 实时推送日志给前端
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

# 导入我们自己的模块
from agent_loop import AgentLoop, 全局停止信号
from providers.openai_provider import OpenAI提供者
from providers.gemini_provider import Gemini提供者
from providers.anthropic_provider import Anthropic提供者
from security import 全局安全配置, 验证提供者名称

# ============================================
# 数据模型（用于定义 API 请求/响应的格式）
# ============================================

class 配置请求(BaseModel):
    """
    用户在前端填写的配置信息。
    provider: 选择的 LLM 提供商 ("openai" / "gemini" / "anthropic")
    api_key:  对应的 API 密钥
    """
    provider: str
    api_key: str

class 聊天请求(BaseModel):
    """
    用户发送的聊天消息。
    message: 用户输入的文字指令，比如 "帮我打开计算器"
    """
    message: str

class 状态响应(BaseModel):
    """
    返回给前端的状态信息。
    is_running: Agent 是否正在运行
    current_task: 当前正在执行的任务描述
    """
    is_running: bool
    current_task: Optional[str] = None

# ============================================
# 全局状态（存储当前的 Agent 和配置）
# ============================================

# 当前活跃的 Agent 循环实例
当前Agent: Optional[AgentLoop] = None
# 所有连接的 WebSocket 客户端（用于广播日志）
websocket连接池: list[WebSocket] = []

# ============================================
# 生命周期管理
# ============================================

@asynccontextmanager
async def 生命周期(app: FastAPI):
    """
    应用启动和关闭时的钩子。
    - 启动时：输出欢迎日志
    - 关闭时：清理资源
    """
    logger.info("🚀 openCowork 后端启动中...")
    yield  # 应用运行期间
    logger.info("👋 openCowork 后端关闭")
    # 停止正在运行的 Agent
    全局停止信号.set()

# ============================================
# 创建 FastAPI 应用
# ============================================

app = FastAPI(
    title="openCowork API",
    description="开源版 Claude Cowork 后端服务",
    version="0.1.0",
    lifespan=生命周期
)

# 允许前端跨域请求（开发时 localhost:3000 需要访问 localhost:8000）
import os

# 根据环境变量决定 CORS 配置
环境 = os.environ.get("ENVIRONMENT", "development")
允许的域名 = ["http://localhost:3000", "http://127.0.0.1:3000"]

if 环境 == "production":
    # 生产环境：只允许特定域名
    允许的域名 = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=允许的域名,  # 限制允许的域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # 限制 HTTP 方法
    allow_headers=["*"],
)

# ============================================
# API 路由
# ============================================

@app.post("/api/config", summary="设置 API 配置")
async def 设置配置(配置: 配置请求):
    """
    保存用户填写的 Provider 和 API Key。
    这个接口会在用户点击"保存设置"时被调用。
    """
    # 验证 provider 名称
    if not 验证提供者名称(配置.provider):
        raise HTTPException(
            status_code=400,
            detail="无效的 Provider，可选值: openai, gemini, anthropic"
        )

    # 使用安全配置管理器保存配置
    成功 = 全局安全配置.保存配置(配置.provider, 配置.api_key)
    if not 成功:
        raise HTTPException(
            status_code=500,
            detail="保存配置失败"
        )

    logger.info(f"✅ 配置已安全保存: Provider={配置.provider}")
    return {"success": True, "message": f"已安全配置 {配置.provider}"}


@app.post("/api/clear-config", summary="清除 API 配置")
async def 清除配置():
    """
    清除当前 API 配置（从内存中删除加密的配置）
    """
    全局安全配置.清除配置()
    logger.info("🔧 配置已清除")
    return {"success": True, "message": "配置已清除"}


@app.post("/api/chat", summary="发送聊天消息")
async def 发送消息(请求: 聊天请求):
    """
    接收用户的指令并启动 Agent 执行。
    """
    global 当前Agent

    # 从安全配置管理器获取配置
    配置 = 全局安全配置.获取配置()
    if not 配置:
        raise HTTPException(status_code=400, detail="请先配置 API Key")

    if 当前Agent and 当前Agent.正在运行:
        raise HTTPException(status_code=400, detail="Agent 正在执行任务，请等待完成或停止")

    # 根据 Provider 创建对应的适配器
    provider名称 = 配置["provider"]
    api_key = 配置["api_key"]

    if provider名称 == "openai":
        提供者 = OpenAI提供者(api_key)
    elif provider名称 == "gemini":
        提供者 = Gemini提供者(api_key)
    elif provider名称 == "anthropic":
        提供者 = Anthropic提供者(api_key)
    else:
        raise HTTPException(status_code=400, detail="未知的 Provider")

    # 创建 Agent 循环并在后台运行
    当前Agent = AgentLoop(提供者=提供者, 广播函数=广播日志)

    # 使用 asyncio 在后台启动 Agent（不阻塞 API 响应）
    asyncio.create_task(当前Agent.执行任务(请求.message))

    logger.info(f"📝 收到任务: {请求.message}")
    return {"success": True, "message": "任务已启动"}


@app.post("/api/validate-config", summary="验证 API 配置")
async def 验证配置():
    """
    验证当前 API 配置是否有效
    """
    配置 = 全局安全配置.获取配置()
    if not 配置:
        raise HTTPException(status_code=400, detail="未找到配置")

    provider名称 = 配置["provider"]
    api_key = 配置["api_key"]

    try:
        # 根据 Provider 创建对应的适配器并尝试验证
        if provider名称 == "openai":
            提供者 = OpenAI提供者(api_key)
            # 尝试进行一个简单的 API 调用
            import openai
            client = openai.AsyncOpenAI(api_key=api_key)
            await client.models.list(limit=1)
        elif provider名称 == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            # 尝试列出模型
            genai.list_models()
        elif provider名称 == "anthropic":
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=api_key)
            # 尝试一个简单的 API 调用
            await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )

        logger.info(f"✅ {provider名称} 配置验证成功")
        return {"success": True, "message": f"{provider名称} 配置验证成功"}
    except Exception as e:
        logger.error(f"❌ {provider名称} 配置验证失败: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"{provider名称} 配置验证失败: {str(e)}"
        )


@app.get("/api/health", summary="健康检查")
async def 健康检查():
    """
    检查服务健康状态
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "has_config": 全局安全配置.配置是否存在(),
        "agent_running": 当前Agent.正在运行 if 当前Agent else False
    }


class 系统信息响应(BaseModel):
    """
    系统信息响应模型
    """
    os_info: str
    python_version: str
    available_providers: list[str]


@app.get("/api/system-info", response_model=系统信息响应, summary="获取系统信息")
async def 获取系统信息():
    """
    获取系统相关信息
    """
    import platform
    import sys

    return 系统信息响应(
        os_info=f"{platform.system()} {platform.release()}",
        python_version=sys.version,
        available_providers=["openai", "gemini", "anthropic"]
    )


@app.post("/api/stop", summary="停止当前任务")
async def 停止任务():
    """
    立即停止正在运行的 Agent。
    """
    全局停止信号.set()
    logger.warning("🛑 用户手动停止了 Agent")
    return {"success": True, "message": "已发送停止信号"}


class 配置状态响应(BaseModel):
    """
    配置状态响应模型
    """
    has_config: bool
    provider: Optional[str] = None
    last_updated: Optional[str] = None


@app.get("/api/config-status", response_model=配置状态响应, summary="获取配置状态")
async def 获取配置状态():
    """
    返回当前配置的状态（不包含敏感的 API 密钥）。
    """
    配置 = 全局安全配置.获取配置()
    if 配置:
        return 配置状态响应(
            has_config=True,
            provider=配置["provider"],
            last_updated=配置["timestamp"]
        )
    return 配置状态响应(has_config=False)


@app.get("/api/status", response_model=状态响应, summary="获取当前状态")
async def 获取状态():
    """
    返回 Agent 的当前运行状态。
    """
    if 当前Agent:
        return 状态响应(
            is_running=当前Agent.正在运行,
            current_task=当前Agent.当前任务
        )
    return 状态响应(is_running=False)


# ============================================
# WebSocket（用于实时日志推送）
# ============================================

@app.websocket("/ws")
async def websocket端点(websocket: WebSocket):
    """
    WebSocket 连接端点。
    前端连接后，会实时收到 Agent 的执行日志。
    """
    await websocket.accept()
    websocket连接池.append(websocket)
    logger.info(f"🔌 WebSocket 客户端连接，当前连接数: {len(websocket连接池)}")
    
    try:
        # 保持连接，等待客户端断开
        while True:
            # 接收心跳或其他消息（暂不处理）
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket连接池.remove(websocket)
        logger.info(f"🔌 WebSocket 客户端断开，当前连接数: {len(websocket连接池)}")


async def 广播日志(消息: str, 类型: str = "info"):
    """
    向所有连接的 WebSocket 客户端广播日志消息。
    
    参数:
        消息: 要发送的文本
        类型: "info" / "action" / "error" / "screenshot"
    """
    数据 = {"type": 类型, "message": 消息}
    断开的连接 = []
    
    for ws in websocket连接池:
        try:
            await ws.send_json(数据)
        except Exception:
            断开的连接.append(ws)
    
    # 清理断开的连接
    for ws in 断开的连接:
        websocket连接池.remove(ws)


# ============================================
# 程序入口
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 50)
    logger.info("openCowork 后端服务")
    logger.info("访问 http://localhost:8000/docs 查看 API 文档")
    logger.info("=" * 50)
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式：文件变化自动重启
        log_level="info"
    )
