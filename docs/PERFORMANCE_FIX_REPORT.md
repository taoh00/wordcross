# 前端性能分析与修复报告

**日期**: 2026-01-26

---

## 1. 体力消耗逻辑整理

### 1.1 体力消耗规则（已统一）

| 游戏模式 | 体力消耗 | 触发时机 |
|----------|----------|----------|
| 闯关模式 (campaign) | 5点 | 进入游戏时、点击下一关按钮时 |
| 计时模式 (timed) | 15点 | 进入游戏时 |
| PK模式 (pk) | 15点 | 进入游戏时 |
| 无限模式 (endless) | 30点 | 进入游戏时 |

### 1.2 修复的问题

1. **重复扣除体力问题**
   - 问题：`claimFreeEnergy()` 领取体力后会再次手动扣除体力，与 `consumeEnergy()` 逻辑重复
   - 修复：改为调用统一的 `consumeEnergy()` 函数

2. **下一关不扣体力问题**
   - 问题：`goNextLevel()` 没有扣除体力
   - 修复：添加体力消耗检查，每关扣除5点

3. **体力数据格式不一致**
   - 问题：Game.vue 使用 `date` 字段，Home.vue 使用 `lastUpdate` 字段
   - 修复：统一使用 `lastUpdate` (时间戳)

---

## 2. 数据同步逻辑优化

### 2.1 统一数据同步入口

- `saveUserEnergy()`: 统一的体力保存入口，同时更新本地和后端
- `loadUserDataFromBackend()`: 只在后端数据更大时更新，防止覆盖刚扣除的体力

### 2.2 奖励领取后的数据刷新

- `claimRewards()` 调用后端API后，正确更新：
  - `userEnergy.value` - 体力值
  - `hintLetterCount.value` - 提示道具
  - `speakPropCount.value` - 发音道具
  - 同时保存到 localStorage

---

## 3. 性能问题分析与修复

### 3.1 发现的问题

#### 问题1：发音重复定时器未清理

- **位置**: `Game.vue` - `speakWordRepeated()`
- **问题**: 使用 `setTimeout` 递归调用，组件卸载时未清理
- **影响**: 内存泄漏，可能导致多次进入后卡死

**修复**:
```javascript
// 添加定时器引用
let speakRepeatTimeout = null

// 修改函数，保存定时器引用
speakRepeatTimeout = setTimeout(() => {
  speakWordRepeated(word, times)
}, 1200)

// 添加清理函数
function stopSpeakRepeat() {
  if (speakRepeatTimeout) {
    clearTimeout(speakRepeatTimeout)
    speakRepeatTimeout = null
  }
}

// 在 onUnmounted 中调用
onUnmounted(() => {
  stopSpeakRepeat()
})
```

#### 问题2：背景音乐振荡器累积

- **位置**: `audio.js` - `bgmOscillators` 数组
- **问题**: 振荡器对象不断累积，从未清理
- **影响**: 内存持续增长

**修复**:
```javascript
// 在每次循环前清理已停止的振荡器
function scheduleLoop() {
  const currentTime = ctx.currentTime
  bgmOscillators = bgmOscillators.filter(item => item.stopTime > currentTime)
  // ...
}
```

#### 问题3：DOM 引用未清理

- **位置**: `Game.vue` - `wordItemRefs`
- **问题**: 组件卸载时 DOM 引用未清理
- **影响**: 可能导致内存泄漏

**修复**:
```javascript
onUnmounted(() => {
  wordItemRefs.value = {}
})
```

#### 问题4：游戏状态未完全重置

- **位置**: `game.js` - `resetGame()`
- **问题**: `prefilledCells` 和 `isPlaying` 未重置
- **影响**: 状态残留导致异常

**修复**:
```javascript
function resetGame() {
  stopTimer()
  puzzle.value = null
  userAnswers.value = {}
  prefilledCells.value = {}  // 添加
  completedWords.value = []
  score.value = 0
  timer.value = 0
  isPlaying.value = false    // 添加
}
```

### 3.2 各游戏模式性能分析

| 模式 | 主要资源 | 清理状态 |
|------|----------|----------|
| 闯关 | 定时器、DOM引用 | ✅ 已修复 |
| 计时 | 定时器、背景音乐、DOM引用 | ✅ 已修复 |
| PK | 定时器、背景音乐、WebSocket | ✅ 定时器已修复 |
| 无限 | 定时器、DOM引用 | ✅ 已修复 |

---

## 4. 资源清理清单

### 4.1 onUnmounted 清理项

```javascript
onUnmounted(() => {
  // 1. 停止游戏计时器
  gameStore.stopTimer()
  
  // 2. 停止背景音乐
  stopBgMusic()
  
  // 3. 停止发音重复定时器
  stopSpeakRepeat()
  
  // 4. 清理 DOM 引用
  wordItemRefs.value = {}
  
  // 5. 重置弹窗状态
  showCompleteModal.value = false
  showEnergyModal.value = false
  showWordDetail.value = false
})
```

### 4.2 audio.js 清理项

- `bgmLoopTimeout` - 背景音乐循环定时器
- `bgmGainNode` - 音量控制节点
- `bgmOscillators` - 振荡器数组
- `bgmSource` - 音源节点

---

## 5. 验证建议

1. **体力消耗测试**:
   - 进入闯关模式，检查扣除5点
   - 通关后点击下一关，检查再扣除5点
   - 进入计时模式，检查扣除15点
   - 进入无限模式，检查扣除30点

2. **性能测试**:
   - 连续进入计时模式5次以上，观察是否卡顿
   - 使用浏览器 DevTools Memory 面板监控内存增长
   - 检查 Performance 面板中的定时器是否正确清理

3. **数据同步测试**:
   - 领取奖励后，检查体力值是否正确更新
   - 返回首页，检查体力值显示是否正确
   - 刷新页面，检查数据是否持久化

---

## 6. 修改的文件清单

| 文件 | 修改内容 |
|------|----------|
| `src/frontend/src/views/Game.vue` | 体力逻辑、定时器清理、DOM清理 |
| `src/frontend/src/stores/game.js` | resetGame 完善 |
| `src/frontend/src/utils/audio.js` | 振荡器清理 |

---

**修复完成时间**: 2026-01-26
