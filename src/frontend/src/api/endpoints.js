/**
 * API 端点常量
 * 从 src/shared/api/endpoints.ts 同步
 */

/** API 基础地址 - 从环境变量读取 */
export const API_BASE = import.meta.env.VITE_API_BASE || ''

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

  // ============ 管理员 ============
  ADMIN_STATS_OVERVIEW: '/api/admin/stats/overview',
  ADMIN_STATS_DAILY: '/api/admin/stats/daily',
  ADMIN_STATS_FEATURE: '/api/admin/stats/feature-usage',
  ADMIN_USERS: '/api/admin/users',
  ADMIN_STATS_PLATFORM: '/api/admin/stats/platform',
  ADMIN_STATS_EVENTS: '/api/admin/stats/events',
  ADMIN_STATS_ENERGY: '/api/admin/stats/energy',
  ADMIN_STATS_PROPS: '/api/admin/stats/props',
  ADMIN_STATS_RETENTION: '/api/admin/stats/retention',
  ADMIN_STATS_HOURLY: '/api/admin/stats/hourly',
  ADMIN_STATS_USER_RETENTION: '/api/admin/stats/user-retention',
  ADMIN_STATS_TOP_PLAYERS: '/api/admin/stats/top-players',
  ADMIN_STATS_VOCAB: '/api/admin/stats/vocab-analysis',
  ADMIN_USER_DETAIL: '/api/admin/user',
  ADMIN_CHANGE_PASSWORD: '/api/admin/change-password',
  ADMIN_PASSWORD_STATUS: '/api/admin/password-status',

  // ============ 行为追踪 ============
  TRACK_SESSION_START: '/api/track/session/start',
  TRACK_SESSION_END: '/api/track/session/end',
  TRACK_EVENT: '/api/track/event',
  TRACK_PROP_USAGE: '/api/track/prop-usage',
  TRACK_LEVEL_COMPLETE: '/api/track/level-complete',
  CLAIM_FREE_ENERGY_TRACKED: '/api/user/energy/claim-free-tracked',
}

/** 动态端点函数 */
export const buildUrl = {
  /** 获取闯关模式关卡 */
  campaignLevel: (level, group) =>
    `${API_BASE}/api/campaign/level/${level}?group=${group}`,

  /** 获取无限模式谜题 */
  endlessPuzzle: (group, difficulty) =>
    `${API_BASE}/api/endless/puzzle?group=${group}&difficulty=${difficulty}`,

  /** 获取计时模式谜题 */
  timedPuzzle: (group, duration, difficulty) =>
    `${API_BASE}/api/timed/puzzle?group=${group}&duration=${duration}&difficulty=${difficulty}`,

  /** 获取排行榜 */
  leaderboard: (type, group = 'all', limit = 50) =>
    `${API_BASE}/api/leaderboard/${type}?group=${group}&limit=${limit}`,

  /** 提交排行榜分数 */
  leaderboardSubmit: (type) =>
    `${API_BASE}/api/leaderboard/${type}/submit`,

  /** 获取用户排名 */
  userRankings: (userId) =>
    `${API_BASE}/api/leaderboard/user/${userId}`,

  /** 关卡数据（静态文件） */
  levelData: (group, level) =>
    `/data/levels/${group}/${level}.json`,

  /** 词库元数据（静态文件） */
  levelMeta: (group) =>
    `/data/levels/${group}/meta.json`,

  /** 关卡汇总（静态文件） */
  levelsSummary: '/data/levels_summary.json',

  /** 音频文件（静态文件） */
  audioFile: (type, word) =>
    `/data/audio/${type}/${word.toLowerCase()}.mp3`,

  /** PK WebSocket */
  pkWebSocket: (group) =>
    `${API_BASE.replace('http', 'ws')}/ws/pk/${group}`,
}

/** 获取完整URL */
export function getFullUrl(endpoint) {
  return `${API_BASE}${endpoint}`
}
