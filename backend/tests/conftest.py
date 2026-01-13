"""
测试配置和工具模块
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 用于测试的模拟 API 密钥
MOCK_API_KEY = "test-key-for-testing"

# 用于测试的模拟图片数据（小尺寸透明PNG）
MOCK_IMAGE_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="