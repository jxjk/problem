#!/bin/bash

# wenTiJi应用Docker部署脚本

set -e  # 遇到错误时退出

echo "开始部署wenTiJi应用..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 检查必要的文件是否存在
if [ ! -f ".env" ]; then
    echo "警告: .env文件不存在，使用默认配置"
    cp .env.example .env 2>/dev/null || echo "请创建.env文件"
fi

if [ ! -f "docker-compose.yml" ]; then
    echo "错误: docker-compose.yml文件不存在"
    exit 1
fi

if [ ! -f "Dockerfile" ]; then
    echo "错误: Dockerfile文件不存在"
    exit 1
fi

# 构建并启动服务
echo "构建并启动Docker容器..."
docker-compose up -d --build

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

echo "部署完成！"
echo "应用将在 http://localhost:5000 可访问"
echo "数据库将在端口 3306 可访问"