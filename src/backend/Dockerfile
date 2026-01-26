# 我爱填单词 - 后端 Docker 镜像
# 使用多阶段构建减小镜像大小

# ============ 构建阶段 ============
FROM python:3.11-slim as builder

WORKDIR /build

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装依赖
COPY requirements.prod.txt .
RUN pip install --no-cache-dir --prefix=/install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r requirements.prod.txt

# ============ 运行阶段 ============
FROM python:3.11-slim

LABEL maintainer="WordCross Team"
LABEL description="我爱填单词 - 后端服务"
LABEL version="1.0.0"

WORKDIR /app

# 从构建阶段复制安装的包
COPY --from=builder /install /usr/local

# 复制应用代码
COPY *.py ./

# 复制数据目录 (关卡数据、词汇等)
COPY ../data ./data

# 创建非root用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# 暴露端口
EXPOSE 10012

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:10012/')" || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10012"]
