#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="docker-compose.yml"

info() {
  echo -e "\033[1;34m[INFO]\033[0m $*"
}

error() {
  echo -e "\033[1;31m[ERROR]\033[0m $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || error "Missing dependency: $1. 请先安装 / please install it first."
}

require_cmd docker

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  error "Docker Compose not found (未检测到 docker compose). Please install the Docker Compose plugin or docker-compose."
fi

info "Using Docker Compose to build and start services... / 使用 Docker Compose 构建并启动服务..."
cd "$ROOT_DIR"
"${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" up -d --build

info "Deployment finished! / 部署完成！"
info "Frontend: http://localhost:3000"
info "Backend: http://localhost:5000"
info "Default account: admin / admin123"
