/**
 * 积分计算逻辑
 * 三端共用的积分和星级计算
 */

import type { Word } from '../api/types';
import { SCORE_CONFIG, STAR_THRESHOLDS } from '../constants/gameConfig';

/**
 * 计算单词得分
 * @param word 单词信息
 * @returns 该单词的得分
 */
export function calculateWordScore(word: Word): number {
  return word.length * SCORE_CONFIG.SCORE_PER_LETTER;
}

/**
 * 计算已完成单词的总分
 * @param completedWords 已完成的单词列表
 * @returns 总分
 */
export function calculateTotalScore(completedWords: Word[]): number {
  return completedWords.reduce((sum, word) => sum + calculateWordScore(word), 0);
}

/**
 * 根据用时计算星级
 * @param timeSeconds 用时（秒）
 * @returns 星级 1-3
 */
export function calculateStars(timeSeconds: number): number {
  if (timeSeconds <= STAR_THRESHOLDS.THREE_STARS) return 3;
  if (timeSeconds <= STAR_THRESHOLDS.TWO_STARS) return 2;
  return 1;
}

/**
 * 计算 PK 对战得分
 * @param wordsCount 完成的单词数
 * @param result 对战结果
 * @returns 本局得分
 */
export function calculatePKScore(
  wordsCount: number,
  result: 'win' | 'lose' | 'draw'
): number {
  let score = wordsCount * SCORE_CONFIG.SCORE_PER_LETTER;

  switch (result) {
    case 'win':
      score += SCORE_CONFIG.PK_WIN_BONUS;
      break;
    case 'draw':
      score += SCORE_CONFIG.PK_DRAW_BONUS;
      break;
    // lose 不加额外分
  }

  return score;
}

/**
 * 计算闯关模式得分
 * @param completedWords 已完成的单词列表
 * @param timeSeconds 用时（秒）
 * @returns { score: number, stars: number, bonus: number }
 */
export function calculateCampaignResult(
  completedWords: Word[],
  timeSeconds: number
): { score: number; stars: number; bonus: number } {
  const baseScore = calculateTotalScore(completedWords);
  const stars = calculateStars(timeSeconds);

  // 星级奖励：三星+50%，两星+20%，一星无奖励
  let bonusMultiplier = 0;
  if (stars === 3) bonusMultiplier = 0.5;
  else if (stars === 2) bonusMultiplier = 0.2;

  const bonus = Math.round(baseScore * bonusMultiplier);
  const score = baseScore + bonus;

  return { score, stars, bonus };
}

/**
 * 格式化分数显示
 * @param score 分数
 * @returns 格式化字符串（带千分位）
 */
export function formatScore(score: number): string {
  return score.toLocaleString();
}

/**
 * 获取星级描述
 * @param stars 星级 1-3
 * @returns 描述文字
 */
export function getStarsDescription(stars: number): string {
  switch (stars) {
    case 3:
      return '完美！';
    case 2:
      return '优秀！';
    case 1:
      return '及格';
    default:
      return '';
  }
}

/**
 * 获取星级对应的 emoji
 * @param stars 星级 1-3
 * @returns emoji 字符串
 */
export function getStarsEmoji(stars: number): string {
  return '⭐'.repeat(Math.min(Math.max(stars, 0), 3));
}
