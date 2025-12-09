# 文档索引 / Documentation Index

## 📚 当前文档 / Current Docs
1. **README.md** — 项目概览与 Docker 快速上手 / Project overview and Docker quick start  
2. **DEPLOYMENT_OPTIONS.md** — Docker 部署指南（脚本 & 手动命令） / Docker deployment guide (script & manual commands)  
3. **deploy-docker.sh** — 一键启动脚本 / One-command launcher  
4. **docker-compose.yml** — 前后端容器编排 / Frontend & backend orchestration

> 其他旧版手动部署文档已下线，仅保留存档，不再推荐使用。Legacy manual deployment docs are archived and no longer recommended.

## 🚀 推荐路径 / Recommended Path
```
1) 阅读 README.md (2 min)
2) 运行 ./deploy-docker.sh (3 min)
3) 登录前端并修改默认密码
```

## 🔗 快速链接 / Quick Links
- ▶️ Docker 一键部署 / One-command deploy: `./deploy-docker.sh`
- ⚙️ 手动 Docker Compose: `docker compose up -d --build`
- 📝 Docker 指南 / Docker guide: [DEPLOYMENT_OPTIONS.md](DEPLOYMENT_OPTIONS.md)
- 🗂️ 项目概览 / Project overview: [README.md](README.md)

## 🆘 需要帮助? / Need Help?
- 检查容器状态 / Check containers: `docker compose ps`
- 查看日志 / Logs: `docker compose logs -f`
- 清理重建 / Clean rebuild: `docker compose down -v && docker compose up -d --build`

感谢使用 Server Manager! / Thanks for using Server Manager! 🎉
