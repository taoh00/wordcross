# 多端架构规划方案

> 版本: 1.0.0  
> 更新时间: 2026-01-26

---

## 一、架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        统一后端服务                              │
│                 FastAPI (Python 3.12)                           │
│           http://superhe.art:10010/api                          │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ HTTP/WebSocket
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   网页版      │    │  微信小程序   │    │   iOS 应用    │
│  Vue 3 SPA   │    │ WXML/WXSS    │    │ React Native │
│  (已完成)     │    │  (已完成)     │    │  (已完成)     │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

## 二、三端对比

| 特性 | 网页版 (Web) | 微信小游戏 | iOS 应用 |
|------|-------------|-----------|----------|
| **技术栈** | Vue 3 + Vite | 原生 WXML/WXSS | React Native + Expo |
| **运行环境** | 浏览器 | 微信客户端 | iOS 系统 |
| **用户认证** | Cookie | openid/unionid | Apple ID / 自定义 |
| **数据存储** | localStorage | wx.storage | UserDefaults/CoreData |
| **网络请求** | axios/fetch | wx.request | URLSession/fetch |
| **音频播放** | Audio API | wx.createInnerAudioContext | AVFoundation |
| **分发渠道** | 直接访问 | 微信搜索/分享 | App Store |
| **审核周期** | 无 | 1-3天 | 1-7天 |
| **支付方式** | 无/第三方 | 微信支付 | Apple IAP |

---

## 三、代码复用策略

### 3.1 可复用部分 (共享)

```
shared/
├── api/                    # API 接口定义
│   ├── types.ts            # 数据类型定义
│   ├── endpoints.ts        # API 端点常量
│   └── models.ts           # 请求/响应模型
├── logic/                  # 核心业务逻辑
│   ├── gameLogic.ts        # 游戏核心逻辑
│   ├── scoreCalculator.ts  # 积分计算
│   ├── levelProgress.ts    # 关卡进度管理
│   └── wordValidator.ts    # 单词验证
├── constants/              # 常量配置
│   ├── groups.ts           # 词库分组配置
│   ├── gameConfig.ts       # 游戏配置
│   └── difficulty.ts       # 难度配置
└── utils/                  # 工具函数
    ├── formatters.ts       # 格式化工具
    └── validators.ts       # 验证工具
```

### 3.2 平台差异部分

| 模块 | 网页版 | 微信小游戏 | iOS 应用 |
|------|--------|-----------|----------|
| **用户认证** | Cookie + localStorage | wx.login + openid | Keychain + Apple ID |
| **网络请求** | axios | wx.request 封装 | URLSession / fetch |
| **本地存储** | localStorage | wx.setStorage | UserDefaults |
| **音频播放** | Audio API | innerAudioContext | AVAudioPlayer |
| **UI 组件** | Vue Components | WXML/WXSS | SwiftUI/RN Components |
| **路由导航** | vue-router | wx.navigateTo | NavigationStack |
| **状态管理** | Pinia | 自定义 Store | Redux / SwiftUI State |

---

## 四、共享业务逻辑设计

### 4.1 游戏核心逻辑 (TypeScript)

```typescript
// shared/logic/gameLogic.ts

export interface Cell {
  row: number;
  col: number;
  letter: string;
  isBlocked: boolean;
  isPrefilled: boolean;
}

export interface Word {
  id: number;
  word: string;
  definition: string;
  direction: 'across' | 'down';
  startRow: number;
  startCol: number;
  length: number;
  clueNumber: number;
}

export interface Puzzle {
  gridSize: number;
  cells: (string | null)[][];
  words: Word[];
  prefilled: Record<string, string>;
}

export interface GameState {
  puzzle: Puzzle | null;
  userAnswers: Record<string, string>;
  completedWords: Word[];
  score: number;
  timer: number;
}

// 核心函数 - 可在任何平台使用
export function checkWord(
  puzzle: Puzzle,
  userAnswers: Record<string, string>,
  wordId: number
): boolean {
  const word = puzzle.words.find(w => w.id === wordId);
  if (!word) return false;

  let userWord = '';
  for (let i = 0; i < word.length; i++) {
    const row = word.direction === 'across' ? word.startRow : word.startRow + i;
    const col = word.direction === 'across' ? word.startCol + i : word.startCol;
    const key = `${row}-${col}`;
    userWord += userAnswers[key] || '';
  }

  return userWord.toUpperCase() === word.word.toUpperCase();
}

export function calculateScore(completedWords: Word[]): number {
  return completedWords.reduce((sum, word) => sum + word.length * 10, 0);
}

export function calculateStars(timeSeconds: number): number {
  if (timeSeconds <= 120) return 3;
  if (timeSeconds <= 180) return 2;
  return 1;
}

export function isLevelComplete(puzzle: Puzzle, completedWords: Word[]): boolean {
  return completedWords.length === puzzle.words.length;
}
```

