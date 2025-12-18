# wenTiJi - 设备问题统计系统

## 项目简介

wenTiJi（问题集）是一个基于Flask的设备问题统计与分析系统，用于记录、跟踪和分析设备问题点，支持AI辅助分析和解决方案推荐。

## 功能特性

- 问题点记录与管理
- 设备类型分类
- 问题分类与解决方案分类
- AI辅助分析与建议
- CSV批量导入功能
- 仪表盘统计分析
- 阶段化问题跟踪（设计、开发、使用、维护）

## 技术栈

- Python 3.9
- Flask 2.3.3
- SQLAlchemy
- MySQL/PuMySQL
- Gunicorn
- Docker & Docker Compose

## 快速部署

### 环境要求

- Docker
- Docker Compose

### 部署步骤

1. 克隆或复制项目文件到本地目录
2. 配置环境变量：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，设置相关配置
   ```
3. 构建并启动服务：
   ```bash
   docker-compose up -d --build
   ```
4. 访问应用：[http://localhost:5000](http://localhost:5000)

## Docker部署文件说明

- `Dockerfile` - 应用容器构建配置
- `docker-compose.yml` - 多容器编排配置
- `.dockerignore` - Docker构建时忽略的文件
- `.env` - 环境变量配置
- `init.sql` - 数据库初始化脚本
- `deploy.sh` - Linux/macOS部署脚本
- `deploy.bat` - Windows部署脚本
- `Docker部署指南.md` - 详细部署文档

## 服务配置

- 应用服务端口：5000
- 数据库端口：3306
- 数据库名称：wenti_ji_db
- 用户名：root
- 密码：在.env文件中配置

## 环境变量

- `DB_PASSWORD` - 数据库密码
- `AI_PROVIDER` - AI服务提供商 (mock/openai/dashscope)
- `DASHSCOPE_API_KEY` - 通义千问API密钥
- `OPENAI_API_KEY` - OpenAI API密钥
- `SECRET_KEY` - Flask密钥

## 开发说明

### 本地开发环境

1. 安装Python依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 初始化数据库：
   ```bash
   python init_db.py
   ```
3. 启动应用：
   ```bash
   python run.py
   ```

### 数据库模型

- `Problem` - 问题点主表
- `EquipmentType` - 设备类型表
- `ProblemCategory` - 问题分类表
- `SolutionCategory` - 解决方案分类表
- `User` - 用户表
- `AIAnalysisHistory` - AI分析历史表
- `ImportHistory` - 导入历史表
- `SystemConfig` - 系统配置表

## API接口

- `GET /api/problems` - 获取问题列表
- `POST /api/problems` - 创建新问题
- `GET /api/problems/{id}` - 获取问题详情
- `POST /api/import-csv` - 导入CSV文件
- `GET /api/dashboard-stats` - 获取仪表盘统计
- `POST /api/ai-query` - AI智能查询