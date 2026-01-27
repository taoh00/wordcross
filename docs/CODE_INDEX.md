# 填单词游戏 - 代码与功能索引

> 版本: 1.0.0  
> 更新时间: 2026-01-27  
> 用途: 快速定位代码与功能的对应关系

---

## 目录

1. [项目架构概览](#1-项目架构概览)
2. [后端模块索引](#2-后端模块索引)
3. [前端模块索引](#3-前端模块索引)
4. [微信小程序模块索引](#4-微信小程序模块索引)
5. [iOS应用模块索引](#5-ios应用模块索引)
6. [共享代码模块索引](#6-共享代码模块索引)
7. [数据文件索引](#7-数据文件索引)
8. [功能到代码的映射](#8-功能到代码的映射)
9. [关联文档索引](#9-关联文档索引)

---

## 1. 项目架构概览

### 1.1 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | Vue 3 + Vite | 网页版主应用 |
| 状态管理 | Pinia | Vue生态状态管理 |
| 样式 | Tailwind CSS | 原子化CSS框架 |
| 后端框架 | FastAPI | Python异步Web框架 |
| 数据库 | SQLite | 轻量级关系数据库 |
| 小程序 | 原生WXML/WXSS | 微信小程序 |
| iOS应用 | React Native + Expo | 跨平台移动框架 |

### 1.2 目录结构

```
project_2_我爱填单词/
├── src/
│   ├── backend/          # FastAPI后端服务
│   ├── frontend/         # Vue 3前端应用
│   ├── wechat-minigame/  # 微信小程序
│   ├── ios-app/          # iOS应用 (React Native)
│   ├── shared/           # 三端共享代码
│   └── data/             # 关卡数据JSON文件
├── data/
│   └── audio/            # 音频文件(MP3)
├── docs/                 # 设计文档
├── scripts/              # 脚本工具
├── deploy-dev.sh         # 开发环境部署
└── deploy-prod.sh        # 生产环境部署
```

---

## 2. 后端模块索引

### 2.1 主应用入口

**文件**: `src/backend/main.py`

| 行号范围 | 功能模块 | 说明 |
|----------|----------|------|
| 1-50 | 导入与初始化 | FastAPI应用创建、中间件配置 |
| 51-120 | 数据模型定义 | Pydantic模型(UserInfo, Puzzle等) |
| 121-200 | 用户API | 注册/登录/信息获取/更新/退出 |
| 201-280 | 体力与道具API | 获取/更新/消耗/领取免费体力 |
| 281-380 | 游戏数据API | 分数同步/奖励生成/奖励领取 |
| 381-500 | 关卡获取API | 闯关/无限/计时模式关卡获取 |
| 501-650 | 排行榜API | 类型列表/数据获取/分数提交 |
| 651-850 | 管理后台API | 用户列表/统计/分析 |
| 851-950 | 行为追踪API | 会话/事件/道具使用追踪 |
| 951-1050 | WebSocket(PK模式) | PK匹配/房间管理/实时对战 |
| 1051-1100 | 静态文件服务 | 音频文件/SPA路由回退 |

### 2.2 数据库模块

**文件**: `src/backend/database.py`

| 行号范围 | 功能模块 | 说明 |
|----------|----------|------|
| 1-50 | 数据库连接 | SQLite连接管理、路径配置 |
| 51-150 | 表结构创建 | users/game_records/user_stats等表 |
| 151-250 | 用户操作 | create_user/get_user/update_user |
| 251-350 | 游戏记录 | add_game_record/get_user_game_records |
| 351-450 | 用户统计 | update_user_stats/get_user_stats |
| 451-550 | 排行榜操作 | refresh_leaderboard/get_leaderboard |
| 551-700 | 管理分析 | get_daily_stats/get_overview_stats |
| 701-850 | 追踪记录 | record_user_event/record_prop_usage |
| 851-950 | 高级分析 | get_retention_analysis/get_top_players |

**数据表一览**:

| 表名 | 用途 | 主要字段 |
|------|------|----------|
| users | 用户信息 | id, nickname, avatar, created_at |
| game_records | 游戏记录 | user_id, game_mode, score, level |
| user_stats | 用户统计 | user_id, game_mode, vocab_group, total_score |
| leaderboard_cache | 排行榜缓存 | lb_type, group, user_id, value, rank |
| user_events | 事件追踪 | user_id, event_type, event_data |
| user_sessions | 会话记录 | session_id, user_id, start_time |
| energy_claims | 体力领取 | user_id, amount, claimed_at |
| prop_usage | 道具使用 | user_id, prop_type, game_mode |
| level_completions | 关卡完成 | user_id, vocab_group, level, stars |

### 2.3 词库管理模块

**文件**: `src/backend/vocabulary.py`

| 行号范围 | 功能模块 | 说明 |
|----------|----------|------|
| 1-30 | 工具函数 | is_pure_alpha()纯字母检查 |
| 31-80 | 词库组定义 | GROUPS字典(小学/初中/高中/考试) |
| 81-150 | 初始化加载 | 加载所有词库JSON到缓存 |
| 151-200 | 年级词库加载 | 从预生成关卡提取单词 |
| 201-280 | 词汇获取 | get_words/get_words_for_puzzle |
| 281-330 | CSP专用获取 | get_all_words_for_csp(交叉验证用) |

### 2.4 关卡生成器模块

#### 2.4.1 稀疏布局生成器

**文件**: `src/backend/puzzle_generator.py`

| 行号范围 | 功能模块 | 说明 |
|----------|----------|------|
| 1-50 | 数据结构 | Word/PlacedWord/CrosswordPuzzle类 |
| 51-120 | 谜题序列化 | to_dict()转换为API响应格式 |
| 121-180 | 难度配置 | LEVEL_CONFIG/DIFFICULTY_CONFIG |
| 181-300 | 核心生成算法 | _generate_puzzle_with_crossable_words |
| 301-400 | 单词放置 | _place_word/_can_place/_try_place_word |
| 401-500 | 交叉验证 | _validate_cross_sequences检查有效序列 |
| 501-600 | 预填字母 | _add_prefilled_letters智能预填 |
| 601-700 | 放置评分 | _calculate_placement_score多交叉点奖励 |

#### 2.4.2 CSP稠密布局生成器

**文件**: `src/backend/csp_puzzle_generator.py`

| 行号范围 | 功能模块 | 说明 |
|----------|----------|------|
| 1-80 | 数据结构 | WordSlot/CSPConstraint/DensePuzzle |
| 81-150 | 预填计算 | compute_revealed_letters智能预填 |
| 151-250 | 单词验证 | WordValidator有效词检查 |
| 251-400 | 单词索引 | WordIndex按长度/位置字母索引 |
| 401-550 | CSP求解器 | CSPSolver回溯+MRV+前向检查 |
| 551-700 | 模板求解器 | TemplateCSPSolver使用预定义模板 |
| 701-850 | 交叉验证生成 | CrossValidatedPuzzleGenerator |
| 851-950 | 闯关关卡生成 | generate_campaign_level难度映射 |
| 951-1050 | 随机关卡生成 | generate_random_puzzle无限/计时用 |

#### 2.4.3 批量关卡生成脚本

**文件**: `src/backend/generate_all_levels.py`

| 行号范围 | 功能模块 | 说明 |
|----------|----------|------|
| 1-50 | 配置常量 | TARGET_COVERAGE/DIFFICULTY_CONFIG |
| 51-150 | 关卡规格 | get_primary_level_specs/get_other_level_specs |
| 151-250 | 词库加载 | load_pep_grade_vocabulary各年级加载 |
| 251-400 | 单关生成 | generate_level核心生成逻辑 |
| 401-500 | 批量生成 | generate_single_group循环生成 |
| 501-600 | 数据保存 | save_group_data写入JSON文件 |
| 601-700 | 汇总更新 | update_summary生成levels_summary.json |

---

## 3. 前端模块索引

### 3.1 应用入口

**文件**: `src/frontend/src/App.vue`
- 根组件，包含路由视图和全局样式

**文件**: `src/frontend/src/main.js`
- Vue应用初始化、Pinia/Router插件注册

### 3.2 页面组件

#### 3.2.1 首页

**文件**: `src/frontend/src/views/Home.vue`

| 行号范围 | 功能模块 | 说明 |
|----------|----------|------|
| 1-50 | 顶部栏 | 用户信息/体力/道具显示 |
| 51-150 | 模式选择 | 闯关/无限/计时/PK按钮 |
| 151-200 | 时长选择 | 3/5/10分钟(计时/PK专用) |
| 201-250 | 难度选择 | 简单/中等/困难 |
| 251-350 | 词库选择 | 主分类按钮(小学/初中等) |
| 351-400 | 子词库选择 | 具体年级/册数选择 |
| 401-550 | 关卡选择 | 分页展示/进度/星级 |
| 551-700 | 脚本逻辑 | 状态管理/API调用/导航 |

#### 3.2.2 游戏页

**文件**: `src/frontend/src/views/Game.vue`

| 行号范围 | 功能模块 | 说明 |
|----------|----------|------|
| 1-80 | 顶部信息栏 | 模式/关卡/计时/积分/进度 |
| 81-200 | 游戏网格 | 动态网格渲染/格子状态 |
| 201-350 | 单词列表 | 横向/纵向单词/完成状态 |
| 351-450 | 虚拟键盘 | QWERTY布局/道具按钮 |
| 451-550 | 完成弹窗 | 星级/奖励/下一关/重玩 |
| 551-650 | 单词详情弹窗 | 单词/音标/释义/例句 |
| 651-750 | 体力不足弹窗 | 领取免费体力选项 |
| 751-1200 | 脚本逻辑 | 游戏核心逻辑/API交互 |

**核心函数映射**:

| 函数名 | 功能 | 行号(约) |
|--------|------|----------|
| handleCellClick | 格子点击处理 | 900 |
| inputLetter | 字母输入 | 920 |
| deleteLetter | 删除字母 | 950 |
| checkWordsAtCell | 检查单词完成 | 980 |
| useHintLetterProp | 使用提示道具 | 850 |
| useSpeakProp | 使用发音道具 | 870 |
| speakWord | 播放单词发音 | 1000 |
| claimRewards | 领取奖励 | 780 |
| goNextLevel | 进入下一关 | 800 |

### 3.3 状态管理

#### 3.3.1 游戏状态

**文件**: `src/frontend/src/stores/game.js`

| 行号范围 | 功能模块 | 说明 |
|----------|----------|------|
| 1-50 | 状态定义 | puzzle/userAnswers/completedWords等 |
| 51-100 | 词库组配置 | groups数组(主分类+子分类) |
| 101-150 | 计算属性 | gridSize/progress/isLevelComplete |
| 151-250 | 关卡加载 | loadSingleLevel/loadLevelsSummary |
| 251-350 | 谜题加载 | loadPuzzle(按模式获取) |
| 351-450 | 答案管理 | setAnswer/checkWord/checkAllWords |
| 451-500 | 计时器 | startTimer/stopTimer |
| 501-550 | 发音功能 | speakWord(多级fallback) |

#### 3.3.2 用户状态

**文件**: `src/frontend/src/stores/user.js`

| 行号范围 | 功能模块 | 说明 |
|----------|----------|------|
| 1-40 | 状态定义 | id/nickname/avatar/loading |
| 41-80 | 本地存储 | loadUserFromLocal/saveUserToLocal |
| 81-120 | 后端同步 | loadUser从后端加载 |
| 121-160 | 用户操作 | register/updateAvatar/updateNickname |
| 161-180 | 退出登录 | logout清除本地和后端 |

#### 3.3.3 设置状态

**文件**: `src/frontend/src/stores/settings.js`

| 功能 | 状态变量 | 说明 |
|------|----------|------|
| 自动发音 | autoSpeak | 填对后自动播放 |
| 发音类型 | voiceType | us/uk |
| 背景音乐 | bgMusic | 开/关 |
| 音效 | soundEffect | 开/关 |
| 震动 | vibration | 开/关 |
| 显示翻译 | showTranslation | 开/关 |

### 3.4 API客户端

**文件**: `src/frontend/src/api/client.js`

| 行号范围 | 模块 | 包含方法 |
|----------|------|----------|
| 1-60 | userApi | getInfo/register/update/logout |
| 61-100 | energyApi | get/update/consume/claimFree |
| 101-130 | propsApi | get/update |
| 131-200 | gameApi | getEndlessPuzzle/getTimedPuzzle/submit |
| 201-230 | leaderboardApi | get/submit/getUserRankings |
| 231-260 | staticApi | getLevelsSummary/getLevelData |
| 261-390 | adminApi | getOverview/getDailyStats等 |
| 391-530 | trackApi | startSession/trackEvent/trackPropUsage |

**文件**: `src/frontend/src/api/endpoints.js`
- API端点常量定义
- 动态URL构建函数(buildUrl)

---

## 4. 微信小程序模块索引

**目录**: `src/wechat-minigame/`

### 4.1 应用入口

| 文件 | 说明 |
|------|------|
| app.js | 全局数据/生命周期/API基础URL |
| app.json | 页面路由/tabBar/窗口配置 |
| app.wxss | 全局样式 |

### 4.2 页面

| 页面路径 | 功能 | 主要文件 |
|----------|------|----------|
| pages/home/ | 首页(模式/词库选择) | home.js/home.wxml |
| pages/game/ | 游戏主界面 | game.js/game.wxml |
| pages/settings/ | 设置页 | settings.js/settings.wxml |
| pages/leaderboard/ | 排行榜 | leaderboard.js/leaderboard.wxml |

### 4.3 组件

| 组件路径 | 功能 |
|----------|------|
| components/grid/ | 填字网格组件 |
| components/keyboard/ | 虚拟键盘组件 |
| components/word-list/ | 单词列表组件 |
| components/modal/ | 通用弹窗组件 |

### 4.4 工具模块

| 文件 | 功能 |
|------|------|
| utils/api.js | API封装(wx.request) |
| utils/request.js | 请求基础封装 |
| utils/storage.js | wx.storage封装 |
| utils/audio.js | 音频播放(wx.createInnerAudioContext) |

---

## 5. iOS应用模块索引

**目录**: `src/ios-app/`

### 5.1 应用结构

| 文件/目录 | 说明 |
|-----------|------|
| App.tsx | 应用入口/导航配置 |
| app.json | Expo配置 |
| src/screens/ | 页面组件 |
| src/stores/ | Redux状态管理 |
| src/components/ | 可复用组件 |
| src/api/ | API客户端 |

### 5.2 页面

| 页面文件 | 功能 |
|----------|------|
| HomeScreen.tsx | 首页(模式选择) |
| GameScreen.tsx | 游戏页 |
| SettingsScreen.tsx | 设置页 |
| LeaderboardScreen.tsx | 排行榜 |
| LevelSelectScreen.tsx | 关卡选择 |
| VocabSelectScreen.tsx | 词库选择 |

### 5.3 状态管理

| 文件 | 功能 |
|------|------|
| userSlice.ts | 用户状态(Redux Toolkit) |
| gameSlice.ts | 游戏状态 |
| settingsSlice.ts | 设置状态 |

---

## 6. 共享代码模块索引

**目录**: `src/shared/`

### 6.1 API类型定义

**文件**: `src/shared/api/types.ts`

| 类型名 | 用途 |
|--------|------|
| Cell | 格子位置与状态 |
| Word | 单词信息(位置/方向/长度) |
| Puzzle | 谜题数据(网格/单词/预填) |
| GameState | 游戏状态 |
| GameMode | 游戏模式枚举 |
| User | 用户信息 |
| EnergyInfo | 体力信息 |
| PropsInfo | 道具信息 |
| LeaderboardEntry | 排行榜条目 |
| VocabGroup | 词库分组 |

### 6.2 游戏逻辑

**文件**: `src/shared/logic/gameLogic.ts`

| 函数名 | 功能 |
|--------|------|
| checkWord | 检查单词是否正确 |
| getWordCells | 获取单词占用的格子 |
| isCellInWord | 判断格子是否属于单词 |
| getWordsAtCell | 获取格子上的所有单词 |
| isLevelComplete | 检查关卡是否完成 |
| calculateProgress | 计算完成进度 |
| formatTimer | 格式化计时器 |
| cellKey/parseKey | 格子坐标键值转换 |
| getNextCell/getPrevCell | 获取相邻格子 |
| initGameState | 初始化游戏状态 |

---

## 7. 数据文件索引

### 7.1 关卡数据

**目录结构**:
```
src/data/levels/
├── levels_summary.json     # 所有词库汇总
├── {group_code}/           # 每个词库一个目录
│   ├── meta.json           # 词库元数据
│   ├── 1.json              # 第1关数据
│   ├── 2.json              # 第2关数据
│   └── ...
```

**meta.json格式**:
```json
{
  "group_code": "grade3_1",
  "group_name": "三年级上册",
  "level_count": 81,
  "word_count": 63,
  "coverage": 98.4
}
```

**单关JSON格式**:
```json
{
  "level": 1,
  "grid_size": 6,
  "cells": [["","","A",...], ...],
  "words": [{
    "id": 1,
    "word": "APPLE",
    "definition": "苹果",
    "direction": "across",
    "start_row": 0,
    "start_col": 2,
    "length": 5,
    "clue_number": 1
  }],
  "prefilled": {"0-2": "A", "0-4": "L"},
  "difficulty": "easy"
}
```

### 7.2 词库源文件

**目录**: `src/data/`

| 文件 | 说明 |
|------|------|
| primary.json | 小学词汇 |
| junior.json | 初中词汇 |
| senior.json | 高中词汇 |
| cet4.json | 四级词汇 |
| cet6.json | 六级词汇 |
| postgraduate.json | 考研词汇 |
| ielts.json | 雅思词汇 |
| toefl.json | 托福词汇 |
| gre.json | GRE词汇 |
| ket.json | KET词汇 |
| pet.json | PET词汇 |
| pep_*.json | 人教版分册词汇 |

### 7.3 音频文件

**目录**: `data/audio/`

```
data/audio/
├── us/           # 美音
│   ├── apple.mp3
│   └── ...
└── uk/           # 英音
    ├── apple.mp3
    └── ...
```

---

## 8. 功能到代码的映射

### 8.1 用户系统

| 功能 | 前端代码 | 后端代码 | 数据表 |
|------|----------|----------|--------|
| 用户注册 | stores/user.js:register | main.py:user_register | users |
| 用户登录 | stores/user.js:loadUser | main.py:get_user_info | users |
| 头像更新 | stores/user.js:updateAvatar | main.py:update_user | users |
| 退出登录 | stores/user.js:logout | main.py:user_logout | users |

### 8.2 体力系统

| 功能 | 前端代码 | 后端代码 | 说明 |
|------|----------|----------|------|
| 体力显示 | Home.vue:userEnergy | main.py:get_user_energy | 每分钟恢复1点 |
| 体力消耗 | Game.vue:consumeEnergy | main.py:consume_energy | 闯关10/其他30 |
| 免费领取 | Game.vue:claimFreeEnergy | main.py:claim_free_energy | 30点/次 |

### 8.3 游戏模式

| 模式 | 前端入口 | 后端API | 特点 |
|------|----------|---------|------|
| 闯关 | Game.vue(campaign) | /api/campaign/level/{n} | 关卡制/1-3星 |
| 无限 | Game.vue(endless) | /api/endless/puzzle | 无限关卡/计时 |
| 计时 | Game.vue(timed) | /api/timed/puzzle | 3/5/10分钟 |
| PK | Game.vue(pk) | /ws/pk/{group} | WebSocket对战 |

### 8.4 道具系统

| 道具 | 使用函数 | 效果 | 初始数量 |
|------|----------|------|----------|
| 提示💡 | useHintLetterProp | 显示一个字母 | 20 |
| 发音🔊 | useSpeakProp | 播放当前单词 | 20 |

### 8.5 关卡生成

| 阶段 | 代码位置 | 说明 |
|------|----------|------|
| 词库加载 | vocabulary.py | is_pure_alpha过滤 |
| 规格计算 | generate_all_levels.py | 网格/难度/单词数 |
| 稀疏生成 | puzzle_generator.py | CrosswordGenerator |
| 稠密生成 | csp_puzzle_generator.py | CSPPuzzleGenerator |
| 预填计算 | compute_revealed_letters | 智能选择交叉点 |
| 保存输出 | save_group_data | JSON文件写入 |

### 8.6 排行榜系统

| 榜单类型 | 排序依据 | API端点 |
|----------|----------|---------|
| campaign_level | 最高关卡 | /api/leaderboard/campaign_level |
| campaign_score | 总积分 | /api/leaderboard/campaign_score |
| endless_level | 通关关卡数 | /api/leaderboard/endless_level |
| timed_words | 单词数量 | /api/leaderboard/timed_words |
| pk_wins | 获胜场次 | /api/leaderboard/pk_wins |

### 8.7 音频播放

| 场景 | 代码位置 | 优先级 |
|------|----------|--------|
| 本地音频 | /data/audio/{type}/{word}.mp3 | 1 |
| 有道API | youdao.com/dictvoice | 2 |
| 浏览器TTS | SpeechSynthesis | 3 |

---

## 9. 关联文档索引

### 9.1 设计文档

| 文档 | 路径 | 内容 |
|------|------|------|
| 游戏设计简报 | docs/GAME_DESIGN_BRIEF.md | 完整功能设计 |
| API参考 | docs/API_REFERENCE.md | 后端接口文档 |
| 排行榜设计 | docs/LEADERBOARD_SYSTEM_DESIGN.md | 排行榜系统 |
| 多端架构 | docs/MULTI_PLATFORM_ARCHITECTURE.md | 三端架构设计 |
| Docker部署 | docs/DOCKER_DEPLOYMENT.md | 容器化部署 |
| CSP生成器 | docs/CSP_PUZZLE_GENERATOR_ARCHITECTURE.md | 算法详解 |
| 词库资源 | docs/VOCABULARY_RESOURCES.md | 词库来源说明 |
| 图标设计 | docs/ICON_DESIGN.md | 应用图标规范 |
| 性能修复 | docs/PERFORMANCE_FIX_REPORT.md | 性能优化记录 |
| 功能更新 | docs/GAME_FEATURE_UPDATES.md | 版本更新日志 |

### 9.2 项目规则

| 文件 | 说明 |
|------|------|
| .cursorrules | 项目规则/关卡配置/技术栈/部署说明 |

### 9.3 部署脚本

| 脚本 | 用途 |
|------|------|
| deploy-dev.sh | 本地开发环境 |
| deploy-prod.sh | 生产环境部署(superhe.art) |

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-01-27 | 1.0.0 | 初始版本，完成全部模块索引 |
