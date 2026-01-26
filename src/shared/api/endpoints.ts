/**
 * API 端点常量
 * 三端共用的 API 路径定义
 */

/** API 基础地址 */
export const API_BASE = 'https://superhe.art:10010';

/** API 端点定义 */
export const ENDPOINTS = {
  // ============ 根接口 ============
  ROOT: '/api',

  // ============ 用户模块 ============
  USER_REGISTER: '/api/user/register',
  USER_INFO: '/api/user/info',
  USER_UPDATE: '/api/user/update',
  USER_LOGOUT: '/api/user/logout',
  USER_STATS: '/api/user/stats',

  // ============ 体力与道具 ============
  USER_ENERGY: '/api/user/energy',
  ENERGY_CONSUME: '/api/user/energy/consume',
  CLAIM_FREE_ENERGY: '/api/user/energy/claim-free',
  USER_PROPS: '/api/user/props',

  // ============ 游戏数据 ============
  GAME_SCORE: '/api/game/score',
  GAME_SUBMIT: '/api/game/submit',
  GENERATE_REWARD: '/api/game/generate-reward',
  CLAIM_REWARD: '/api/game/claim-reward',
  PK_RESULT: '/api/game/pk-result',

  // ============ 词库 ============
  VOCABULARY_GROUPS: '/api/vocabulary/groups',
  
  // ============ 关卡 ============
  /** 获取闯关模式关卡 */
  campaignLevel: (level: number, group: string) =>
    `/api/campaign/level/${level}?group=${group}`,
  
  /** 获取无限模式谜题 */
  endlessPuzzle: (group: string, difficulty: string) =>
    `/api/endless/puzzle?group=${group}&difficulty=${difficulty}`,
  
  /** 获取计时模式谜题 */
  timedPuzzle: (group: string, duration: number, difficulty: string) =>
    `/api/timed/puzzle?group=${group}&duration=${duration}&difficulty=${difficulty}`,

  // ============ 排行榜 ============
  /** 获取排行榜 */
  leaderboard: (type: string, group: string = 'all', limit: number = 50) =>
    `/api/leaderboard/${type}?group=${group}&limit=${limit}`,
  
  /** 提交排行榜分数 */
  leaderboardSubmit: (type: string) =>
    `/api/leaderboard/${type}/submit`,
  
  /** 获取用户排名 */
  userRankings: (userId: string) =>
    `/api/leaderboard/user/${userId}`,

  // ============ 静态资源 ============
  /** 关卡数据 */
  levelData: (group: string, level: number) =>
    `/data/levels/${group}/${level}.json`,
  
  /** 词库元数据 */
  levelMeta: (group: string) =>
    `/data/levels/${group}/meta.json`,
  
  /** 关卡汇总 */
  levelsSummary: '/data/levels_summary.json',
  
  /** 音频文件 */
  audioFile: (type: 'us' | 'uk', word: string) =>
    `/data/audio/${type}/${word.toLowerCase()}.mp3`,

  // ============ WebSocket ============
  /** PK 对战 */
  pkWebSocket: (group: string) =>
    `/ws/pk/${group}`,
} as const;

/** HTTP 方法 */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

/** 请求头 */
export const HEADERS = {
  /** JSON 内容类型 */
  JSON: {
    'Content-Type': 'application/json',
  },
  /** 用户ID请求头（用于小程序/App） */
  userIdHeader: (userId: string) => ({
    'X-User-Id': userId,
  }),
} as const;
