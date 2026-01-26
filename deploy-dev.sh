#!/bin/bash
# 我爱填单词 - 开发环境部署脚本
# 使用: ./deploy-dev.sh [start|stop|restart|logs|status]

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/src/frontend"
BACKEND_DIR="$PROJECT_ROOT/src/backend"

# 端口配置
FRONTEND_PORT=10010
BACKEND_PORT=10012

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

# 检查依赖
check_deps() {
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装，请先安装 Node.js"
        exit 1
    fi
    
    # 检查 Python
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        log_error "Python 未安装，请先安装 Python 3"
        exit 1
    fi
    
    log_info "依赖检查通过 ✓"
}

# 安装前端依赖
install_frontend_deps() {
    log_info "检查前端依赖..."
    
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        log_info "安装前端依赖..."
        cd "$FRONTEND_DIR"
        npm install --registry=https://registry.npmmirror.com
    else
        log_info "前端依赖已安装 ✓"
    fi
}

# 安装后端依赖
install_backend_deps() {
    log_info "检查后端依赖..."
    
    cd "$BACKEND_DIR"
    
    # 检查是否需要安装依赖（通过检查关键模块）
    if ! python3 -c "import fastapi" 2>/dev/null; then
        log_info "安装后端依赖..."
        pip3 install -r requirements.prod.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    else
        log_info "后端依赖已安装 ✓"
    fi
}

# 同步关卡数据到前端
sync_levels() {
    log_info "同步关卡数据到前端..."
    
    local SOURCE_DIR="$PROJECT_ROOT/src/data/levels"
    local TARGET_DIR="$FRONTEND_DIR/public/data/levels"
    local SUMMARY_FILE="$PROJECT_ROOT/src/data/levels_summary.json"
    local TARGET_SUMMARY="$FRONTEND_DIR/public/data/levels_summary.json"
    
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

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -i:$port &>/dev/null; then
        return 0  # 被占用
    else
        return 1  # 未占用
    fi
}

# 获取进程PID
get_pid() {
    local port=$1
    lsof -ti:$port 2>/dev/null || echo ""
}

# 停止服务
stop_service() {
    local port=$1
    local name=$2
    
    local pid=$(get_pid $port)
    if [ -n "$pid" ]; then
        log_info "停止 $name (PID: $pid, 端口: $port)..."
        kill $pid 2>/dev/null || true
        sleep 1
        # 强制停止
        kill -9 $pid 2>/dev/null || true
        log_info "$name 已停止 ✓"
    fi
}

# 启动后端
start_backend() {
    log_info "启动后端服务..."
    
    if check_port $BACKEND_PORT; then
        log_warn "后端端口 $BACKEND_PORT 已被占用，尝试停止..."
        stop_service $BACKEND_PORT "后端"
    fi
    
    cd "$BACKEND_DIR"
    nohup python3 main.py > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
    
    # 等待启动
    sleep 2
    
    if check_port $BACKEND_PORT; then
        log_info "后端服务启动成功 ✓ (http://localhost:$BACKEND_PORT)"
    else
        log_error "后端服务启动失败，查看日志: $PROJECT_ROOT/logs/backend.log"
        exit 1
    fi
}

# 启动前端
start_frontend() {
    log_info "启动前端开发服务器..."
    
    if check_port $FRONTEND_PORT; then
        log_warn "前端端口 $FRONTEND_PORT 已被占用，尝试停止..."
        stop_service $FRONTEND_PORT "前端"
    fi
    
    cd "$FRONTEND_DIR"
    nohup npm run dev > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
    
    # 等待启动
    sleep 3
    
    if check_port $FRONTEND_PORT; then
        log_info "前端服务启动成功 ✓ (http://localhost:$FRONTEND_PORT)"
    else
        log_error "前端服务启动失败，查看日志: $PROJECT_ROOT/logs/frontend.log"
        exit 1
    fi
}

# 启动所有服务
start() {
    log_title "启动开发环境"
    
    check_deps
    
    # 创建日志目录
    mkdir -p "$PROJECT_ROOT/logs"
    
    install_frontend_deps
    install_backend_deps
    sync_levels
    
    start_backend
    start_frontend
    
    echo ""
    log_title "开发环境已启动"
    echo ""
    echo "  前端: http://localhost:$FRONTEND_PORT"
    echo "  后端: http://localhost:$BACKEND_PORT"
    echo ""
    echo "  日志目录: $PROJECT_ROOT/logs/"
    echo "  停止服务: ./deploy-dev.sh stop"
    echo ""
}

# 停止所有服务
stop() {
    log_title "停止开发环境"
    
    stop_service $FRONTEND_PORT "前端"
    stop_service $BACKEND_PORT "后端"
    
    log_info "所有服务已停止"
}

# 重启服务
restart() {
    stop
    sleep 1
    start
}

# 查看状态
status() {
    log_title "开发环境状态"
    
    echo ""
    echo "前端 (端口 $FRONTEND_PORT):"
    if check_port $FRONTEND_PORT; then
        local pid=$(get_pid $FRONTEND_PORT)
        echo "  状态: 运行中 (PID: $pid)"
        echo "  地址: http://localhost:$FRONTEND_PORT"
    else
        echo "  状态: 未运行"
    fi
    
    echo ""
    echo "后端 (端口 $BACKEND_PORT):"
    if check_port $BACKEND_PORT; then
        local pid=$(get_pid $BACKEND_PORT)
        echo "  状态: 运行中 (PID: $pid)"
        echo "  地址: http://localhost:$BACKEND_PORT"
    else
        echo "  状态: 未运行"
    fi
    echo ""
}

# 查看日志
logs() {
    local service=${1:-"all"}
    
    if [ "$service" = "frontend" ]; then
        tail -f "$PROJECT_ROOT/logs/frontend.log"
    elif [ "$service" = "backend" ]; then
        tail -f "$PROJECT_ROOT/logs/backend.log"
    else
        # 同时查看两个日志
        tail -f "$PROJECT_ROOT/logs/frontend.log" "$PROJECT_ROOT/logs/backend.log"
    fi
}

# 显示帮助
usage() {
    echo "我爱填单词 - 开发环境部署脚本"
    echo ""
    echo "使用方法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start      启动开发环境（前端+后端）"
    echo "  stop       停止所有服务"
    echo "  restart    重启所有服务"
    echo "  status     查看服务状态"
    echo "  logs       查看日志（可选: frontend/backend）"
    echo ""
    echo "端口配置:"
    echo "  前端(Vite):   $FRONTEND_PORT"
    echo "  后端(FastAPI): $BACKEND_PORT"
    echo ""
    echo "示例:"
    echo "  $0 start          # 启动开发环境"
    echo "  $0 logs backend   # 查看后端日志"
    echo "  $0 status         # 查看服务状态"
}

# 主函数
main() {
    case "${1:-}" in
        start)
            start
            ;;
        stop)
            stop
            ;;
        restart)
            restart
            ;;
        status)
            status
            ;;
        logs)
            logs "${2:-}"
            ;;
        *)
            usage
            ;;
    esac
}

main "$@"