### 4.2 API 接口定义

```typescript
// shared/api/endpoints.ts

export const API_BASE = 'https://superhe.art:10010';

export const ENDPOINTS = {
  // 用户
  USER_REGISTER: '/api/user/register',
  USER_INFO: '/api/user/info',
  USER_UPDATE: '/api/user/update',
  USER_LOGOUT: '/api/user/logout',
  
  // 体力道具
  USER_ENERGY: '/api/user/energy',
  USER_PROPS: '/api/user/props',
  CLAIM_FREE_ENERGY: '/api/user/energy/claim-free',
  
  // 游戏
  GAME_SCORE: '/api/game/score',
  GAME_SUBMIT: '/api/game/submit',
  GENERATE_REWARD: '/api/game/generate-reward',
  CLAIM_REWARD: '/api/game/claim-reward',
  
  // 关卡
  VOCABULARY_GROUPS: '/api/vocabulary/groups',
  CAMPAIGN_LEVEL: (level: number, group: string) => 
    `/api/campaign/level/${level}?group=${group}`,
  ENDLESS_PUZZLE: (group: string, difficulty: string) =>
    `/api/endless/puzzle?group=${group}&difficulty=${difficulty}`,
  
  // 排行榜
  LEADERBOARD: (type: string, group: string) =>
    `/api/leaderboard/${type}?group=${group}`,
  
  // 静态资源
  LEVEL_DATA: (group: string, level: number) =>
    `/data/levels/${group}/${level}.json`,
  AUDIO_FILE: (type: 'us' | 'uk', word: string) =>
    `/data/audio/${type}/${word.toLowerCase()}.mp3`,
};
```

### 4.3 词库配置

```typescript
// shared/constants/groups.ts

export interface VocabGroup {
  code: string;
  name: string;
  icon: string;
  hasSubGroups?: boolean;
  subGroups?: VocabGroup[];
}

export const VOCAB_GROUPS: VocabGroup[] = [
  {
    code: 'primary',
    name: '小学词汇',
    icon: '📚',
    hasSubGroups: true,
    subGroups: [
      { code: 'primary_all', name: '全部', icon: '📚' },
      { code: 'grade3_1', name: '三年级上册', icon: '🌱' },
      { code: 'grade3_2', name: '三年级下册', icon: '🌿' },
      // ... 其他年级
    ]
  },
  { code: 'junior', name: '初中词汇', icon: '📖', hasSubGroups: true, /* ... */ },
  { code: 'senior', name: '高中词汇', icon: '📕', hasSubGroups: true, /* ... */ },
  { code: 'cet4', name: '大学四级', icon: '🏛️' },
  { code: 'cet6', name: '大学六级', icon: '🎖️' },
  // ... 其他词库
];

export const ENERGY_COST = {
  campaign: 10,
  timed: 30,
  pk: 30,
  endless: 30,
};
```

---

## 五、各平台实现指南

### 5.1 微信小游戏

#### 目录结构
```
src/wechat-minigame/
├── project.config.json      # 项目配置
├── game.json                 # 游戏配置
├── game.js                   # 入口文件
├── src/
│   ├── api/                  # API 封装
│   │   └── request.js        # wx.request 封装
│   ├── stores/               # 状态管理
│   │   ├── user.js
│   │   └── game.js
│   ├── pages/                # 页面
│   │   ├── home/
│   │   ├── game/
│   │   └── settings/
│   └── components/           # 组件
│       ├── grid/
│       └── keyboard/
├── libs/
│   └── shared/               # 引用共享代码
└── assets/
    └── images/
```

#### 用户认证适配
```javascript
// wechat-minigame/src/api/auth.js

export async function login() {
  return new Promise((resolve, reject) => {
    wx.login({
      success: async (res) => {
        if (res.code) {
          // 发送 code 到后端换取 openid
          const result = await request({
            url: '/api/user/wx-login',
            method: 'POST',
            data: { code: res.code }
          });
          resolve(result);
        } else {
          reject(new Error('登录失败'));
        }
      },
      fail: reject
    });
  });
}
```

