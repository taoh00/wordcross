/**
 * 共享代码入口
 * 三端（网页、微信小游戏、iOS）共用
 */

// ============ 类型导出 ============
export * from './api/types';

// ============ API 端点 ============
export { API_BASE, ENDPOINTS, HEADERS } from './api/endpoints';

// ============ 常量配置 ============
export {
  VOCAB_GROUPS,
  ALL_GROUP_CODES,
  GROUP_NAMES,
  getGroupName,
  isValidGroupCode,
  getGroupCategory,
} from './constants/groups';

export {
  ENERGY_COST,
  SCORE_CONFIG,
  STAR_THRESHOLDS,
  MAX_ENERGY,
  DEFAULT_ENERGY,
  DEFAULT_PROPS,
  DEFAULT_TIMED_DURATION,
  LEADERBOARD_TYPES,
  DIFFICULTY_CONFIG,
  GRID_CONFIG,
} from './constants/gameConfig';

// ============ 游戏逻辑 ============
export {
  checkWord,
  getWordCells,
  isCellInWord,
  getWordsAtCell,
  isLevelComplete,
  calculateProgress,
  formatTimer,
  cellKey,
  parseKey,
  isCellBlocked,
  getNextCell,
  getPrevCell,
  initGameState,
  getClueNumber,
  groupWordsByDirection,
} from './logic/gameLogic';

// ============ 积分计算 ============
export {
  calculateWordScore,
  calculateTotalScore,
  calculateStars,
  calculatePKScore,
  calculateCampaignResult,
  formatScore,
  getStarsDescription,
  getStarsEmoji,
} from './logic/scoreCalculator';

// ============ 工具函数 ============
export {
  isValidNickname,
  isValidLetter,
  isValidWord,
  isValidUserId,
  isValidLevel,
  isValidEnergy,
  sanitizeInput,
  normalizeWord,
} from './utils/validators';

export {
  formatTime,
  formatTimeLong,
  formatDate,
  formatDateTime,
  formatNumber,
  formatPercent,
  formatRank,
  formatRankShort,
  truncateText,
} from './utils/formatters';
