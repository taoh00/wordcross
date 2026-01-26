/**
 * 共享类型定义
 * 三端（网页、微信小游戏、iOS）共用的数据类型
 */

// ============ 游戏核心类型 ============

/** 格子位置 */
export interface Cell {
  row: number;
  col: number;
  letter: string;
  isBlocked: boolean;
  isPrefilled: boolean;
}

/** 单词方向 */
export type WordDirection = 'across' | 'down';

/** 单词信息 */
export interface Word {
  id: number;
  word: string;
  definition: string;
  direction: WordDirection;
  start_row: number;
  start_col: number;
  length: number;
  clue_number?: number;
}

/** 谜题数据 */
export interface Puzzle {
  grid_size: number;
  cells: (string | null)[][];
  words: Word[];
  prefilled: Record<string, string>;
  level?: number;
  difficulty?: string;
  group?: string;
}

/** 游戏状态 */
export interface GameState {
  puzzle: Puzzle | null;
  userAnswers: Record<string, string>;
  completedWords: Word[];
  score: number;
  timer: number;
  isPlaying: boolean;
}

/** 游戏模式 */
export type GameMode = 'campaign' | 'endless' | 'timed' | 'pk';

/** 难度等级 */
export type Difficulty = 'easy' | 'medium' | 'hard' | 'low' | 'high';

// ============ 用户相关类型 ============

/** 用户信息 */
export interface User {
  id: string;
  nickname: string;
  avatar: string;
  created_at: string;
}

/** 用户注册请求 */
export interface UserRegisterRequest {
  nickname: string;
  avatar?: string;
}

/** 用户信息响应 */
export interface UserInfoResponse {
  registered: boolean;
  id?: string;
  nickname?: string;
  avatar?: string;
  created_at?: string;
}

// ============ 体力和道具类型 ============

/** 体力信息 */
export interface EnergyInfo {
  energy: number;
  max_energy: number;
}

/** 道具信息 */
export interface PropsInfo {
  hintLetterCount: number;
  showTranslationCount: number;
}

// ============ 游戏数据类型 ============

/** 游戏提交数据 */
export interface GameSubmitData {
  game_mode: GameMode;
  vocab_group: string;
  score: number;
  words_count: number;
  level_reached: number;
  duration_seconds?: number;
  result?: 'win' | 'lose' | 'draw';
  extra_data?: Record<string, unknown>;
}

/** 关卡奖励 */
export interface Reward {
  type: 'energy' | 'hint' | 'speak';
  name: string;
  icon: string;
  value: number;
}

/** 奖励响应 */
export interface RewardResponse {
  success: boolean;
  rewards: Reward[];
}

// ============ 排行榜类型 ============

/** 排行榜类型代码 */
export type LeaderboardType = 
  | 'campaign_level'
  | 'campaign_score'
  | 'endless_level'
  | 'endless_score'
  | 'timed_words'
  | 'timed_score'
  | 'pk_wins'
  | 'pk_score';

/** 排行榜条目 */
export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  nickname: string;
  avatar: string;
  group: string;
  group_name: string;
  value: number;
  extra?: Record<string, unknown>;
  timestamp?: string;
}

/** 排行榜响应 */
export interface LeaderboardResponse {
  lb_type: LeaderboardType;
  lb_name: string;
  group: string;
  group_name: string;
  count: number;
  entries: LeaderboardEntry[];
}

// ============ 词库类型 ============

/** 词库分组 */
export interface VocabGroup {
  code: string;
  name: string;
  icon: string;
  hasSubGroups?: boolean;
  subGroups?: VocabGroup[];
}

/** 词库元数据 */
export interface VocabMeta {
  group_code: string;
  group_name: string;
  level_count: number;
  word_count: number;
  coverage: number;
}

// ============ API 响应类型 ============

/** 通用成功响应 */
export interface SuccessResponse {
  success: boolean;
  message?: string;
}

/** 通用错误响应 */
export interface ErrorResponse {
  detail: string;
}

/** 关卡汇总 */
export interface LevelsSummary {
  generated_at: string;
  total_groups: number;
  total_levels: number;
  groups: VocabMeta[];
}