#### 网络请求适配
```javascript
// wechat-minigame/src/api/request.js

const BASE_URL = 'https://superhe.art:10010';

export function request(options) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        'X-User-Id': wx.getStorageSync('userId') || ''
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          reject(new Error(res.data?.detail || '请求失败'));
        }
      },
      fail: reject
    });
  });
}
```

#### 音频播放适配
```javascript
// wechat-minigame/src/utils/audio.js

let audioContext = null;

export function speakWord(word, type = 'us') {
  if (audioContext) {
    audioContext.stop();
    audioContext.destroy();
  }
  
  audioContext = wx.createInnerAudioContext();
  audioContext.src = `${BASE_URL}/data/audio/${type}/${word.toLowerCase()}.mp3`;
  audioContext.play();
  
  audioContext.onError((err) => {
    console.warn('音频播放失败:', err);
  });
}
```

---

### 5.2 iOS 应用 (React Native 方案)

#### 目录结构
```
src/ios-app/
├── package.json
├── app.json
├── index.js
├── src/
│   ├── api/                  # API 封装
│   │   └── client.ts
│   ├── stores/               # Redux 状态管理
│   │   ├── userSlice.ts
│   │   └── gameSlice.ts
│   ├── screens/              # 页面
│   │   ├── HomeScreen.tsx
│   │   ├── GameScreen.tsx
│   │   └── SettingsScreen.tsx
│   ├── components/           # 组件
│   │   ├── Grid.tsx
│   │   └── Keyboard.tsx
│   └── utils/
│       └── audio.ts
├── ios/                      # iOS 原生代码
└── shared/                   # 软链接到共享代码
```

#### 用户认证适配
```typescript
// ios-app/src/api/auth.ts

import AsyncStorage from '@react-native-async-storage/async-storage';
import * as AppleAuthentication from 'expo-apple-authentication';

export async function signInWithApple() {
  try {
    const credential = await AppleAuthentication.signInAsync({
      requestedScopes: [
        AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
        AppleAuthentication.AppleAuthenticationScope.EMAIL,
      ],
    });
    
    // 发送到后端验证
    const response = await fetch(`${API_BASE}/api/user/apple-login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        identityToken: credential.identityToken,
        fullName: credential.fullName,
      }),
    });
    
    const userData = await response.json();
    await AsyncStorage.setItem('userId', userData.id);
    return userData;
  } catch (e) {
    throw e;
  }
}
```

#### 网络请求适配
```typescript
// ios-app/src/api/client.ts

import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL = 'https://superhe.art:10010';

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const userId = await AsyncStorage.getItem('userId');
  
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': userId || '',
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Request failed');
  }
  
  return response.json();
}
```

#### 音频播放适配
```typescript
// ios-app/src/utils/audio.ts

import { Audio } from 'expo-av';

let currentSound: Audio.Sound | null = null;

export async function speakWord(word: string, type: 'us' | 'uk' = 'us') {
  try {
    if (currentSound) {
      await currentSound.unloadAsync();
    }
    
    const { sound } = await Audio.Sound.createAsync({
      uri: `${BASE_URL}/data/audio/${type}/${word.toLowerCase()}.mp3`,
    });
    
    currentSound = sound;
    await sound.playAsync();
  } catch (e) {
    console.warn('音频播放失败:', e);
  }
}
```

---

### 5.3 iOS 应用 (SwiftUI 原生方案)

#### 目录结构
```
src/ios-native/
├── WordCross.xcodeproj
├── WordCross/
│   ├── App/
│   │   ├── WordCrossApp.swift
│   │   └── ContentView.swift
│   ├── Views/
│   │   ├── HomeView.swift
│   │   ├── GameView.swift
│   │   ├── GridView.swift
│   │   └── SettingsView.swift
│   ├── ViewModels/
│   │   ├── UserViewModel.swift
│   │   └── GameViewModel.swift
│   ├── Models/
│   │   ├── Puzzle.swift
│   │   ├── Word.swift
│   │   └── User.swift
│   ├── Services/
│   │   ├── APIService.swift
│   │   ├── AudioService.swift
│   │   └── StorageService.swift
│   └── Utilities/
│       └── Extensions.swift
└── Tests/
```

---

## 六、后端适配改造

### 6.1 用户认证扩展

需要新增以下接口支持多端认证：

```python
# 微信小游戏登录
@app.post("/api/user/wx-login")
async def wx_login(code: str):
    """
    通过微信 code 获取 openid，创建或关联用户
    """
    # 调用微信API获取 openid
    # 创建用户或返回已有用户
    pass

