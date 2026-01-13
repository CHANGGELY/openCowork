"""
============================================
LLM 提供者抽象基类
============================================
这个文件定义了"LLM 提供者"的标准接口。

什么是"抽象基类"？（高中数学类比）
想象一个"函数模板"：f(x) = ?
我们只定义了输入和输出的格式，但没有定义具体怎么计算。
具体的计算由"子类"（OpenAI、Gemini、Anthropic）来实现。

这样做的好处：
主程序不需要关心用的是哪个 LLM，只需要调用统一的接口。
切换 Provider 就像换电池一样简单。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class 工具调用:
    """
    表示 LLM 返回的一个工具调用请求
    
    例如 LLM 说"帮我点击坐标 (500, 300)"，
    就会生成一个 工具调用 对象：
        工具名称 = "left_click"
        参数 = {"x": 500, "y": 300}
    """
    工具名称: str              # 工具名，如 "mouse_move", "left_click", "type"
    参数: dict[str, Any]       # 工具参数
    工具调用ID: str = ""       # 部分 Provider 需要 ID 来追踪调用结果


@dataclass
class LLM响应:
    """
    LLM 返回的响应
    
    可能包含：
    - 文本内容：LLM 的解释或回复
    - 工具调用列表：LLM 要求执行的操作
    """
    文本内容: Optional[str] = None                  # LLM 说的话
    工具调用列表: list[工具调用] = field(default_factory=list)  # 要执行的工具操作
    原始响应: Any = None                             # 保留原始 API 响应（debug 用）


class LLM提供者基类(ABC):
    """
    LLM 提供者的抽象基类
    
    所有具体的 Provider（OpenAI、Gemini、Anthropic）都必须继承这个类，
    并实现 `发送消息` 方法。
    """
    
    def __init__(self, api_key: str):
        """
        初始化提供者
        
        参数:
            api_key: 对应 Provider 的 API 密钥
        """
        self.api_key = api_key
    
    @abstractmethod
    async def 发送消息(
        self,
        对话历史: list[dict],
        截图base64: Optional[str] = None
    ) -> LLM响应:
        """
        发送消息给 LLM，获取响应
        
        这是一个"抽象方法"——这里只定义接口，具体实现由子类完成。
        
        参数:
            对话历史: 之前的对话记录，格式: [{"role": "user/assistant", "content": "..."}]
            截图base64: 当前屏幕截图的 Base64 编码（可选）
        
        返回:
            LLM响应 对象，包含文本和工具调用
        """
        pass  # 子类必须实现这个方法
    
    @property
    def 提供者名称(self) -> str:
        """返回提供者的名称，用于日志显示"""
        return self.__class__.__name__


# ============================================
# 通用工具定义（所有 Provider 共享）
# ============================================

# 这些是我们定义的"虚拟工具"，告诉 LLM：你可以用这些操作来控制电脑
COMPUTER_USE_TOOLS = [
    {
        "name": "mouse_move",
        "description": "将鼠标移动到屏幕上的指定坐标 (x, y)。坐标原点在屏幕左上角。",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "目标 X 坐标（像素）"},
                "y": {"type": "integer", "description": "目标 Y 坐标（像素）"}
            },
            "required": ["x", "y"]
        }
    },
    {
        "name": "left_click",
        "description": "在当前鼠标位置执行左键单击。如果提供坐标，先移动再点击。",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "可选：点击的 X 坐标"},
                "y": {"type": "integer", "description": "可选：点击的 Y 坐标"}
            }
        }
    },
    {
        "name": "right_click",
        "description": "在当前鼠标位置执行右键单击。",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "可选：点击的 X 坐标"},
                "y": {"type": "integer", "description": "可选：点击的 Y 坐标"}
            }
        }
    },
    {
        "name": "double_click",
        "description": "在当前鼠标位置执行双击。",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "可选：点击的 X 坐标"},
                "y": {"type": "integer", "description": "可选：点击的 Y 坐标"}
            }
        }
    },
    {
        "name": "scroll",
        "description": "滚动鼠标滚轮。正数向上滚动，负数向下滚动。",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {"type": "integer", "description": "滚动量，正数向上，负数向下"}
            },
            "required": ["amount"]
        }
    },
    {
        "name": "type",
        "description": "在当前焦点位置输入文字。",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "要输入的文字"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "key",
        "description": "按下一个特殊键，如 Enter、Tab、Escape 等。",
        "parameters": {
            "type": "object",
            "properties": {
                "key_name": {"type": "string", "description": "键名，如 'enter', 'tab', 'escape', 'backspace'"}
            },
            "required": ["key_name"]
        }
    },
    {
        "name": "hotkey",
        "description": "按下组合键，如 Ctrl+C、Ctrl+V 等。",
        "parameters": {
            "type": "object",
            "properties": {
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "按键列表，如 ['ctrl', 'c'] 表示 Ctrl+C"
                }
            },
            "required": ["keys"]
        }
    }
]


# ============================================
# 系统提示词（告诉 LLM 它是一个电脑控制助手）
# ============================================

SYSTEM_PROMPT = """你是一个能够控制用户电脑的 AI 助手。
当前使用的模型是：{model_name}。如果用户问你是谁或用什么模型，请如实回答。

你可以看到用户屏幕的截图，并使用以下工具来操作电脑：
- mouse_move: 移动鼠标到指定坐标
- left_click: 左键单击
- right_click: 右键单击
- double_click: 双击
- scroll: 滚动滚轮
- type: 输入文字
- key: 按下特殊键
- hotkey: 按下组合键

工作流程：
1. 仔细观察截图，理解当前屏幕状态
2. 根据用户指令，决定下一步操作
3. 执行操作后，等待新的截图来确认结果
4. 重复以上步骤直到任务完成

注意事项：
- 坐标使用像素值，原点在屏幕左上角
- 如果不确定元素位置，可以先移动鼠标观察
- 每次只执行一个操作，等待反馈后再继续
- 任务完成后，直接回复文字说明，不要调用工具

请用中文回复用户。
"""
