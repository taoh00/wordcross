# 我爱填单词 - 微信小程序版

## 项目简介

这是「我爱填单词」游戏的微信小程序版本，与网页版共用同一后端服务。

## 目录结构

```
src/wechat-minigame/
├── app.js                # 小程序入口
├── app.json              # 全局配置
├── app.wxss              # 全局样式
├── project.config.json   # 项目配置
├── sitemap.json          # 搜索配置
├── utils/                # 工具函数
│   ├── request.js        # 网络请求封装
│   ├── api.js            # API接口封装
│   ├── storage.js        # 本地存储封装
│   └── audio.js          # 音频播放封装
├── pages/                # 页面
│   ├── home/             # 首页
│   ├── game/             # 游戏页
│   ├── settings/         # 设置页
│   └── leaderboard/      # 排行榜页
├── components/           # 组件
│   ├── keyboard/         # 键盘组件
│   ├── grid/             # 网格组件
│   ├── word-list/        # 单词列表组件
│   └── modal/            # 弹窗组件
└── images/               # 图片资源
```

## 开发说明

### 1. 配置 AppID

在 `project.config.json` 中将 `appid` 替换为你的小程序 AppID：

```json
{
  "appid": "wx你的真实appid"
}
```

### 2. 配置后端地址

在 `app.js` 中修改 API 基础地址：

```javascript
globalData: {
  apiBase: 'https://superhe.art:10010',  // 改为你的后端地址
}
```

### 3. 添加域名白名单

在微信小程序后台添加以下域名到「服务器域名」配置：

- request合法域名：`https://superhe.art:10010`
- downloadFile合法域名：`https://superhe.art:10010`

### 4. 导入项目

1. 打开微信开发者工具
2. 选择「导入项目」
3. 选择 `src/wechat-minigame` 目录
4. 填入 AppID
5. 点击「导入」

## 功能特性

### 游戏模式

- **闯关模式**：逐关挑战，31个词库共12000+关卡
- **无限模式**：随机生成，每关3分钟限时
- **计时模式**：限时挑战，可选3/5/10分钟
- **PK模式**：在线对战（待实现WebSocket）

### 词库覆盖

- 小学：三年级~六年级各学期
- 初中：七年级~九年级各学期
- 高中：必修1~5
- 考试：KET、PET、CET4、CET6、考研、雅思、托福、GRE

### 体力系统

- 初始体力：200点
- 闯关消耗：10点/关
- 其他模式：30点/局
- 恢复速度：1点/分钟（离线也恢复）

### 道具系统

- 提示道具：高亮当前单词包含的字母
- 发音道具：朗读当前单词3遍

## 后端 API

小程序使用 `X-User-Id` Header 进行用户认证，不使用 Cookie。

详细 API 文档：[docs/API_REFERENCE.md](../../docs/API_REFERENCE.md)

## 技术栈

- 微信小程序原生开发
- ES6+ 语法
- WXML + WXSS
- Component 组件化

## 与网页版的差异

| 功能 | 网页版 | 小程序版 |
|------|--------|----------|
| 用户认证 | Cookie | X-User-Id Header |
| 网络请求 | axios | wx.request |
| 本地存储 | localStorage | wx.storage |
| 音频播放 | Audio API | innerAudioContext |
| 路由导航 | vue-router | wx.navigateTo |

## 版本信息

- 版本：1.0.0
- 更新日期：2026-01-26
