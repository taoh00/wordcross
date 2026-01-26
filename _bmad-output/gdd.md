---
stepsCompleted: [1,2,3,4,5,6,7,8,9,10,11,12,13,14]
inputDocuments: []
documentCounts:
  briefs: 1
  research: 1
  brainstorming: 1
  projectDocs: 1
workflowType: 'gdd'
lastStep: 14
project_name: '我爱填单词'
user_name: 'Boss'
date: '2026-01-24'
game_type: 'Educational Puzzle / Crossword'
game_name: '我爱填单词 WordCross'
---

# 我爱填单词 WordCross - Game Design Document

**Author:** Boss
**Game Type:** Educational Puzzle / Crossword
**Target Platform(s):** Web Browser (PC/Mobile), 后续支持微信小程序/App

---

## Executive Summary

### Core Concept

一款面向小学生到研究生的英语单词交叉填字游戏。玩家在NxN的网格中填写交叉的单词，共用字母形成交叉点。游戏融合教育与娱乐，通过多种模式激发学习兴趣。

**核心玩法示例：**
```
    D
G I R L
    G
M O O N
```
- 横向: GIRL, MOON
- 纵向: DOG (与GIRL共用G), IRON (与MOON共用O)

### Target Audience

| 用户群体 | 年龄 | 词汇级别 |
|---------|------|----------|
| 小学生 | 6-12岁 | 小学词汇 / PET / KET |
| 初中生 | 12-15岁 | 中考词汇 |
| 高中生 | 15-18岁 | 高考词汇 |
| 大学生 | 18-22岁 | 四级 / 六级 |
| 研究生 | 22岁+ | 考研 / 雅思 / 托福 / GRE |

### Unique Selling Points (USPs)

1. **多级词汇覆盖** - 从小学到研究生全覆盖
2. **四种游戏模式** - 闯关、无限、计时、PK满足不同需求
3. **Q版26字母设计** - 可爱有趣的视觉风格
4. **智能自动跳格** - 填完自动跳到下一个空格
5. **即时单词朗读** - 答对后自动发音强化记忆
6. **排行榜系统** - 激发竞争学习动力

---

## Goals and Context

### Project Goals

1. **教育目标**: 帮助用户在游戏中记忆英语单词
2. **娱乐目标**: 提供有趣的填字游戏体验
3. **社交目标**: 通过PK和排行榜促进用户互动
4. **商业目标**: 积累用户，后期可接入广告或会员服务

### Background and Rationale

传统背单词方式枯燥乏味，通过游戏化的交叉填字形式，让用户在解谜过程中自然记忆单词拼写和含义。

---

## Core Gameplay

### Game Pillars

1. **学习** - 核心是英语单词学习
2. **挑战** - 逐级递进的难度设计
3. **趣味** - Q版设计和成就系统
4. **竞技** - PK和排行榜

### Core Gameplay Loop

```
选择组别 → 选择模式 → 查看提示/定义 → 填写字母 → 
自动跳格 → 完成单词 → 朗读发音 → 计分 → 下一关/结算
```

### Win/Loss Conditions

| 模式 | 胜利条件 | 失败条件 |
|------|----------|----------|
| 闯关模式 | 完成当前关卡所有单词 | 无 (可重试) |
| 无限模式 | 持续通关 | 单关超时5分钟 |
| 计时模式 | 时间内尽可能多得分 | 时间结束 |
| PK模式 | 5分钟内得分更高 | 对方得分更高 |

---

## Game Mechanics

### Primary Mechanics

#### 1. 网格填字系统
- NxN可变网格 (根据难度3x3到10x10)
- 单词横纵交叉，共用字母
- 字母格子状态: 空白、已填、正确、错误

#### 2. 提示系统
- 显示单词的中文释义
- 可选: 显示首字母/音标提示
- 提示使用消耗积分

#### 3. 自动导航系统
- 填完一格自动跳到下一个空格
- 横向优先扫描
- 支持手动点击切换

#### 4. 答题反馈系统
- 正确: 高亮显示 + 朗读发音 + 加入已答列表
- 错误: 震动提示 + 显示正确答案

### Controls and Input

| 操作 | PC | Mobile |
|------|-----|--------|
| 选择格子 | 鼠标点击 | 触摸点击 |
| 输入字母 | 键盘输入 | 虚拟键盘 |
| 删除字母 | Backspace | 删除键 |
| 切换方向 | Tab / 点击 | 双击格子 |

---

## Game Modes Detail

### Mode 1: 闯关模式 (Campaign)

- **关卡数**: 256关
- **难度递进**:
  - 1-32关: 3x3网格, 2-3个单词
  - 33-64关: 4x4网格, 3-4个单词
  - 65-128关: 5x5网格, 4-5个单词
  - 129-192关: 6x6网格, 5-6个单词
  - 193-256关: 7x7+网格, 6+个单词
- **星级评价**: 根据用时和提示使用次数评1-3星
- **解锁机制**: 前一关通过后解锁下一关

### Mode 2: 无限模式 (Endless)

- **关卡生成**: 随机算法生成
- **单关时限**: 5分钟
- **计分方式**: 累计正确单词数
- **排行榜**: 按累计单词数排名
- **失败条件**: 超时未完成

### Mode 3: 计时模式 (Time Attack)

- **时间选项**: 3分钟 / 5分钟 / 10分钟
- **关卡生成**: 随机快速关卡
- **计分方式**: 时间内累计单词数
- **排行榜**: 各时段分开排名

