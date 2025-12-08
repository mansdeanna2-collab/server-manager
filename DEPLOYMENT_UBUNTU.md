# Ubuntu 22.04 部署教程 / Ubuntu 22.04 Deployment Guide

本教程将指导您在 Ubuntu 22.04 系统上从零开始部署服务器管理系统。

This guide will walk you through deploying the Server Manager system on Ubuntu 22.04 from scratch.

---

## 目录 / Table of Contents

1. [系统要求 / System Requirements](#系统要求--system-requirements)
2. [准备工作 / Prerequisites](#准备工作--prerequisites)
3. [安装依赖 / Installing Dependencies](#安装依赖--installing-dependencies)
4. [部署后端 / Deploy Backend](#部署后端--deploy-backend)
5. [部署前端 / Deploy Frontend](#部署前端--deploy-frontend)
6. [配置 Nginx / Configure Nginx](#配置-nginx--configure-nginx)
7. [配置 Systemd 服务 / Configure Systemd Services](#配置-systemd-服务--configure-systemd-services)
8. [安全加固 / Security Hardening](#安全加固--security-hardening)
9. [故障排除 / Troubleshooting](#故障排除--troubleshooting)

---

## 系统要求 / System Requirements

### 最低配置 / Minimum Requirements
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 1 核心 / 1 Core
- **RAM**: 1GB
- **磁盘空间 / Disk Space**: 10GB
- **网络 / Network**: 公网 IP 或可访问的内网 IP

### 推荐配置 / Recommended
- **CPU**: 2 核心 / 2 Cores
- **RAM**: 2GB
- **磁盘空间 / Disk Space**: 20GB
- **网络 / Network**: 固定公网 IP

---

## 准备工作 / Prerequisites

### 1. 更新系统 / Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. 创建部署用户 / Create Deployment User

```bash
# 创建专用用户
sudo adduser --disabled-password --gecos "" servermgr

# 添加到 sudo 组（可选）
sudo usermod -aG sudo servermgr

# 切换到新用户
sudo su - servermgr
```

### 3. 创建项目目录 / Create Project Directory

```bash
mkdir -p ~/server-manager
cd ~/server-manager
```

---

## 安装依赖 / Installing Dependencies

### 1. 安装 Python 3.11+ / Install Python 3.11+

```bash
# 添加 Python 仓库
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# 安装 Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# 验证安装
python3.11 --version
```

### 2. 安装 Node.js 20+ / Install Node.js 20+

```bash
# 安装 Node.js 20.x LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

# 验证安装
node --version
npm --version
```

### 3. 安装 Nginx / Install Nginx

```bash
sudo apt install nginx -y

# 启动并启用 Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# 验证安装
sudo systemctl status nginx
```

### 4. 安装其他依赖 / Install Other Dependencies

```bash
# Git
sudo apt install git -y

# 构建工具
sudo apt install build-essential libssl-dev libffi-dev -y

# 系统工具
sudo apt install curl wget vim net-tools -y
```

---

## 部署后端 / Deploy Backend

### 1. 克隆代码 / Clone Repository

```bash
cd ~/server-manager

# 如果使用 Git
git clone https://github.com/mansdeanna2-collab/server-manager.git .

# 或者从本地上传文件
# 使用 scp 上传：
# scp -r /local/path/server-manager/* user@server:~/server-manager/
```

### 2. 创建 Python 虚拟环境 / Create Python Virtual Environment

```bash
cd ~/server-manager/backend

# 创建虚拟环境
python3.11 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip
```

### 3. 安装 Python 依赖 / Install Python Dependencies

```bash
# 确保在虚拟环境中
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 验证安装
pip list
```

### 4. 配置环境变量 / Configure Environment Variables

```bash
cd ~/server-manager/backend

# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

**编辑 `.env` 文件内容：**

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Database Configuration
DATABASE_URI=sqlite:////home/servermgr/server-manager/backend/server_manager.db

# Encryption Key (32 bytes) - 生成安全密钥
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Server Configuration
HOST=127.0.0.1
PORT=5000
DEBUG=False

# Rate Limiting
RATELIMIT_ENABLED=True
RATELIMIT_DEFAULT=200 per day;50 per hour
RATELIMIT_STORAGE_URL=memory://

# CORS Configuration - 替换为您的域名
CORS_ORIGINS=http://localhost,http://your-domain.com

# Timeouts
SSH_TIMEOUT=10
PING_TIMEOUT=3
PORT_TIMEOUT=5
```

**生成安全密钥的命令：**

```bash
# 生成 SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# 生成 JWT_SECRET_KEY
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"

# 生成 ENCRYPTION_KEY
python3 -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

### 5. 初始化数据库 / Initialize Database

```bash
cd ~/server-manager/backend
source venv/bin/activate

# 初始化数据库（首次运行会自动创建）
python3 -c "from app import create_app; app = create_app()"

# 验证数据库文件已创建
ls -lh server_manager.db
```

### 6. 测试后端 / Test Backend

```bash
# 在虚拟环境中
source venv/bin/activate

# 启动测试服务器
python app.py
```

**在另一个终端测试：**

```bash
# 测试 API
curl http://localhost:5000/
curl http://localhost:5000/health

# 测试登录
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

按 `Ctrl+C` 停止测试服务器。

---

## 部署前端 / Deploy Frontend

### 1. 安装前端依赖 / Install Frontend Dependencies

```bash
cd ~/server-manager/frontend

# 安装 npm 依赖
npm install

# 如果遇到权限问题
npm install --unsafe-perm
```

### 2. 配置环境变量 / Configure Environment Variables

```bash
cd ~/server-manager/frontend

# 复制环境变量模板
cp .env.example .env.production

# 编辑生产环境配置
nano .env.production
```

**编辑 `.env.production` 文件内容：**

```bash
# API Configuration - 替换为您的域名或 IP
VITE_API_BASE_URL=http://your-domain.com/api

# 或者使用 IP
# VITE_API_BASE_URL=http://123.456.789.0/api

# Environment
NODE_ENV=production
```

### 3. 构建前端 / Build Frontend

```bash
cd ~/server-manager/frontend

# 构建生产版本
npm run build

# 验证构建输出
ls -lh dist/
```

构建完成后，`dist/` 目录包含所有静态文件。

---

## 配置 Nginx / Configure Nginx

### 1. 创建 Nginx 配置文件 / Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/server-manager
```

**添加以下配置：**

```nginx
# Server Manager Nginx Configuration

# 后端 API 服务器
upstream backend {
    server 127.0.0.1:5000;
    keepalive 64;
}

# HTTP 服务器
server {
    listen 80;
    server_name your-domain.com;  # 替换为您的域名或 IP
    
    # 日志配置
    access_log /var/log/nginx/server-manager-access.log;
    error_log /var/log/nginx/server-manager-error.log;
    
    # 前端静态文件
    location / {
        root /home/servermgr/server-manager/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # 缓存静态资源
        location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # 后端 API 代理
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        
        # 代理头设置
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲设置
        proxy_buffering off;
        proxy_request_buffering off;
    }
    
    # 健康检查端点
    location /health {
        proxy_pass http://backend/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        access_log off;
    }
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # 隐藏版本信息
    server_tokens off;
    
    # 文件上传大小限制
    client_max_body_size 10M;
}
```

### 2. 启用配置 / Enable Configuration

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/server-manager /etc/nginx/sites-enabled/

# 删除默认配置（可选）
sudo rm /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重新加载 Nginx
sudo systemctl reload nginx
```

### 3. 配置防火墙 / Configure Firewall

```bash
# 如果使用 UFW
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
sudo ufw status
```

---

## 配置 Systemd 服务 / Configure Systemd Services

### 1. 创建后端服务文件 / Create Backend Service

```bash
sudo nano /etc/systemd/system/server-manager-backend.service
```

**添加以下内容：**

```ini
[Unit]
Description=Server Manager Backend API
After=network.target

[Service]
Type=simple
User=servermgr
Group=servermgr
WorkingDirectory=/home/servermgr/server-manager/backend
Environment="PATH=/home/servermgr/server-manager/backend/venv/bin"
EnvironmentFile=/home/servermgr/server-manager/backend/.env

# 启动命令 - 使用 Gunicorn（生产环境推荐）
ExecStart=/home/servermgr/server-manager/backend/venv/bin/gunicorn \
    --bind 127.0.0.1:5000 \
    --workers 4 \
    --threads 2 \
    --timeout 60 \
    --access-logfile /home/servermgr/server-manager/backend/logs/access.log \
    --error-logfile /home/servermgr/server-manager/backend/logs/error.log \
    --log-level info \
    'app:create_app()'

# 或者使用 Flask 开发服务器（仅用于测试）
# ExecStart=/home/servermgr/server-manager/backend/venv/bin/python app.py

# 重启配置
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# 安全设置
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 2. 安装 Gunicorn（推荐用于生产环境）/ Install Gunicorn

```bash
cd ~/server-manager/backend
source venv/bin/activate

# 安装 Gunicorn
pip install gunicorn

# 创建日志目录
mkdir -p ~/server-manager/backend/logs
```

### 3. 启动并启用服务 / Start and Enable Service

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start server-manager-backend

# 启用开机自启
sudo systemctl enable server-manager-backend

# 查看服务状态
sudo systemctl status server-manager-backend

# 查看日志
sudo journalctl -u server-manager-backend -f
```

### 4. 服务管理命令 / Service Management Commands

```bash
# 重启服务
sudo systemctl restart server-manager-backend

# 停止服务
sudo systemctl stop server-manager-backend

# 查看日志（最近 100 行）
sudo journalctl -u server-manager-backend -n 100

# 查看实时日志
sudo journalctl -u server-manager-backend -f

# 检查服务配置
sudo systemctl cat server-manager-backend
```

---

## 安全加固 / Security Hardening

### 1. 配置 SSL/TLS（使用 Let's Encrypt）/ Configure SSL/TLS

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取 SSL 证书（替换 your-domain.com）
sudo certbot --nginx -d your-domain.com

# 测试自动续期
sudo certbot renew --dry-run
```

### 2. 修改默认管理员密码 / Change Default Admin Password

登录系统后，立即修改默认密码：

```bash
# 可以通过 API 或创建管理脚本
cd ~/server-manager/backend
source venv/bin/activate

# 创建密码修改脚本
cat > change_admin_password.py << 'EOF'
from app import create_app
from models import db
from models.user import User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        new_password = input("Enter new password: ")
        admin.set_password(new_password)
        db.session.commit()
        print("Password changed successfully!")
    else:
        print("Admin user not found!")
EOF

# 运行脚本
python change_admin_password.py
```

### 3. 配置防火墙规则 / Configure Firewall Rules

```bash
# 只允许必要的端口
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### 4. 限制文件权限 / Restrict File Permissions

```bash
# 设置正确的文件权限
chmod 600 ~/server-manager/backend/.env
chmod 644 ~/server-manager/backend/server_manager.db
chmod 755 ~/server-manager/backend
chmod 755 ~/server-manager/frontend/dist
```

### 5. 配置日志轮转 / Configure Log Rotation

```bash
sudo nano /etc/logrotate.d/server-manager
```

**添加以下内容：**

```
/home/servermgr/server-manager/backend/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 644 servermgr servermgr
    postrotate
        systemctl reload server-manager-backend > /dev/null 2>&1 || true
    endscript
}

/var/log/nginx/server-manager-*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

### 6. 设置自动备份 / Setup Automatic Backups

```bash
# 创建备份脚本
cat > ~/backup-server-manager.sh << 'EOF'
#!/bin/bash

# 配置
BACKUP_DIR="/home/servermgr/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="/home/servermgr/server-manager/backend/server_manager.db"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cp $DB_FILE $BACKUP_DIR/server_manager_$DATE.db

# 删除 30 天前的备份
find $BACKUP_DIR -name "server_manager_*.db" -mtime +30 -delete

echo "Backup completed: server_manager_$DATE.db"
EOF

# 添加执行权限
chmod +x ~/backup-server-manager.sh

# 添加到 crontab（每天凌晨 2 点执行）
(crontab -l 2>/dev/null; echo "0 2 * * * /home/servermgr/backup-server-manager.sh >> /home/servermgr/backup.log 2>&1") | crontab -
```

---

## 验证部署 / Verify Deployment

### 1. 检查所有服务 / Check All Services

```bash
# 检查后端服务
sudo systemctl status server-manager-backend

# 检查 Nginx
sudo systemctl status nginx

# 检查端口监听
sudo netstat -tulpn | grep -E ':(80|443|5000)'

# 或使用 ss
sudo ss -tulpn | grep -E ':(80|443|5000)'
```

### 2. 测试 API / Test API

```bash
# 测试根路径
curl http://localhost/

# 测试 API
curl http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 测试健康检查
curl http://localhost/health
```

### 3. 浏览器访问 / Browser Access

打开浏览器访问：
- **HTTP**: `http://your-server-ip/`
- **HTTPS**: `https://your-domain.com/`

使用默认凭据登录：
- **用户名**: admin
- **密码**: admin123

---

## 监控和维护 / Monitoring and Maintenance

### 1. 查看系统资源使用 / Check System Resources

```bash
# CPU 和内存使用
top
htop

# 磁盘使用
df -h

# 查看进程
ps aux | grep -E '(gunicorn|nginx)'
```

### 2. 查看日志 / View Logs

```bash
# 后端日志
sudo journalctl -u server-manager-backend -f

# Nginx 访问日志
sudo tail -f /var/log/nginx/server-manager-access.log

# Nginx 错误日志
sudo tail -f /var/log/nginx/server-manager-error.log

# 应用日志
tail -f ~/server-manager/backend/logs/error.log
```

### 3. 性能优化建议 / Performance Optimization

```bash
# 调整 Gunicorn workers（根据 CPU 核心数）
# workers = (2 x CPU cores) + 1
# 编辑 /etc/systemd/system/server-manager-backend.service
# 修改 --workers 参数

# 启用 Nginx 缓存
# 在 Nginx 配置中添加：
# proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g;
```

---

## 故障排除 / Troubleshooting

### 问题 1: 后端服务无法启动 / Backend Service Won't Start

```bash
# 查看详细错误日志
sudo journalctl -u server-manager-backend -n 50 --no-pager

# 检查 Python 环境
cd ~/server-manager/backend
source venv/bin/activate
python app.py

# 检查端口占用
sudo lsof -i :5000
```

### 问题 2: Nginx 502 Bad Gateway

```bash
# 检查后端服务是否运行
sudo systemctl status server-manager-backend

# 检查端口连接
curl http://127.0.0.1:5000/

# 检查 Nginx 错误日志
sudo tail -f /var/log/nginx/server-manager-error.log

# 检查 SELinux（如果启用）
sudo getenforce
# 如果是 Enforcing，可能需要配置 SELinux 规则
```

### 问题 3: 数据库权限错误 / Database Permission Error

```bash
# 检查数据库文件权限
ls -l ~/server-manager/backend/server_manager.db

# 修复权限
chown servermgr:servermgr ~/server-manager/backend/server_manager.db
chmod 644 ~/server-manager/backend/server_manager.db

# 检查目录权限
chmod 755 ~/server-manager/backend
```

### 问题 4: 前端无法连接后端 / Frontend Can't Connect to Backend

```bash
# 检查 CORS 配置
grep CORS_ORIGINS ~/server-manager/backend/.env

# 检查前端 API 配置
cat ~/server-manager/frontend/dist/assets/*.js | grep -i api

# 检查网络连接
curl -v http://your-domain.com/api/auth/me
```

### 问题 5: SSL 证书问题 / SSL Certificate Issues

```bash
# 检查证书状态
sudo certbot certificates

# 手动续期
sudo certbot renew

# 测试 Nginx 配置
sudo nginx -t

# 查看 Certbot 日志
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

---

## 升级和更新 / Upgrade and Update

### 升级应用 / Upgrade Application

```bash
# 1. 备份数据库
cp ~/server-manager/backend/server_manager.db ~/server_manager_backup_$(date +%Y%m%d).db

# 2. 停止服务
sudo systemctl stop server-manager-backend

# 3. 更新代码
cd ~/server-manager
git pull origin main

# 4. 更新后端依赖
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 5. 运行数据库迁移（如果有）
# flask db upgrade

# 6. 重新构建前端
cd ../frontend
npm install
npm run build

# 7. 启动服务
sudo systemctl start server-manager-backend

# 8. 验证
curl http://localhost/health
```

---

## 卸载 / Uninstall

如需完全卸载系统：

```bash
# 1. 停止并禁用服务
sudo systemctl stop server-manager-backend
sudo systemctl disable server-manager-backend

# 2. 删除服务文件
sudo rm /etc/systemd/system/server-manager-backend.service
sudo systemctl daemon-reload

# 3. 删除 Nginx 配置
sudo rm /etc/nginx/sites-enabled/server-manager
sudo rm /etc/nginx/sites-available/server-manager
sudo systemctl reload nginx

# 4. 删除应用文件
rm -rf ~/server-manager
rm -rf ~/backups

# 5. 删除用户（可选）
# sudo deluser --remove-home servermgr
```

---

## 附录 / Appendix

### A. 有用的命令 / Useful Commands

```bash
# 查看系统信息
lsb_release -a
uname -a

# 查看 Python 版本
python3.11 --version

# 查看 Node.js 版本
node --version
npm --version

# 查看 Nginx 版本
nginx -v

# 查看服务状态
sudo systemctl list-units --type=service --state=running

# 查看开放端口
sudo netstat -tulpn
sudo ss -tulpn

# 查看磁盘 I/O
iostat -x 1
```

### B. 性能测试 / Performance Testing

```bash
# 安装 Apache Bench
sudo apt install apache2-utils -y

# 测试 API 性能
ab -n 1000 -c 10 http://localhost/health

# 使用 wrk 进行更高级的测试
# sudo apt install wrk -y
# wrk -t4 -c100 -d30s http://localhost/
```

### C. 监控工具 / Monitoring Tools

```bash
# 安装 htop（系统监控）
sudo apt install htop -y

# 安装 nethogs（网络监控）
sudo apt install nethogs -y
sudo nethogs

# 安装 iotop（磁盘 I/O 监控）
sudo apt install iotop -y
sudo iotop
```

---

## 联系支持 / Contact Support

如果遇到问题，请：
1. 查看故障排除部分
2. 检查 GitHub Issues
3. 查看项目文档

---

## 更新日志 / Changelog

- **2025-12-08**: 初始版本，支持 Ubuntu 22.04
- 基于 Server Manager v2.0.0

---

**祝您部署顺利！/ Happy Deploying!** 🚀
