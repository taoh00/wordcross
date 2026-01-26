# 发布应用到 SuperTeam

将本项目发布到 SuperTeam 应用平台，让用户可以在 App 的「应用」页面体验。

## 环境说明

| 环境 | 地址 | 说明 |
|------|------|------|
| 开发环境 | http://43.153.19.112:10010 | 本地开发服务器 |
| 生产环境 | http://superhe.art:10010 | 线上部署服务器 |

## 发布命令

在项目目录下执行以下命令：

### 开发环境发布

```bash
# 仅发布前端（静态网页）
python3 /root/SuperTeam/superteam/apps/backend/scripts/internal_publish.py \
    --project-id 2 \
    --frontend-port 10010 \
    --version "1.0.0"

# 同时发布前端和后端
python3 /root/SuperTeam/superteam/apps/backend/scripts/internal_publish.py \
    --project-id 2 \
    --frontend-port 10010 \
    --backend-port 10012 \
    --version "1.0.0"
```

### 生产环境发布

```bash
# 发布到生产环境（superhe.art）
python3 /root/SuperTeam/superteam/apps/backend/scripts/internal_publish.py \
    --project-id 2 \
    --environment production \
    --frontend-url "http://superhe.art:10010" \
    --version "1.0.0"
```

## 发布前检查

1. **确保服务正在运行**：发布前请确认前端/后端服务已在对应端口启动
   ```bash
   # 检查端口是否在监听
   ss -tlnp | grep 10010
   ss -tlnp | grep 10012
   ```

2. **使用 nohup 保持服务运行**：确保服务在后台持续运行
   ```bash
   # 静态网页示例
   cd /path/to/dist && nohup python3 -m http.server 10010 > /dev/null 2>&1 &
   
   # 后端 API 示例
   nohup uvicorn main:app --host 0.0.0.0 --port 10012 > /dev/null 2>&1 &
   ```

## 发布后验证

```bash
# 查看项目应用列表
python3 /root/SuperTeam/superteam/apps/backend/scripts/internal_publish.py \
    --project-id 2 --list
```

## 端口配置

| 用途 | 端口号 |
|------|--------|
| 前端端口 | `10010` |
| 后端端口 | `10012` |

## 更新应用

每次更新后重新执行发布命令，记得更新版本号：

```bash
python3 /root/SuperTeam/superteam/apps/backend/scripts/internal_publish.py \
    --project-id 2 \
    --frontend-port 10010 \
    --version "1.0.1"  # 更新版本号
```

## 访问应用

发布成功后，应用可通过以下方式访问：
- 在 SuperTeam App 的「应用」页面
- 开发环境直接访问：http://43.153.19.112:10010
- 生产环境直接访问：http://superhe.art:10010

## 部署脚本

| 脚本 | 用途 | 说明 |
|------|------|------|
| `deploy-dev.sh` | 开发环境部署 | 本地启动 Node.js + Python |
| `deploy-prod.sh` | 生产环境部署 | Docker 部署到 superhe.art |
| `scripts/start.sh` | SuperTeam 调度 | 调用 deploy-dev.sh |
| `scripts/stop.sh` | SuperTeam 调度 | 调用 deploy-dev.sh |

### 开发环境启动

```bash
# 方式1：使用 deploy-dev.sh
./deploy-dev.sh start

# 方式2：使用 SuperTeam 调度脚本
./scripts/start.sh
```

### 生产环境部署

```bash
# 完整部署（首次）
./deploy-prod.sh all

# 快速更新（日常）
./deploy-prod.sh quick
```
