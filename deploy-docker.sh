#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

info() {
  echo -e "\033[1;34m[INFO]\033[0m $*"
}

error() {
  echo -e "\033[1;31m[ERROR]\033[0m $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || error "缺少依赖：$1，请先安装。"
}

require_cmd docker

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  error "未检测到 Docker Compose，请先安装 docker compose 插件或 docker-compose。"
fi

info "使用 Docker Compose 构建并启动服务..."
cd "$ROOT_DIR"
"${COMPOSE_CMD[@]}" -f docker-compose.yml up -d --build

info "部署完成！"
info "前端: http://localhost:3000"
info "后端: http://localhost:5000"
info "默认账号: admin / admin123"
