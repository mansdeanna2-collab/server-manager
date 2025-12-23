#!/usr/bin/env bash

###############################################################################
# Server Manager - Docker Deployment Script
# 服务器管理系统 - Docker 部署脚本
#
# Usage / 使用方法:
#   ./deploy-docker.sh [OPTIONS]
#
# Options / 选项:
#   --ssl         Use SSL configuration (HTTPS) / 使用 SSL 配置 (HTTPS)
#   --clean       Clean rebuild (remove volumes) / 清理重建（删除数据卷）
#   --stop        Stop all services / 停止所有服务
#   --restart     Restart all services / 重启所有服务
#   --status      Show service status / 显示服务状态
#   --logs        Show service logs / 显示服务日志
#   --help        Show this help message / 显示帮助信息
#
###############################################################################

set -euo pipefail

# Configuration / 配置
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="docker-compose.yml"
COMPOSE_SSL_FILE="docker-compose-ssl.yml"
SSL_DIR="$ROOT_DIR/ssl"
SERVER_FILES_DIR="$ROOT_DIR/server_files"

# Service Ports / 服务端口
BACKEND_PORT=5000
FRONTEND_PORT=3000
FRONTEND_HTTP_PORT=3080  # For SSL mode

# Colors / 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Options / 选项
USE_SSL=false
CLEAN_BUILD=false
SHOW_HELP=false
DO_STOP=false
DO_RESTART=false
SHOW_STATUS=false
SHOW_LOGS=false

###############################################################################
# Helper Functions / 辅助函数
###############################################################################

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

info() {
    echo -e "${CYAN}[INFO]${NC} $*"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
    exit 1
}

require_cmd() {
    command -v "$1" >/dev/null 2>&1 || error "Missing dependency: $1. Please install it first. / 缺少依赖：$1，请先安装。"
}

show_help() {
    cat << EOF
${BLUE}Server Manager - Docker Deployment Script${NC}
${BLUE}服务器管理系统 - Docker 部署脚本${NC}

${YELLOW}Usage / 使用方法:${NC}
  ./deploy-docker.sh [OPTIONS]

${YELLOW}Options / 选项:${NC}
  ${GREEN}--ssl${NC}         Use SSL configuration (HTTPS)
                使用 SSL 配置 (HTTPS)
  ${GREEN}--clean${NC}       Clean rebuild (remove volumes and rebuild)
                清理重建（删除数据卷并重新构建）
  ${GREEN}--stop${NC}        Stop all services
                停止所有服务
  ${GREEN}--restart${NC}     Restart all services
                重启所有服务
  ${GREEN}--status${NC}      Show service status
                显示服务状态
  ${GREEN}--logs${NC}        Show service logs (use Ctrl+C to exit)
                显示服务日志（按 Ctrl+C 退出）
  ${GREEN}--help${NC}        Show this help message
                显示帮助信息

${YELLOW}Examples / 示例:${NC}
  ./deploy-docker.sh                  # Standard deployment / 标准部署
  ./deploy-docker.sh --ssl            # Deploy with SSL/HTTPS / 使用 SSL/HTTPS 部署
  ./deploy-docker.sh --clean          # Clean and rebuild / 清理并重建
  ./deploy-docker.sh --ssl --clean    # SSL with clean rebuild / SSL 清理重建
  ./deploy-docker.sh --status         # Check service status / 检查服务状态
  ./deploy-docker.sh --logs           # View logs / 查看日志

${YELLOW}Documentation / 文档:${NC}
  See DEPLOYMENT_OPTIONS.md for detailed instructions
  详细说明请查看 DEPLOYMENT_OPTIONS.md

EOF
}

###############################################################################
# Parse Arguments / 解析参数
###############################################################################

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --ssl)
                USE_SSL=true
                shift
                ;;
            --clean)
                CLEAN_BUILD=true
                shift
                ;;
            --stop)
                DO_STOP=true
                shift
                ;;
            --restart)
                DO_RESTART=true
                shift
                ;;
            --status)
                SHOW_STATUS=true
                shift
                ;;
            --logs)
                SHOW_LOGS=true
                shift
                ;;
            --help|-h)
                SHOW_HELP=true
                shift
                ;;
            *)
                warn "Unknown option: $1 / 未知选项：$1"
                show_help
                exit 1
                ;;
        esac
    done
}

