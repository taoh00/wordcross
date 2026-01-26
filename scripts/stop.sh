#!/bin/bash
# 项目停止脚本 - 由 SuperTeam 自动生成
# 项目: 我爱填单词 (ID: 2)
# 此脚本调用 deploy-dev.sh 停止开发环境

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "停止项目: 我爱填单词 (开发环境)"
echo "=========================================="

# 调用 deploy-dev.sh 停止开发环境
cd "$PROJECT_DIR"

if [ -f "deploy-dev.sh" ]; then
    echo "[调度] 调用 deploy-dev.sh stop"
    ./deploy-dev.sh stop
else
    # 回退方案：直接释放端口
    echo "[警告] deploy-dev.sh 不存在，直接释放端口"
    fuser -k 10010/tcp 2>/dev/null || true
    fuser -k 10012/tcp 2>/dev/null || true
fi

echo "=========================================="
echo "停止完成"
echo "=========================================="
