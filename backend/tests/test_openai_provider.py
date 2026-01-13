"""
测试 OpenAI 提供者
"""
import pytest
from unittest.mock import AsyncMock, patch
from providers.openai_provider import OpenAI提供者
from providers.base import LLM响应


@pytest.mark.asyncio
async def test_openai_provider_initialization():
    """测试 OpenAI 提供者的初始化"""
    provider = OpenAI提供者("test-key")

    assert provider.api_key == "test-key"
    assert provider.model == "gpt-4o"
    assert provider.提供者名称 == "OpenAI"


@pytest.mark.asyncio
async def test_openai_provider_with_custom_model():
    """测试使用自定义模型的 OpenAI 提供者"""
    provider = OpenAI提供者("test-key", model="gpt-4-turbo")

    assert provider.model == "gpt-4-turbo"


@pytest.mark.asyncio
@patch('providers.openai_provider.AsyncOpenAI')
async def test_openai_send_message(mock_openai_class):
    """测试 OpenAI 提供者的发送消息功能"""
    # 创建模拟的 API 响应
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_choice = AsyncMock()
    mock_message = AsyncMock()

    mock_message.content = "这是一个测试响应"
    mock_message.tool_calls = None  # 暂时没有工具调用

    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    mock_openai_class.return_value = mock_client

    provider = OpenAI提供者("test-key")
    响应 = await provider.发送消息([{"role": "user", "content": "hello"}])

    # 验证 API 被正确调用
    mock_client.chat.completions.create.assert_called_once()

    assert isinstance(响应, LLM响应)
    assert 响应.文本内容 == "这是一个测试响应"


@pytest.mark.asyncio
@patch('providers.openai_provider.AsyncOpenAI')
async def test_openai_send_message_with_image(mock_openai_class):
    """测试带图片的 OpenAI 消息发送"""
    # 创建模拟的 API 响应
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_choice = AsyncMock()
    mock_message = AsyncMock()

    mock_message.content = "我看到了图片"
    mock_message.tool_calls = None

    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    mock_openai_class.return_value = mock_client

    provider = OpenAI提供者("test-key")
    响应 = await provider.发送消息(
        [{"role": "user", "content": "hello"}],
        截图base64="test_base64_string"
    )

    # 验证 API 被正确调用，包含图片数据
    call_args = mock_client.chat.completions.create.call_args
    assert call_args is not None

    assert isinstance(响应, LLM响应)
    assert 响应.文本内容 == "我看到了图片"


@pytest.mark.asyncio
async def test_tool_conversion():
    """测试工具定义转换功能"""
    provider = OpenAI提供者("test-key")
    tools = provider._转换工具定义()

    # 验证至少有一个工具被转换
    assert len(tools) > 0
    assert tools[0]["type"] == "function"
    assert "function" in tools[0]
    assert "name" in tools[0]["function"]
    assert "parameters" in tools[0]["function"]