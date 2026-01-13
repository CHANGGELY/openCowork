"""
性能测试模块
"""
import time
import pytest
from unittest.mock import patch
from tools.screen import 截图缓存, 截取屏幕


def test_screenshot_caching_performance():
    """测试截图缓存性能"""
    # 创建缓存实例
    cache = 截图缓存(缓存超时=1.0)  # 1秒超时

    # 模拟一个图片对象
    class MockImage:
        def copy(self):
            return self

    mock_img = MockImage()

    # 第一次设置
    cache.设置截图(mock_img)
    result1 = cache.获取截图()
    assert result1 is not None

    # 立即再次获取，应该返回缓存
    result2 = cache.获取截图()
    assert result2 is not None


def test_screenshot_caching_timeout():
    """测试截图缓存超时"""
    import time
    from unittest.mock import patch

    # 创建超时为0.1秒的缓存
    cache = 截图缓存(缓存超时=0.1)

    class MockImage:
        def copy(self):
            return self

    mock_img = MockImage()

    # 设置缓存
    cache.设置截图(mock_img)

    # 立即获取，应该有缓存
    result1 = cache.获取截图()
    assert result1 is not None

    # 等待超过超时时间
    time.sleep(0.2)

    # 再次获取，应该没有缓存
    result2 = cache.获取截图()
    assert result2 is None


def test_screenshot_caching_clear():
    """测试清除缓存功能"""
    cache = 截图缓存()

    class MockImage:
        def copy(self):
            return self

    mock_img = MockImage()
    cache.设置截图(mock_img)

    # 验证有缓存
    assert cache.获取截图() is not None

    # 清除缓存
    cache.清除缓存()

    # 验证没有缓存
    assert cache.获取截图() is None


def test_screenshot_function_uses_cache_logic():
    """测试缓存机制的逻辑"""
    # 简单测试缓存机制的逻辑
    cache = 截图缓存()

    class MockImage:
        def __init__(self, name):
            self.name = name

        def resize(self, size, resample):
            return self

        def copy(self):
            # 返回一个新的实例，而不是修改名称
            return MockImage(f"{self.name}")

    # 设置初始缓存
    original_img = MockImage("original")
    cache.设置截图(original_img)

    # 尝试获取，应该返回缓存的图片
    cached_img = cache.获取截图()
    assert cached_img is not None
    assert cached_img.name == "original"


def test_performance_comparison_flags():
    """测试截图函数参数性能标记"""
    # 仅测试函数是否能接受新参数
    # 实际的性能测试需要真实的屏幕环境

    # 验证函数签名包含新参数
    import inspect
    from tools.screen import 截取屏幕

    sig = inspect.signature(截取屏幕)
    params = sig.parameters

    assert '使用缓存' in params
    assert '快速缩放' in params

    print("✅ 截图函数参数验证通过")