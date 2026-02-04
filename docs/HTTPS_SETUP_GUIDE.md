# 填单词 - HTTPS 证书配置指南

## 概述

本文档介绍如何为「填单词」配置 HTTPS 证书，使用 Let's Encrypt 免费证书服务。

**重要**：微信小程序和 iOS App 均要求 HTTPS 连接，必须完成此配置才能正常使用。

---

## 一、前提条件

### 1.1 域名解析

确保域名 `superhe.art` 已正确解析到服务器 IP：

```bash
# 检查 DNS 解析
nslookup superhe.art

# 或使用 dig
dig superhe.art
```

### 1.2 端口开放

确保服务器防火墙开放以下端口：

| 端口 | 用途 |
|------|------|
| 10010 | HTTP 服务（证书验证 + 重定向） |
| 10443 | HTTPS 服务 |

```bash
# 检查端口是否开放
sudo firewall-cmd --list-ports

# 开放端口（如需要）
sudo firewall-cmd --permanent --add-port=10010/tcp
sudo firewall-cmd --permanent --add-port=10443/tcp
sudo firewall-cmd --reload
```

### 1.3 服务器环境

- Docker 已安装
- Docker Compose 已安装
- 项目已部署到 `/opt/wordcross`

---

## 二、文件结构

```
/opt/wordcross/
├── docker-compose.prod.yml    # 生产环境编排（支持SSL）
├── setup-ssl.sh               # SSL 配置脚本
├── certbot/                   # 证书目录（自动创建）
│   ├── conf/                  # Let's Encrypt 配置
│   │   └── live/
│   │       └── superhe.art/
│   │           ├── fullchain.pem   # 完整证书链
│   │           └── privkey.pem     # 私钥
│   └── www/                   # ACME 验证目录
└── src/frontend/
    ├── nginx.ssl.conf         # SSL Nginx 配置
    ├── nginx.init.conf        # 初始化配置（仅HTTP）
    └── Dockerfile.ssl         # SSL 版本 Dockerfile
```

---

## 三、首次配置流程

### 步骤 1: 传输 SSL 配置文件到服务器

在本地执行：

```bash
# 传输 SSL 相关文件
cd /root/AllProjects/project_2_我爱填单词

# 传输配置文件
scp docker-compose.prod.yml root@superhe.art:/opt/wordcross/
scp setup-ssl.sh root@superhe.art:/opt/wordcross/
scp src/frontend/nginx.ssl.conf root@superhe.art:/opt/wordcross/src/frontend/
scp src/frontend/nginx.init.conf root@superhe.art:/opt/wordcross/src/frontend/
scp src/frontend/Dockerfile.ssl root@superhe.art:/opt/wordcross/src/frontend/
```

### 步骤 2: SSH 到服务器

```bash
ssh root@superhe.art
cd /opt/wordcross
```

### 步骤 3: 修改邮箱配置

编辑 `setup-ssl.sh`，将 `EMAIL` 变量改为你的邮箱：

```bash
# 修改第 13 行
EMAIL="your-email@example.com"
```

### 步骤 4: 获取 SSL 证书

```bash
# 设置可执行权限
chmod +x setup-ssl.sh

# 首次获取证书
./setup-ssl.sh init
```

脚本将自动：
1. 创建证书目录
2. 启动临时 nginx 服务器
3. 通过 ACME 验证获取证书
4. 停止临时服务器

### 步骤 5: 启动 HTTPS 服务

```bash
# 重新构建前端镜像（使用 SSL Dockerfile）
docker compose -f docker-compose.prod.yml build frontend

# 启动所有服务
docker compose -f docker-compose.prod.yml up -d
```

### 步骤 6: 验证

```bash
# 检查服务状态
docker compose -f docker-compose.prod.yml ps

# 测试 HTTPS 连接
curl -I https://superhe.art:10443

# 查看证书信息
./setup-ssl.sh status
```

---

## 四、证书续期

Let's Encrypt 证书有效期为 90 天，需要定期续期。

### 4.1 自动续期

`docker-compose.prod.yml` 中的 certbot 服务会自动每 12 小时检查续期。

### 4.2 手动续期

```bash
./setup-ssl.sh renew
```

### 4.3 设置 Cron 任务（推荐）

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天凌晨 3 点检查续期）
0 3 * * * cd /opt/wordcross && ./setup-ssl.sh renew >> /var/log/certbot-renew.log 2>&1
```

---

## 五、常见问题

### Q1: 证书获取失败 - 域名验证失败

**原因**：域名未正确解析到服务器，或端口被防火墙阻挡。

**解决**：
```bash
# 检查域名解析
dig superhe.art

# 检查端口可达性（从外部）
nc -zv superhe.art 10010
```

### Q2: nginx 启动失败 - 证书文件不存在

**原因**：首次部署时证书尚未获取。

**解决**：
```bash
# 先获取证书
./setup-ssl.sh init

# 再启动服务
docker compose -f docker-compose.prod.yml up -d
```

### Q3: 证书续期失败

**原因**：可能是服务未运行或证书目录权限问题。

**解决**：
```bash
# 检查目录权限
ls -la certbot/

# 手动续期并查看详细日志
docker run --rm -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/certbot/www:/var/www/certbot" \
    certbot/certbot renew --dry-run
```

### Q4: 微信小程序仍报 HTTPS 错误

**可能原因**：
1. 微信后台未配置域名白名单
2. 使用了非标准端口（10443）

**解决**：
1. 在微信公众平台配置 `superhe.art:10443` 为合法域名
2. 或考虑使用 80/443 标准端口

### Q5: iOS App 报 ATS 错误

**原因**：证书链不完整或 TLS 版本过低。

**解决**：
```bash
# 验证证书链
openssl s_client -connect superhe.art:10443 -servername superhe.art

# 检查 TLS 版本
openssl s_client -connect superhe.art:10443 -tls1_2
```

---

## 六、端口方案对比

| 方案 | HTTP 端口 | HTTPS 端口 | 优点 | 缺点 |
|------|-----------|------------|------|------|
| 当前方案 | 10010 | 10443 | 不影响其他服务 | 非标准端口，微信可能有限制 |
| 标准端口 | 80 | 443 | 完全兼容所有平台 | 可能与其他服务冲突 |

### 切换到标准端口

如需使用标准端口，修改 `docker-compose.prod.yml`：

```yaml
frontend:
  ports:
    - "80:80"      # 替换 10010:80
    - "443:443"    # 替换 10443:443
```

同时更新 nginx 配置中的重定向端口。

---

## 七、安全建议

### 7.1 启用 HSTS

在 `nginx.ssl.conf` 中取消注释以下行：

```nginx
add_header Strict-Transport-Security "max-age=63072000" always;
```

### 7.2 定期检查证书

```bash
# 添加到监控脚本
./setup-ssl.sh status
```

### 7.3 备份证书

```bash
# 备份证书目录
tar -czf certbot-backup-$(date +%Y%m%d).tar.gz certbot/
```

---

## 八、参考链接

- [Let's Encrypt 官网](https://letsencrypt.org/)
- [Certbot 文档](https://certbot.eff.org/docs/)
- [Nginx SSL 配置最佳实践](https://ssl-config.mozilla.org/)
- [微信小程序 HTTPS 要求](https://developers.weixin.qq.com/miniprogram/dev/framework/ability/network.html)

---

*文档版本: v1.0*
*更新日期: 2026-01-29*
