"""
测试安全配置模块
"""
import os
import pytest
from security import 安全配置管理器, 验证提供者名称


def test_provider_validation():
    """测试提供者名称验证"""
    assert 验证提供者名称("openai") is True
    assert 验证提供者名称("OpenAI") is True  # 测试大小写不敏感
    assert 验证提供者名称("gemini") is True
    assert 验证提供者名称("anthropic") is True
    assert 验证提供者名称("invalid_provider") is False
    assert 验证提供者名称("") is False


def test_security_manager_initialization():
    """测试安全配置管理器初始化"""
    manager = 安全配置管理器()
    assert manager is not None


def test_save_and_retrieve_config():
    """测试保存和获取配置"""
    manager = 安全配置管理器()

    # 测试保存配置
    result = manager.保存配置("openai", "test-api-key-123")
    assert result is True

    # 测试获取配置
    config = manager.获取配置()
    assert config is not None
    assert config["provider"] == "openai"
    assert config["api_key"] == "test-api-key-123"
    assert "timestamp" in config


def test_config_encryption():
    """测试配置加密存储"""
    manager = 安全配置管理器()

    # 保存配置
    manager.保存配置("gemini", "my-secret-key")

    # 确保配置被加密存储（不是明文）
    assert manager.加密配置 is not None

    # 获取解密后的配置
    config = manager.获取配置()
    assert config["api_key"] == "my-secret-key"


def test_invalid_config():
    """测试无效配置"""
    manager = 安全配置管理器()

    # 测试空参数
    result = manager.保存配置("", "")
    assert result is False

    result = manager.保存配置("openai", "")
    assert result is False

    result = manager.保存配置("", "some-key")
    assert result is False


def test_config_verification():
    """测试配置验证功能"""
    manager = 安全配置管理器()

    # 保存一个有效配置
    manager.保存配置("openai", "valid-api-key")

    # 验证提供者
    assert manager.验证API密钥("openai") is True
    assert manager.验证API密钥("gemini") is False  # 不同的提供者


def test_config_clearing():
    """测试配置清除"""
    manager = 安全配置管理器()

    # 保存配置
    manager.保存配置("anthropic", "test-key")
    assert manager.配置是否存在() is True

    # 清除配置
    manager.清除配置()
    assert manager.配置是否存在() is False

    # 获取配置应该返回 None
    config = manager.获取配置()
    assert config is None


def test_session_token_generation():
    """测试会话令牌生成"""
    manager = 安全配置管理器()

    token = manager.生成会话令牌()
    assert isinstance(token, str)
    assert len(token) > 0

    # 生成的令牌应该是唯一的
    token2 = manager.生成会话令牌()
    assert token != token2