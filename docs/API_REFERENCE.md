# 填单词游戏 - 后台API接口文档

> 版本: 1.0.0  
> 更新时间: 2026-01-26  
> 基础URL: `http://superhe.art:10010/api`

---

## 目录

1. [用户模块](#1-用户模块)
2. [体力与道具](#2-体力与道具)
3. [关卡数据](#3-关卡数据)
4. [游戏数据](#4-游戏数据)
5. [排行榜](#5-排行榜)
6. [管理后台](#6-管理后台)
7. [WebSocket](#7-websocket)

---

## 通用说明

### 认证方式
- 使用 Cookie 进行用户身份识别
- Cookie 名称: `user_id`
- 有效期: 7天

### 响应格式
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功"
}
```

### 错误响应
```json
{
  "detail": "错误描述"
}
```
HTTP状态码: 400/401/403/404/500

---

## 1. 用户模块

### 1.1 用户注册
```http
POST /api/user/register
Content-Type: application/json
```

**请求体:**
```json
{
  "nickname": "玩家昵称",
  "avatar": "😊"
}
```

**响应:**
```json
{
  "id": "uuid-string",
  "nickname": "玩家昵称",
  "avatar": "😊",
  "created_at": "2026-01-26T10:00:00"
}
```

**说明:** 后端生成用户ID，并通过 Set-Cookie 返回 `user_id`

---

### 1.2 获取用户信息
```http
GET /api/user/info
Cookie: user_id=xxx
```

**响应:**
```json
{
  "registered": true,
  "id": "uuid-string",
  "nickname": "玩家昵称",
  "avatar": "😊",
  "created_at": "2026-01-26T10:00:00"
}
```

**未注册时:**
```json
{
  "registered": false
}
```

---

### 1.3 更新用户信息
```http
PUT /api/user/update
Cookie: user_id=xxx
Content-Type: application/json
```

**请求体:**
```json
{
  "nickname": "新昵称",
  "avatar": "😎"
}
```

---

### 1.4 退出登录
```http
DELETE /api/user/logout
Cookie: user_id=xxx
```

**响应:**
```json
{
  "success": true,
  "message": "已退出登录"
}
```

---

## 2. 体力与道具

### 2.1 获取用户体力
```http
GET /api/user/energy
Cookie: user_id=xxx
```

**响应:**
```json
{
  "energy": 200,
  "max_energy": 200
}
```

---

### 2.2 更新用户体力
```http
PUT /api/user/energy
Cookie: user_id=xxx
Content-Type: application/json
```

**请求体:**
```json
{
  "energy": 180,
  "mode": "campaign"
}
```

---

### 2.3 领取免费体力
```http
POST /api/user/energy/claim-free
Cookie: user_id=xxx
Content-Type: application/json
```

**请求体:**
```json
{
  "amount": 10
}
```

**响应:**
```json
{
  "energy": 200,
  "max_energy": 200,
  "added": 10
}
```

---

### 2.4 获取用户道具
```http
GET /api/user/props
Cookie: user_id=xxx
```

**响应:**
```json
{
  "hintLetterCount": 20,
  "showTranslationCount": 20
}
```

---

### 2.5 更新用户道具
```http
PUT /api/user/props
Cookie: user_id=xxx
Content-Type: application/json
```

**请求体:**
```json
{
  "hintLetterCount": 18,
  "showTranslationCount": 19
}
```

---

## 3. 关卡数据

### 3.1 获取词库列表
```http
GET /api/vocabulary/groups
```

**响应:**
```json
[
  {"code": "grade3_1", "name": "三年级上册", "count": 63},
  {"code": "junior", "name": "初中词汇", "count": 2390},
  {"code": "cet4", "name": "大学四级", "count": 4198}
]
```

---

### 3.2 获取闯关关卡（后端API）
```http
GET /api/campaign/level/{level}?group={group}&mode=auto
```

**参数:**
- `level`: 关卡号 (1-2000)
- `group`: 词库代码 (grade3_1, junior, cet4等)
- `mode`: 生成模式 (auto/classic/csp)

**响应:**
```json
{
  "level": 1,
  "grid_size": 6,
  "cells": [["A","B",...], ...],
  "words": [
    {
      "id": 1,
      "word": "APPLE",
      "definition": "苹果",
      "direction": "across",
      "start_row": 0,
      "start_col": 0,
      "length": 5,
      "clue_number": 1
    }
  ],
  "prefilled": {"0-0": "A", "2-3": "E"},
  "difficulty": "easy",
  "layout_type": "dense"
}
```

---

### 3.3 获取关卡（静态文件 - 推荐）
```http
GET /data/levels/{group}/{level}.json
```

**示例:** `/data/levels/grade3_1/1.json`

**优势:** 毫秒级加载，无需后端计算

---

### 3.4 获取关卡汇总
```http
GET /data/levels_summary.json
```

**响应:**
```json
{
  "generated_at": "2026-01-25 20:25",
  "total_levels": 8954,
  "groups": [
    {
      "group_code": "grade3_1",
      "name": "三年级上册",
      "level_count": 81,
      "word_count": 63,
      "coverage": 98.4
    }
  ]
}
```

---

### 3.5 获取无限模式关卡
```http
GET /api/endless/puzzle?group={group}&difficulty={difficulty}
```

**参数:**
- `group`: 词库代码
- `difficulty`: low/medium/high

---

### 3.6 获取计时模式关卡
```http
GET /api/timed/puzzle?group={group}&duration=180&difficulty={difficulty}
```

---

## 4. 游戏数据

### 4.1 同步游戏积分
```http
POST /api/game/score
Cookie: user_id=xxx
Content-Type: application/json
```

**请求体:**
```json
{
  "score": 100,
  "vocab_group": "grade3_1",
  "level": 5
}
```

---

### 4.2 获取用户积分
```http
GET /api/game/score
Cookie: user_id=xxx
```

---

### 4.3 生成关卡奖励
```http
POST /api/game/generate-reward
Cookie: user_id=xxx
```

**响应:**
```json
{
  "success": true,
  "rewards": [
    {"type": "energy", "name": "体力", "icon": "⚡", "value": 10},
    {"type": "hint", "name": "提示", "icon": "💡", "value": 1}
  ]
}
```

**奖励规则:**
- 三个品类(体力/提示/发音)随机选两个
- 体力: 80%→10点, 19%→20点, 1%→50点
- 提示: 80%→1个, 19%→2个, 1%→5个
- 发音: 80%→1个, 19%→2个, 1%→3个

---

### 4.4 领取关卡奖励
```http
POST /api/game/claim-reward
Cookie: user_id=xxx
Content-Type: application/json
```

**请求体:**
```json
{
  "level": 5,
  "vocab_group": "grade3_1",
  "stars": 3,
  "time_seconds": 90
}
```

---

### 4.5 提交游戏数据
```http
POST /api/game/submit
Cookie: user_id=xxx
Content-Type: application/json
```

**请求体:**
```json
{
  "game_mode": "campaign",
  "vocab_group": "grade3_1",
  "score": 150,
  "words_count": 10,
  "level_reached": 5,
  "duration_seconds": 120,
  "result": null,
  "extra_data": {}
}
```

**游戏模式:** campaign / endless / timed / pk

---

### 4.6 提交PK结果
```http
POST /api/game/pk-result
Cookie: user_id=xxx
Content-Type: application/json
```

**请求体:**
```json
{
  "vocab_group": "grade3_1",
  "result": "win",
  "words_count": 8,
  "duration_seconds": 180
}
```

**结果:** win / lose / draw

---

## 5. 排行榜

### 5.1 获取排行榜类型
```http
GET /api/leaderboard/types
```

**响应:**
```json
{
  "types": [
    {"code": "campaign_level", "name": "闯关关卡榜"},
    {"code": "campaign_score", "name": "闯关积分榜"},
    {"code": "endless_level", "name": "无限关卡榜"},
    {"code": "endless_score", "name": "无限积分榜"},
    {"code": "timed_words", "name": "计时单词榜"},
    {"code": "timed_score", "name": "计时积分榜"},
    {"code": "pk_wins", "name": "PK获胜榜"},
    {"code": "pk_score", "name": "PK积分榜"}
  ],
  "groups": [
    {"code": "grade3_1", "name": "三年级上册"},
    {"code": "junior", "name": "初中词汇"}
  ]
}
```

---

### 5.2 获取排行榜数据
```http
GET /api/leaderboard/{lb_type}?group={group}&limit=50
```

**参数:**
- `lb_type`: 排行榜类型代码
- `group`: 词库分组 或 "all"
- `limit`: 返回条数

**响应:**
```json
{
  "lb_type": "campaign_level",
  "lb_name": "闯关关卡榜",
  "group": "all",
  "group_name": "全部",
  "count": 50,
  "entries": [
    {
      "rank": 1,
      "user_id": "uuid",
      "nickname": "玩家1",
      "avatar": "😊",
      "value": 100,
      "extra": {},
      "timestamp": "2026-01-26 10:00:00"
    }
  ]
}
```

---

### 5.3 提交排行榜分数
```http
POST /api/leaderboard/{lb_type}/submit
Content-Type: application/json
```

**请求体:**
```json
{
  "user_id": "uuid",
  "nickname": "玩家",
  "avatar": "😊",
  "group": "grade3_1",
  "value": 100,
  "extra": {}
}
```

---

### 5.4 获取用户排名
```http
GET /api/leaderboard/user/{user_id}
```

---

## 6. 管理后台

> 需要管理员Token: `?token=wordcross_admin_2026`

### 6.1 获取用户列表
```http
GET /api/admin/users?limit=50&offset=0&token=xxx
```

### 6.2 获取统计概览
```http
GET /api/admin/stats/overview?token=xxx
```

### 6.3 获取每日统计
```http
GET /api/admin/stats/daily?days=30&token=xxx
```

### 6.4 获取用户详情
```http
GET /api/admin/user/{user_id}?token=xxx
```

---

## 7. WebSocket

### 7.1 PK对战
```
ws://superhe.art:10010/ws/pk/{group}
```

**消息类型:**

**等待匹配:**
```json
{"type": "waiting", "message": "等待对手..."}
```

**开始游戏:**
```json
{
  "type": "start",
  "room_id": "grade3_1_1234",
  "puzzle": {...}
}
```

**提交答案:**
```json
{
  "type": "answer",
  "room_id": "grade3_1_1234",
  "correct": true
}
```

**分数更新:**
```json
{
  "type": "score_update",
  "scores": {"player1": 5, "player2": 3}
}
```

---

## 8. 静态资源

### 8.1 关卡数据
```
GET /data/levels/{group}/{level}.json
GET /data/levels/{group}/meta.json
GET /data/levels_summary.json
```

### 8.2 音频文件
```
GET /data/audio/us/{word}.mp3  # 美音
GET /data/audio/uk/{word}.mp3  # 英音
```

---

## 9. 词库代码对照表

| 分类 | 代码 | 名称 |
|------|------|------|
| 小学 | grade3_1 | 三年级上册 |
| 小学 | grade3_2 | 三年级下册 |
| 小学 | grade4_1 | 四年级上册 |
| 小学 | grade4_2 | 四年级下册 |
| 小学 | grade5_1 | 五年级上册 |
| 小学 | grade5_2 | 五年级下册 |
| 小学 | grade6_1 | 六年级上册 |
| 小学 | grade6_2 | 六年级下册 |
| 小学 | primary_all | 小学全部 |
| 初中 | junior7_1 | 七年级上册 |
| 初中 | junior7_2 | 七年级下册 |
| 初中 | junior8_1 | 八年级上册 |
| 初中 | junior8_2 | 八年级下册 |
| 初中 | junior9 | 九年级全册 |
| 初中 | junior_all | 初中全部 |
| 高中 | senior1-5 | 必修1-5 |
| 高中 | senior_all | 高中全部 |
| 考试 | ket | KET考试 |
| 考试 | pet | PET考试 |
| 考试 | cet4 | 大学四级 |
| 考试 | cet6 | 大学六级 |
| 考试 | postgrad | 考研词汇 |
| 考试 | ielts | 雅思 |
| 考试 | toefl | 托福 |
| 考试 | gre | GRE |

---

## 10. 体力消耗配置

| 游戏模式 | 体力消耗 |
|----------|----------|
| campaign (闯关) | 10 |
| timed (计时) | 30 |
| pk (对战) | 30 |
| endless (无限) | 30 |
