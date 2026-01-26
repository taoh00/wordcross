# 排行榜系统设计文档

## 1. 系统概述

### 1.1 目标
构建一个完整的排行榜系统，与账号系统联动，记录用户各种玩法数据，汇总成榜单，并提供后台统计报表。

### 1.2 核心功能
- **用户数据持久化**：使用SQLite数据库存储用户数据
- **玩法数据记录**：记录每个用户各种模式的游戏数据
- **多维度排行榜**：按类别、组别展示排行榜
- **后台管理系统**：用户管理和数据统计报表

---

## 2. 数据库设计

### 2.1 用户表 (users)
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,           -- UUID
    nickname TEXT NOT NULL,        -- 昵称
    avatar TEXT DEFAULT '😊',      -- 头像表情
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active_at DATETIME,       -- 最后活跃时间
    total_play_count INTEGER DEFAULT 0  -- 总游玩次数
);
```

### 2.2 用户游戏记录表 (game_records)
```sql
CREATE TABLE game_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    game_mode TEXT NOT NULL,       -- campaign/endless/timed/pk
    vocab_group TEXT NOT NULL,     -- grade3_1/junior/cet4 等
    score INTEGER DEFAULT 0,       -- 本局积分
    words_count INTEGER DEFAULT 0, -- 完成单词数
    level_reached INTEGER DEFAULT 0, -- 达到的关卡
    duration_seconds INTEGER,      -- 游戏时长(秒)
    result TEXT,                   -- win/lose/draw (PK模式)
    extra_data TEXT,               -- JSON扩展字段
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 2.3 用户统计表 (user_stats)
每个用户每个模式每个分组的汇总统计
```sql
CREATE TABLE user_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    game_mode TEXT NOT NULL,
    vocab_group TEXT NOT NULL,
    -- 闯关模式
    campaign_max_level INTEGER DEFAULT 0,    -- 最高关卡
    campaign_total_score INTEGER DEFAULT 0,  -- 总积分
    campaign_total_words INTEGER DEFAULT 0,  -- 总单词数
    -- 无限模式
    endless_max_level INTEGER DEFAULT 0,     -- 最长关卡数
    endless_total_score INTEGER DEFAULT 0,
    -- 计时模式
    timed_max_words INTEGER DEFAULT 0,       -- 单次最多单词
    timed_total_score INTEGER DEFAULT 0,
    timed_best_time INTEGER DEFAULT 0,       -- 最佳用时(秒)
    -- PK模式
    pk_wins INTEGER DEFAULT 0,               -- 胜场
    pk_draws INTEGER DEFAULT 0,              -- 平局
    pk_losses INTEGER DEFAULT 0,             -- 负场
    pk_total_score INTEGER DEFAULT 0,        -- PK积分
    -- 通用
    play_count INTEGER DEFAULT 0,            -- 该模式游玩次数
    last_played_at DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, game_mode, vocab_group)
);
```

### 2.4 功能使用统计表 (feature_usage)
```sql
CREATE TABLE feature_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    feature_name TEXT NOT NULL,    -- 功能名称
    usage_count INTEGER DEFAULT 0, -- 使用次数
    last_used_at DATETIME,
    UNIQUE(user_id, feature_name)
);
```

### 2.5 排行榜缓存表 (leaderboard_cache)
定时刷新的排行榜缓存
```sql
CREATE TABLE leaderboard_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lb_type TEXT NOT NULL,         -- 榜单类型
    vocab_group TEXT NOT NULL,     -- 分组(all表示总榜)
    rank INTEGER NOT NULL,         -- 排名
    user_id TEXT NOT NULL,
    nickname TEXT,
    avatar TEXT,
    value INTEGER,                 -- 分数/关卡数
    extra_data TEXT,               -- JSON扩展
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lb_type, vocab_group, user_id)
);
```

---

## 3. 排行榜类型

