# 填单词游戏测试指南

## 测试脚本

### 1. API自动化测试
测试所有HTTP接口功能。

```bash
# 安装依赖
pip install requests

# 运行测试（本地开发环境）
python tests/test_api.py --base-url http://localhost:10010

# 运行测试（生产环境）
python tests/test_api.py --base-url http://superhe.art:10010

# 指定报告输出文件
python tests/test_api.py --report my_report.json
```

### 2. UI截图测试
使用Playwright对各页面进行截图，验证布局和样式。

```bash
# 安装依赖
pip install playwright
playwright install chromium

# 运行测试
python tests/test_ui_screenshot.py --base-url http://localhost:10010

# 指定截图输出目录
python tests/test_ui_screenshot.py --output-dir ./my_screenshots
```

## 测试覆盖

### API测试项（共15项）
- A001: 用户注册
- A002: 已注册用户获取信息
- A003: 更新用户信息
- A004: 用户退出
- A005: 未注册用户获取信息
- A101: 获取体力
- A104: 获取道具
- A201: 获取词库列表
- A202: 获取关卡数据
- A203: 获取词库元数据
- A204: 获取词库汇总
- A206: 获取无限模式关卡
- A401: 获取排行榜类型
- A402: 获取排行榜数据
- A701: 美音音频
- A702: 英音音频

### UI截图测试项
- 首页（移动端/平板/桌面）
- 设置页（移动端/平板/桌面）
- 排行榜（移动端/平板/桌面）

## 测试报告

- API测试报告: `test_report.json`
- 截图测试报告: `tests/screenshots/screenshot_report.json`
- 截图文件: `tests/screenshots/*.png`

## 手动测试指南

### 游戏功能测试
1. 注册新用户，验证昵称和头像显示
2. 进入闯关模式，验证关卡加载
3. 填写单词，验证正确/错误反馈
4. 完成关卡，验证星级和奖励
5. 使用道具（提示/发音），验证功能
6. 切换设置（音效/翻译），验证生效

### 布局验证
1. 检查网格和单词列表是否有重叠
2. 检查Tab按钮是否正确显示
3. 检查不同屏幕尺寸的适配

## 环境要求

- Python 3.8+
- requests (API测试)
- playwright (UI测试)
- Node.js 16+ (前端)
- 后端服务运行中
