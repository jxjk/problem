"""
设备问题统计系统启动脚本
"""

import os
import sys
from app import app
from init_db import init_database
from vector_db import init_vector_db


def main():
    """主函数"""
    print("正在启动设备问题统计系统...")
    
    # 初始化数据库
    print("正在初始化数据库...")
    init_database()
    
    # 初始化向量数据库
    print("正在初始化向量数据库...")
    init_vector_db()
    
    # 获取端口配置，默认为5000
    port = int(os.environ.get('PORT', 5000))
    
    # 获取主机配置，默认为0.0.0.0（允许外部访问）
    host = os.environ.get('HOST', '0.0.0.0')
    
    # 获取调试模式，默认为False
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"应用将在 {host}:{port} 上启动")
    print(f"调试模式: {debug}")
    
    # 启动应用
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()