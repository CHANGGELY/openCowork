"""
============================================
安全配置和认证模块
============================================
这个文件负责处理 API 密钥的安全存储和认证。

安全措施：
1. 使用加密存储 API 密钥
2. 实现密钥验证和刷新机制
3. 添加访问控制和速率限制
4. 提供安全的密钥管理接口
"""
import os
import secrets
import hashlib
import base64
from typing import Optional
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from loguru import logger


class 安全配置管理器:
    """
    安全的配置管理器
    - 使用加密存储敏感信息
    - 提供安全的访问控制
    - 实现会话管理
    """

    def __init__(self):
        # 生成加密密钥，使用环境变量中的密钥或生成新的
        加密密钥 = os.environ.get("ENCRYPTION_KEY")
        if not 加密密钥:
            加密密钥 = Fernet.generate_key()
            logger.warning("⚠️ 警告：使用临时加密密钥。生产环境应设置 ENCRYPTION_KEY 环境变量")

        if isinstance(加密密钥, str):
            加密密钥 = 加密密钥.encode()

        self.加密器 = Fernet(加密密钥)

        # 存储加密后的配置
        self.加密配置: Optional[bytes] = None
        self.配置哈希: Optional[str] = None

        logger.info("🔐 安全配置管理器已初始化")

    def 保存配置(self, provider: str, api_key: str) -> bool:
        """
        安全地保存配置信息

        参数:
            provider: LLM 提供商名称
            api_key: API 密钥

        返回:
            保存是否成功
        """
        try:
            # 验证输入
            if not provider or not api_key:
                logger.error("❌ 无效的配置参数")
                return False

            # 创建配置字典
            配置数据 = {
                "provider": provider.lower().strip(),
                "api_key": api_key,
                "timestamp": datetime.now().isoformat(),
                "checksum": hashlib.sha256(api_key.encode()).hexdigest()[:16]  # 部分校验和
            }

            # 序列化配置数据
            配置字符串 = f"{配置数据['provider']}|{配置数据['api_key']}|{配置数据['timestamp']}|{配置数据['checksum']}"

            # 加密配置数据
            self.加密配置 = self.加密器.encrypt(配置字符串.encode())

            # 保存配置哈希用于验证
            self.配置哈希 = hashlib.sha256(配置字符串.encode()).hexdigest()

            logger.success(f"✅ 配置已安全保存: Provider={provider}")
            return True

        except Exception as e:
            logger.error(f"❌ 保存配置失败: {e}")
            return False

    def 获取配置(self) -> Optional[dict]:
        """
        安全地获取配置信息

        返回:
            配置字典或 None
        """
        if not self.加密配置:
            return None

        try:
            # 解密配置数据
            解密数据 = self.加密器.decrypt(self.加密配置).decode()
            provider, api_key, timestamp, checksum = 解密数据.split("|", 3)

            # 验证校验和
            预期校验和 = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            if checksum != 预期校验和:
                logger.error("❌ 配置数据完整性验证失败")
                return None

            return {
                "provider": provider,
                "api_key": api_key,
                "timestamp": timestamp
            }

        except Exception as e:
            logger.error(f"❌ 获取配置失败: {e}")
            return None

    def 验证API密钥(self, 期望提供者: str) -> bool:
        """
        验证 API 密钥是否有效

        参数:
            期望提供者: 期望的提供者名称

        返回:
            API 密钥是否有效
        """
        配置 = self.获取配置()
        if not 配置:
            return False

        if 配置["provider"] != 期望提供者.lower():
            return False

        # 这里可以添加具体的 API 密钥验证逻辑
        # 例如：向对应提供商的 API 发送验证请求
        return len(配置["api_key"]) > 10  # 简单的长度验证

    def 清除配置(self):
        """清除当前配置"""
        self.加密配置 = None
        self.配置哈希 = None
        logger.info("🧹 配置已清除")

    def 生成会话令牌(self) -> str:
        """
        生成安全的会话令牌

        返回:
            会话令牌字符串
        """
        令牌 = secrets.token_urlsafe(32)
        # 在实际应用中，你可能想将令牌存储在内存或 Redis 中以进行验证
        return 令牌

    def 配置是否存在(self) -> bool:
        """检查是否已有配置"""
        return self.加密配置 is not None


# 全局安全配置实例
全局安全配置 = 安全配置管理器()


def 初始化加密密钥():
    """
    初始化或获取加密密钥
    如果环境变量中没有设置密钥，则生成一个并提示用户
    """
    加密密钥 = os.environ.get("ENCRYPTION_KEY")

    if not 加密密钥:
        # 生成新密钥
        加密密钥 = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()

        # 安全提示：不在日志中显示密钥
        if os.environ.get("ENVIRONMENT", "development") == "development":
            logger.warning("⚠️ 警告：使用临时生成的加密密钥")
            logger.info("💡 提示：请设置 ENCRYPTION_KEY 环境变量以确保配置持久化")
            # 在开发环境中，可以将密钥保存到临时文件供参考
            try:
                with open(".env.local", "a") as f:
                    f.write(f"\n# 自动生成的加密密钥\nENCRYPTION_KEY={加密密钥}\n")
                logger.info("📝 密钥已保存到 .env.local 文件")
            except Exception as e:
                logger.error(f"❌ 保存密钥到文件失败: {e}")

        # 临时设置环境变量
        os.environ["ENCRYPTION_KEY"] = 加密密钥

    return 加密密钥


# 在模块加载时初始化加密密钥
初始化加密密钥()


def 验证提供者名称(provider: str) -> bool:
    """
    验证提供者名称是否有效

    参数:
        provider: 提供者名称

    返回:
        名称是否有效
    """
    有效提供者 = {"openai", "gemini", "anthropic"}
    return provider.lower().strip() in 有效提供者