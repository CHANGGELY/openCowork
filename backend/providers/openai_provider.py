"""
============================================
OpenAI Provider 适配器
============================================
这个文件实现了 OpenAI GPT-4o 的接口适配。

GPT-4o 支持：
1. Vision（视觉）：可以理解图片内容
2. Function Calling（函数调用）：可以输出结构化的工具调用

我们利用这两个能力，让 GPT-4o 也能"控制电脑"。
"""

import json
from typing import Optional

from openai import AsyncOpenAI
from loguru import logger

from .base import LLM提供者基类, LLM响应, 工具调用, COMPUTER_USE_TOOLS, SYSTEM_PROMPT


class OpenAI提供者(LLM提供者基类):
    """
    OpenAI GPT-4o 提供者适配器
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        初始化 OpenAI 客户端
        
        参数:
            api_key: OpenAI API 密钥
            model: 使用的模型，默认 gpt-4o（支持视觉）
        """
        super().__init__(api_key)
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        logger.info(f"✅ OpenAI 提供者已初始化，模型: {model}")
    
    async def 发送消息(
        self,
        对话历史: list[dict],
        截图base64: Optional[str] = None
    ) -> LLM响应:
        """
        发送消息给 GPT-4o
        """
        try:
            # 构建消息列表
            system_content = SYSTEM_PROMPT.format(model_name=self.model)
            messages = [{"role": "system", "content": system_content}]
            
            # 添加对话历史
            for 消息 in 对话历史:
                messages.append({
                    "role": 消息["role"],
                    "content": 消息["content"]
                })
            
            # 如果有截图，添加到最后一条消息
            if 截图base64:
                # 创建包含图片的消息
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "这是当前屏幕截图，请根据截图内容和之前的指令决定下一步操作。"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{截图base64}",
                                "detail": "high"  # 高分辨率模式
                            }
                        }
                    ]
                })
            
            # 将我们的工具定义转换为 OpenAI 格式
            tools = self._转换工具定义()
            
            # 调用 API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",  # 让模型自己决定是否调用工具
                max_tokens=1024
            )
            
            # 解析响应
            return self._解析响应(response)
        
        except Exception as e:
            logger.error(f"OpenAI API 调用失败: {e}")
            raise
    
    def _转换工具定义(self) -> list[dict]:
        """
        将我们的通用工具定义转换为 OpenAI 的 Function Calling 格式
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            }
            for tool in COMPUTER_USE_TOOLS
        ]
    
    def _解析响应(self, response) -> LLM响应:
        """
        解析 OpenAI API 的响应
        """
        choice = response.choices[0]
        message = choice.message
        
        结果 = LLM响应(原始响应=response)
        
        # 提取文本内容
        if message.content:
            结果.文本内容 = message.content
        
        # 提取工具调用
        if message.tool_calls:
            for tool_call in message.tool_calls:
                func = tool_call.function
                try:
                    参数 = json.loads(func.arguments) if func.arguments else {}
                except json.JSONDecodeError:
                    参数 = {}
                
                结果.工具调用列表.append(工具调用(
                    工具名称=func.name,
                    参数=参数,
                    工具调用ID=tool_call.id
                ))
        
        return 结果
    
    @property
    def 提供者名称(self) -> str:
        return "OpenAI"
