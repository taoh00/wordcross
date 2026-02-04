# 微信小游戏自动化截图对比工具

## 概述

本工具用于自动化截取微信小游戏各界面的截图，并与Web版进行对比。

## 方案概述

### 方案1: 微信开发者工具自动化 (推荐)

使用微信官方的 `miniprogram-automator` 模块来控制开发者工具并截图。

**优点**:
- 官方支持，稳定可靠
- 可以模拟触摸事件
- 可以获取截图

**缺点**:
- 需要本地安装微信开发者工具
- 小游戏使用Canvas，触摸事件需要特殊处理

### 方案2: 浏览器模拟 (备选)

创建一个HTML页面来模拟运行小游戏代码。

**优点**:
- 可以使用Playwright等工具自动化
- 不依赖微信开发者工具

**缺点**:
- 需要模拟所有wx API
- 可能存在兼容性问题

## 使用方法

### 前置条件

1. 安装微信开发者工具
2. 在工具的 **设置 → 安全设置** 中开启：
   - ✅ **服务端口（CLI/HTTP 调用功能）** — 必开，自动化脚本通过该端口连接开发者工具
   - ✅ 网络调试（可选，用于抓包/接口调试）
3. **自动远程 Debug 说明**：本仓库用 `miniprogram-automator` 连接本地微信开发者工具（需已打开项目并开启服务端口），在终端执行 `npm run screenshot` 即可自动打开工具、进入各页面并截图，无需在模拟器里手动点。

### 安装

```bash
cd src/wechat-minigame/autotest
npm install
```

### 运行截图

```bash
npm run screenshot
```

截图将保存到 `screenshots/` 目录。

## 手动对比流程

如果自动化脚本无法正常工作，可以采用手动对比：

1. **Web版截图**：
   - 打开 http://43.153.19.112:10010
   - 使用浏览器开发者工具将视口设置为 375x667 (iPhone 8)
   - 手动截取各页面

2. **小游戏截图**：
   - 打开微信开发者工具
   - 编译运行小游戏
   - 在模拟器中右键选择"截图"

3. **对比**：
   - 将截图并排放置对比
   - 记录差异点

## 截图清单

| 编号 | 界面名称 | 操作路径 |
|------|----------|----------|
| 01 | 首页-模式选择 | 启动后首页 |
| 02 | 闯关-词库选择 | 首页 → 闯关模式 |
| 03 | 闯关-子分组选择 | → 点击小学词汇 |
| 04 | 闯关-关卡选择 | → 点击"全部" |
| 05 | 设置页 | 首页 → 设置 |
| 06 | 排行榜 | 首页 → 排行榜 |
| 07 | 计时模式-时间选择 | 首页 → 计时模式 |
| 08 | 无限模式-难度选择 | 首页 → 无限模式 |
| 09 | 游戏页-网格 | 开始任意关卡 |
| 10 | 游戏页-通关弹窗 | 完成一关 |

## 微信开发者工具CLI命令

```bash
# Mac路径
/Applications/wechatwebdevtools.app/Contents/MacOS/cli

# 打开项目并启用自动化
cli --auto /path/to/project --auto-port 9420

# 连接到自动化端口
# 在脚本中使用 automator.connect({ wsEndpoint: 'ws://localhost:9420' })
```

## 常见问题

### Q: 截图失败
A: 确保开发者工具的安全设置中已开启服务端口。

### Q: 点击事件不生效
A: 小游戏使用Canvas，需要通过evaluate注入代码来模拟触摸事件。

### Q: 找不到CLI
A: 检查微信开发者工具的安装路径，Windows路径通常为：
   `C:/Program Files (x86)/Tencent/微信web开发者工具/cli.bat`

## 参考文档

- [微信小程序自动化](https://developers.weixin.qq.com/miniprogram/dev/devtools/auto/)
- [Automator API](https://developers.weixin.qq.com/miniprogram/dev/devtools/auto/automator.html)
- [MiniProgram API](https://developers.weixin.qq.com/miniprogram/dev/devtools/auto/miniprogram.html)