# Apple ID 登录
@app.post("/api/user/apple-login")
async def apple_login(identity_token: str, full_name: dict = None):
    """
    验证 Apple identityToken，创建或关联用户
    """
    # 验证 token
    # 创建用户或返回已有用户
    pass
```

### 6.2 认证方式切换

由于 Cookie 在小程序/App 中不适用，需要支持 Header 认证：

```python
# 从 Cookie 或 Header 获取用户ID
def get_user_id(
    user_id_cookie: Optional[str] = Cookie(default=None, alias="user_id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")
) -> Optional[str]:
    return user_id_cookie or x_user_id
```

### 6.3 CORS 配置

确保支持跨域请求：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 七、开发进度

### 第一阶段：代码重构 ✅ 已完成
1. ✅ 提取共享业务逻辑到 `shared/` 目录
2. ✅ 抽象 API 接口定义
3. ✅ 后端支持 Header 认证方式
4. ✅ 编写共享代码单元测试 (79个测试全部通过)

### 第二阶段：微信小程序 ✅ 已完成
1. ✅ 搭建小程序项目框架
2. ✅ 实现 wx.request 封装
3. ✅ 适配用户认证 (X-User-Id Header)
4. ✅ UI 组件开发 (Grid/Keyboard/WordList/Modal)
5. ✅ 功能联调测试

### 第三阶段：iOS 应用 ✅ 已完成
1. ✅ 选择技术方案：React Native + Expo
2. ✅ 搭建项目框架
3. ✅ 实现 API 客户端 (X-User-Id Header认证)
4. ✅ Redux Toolkit 状态管理
5. ✅ UI 组件开发 (Grid/Keyboard/WordList)
6. ✅ 页面开发 (Home/Game/Settings/Leaderboard/LevelSelect/VocabSelect)
7. 🔲 App Store 审核准备（待提交）

---

## 八、注意事项

### 8.1 微信小游戏限制
- 包体大小限制: 4MB (分包后 8MB)
- 必须使用 HTTPS
- 需要配置域名白名单
- 音频资源需要网络加载

### 8.2 iOS 应用限制
- 必须使用 HTTPS
- 内购必须使用 Apple IAP
- 用户数据隐私政策要求
- App Store 审核规范

### 8.3 数据同步策略
- 优先使用服务端数据
- 本地缓存作为离线备份
- 冲突时服务端优先
- 定期同步本地进度

---

## 九、项目结构总览

```
project_2_我爱填单词/
├── src/
│   ├── shared/                 # ✅ 共享代码
│   │   ├── api/                # 类型定义、API端点
│   │   ├── logic/              # 游戏逻辑、积分计算
│   │   ├── constants/          # 词库配置、游戏配置
│   │   └── utils/              # 验证、格式化工具
│   ├── frontend/               # ✅ 网页版 (Vue 3)
│   │   └── src/
│   ├── wechat-minigame/        # ✅ 微信小程序
│   │   ├── pages/              # 页面
│   │   ├── components/         # 组件
│   │   └── utils/              # 工具
│   ├── ios-app/                # ✅ iOS应用 (React Native)
│   │   ├── src/screens/        # 页面
│   │   ├── src/components/     # 组件
│   │   ├── src/stores/         # Redux状态
│   │   └── src/api/            # API客户端
│   ├── backend/                # ✅ 后端服务 (FastAPI)
│   │   └── main.py
│   └── data/                   # ✅ 关卡数据
│       └── levels/
├── docs/
│   ├── API_REFERENCE.md        # ✅ API文档
│   └── MULTI_PLATFORM_ARCHITECTURE.md  # ✅ 本文档
└── data/
    └── audio/                  # ✅ 音频资源
```

---

## 十、总结

| 模块 | 复用率 | 说明 |
|------|--------|------|
| 后端服务 | 100% | 三端共用同一后端 |
| API接口定义 | 100% | 共享接口常量和类型 |
| 业务逻辑 | 90% | 核心游戏逻辑共享 |
| UI组件 | 0% | 各平台独立实现 |
| 用户认证 | 30% | 认证流程需适配 |
| 数据存储 | 30% | 存储API需适配 |
| 音频播放 | 50% | 播放逻辑可复用，API需适配 |

**预计复用率: 60-70%**
