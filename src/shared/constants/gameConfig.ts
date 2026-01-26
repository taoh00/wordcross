/**
 * 游戏配置常量
 * 三端共用的游戏规则配置
 */

/** 体力消耗配置 */
export const ENERGY_COST = {
  /** 闯关模式 */
  campaign: 10,
  /** 计时模式 */
  timed: 30,
  /** PK 模式 */
  pk: 30,
  /** 无限模式 */
  endless: 30,
} as const;

/** 积分配置 */
export const SCORE_CONFIG = {
  /** 每个单词基础分（乘以单词长度） */
  SCORE_PER_LETTER: 10,
  /** PK 胜利奖励分 */
  PK_WIN_BONUS: 3,
  /** PK 平局奖励分 */
  PK_DRAW_BONUS: 1,
} as const;

/** 星级评定配置（秒） */
export const STAR_THRESHOLDS = {
  /** 三星时间上限 */
  THREE_STARS: 120,
  /** 两星时间上限 */
  TWO_STARS: 180,
} as const;

/** 最大体力值 */
export const MAX_ENERGY = 200;

/** 默认体力值 */
export const DEFAULT_ENERGY = 200;

/** 默认道具数量 */
export const DEFAULT_PROPS = {
  hintLetterCount: 20,
  showTranslationCount: 20,
} as const;

/** 计时模式默认时长（秒） */
export const DEFAULT_TIMED_DURATION = 180;

/** 排行榜类型 */
export const LEADERBOARD_TYPES = {
  campaign_level: '闯关关卡榜',
  campaign_score: '闯关积分榜',
  endless_level: '无限关卡榜',
  endless_score: '无限积分榜',
  timed_words: '计时单词榜',
  timed_score: '计时积分榜',
  pk_wins: 'PK获胜榜',
  pk_score: 'PK积分榜',
} as const;

/** 难度配置 */
export const DIFFICULTY_CONFIG = {
  easy: {
    name: '简单',
    minLen: 2,
    maxLen: 4,
    prefilledRatio: 0.4,
  },
  medium: {
    name: '中等',
    minLen: 3,
    maxLen: 6,
    prefilledRatio: 0.25,
  },
  hard: {
    name: '困难',
    minLen: 5,
    maxLen: 10,
    prefilledRatio: 0.15,
  },
} as const;

/** 网格尺寸配置 */
export const GRID_CONFIG = {
  /** 小学词库最大网格 */
  PRIMARY_MAX: 8,
  /** 其他词库最大网格 */
  OTHER_MAX: 10,
  /** 小学词库起始网格 */
  PRIMARY_START: 5,
  /** 其他词库起始网格 */
  OTHER_START: 6,
} as const;
