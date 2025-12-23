# Server Manager - Docker 部署指南 / Docker Deployment Guide

> 现已统一为 Docker 部署，其他方案已下线。 本指南覆盖脚本式一键部署与手动命令两种方式。

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

## 🔐 SSL/HTTPS 配置 / SSL/HTTPS Configuration

### 启用 SSL / Enable SSL

1. **使用 SSL 专用 docker-compose 文件 / Use the SSL docker-compose file**
   ```bash
   # 停止现有服务 / Stop existing services
   docker compose down
   
   # 使用 SSL 配置启动 / Start with SSL configuration
   docker compose -f docker-compose-ssl.yml up -d --build
   ```

2. **生成 SSL 证书 / Generate SSL Certificate**
   - 方式一：通过系统设置页面自动生成 / Method 1: Auto-generate via System Settings
     1. 访问 `http://your-server-ip:3080` (HTTP 端口)
     2. 登录后进入 系统设置 -> SSL设置
     3. 输入服务器的外部 IP 地址（如 `38.190.222.15`）或域名
     4. 点击"一键自动配置SSL"
   
   - 方式二：手动放置证书 / Method 2: Place certificates manually
     ```bash
     mkdir -p ./ssl
     cp your_certificate.crt ./ssl/server.crt
     cp your_private_key.key ./ssl/server.key
     ```

3. **重启服务 / Restart services**
   ```bash
   docker compose -f docker-compose-ssl.yml restart
   ```

4. **访问 HTTPS / Access via HTTPS**
   - HTTPS: `https://your-server-ip:3000`
   - HTTP (重定向): `http://your-server-ip:3080`

### SSL 相关文件 / SSL Related Files
- `docker-compose-ssl.yml`: SSL 专用的 Docker Compose 配置
- `frontend/nginx-ssl.conf`: SSL 版本的 Nginx 配置
- `frontend/Dockerfile.ssl`: SSL 专用的 Dockerfile，支持自动生成证书
- `frontend/docker-entrypoint-ssl.sh`: SSL 容器启动脚本
- `./ssl/`: SSL 证书存放目录
  - `server.crt`: 证书文件
  - `server.key`: 私钥文件

### SSL 自动配置 / SSL Auto Configuration
使用 `docker-compose-ssl.yml` 启动时，系统会自动：
1. 检测是否存在 SSL 证书
2. 如果不存在，自动生成自签名证书
3. 证书会使用检测到的外部 IP 地址

### 常见 SSL 问题 / Common SSL Issues
- **ERR_SSL_PROTOCOL_ERROR 错误**  
  这通常表示证书配置有问题。尝试以下步骤：
  1. 删除现有证书: `rm -rf ./ssl/*`
  2. 重新构建容器: `docker compose -f docker-compose-ssl.yml down && docker compose -f docker-compose-ssl.yml up -d --build`
  3. 等待容器自动生成新证书

- **证书地址不匹配 / Certificate address mismatch**  
  确保生成证书时使用的地址与访问时使用的地址一致（外部 IP 或域名）。
  如果需要为特定 IP 生成证书，请使用系统设置页面手动配置。

- **Docker 检测到内部 IP / Docker detects internal IP**  
  在系统设置中手动输入外部 IP 地址，不要依赖自动检测。

- **自签名证书警告 / Self-signed certificate warning**  
  首次访问时浏览器会显示证书警告，选择"继续访问"或"高级" -> "继续前往"即可。

- **查看证书生成日志 / View certificate generation logs**  
  ```bash
  docker compose -f docker-compose-ssl.yml logs frontend
  ```

## 🆘 常见问题 / Troubleshooting
- **`docker compose` 找不到 / command not found**  
  安装 Docker Compose 插件，或改用 `docker-compose` 命令。
- **端口被占用 / Ports already in use**  
  编辑 `docker-compose.yml` 中的 `ports` 映射，选择未占用的主机端口。
- **需要清理并重新部署 / Need a clean redeploy**  
  执行 `docker compose down -v && docker compose up -d --build`。
- **Docker 网络创建失败 (iptables 错误) / Docker network creation failed (iptables error)**
  
  如果看到类似以下错误：
  ```
  failed to create network server-manager_default: Error response from daemon: 
  add inter-network communication rule: iptables failed: Chain 'DOCKER-ISOLATION-STAGE-2' does not exist
  ```
  
  这是 Docker 的 iptables 规则不同步问题。解决方法：
  
  **方法一：重启 Docker 服务 / Method 1: Restart Docker daemon**
  ```bash
  sudo systemctl restart docker
  # 然后重新运行 / Then run again
  ./deploy-docker.sh
  ```
  
  **方法二：清理并重建网络 / Method 2: Clean and recreate networks**
  ```bash
  # 停止所有容器 / Stop all containers
  docker compose down
  
  # 删除所有未使用的网络 / Remove unused networks
  docker network prune -f
  
  # 重新部署 / Redeploy
  ./deploy-docker.sh
  ```
  
  **方法三：手动重建 iptables 规则 / Method 3: Manually rebuild iptables rules**
  ```bash
  # 停止 Docker / Stop Docker
  sudo systemctl stop docker
  
  # 清理 iptables Docker 规则 / Clear Docker iptables rules
  sudo iptables -t filter -F DOCKER-ISOLATION-STAGE-1 2>/dev/null || true
  sudo iptables -t filter -X DOCKER-ISOLATION-STAGE-1 2>/dev/null || true
  sudo iptables -t filter -F DOCKER-ISOLATION-STAGE-2 2>/dev/null || true
  sudo iptables -t filter -X DOCKER-ISOLATION-STAGE-2 2>/dev/null || true
  
  # 启动 Docker / Start Docker
  sudo systemctl start docker
  
  # 重新部署 / Redeploy
  ./deploy-docker.sh
  ```

祝你部署顺利！Happy deploying! 🚀