###############################################################################
# Pre-deployment Checks / 部署前检查
###############################################################################

check_dependencies() {
    info "Checking dependencies... / 检查依赖..."
    
    require_cmd docker
    
    if docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD=(docker compose)
    elif command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD=(docker-compose)
    else
        error "Docker Compose not found. Please install the Docker Compose plugin or docker-compose. / 未检测到 Docker Compose，请安装 Docker Compose 插件或 docker-compose。"
    fi
    
    success "Dependencies OK / 依赖检查通过"
}

setup_directories() {
    info "Setting up directories... / 设置目录..."
    
    # Create server_files directory if not exists
    if [[ ! -d "$SERVER_FILES_DIR" ]]; then
        mkdir -p "$SERVER_FILES_DIR"
        info "Created server_files directory / 已创建 server_files 目录"
    fi
    
    # Create ssl directory if using SSL
    if [[ "$USE_SSL" == true ]] && [[ ! -d "$SSL_DIR" ]]; then
        mkdir -p "$SSL_DIR"
        info "Created ssl directory / 已创建 ssl 目录"
    fi
    
    success "Directories ready / 目录准备就绪"
}

select_compose_file() {
    if [[ "$USE_SSL" == true ]]; then
        COMPOSE_FILE="$COMPOSE_SSL_FILE"
        if [[ ! -f "$ROOT_DIR/$COMPOSE_FILE" ]]; then
            error "SSL compose file not found: $COMPOSE_FILE / SSL 配置文件未找到：$COMPOSE_FILE"
        fi
        info "Using SSL configuration: $COMPOSE_FILE / 使用 SSL 配置：$COMPOSE_FILE"
    else
        if [[ ! -f "$ROOT_DIR/$COMPOSE_FILE" ]]; then
            error "Compose file not found: $COMPOSE_FILE / 配置文件未找到：$COMPOSE_FILE"
        fi
        info "Using standard configuration: $COMPOSE_FILE / 使用标准配置：$COMPOSE_FILE"
    fi
}

###############################################################################
# Docker Operations / Docker 操作
###############################################################################

stop_services() {
    info "Stopping services... / 停止服务..."
    pushd "$ROOT_DIR" >/dev/null
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" down || true
    # Also try the other compose file in case it was used before
    if [[ "$USE_SSL" == true ]]; then
        "${COMPOSE_CMD[@]}" -f "docker-compose.yml" down 2>/dev/null || true
    else
        "${COMPOSE_CMD[@]}" -f "docker-compose-ssl.yml" down 2>/dev/null || true
    fi
    popd >/dev/null
    success "Services stopped / 服务已停止"
}

clean_volumes() {
    info "Cleaning volumes... / 清理数据卷..."
    pushd "$ROOT_DIR" >/dev/null
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" down -v 2>/dev/null || true
    "${COMPOSE_CMD[@]}" -f "docker-compose.yml" down -v 2>/dev/null || true
    "${COMPOSE_CMD[@]}" -f "docker-compose-ssl.yml" down -v 2>/dev/null || true
    popd >/dev/null
    success "Volumes cleaned / 数据卷已清理"
}

build_and_start() {
    info "Building and starting services... / 构建并启动服务..."
    pushd "$ROOT_DIR" >/dev/null
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" up -d --build
    popd >/dev/null
    success "Services started / 服务已启动"
}

restart_services() {
    info "Restarting services... / 重启服务..."
    pushd "$ROOT_DIR" >/dev/null
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" restart
    popd >/dev/null
    success "Services restarted / 服务已重启"
}

show_service_status() {
    info "Service status / 服务状态:"
    pushd "$ROOT_DIR" >/dev/null
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" ps
    popd >/dev/null
}

show_service_logs() {
    info "Showing logs (Ctrl+C to exit) / 显示日志（按 Ctrl+C 退出）..."
    pushd "$ROOT_DIR" >/dev/null
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" logs -f
    popd >/dev/null
}

###############################################################################
# Health Check / 健康检查
###############################################################################

