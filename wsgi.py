"""
WSGI应用入口文件
用于Gunicorn等WSGI服务器部署
"""

import os
from app import app
from init_db import init_database


def create_app():
    """创建应用实例并初始化数据库"""
    # 初始化数据库
    init_database()
    return app


# 创建应用实例
wsgi_app = create_app()

# 也可以直接导出app
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    wsgi_app.run(host='0.0.0.0', port=port)