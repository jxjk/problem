# Ubuntu 22.04 云服务器迁移方案 - wenTiJi 应用

## 概述
本文档详细说明了从现有环境迁移到Ubuntu 22.04云服务器的完整流程，确保数据完整性、服务连续性和最小化停机时间。

## 迁移前准备

### 1.1 环境评估
- 记录当前系统配置（硬件、软件、网络设置）
- 记录当前应用版本和配置
- 记录当前数据库结构和数据量
- 记录当前用户和权限设置
- 记录当前服务依赖关系

### 1.2 迁移计划
- 选择迁移时间窗口（建议业务低峰期）
- 准备回滚方案
- 通知相关用户迁移计划
- 备份所有数据

### 1.3 目标服务器准备
- 确保Ubuntu 22.04云服务器已按部署方案配置完成
- 确保网络连接正常
- 确保安全组/防火墙规则已正确设置

## 2. 数据备份

### 2.1 数据库备份
```bash
# 在当前服务器上
docker exec wenti-ji-mysql mysqldump -u root -p$(docker exec -it wenti-ji-mysql printenv DB_PASSWORD) wenti_ji_db > wenti_ji_backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2.2 上传文件备份
```bash
# 打包上传文件目录
tar -czf uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz uploads/
```

### 2.3 配置文件备份
```bash
# 备份环境配置文件
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
```

### 2.4 代码备份
```bash
# 如果使用Git，确保代码已推送到远程仓库
git add .
git commit -m "Pre-migration backup $(date +%Y%m%d_%H%M%S)"
git push origin main
```

## 3. 数据传输

### 3.1 传输数据库备份
```bash
# 将数据库备份文件传输到目标服务器
scp wenti_ji_backup_*.sql user@target-server-ip:/opt/wenti-ji/
```

### 3.2 传输上传文件
```bash
# 传输上传文件
scp uploads_backup_*.tar.gz user@target-server-ip:/opt/wenti-ji/
```

### 3.3 传输配置文件
```bash
# 传输配置文件（注意保护敏感信息）
scp .env user@target-server-ip:/opt/wenti-ji/
```

## 4. 目标服务器部署

### 4.1 登录目标服务器
```bash
ssh user@target-server-ip
```

### 4.2 克隆或上传代码
```bash
# 方法1：使用Git克隆
cd /opt/wenti-ji
git clone <repository-url> .

# 方法2：上传代码包
# scp 本地代码包到目标服务器
# tar -xzf 代码包.tar.gz -C /opt/wenti-ji/
```

### 4.3 解压上传文件
```bash
cd /opt/wenti-ji
tar -xzf uploads_backup_*.tar.gz
```

### 4.4 恢复配置文件
```bash
# 将备份的配置文件复制到适当位置
cp .env /opt/wenti-ji/.env
```

## 5. 数据库迁移

### 5.1 启动目标服务器上的MySQL容器
```bash
cd /opt/wenti-ji
docker compose -f docker-compose.prod.yml up -d mysql
```

### 5.2 等待数据库准备就绪
```bash
# 等待MySQL容器完全启动
docker compose -f docker-compose.prod.yml exec mysql mysqladmin ping -h localhost -u root -p$(grep DB_PASSWORD .env | cut -d'=' -f2)
```

### 5.3 恢复数据库
```bash
# 导入数据库备份
docker compose -f docker-compose.prod.yml exec -T mysql mysql -u root -p$(grep DB_PASSWORD .env | cut -d'=' -f2) wenti_ji_db < wenti_ji_backup_*.sql
```

### 5.4 验证数据恢复
```bash
# 检查数据表数量和内容
docker compose -f docker-compose.prod.yml exec mysql mysql -u root -p$(grep DB_PASSWORD .env | cut -d'=' -f2) -e "USE wenti_ji_db; SHOW TABLES;"
```

## 6. 应用启动和验证

### 6.1 启动应用服务
```bash
cd /opt/wenti-ji
docker compose -f docker-compose.prod.yml up -d --build
```

### 6.2 等待服务启动
```bash
# 等待应用完全启动
sleep 30
```

### 6.3 检查服务状态
```bash
docker compose -f docker-compose.prod.yml ps
```

### 6.4 验证应用功能
```bash
# 检查应用响应
curl -I http://localhost:5000
```

### 6.5 检查应用日志
```bash
docker compose -f docker-compose.prod.yml logs app
```

## 7. 域名和网络配置

### 7.1 更新DNS记录
- 将域名A记录指向新的云服务器IP地址
- 等待DNS传播（通常需要几分钟到几小时）

### 7.2 配置反向代理（如果使用Nginx）
```bash
sudo vim /etc/nginx/sites-available/wenti-ji
# 确保配置指向正确的后端服务
```

### 7.3 测试网络连接
```bash
# 从外部测试访问
curl -I http://your-domain.com
```

## 8. 功能验证

### 8.1 基础功能测试
- 访问登录页面
- 尝试登录
- 检查数据是否正确显示
- 测试添加新问题点
- 测试导入CSV功能
- 测试AI分析功能

### 8.2 数据完整性验证
- 检查问题点数量是否与原系统一致
- 随机检查几个问题点的数据完整性
- 验证上传文件是否可以正常访问

### 8.3 性能测试
- 测试页面加载速度
- 测试大量数据查询性能
- 监控系统资源使用情况

## 9. 监控和日志

### 9.1 设置监控
```bash
# 检查系统资源
htop
docker stats

