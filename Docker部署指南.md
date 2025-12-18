# wenTiJi应用Docker部署指南

## 项目概述

wenTiJi（问题集）是一个基于Flask的设备问题统计与分析系统，用于记录、跟踪和分析设备问题点，支持AI辅助分析和解决方案推荐。

## 部署准备

### 系统要求
- Docker 19.03 或更高版本
- Docker Compose 1.25 或更高版本
- 至少4GB可用内存

### 环境配置

1. 复制环境配置文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，配置以下参数：
   - `DB_PASSWORD`: MySQL数据库密码
   - `DASHSCOPE_API_KEY`: 通义千问API密钥（可选）
   - `OPENAI_API_KEY`: OpenAI API密钥（可选）
   - `SECRET_KEY`: Flask应用密钥

## 部署步骤

### 使用Docker Compose部署（推荐）

1. 构建并启动服务：
   ```bash
   docker-compose up -d --build
   ```

2. 检查服务状态：
   ```bash
   docker-compose ps
   ```

3. 查看应用日志：
   ```bash
   docker-compose logs app
   ```

### 使用部署脚本

- Linux/macOS: 运行 `./deploy.sh`
- Windows: 运行 `deploy.bat`

## 服务访问

- 应用访问地址：[http://localhost:5000](http://localhost:5000)
- MySQL数据库端口：3306
- 数据库名称：wenti_ji_db

## 服务管理

### 启动服务
```bash
docker-compose up -d
```

### 停止服务
```bash
docker-compose down
```

### 重启服务
```bash
docker-compose restart
```

### 查看日志
```bash
docker-compose logs -f app
```

### 扩展应用实例（可选）
```bash
docker-compose up -d --scale app=2
```

## 配置说明

### 数据库配置
- 默认使用MySQL数据库
- 数据持久化存储在Docker卷中
- 初始化脚本在 `init.sql` 中定义

### AI服务配置
- 支持通义千问（DashScope）和OpenAI
- 可配置为mock模式进行测试
- API密钥通过环境变量传入

### 文件上传
- 上传文件存储在 `uploads` 目录
- 该目录映射到容器的 `/app/uploads`

## 故障排除

### 服务启动失败
1. 检查Docker和Docker Compose是否正确安装
2. 确认端口5000和3306未被占用
3. 检查.env文件配置是否正确

### 数据库连接问题
1. 确认MySQL服务已正常启动
2. 检查数据库连接参数是否正确
3. 查看数据库容器日志

### 应用无法访问
1. 检查容器是否正常运行
2. 确认防火墙未阻止端口访问
3. 查看应用日志中的错误信息

## 生产环境建议

1. 使用强密码并定期更换
2. 配置外部MySQL数据库以提高可靠性
3. 设置监控和告警机制
4. 定期备份数据库和上传文件
5. 使用HTTPS反向代理（如Nginx）

## 安全注意事项

- 生产环境中请勿使用默认密码
- API密钥不应硬编码在配置文件中
- 定期更新Docker镜像以获取安全补丁
- 限制对数据库端口的访问