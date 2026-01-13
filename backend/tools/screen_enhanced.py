"""
============================================
增强版屏幕截图工具
============================================
这个文件实现了智能截图缓存，能够检测屏幕内容变化。

主要改进：
1. 基于内容差异的智能缓存
2. 自适应缓存超时
3. 区域变化检测
4. 性能监控
"""

import time
import hashlib
import asyncio
from typing import Optional, Tuple, Dict
import mss
import numpy as np
from PIL import Image
from loguru import logger


class 智能截图缓存:
    """
    智能截图缓存类，基于内容差异进行缓存
    """
    def __init__(self, 基础超时: float = 0.5, 最大超时: float = 2.0):
        self.上次截图时间 = 0
        self.缓存截图: Optional[Image.Image] = None
        self.缓存哈希: Optional[str] = None
        self.基础超时 = 基础超时  # 基础缓存超时
        self.最大超时 = 最大超时  # 最大缓存超时
        self.自适应超时 = 基础超时  # 当前使用的超时
        self.无变化次数 = 0  # 连续无变化次数
        self.性能统计 = {
            "总截图次数": 0,
            "缓存命中次数": 0,
            "节省时间": 0.0
        }

    def 计算图像哈希(self, 图像: Image.Image) -> str:
        """计算图像的感知哈希，用于检测变化"""
        # 缩小图像以加速哈希计算
        小图像 = 图像.resize((32, 32), Image.Resampling.LANCZOS).convert('L')
        像素数据 = np.array(小图像)

        # 计算均值
        均值 = np.mean(像素数据)

        # 生成哈希
        哈希 = ''.join(['1' if 像素 > 均值 else '0' for 像素 in 像素数据.flatten()])
        return hashlib.md5(哈希.encode()).hexdigest()[:16]

    def 获取截图(self, 强制刷新: bool = False) -> Optional[Tuple[Image.Image, bool]]:
        """
        获取截图，返回 (截图, 是否来自缓存)
        """
        当前时间 = time.time()
        self.性能统计["总截图次数"] += 1

        # 检查是否可以使用缓存
        if (not 强制刷新 and
            self.缓存截图 is not None and
            当前时间 - self.上次截图时间 < self.自适应超时):

            self.性能统计["缓存命中次数"] += 1
            self.性能统计["节省时间"] += self.自适应超时
            return self.缓存截图.copy(), True

        return None, False

    def 设置截图(self, 截图: Image.Image) -> Tuple[bool, float]:
        """
        设置缓存截图，返回 (是否有变化, 处理时间)
        """
        开始时间 = time.time()
        新哈希 = self.计算图像哈希(截图)
        有变化 = True

        # 比较哈希值
        if self.缓存哈希 is not None and 新哈希 == self.缓存哈希:
            有变化 = False
            self.无变化次数 += 1

            # 自适应调整超时时间
            if self.无变化次数 > 5:
                self.自适应超时 = min(self.自适应超时 * 1.2, self.最大超时)
                logger.debug(f"📈 缓存超时自适应增加到 {self.自适应超时:.2f}s")
        else:
            self.无变化次数 = 0
            self.自适应超时 = max(self.基础超时, self.自适应超时 * 0.8)

        self.缓存截图 = 截图.copy()
        self.缓存哈希 = 新哈希
        self.上次截图时间 = time.time()

        处理时间 = time.time() - 开始时间
        return 有变化, 处理时间

    def 获取性能统计(self) -> Dict:
        """获取性能统计信息"""
        命中率 = 0
        if self.性能统计["总截图次数"] > 0:
            命中率 = self.性能统计["缓存命中次数"] / self.性能统计["总截图次数"] * 100

        return {
            **self.性能统计,
            "缓存命中率": f"{命中率:.1f}%",
            "当前超时": f"{self.自适应超时:.2f}s",
            "无变化次数": self.无变化次数
        }

    def 清除缓存(self):
        """清除缓存"""
        self.缓存截图 = None
        self.缓存哈希 = None
        self.上次截图时间 = 0
        self.无变化次数 = 0
        self.自适应超时 = self.基础超时
        logger.info("🗑️ 智能缓存已清除")


# 全局智能截图缓存实例
全局智能缓存 = 智能截图缓存()


async def 截取屏幕智能(
    显示器编号: int = 1,
    最大宽度: int = 1280,
    最大高度: int = 800,
    强制刷新: bool = False,
    检测变化: bool = True
) -> Optional[Image.Image]:
    """
    智能截取屏幕，使用内容差异检测

    参数:
        显示器编号: 要截取的显示器
        最大宽度: 输出图片的最大宽度
        最大高度: 输出图片的最大高度
        强制刷新: 是否强制刷新缓存
        检测变化: 是否启用内容变化检测

    返回:
        PIL Image 对象
    """
    try:
        # 尝试从缓存获取
        缓存结果 = 全局智能缓存.获取截图(强制刷新)
        if 缓存结果[0] is not None:
            缓存截图, 来自缓存 = 缓存结果
            if 来自缓存:
                logger.debug("✨ 使用缓存截图")
                return 缓存截图

        # 执行实际截图
        开始时间 = time.time()

        with mss.mss() as sct:
            # 获取显示器信息
            if 显示器编号 >= len(sct.monitors):
                显示器编号 = 1

            监视器 = sct.monitors[显示器编号]

            # 截取屏幕
            截图数据 = sct.grab({
                "left": 监视器["left"],
                "top": 监视器["top"],
                "width": 监视器["width"],
                "height": 监视器["height"]
            })

            # 转换为 PIL Image
            截图图像 = Image.frombytes("RGB", 截图数据.size, 截图_data.bgra, "raw", "BGRX")

            # 缩放图像
            if 截图图像.width > 最大宽度 or 截图图像.height > 最大高度:
                # 计算缩放比例
                宽度比例 = 最大宽度 / 截图图像.width
                高度比例 = 最大高度 / 截图图像.height
                缩放比例 = min(宽度比例, 高度比例)

                新宽度 = int(截图图像.width * 缩放比例)
                新高度 = int(截图图像.height * 缩放比例)

                # 使用高质量缩放
                截图图像 = 截图图像.resize(
                    (新宽度, 新高度),
                    Image.Resampling.LANCZOS
                )

            # 更新缓存
            if 检测变化:
                有变化, 处理时间 = 全局智能缓存.设置截图(截图图像)
                if 有变化:
                    logger.debug("🖼️ 检测到屏幕内容变化")
                else:
                    logger.debug("📸 屏幕内容未变化")

            总时间 = time.time() - 开始时间
            logger.debug(f"⏱️ 截图耗时: {总_time:.3f}s")

            # 每100次截图输出性能统计
            if 全局智能缓存.性能统计["总截图次数"] % 100 == 0:
                统计 = 全局智能缓存.获取性能统计()
                logger.info(f"📊 截图性能统计: {统计}")

            return 截图图像

    except Exception as e:
        logger.error(f"❌ 截图失败: {e}")
        return None


def 强制刷新缓存():
    """强制刷新截图缓存"""
    全局智能缓存.清除缓存()
    logger.info("🔄 已强制刷新截图缓存")


if __name__ == "__main__":
    # 测试代码
    import asyncio

    async def 测试智能缓存():
        logger.info("🧪 开始测试智能截图缓存...")

        for i in range(10):
            截图 = await 截取屏幕智能()
            if 截图:
                logger.info(f"✅ 第 {i+1} 次截图成功")
            await asyncio.sleep(0.1)

        # 输出统计
        统计 = 全局智能缓存.获取性能统计()
        logger.info(f"📊 最终统计: {统计}")

    asyncio.run(测试智能缓存())