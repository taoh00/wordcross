/**
 * API 客户端
 * 封装网络请求，使用 X-User-Id Header 认证
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE = 'https://superhe.art:10010';

/** 请求配置 */
interface RequestConfig extends RequestInit {
  params?: Record<string, string | number>;
}

/** 通用请求函数 */
export async function request<T>(
  endpoint: string,
  config: RequestConfig = {}
): Promise<T> {
  const { params, ...init } = config;
  
  // 构建 URL
  let url = `${API_BASE}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      searchParams.append(key, String(value));
    });
    url += `?${searchParams.toString()}`;
  }
  
  // 获取用户 ID
  const userId = await AsyncStorage.getItem('userId');
  
  // 构建请求头
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(userId ? { 'X-User-Id': userId } : {}),
    ...init.headers,
  };
  
  // 发送请求
  const response = await fetch(url, {
    ...init,
    headers,
  });
  
  // 处理响应
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/** GET 请求 */
export function get<T>(endpoint: string, params?: Record<string, string | number>): Promise<T> {
  return request<T>(endpoint, { method: 'GET', params });
}

/** POST 请求 */
export function post<T>(endpoint: string, data?: unknown): Promise<T> {
  return request<T>(endpoint, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  });
}

/** PUT 请求 */
export function put<T>(endpoint: string, data?: unknown): Promise<T> {
  return request<T>(endpoint, {
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  });
}

/** DELETE 请求 */
export function del<T>(endpoint: string): Promise<T> {
  return request<T>(endpoint, { method: 'DELETE' });
}

// ============ API 模块 ============

/** 用户 API */
export const userApi = {
  /** 获取用户信息 */
  getInfo: () => get<{
    registered: boolean;
    id?: string;
    nickname?: string;
    avatar?: string;
  }>('/api/user/info'),
  
  /** 注册用户 */
  register: (nickname: string, avatar?: string) =>
    post<{ success: boolean; id: string; nickname: string; avatar: string }>(
      '/api/user/register',
      { nickname, avatar }
    ),
  
  /** 更新用户信息 */
  update: (nickname?: string, avatar?: string) =>
    post<{ success: boolean }>('/api/user/update', { nickname, avatar }),
  
  /** 登出 */
  logout: () => post<{ success: boolean }>('/api/user/logout'),
  
  /** 获取用户统计 */
  getStats: () => get<Record<string, unknown>>('/api/user/stats'),
};

/** 体力 API */
export const energyApi = {
  /** 获取体力 */
  get: () => get<{ energy: number; max_energy: number }>('/api/user/energy'),
  
  /** 消耗体力 */
  consume: (amount: number, mode: string) =>
    post<{ success: boolean; energy: number }>('/api/user/energy/consume', { amount, mode }),
  
  /** 领取免费体力 */
  claimFree: () =>
    post<{ success: boolean; energy: number; amount_claimed: number }>('/api/user/energy/claim-free'),
};

/** 道具 API */
export const propsApi = {
  /** 获取道具 */
  get: () => get<{ hintLetterCount: number; showTranslationCount: number }>('/api/user/props'),
  
  /** 使用道具 */
  use: (propType: string, amount: number = 1) =>
    post<{ success: boolean; remaining: number }>('/api/user/props/use', { prop_type: propType, amount }),
};

/** 游戏 API */
export const gameApi = {
  /** 获取积分 */
  getScore: () => get<{ score: number }>('/api/game/score'),
  
  /** 提交游戏数据 */
  submit: (data: {
    game_mode: string;
    vocab_group: string;
    score: number;
    words_count: number;
    level_reached: number;
    duration_seconds?: number;
    result?: string;
  }) => post<{ success: boolean }>('/api/game/submit', data),
  
  /** 生成奖励 */
  generateReward: (mode: string, level?: number) =>
    get<{ rewards: Array<{ type: string; name: string; icon: string; value: number }> }>(
      '/api/game/generate-reward',
      { mode, ...(level ? { level } : {}) }
    ),
  
  /** 领取奖励 */
  claimReward: (rewards: Array<{ type: string; value: number }>) =>
    post<{ success: boolean }>('/api/game/claim-reward', { rewards }),
};

/** 排行榜 API */
export const leaderboardApi = {
  /** 获取排行榜 */
  get: (type: string, group: string = 'all', limit: number = 50) =>
    get<{
      lb_type: string;
      lb_name: string;
      group: string;
      group_name: string;
      count: number;
      entries: Array<{
        rank: number;
        user_id: string;
        nickname: string;
        avatar: string;
        value: number;
      }>;
    }>(`/api/leaderboard/${type}`, { group, limit }),
  
  /** 提交排行榜分数 */
  submit: (type: string, group: string, score: number, extra?: Record<string, unknown>) =>
    post<{ success: boolean }>(`/api/leaderboard/${type}/submit`, { group, score, extra }),
  
  /** 获取用户排名 */
  getUserRankings: (userId: string) =>
    get<Record<string, { rank: number; value: number }>>(`/api/leaderboard/user/${userId}`),
};

/** 静态资源 API */
export const staticApi = {
  /** 获取关卡数据 */
  getLevel: (group: string, level: number) =>
    get<{
      grid_size: number;
      cells: (string | null)[][];
      words: Array<{
        id: number;
        word: string;
        definition: string;
        direction: string;
        start_row: number;
        start_col: number;
        length: number;
      }>;
      prefilled: Record<string, string>;
    }>(`/data/levels/${group}/${level}.json`),
  
  /** 获取词库元数据 */
  getMeta: (group: string) =>
    get<{
      group_code: string;
      group_name: string;
      level_count: number;
      word_count: number;
      coverage: number;
    }>(`/data/levels/${group}/meta.json`),
  
  /** 获取汇总数据 */
  getSummary: () =>
    get<{
      generated_at: string;
      total_groups: number;
      total_levels: number;
      groups: Array<{
        group_code: string;
        group_name: string;
        level_count: number;
      }>;
    }>('/data/levels_summary.json'),
  
  /** 获取音频 URL */
  getAudioUrl: (word: string, type: 'us' | 'uk' = 'us') =>
    `${API_BASE}/data/audio/${type}/${word.toLowerCase()}.mp3`,
};

/** 行为追踪 API（埋点） */
export const trackApi = {
  /** 会话ID缓存 */
  _sessionId: null as string | null,
  
  /** 生成会话ID */
  generateSessionId(): string {
    this._sessionId = 'ios_session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    return this._sessionId;
  },
  
  /** 获取设备信息 */
  getDeviceInfo(): Record<string, string | number> {
    // React Native 环境下使用 Platform 获取设备信息
    return {
      platform: 'ios',
      deviceType: 'mobile',
      browser: 'ReactNative',
      os: 'iOS',
    };
  },
  
  /** 开始会话 */
  async startSession(sessionId: string, deviceInfo: Record<string, string | number> = {}): Promise<void> {
    try {
      await post('/api/track/session/start', {
        session_id: sessionId,
        platform: deviceInfo.platform || 'ios',
        device_type: deviceInfo.deviceType,
        browser: deviceInfo.browser || 'ReactNative',
        os: deviceInfo.os,
        screen_width: deviceInfo.screenWidth,
        screen_height: deviceInfo.screenHeight,
      });
    } catch (e) {
      console.warn('会话追踪失败:', e);
    }
  },
  
  /** 结束会话 */
  async endSession(sessionId: string): Promise<void> {
    try {
      await post(`/api/track/session/end?session_id=${sessionId}`);
    } catch (e) {
      console.warn('会话结束追踪失败:', e);
    }
  },
  
  /** 记录事件 */
  async trackEvent(eventType: string, eventData: Record<string, unknown> | null = null, platform: string = 'ios'): Promise<void> {
    try {
      await post('/api/track/event', {
        event_type: eventType,
        event_data: eventData,
        platform,
      });
    } catch (e) {
      console.warn('事件追踪失败:', e);
    }
  },
  
  /** 记录道具使用 */
  async trackPropUsage(
    propType: string, 
    gameMode: string | null = null, 
    vocabGroup: string | null = null, 
    level: number | null = null, 
    platform: string = 'ios'
  ): Promise<void> {
    try {
      await post('/api/track/prop-usage', {
        prop_type: propType,
        game_mode: gameMode,
        vocab_group: vocabGroup,
        level,
        platform,
      });
    } catch (e) {
      console.warn('道具追踪失败:', e);
    }
  },
  
  /** 记录关卡完成 */
  async trackLevelComplete(
    vocabGroup: string, 
    level: number, 
    stars: number = 0, 
    score: number = 0, 
    durationSeconds: number | null = null, 
    platform: string = 'ios'
  ): Promise<void> {
    try {
      await post('/api/track/level-complete', {
        vocab_group: vocabGroup,
        level,
        stars,
        score,
        duration_seconds: durationSeconds,
        platform,
      });
    } catch (e) {
      console.warn('关卡完成追踪失败:', e);
    }
  },
  
  /** 领取免费体力（带追踪） */
  async claimFreeEnergyTracked(amount: number = 30, platform: string = 'ios'): Promise<{ energy: number } | null> {
    try {
      return await post<{ energy: number }>(`/api/user/energy/claim-free-tracked?platform=${platform}`, { amount });
    } catch (e) {
      console.warn('领取体力追踪失败:', e);
      return null;
    }
  },
};

export { API_BASE };
