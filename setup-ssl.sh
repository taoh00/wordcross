#!/bin/bash

# ============================================
# 填单词 - SSL 证书设置脚本
# 使用 Let's Encrypt 免费证书
# ============================================

set -e

# 配置变量
DOMAIN="superhe.art"
EMAIL="admin@superhe.art"  # 更换为你的邮箱
REMOTE_HOST="root@superhe.art"
REMOTE_DIR="/opt/wordcross"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_help() {
    echo "用法: $0 <命令>"
    echo ""
    echo "命令:"
    echo "  init          首次初始化SSL证书（在远程服务器执行）"
    echo "  renew         手动续期证书"
    echo "  status        查看证书状态"
    echo "  test          测试证书配置"
    echo "  deploy        完整部署（含SSL）"
    echo "  local-init    本地初始化（用于测试）"
    echo ""
    echo "首次部署流程:"
    echo "  1. 确保域名 $DOMAIN 已解析到服务器IP"
    echo "  2. 运行 $0 deploy 进行完整部署"
    echo ""
}

# 检查是否在远程服务器上
check_remote() {
    if [[ ! -d "$REMOTE_DIR" ]]; then
        log_error "此命令需要在远程服务器 ($REMOTE_HOST) 上执行"
        log_info "请先 SSH 到服务器: ssh $REMOTE_HOST"
        log_info "然后进入目录: cd $REMOTE_DIR"
        exit 1
    fi
}

# 创建必要的目录
create_dirs() {
    log_info "创建证书目录..."
    mkdir -p certbot/conf
    mkdir -p certbot/www
    log_success "目录创建完成"
}

# 初始化证书（首次获取）
init_cert() {
    check_remote
    
    log_info "===== 首次获取 Let's Encrypt 证书 ====="
    
    # 创建目录
    create_dirs
    
    # 使用初始化配置启动nginx（仅HTTP）
    log_info "启动临时 nginx 服务器用于域名验证..."
    
    # 创建临时docker-compose配置
    cat > docker-compose.init.yml << 'EOF'
version: '3.8'
services:
  nginx-init:
    image: nginx:alpine
    container_name: wordcross-nginx-init
    ports:
      - "10010:80"
    volumes:
      - ./src/frontend/nginx.init.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certbot/www:/var/www/certbot:rw
EOF
    
    # 启动临时nginx
    docker compose -f docker-compose.init.yml up -d
    
    sleep 3
    
    # 获取证书
    log_info "获取 Let's Encrypt 证书..."
    docker run --rm \
        -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
        -v "$(pwd)/certbot/www:/var/www/certbot" \
        certbot/certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --force-renewal \
        -d "$DOMAIN"
    
    # 停止临时nginx
    docker compose -f docker-compose.init.yml down
    rm -f docker-compose.init.yml
    
    log_success "证书获取成功！"
    log_info "证书位置: certbot/conf/live/$DOMAIN/"
    
    # 验证证书
    if [[ -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]]; then
        log_success "证书文件验证通过"
        openssl x509 -in "certbot/conf/live/$DOMAIN/fullchain.pem" -noout -dates
    else
        log_error "证书文件未找到"
        exit 1
    fi
}

# 续期证书
renew_cert() {
    check_remote
    
    log_info "===== 续期 SSL 证书 ====="
    
    docker compose -f docker-compose.prod.yml run --rm certbot renew
    
    # 重载nginx配置
    docker compose -f docker-compose.prod.yml exec frontend nginx -s reload
    
    log_success "证书续期完成"
}

# 查看证书状态
cert_status() {
    if [[ -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]]; then
        log_info "===== 证书状态 ====="
        openssl x509 -in "certbot/conf/live/$DOMAIN/fullchain.pem" -noout -text | grep -E "(Subject:|Not Before:|Not After:)"
        echo ""
        log_info "证书到期时间:"
        openssl x509 -in "certbot/conf/live/$DOMAIN/fullchain.pem" -noout -enddate
    else
        log_warn "证书文件不存在: certbot/conf/live/$DOMAIN/fullchain.pem"
    fi
}

# 测试证书配置
test_cert() {
    log_info "===== 测试 SSL 配置 ====="
    
    # 测试HTTPS连接
    log_info "测试 HTTPS 连接..."
    curl -I --connect-timeout 5 "https://$DOMAIN:10443" 2>/dev/null || {
        log_warn "HTTPS 连接测试失败，可能证书未配置或服务未启动"
    }
    
    # 测试证书有效性
    log_info "测试证书有效性..."
    echo | openssl s_client -connect "$DOMAIN:10443" -servername "$DOMAIN" 2>/dev/null | openssl x509 -noout -dates || {
        log_warn "无法获取证书信息"
    }
}

# 完整部署（含SSL）
deploy_ssl() {
    log_info "===== 完整 SSL 部署 ====="
    
    # 检查是否有证书
    if [[ ! -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]]; then
        log_warn "证书不存在，将先获取证书..."
        init_cert
    fi
    
    # 使用SSL配置启动
    log_info "使用 SSL 配置启动服务..."
    docker compose -f docker-compose.prod.yml up -d
    
    log_success "SSL 部署完成！"
    echo ""
    log_info "访问地址:"
    echo "  HTTP:  http://$DOMAIN:10010 (自动重定向)"
    echo "  HTTPS: https://$DOMAIN:10443"
}

# 本地测试初始化（生成自签名证书）
local_init() {
    log_info "===== 本地测试: 生成自签名证书 ====="
    
    create_dirs
    
    # 生成自签名证书
    mkdir -p "certbot/conf/live/$DOMAIN"
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "certbot/conf/live/$DOMAIN/privkey.pem" \
        -out "certbot/conf/live/$DOMAIN/fullchain.pem" \
        -subj "/CN=$DOMAIN"
    
    log_success "自签名证书生成完成（仅用于测试）"
    log_warn "生产环境请使用 '$0 init' 获取真实证书"
}

# 主入口
case "${1:-help}" in
    init)
        init_cert
        ;;
    renew)
        renew_cert
        ;;
    status)
        cert_status
        ;;
    test)
        test_cert
        ;;
    deploy)
        deploy_ssl
        ;;
    local-init)
        local_init
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "未知命令: $1"
        show_help
        exit 1
        ;;
esac
