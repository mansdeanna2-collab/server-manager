# Ubuntu 22.04 部署快速参考 / Quick Reference

## 一键部署 / One-Click Deployment

```bash
git clone https://github.com/mansdeanna2-collab/server-manager.git
cd server-manager
sudo bash deploy-ubuntu.sh
```

---

## 系统要求 / Requirements

- Ubuntu 22.04 LTS
- 1GB RAM (推荐 2GB / Recommended 2GB)
- 10GB 磁盘空间 / Disk Space
- Root 权限 / Root access

---

## 手动安装步骤 / Manual Installation Steps

### 1. 安装依赖 / Install Dependencies

```bash
# Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

# Nginx
sudo apt install nginx -y
```

### 2. 创建用户 / Create User

```bash
sudo adduser --disabled-password --gecos "" servermgr
sudo su - servermgr
mkdir -p ~/server-manager
cd ~/server-manager
```

### 3. 部署后端 / Deploy Backend

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# 配置环境变量
cp .env.example .env
nano .env  # 编辑配置 / Edit config

# 生成安全密钥 / Generate secure keys
python3 -c "import secrets; print(secrets.token_hex(32))"
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4. 部署前端 / Deploy Frontend

```bash
cd ../frontend
npm install
cp .env.example .env.production
nano .env.production  # 设置 API URL / Set API URL
npm run build
```

### 5. 配置 Systemd / Configure Systemd

```bash
sudo nano /etc/systemd/system/server-manager-backend.service
```

```ini
[Unit]
Description=Server Manager Backend
After=network.target

[Service]
Type=simple
User=servermgr
WorkingDirectory=/home/servermgr/server-manager/backend
Environment="PATH=/home/servermgr/server-manager/backend/venv/bin"
EnvironmentFile=/home/servermgr/server-manager/backend/.env
ExecStart=/home/servermgr/server-manager/backend/venv/bin/gunicorn \
    --bind 127.0.0.1:5000 \
    --workers 4 \
    'app:create_app()'
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start server-manager-backend
sudo systemctl enable server-manager-backend
```

### 6. 配置 Nginx / Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/server-manager
```

```nginx
upstream backend {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /home/servermgr/server-manager/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/server-manager /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. 配置防火墙 / Configure Firewall

```bash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

---

## 常用命令 / Common Commands

### 服务管理 / Service Management

```bash
# 状态检查 / Check status
sudo systemctl status server-manager-backend
sudo systemctl status nginx

# 重启服务 / Restart services
sudo systemctl restart server-manager-backend
sudo systemctl reload nginx

# 查看日志 / View logs
sudo journalctl -u server-manager-backend -f
sudo tail -f /var/log/nginx/server-manager-error.log
```

### 数据库备份 / Database Backup

```bash
# 手动备份 / Manual backup
cp ~/server-manager/backend/server_manager.db ~/backup_$(date +%Y%m%d).db

# 自动备份脚本 / Auto backup script
cat > ~/backup.sh << 'EOF'
#!/bin/bash
cp ~/server-manager/backend/server_manager.db ~/backups/backup_$(date +%Y%m%d).db
find ~/backups -name "backup_*.db" -mtime +30 -delete
EOF
chmod +x ~/backup.sh

# 添加到 crontab (每天 2:00)
crontab -e
# 添加: 0 2 * * * /home/servermgr/backup.sh
```

### 修改管理员密码 / Change Admin Password

```bash
cd ~/server-manager/backend
source venv/bin/activate
python3 << EOF
from app import create_app
from models import db
from models.user import User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    admin.set_password('new_password')
    db.session.commit()
    print("Password changed!")
EOF
```

### SSL 证书 / SSL Certificate

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书 / Get certificate
sudo certbot --nginx -d your-domain.com

# 测试自动续期 / Test auto-renewal
sudo certbot renew --dry-run
```

---

## 故障排除 / Troubleshooting

### 后端无法启动 / Backend Won't Start

```bash
# 查看详细日志 / Check logs
sudo journalctl -u server-manager-backend -n 100

# 手动测试 / Manual test
cd ~/server-manager/backend
source venv/bin/activate
python app.py
```

### Nginx 502 错误 / Nginx 502 Error

```bash
# 检查后端 / Check backend
curl http://127.0.0.1:5000/

# 检查日志 / Check logs
sudo tail -f /var/log/nginx/server-manager-error.log
```

### 端口被占用 / Port in Use

```bash
# 查看端口使用 / Check port
sudo lsof -i :5000
sudo lsof -i :80

# 停止进程 / Kill process
sudo kill -9 <PID>
```

---

## 性能优化 / Performance Tuning

```bash
# Gunicorn Workers
# 计算: workers = (2 x CPU cores) + 1
# Calculate: workers = (2 x CPU cores) + 1

# 查看 CPU 核心数 / Check CPU cores
nproc

# 编辑服务文件 / Edit service file
sudo nano /etc/systemd/system/server-manager-backend.service
# 修改 --workers 参数 / Change --workers parameter
```

---

## 监控 / Monitoring

```bash
# 系统资源 / System resources
htop
free -h
df -h

# 网络连接 / Network connections
sudo netstat -tulpn | grep -E ':(80|443|5000)'

# 进程状态 / Process status
ps aux | grep -E '(gunicorn|nginx)'
```

---

## 访问地址 / Access URLs

- **Web 界面 / Web UI**: `http://your-server-ip/`
- **API 文档 / API Docs**: `http://your-server-ip/api/`
- **健康检查 / Health Check**: `http://your-server-ip/health`

**默认凭据 / Default Credentials**:
- 用户名 / Username: `admin`
- 密码 / Password: `admin123`

⚠️ **首次登录后立即修改密码！/ Change password after first login!**

---

## 更多信息 / More Information

- 📖 **完整文档 / Full Documentation**: [DEPLOYMENT_UBUNTU.md](DEPLOYMENT_UBUNTU.md)
- 🚀 **自动脚本 / Auto Script**: [deploy-ubuntu.sh](deploy-ubuntu.sh)
- 🐛 **问题反馈 / Issue Tracking**: GitHub Issues
- 📝 **项目主页 / Project Home**: [README.md](README.md)

---

**版本 / Version**: 2.0.0  
**更新日期 / Last Updated**: 2025-12-08