wait_for_services() {
    info "Waiting for services to be ready... / 等待服务就绪..."
    
    local max_attempts=30
    local attempt=1
    local backend_ready=false
    local frontend_ready=false
    
    while [[ $attempt -le $max_attempts ]]; do
        # Check backend health endpoint
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$BACKEND_PORT/health" 2>/dev/null | grep -q "200"; then
            backend_ready=true
        fi
        
        # Check frontend availability
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$FRONTEND_PORT" 2>/dev/null | grep -qE "200|301|302"; then
            frontend_ready=true
        fi
        
        if [[ "$backend_ready" == true ]] && [[ "$frontend_ready" == true ]]; then
            success "All services are ready! / 所有服务已就绪！"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    echo ""
    warn "Some services may not be ready yet. Check logs with --logs / 部分服务可能尚未就绪，请使用 --logs 查看日志"
    return 0
}

###############################################################################
# Print Summary / 打印摘要
###############################################################################

print_success_summary() {
    echo ""
    print_header "Deployment Complete! / 部署完成！"
    echo ""
    
    if [[ "$USE_SSL" == true ]]; then
        echo -e "${GREEN}✓ Services deployed with SSL/HTTPS${NC}"
        echo -e "${GREEN}  已使用 SSL/HTTPS 部署服务${NC}"
        echo ""
        echo -e "${YELLOW}Access URLs / 访问地址:${NC}"
        echo -e "  HTTPS Frontend: ${CYAN}https://localhost:$FRONTEND_PORT${NC}"
        echo -e "  HTTP  Frontend: ${CYAN}http://localhost:$FRONTEND_HTTP_PORT${NC} (redirects to HTTPS)"
        echo -e "  Backend API:    ${CYAN}http://localhost:$BACKEND_PORT${NC}"
    else
        echo -e "${GREEN}✓ Services deployed successfully${NC}"
        echo -e "${GREEN}  服务已成功部署${NC}"
        echo ""
        echo -e "${YELLOW}Access URLs / 访问地址:${NC}"
        echo -e "  Frontend: ${CYAN}http://localhost:$FRONTEND_PORT${NC}"
        echo -e "  Backend:  ${CYAN}http://localhost:$BACKEND_PORT${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}Default Credentials / 默认凭据:${NC}"
    echo -e "  Username / 用户名: ${CYAN}admin${NC}"
    echo -e "  Password / 密码:   ${CYAN}admin123${NC}"
    echo ""
    echo -e "${RED}⚠  IMPORTANT: Please change the default password after login!${NC}"
    echo -e "${RED}   重要提示：请登录后立即修改默认密码！${NC}"
    echo ""
    echo -e "${YELLOW}Useful Commands / 常用命令:${NC}"
    echo -e "  Check status / 查看状态:  ${CYAN}./deploy-docker.sh --status${NC}"
    echo -e "  View logs / 查看日志:     ${CYAN}./deploy-docker.sh --logs${NC}"
    echo -e "  Restart / 重启服务:       ${CYAN}./deploy-docker.sh --restart${NC}"
    echo -e "  Stop / 停止服务:          ${CYAN}./deploy-docker.sh --stop${NC}"
    echo ""
}

###############################################################################
# Main Function / 主函数
###############################################################################

main() {
    parse_args "$@"
    
    # Show help if requested
    if [[ "$SHOW_HELP" == true ]]; then
        show_help
        exit 0
    fi
    
    print_header "Server Manager - Docker Deployment"
    
    # Check dependencies first
    check_dependencies
    
    # Select compose file
    select_compose_file
    
    # Handle different operations
    if [[ "$SHOW_STATUS" == true ]]; then
        show_service_status
        exit 0
    fi
    
    if [[ "$SHOW_LOGS" == true ]]; then
        show_service_logs
        exit 0
    fi
    
    if [[ "$DO_STOP" == true ]]; then
        stop_services
        exit 0
    fi
    
    if [[ "$DO_RESTART" == true ]]; then
        restart_services
        exit 0
    fi
    
    # Setup directories
    setup_directories
    
    # Clean if requested
    if [[ "$CLEAN_BUILD" == true ]]; then
        warn "Clean build requested. This will remove all data volumes! / 请求清理重建，这将删除所有数据卷！"
        read -r -p "Continue? / 继续？ [y/N] " response
        case "$response" in
            [yY][eE][sS]|[yY])
                clean_volumes
                ;;
            *)
                info "Clean build cancelled / 清理重建已取消"
                ;;
        esac
    fi
    
    # Build and start services
    build_and_start
    
    # Wait for services and show summary
    wait_for_services
    show_service_status
    print_success_summary
}

# Run main function
main "$@"
