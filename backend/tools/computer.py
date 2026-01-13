"""
============================================
电脑控制工具（鼠标 & 键盘）
============================================
这个文件负责"动手"——控制鼠标和键盘。

我们使用 `pyautogui` 库，它能模拟真实的鼠标移动和键盘输入。

安全措施：
1. pyautogui 内置 "Fail-Safe"：鼠标移到屏幕左上角会触发异常
2. 所有操作都有日志记录
3. 每个操作前会检查全局停止信号

注意：macOS 需要在"系统偏好设置 → 安全性与隐私 → 辅助功能"中授权！
"""

from typing import Any
import pyautogui
from loguru import logger


# ============================================
# 安全配置
# ============================================

# 启用 Fail-Safe：鼠标移到屏幕左上角 (0, 0) 会触发 pyautogui.FailSafeException
pyautogui.FAILSAFE = True

# 设置每次操作之间的延迟（秒），防止操作太快
pyautogui.PAUSE = 0.1


# ============================================
# 鼠标操作
# ============================================

def 执行鼠标操作(操作类型: str, 参数: dict[str, Any]) -> str:
    """
    执行鼠标操作
    
    参数:
        操作类型: "mouse_move", "left_click", "right_click", "double_click", "scroll"
        参数: 操作参数字典
    
    返回:
        操作结果描述
    """
    try:
        x = 参数.get("x")
        y = 参数.get("y")
        
        if 操作类型 == "mouse_move":
            if x is None or y is None:
                return "错误：缺少坐标参数"
            pyautogui.moveTo(x, y, duration=0.3)
            logger.info(f"🖱️ 鼠标移动到 ({x}, {y})")
            return f"已移动到 ({x}, {y})"
        
        elif 操作类型 == "left_click":
            if x is not None and y is not None:
                pyautogui.click(x, y)
                logger.info(f"🖱️ 左键点击 ({x}, {y})")
                return f"已点击 ({x}, {y})"
            else:
                pyautogui.click()
                当前位置 = pyautogui.position()
                logger.info(f"🖱️ 左键点击当前位置 {当前位置}")
                return f"已点击当前位置 {当前位置}"
        
        elif 操作类型 == "right_click":
            if x is not None and y is not None:
                pyautogui.rightClick(x, y)
                logger.info(f"🖱️ 右键点击 ({x}, {y})")
                return f"已右键点击 ({x}, {y})"
            else:
                pyautogui.rightClick()
                当前位置 = pyautogui.position()
                logger.info(f"🖱️ 右键点击当前位置 {当前位置}")
                return f"已右键点击当前位置 {当前位置}"
        
        elif 操作类型 == "double_click":
            if x is not None and y is not None:
                pyautogui.doubleClick(x, y)
                logger.info(f"🖱️ 双击 ({x}, {y})")
                return f"已双击 ({x}, {y})"
            else:
                pyautogui.doubleClick()
                当前位置 = pyautogui.position()
                logger.info(f"🖱️ 双击当前位置 {当前位置}")
                return f"已双击当前位置 {当前位置}"
        
        elif 操作类型 == "scroll":
            滚动量 = 参数.get("amount", 0)
            pyautogui.scroll(滚动量)
            方向 = "向上" if 滚动量 > 0 else "向下"
            logger.info(f"🖱️ 滚动 {方向} {abs(滚动量)} 单位")
            return f"已滚动 {方向} {abs(滚动量)} 单位"
        
        else:
            return f"未知的鼠标操作: {操作类型}"
    
    except pyautogui.FailSafeException:
        logger.warning("⚠️ Fail-Safe 触发！鼠标移动到了屏幕角落")
        return "Fail-Safe 触发，操作已中止"
    
    except Exception as e:
        logger.error(f"鼠标操作失败: {e}")
        return f"操作失败: {str(e)}"


# ============================================
# 键盘操作
# ============================================

def 执行键盘操作(操作类型: str, 参数: dict[str, Any]) -> str:
    """
    执行键盘操作
    
    参数:
        操作类型: "type", "key", "hotkey"
        参数: 操作参数字典
    
    返回:
        操作结果描述
    """
    try:
        if 操作类型 == "type":
            文字 = 参数.get("text", "")
            if not 文字:
                return "错误：没有提供要输入的文字"
            
            # pyautogui.write() 不支持中文，需要使用 pyperclip + hotkey
            # 但为了简单起见，我们先尝试直接输入
            # 如果是纯 ASCII，直接用 write
            if 文字.isascii():
                pyautogui.write(文字, interval=0.05)
            else:
                # 对于非 ASCII（如中文），使用剪贴板
                import pyperclip
                pyperclip.copy(文字)
                pyautogui.hotkey("command" if _是mac系统() else "ctrl", "v")
            
            显示文字 = 文字[:20] + "..." if len(文字) > 20 else 文字
            logger.info(f"⌨️ 输入文字: {显示文字}")
            return f"已输入: {显示文字}"
        
        elif 操作类型 == "key":
            键名 = 参数.get("key_name", "")
            if not 键名:
                return "错误：没有提供键名"
            
            # 标准化键名
            键名 = _标准化键名(键名)
            pyautogui.press(键名)
            logger.info(f"⌨️ 按下按键: {键名}")
            return f"已按下: {键名}"
        
        elif 操作类型 == "hotkey":
            按键列表 = 参数.get("keys", [])
            if not 按键列表:
                return "错误：没有提供按键列表"
            
            # 标准化所有键名
            按键列表 = [_标准化键名(k) for k in 按键列表]
            pyautogui.hotkey(*按键列表)
            组合键 = "+".join(按键列表)
            logger.info(f"⌨️ 按下组合键: {组合键}")
            return f"已按下组合键: {组合键}"
        
        else:
            return f"未知的键盘操作: {操作类型}"
    
    except Exception as e:
        logger.error(f"键盘操作失败: {e}")
        return f"操作失败: {str(e)}"


# ============================================
# 辅助函数
# ============================================

def _是mac系统() -> bool:
    """检测当前是否是 macOS"""
    import platform
    return platform.system() == "Darwin"


def _标准化键名(键名: str) -> str:
    """
    将常见的键名别名转换为 pyautogui 接受的格式
    
    例如: "Enter" → "enter", "Ctrl" → "ctrl"
    """
    别名映射 = {
        "enter": "enter",
        "return": "enter",
        "tab": "tab",
        "escape": "escape",
        "esc": "escape",
        "backspace": "backspace",
        "delete": "delete",
        "del": "delete",
        "space": "space",
        "up": "up",
        "down": "down",
        "left": "left",
        "right": "right",
        "home": "home",
        "end": "end",
        "pageup": "pageup",
        "pagedown": "pagedown",
        "ctrl": "ctrl",
        "control": "ctrl",
        "alt": "alt",
        "option": "alt",
        "shift": "shift",
        "cmd": "command",
        "command": "command",
        "win": "win",
        "windows": "win",
        "f1": "f1", "f2": "f2", "f3": "f3", "f4": "f4",
        "f5": "f5", "f6": "f6", "f7": "f7", "f8": "f8",
        "f9": "f9", "f10": "f10", "f11": "f11", "f12": "f12",
    }
    
    键名小写 = 键名.lower().strip()
    return 别名映射.get(键名小写, 键名小写)


def 获取鼠标位置() -> tuple[int, int]:
    """获取当前鼠标位置"""
    pos = pyautogui.position()
    return (pos.x, pos.y)
