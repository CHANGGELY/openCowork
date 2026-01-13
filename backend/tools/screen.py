"""
============================================
屏幕截图工具
============================================
这个文件负责"看"——截取屏幕内容。

我们使用 `mss` 库，它比 `pyautogui` 的截图快很多倍。
（类比：mss 是专业摄影师用的单反，pyautogui 是手机自带相机）

截图后会自动缩放到合适的尺寸，因为：
1. 原始截图太大（4K 屏幕可能有数 MB）
2. LLM API 对图片大小有限制
3. 缩小后能加快传输和处理速度
"""

from typing import Optional
import mss
from PIL import Image
from loguru import logger


def 截取屏幕(
    显示器编号: int = 1,
    最大宽度: int = 1280,
    最大高度: int = 800
) -> Optional[Image.Image]:
    """
    截取屏幕并返回 PIL Image 对象
    
    参数:
        显示器编号: 要截取的显示器，1 表示主显示器
        最大宽度: 输出图片的最大宽度（会等比缩放）
        最大高度: 输出图片的最大高度
    
    返回:
        PIL Image 对象，如果失败返回 None
    
    原理：
    1. mss 库直接读取显卡缓冲区（非常快）
    2. 获取的是原始 BGRA 数据
    3. 转换为 RGB 格式的 PIL Image
    4. 按比例缩放到目标尺寸
    """
    try:
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
                图片 = 图片.resize((新宽, 新高), Image.Resampling.LANCZOS)
                logger.debug(f"截图已缩放: {原宽}x{原高} → {新宽}x{新高}")
            
            return 图片
    
    except Exception as e:
        logger.error(f"截图失败: {e}")
        return None


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
