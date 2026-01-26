#!/bin/bash
# 我爱填单词 - 远程部署脚本
# 使用: ./deploy_remote.sh [build|deploy|start|stop|all]

set -e

# ============ 配置 ============
PROJECT_NAME="wordcross"
REMOTE_HOST="superhe.art"
REMOTE_USER="root"
REMOTE_DIR="/opt/wordcross"
LOCAL_IMAGES_DIR="./docker-images"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 本地构建镜像
build_local() {
    log_info "开始本地构建镜像..."
    
    # 同步关卡数据
    log_info "同步关卡数据到前端..."
    mkdir -p src/frontend/public/data/levels
    cp -r src/data/levels/* src/frontend/public/data/levels/
    [ -f src/data/levels_summary.json ] && cp src/data/levels_summary.json src/frontend/public/data/
    
    # 构建镜像
    docker compose build --no-cache
    
    log_info "镜像构建完成"
    docker images | grep $PROJECT_NAME
}

# 导出镜像
export_images() {
    log_info "导出镜像为tar包..."
    
    mkdir -p $LOCAL_IMAGES_DIR
    
    docker save wordcross-backend:latest | gzip > $LOCAL_IMAGES_DIR/wordcross-backend.tar.gz
    docker save wordcross-frontend:latest | gzip > $LOCAL_IMAGES_DIR/wordcross-frontend.tar.gz
    
    log_info "镜像导出完成:"
    ls -lh $LOCAL_IMAGES_DIR/
}

# 传输到远程服务器
transfer_files() {
    log_info "传输文件到远程服务器 ${REMOTE_HOST}..."
    
    # 创建远程目录
    ssh ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${REMOTE_DIR}/src/data ${REMOTE_DIR}/data/audio"
    
    # 传输镜像
    log_info "传输镜像文件（约37MB）..."
    scp $LOCAL_IMAGES_DIR/wordcross-backend.tar.gz ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/
    scp $LOCAL_IMAGES_DIR/wordcross-frontend.tar.gz ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/
    
    # 传输 docker-compose 和部署脚本
    scp docker-compose.yml ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/
    scp deploy.sh ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/
    
    # 打包并传输关卡数据（比逐个文件传输快得多）
    log_info "打包关卡数据..."
    tar -czf $LOCAL_IMAGES_DIR/levels.tar.gz -C src/data levels levels_summary.json 2>/dev/null || \
    tar -czf $LOCAL_IMAGES_DIR/levels.tar.gz -C src/data levels
    
    log_info "传输关卡数据（打包后）..."
    scp $LOCAL_IMAGES_DIR/levels.tar.gz ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/
    
    # 远程解压
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_DIR}
        tar -xzf levels.tar.gz -C src/data
        rm -f levels.tar.gz
        echo '关卡数据解压完成'
    "
    
    # 传输音频文件（如果存在且非空）
    if [ -d "data/audio" ] && [ "$(ls -A data/audio 2>/dev/null)" ]; then
        log_info "打包并传输音频文件..."
        tar -czf $LOCAL_IMAGES_DIR/audio.tar.gz -C data audio
        scp $LOCAL_IMAGES_DIR/audio.tar.gz ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/
        ssh ${REMOTE_USER}@${REMOTE_HOST} "
            cd ${REMOTE_DIR}
            tar -xzf audio.tar.gz -C data
            rm -f audio.tar.gz
        "
    fi
    
    log_info "文件传输完成"
}

# 远程加载镜像
load_remote_images() {
    log_info "在远程服务器加载镜像..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_DIR}
        echo '加载后端镜像...'
        gunzip -c wordcross-backend.tar.gz | docker load
        echo '加载前端镜像...'
        gunzip -c wordcross-frontend.tar.gz | docker load
        echo '清理tar包...'
        rm -f wordcross-backend.tar.gz wordcross-frontend.tar.gz
        echo '镜像加载完成:'
        docker images | grep wordcross
    "
}

# 远程启动服务
start_remote() {
    log_info "在远程服务器启动服务..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_DIR}
        
        # 停止旧容器（如果存在）
        docker compose down 2>/dev/null || true
        
        # 启动服务
        docker compose up -d
        
        # 等待启动
        sleep 5
        
        # 显示状态
        echo '服务状态:'
        docker ps | grep wordcross
        
        echo ''
        echo '服务已启动！'
        echo '访问地址: http://superhe.art:10010'
    "
}

# 远程停止服务
stop_remote() {
    log_info "在远程服务器停止服务..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_DIR}
        docker compose down
        echo '服务已停止'
    "
}

# 查看远程日志
logs_remote() {
    log_info "查看远程服务日志..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_DIR}
        docker compose logs --tail=100 -f
    "
}

# 远程状态
status_remote() {
    log_info "查看远程服务状态..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        echo '容器状态:'
        docker ps -a | grep wordcross || echo '无运行中的容器'
        echo ''
        echo '镜像列表:'
        docker images | grep wordcross || echo '无相关镜像'
    "
}

# 完整部署流程
deploy_all() {
    log_info "开始完整部署流程..."
    
    build_local
    export_images
    transfer_files
    load_remote_images
    start_remote
    
    log_info "=========================================="
    log_info "部署完成！"
    log_info "访问地址: http://superhe.art:10010"
    log_info "=========================================="
}

# 显示帮助
usage() {
    echo "使用方法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  build      本地构建Docker镜像"
    echo "  export     导出镜像为tar包"
    echo "  transfer   传输文件到远程服务器"
    echo "  load       远程加载镜像"
    echo "  start      远程启动服务"
    echo "  stop       远程停止服务"
    echo "  logs       查看远程日志"
    echo "  status     查看远程状态"
    echo "  all        完整部署（构建+传输+启动）"
    echo ""
    echo "示例:"
    echo "  $0 all       # 完整部署"
    echo "  $0 start     # 仅启动远程服务"
    echo "  $0 status    # 查看远程状态"
}

# 主函数
main() {
    case "${1:-}" in
        build)
            build_local
            ;;
        export)
            export_images
            ;;
        transfer)
            transfer_files
            ;;
        load)
            load_remote_images
            ;;
        start)
            start_remote
            ;;
        stop)
            stop_remote
            ;;
        logs)
            logs_remote
            ;;
        status)
            status_remote
            ;;
        all)
            deploy_all
            ;;
        *)
            usage
            ;;
    esac
}

main "$@"