# 检查应用日志
docker compose -f docker-compose.prod.yml logs -f app
```

### 9.2 设置日志轮转
```bash
sudo vim /etc/logrotate.d/wenti-ji
```

配置内容：
```
/opt/wenti-ji/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        # 如果使用日志轮转，重启服务
    endscript
}
```

## 10. 回滚计划

### 10.1 迁移失败时的回滚步骤
1. 立即停止目标服务器上的应用
   ```bash
   docker compose -f docker-compose.prod.yml down
   ```

2. 恢复原服务器的服务
   ```bash
   # 在原服务器上重新启动服务
   docker compose up -d
   ```

3. 恢复DNS设置（如果已更改）
   - 将域名A记录指回原服务器IP

4. 通知用户服务已恢复

### 10.2 数据回滚
- 如果数据库已修改，使用备份恢复数据
- 如果文件已上传，使用备份恢复文件

## 11. 迁移后清理

### 11.1 监控期
- 迁移后至少24小时密切监控系统
- 检查错误日志
- 监控系统性能

### 11.2 原服务器处理
- 在确认新服务器运行稳定后，保留原服务器一段时间作为备份
- 清理不再需要的备份文件
- 确保所有数据都已安全迁移

## 12. 迁移检查清单

- [ ] 系统环境配置完成
- [ ] Docker和相关组件安装验证
- [ ] 代码成功部署
- [ ] 数据库成功迁移
- [ ] 上传文件成功迁移
- [ ] 应用服务成功启动
- [ ] 数据完整性验证
- [ ] 功能测试完成
- [ ] 性能测试通过
- [ ] DNS/网络配置完成
- [ ] 备份策略配置
- [ ] 监控系统配置
- [ ] 文档更新完成
- [ ] 用户通知完成

## 13. 迁移时间表

| 阶段 | 预计时间 | 说明 |
|------|----------|------|
| 准备工作 | 30分钟 | 环境评估和备份 |
| 数据传输 | 1-2小时 | 根据数据量大小 |
| 数据库恢复 | 30-60分钟 | 根据数据量大小 |
| 应用部署 | 30分钟 | 构建和启动 |
| 功能验证 | 1小时 | 全面测试 |
| DNS切换 | 1-24小时 | DNS传播时间 |
| 总计 | 3-28小时 | 不包括DNS传播时间 |

## 14. 风险和缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 数据丢失 | 高 | 多重备份策略 |
| 服务中断 | 高 | 详细的回滚计划 |
| 数据不一致 | 中 | 迁移后验证 |
| DNS传播延迟 | 低 | 提前准备 |
| 性能下降 | 中 | 迁移后性能测试 |
| 配置错误 | 中 | 预部署测试 |