# Server Manager - 部署选项 / Deployment Options

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Server Manager v2.0.0                            │
│              Ubuntu 22.04 部署方案 / Deployment Solutions             │
└─────────────────────────────────────────────────────────────────────┘
```

## 📚 文档结构 / Documentation Structure

```
server-manager/
├── 📖 README.md                    # 项目主文档 / Main documentation
├── 📋 QUICK_REFERENCE.md           # 快速参考 / Quick reference  
├── 📖 DEPLOYMENT_UBUNTU.md         # 完整部署指南 / Full deployment guide
└── 🚀 deploy-ubuntu.sh             # 自动部署脚本 / Auto deployment script
```

---

## 🎯 选择您的部署方式 / Choose Your Deployment Method

### 方案 1: 自动部署 (推荐) / Option 1: Automated (Recommended)

**适合人群 / Best for**: 快速部署、生产环境 / Quick deployment, production

```bash
# 一键安装 / One-command installation
git clone https://github.com/mansdeanna2-collab/server-manager.git
cd server-manager
sudo bash deploy-ubuntu.sh
```

**特点 / Features**:
- ✅ 全自动安装 / Fully automated
- ✅ 安全密钥自动生成 / Auto key generation
- ✅ 服务自动配置 / Auto service setup
- ✅ 防火墙自动配置 / Auto firewall config
- ⏱️ 约 10-15 分钟 / ~10-15 minutes

**查看脚本 / View script**: [deploy-ubuntu.sh](deploy-ubuntu.sh)

---

### 方案 2: 完整手动部署 / Option 2: Complete Manual Deployment

**适合人群 / Best for**: 学习过程、自定义配置 / Learning process, custom config

**步骤 / Steps**:

1. **系统准备 / System Preparation**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **安装依赖 / Install Dependencies**
   - Python 3.11
   - Node.js 20
   - Nginx
   - 其他工具 / Other tools

3. **部署后端 / Deploy Backend**
   - 创建虚拟环境 / Create venv
   - 安装依赖 / Install dependencies
   - 配置环境变量 / Configure env vars
   - 设置 Systemd / Setup systemd

4. **部署前端 / Deploy Frontend**
   - 安装 npm 包 / Install npm packages
   - 构建生产版本 / Build production
   - 配置 Nginx / Configure Nginx

5. **安全加固 / Security Hardening**
   - SSL 证书 / SSL certificate
   - 防火墙 / Firewall
   - 日志轮转 / Log rotation
   - 自动备份 / Auto backup

**完整指南 / Full guide**: [DEPLOYMENT_UBUNTU.md](DEPLOYMENT_UBUNTU.md) (992 行 / lines)

---

### 方案 3: 快速命令参考 / Option 3: Quick Command Reference

**适合人群 / Best for**: 有经验的管理员、快速查询 / Experienced admins, quick lookup

**常用命令 / Common commands**:

```bash
# 服务管理 / Service management
sudo systemctl status server-manager-backend
sudo systemctl restart server-manager-backend
sudo journalctl -u server-manager-backend -f

# 数据库备份 / Database backup
cp ~/server-manager/backend/server_manager.db ~/backup_$(date +%Y%m%d).db

# SSL 证书 / SSL certificate
sudo certbot --nginx -d your-domain.com
```

**快速参考 / Quick reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (320 行 / lines)

---

## 📊 方案对比 / Comparison

| 特性 / Feature | 自动部署 / Auto | 手动部署 / Manual | 快速参考 / Quick |
|---------------|----------------|------------------|-----------------|
| 安装时间 / Install Time | ⚡ 10-15 分钟 / min | 🕐 30-60 分钟 / min | ⚡ 依经验而定 / Varies |
| 技术要求 / Skill Level | 👤 初级 / Beginner | 👥 中级 / Intermediate | 👨‍💻 高级 / Advanced |
| 自定义性 / Customization | 🔧 低 / Low | 🔧🔧🔧 高 / High | 🔧🔧 中 / Medium |
| 学习价值 / Learning Value | 📖 低 / Low | 📖📖📖 高 / High | 📖📖 中 / Medium |
| 适用场景 / Best Use | 🚀 快速上线 / Quick deploy | 📚 学习理解 / Learning | 🔍 日常维护 / Maintenance |

---

## 🛠️ 部署后步骤 / Post-Deployment Steps

无论选择哪种方案，部署完成后都需要：

Regardless of which method you choose, after deployment:

### 1. 访问系统 / Access System

```
http://your-server-ip/
```

### 2. 使用默认凭据登录 / Login with Default Credentials

- **用户名 / Username**: `admin`
- **密码 / Password**: `admin123`

### 3. ⚠️ 立即修改密码 / Change Password Immediately

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
    admin.set_password('your_new_secure_password')
    db.session.commit()
    print("Password changed successfully!")
EOF
```

### 4. 配置 SSL (可选但推荐) / Configure SSL (Optional but Recommended)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

### 5. 设置监控 / Setup Monitoring