### Mode 4: PK模式 (Versus)

- **对战时长**: 5分钟
- **匹配机制**: 相同组别匹配
- **同步机制**: 双方相同题目
- **胜负判定**: 正确单词数多者胜

---

## Vocabulary Groups (词汇组别)

| 组别代码 | 名称 | 词汇量 | 来源 |
|----------|------|--------|------|
| primary | 小学词汇 | ~800 | 新课标小学词汇 |
| pet | PET考试 | ~1500 | 剑桥PET词汇 |
| ket | KET考试 | ~1000 | 剑桥KET词汇 |
| junior | 初中词汇 | ~1600 | 新课标初中词汇 |
| senior | 高中词汇 | ~3500 | 新课标高中词汇 |
| cet4 | 大学四级 | ~4500 | 大学英语四级 |
| cet6 | 大学六级 | ~6000 | 大学英语六级 |
| postgrad | 考研词汇 | ~5500 | 考研英语大纲 |
| ielts | 雅思 | ~7000 | 雅思核心词汇 |
| toefl | 托福 | ~8000 | 托福核心词汇 |
| gre | GRE | ~10000 | GRE核心词汇 |

---

## Progression and Balance

### Player Progression

- **经验值系统**: 答对获得经验
- **等级系统**: 升级解锁新功能
- **成就系统**: 完成特定目标获得成就
- **收集系统**: 收集26个字母的Q版形象

### Difficulty Curve

```
简单 ──────────────────────────────── 困难
  │                                      │
  ├─ 3x3网格, 简单词汇, 长时间            │
  │                                      │
  ├─ 5x5网格, 中等词汇, 标准时间          │
  │                                      │
  └─ 7x7+网格, 复杂词汇, 紧迫时间 ────────┘
```

### Economy and Resources

- **金币**: 完成关卡获得，用于购买提示
- **钻石**: 成就获得，用于解锁主题
- **能量**: 限制每日PK次数 (可选)

---

## Level Design Framework

### Level Types

1. **标准关卡** - 固定设计的闯关关卡
2. **随机关卡** - 算法生成的无限/计时关卡
3. **PK关卡** - 双人同步对战关卡

### Level Progression

闯关模式关卡设计原则:
1. 新单词逐步引入
2. 已学单词循环出现
3. 难度平滑递增
4. 每8关一个检查点

---

## Art and Audio Direction

### Art Style

- **整体风格**: Q版可爱，扁平化设计
- **配色方案**: 明快活泼，蓝绿橙为主色
- **字母设计**: 26个字母各有Q版形象
- **UI风格**: 圆角卡片，柔和阴影

**26字母Q版形象概念**:
- A: 带天线的外星人
- B: 戴眼镜的蜜蜂
- C: 微笑的月亮
- D: 可爱的恐龙
- ... (每个字母一个可爱形象)

### Audio and Music

- **BGM**: 轻松愉快的学习背景音乐
- **单词朗读**: Web Speech API / 第三方TTS
- **音效**: 
  - 输入音效: 清脆打字声
  - 正确音效: 欢快叮咚声
  - 错误音效: 轻柔提示音
  - 通关音效: 胜利号角

---

## Technical Specifications

### Technology Stack

| 层级 | 技术选型 |
|------|----------|
| 前端框架 | Vue 3 + Vite |
| UI组件 | 自定义 + Tailwind CSS |
| 状态管理 | Pinia |
| 后端框架 | Python FastAPI |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |
| 缓存 | Redis |
| TTS | Web Speech API |

### Performance Requirements

- 首屏加载 < 3秒
- 交互响应 < 100ms
- 支持离线游戏 (PWA)
- 移动端适配

### Platform-Specific Details

- **PC浏览器**: Chrome/Firefox/Edge/Safari
- **移动浏览器**: iOS Safari, Android Chrome
- **后续**: 微信小程序, iOS/Android App

### Asset Requirements

- 26个Q版字母图片 (PNG/SVG)
- 10+套主题皮肤
- 背景音乐 3-5首
- 音效包 20+个
- 词汇库 JSON 文件

---

## Development Epics

### Epic 1: 核心引擎 (Sprint 1-2)
- 网格渲染系统
- 交叉单词生成算法
- 输入处理与自动跳格
- 答题验证逻辑

### Epic 2: 游戏模式 (Sprint 3-4)
- 闯关模式 (256关数据)
- 无限模式 (随机生成)
- 计时模式
- PK模式 (WebSocket)

### Epic 3: 词汇系统 (Sprint 2-3)
- 词汇库数据收集整理
- 难度分级算法
- 单词朗读集成

### Epic 4: UI/UX (Sprint 1-4)
- Q版26字母设计
- 响应式界面
- 主题系统

### Epic 5: 用户系统 (Sprint 4-5)
- 注册登录
- 进度同步
- 排行榜
- 成就系统

---

## Success Metrics

### Technical Metrics

- 崩溃率 < 0.1%
- API响应 < 200ms
- 前端性能评分 > 90 (Lighthouse)

### Gameplay Metrics

- 关卡通过率 > 80%
- 日均游戏时长 > 10分钟
- 次日留存 > 40%
- 周留存 > 20%

---

## Out of Scope (V1版本不包含)

- 自定义词库上传
- 社交好友系统
- 游戏内聊天
- 付费内容

---

## Assumptions and Dependencies

1. 用户有基本的英语基础
2. 词汇表数据可从公开资源获取
3. Web Speech API 在主流浏览器可用
4. 初期不需要用户认证 (本地存储进度)
