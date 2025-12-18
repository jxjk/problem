@echo off
REM wenTiJi应用Docker部署脚本 (Windows)

echo 开始部署wenTiJi应用...

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Docker未安装，请先安装Docker
    pause
    exit /b 1
)

REM 检查Docker Compose是否安装
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Docker Compose未安装，请先安装Docker Compose
    pause
    exit /b 1
)

REM 检查必要的文件是否存在
if not exist ".env" (
    echo 警告: .env文件不存在，使用默认配置
    if exist ".env.example" (
        copy .env.example .env
    ) else (
        echo 请创建.env文件
    )
)

if not exist "docker-compose.yml" (
    echo 错误: docker-compose.yml文件不存在
    pause
    exit /b 1
)

if not exist "Dockerfile" (
    echo 错误: Dockerfile文件不存在
    pause
    exit /b 1
)

REM 构建并启动服务
echo 构建并启动Docker容器...
docker-compose up -d --build

REM 等待服务启动
echo 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo 检查服务状态...
docker-compose ps

echo 部署完成！
echo 应用将在 http://localhost:5000 可访问
echo 数据库将在端口 3306 可访问

pause