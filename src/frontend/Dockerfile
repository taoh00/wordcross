# 我爱填单词 - 前端 Docker 镜像 (极小化)
# 使用多阶段构建：Node构建 + Nginx运行

# ============ 构建阶段 ============
FROM node:20-alpine as builder

WORKDIR /build

# 设置npm镜像源
RUN npm config set registry https://registry.npmmirror.com

# 复制package文件
COPY package*.json ./

# 安装依赖并清理缓存
RUN npm ci && npm cache clean --force

# 复制配置文件
COPY index.html ./
COPY vite.config.js ./
COPY postcss.config.js ./
COPY tailwind.config.js ./

# 复制源码
COPY src ./src

# 复制public目录（包含关卡数据）
COPY public ./public

# 构建并清理
RUN npm run build && rm -rf node_modules

# ============ 运行阶段 ============
FROM nginx:1.27-alpine-slim

LABEL maintainer="WordCross Team"
LABEL description="我爱填单词 - 前端服务"
LABEL version="1.0.0"

# 删除默认配置并复制自定义配置
RUN rm -rf /etc/nginx/conf.d/default.conf /var/cache/nginx/*

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/wordcross.conf

# 从构建阶段复制静态文件
COPY --from=builder /build/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
