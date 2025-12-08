#!/bin/bash

###############################################################################
# Server Manager - Ubuntu 22.04 Quick Deployment Script
# 服务器管理系统 - Ubuntu 22.04 快速部署脚本
#
# Usage: sudo bash deploy-ubuntu.sh
# 使用方法: sudo bash deploy-ubuntu.sh
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_USER="servermgr"
APP_DIR="/home/$APP_USER/server-manager"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
PYTHON_VERSION="3.11"
NODE_VERSION="20"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_ubuntu() {
    if [ ! -f /etc/lsb-release ]; then
        print_error "This script is for Ubuntu only"
        exit 1
    fi
    
    source /etc/lsb-release
    if [ "$DISTRIB_ID" != "Ubuntu" ]; then
        print_error "This script is for Ubuntu only"
        exit 1
    fi
    
    if [ "$DISTRIB_RELEASE" != "22.04" ]; then
        print_warning "This script is designed for Ubuntu 22.04, but you're running $DISTRIB_RELEASE"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Main installation steps
step_update_system() {
    print_header "Step 1: Updating System / 更新系统"
    apt update && apt upgrade -y
    apt install -y software-properties-common curl wget git build-essential libssl-dev libffi-dev
    print_success "System updated successfully"
}

step_install_python() {
    print_header "Step 2: Installing Python $PYTHON_VERSION / 安装 Python $PYTHON_VERSION"
    
    # Check if Python is already installed
    if command -v python$PYTHON_VERSION &> /dev/null; then
        print_info "Python $PYTHON_VERSION is already installed"
    else
        add-apt-repository ppa:deadsnakes/ppa -y
        apt update
        apt install -y python$PYTHON_VERSION python$PYTHON_VERSION-venv python$PYTHON_VERSION-dev
    fi
    
    python$PYTHON_VERSION --version
    print_success "Python $PYTHON_VERSION installed successfully"
}

step_install_nodejs() {
    print_header "Step 3: Installing Node.js $NODE_VERSION / 安装 Node.js $NODE_VERSION"
    
    # Check if Node.js is already installed
    if command -v node &> /dev/null; then
        CURRENT_NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$CURRENT_NODE_VERSION" -ge "$NODE_VERSION" ]; then
            print_info "Node.js $CURRENT_NODE_VERSION is already installed"
            return
        fi
    fi
    
    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash -
    apt install -y nodejs
    
    node --version
    npm --version
    print_success "Node.js $NODE_VERSION installed successfully"
}

step_install_nginx() {
    print_header "Step 4: Installing Nginx / 安装 Nginx"
    
    apt install -y nginx
    systemctl start nginx
    systemctl enable nginx
    
    print_success "Nginx installed successfully"
}

step_create_user() {
    print_header "Step 5: Creating Application User / 创建应用用户"
    
    if id "$APP_USER" &>/dev/null; then
        print_info "User $APP_USER already exists"
    else
        adduser --disabled-password --gecos "" $APP_USER
        print_success "User $APP_USER created successfully"
    fi
}

step_clone_or_copy() {
    print_header "Step 6: Setting Up Application Files / 设置应用文件"
    
    # Create directory
    sudo -u $APP_USER mkdir -p $APP_DIR
    
    print_info "Application directory: $APP_DIR"
    print_warning "Please copy your application files to $APP_DIR"
    print_warning "Or clone from git: cd $APP_DIR && git clone <your-repo> ."
    
    read -p "Press Enter when files are ready..."
}

step_setup_backend() {
    print_header "Step 7: Setting Up Backend / 设置后端"
    
    cd $BACKEND_DIR
    
    # Create virtual environment
    print_info "Creating Python virtual environment..."
    sudo -u $APP_USER python$PYTHON_VERSION -m venv venv
    
    # Install dependencies
    print_info "Installing Python dependencies..."
    sudo -u $APP_USER $BACKEND_DIR/venv/bin/pip install --upgrade pip
    sudo -u $APP_USER $BACKEND_DIR/venv/bin/pip install -r requirements.txt
    sudo -u $APP_USER $BACKEND_DIR/venv/bin/pip install gunicorn
    
    # Create .env file if not exists
    if [ ! -f .env ]; then
        print_info "Creating .env file..."
        sudo -u $APP_USER cp .env.example .env
        
        # Generate secure keys
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
        
        sudo -u $APP_USER sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        sudo -u $APP_USER sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET_KEY/" .env
        sudo -u $APP_USER sed -i "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
        sudo -u $APP_USER sed -i "s/DEBUG=True/DEBUG=False/" .env
        sudo -u $APP_USER sed -i "s|DATABASE_URI=.*|DATABASE_URI=sqlite:///$BACKEND_DIR/server_manager.db|" .env
        
        print_success ".env file created with secure keys"
    fi
    
    # Create logs directory
    sudo -u $APP_USER mkdir -p logs
    
    # Initialize database
    print_info "Initializing database..."
    sudo -u $APP_USER $BACKEND_DIR/venv/bin/python -c "from app import create_app; app = create_app()"
    
    print_success "Backend setup completed"
}

step_setup_frontend() {
    print_header "Step 8: Setting Up Frontend / 设置前端"
    
    cd $FRONTEND_DIR
    
    # Install dependencies
    print_info "Installing npm dependencies..."
    sudo -u $APP_USER npm install
    
    # Create .env.production if not exists
    if [ ! -f .env.production ]; then
        print_info "Creating .env.production..."
        sudo -u $APP_USER cp .env.example .env.production
        
        read -p "Enter your domain or IP (e.g., example.com or 192.168.1.100): " DOMAIN
        sudo -u $APP_USER sed -i "s|VITE_API_BASE_URL=.*|VITE_API_BASE_URL=http://$DOMAIN/api|" .env.production
    fi
    
    # Build frontend
    print_info "Building frontend..."
    sudo -u $APP_USER npm run build
    
    print_success "Frontend setup completed"
}

step_setup_systemd() {
    print_header "Step 9: Setting Up Systemd Service / 设置系统服务"
    
    # Create systemd service file
    cat > /etc/systemd/system/server-manager-backend.service << EOF
[Unit]
Description=Server Manager Backend API
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin"
EnvironmentFile=$BACKEND_DIR/.env

ExecStart=$BACKEND_DIR/venv/bin/gunicorn \\
    --bind 127.0.0.1:5000 \\
    --workers 4 \\
    --threads 2 \\
    --timeout 60 \\
    --access-logfile $BACKEND_DIR/logs/access.log \\
    --error-logfile $BACKEND_DIR/logs/error.log \\
    --log-level info \\
    'app:create_app()'

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload
    
    # Start and enable service
    systemctl start server-manager-backend
    systemctl enable server-manager-backend
    
    # Check status
    sleep 2
    if systemctl is-active --quiet server-manager-backend; then
        print_success "Backend service started successfully"
    else
        print_error "Backend service failed to start"
        systemctl status server-manager-backend
    fi
}

step_setup_nginx() {
    print_header "Step 10: Setting Up Nginx / 设置 Nginx"
    
    read -p "Enter your domain or IP (e.g., example.com or 192.168.1.100): " DOMAIN
    
    # Create Nginx configuration
    cat > /etc/nginx/sites-available/server-manager << EOF
upstream backend {
    server 127.0.0.1:5000;
    keepalive 64;
}

server {
    listen 80;
    server_name $DOMAIN;
    
    access_log /var/log/nginx/server-manager-access.log;
    error_log /var/log/nginx/server-manager-error.log;
    
    location / {
        root $FRONTEND_DIR/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
        
        location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
    }
    
    location /health {
        proxy_pass http://backend/health;
        access_log off;
    }
    
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    server_tokens off;
    client_max_body_size 10M;
}
EOF

    # Enable site
    ln -sf /etc/nginx/sites-available/server-manager /etc/nginx/sites-enabled/
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Test configuration
    nginx -t
    
    # Reload Nginx
    systemctl reload nginx
    
    print_success "Nginx configured successfully"
}

step_setup_firewall() {
    print_header "Step 11: Setting Up Firewall / 设置防火墙"
    
    # Install UFW if not installed
    apt install -y ufw
    
    # Configure UFW
    ufw --force enable
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 'Nginx Full'
    
    ufw status
    
    print_success "Firewall configured successfully"
}

step_final_checks() {
    print_header "Step 12: Final Checks / 最终检查"
    
    print_info "Checking backend service..."
    systemctl status server-manager-backend --no-pager
    
    print_info "Checking Nginx..."
    systemctl status nginx --no-pager
    
    print_info "Testing API..."
    sleep 2
    curl -s http://localhost/health | python3 -m json.tool || true
    
    print_success "All checks completed"
}

print_summary() {
    print_header "Installation Complete! / 安装完成！"
    
    echo ""
    echo -e "${GREEN}✓ Server Manager has been successfully deployed!${NC}"
    echo -e "${GREEN}  服务器管理系统已成功部署！${NC}"
    echo ""
    echo -e "${BLUE}Access your application at:${NC}"
    echo -e "${BLUE}访问您的应用:${NC}"
    echo ""
    echo -e "  ${YELLOW}http://$(hostname -I | awk '{print $1}')/${NC}"
    echo ""
    echo -e "${BLUE}Default credentials / 默认凭据:${NC}"
    echo -e "  ${YELLOW}Username / 用户名: admin${NC}"
    echo -e "  ${YELLOW}Password / 密码: admin123${NC}"
    echo ""
    echo -e "${RED}⚠  IMPORTANT / 重要提示:${NC}"
    echo -e "${RED}   Please change the default password immediately!${NC}"
    echo -e "${RED}   请立即更改默认密码！${NC}"
    echo ""
    echo -e "${BLUE}Useful commands / 常用命令:${NC}"
    echo -e "  ${YELLOW}Check service status / 查看服务状态:${NC}"
    echo -e "    sudo systemctl status server-manager-backend"
    echo ""
    echo -e "  ${YELLOW}View logs / 查看日志:${NC}"
    echo -e "    sudo journalctl -u server-manager-backend -f"
    echo ""
    echo -e "  ${YELLOW}Restart service / 重启服务:${NC}"
    echo -e "    sudo systemctl restart server-manager-backend"
    echo ""
    echo -e "${BLUE}For detailed documentation, see:${NC}"
    echo -e "${BLUE}详细文档请查看:${NC}"
    echo -e "  ${YELLOW}$APP_DIR/DEPLOYMENT_UBUNTU.md${NC}"
    echo ""
}

# Main execution
main() {
    print_header "Server Manager - Ubuntu 22.04 Deployment"
    print_header "服务器管理系统 - Ubuntu 22.04 部署脚本"
    
    check_root
    check_ubuntu
    
    step_update_system
    step_install_python
    step_install_nodejs
    step_install_nginx
    step_create_user
    
    print_warning "Please copy your application files to $APP_DIR now"
    print_warning "请现在将应用文件复制到 $APP_DIR"
    read -p "Press Enter when ready / 准备好后按回车键..."
    
    step_setup_backend
    step_setup_frontend
    step_setup_systemd
    step_setup_nginx
    step_setup_firewall
    step_final_checks
    
    print_summary
}

# Run main function
main
