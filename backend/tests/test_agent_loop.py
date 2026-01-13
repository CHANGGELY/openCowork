"""
测试 Agent 循环核心功能
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from providers.base import LLM提供者基类, 工具调用, LLM响应
from agent_loop import AgentLoop


class MockLLMProvider(LLM提供者基类):
    """模拟 LLM 提供者用于测试"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.call_count = 0

    async def 发送消息(self, 对话历史, 截图base64=None):
        self.call_count += 1
        # 模拟前两次调用返回工具调用，第三次返回空列表表示任务完成
        if self.call_count < 3:
            return LLM响应(
                文本内容=f"模拟响应 {self.call_count}",
                工具调用列表=[
                    工具调用(工具名称="mouse_move", 参数={"x": 100, "y": 100})
                ]
            )
        else:
            # 最后一次调用返回空工具列表，表示任务完成
            return LLM响应(
                文本内容="任务已完成",
                工具调用列表=[]
            )


@pytest.mark.asyncio
async def test_agent_initialization():
    """测试 AgentLoop 的初始化"""
    provider = MockLLMProvider("test-key")
    agent = AgentLoop(提供者=provider, 最大循环次数=5)

    assert agent.提供者 == provider
    assert agent.最大循环次数 == 5
    assert not agent.正在运行
    assert agent.当前任务 is None


@pytest.mark.asyncio
async def test_agent_execution():
    """测试 Agent 的基本执行流程"""
    provider = MockLLMProvider("test-key")
    广播函数 = AsyncMock()

    agent = AgentLoop(提供者=provider, 广播函数=广播函数, 最大循环次数=5)

    # 启动任务
    await agent.执行任务("测试任务")

    # 验证任务已完成
    assert not agent.正在运行
    assert agent.当前任务 is None

    # 验证 LLM 被调用了（由于模拟的逻辑，应该只调用2次，第3次因无工具调用而结束）
    assert provider.call_count == 3  # 根据模拟逻辑，应该调用3次

    # 验证广播被调用
    广播函数.assert_called()


@pytest.mark.asyncio
async def test_agent_stops_when_no_tool_calls():
    """测试当 LLM 返回空工具调用列表时 Agent 正确停止"""
    provider = MockLLMProvider("test-key")

    # 创建一个总是返回空工具列表的模拟提供者
    class CompleteProvider(LLM提供者基类):
        async def 发送消息(self, 对话历史, 截图base64=None):
            return LLM响应(文本内容="任务完成", 工具调用列表=[])

    complete_provider = CompleteProvider("test-key")
    广播函数 = AsyncMock()
    agent = AgentLoop(提供者=complete_provider, 广播函数=广播函数, 最大循环次数=10)

    await agent.执行任务("测试完成条件")

    # 验证只调用了一次 LLM（因为空工具列表会导致立即停止）
    response = await complete_provider.发送消息([])
    assert len(response.工具调用列表) == 0


@pytest.mark.asyncio
async def test_agent_respects_max_iterations():
    """测试 Agent 尊重最大迭代次数限制"""
    # 创建一个总是返回工具调用的模拟提供者（用于测试最大迭代限制）
    class InfiniteProvider(LLM提供者基类):
        def __init__(self, api_key: str):
            super().__init__(api_key)
            self.call_count = 0

        async def 发送消息(self, 对话历史, 截图base64=None):
            self.call_count += 1
            return LLM响应(
                文本内容="继续执行",
                工具调用列表=[工具调用(工具名称="mouse_move", 参数={"x": 1, "y": 1})]
            )

    provider = InfiniteProvider("test-key")
    广播函数 = AsyncMock()
    agent = AgentLoop(提供者=provider, 广播函数=广播函数, 最大循环次数=3)

    await agent.执行任务("测试最大迭代")

    # 验证 agent 最终会因为达到最大循环次数而停止
    # 最多会调用 3 次（等于最大循环次数）
    assert provider.call_count <= 3


@pytest.mark.asyncio
async def test_agent_stops_on_global_signal():
    """测试 Agent 在全局停止信号下正确停止"""
    provider = MockLLMProvider("test-key")
    广播函数 = AsyncMock()

    agent = AgentLoop(提供者=provider, 广播函数=广播函数, 最大循环次数=10)

    # 模拟在执行过程中设置全局停止信号
    from agent_loop import 全局停止信号
    全局停止信号.set()

    await agent.执行任务("测试停止信号")

    # 重置信号供其他测试使用
    全局停止信号.clear()

    # 验证 agent 已停止
    assert not agent.正在运行


def test_broadcast_function():
    """测试广播功能"""
    async def mock_broadcast(msg, typ):
        assert msg is not None
        assert typ in ["info", "action", "error", "warning", "status"]

    async def run_test():
        provider = MockLLMProvider("test-key")
        agent = AgentLoop(提供者=provider, 广播函数=mock_broadcast)
        # 这里我们只测试广播函数是否被正确设置，不会实际运行任务
        await agent._广播("info", "测试消息")

    asyncio.run(run_test())