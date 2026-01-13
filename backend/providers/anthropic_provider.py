"""
============================================
Anthropic Claude Provider 适配器
============================================
这个文件实现了 Anthropic Claude 的接口适配。

Claude 是唯一一个**原生支持 Computer Use**的模型！
Anthropic 专门训练了 Claude 来理解屏幕截图并输出精确的操作坐标。

所以使用 Claude 的体验会比 OpenAI/Gemini 更好（理论上）。
"""

from typing import Optional

import anthropic
from loguru import logger

from .base import LLM提供者基类, LLM响应, 工具调用, SYSTEM_PROMPT


class Anthropic提供者(LLM提供者基类):
    """
    Anthropic Claude 提供者适配器
    
    使用 Claude 原生的 Computer Use 能力，不需要自定义工具定义。
    """
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        初始化 Anthropic 客户端
        
        参数:
            api_key: Anthropic API 密钥
            model: 使用的模型
        """
        super().__init__(api_key)
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        logger.info(f"✅ Anthropic 提供者已初始化，模型: {model}")
    
    async def 发送消息(
        self,
        对话历史: list[dict],
        截图base64: Optional[str] = None
    ) -> LLM响应:
        """
        发送消息给 Claude
        
        使用 Computer Use Beta API
        """
        try:
            # 构建消息列表
            messages = []
            
            # 添加对话历史
            for 消息 in 对话历史:
                messages.append({
                    "role": 消息["role"],
                    "content": 消息["content"]
                })
            
            # 如果有截图，构建特殊的图片消息
            if 截图base64:
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "这是当前屏幕截图，请根据截图内容和之前的指令决定下一步操作。"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": 截图base64
                            }
                        }
                    ]
                })
            
            # 定义 Computer Use 工具（Claude 原生支持）
            tools = self._定义原生工具()
            
            # 调用 API（使用 beta header 启用 Computer Use）
            response = await self.client.beta.messages.create(
                model=self.model,
                max_tokens=1024,
                system=SYSTEM_PROMPT.format(model_name=self.model),
                messages=messages,
                tools=tools,
                betas=["computer-use-2024-10-22"]  # 启用 Computer Use
            )
            
            # 解析响应
            return self._解析响应(response)
        
        except Exception as e:
            logger.error(f"Anthropic API 调用失败: {e}")
            raise
    
    def _定义原生工具(self) -> list[dict]:
        """
        定义 Claude 原生的 Computer Use 工具
        
        Claude 有一个特殊的 'computer' 工具类型，专门用于屏幕操作。
        但为了与其他 Provider 统一，我们也可以使用自定义工具。
        这里我们使用自定义工具，以便与其他 Provider 保持一致的接口。
        """
        return [
            {
                "name": "mouse_move",
                "description": "将鼠标移动到屏幕上的指定坐标 (x, y)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "目标 X 坐标"},
                        "y": {"type": "integer", "description": "目标 Y 坐标"}
                    },
                    "required": ["x", "y"]
                }
            },
            {
                "name": "left_click",
                "description": "在当前或指定位置执行左键单击",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "点击的 X 坐标"},
                        "y": {"type": "integer", "description": "点击的 Y 坐标"}
                    }
                }
            },
            {
                "name": "right_click",
                "description": "执行右键单击",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer"},
                        "y": {"type": "integer"}
                    }
                }
            },
            {
                "name": "double_click",
                "description": "执行双击",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer"},
                        "y": {"type": "integer"}
                    }
                }
            },
            {
                "name": "scroll",
                "description": "滚动鼠标滚轮",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "integer", "description": "滚动量，正数向上，负数向下"}
                    },
                    "required": ["amount"]
                }
            },
            {
                "name": "type",
                "description": "输入文字",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "要输入的文字"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "key",
                "description": "按下特殊键",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "key_name": {"type": "string", "description": "键名"}
                    },
                    "required": ["key_name"]
                }
            },
            {
                "name": "hotkey",
                "description": "按下组合键",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "keys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "按键列表"
                        }
                    },
                    "required": ["keys"]
                }
            }
        ]
    
    def _解析响应(self, response) -> LLM响应:
        """
        解析 Claude API 的响应
        """
        结果 = LLM响应(原始响应=response)
        
        # 遍历响应内容
        for block in response.content:
            if block.type == "text":
                结果.文本内容 = (结果.文本内容 or "") + block.text
            
            elif block.type == "tool_use":
                结果.工具调用列表.append(工具调用(
                    工具名称=block.name,
                    参数=block.input or {},
                    工具调用ID=block.id
                ))
        
        return 结果
    
    @property
    def 提供者名称(self) -> str:
        return "Anthropic"
