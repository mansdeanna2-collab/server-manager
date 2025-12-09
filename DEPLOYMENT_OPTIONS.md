# Server Manager - Docker 部署指南 / Docker Deployment Guide

> 现已统一为 Docker 部署，其他方案已下线。本指南覆盖脚本式一键部署与手动命令两种方式。

## 🎯 部署方式 / Deployment Methods

### 1) 一键脚本（推荐） / One-command Script (Recommended)

**前置 / Prerequisites**
- Docker Engine
- Docker Compose 插件（或 `docker-compose`）

**步骤 / Steps**
```bash
git clone https://github.com/mansdeanna2-collab/server-manager.git
cd server-manager
chmod +x deploy-docker.sh
./deploy-docker.sh
```

**结果 / Result**
- Backend API: `http://localhost:5000`
- Frontend UI: `http://localhost:3000`
- 默认账号 / Default credentials: `admin / admin123`

### 2) 手动 Docker Compose / Manual Docker Compose

```bash
# 构建并启动 / Build and start
docker compose up -d --build

# 查看状态 / Check status
docker compose ps

# 查看日志 / Tail logs
docker compose logs -f

# 重启 / Restart
docker compose restart

# 停止并移除容器 / Stop and remove
docker compose down
```

> 如果你的环境只提供 `docker-compose` 二进制，请将上述命令中的 `docker compose` 替换为 `docker-compose`。

## 🧰 目录说明 / Relevant Files
- `docker-compose.yml`：定义前后端服务、端口与卷映射。
- `backend/Dockerfile`：Flask API 镜像构建。
- `frontend/Dockerfile`：Vue 前端构建并由 Nginx 提供静态文件。
- `deploy-docker.sh`：一键启动脚本（推荐）。

## ✅ 部署后检查 / Post-deploy Checklist
- [ ] 前端可通过 `http://localhost:3000` 访问
- [ ] 后端 API 可通过 `http://localhost:5000/api` 访问
- [ ] 登录后立即修改默认密码
- [ ] (可选) 修改 `docker-compose.yml` 端口映射以适配生产环境

## 🆘 常见问题 / Troubleshooting
- **`docker compose` 找不到 / command not found**  
  安装 Docker Compose 插件，或改用 `docker-compose` 命令。
- **端口被占用 / Ports already in use**  
  编辑 `docker-compose.yml` 中的 `ports` 映射，选择未占用的主机端口。
- **需要清理并重新部署 / Need a clean redeploy**  
  执行 `docker compose down -v && docker compose up -d --build`。

祝你部署顺利！Happy deploying! 🚀
