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
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    
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
    
    # 向量数据库配置
    VECTOR_DB_PERSIST_DIR = os.environ.get('VECTOR_DB_PERSIST_DIR', './chroma_data')
    EMBEDDING_MODEL_NAME = os.environ.get('EMBEDDING_MODEL_NAME', 'all-MiniLM-L6-v2')
    VECTOR_DB_SEARCH_LIMIT = int(os.environ.get('VECTOR_DB_SEARCH_LIMIT', '5'))
    
    # 向量数据库配置
    VECTOR_DB_PATH = os.environ.get('VECTOR_DB_PATH', './chroma_data')
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    
    # CSV导入配置
    CSV_MAX_ROWS = int(os.environ.get('CSV_MAX_ROWS', '10000'))  # CSV最大行数
    CSV_TITLE_MAX_LENGTH = int(os.environ.get('CSV_TITLE_MAX_LENGTH', '500'))  # 标题最大长度
    CSV_DESCRIPTION_MAX_LENGTH = int(os.environ.get('CSV_DESCRIPTION_MAX_LENGTH', '2000'))  # 描述最大长度
    CSV_EQUIPMENT_TYPE_MAX_LENGTH = int(os.environ.get('CSV_EQUIPMENT_TYPE_MAX_LENGTH', '100'))  # 设备类型最大长度
    CSV_BATCH_SIZE = int(os.environ.get('CSV_BATCH_SIZE', '100'))  # CSV批量处理大小
    CSV_FILE_SIZE_LIMIT = int(os.environ.get('CSV_FILE_SIZE_LIMIT', '104857600'))  # CSV文件大小限制（100MB）
    CSV_ALLOWED_EXTENSIONS = set(os.environ.get('CSV_ALLOWED_EXTENSIONS', 'csv').lower().split(','))  # 允许的文件扩展名
    CSV_SPECIAL_CHAR_THRESHOLD = float(os.environ.get('CSV_SPECIAL_CHAR_THRESHOLD', '0.5'))  # 特殊字符比例阈值


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
