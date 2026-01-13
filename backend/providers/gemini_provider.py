"""
============================================
Google Gemini Provider 适配器
============================================
这个文件实现了 Google Gemini 2.0 的接口适配。

Gemini 2.0 Flash 支持：
1. Multimodal（多模态）：可以理解图片
2. Function Calling：可以调用自定义函数

和 OpenAI 类似，我们定义工具 Schema，让 Gemini 输出结构化的操作指令。
"""

from typing import Optional

import google.generativeai as genai
from loguru import logger

from .base import LLM提供者基类, LLM响应, 工具调用, COMPUTER_USE_TOOLS, SYSTEM_PROMPT


class Gemini提供者(LLM提供者基类):
    """
    Google Gemini 2.0 提供者适配器
    """
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        """
        初始化 Gemini 客户端
        
        参数:
            api_key: Google AI API 密钥
            model: 使用的模型，默认 gemini-2.0-flash
        """
        super().__init__(api_key)
        genai.configure(api_key=api_key)
        self.model_name = model
        
        # 创建工具定义（使用字典格式，兼容新版 SDK）
        self._tools = self._创建工具定义()
        
        # 创建模型
        self.model = genai.GenerativeModel(
            model_name=model,
            system_instruction=SYSTEM_PROMPT.format(model_name=model),
            tools=self._tools
        )
        
        logger.info(f"✅ Gemini 提供者已初始化，模型: {model}")
    
    async def 发送消息(
        self,
        对话历史: list[dict],
        截图base64: Optional[str] = None
    ) -> LLM响应:
        """
        发送消息给 Gemini
        """
        try:
            # 构建内容列表
            contents = []
            
            # 添加对话历史
            for 消息 in 对话历史:
                role = "user" if 消息["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": 消息["content"]}]
                })
            
            # 如果有截图，添加到内容中
            if 截图base64:
                contents.append({
                    "role": "user",
                    "parts": [
                        {"text": "这是当前屏幕截图，请根据截图内容和之前的指令决定下一步操作。"},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": 截图base64
                            }
                        }
                    ]
                })
            
            # 调用 API
            response = self.model.generate_content(
                contents,
                generation_config={
                    "max_output_tokens": 1024,
                    "temperature": 0.7
                }
            )
            
            # 解析响应
            return self._解析响应(response)
        
        except Exception as e:
            logger.error(f"Gemini API 调用失败: {e}")
            raise
    
    def _创建工具定义(self) -> list:
        """
        将我们的通用工具定义转换为 Gemini 的 Tool 格式
        使用字典格式定义，兼容 google-generativeai SDK
        """
        function_declarations = []
        
        for tool in COMPUTER_USE_TOOLS:
            # 使用字典格式定义函数（SDK 会自动转换）
            func_decl = {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": tool["parameters"].get("required", [])
                }
            }
            
            # 转换属性
            for prop_name, prop_def in tool["parameters"].get("properties", {}).items():
                prop_type = prop_def.get("type", "string")
                
                if prop_type == "integer":
                    func_decl["parameters"]["properties"][prop_name] = {
                        "type": "integer",
                        "description": prop_def.get("description", "")
                    }
                elif prop_type == "array":
                    func_decl["parameters"]["properties"][prop_name] = {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": prop_def.get("description", "")
                    }
                else:
                    func_decl["parameters"]["properties"][prop_name] = {
                        "type": "string",
                        "description": prop_def.get("description", "")
                    }
            
            function_declarations.append(func_decl)
        
        # 返回工具列表（使用字典格式）
        return [{"function_declarations": function_declarations}]
    
    def _解析响应(self, response) -> LLM响应:
        """
        解析 Gemini API 的响应
        """
        结果 = LLM响应(原始响应=response)
        
        # 检查是否有有效的候选响应
        if not response.candidates:
            return 结果
        
        candidate = response.candidates[0]
        
        # 遍历所有 parts
        for part in candidate.content.parts:
            # 文本内容
            if hasattr(part, 'text') and part.text:
                结果.文本内容 = (结果.文本内容 or "") + part.text
            
            # 函数调用
            if hasattr(part, 'function_call') and part.function_call:
                fc = part.function_call
                参数 = dict(fc.args) if fc.args else {}
                
                结果.工具调用列表.append(工具调用(
                    工具名称=fc.name,
                    参数=参数
                ))
        
        return 结果
    
    @property
    def 提供者名称(self) -> str:
        return "Gemini"
