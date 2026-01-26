/**
 * 前端静态文件服务器 + API反向代理
 * 监听端口10010，将/api、/ws、/data请求转发到后端10012端口
 */
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');

const app = express();
const PORT = 10010;
const BACKEND_URL = 'http://localhost:10012';

// API代理 - 将/api请求转发到后端 (必须在静态文件之前)
const apiProxy = createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  logger: console,
  pathRewrite: undefined  // 保留原路径，不重写
});

// 使用正则匹配确保/api前缀被保留
app.use('/api', (req, res, next) => {
  // 修正路径：确保完整的 /api 前缀被保留
  req.url = '/api' + req.url;
  apiProxy(req, res, next);
});

// 音频文件代理 - 将/data请求转发到后端
const dataProxy = createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  logger: console
});

app.use('/data', dataProxy);

// WebSocket代理 - 将/ws请求转发到后端
const wsProxy = createProxyMiddleware({
  target: BACKEND_URL,
  ws: true,
  changeOrigin: true,
  logger: console
});

app.use('/ws', wsProxy);

// 静态文件服务
app.use(express.static(path.join(__dirname, 'dist')));

// SPA回退 - 所有其他路由返回index.html
app.use((req, res, next) => {
  // 如果文件不存在，返回index.html
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

const server = app.listen(PORT, '0.0.0.0', () => {
  console.log(`[前端] 服务运行在 http://0.0.0.0:${PORT}`);
  console.log(`[前端] API代理转发到 ${BACKEND_URL}`);
});

// 升级WebSocket连接
server.on('upgrade', wsProxy.upgrade);
