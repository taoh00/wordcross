# 荷尔蒙色组件库使用指南

## 概述

荷尔蒙色组件库 (`hormone-components.css`) 是基于荷尔蒙色配色方案的统一组件样式库，用于替换原有的马卡龙色（kawaii）主题。

## 引入方式

在 `main.js` 或 `App.vue` 中引入：

```javascript
import './assets/hormone-components.css'
```

## 组件清单

### 1. 按钮组件

#### 基础按钮
```html
<button class="hormone-btn hormone-btn-primary">主按钮</button>
<button class="hormone-btn hormone-btn-secondary">次要按钮</button>
<button class="hormone-btn hormone-btn-success">成功按钮</button>
<button class="hormone-btn hormone-btn-warning">警告按钮</button>
<button class="hormone-btn hormone-btn-info">信息按钮</button>
<button class="hormone-btn hormone-btn-error">错误按钮</button>
<button class="hormone-btn hormone-btn-accent">强调按钮</button>
```

#### 按钮状态
- **悬停**: 自动提升并增强阴影
- **激活**: 按下效果，阴影减小
- **禁用**: `disabled` 属性，降低透明度

```html
<button class="hormone-btn hormone-btn-primary" disabled>禁用按钮</button>
```

### 2. 卡片组件

#### 基础卡片
```html
<div class="hormone-card">
  <h3>卡片标题</h3>
  <p>卡片内容</p>
</div>
```

#### 信息卡片
```html
<div class="hormone-card hormone-card-info">
  <h3>信息卡片</h3>
  <p>用于显示信息内容</p>
</div>
```

#### 统计卡片
```html
<div class="hormone-card hormone-card-stats">
  <div class="stat-value">1,234</div>
  <div class="stat-label">总分数</div>
</div>
```

### 3. 输入框组件

```html
<input type="text" class="hormone-input" placeholder="请输入内容">
<input type="email" class="hormone-input" placeholder="邮箱地址">
<input type="password" class="hormone-input" placeholder="密码">
```

**状态**:
- **聚焦**: 边框变为主色，添加发光效果
- **禁用**: `disabled` 属性
- **无效**: 自动显示错误样式

### 4. Tab 按钮组件

```html
<div class="tab-group">
  <button class="hormone-tab active">标签1</button>
  <button class="hormone-tab">标签2</button>
  <button class="hormone-tab">标签3</button>
</div>
```

**状态**:
- **激活**: 添加 `active` 类，显示主色背景
- **悬停**: 提升并改变边框颜色

### 5. 徽章/标签组件

```html
<span class="hormone-badge">默认徽章</span>
<span class="hormone-badge hormone-badge-success">成功</span>
<span class="hormone-badge hormone-badge-warning">警告</span>
<span class="hormone-badge hormone-badge-error">错误</span>
<span class="hormone-badge hormone-badge-info">信息</span>
```

### 6. 列表项组件

```html
<div class="hormone-list-item">列表项 1</div>
<div class="hormone-list-item">列表项 2</div>
<div class="hormone-list-item selected">选中项</div>
```

**状态**:
- **悬停**: 提升并改变边框颜色
- **选中**: 添加 `selected` 类，显示主色背景渐变

### 7. 弹窗/模态框组件

```html
<!-- 遮罩层 -->
<div class="hormone-modal-overlay">
  <!-- 模态框 -->
  <div class="hormone-modal">
    <!-- 头部 -->
    <div class="hormone-modal-header">
      <h2 class="hormone-modal-title">标题</h2>
      <button class="hormone-modal-close">×</button>
    </div>
    <!-- 内容 -->
    <div class="hormone-modal-body">
      <p>模态框内容</p>
    </div>
    <!-- 底部 -->
    <div class="hormone-modal-footer">
      <button class="hormone-btn hormone-btn-secondary">取消</button>
      <button class="hormone-btn hormone-btn-primary">确认</button>
    </div>
  </div>
</div>
```

### 8. 进度条组件

```html
<!-- 默认进度条 -->
<div class="hormone-progress">
  <div class="hormone-progress-bar" style="width: 60%"></div>
</div>

<!-- 成功进度条 -->
<div class="hormone-progress hormone-progress-success">
  <div class="hormone-progress-bar" style="width: 80%"></div>
</div>

<!-- 警告进度条 -->
<div class="hormone-progress hormone-progress-warning">
  <div class="hormone-progress-bar" style="width: 50%"></div>
</div>

<!-- 错误进度条 -->
<div class="hormone-progress hormone-progress-error">
  <div class="hormone-progress-bar" style="width: 30%"></div>
</div>
```

