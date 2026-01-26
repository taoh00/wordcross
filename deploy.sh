#!/bin/bash
# 我爱填单词 - Docker 部署脚本
# 使用: ./deploy.sh [build|start|stop|restart|logs|clean|pack-audio|unpack-audio|save|load]

set -e

PROJECT_NAME="wordcross"
COMPOSE_FILE="docker-compose.yml"
AUDIO_DIR="data/audio"
AUDIO_ARCHIVE="wordcross-audio.tar.gz"
IMAGES_DIR="docker-images"
FRONTEND_IMAGE="wordcross-frontend.tar.gz"
BACKEND_IMAGE="wordcross-backend.tar.gz"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi
}

# 同步关卡数据到前端public目录
sync_levels() {
    log_info "同步关卡数据到前端..."
    
    local SOURCE_DIR="src/data/levels"
    local TARGET_DIR="src/frontend/public/data/levels"
    local SUMMARY_FILE="src/data/levels_summary.json"
    local TARGET_SUMMARY="src/frontend/public/data/levels_summary.json"
    
    # 创建目标目录
    mkdir -p "$TARGET_DIR"
    mkdir -p "$(dirname $TARGET_SUMMARY)"
    
    # 复制关卡数据
    if [ -d "$SOURCE_DIR" ]; then
        cp -r "$SOURCE_DIR"/* "$TARGET_DIR/"
        log_info "关卡数据已复制到 $TARGET_DIR"
    else
        log_warn "源目录 $SOURCE_DIR 不存在，跳过关卡数据同步"
    fi
    
    # 复制汇总文件
    if [ -f "$SUMMARY_FILE" ]; then
        cp "$SUMMARY_FILE" "$TARGET_SUMMARY"
        log_info "汇总文件已复制到 $TARGET_SUMMARY"
    fi
}

# 构建镜像
build() {
    log_info "开始构建镜像..."
    
    # 先同步关卡数据到前端
    sync_levels
    
    # 使用 docker compose (v2) 或 docker-compose (v1)
    if docker compose version &> /dev/null; then
        docker compose -f $COMPOSE_FILE build --no-cache
    else
        docker-compose -f $COMPOSE_FILE build --no-cache
    fi
    
    log_info "镜像构建完成"
    
    # 显示镜像大小
    log_info "镜像大小:"
    docker images | grep $PROJECT_NAME || true
}

# 启动服务
start() {
    log_info "启动服务..."
    
    if docker compose version &> /dev/null; then
        docker compose -f $COMPOSE_FILE up -d
    else
        docker-compose -f $COMPOSE_FILE up -d
    fi
    
    log_info "服务启动完成"
    log_info "前端地址: http://localhost:10010"
    log_info "后端API: http://localhost:10010/api/"
    
    # 显示容器状态
    docker ps | grep $PROJECT_NAME || true
}

# 停止服务
stop() {
    log_info "停止服务..."
    
    if docker compose version &> /dev/null; then
        docker compose -f $COMPOSE_FILE down
    else
        docker-compose -f $COMPOSE_FILE down
    fi
    
    log_info "服务已停止"
}

# 重启服务
restart() {
    stop
    start
}

# 查看日志
logs() {
    local service=${1:-""}
    
    if docker compose version &> /dev/null; then
        docker compose -f $COMPOSE_FILE logs -f $service
    else
        docker-compose -f $COMPOSE_FILE logs -f $service
    fi
}

# 清理（删除容器和镜像）
clean() {
    log_warn "将删除所有容器和镜像，确认继续? [y/N]"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        stop
        log_info "删除镜像..."
        docker rmi ${PROJECT_NAME}-frontend ${PROJECT_NAME}-backend 2>/dev/null || true
        log_info "清理完成"
    else
        log_info "取消清理"
    fi
}

# 显示状态
status() {
    log_info "容器状态:"
    docker ps -a | grep $PROJECT_NAME || echo "无运行中的容器"
    
    echo ""
    log_info "镜像列表:"
    docker images | grep $PROJECT_NAME || echo "无相关镜像"
}

# 打包音频文件
pack_audio() {
    if [ ! -d "$AUDIO_DIR" ]; then
        log_error "音频目录 $AUDIO_DIR 不存在"
        exit 1
    fi
    
    log_info "开始打包音频文件..."
    log_info "源目录: $AUDIO_DIR"
    
    # 统计文件数量
    local file_count=$(find "$AUDIO_DIR" -name "*.mp3" | wc -l)
    log_info "音频文件数量: $file_count"
    
    # 打包 (使用pigz多线程压缩加速，如果没有则用gzip)
    if command -v pigz &> /dev/null; then
        log_info "使用 pigz 多线程压缩..."
        tar -I pigz -cf "$AUDIO_ARCHIVE" -C data audio
    else
        log_info "使用 gzip 压缩..."
        tar -czf "$AUDIO_ARCHIVE" -C data audio
    fi
    
    local size=$(du -h "$AUDIO_ARCHIVE" | cut -f1)
    log_info "打包完成: $AUDIO_ARCHIVE ($size)"
    log_info "可将此文件传输到目标服务器后使用 ./deploy.sh unpack-audio 解压"
}

# 解压音频文件
unpack_audio() {
    if [ ! -f "$AUDIO_ARCHIVE" ]; then
        log_error "音频包 $AUDIO_ARCHIVE 不存在"
        log_error "请先将音频包文件放到当前目录"
        exit 1
    fi
    
    log_info "开始解压音频文件..."
    
    # 创建目标目录
    mkdir -p data
    
    # 解压 (自动检测pigz)
    if command -v pigz &> /dev/null; then
        log_info "使用 pigz 多线程解压..."
        tar -I pigz -xf "$AUDIO_ARCHIVE" -C data
    else
        log_info "使用 gzip 解压..."
        tar -xzf "$AUDIO_ARCHIVE" -C data
    fi
    
    # 统计解压后的文件
    local file_count=$(find "$AUDIO_DIR" -name "*.mp3" 2>/dev/null | wc -l)
    log_info "解压完成: $file_count 个音频文件"
    log_info "音频目录: $AUDIO_DIR"
}

# 保存Docker镜像到文件（用于离线传输）
save_images() {
    log_info "保存Docker镜像到文件..."
    
    # 创建输出目录
    mkdir -p "$IMAGES_DIR"
    
    # 检查镜像是否存在
    if ! docker images wordcross-frontend:latest --format "{{.Repository}}" | grep -q "wordcross-frontend"; then
        log_error "前端镜像不存在，请先运行 ./deploy.sh build"
        exit 1
    fi
    
    if ! docker images wordcross-backend:latest --format "{{.Repository}}" | grep -q "wordcross-backend"; then
        log_error "后端镜像不存在，请先运行 ./deploy.sh build"
        exit 1
    fi
    
    # 保存前端镜像
    log_info "保存前端镜像..."
    docker save wordcross-frontend:latest | gzip > "$IMAGES_DIR/$FRONTEND_IMAGE"
    local frontend_size=$(du -h "$IMAGES_DIR/$FRONTEND_IMAGE" | cut -f1)
    log_info "前端镜像已保存: $IMAGES_DIR/$FRONTEND_IMAGE ($frontend_size)"
    
    # 保存后端镜像
    log_info "保存后端镜像..."
    docker save wordcross-backend:latest | gzip > "$IMAGES_DIR/$BACKEND_IMAGE"
    local backend_size=$(du -h "$IMAGES_DIR/$BACKEND_IMAGE" | cut -f1)
    log_info "后端镜像已保存: $IMAGES_DIR/$BACKEND_IMAGE ($backend_size)"
    
    # 总结
    log_info "========================================="
    log_info "镜像保存完成！"
    log_info "文件位置: $IMAGES_DIR/"
    ls -lh "$IMAGES_DIR/"
    echo ""
    log_info "部署到服务器需要的文件:"
    echo "  1. $IMAGES_DIR/$FRONTEND_IMAGE (代码+关卡数据)"
    echo "  2. $IMAGES_DIR/$BACKEND_IMAGE (后端代码)"
    echo "  3. $AUDIO_ARCHIVE (音频文件，首次需要)"
    echo "  4. docker-compose.yml (编排配置)"
    echo "  5. deploy.sh (部署脚本)"
}

# 加载Docker镜像（从文件加载）
load_images() {
    log_info "从文件加载Docker镜像..."
    
    # 检查文件是否存在
    if [ ! -f "$IMAGES_DIR/$FRONTEND_IMAGE" ]; then
        log_error "前端镜像文件不存在: $IMAGES_DIR/$FRONTEND_IMAGE"
        exit 1
    fi
    
    if [ ! -f "$IMAGES_DIR/$BACKEND_IMAGE" ]; then
        log_error "后端镜像文件不存在: $IMAGES_DIR/$BACKEND_IMAGE"
        exit 1
    fi
    
    # 加载前端镜像
    log_info "加载前端镜像..."
    gunzip -c "$IMAGES_DIR/$FRONTEND_IMAGE" | docker load
    
    # 加载后端镜像
    log_info "加载后端镜像..."
    gunzip -c "$IMAGES_DIR/$BACKEND_IMAGE" | docker load
    
    log_info "镜像加载完成！"
    docker images | grep $PROJECT_NAME || true
}

# 显示帮助
usage() {
    echo "使用方法: $0 [命令]"
    echo ""
    echo "基础命令:"
    echo "  build        构建Docker镜像（代码+关卡数据，约125MB）"
    echo "  start        启动服务（端口10010）"
    echo "  stop         停止服务"
    echo "  restart      重启服务"
    echo "  logs         查看日志 (可选参数: frontend/backend)"
    echo "  status       查看状态"
    echo "  clean        清理容器和镜像"
    echo ""
    echo "打包命令（用于离线部署）:"
    echo "  save         保存镜像到 $IMAGES_DIR/ (用于传输到服务器)"
    echo "  load         从 $IMAGES_DIR/ 加载镜像"
    echo "  pack-audio   打包音频文件为 $AUDIO_ARCHIVE"
    echo "  unpack-audio 解压音频文件到 $AUDIO_DIR"
    echo ""
    echo "端口分配:"
    echo "  前端(nginx):  10010 (避免与80端口冲突)"
    echo "  后端(fastapi): 内部10012 (仅容器网络访问)"
    echo ""
    echo "========================================="
    echo "首次部署流程（离线传输）:"
    echo "========================================="
    echo "  开发机执行:"
    echo "    1. ./deploy.sh build      # 构建镜像"
    echo "    2. ./deploy.sh save       # 保存镜像到文件"
    echo "    3. ./deploy.sh pack-audio # 打包音频（首次需要）"
    echo ""
    echo "  传输以下文件到服务器:"
    echo "    - $IMAGES_DIR/*.tar.gz    # 镜像文件(约125MB)"
    echo "    - $AUDIO_ARCHIVE          # 音频文件(约350MB，首次)"
    echo "    - docker-compose.yml"
    echo "    - deploy.sh"
    echo ""
    echo "  服务器执行:"
    echo "    1. ./deploy.sh load        # 加载镜像"
    echo "    2. ./deploy.sh unpack-audio # 解压音频（首次）"
    echo "    3. ./deploy.sh start       # 启动服务"
    echo ""
    echo "========================================="
    echo "更新代码（无需重传音频）:"
    echo "========================================="
    echo "  开发机: ./deploy.sh build && ./deploy.sh save"
    echo "  传输 $IMAGES_DIR/*.tar.gz 到服务器"
    echo "  服务器: ./deploy.sh load && ./deploy.sh restart"
    echo ""
    echo "示例:"
    echo "  $0 build          # 构建镜像"
    echo "  $0 save           # 保存镜像到文件"
    echo "  $0 start          # 启动服务"
    echo "  $0 logs backend   # 查看后端日志"
}

# 主函数
main() {
    case "${1:-}" in
        build)
            check_docker
            build
            ;;
        start)
            check_docker
            start
            ;;
        stop)
            check_docker
            stop
            ;;
        restart)
            check_docker
            restart
            ;;
        logs)
            check_docker
            logs "${2:-}"
            ;;
        status)
            check_docker
            status
            ;;
        clean)
            check_docker
            clean
            ;;
        save)
            check_docker
            save_images
            ;;
        load)
            check_docker
            load_images
            ;;
        pack-audio)
            pack_audio
            ;;
        unpack-audio)
            unpack_audio
            ;;
        *)
            usage
            ;;
    esac
}

main "$@"
