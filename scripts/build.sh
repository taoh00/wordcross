#!/bin/bash
# 项目编译脚本 - 由 SuperTeam 自动生成
# 项目: 我爱填单词 (ID: 2)
# 请根据项目实际情况修改此脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=========================================="
echo "编译项目: 我爱填单词"
echo "项目目录: $PROJECT_DIR"
echo "=========================================="

# 检测并执行编译
# 前端编译（自动检测项目类型）
if [ -f "package.json" ]; then
    echo "[前端] 检测到 Node.js 项目"
    npm install --registry=https://registry.npmmirror.com
    npm run build 2>/dev/null || echo "[前端] 无 build 命令或编译跳过"
elif [ -f "index.html" ]; then
    echo "[前端] 检测到静态 HTML 项目，无需编译"
fi

# 后端编译（自动检测项目类型）
if [ -f "requirements.txt" ]; then
    echo "[后端] 检测到 Python 项目"
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || true
elif [ -f "go.mod" ]; then
    echo "[后端] 检测到 Go 项目"
    go build -o app . 2>/dev/null || true
fi

echo "=========================================="
echo "编译完成"
echo "=========================================="