### 3.1 榜单类型
| 榜单代码 | 榜单名称 | 排名依据 | 说明 |
|---------|---------|---------|------|
| campaign_level | 闯关关卡榜 | 最高通关关卡 | 越高越好 |
| campaign_score | 闯关积分榜 | 总积分(每单词10分) | 累计积分 |
| endless_level | 无限关卡榜 | 单次最长关卡数 | 最佳成绩 |
| endless_score | 无限积分榜 | 总积分 | 累计积分 |
| timed_words | 计时单词榜 | 单次最多单词数 | 最佳成绩 |
| timed_score | 计时积分榜 | 总积分 | 累计积分 |
| pk_wins | PK获胜榜 | 获胜局数 | 累计胜场 |
| pk_score | PK积分榜 | PK积分(赢3平1) | 累计积分 |

### 3.2 分组类型
| 分类 | 分组代码 | 分组名称 |
|-----|---------|---------|
| 小学 | grade3_1 | 三年级上册 |
| 小学 | grade3_2 | 三年级下册 |
| 小学 | grade4_1 | 四年级上册 |
| 小学 | grade4_2 | 四年级下册 |
| 小学 | grade5_1 | 五年级上册 |
| 小学 | grade5_2 | 五年级下册 |
| 小学 | grade6_1 | 六年级上册 |
| 小学 | grade6_2 | 六年级下册 |
| 初高中 | junior | 初中词汇 |
| 初高中 | senior | 高中词汇 |
| 考试 | ket | KET考试 |
| 考试 | pet | PET考试 |
| 考试 | cet4 | 大学四级 |
| 考试 | cet6 | 大学六级 |
| 考试 | postgrad | 考研词汇 |
| 考试 | ielts | 雅思 |
| 考试 | toefl | 托福 |
| 考试 | gre | GRE |

### 3.3 积分规则
- **每对一个单词**: 10分
- **PK胜利**: 3分
- **PK平局**: 1分
- **PK失败**: 0分

---

## 4. API设计

### 4.1 游戏数据提交 API

#### POST /api/game/submit
提交一局游戏数据
```json
{
    "game_mode": "campaign",
    "vocab_group": "grade3_1",
    "score": 50,
    "words_count": 5,
    "level_reached": 3,
    "duration_seconds": 120,
    "result": null
}
```

#### POST /api/game/pk-result
提交PK对战结果
```json
{
    "vocab_group": "grade3_1",
    "result": "win",
    "words_count": 5,
    "duration_seconds": 90
}
```

### 4.2 排行榜 API

#### GET /api/leaderboard/{lb_type}
获取排行榜
- 参数: group (分组), limit (条数)
- 返回: 排行榜列表

#### GET /api/leaderboard/user/{user_id}
获取用户所有排名

### 4.3 用户统计 API

#### GET /api/user/stats
获取当前用户的游戏统计

#### GET /api/user/feature-usage
获取用户功能使用统计

### 4.4 后台管理 API

#### GET /api/admin/users
获取用户列表(分页)

#### GET /api/admin/stats/overview
获取整体统计概览

#### GET /api/admin/stats/daily
获取每日统计

#### GET /api/admin/stats/feature-usage
获取功能使用统计

---

## 5. 前端页面

### 5.1 排行榜页面 (已有，需增强)
- 榜单类型切换
- 分组筛选
- 我的排名
- 分页加载

### 5.2 个人中心页面 (新增)
- 游戏统计概览
- 各模式详细数据
- 历史记录

### 5.3 后台管理页面 (新增)
- 用户管理
- 数据统计报表
- 功能使用分析

---

## 6. 实现步骤

### Phase 1: 数据库层
1. 创建SQLite数据库和表结构
2. 实现数据库操作模块

### Phase 2: 后端API
1. 游戏数据提交API
2. 用户统计API
3. 排行榜刷新机制
4. 后台管理API

### Phase 3: 前端集成
1. 游戏结束时提交数据
2. 增强排行榜页面
3. 创建后台管理页面

### Phase 4: 测试验证
1. 模拟游戏数据测试
2. 排行榜正确性验证
3. 性能测试

---

## 7. 技术要点

### 7.1 数据一致性
- 使用事务确保数据完整性
- 排行榜缓存定时刷新

### 7.2 性能优化
- 排行榜使用缓存表，避免实时计算
- 分页加载大数据量

### 7.3 安全性
- 后台API需要管理员认证
- 防止刷分作弊

---

*文档版本: 1.0*
*创建日期: 2026-01-25*
