#!/bin/bash
# 项目启动脚本 - 由 SuperTeam 自动生成
# 项目: 我爱填单词 (ID: 2)
# 端口: 前端=10010, 后端=10012
# 此脚本调用 deploy-dev.sh 进行开发环境部署

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "启动项目: 我爱填单词 (开发环境)"
echo "项目目录: $PROJECT_DIR"
echo "前端端口: 10010"
echo "后端端口: 10012"
echo "=========================================="

# 调用 deploy-dev.sh 启动开发环境
cd "$PROJECT_DIR"

if [ -f "deploy-dev.sh" ]; then
    echo "[调度] 调用 deploy-dev.sh start"
    ./deploy-dev.sh start
else
    echo "[错误] deploy-dev.sh 不存在"
    exit 1
fi

echo "=========================================="
echo "启动完成"
echo "=========================================="
