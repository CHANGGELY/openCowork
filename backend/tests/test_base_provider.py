"""
测试 LLM 提供者基类和相关数据结构
"""
import pytest
from providers.base import LLM提供者基类, 工具调用, LLM响应


class MockProvider(LLM提供者基类):
    """用于测试的模拟提供者"""

    async def 发送消息(self, 对话历史, 截图base64=None):
        # 模拟 API 调用返回
        return LLM响应(
            文本内容="这是一个模拟响应",
            工具调用列表=[
                工具调用(工具名称="mouse_move", 参数={"x": 100, "y": 200})
            ]
        )


def test_工具调用创建():
    """测试工具调用对象的创建"""
    工具 = 工具调用(
        工具名称="mouse_move",
        参数={"x": 100, "y": 200},
        工具调用ID="test-id"
    )

    assert 工具.工具名称 == "mouse_move"
    assert 工具.参数 == {"x": 100, "y": 200}
    assert 工具.工具调用ID == "test-id"


def test_llm响应创建():
    """测试LLM响应对象的创建"""
    响应 = LLM响应(
        文本内容="测试内容",
        工具调用列表=[
            工具调用(工具名称="test", 参数={})
        ]
    )

    assert 响应.文本内容 == "测试内容"
    assert len(响应.工具调用列表) == 1
    assert 响应.工具调用列表[0].工具名称 == "test"


def test_provider初始化():
    """测试提供者的初始化"""
    provider = MockProvider("test-key")
    assert provider.api_key == "test-key"
    assert provider.提供者名称 == "MockProvider"


@pytest.mark.asyncio
async def test_mock_provider():
    """测试模拟提供者的功能"""
    provider = MockProvider("test-key")
    响应 = await provider.发送消息([{"role": "user", "content": "hello"}])

    assert 响应.文本内容 == "这是一个模拟响应"
    assert len(响应.工具调用列表) == 1
    assert 响应.工具调用列表[0].工具名称 == "mouse_move"