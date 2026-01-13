"""
============================================
屏幕截图工具
============================================
这个文件负责"看"——截取屏幕内容。

我们使用 `mss` 库，它比 `pyautogui` 的截图快很多倍。
（类比：mss 是专业摄影师用的单反，pyautogui 是手机自带相机）

性能优化：
1. 添加缓存机制，避免在短时间内重复截图
2. 优化缩放算法，平衡质量和速度
3. 使用更快的缩放方法

截图后会自动缩放到合适的尺寸，因为：
1. 原始截图太大（4K 屏幕可能有数 MB）
2. LLM API 对图片大小有限制
3. 缩小后能加快传输和处理速度
"""

import time
from typing import Optional
import mss
from PIL import Image
from loguru import logger


class 截图缓存:
    """
    截图缓存类，避免在短时间内重复截图
    """
    def __init__(self, 缓存超时: float = 0.5):  # 0.5秒缓存
        self.上次截图时间 = 0
        self.缓存截图: Optional[Image.Image] = None
        self.缓存超时 = 缓存超时

    def 获取截图(self) -> Optional[Image.Image]:
        """获取缓存的截图或返回None"""
        当前时间 = time.time()
        if (self.缓存截图 is not None and
            当前时间 - self.上次截图时间 < self.缓存超时):
            return self.缓存截图
        return None

    def 设置截图(self, 截图: Image.Image):
        """设置缓存截图"""
        self.缓存截图 = 截图
        self.上次截图时间 = time.time()

    def 清除缓存(self):
        """清除缓存"""
        self.缓存截图 = None
        self.上次截图时间 = 0


# 全局截图缓存实例
全局截图缓存 = 截图缓存()


def 截取屏幕(
    显示器编号: int = 1,
    最大宽度: int = 1280,
    最大高度: int = 800,
    使用缓存: bool = True,
    快速缩放: bool = True
) -> Optional[Image.Image]:
    """
    截取屏幕并返回 PIL Image 对象

    参数:
        显示器编号: 要截取的显示器，1 表示主显示器
        最大宽度: 输出图片的最大宽度（会等比缩放）
        最大高度: 输出图片的最大高度
        使用缓存: 是否使用截图缓存，默认True
        快速缩放: 是否使用快速缩放算法，默认True（速度优先）

    返回:
        PIL Image 对象，如果失败返回 None

    原理：
    1. mss 库直接读取显卡缓冲区（非常快）
    2. 获取的是原始 BGRA 数据
    3. 转换为 RGB 格式的 PIL Image
    4. 按比例缩放到目标尺寸
    """
    try:
        # 检查缓存
        if 使用缓存:
            缓存截图 = 全局截图缓存.获取截图()
            if 缓存截图 is not None:
                return 缓存截图.copy()  # 返回副本，避免外部修改缓存

        with mss.mss() as sct:
            # 获取显示器信息
            # monitors[0] 是所有屏幕的合并，monitors[1] 是主屏幕
            if 显示器编号 >= len(sct.monitors):
                显示器编号 = 1  # 默认主屏幕

            监视器 = sct.monitors[显示器编号]

            # 截图
            截图 = sct.grab(监视器)

            # 转换为 PIL Image（mss 输出是 BGRA，需要转 RGB）
            图片 = Image.frombytes("RGB", 截图.size, 截图.bgra, "raw", "BGRX")

            # 获取原始尺寸
            原宽, 原高 = 图片.size

            # 计算缩放比例（保持宽高比）
            宽度比 = 最大宽度 / 原宽
            高度比 = 最大高度 / 原高
            缩放比 = min(宽度比, 高度比, 1.0)  # 不放大，只缩小

            if 缩放比 < 1.0:
                新宽 = int(原宽 * 缩放比)
                新高 = int(原高 * 缩放比)
                # 根据参数选择缩放质量
                缩放算法 = Image.Resampling.BILINEAR if 快速缩放 else Image.Resampling.LANCZOS
                图片 = 图片.resize((新宽, 新高), 缩放算法)
                logger.debug(f"截图已缩放: {原宽}x{原高} → {新宽}x{新高}")

            # 如果启用了缓存，保存到缓存
            if 使用缓存:
                全局截图缓存.设置截图(图片)

            return 图片

    except Exception as e:
        logger.error(f"截图失败: {e}")
        return None


class 截图缓存:
    """
    截图缓存类，避免在短时间内重复截图
    """
    def __init__(self, 缓存超时: float = 0.5):  # 0.5秒缓存
        self.上次截图时间 = 0
        self.缓存截图: Optional[Image.Image] = None
        self.缓存超时 = 缓存超时

    def 获取截图(self) -> Optional[Image.Image]:
        """获取缓存的截图或返回None"""
        当前时间 = time.time()
        if (self.缓存截图 is not None and
            当前时间 - self.上次截图时间 < self.缓存超时):
            return self.缓存截图
        return None

    def 设置截图(self, 截图: Image.Image):
        """设置缓存截图"""
        self.缓存截图 = 截图
        self.上次截图时间 = time.time()

    def 清除缓存(self):
        """清除缓存"""
        self.缓存截图 = None
        self.上次截图时间 = 0


def 获取屏幕尺寸() -> tuple[int, int]:
    """
    获取主屏幕的分辨率
    
    返回:
        (宽度, 高度) 元组
    """
    try:
        with mss.mss() as sct:
            监视器 = sct.monitors[1]  # 主屏幕
            return (监视器["width"], 监视器["height"])
    except Exception as e:
        logger.error(f"获取屏幕尺寸失败: {e}")
        return (1920, 1080)  # 默认值


def 获取所有显示器() -> list[dict]:
    """
    获取所有显示器的信息
    
    返回:
        显示器信息列表，每个元素包含 left, top, width, height
    """
    try:
        with mss.mss() as sct:
            return [
                {
                    "index": i,
                    "left": m["left"],
                    "top": m["top"],
                    "width": m["width"],
                    "height": m["height"]
                }
                for i, m in enumerate(sct.monitors)
                if i > 0  # 跳过 monitors[0]（合并屏幕）
            ]
    except Exception as e:
        logger.error(f"获取显示器列表失败: {e}")
        return []
