# Ubuntu 22.04 云服务器部署方案 - wenTiJi 应用

## 概述
本文档详细说明了在Ubuntu 22.04云服务器上部署wenTiJi（问题集）应用的完整流程，包括系统准备、环境配置、应用部署和安全设置。

## 系统要求
- Ubuntu 22.04 LTS
- 至少2GB RAM（推荐4GB）
- 至少10GB可用磁盘空间
- 至少2个CPU核心（推荐4个）
- 开放端口：22（SSH）、80（HTTP）、443（HTTPS）、5000（应用）、3306（可选，数据库）

## 1. 服务器初始化配置

### 1.1 更新系统
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 安装基本工具
```bash
sudo apt install -y curl wget git htop vim nano net-tools
```

### 1.3 设置时区
```bash
sudo timedatectl set-timezone Asia/Shanghai
```

## 2. 安装Docker和Docker Compose

### 2.1 卸载旧版本（如果存在）
```bash
sudo apt remove docker docker-engine docker.io containerd runc
```

### 2.2 安装Docker
```bash
# 添加Docker官方GPG密钥
sudo apt update
sudo apt install ca-certificates curl gnupg lsb-release

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 设置Docker仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update

# 安装最新版Docker
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

### 2.3 将当前用户添加到Docker组
```bash
sudo usermod -aG docker $USER
```

### 2.4 启动并启用Docker服务
```bash
sudo systemctl enable docker
sudo systemctl start docker
```

### 2.5 验证Docker安装
```bash
docker --version
docker compose version
```

## 3. 配置防火墙

### 3.1 启用UFW防火墙
```bash
sudo ufw enable
```

### 3.2 设置基本规则
```bash
# 允许SSH（重要：避免锁定服务器）
sudo ufw allow ssh
sudo ufw allow 22/tcp

# 允许HTTP和HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 允许应用端口
sudo ufw allow 5000/tcp

# 查看状态
sudo ufw status
```

## 4. 部署wenTiJi应用

### 4.1 克隆项目代码
```bash
# 创建应用目录
sudo mkdir -p /opt/wenti-ji
sudo chown $USER:$USER /opt/wenti-ji
cd /opt/wenti-ji

# 克隆代码（如果使用Git）
git clone <repository-url> .
# 或者上传本地代码
```

### 4.2 配置环境变量
```bash
# 创建环境配置文件
cp .env.example .env
vim .env
```

在`.env`文件中配置：
- `DB_PASSWORD`: 强密码
- `SECRET_KEY`: 使用强密钥
- `AI_PROVIDER`: AI服务提供商
- `DASHSCOPE_API_KEY`: 通义千问API密钥（如果使用）
- `OPENAI_API_KEY`: OpenAI API密钥（如果使用）

### 4.3 创建必要的目录
```bash
mkdir -p uploads
sudo chown -R $USER:$USER uploads
```

### 4.4 启动应用
```bash
# 使用生产环境配置启动
docker compose -f docker-compose.prod.yml up -d --build
```

## 5. 配置Nginx反向代理（可选但推荐）

### 5.1 安装Nginx
```bash
sudo apt install nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 5.2 配置Nginx
```bash
sudo vim /etc/nginx/sites-available/wenti-ji
```

配置内容：
```
server {
    listen 80;
    server_name your-domain.com;  # 替换为实际域名

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 50M;
}
```

### 5.3 启用站点
```bash
sudo ln -s /etc/nginx/sites-available/wenti-ji /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 6. 配置SSL证书（可选但推荐）

### 6.1 安装Certbot
```bash
sudo apt install certbot python3-certbot-nginx
```

### 6.2 获取SSL证书
```bash
sudo certbot --nginx -d your-domain.com
```

## 7. 数据库备份策略

### 7.1 创建备份脚本
```bash
sudo vim /opt/wenti-ji/backup_db.sh
```

脚本内容：
```bash
#!/bin/bash
BACKUP_DIR="/opt/wenti-ji/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

docker exec wenti-ji-mysql mysqldump -u root -p$(docker exec -it wenti-ji-mysql printenv DB_PASSWORD) wenti_ji_db > $BACKUP_DIR/wenti_ji_db_$DATE.sql

# 保留最近7天的备份
find $BACKUP_DIR -name "wenti_ji_db_*.sql" -mtime +7 -delete
```

### 7.2 设置定时备份
```bash
chmod +x /opt/wenti-ji/backup_db.sh

# 编辑crontab
crontab -e

# 添加每日凌晨2点备份
0 2 * * * /opt/wenti-ji/backup_db.sh
```

## 8. 监控和日志管理

### 8.1 查看应用日志
```bash
docker compose -f docker-compose.prod.yml logs -f app
```

### 8.2 查看数据库日志
```bash
docker compose -f docker-compose.prod.yml logs -f mysql
```

### 8.3 系统资源监控
```bash
# 实时监控
htop
# 或
top

# 查看Docker容器资源使用
docker stats
```

## 9. 安全加固

### 9.1 限制SSH访问
编辑SSH配置：
```bash
sudo vim /etc/ssh/sshd_config
```

推荐设置：
```
Port 2222  # 更改默认SSH端口
PermitRootLogin no
PasswordAuthentication no  # 如果使用密钥认证
MaxAuthTries 3
```

### 9.2 定期更新系统
```bash
# 设置自动安全更新
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## 10. 应用管理

### 10.1 启动应用
```bash
cd /opt/wenti-ji
docker compose -f docker-compose.prod.yml up -d
```

### 10.2 停止应用
```bash
cd /opt/wenti-ji
docker compose -f docker-compose.prod.yml down
```

### 10.3 重启应用
```bash
cd /opt/wenti-ji
docker compose -f docker-compose.prod.yml restart
```

### 10.4 更新应用
```bash
cd /opt/wenti-ji
git pull  # 如果使用Git
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d --force-recreate
```

## 11. 故障排除

### 11.1 检查容器状态
```bash
docker compose -f docker-compose.prod.yml ps
```

### 11.2 检查Docker服务
```bash
sudo systemctl status docker
```

### 11.3 检查Nginx状态
```bash
sudo systemctl status nginx
```

### 11.4 检查端口占用
```bash
sudo netstat -tlnp | grep :5000
sudo netstat -tlnp | grep :3306
```

## 12. 性能优化建议

1. **数据库优化**：定期优化MySQL配置，根据服务器资源调整内存参数
2. **应用优化**：根据负载调整Gunicorn工作进程数
3. **缓存策略**：考虑添加Redis缓存层
4. **CDN**：为静态资源配置CDN加速
5. **负载均衡**：高并发场景下可配置负载均衡器

## 13. 部署验证

部署完成后，验证以下内容：

1. 应用是否正常启动
   ```bash
   curl http://localhost:5000
   ```

2. 数据库连接是否正常
   ```bash
   docker exec wenti-ji-mysql mysql -u root -p$(docker exec -it wenti-ji-mysql printenv DB_PASSWORD) -e "SHOW DATABASES;"
   ```

3. 访问Web界面，确认功能正常

4. 检查日志中无错误信息
   ```bash
   docker compose -f docker-compose.prod.yml logs
   ```