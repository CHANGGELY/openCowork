"""
测试工具模块（屏幕截图和电脑控制）
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# 添加 backend 目录到路径，以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.screen import 截取屏幕
from tools.computer import 执行鼠标操作, 执行键盘操作


def test_screen_capture_stub():
    """屏幕截图功能的测试桩（由于实际截图需要图形环境）"""
    # 由于截图功能依赖于实际的图形环境，我们只验证其存在和签名
    assert callable(截取屏幕)
    # 注意：这个测试在无头环境中无法实际运行截图，因此我们只验证函数存在


def test_mouse_operations():
    """测试鼠标操作函数"""
    # 测试 mouse_move
    result = 执行鼠标操作("mouse_move", {"x": 100, "y": 200})
    assert isinstance(result, str)
    assert "移动到" in result or "移到" in result

    # 测试 left_click
    result = 执行鼠标操作("left_click", {"x": 100, "y": 200})
    assert isinstance(result, str)
    assert "点击" in result

    # 测试 right_click
    result = 执行鼠标操作("right_click", {"x": 100, "y": 200})
    assert isinstance(result, str)
    assert "右键点击" in result

    # 测试 double_click
    result = 执行鼠标操作("double_click", {"x": 100, "y": 200})
    assert isinstance(result, str)
    assert "双击" in result

    # 测试 scroll
    result = 执行鼠标操作("scroll", {"amount": 1})
    assert isinstance(result, str)
    assert "滚动" in result

    # 测试不带坐标的点击
    result = 执行鼠标操作("left_click", {})
    assert isinstance(result, str)


def test_keyboard_operations():
    """测试键盘操作函数"""
    # 测试 type
    result = 执行键盘操作("type", {"text": "hello"})
    assert isinstance(result, str)
    assert "输入" in result

    # 测试 key
    result = 执行键盘操作("key", {"key_name": "enter"})
    assert isinstance(result, str)
    assert "按下" in result

    # 测试 hotkey
    result = 执行键盘操作("hotkey", {"keys": ["ctrl", "c"]})
    assert isinstance(result, str)
    assert "组合键" in result or "按下" in result

    # 测试未知操作
    result = 执行键盘操作("unknown_operation", {})
    assert isinstance(result, str)
    assert "未知" in result


@patch('tools.computer.pyautogui')
def test_mouse_operations_with_mock(mock_pyautogui):
    """使用模拟对象测试鼠标操作"""
    # 设置模拟返回值
    mock_pyautogui.position.return_value = (100, 100)

    # 测试 mouse_move
    result = 执行鼠标操作("mouse_move", {"x": 200, "y": 300})
    mock_pyautogui.moveTo.assert_called_once_with(200, 300, duration=0.3)


@patch('tools.computer.pyautogui')
def test_keyboard_operations_with_mock(mock_pyautogui):
    """使用模拟对象测试键盘操作"""
    # 测试 type - 对于ASCII字符，使用write
    result = 执行键盘操作("type", {"text": "hello world"})
    # 根据代码，ASCII字符会使用write方法
    mock_pyautogui.write.assert_called_once_with("hello world", interval=0.05)

    # 重置 mock
    mock_pyautogui.reset_mock()

    # 测试 key
    result = 执行键盘操作("key", {"key_name": "enter"})
    mock_pyautogui.press.assert_called_once_with("enter")

    # 重置 mock
    mock_pyautogui.reset_mock()

    # 测试 hotkey
    result = 执行键盘操作("hotkey", {"keys": ["ctrl", "c"]})
    mock_pyautogui.hotkey.assert_called_once_with("ctrl", "c")


def test_invalid_operations():
    """测试无效操作的处理"""
    # 测试无效的鼠标操作
    result = 执行鼠标操作("invalid_operation", {})
    assert isinstance(result, str)

    # 测试无效的键盘操作
    result = 执行键盘操作("invalid_operation", {})
    assert isinstance(result, str)