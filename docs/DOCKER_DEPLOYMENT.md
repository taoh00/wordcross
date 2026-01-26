# 我爱填单词 - Docker 部署指南

## 架构说明

应用采用前后端分离的 Docker 部署架构：

```
┌─────────────────────────────────────────────────────────────┐
│                         用户浏览器                            │
└───────────────────────────┬─────────────────────────────────┘
                            │ :10010
┌───────────────────────────▼─────────────────────────────────┐
│                   前端容器 (nginx:alpine)                     │
│  - 静态文件服务 (Vue.js 构建产物)                              │
│  - API 反向代理 (/api/* → backend:10012)                     │
│  - WebSocket 代理 (/ws/* → backend:10012)                    │
│  - Gzip 压缩                                                 │
└───────────────────────────┬─────────────────────────────────┘
                            │ :10012 (内部网络)
┌───────────────────────────▼─────────────────────────────────┐
│                  后端容器 (python:3.11-slim)                  │
│  - FastAPI 应用                                              │
│  - 游戏逻辑 API                                              │
│  - 排行榜系统                                                │
│  - SQLite 数据库                                             │
└─────────────────────────────────────────────────────────────┘
```

## 镜像规格

| 镜像 | 基础镜像 | 预估大小 | 说明 |
|------|---------|---------|------|
| 前端 | nginx:1.25-alpine | ~25MB | 仅包含静态文件和nginx配置 |
| 后端 | python:3.11-slim | ~150MB | Python运行时 + FastAPI依赖 |

## 快速部署

### 使用部署脚本

```bash
# 构建镜像
./deploy.sh build

# 启动服务
./deploy.sh start

# 查看状态
./deploy.sh status

# 查看日志
./deploy.sh logs

# 停止服务
./deploy.sh stop
```

### 手动部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 访问地址

- **前端界面**: http://localhost:10010
- **API 接口**: http://localhost:10010/api/
- **健康检查**: http://localhost:10010/api/

## 目录结构

```
project/
├── docker-compose.yml          # Docker Compose 配置
├── deploy.sh                   # 部署脚本
├── .dockerignore               # Docker 构建忽略文件
├── src/
│   ├── backend/
│   │   ├── Dockerfile.prod     # 后端 Dockerfile
│   │   ├── requirements.prod.txt # 生产环境依赖
│   │   └── *.py                # 后端代码
│   ├── frontend/
│   │   ├── Dockerfile          # 前端 Dockerfile
│   │   ├── nginx.conf          # Nginx 配置
│   │   └── src/                # 前端源码
│   └── data/                   # 数据目录 (volume挂载)
│       ├── vocabulary/         # 词库文件
│       ├── levels/             # 关卡数据
│       └── wordcross.db        # SQLite数据库
└── data/
    └── audio/                  # 音频文件 (只读挂载)
```

## 数据持久化

通过 Docker Volume 挂载实现数据持久化：

- `./src/data` → `/app/data` (读写): 关卡数据、词库、数据库
- `./data/audio` → `/app/audio` (只读): 音频文件

## 环境变量

后端支持以下环境变量配置：

| 变量名 | 默认值 | 说明 |
|-------|--------|------|
| WORDCROSS_DATA_DIR | /app/data | 数据目录路径 |
| WORDCROSS_AUDIO_DIR | /app/audio | 音频目录路径 |
| TZ | Asia/Shanghai | 时区设置 |

## 生产环境优化

### 1. 使用外部数据库

如需更高性能，可将 SQLite 替换为 PostgreSQL：

```yaml
# docker-compose.yml 添加
services:
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: wordcross
      POSTGRES_USER: wordcross
      POSTGRES_PASSWORD: your_password
```

### 2. 添加 Redis 缓存

```yaml
services:
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
```

### 3. 使用 HTTPS

推荐在前端 nginx 容器前再加一层反向代理（如 Traefik/Caddy）处理 HTTPS。

### 4. 健康检查

两个容器都配置了健康检查：
- 前端: 每30秒检查 `/` 是否可访问
- 后端: 每30秒检查 `/api/` 是否可访问

## 故障排查

### 后端无法启动

```bash
# 查看后端日志
docker-compose logs backend

# 进入容器检查
docker exec -it wordcross-backend /bin/sh
```

### 前端无法连接后端

1. 检查后端健康状态: `docker-compose ps`
2. 检查 nginx 配置: `docker exec wordcross-frontend cat /etc/nginx/conf.d/wordcross.conf`
3. 检查网络: `docker network ls`

### 数据库迁移

如需升级数据库结构：

```bash
# 备份数据库
cp src/data/wordcross.db src/data/wordcross.db.bak

# 进入后端容器
docker exec -it wordcross-backend /bin/sh

# 执行迁移
python -c "import database; database.init_database()"
```

## 镜像导出

用于离线部署：

```bash
# 导出镜像
docker save wordcross-frontend wordcross-backend | gzip > wordcross-images.tar.gz

# 导入镜像
docker load < wordcross-images.tar.gz
```
