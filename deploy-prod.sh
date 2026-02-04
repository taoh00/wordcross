#!/bin/bash
# 我爱填单词 - 生产环境部署脚本
# 使用: ./deploy-prod.sh [build|deploy|start|stop|status|logs|all]
# 目标服务器: superhe.art

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

# ============ 配置 ============
PROJECT_NAME="wordcross"
REMOTE_HOST="superhe.art"
REMOTE_USER="root"
REMOTE_DIR="/opt/wordcross"
LOCAL_IMAGES_DIR="$PROJECT_ROOT/docker-images"
AUDIO_ARCHIVE="$PROJECT_ROOT/wordcross-audio.tar.gz"

# 端口配置
FRONTEND_PORT=10010
FRONTEND_PORT_SSL=10443
BACKEND_PORT=10012  # 内部端口

# SSL相关
SSL_ENABLED=false  # 是否启用SSL

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_title() { echo -e "${BLUE}========================================${NC}"; echo -e "${BLUE} $1${NC}"; echo -e "${BLUE}========================================${NC}"; }

# 检查Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi
}

# 检查SSH连接
check_ssh() {
    log_info "检查SSH连接到 ${REMOTE_HOST}..."
    if ! ssh -o ConnectTimeout=5 ${REMOTE_USER}@${REMOTE_HOST} "echo 'SSH连接成功'" &>/dev/null; then
        log_error "无法连接到 ${REMOTE_USER}@${REMOTE_HOST}"
        log_error "请确保SSH密钥已配置"
        exit 1
    fi
    log_info "SSH连接正常 ✓"
}

