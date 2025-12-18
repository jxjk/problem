"""
应用配置文件
包含数据库连接、AI服务配置等设置
"""

import os
from datetime import timedelta


class Config:
    """基础配置类"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-for-equipment-problem-tracker'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///equipment_problems.db'  # 默认使用SQLite，可以根据需要更改为MySQL或PostgreSQL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 上传文件配置
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size
    
    # AI服务配置
    AI_PROVIDER = os.environ.get('AI_PROVIDER', 'mock').lower()  # 可选: openai, dashscope, mock
    
    # OpenAI配置
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    # 通义千问配置 (DashScope)
    DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', '')
    DASHSCOPE_API_BASE = os.environ.get('DASHSCOPE_API_BASE', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation')
    DASHSCOPE_MODEL = os.environ.get('DASHSCOPE_MODEL', 'qwen-max')
    
    # AI参数配置
    AI_TEMPERATURE = float(os.environ.get('AI_TEMPERATURE', '0.7'))
    AI_TOP_P = float(os.environ.get('AI_TOP_P', '0.8'))
    
    # 分页配置
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', '10'))
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///dev_equipment_problems.db'


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///equipment_problems.db'  # 生产环境应使用更可靠的数据库


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # 使用内存数据库进行测试
    WTF_CSRF_ENABLED = False


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