### 9. 开关组件

```html
<label class="hormone-switch">
  <input type="checkbox">
  <span class="hormone-switch-slider"></span>
</label>
```

**状态**:
- **开启**: 显示主色背景和发光效果
- **禁用**: `disabled` 属性

### 10. 网格组件

```html
<div class="hormone-grid" style="grid-template-columns: repeat(3, 1fr);">
  <div class="hormone-grid-item">网格项 1</div>
  <div class="hormone-grid-item">网格项 2</div>
  <div class="hormone-grid-item">网格项 3</div>
</div>
```

### 11. 图标组件

```html
<div class="hormone-icon">⭐</div>
<div class="hormone-icon hormone-icon-primary">🎮</div>
<div class="hormone-icon hormone-icon-success">✅</div>
<div class="hormone-icon hormone-icon-warning">⚠️</div>
<div class="hormone-icon hormone-icon-error">❌</div>
<div class="hormone-icon hormone-icon-info">ℹ️</div>
```

### 12. 标题组件

```html
<h1 class="hormone-title">普通标题</h1>
<h1 class="hormone-title-gradient">渐变标题</h1>
```

### 13. 分割线

```html
<hr class="hormone-divider">
```

### 14. 加载状态

```html
<div class="hormone-loading"></div>
```

### 15. 工具提示

```html
<div class="hormone-tooltip">
  悬停我
  <span class="hormone-tooltip-text">这是提示文本</span>
</div>
```

## 动画工具类

```html
<div class="hormone-animate-pulse">脉冲动画</div>
<div class="hormone-animate-glow">发光动画</div>
<div class="hormone-animate-float">浮动动画</div>
<div class="hormone-animate-bounce">弹跳动画</div>
```

## 响应式适配

组件库已内置响应式适配：

- **平板** (≤768px): 减小内边距和字体大小
- **手机** (≤480px): 进一步优化尺寸

## 从 Kawaii 迁移

### 类名映射表

| Kawaii 类名 | Hormone 类名 |
|------------|-------------|
| `kawaii-btn` | `hormone-btn` |
| `kawaii-btn-primary` | `hormone-btn-primary` |
| `kawaii-btn-secondary` | `hormone-btn-secondary` |
| `kawaii-btn-mint` | `hormone-btn-success` |
| `kawaii-btn-blue` | `hormone-btn-info` |
| `kawaii-btn-yellow` | `hormone-btn-warning` |
| `kawaii-card` | `hormone-card` |
| `kawaii-input` | `hormone-input` |
| `kawaii-badge` | `hormone-badge` |
| `kawaii-tab` | `hormone-tab` |
| `kawaii-list-item` | `hormone-list-item` |
| `kawaii-title` | `hormone-title` |
| `kawaii-title-gradient` | `hormone-title-gradient` |

### 迁移步骤

1. **引入新样式**:
   ```javascript
   import './assets/hormone-components.css'
   ```

2. **全局替换类名**:
   ```bash
   # 使用编辑器查找替换功能
   kawaii- → hormone-
   ```

3. **更新背景色**:
   - 页面背景从 `#FFFAF0` (奶白色) 改为 `#1A1A2E` (深蓝黑)
   - 文字颜色从 `#5D5D5D` (深灰) 改为 `#FFFFFF` (纯白)

4. **测试所有组件**:
   - 检查按钮状态（悬停、激活、禁用）
   - 检查表单输入（聚焦、错误状态）
   - 检查响应式布局

## 配色方案参考

详细配色方案请参考: [docs/HORMONE_COLOR_PALETTE.md](HORMONE_COLOR_PALETTE.md)

## 注意事项

1. **深色背景**: 所有组件设计用于深色背景 (`#1A1A2E`)，确保文字对比度
2. **高饱和度**: 使用100%饱和度的纯正色彩，营造视觉冲击
3. **3D效果**: 按钮和卡片使用3D阴影效果，增强立体感
4. **发光效果**: 重要元素使用发光动画，增强视觉吸引力
5. **三端一致性**: 确保网页版、小程序、iOS应用使用相同的组件样式

## 更新日期

2026-02-01