# 同步关卡数据到前端
sync_levels() {
    log_info "同步关卡数据到前端..."
    
    local SOURCE_DIR="$PROJECT_ROOT/src/data/levels"
    local TARGET_DIR="$PROJECT_ROOT/src/frontend/public/data/levels"
    local SUMMARY_FILE="$PROJECT_ROOT/src/data/levels_summary.json"
    local TARGET_SUMMARY="$PROJECT_ROOT/src/frontend/public/data/levels_summary.json"
    
    mkdir -p "$TARGET_DIR"
    mkdir -p "$(dirname $TARGET_SUMMARY)"
    
    if [ -d "$SOURCE_DIR" ]; then
        cp -r "$SOURCE_DIR"/* "$TARGET_DIR/"
        log_info "关卡数据已同步 ✓"
    fi
    
    if [ -f "$SUMMARY_FILE" ]; then
        cp "$SUMMARY_FILE" "$TARGET_SUMMARY"
    fi
}

# 本地构建镜像
build() {
    log_title "构建Docker镜像"
    
    check_docker
    sync_levels
    
    log_info "开始构建镜像..."
    cd "$PROJECT_ROOT"
    docker compose build --no-cache
    
    log_info "镜像构建完成 ✓"
    docker images | grep $PROJECT_NAME
}

# 构建SSL版本镜像
build_ssl() {
    log_title "构建SSL版Docker镜像"
    
    check_docker
    sync_levels
    
    log_info "开始构建SSL版镜像..."
    cd "$PROJECT_ROOT"
    
    # 使用SSL版的docker-compose配置
    docker compose -f docker-compose.prod.yml build --no-cache
    
    log_info "SSL版镜像构建完成 ✓"
    docker images | grep $PROJECT_NAME
}

# 导出镜像
export_images() {
    log_info "导出镜像为tar包..."
    
    mkdir -p "$LOCAL_IMAGES_DIR"
    
    # 检查镜像是否存在
    if ! docker images wordcross-frontend:latest --format "{{.Repository}}" | grep -q "wordcross-frontend"; then
        log_error "前端镜像不存在，请先运行 ./deploy-prod.sh build"
        exit 1
    fi
    
    if ! docker images wordcross-backend:latest --format "{{.Repository}}" | grep -q "wordcross-backend"; then
        log_error "后端镜像不存在，请先运行 ./deploy-prod.sh build"
        exit 1
    fi
    
    docker save wordcross-backend:latest | gzip > "$LOCAL_IMAGES_DIR/wordcross-backend.tar.gz"
    docker save wordcross-frontend:latest | gzip > "$LOCAL_IMAGES_DIR/wordcross-frontend.tar.gz"
    
    log_info "镜像导出完成 ✓"
    ls -lh "$LOCAL_IMAGES_DIR/"*.tar.gz
}

# 打包关卡数据
pack_levels() {
    log_info "打包关卡数据..."
    
    cd "$PROJECT_ROOT"
    tar -czf "$LOCAL_IMAGES_DIR/levels.tar.gz" -C src/data levels levels_summary.json 2>/dev/null || \
    tar -czf "$LOCAL_IMAGES_DIR/levels.tar.gz" -C src/data levels
    
    local size=$(du -h "$LOCAL_IMAGES_DIR/levels.tar.gz" | cut -f1)
    log_info "关卡数据打包完成: $size"
}

# 打包音频文件
pack_audio() {
    log_info "打包音频文件..."
    
    local AUDIO_DIR="$PROJECT_ROOT/data/audio"
    
    if [ ! -d "$AUDIO_DIR" ]; then
        log_error "音频目录 $AUDIO_DIR 不存在"
        exit 1
    fi
    
    local file_count=$(find "$AUDIO_DIR" -name "*.mp3" | wc -l)
    log_info "音频文件数量: $file_count"
    
    if command -v pigz &> /dev/null; then
        log_info "使用 pigz 多线程压缩..."
        tar -I pigz -cf "$AUDIO_ARCHIVE" -C "$PROJECT_ROOT/data" audio
    else
        log_info "使用 gzip 压缩..."
        tar -czf "$AUDIO_ARCHIVE" -C "$PROJECT_ROOT/data" audio
    fi
    
    local size=$(du -h "$AUDIO_ARCHIVE" | cut -f1)
    log_info "音频文件打包完成: $AUDIO_ARCHIVE ($size)"
}

# 传输到远程服务器
transfer() {
    log_title "传输文件到 ${REMOTE_HOST}"
    
    check_ssh
    
    # 创建远程目录
    log_info "创建远程目录..."
    ssh ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${REMOTE_DIR}/src/data ${REMOTE_DIR}/data/audio ${REMOTE_DIR}/docker-images"
    
    # 传输镜像
    log_info "传输Docker镜像..."
    scp "$LOCAL_IMAGES_DIR/wordcross-backend.tar.gz" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/docker-images/
    scp "$LOCAL_IMAGES_DIR/wordcross-frontend.tar.gz" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/docker-images/
    
    # 传输配置文件
    log_info "传输配置文件..."
    scp "$PROJECT_ROOT/docker-compose.yml" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/
    scp "$PROJECT_ROOT/deploy.sh" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/
    
    # 传输SSL相关文件
    if [ -f "$PROJECT_ROOT/docker-compose.prod.yml" ]; then
        scp "$PROJECT_ROOT/docker-compose.prod.yml" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/
    fi
    if [ -f "$PROJECT_ROOT/setup-ssl.sh" ]; then
        scp "$PROJECT_ROOT/setup-ssl.sh" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/
        ssh ${REMOTE_USER}@${REMOTE_HOST} "chmod +x ${REMOTE_DIR}/setup-ssl.sh"
    fi
    
    # 传输SSL配置文件到前端目录
    if [ -f "$PROJECT_ROOT/src/frontend/nginx.ssl.conf" ]; then
        ssh ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${REMOTE_DIR}/src/frontend"
        scp "$PROJECT_ROOT/src/frontend/nginx.ssl.conf" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/src/frontend/
        scp "$PROJECT_ROOT/src/frontend/nginx.init.conf" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/src/frontend/
        scp "$PROJECT_ROOT/src/frontend/Dockerfile.ssl" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/src/frontend/
    fi
    
    # 传输关卡数据
    log_info "传输关卡数据..."
    scp "$LOCAL_IMAGES_DIR/levels.tar.gz" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/
    
    # 远程解压关卡数据
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_DIR}
        mkdir -p src/data
        tar -xzf levels.tar.gz -C src/data
        rm -f levels.tar.gz
        echo '关卡数据解压完成'
    "
    
    log_info "文件传输完成 ✓"
}

# 传输音频文件（首次部署或更新音频时使用）
transfer_audio() {
    log_title "传输音频文件到 ${REMOTE_HOST}"
    
    check_ssh
    
    if [ ! -f "$AUDIO_ARCHIVE" ]; then
        log_error "音频包 $AUDIO_ARCHIVE 不存在"
        log_error "请先运行 ./deploy-prod.sh pack-audio"
        exit 1
    fi
    
    log_info "传输音频文件（约580MB，请耐心等待）..."
    scp "$AUDIO_ARCHIVE" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/
    
    # 远程解压
    log_info "远程解压音频文件..."
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_DIR}
        mkdir -p data
        if command -v pigz &> /dev/null; then
            tar -I pigz -xf wordcross-audio.tar.gz -C data
        else
            tar -xzf wordcross-audio.tar.gz -C data
        fi
        rm -f wordcross-audio.tar.gz
        echo '音频解压完成'
        find data/audio -name '*.mp3' | wc -l
    "
    
    log_info "音频文件传输完成 ✓"
}

# 远程加载镜像
load_remote() {
    log_info "在远程服务器加载镜像..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_DIR}
        echo '加载后端镜像...'
        gunzip -c docker-images/wordcross-backend.tar.gz | docker load
        echo '加载前端镜像...'
        gunzip -c docker-images/wordcross-frontend.tar.gz | docker load
        echo '清理tar包...'
        rm -f docker-images/wordcross-backend.tar.gz docker-images/wordcross-frontend.tar.gz
        echo '镜像加载完成:'
        docker images | grep wordcross
    "
}

# 远程启动服务
start_remote() {
    log_info "在远程服务器启动服务..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_DIR}
        
        # 停止旧容器
        docker compose down 2>/dev/null || true
        
        # 启动服务
        docker compose up -d
        
        # 等待启动
        sleep 5
        
        # 显示状态
        echo ''
        echo '服务状态:'
        docker ps | grep wordcross || echo '未找到运行中的容器'
    "
    
    log_info "服务已启动 ✓"
    echo ""
    echo "访问地址: http://${REMOTE_HOST}:${FRONTEND_PORT}"
}

# 远程停止服务
stop_remote() {
    log_info "停止远程服务..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_DIR}
        docker compose down
        echo '服务已停止'
    "
}

# 远程重启服务
restart_remote() {
    log_info "重启远程服务..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_DIR}
        docker compose restart
        sleep 3
        docker ps | grep wordcross
    "
    
    log_info "服务已重启 ✓"
}

# 查看远程状态
status_remote() {
    log_title "远程服务状态"
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        echo '容器状态:'
        docker ps -a | grep wordcross || echo '无运行中的容器'
        echo ''
        echo '镜像列表:'
        docker images | grep wordcross || echo '无相关镜像'
        echo ''
        echo '磁盘使用:'
        du -sh ${REMOTE_DIR}/data/audio 2>/dev/null || echo '音频目录未找到'
        du -sh ${REMOTE_DIR}/src/data/levels 2>/dev/null || echo '关卡目录未找到'
    "
}

# 查看远程日志
logs_remote() {
    local service=${1:-""}
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_DIR}
        docker compose logs --tail=100 -f $service
    "
}

# 完整部署（首次）
deploy_full() {
    log_title "完整部署到 ${REMOTE_HOST}"
    
    check_docker
    check_ssh
    
    build
    export_images
    pack_levels
    
    # 检查是否需要传输音频
    if [ ! -f "$AUDIO_ARCHIVE" ]; then
        log_warn "音频包不存在，正在打包..."
        pack_audio
    fi
    
    transfer
    
    # 检查远程是否有音频
    local remote_audio_count=$(ssh ${REMOTE_USER}@${REMOTE_HOST} "find ${REMOTE_DIR}/data/audio -name '*.mp3' 2>/dev/null | wc -l")
    if [ "$remote_audio_count" -lt 1000 ]; then
        log_info "远程音频文件不足，开始传输..."
        transfer_audio
    else
        log_info "远程已有 $remote_audio_count 个音频文件，跳过传输"
    fi
    
    load_remote
    start_remote
    
    log_title "部署完成"
    echo ""
    echo "访问地址: http://${REMOTE_HOST}:${FRONTEND_PORT}"
    echo ""
}

# 快速更新（代码更新，不含音频）
deploy_quick() {
    log_title "快速更新部署"
    
    check_docker
    check_ssh
    
    build
    export_images
    pack_levels
    transfer
    load_remote
    start_remote
    
    log_title "更新部署完成"
    echo ""
    echo "访问地址: http://${REMOTE_HOST}:${FRONTEND_PORT}"
    echo ""
}

# SSL初始化（首次获取证书）
init_ssl() {
    log_title "初始化SSL证书"
    
    check_ssh
    
    log_info "在远程服务器初始化SSL证书..."
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_DIR}
        
        if [ ! -f setup-ssl.sh ]; then
            echo '错误: setup-ssl.sh 不存在，请先运行 transfer'
            exit 1
        fi
        
        chmod +x setup-ssl.sh
        ./setup-ssl.sh init
    "
    
    log_info "SSL证书初始化完成 ✓"
}

# SSL版本启动
start_ssl() {
    log_info "在远程服务器启动SSL服务..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_DIR}
        
        # 检查证书是否存在
        if [ ! -f certbot/conf/live/superhe.art/fullchain.pem ]; then
            echo '错误: SSL证书不存在，请先运行 init-ssl'
            exit 1
        fi
        
        # 停止旧容器
        docker compose -f docker-compose.prod.yml down 2>/dev/null || true
        docker compose down 2>/dev/null || true
        
        # 启动SSL版服务
        docker compose -f docker-compose.prod.yml up -d
        
        # 等待启动
        sleep 5
        
        # 显示状态
        echo ''
        echo '服务状态:'
        docker ps | grep wordcross || echo '未找到运行中的容器'
    "
    
    log_info "SSL服务已启动 ✓"
    echo ""
    echo "访问地址:"
    echo "  HTTP:  http://${REMOTE_HOST}:${FRONTEND_PORT} (自动重定向)"
    echo "  HTTPS: https://${REMOTE_HOST}:${FRONTEND_PORT_SSL}"
}

# SSL完整部署
deploy_ssl() {
    log_title "SSL完整部署到 ${REMOTE_HOST}"
    
    check_docker
    check_ssh
    
    # 构建镜像
    build_ssl
    export_images
    pack_levels
    transfer
    
    # 检查远程是否有音频
    local remote_audio_count=$(ssh ${REMOTE_USER}@${REMOTE_HOST} "find ${REMOTE_DIR}/data/audio -name '*.mp3' 2>/dev/null | wc -l")
    if [ "$remote_audio_count" -lt 1000 ]; then
        log_info "远程音频文件不足，开始传输..."
        if [ ! -f "$AUDIO_ARCHIVE" ]; then
            pack_audio
        fi
        transfer_audio
    else
        log_info "远程已有 $remote_audio_count 个音频文件，跳过传输"
    fi
    
    load_remote
    
    # 检查SSL证书
    local cert_exists=$(ssh ${REMOTE_USER}@${REMOTE_HOST} "[ -f ${REMOTE_DIR}/certbot/conf/live/superhe.art/fullchain.pem ] && echo 'yes' || echo 'no'")
    
    if [ "$cert_exists" = "no" ]; then
        log_info "SSL证书不存在，开始初始化..."
        init_ssl
    fi
    
    start_ssl
    
    log_title "SSL部署完成"
    echo ""
    echo "访问地址:"
    echo "  HTTP:  http://${REMOTE_HOST}:${FRONTEND_PORT} (自动重定向)"
    echo "  HTTPS: https://${REMOTE_HOST}:${FRONTEND_PORT_SSL}"
    echo ""
}

# SSL快速更新
deploy_ssl_quick() {
    log_title "SSL快速更新部署"
    
    check_docker
    check_ssh
    
    build_ssl
    export_images
    pack_levels
    transfer
    load_remote
    start_ssl
    
    log_title "SSL更新部署完成"
    echo ""
    echo "访问地址:"
    echo "  HTTP:  http://${REMOTE_HOST}:${FRONTEND_PORT} (自动重定向)"
    echo "  HTTPS: https://${REMOTE_HOST}:${FRONTEND_PORT_SSL}"
    echo ""
}

# 证书续期
renew_ssl() {
    log_info "续期SSL证书..."
    
    check_ssh
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_DIR}
        ./setup-ssl.sh renew
    "
    
    log_info "证书续期完成 ✓"
}

# SSL证书状态
ssl_status() {
    log_info "查看SSL证书状态..."
    
    check_ssh
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_DIR}
        ./setup-ssl.sh status
    "
}

# 显示帮助
usage() {
    echo "我爱填单词 - 生产环境部署脚本"
    echo ""
    echo "使用方法: $0 [命令]"
    echo ""
    echo "本地命令:"
    echo "  build        构建Docker镜像（HTTP版）"
    echo "  build-ssl    构建Docker镜像（HTTPS版）"
    echo "  export       导出镜像为tar包"
    echo "  pack-levels  打包关卡数据"
    echo "  pack-audio   打包音频文件"
    echo ""
    echo "传输命令:"
    echo "  transfer       传输镜像和关卡数据到远程"
    echo "  transfer-audio 传输音频文件到远程（首次需要）"
    echo ""
    echo "远程命令:"
    echo "  load         远程加载镜像"
    echo "  start        远程启动服务（HTTP）"
    echo "  stop         远程停止服务"
    echo "  restart      远程重启服务"
    echo "  status       查看远程状态"
    echo "  logs         查看远程日志（可选: frontend/backend）"
    echo ""
    echo "SSL命令:"
    echo "  init-ssl     初始化SSL证书（首次需要）"
    echo "  start-ssl    启动SSL服务"
    echo "  renew-ssl    续期SSL证书"
    echo "  ssl-status   查看SSL证书状态"
    echo ""
    echo "一键部署:"
    echo "  all          完整部署（HTTP，构建+传输+启动）"
    echo "  quick        快速更新（HTTP，构建+传输+启动）"
    echo "  ssl          完整SSL部署（HTTPS，含证书初始化）"
    echo "  ssl-quick    快速SSL更新（HTTPS，不初始化证书）"
    echo ""
    echo "配置:"
    echo "  目标服务器: ${REMOTE_USER}@${REMOTE_HOST}"
    echo "  远程目录:   ${REMOTE_DIR}"
    echo "  HTTP端口:   ${FRONTEND_PORT}"
    echo "  HTTPS端口:  ${FRONTEND_PORT_SSL}"
    echo ""
    echo "示例:"
    echo "  $0 all            # 完整HTTP部署（首次）"
    echo "  $0 quick          # 快速HTTP更新（日常）"
    echo "  $0 ssl            # 完整SSL部署（首次HTTPS）"
    echo "  $0 ssl-quick      # 快速SSL更新（日常HTTPS）"
    echo "  $0 logs backend   # 查看后端日志"
}

# 主函数
main() {
    case "${1:-}" in
        build)
            build
            ;;
        build-ssl)
            build_ssl
            ;;
        export)
            export_images
            ;;
        pack-levels)
            pack_levels
            ;;
        pack-audio)
            pack_audio
            ;;
        transfer)
            check_ssh
            transfer
            ;;
        transfer-audio)
            check_ssh
            transfer_audio
            ;;
        load)
            check_ssh
            load_remote
            ;;
        start)
            check_ssh
            start_remote
            ;;
        stop)
            check_ssh
            stop_remote
            ;;
        restart)
            check_ssh
            restart_remote
            ;;
        status)
            check_ssh
            status_remote
            ;;
        logs)
            check_ssh
            logs_remote "${2:-}"
            ;;
        # SSL 相关命令
        init-ssl)
            init_ssl
            ;;
        start-ssl)
            check_ssh
            start_ssl
            ;;
        renew-ssl)
            renew_ssl
            ;;
        ssl-status)
            ssl_status
            ;;
        # 一键部署
        all)
            deploy_full
            ;;
        quick)
            deploy_quick
            ;;
        ssl)
            deploy_ssl
            ;;
        ssl-quick)
            deploy_ssl_quick
            ;;
        *)
            usage
            ;;
    esac
}

main "$@"