```bash
# 查看服务状态 / Check service status
sudo systemctl status server-manager-backend

# 实时日志 / Real-time logs
sudo journalctl -u server-manager-backend -f
```

---

## 🆘 需要帮助? / Need Help?

### 问题排查流程 / Troubleshooting Flow

```
遇到问题 / Got a problem?
    ↓
1. 查看 QUICK_REFERENCE.md 故障排除部分
   Check QUICK_REFERENCE.md troubleshooting section
    ↓
2. 查看 DEPLOYMENT_UBUNTU.md 详细说明
   Check DEPLOYMENT_UBUNTU.md detailed guide
    ↓
3. 检查日志文件 / Check log files
   - Backend: sudo journalctl -u server-manager-backend
   - Nginx: /var/log/nginx/server-manager-error.log
    ↓
4. GitHub Issues
   https://github.com/mansdeanna2-collab/server-manager/issues
```

### 常见问题 / Common Issues

| 问题 / Issue | 解决方案 / Solution | 文档位置 / Doc Location |
|-------------|-------------------|----------------------|
| 后端无法启动 / Backend won't start | 检查日志和 Python 环境 / Check logs & Python env | QUICK_REFERENCE.md |
| Nginx 502 错误 / Nginx 502 error | 确认后端服务运行 / Verify backend running | DEPLOYMENT_UBUNTU.md §9 |
| 数据库权限错误 / DB permission error | 修复文件权限 / Fix file permissions | QUICK_REFERENCE.md |
| SSL 证书问题 / SSL cert issues | 重新运行 Certbot / Re-run Certbot | DEPLOYMENT_UBUNTU.md §8.1 |

---

## 📈 系统架构 / System Architecture

```
┌─────────────────────────────────────────────────────┐
│                     Internet                        │
└──────────────────────┬──────────────────────────────┘
                       │
                       ↓
        ┌──────────────────────────┐
        │   Nginx (Port 80/443)    │
        │   - SSL/TLS              │
        │   - Reverse Proxy        │
        │   - Static Files         │
        └──────────┬───────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ↓                     ↓
┌───────────────┐    ┌───────────────────┐
│   Frontend    │    │   Backend API     │
│   (Vue 3)     │    │   (Flask)         │
│   /dist/      │    │   Gunicorn        │
│               │    │   Port 5000       │
└───────────────┘    └────────┬──────────┘
                              │
                              ↓
                     ┌────────────────┐
                     │  SQLite DB     │
                     │  server_       │
                     │  manager.db    │
                     └────────────────┘
```

---

## 📱 快速链接 / Quick Links

- 📖 **主文档 / Main Docs**: [README.md](README.md)
- 📋 **快速参考 / Quick Ref**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- 📖 **完整指南 / Full Guide**: [DEPLOYMENT_UBUNTU.md](DEPLOYMENT_UBUNTU.md)
- 🚀 **自动脚本 / Auto Script**: [deploy-ubuntu.sh](deploy-ubuntu.sh)
- 🐛 **问题追踪 / Issues**: GitHub Issues
- 💬 **讨论 / Discussions**: GitHub Discussions

---

## ✅ 部署检查清单 / Deployment Checklist

使用此清单确保部署成功：

Use this checklist to ensure successful deployment:

- [ ] 系统要求满足 (Ubuntu 22.04, 1GB+ RAM) / System requirements met
- [ ] 依赖已安装 (Python 3.11, Node.js 20, Nginx) / Dependencies installed
- [ ] 后端服务运行正常 / Backend service running
- [ ] 前端构建成功 / Frontend built successfully
- [ ] Nginx 配置正确 / Nginx configured correctly
- [ ] 防火墙规则设置 / Firewall rules set
- [ ] 可以访问 Web 界面 / Web interface accessible
- [ ] 默认密码已修改 / Default password changed
- [ ] SSL 证书已配置 (如需要) / SSL configured (if needed)
- [ ] 日志轮转已设置 / Log rotation set up
- [ ] 备份脚本已配置 / Backup script configured

---

## 🎓 学习路径 / Learning Path

### 新手 / Beginners

1. 阅读 [README.md](README.md) 了解项目
2. 使用 [deploy-ubuntu.sh](deploy-ubuntu.sh) 快速部署
3. 体验功能，熟悉界面
4. 阅读 [QUICK_REFERENCE.md](QUICK_REFERENCE.md) 学习基本命令

### 进阶 / Intermediate

1. 阅读 [DEPLOYMENT_UBUNTU.md](DEPLOYMENT_UBUNTU.md) 理解架构
2. 手动部署一次，理解每个步骤
3. 学习配置文件的含义
4. 尝试性能优化

### 高级 / Advanced

1. 自定义配置和优化
2. 实现高可用部署
3. 集成监控系统
4. 贡献代码和文档

---

**版本 / Version**: 2.0.0  
**更新时间 / Last Updated**: 2025-12-08  
**状态 / Status**: ✅ 生产就绪 / Production Ready

**祝您部署顺利！/ Happy Deploying!** 🚀
