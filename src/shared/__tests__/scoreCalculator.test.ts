/**
 * 积分计算单元测试
 */

import {
  calculateWordScore,
  calculateTotalScore,
  calculateStars,
  calculatePKScore,
  calculateCampaignResult,
  formatScore,
  getStarsDescription,
  getStarsEmoji,
} from '../logic/scoreCalculator';
import type { Word } from '../api/types';

const mockWords: Word[] = [
  {
    id: 1,
    word: 'CAT',
    definition: '猫',
    direction: 'across',
    start_row: 0,
    start_col: 0,
    length: 3,
  },
  {
    id: 2,
    word: 'TEST',
    definition: '测试',
    direction: 'down',
    start_row: 0,
    start_col: 2,
    length: 4,
  },
  {
    id: 3,
    word: 'HELLO',
    definition: '你好',
    direction: 'across',
    start_row: 2,
    start_col: 0,
    length: 5,
  },
];

describe('scoreCalculator', () => {
  describe('calculateWordScore', () => {
    it('应该根据单词长度计算分数', () => {
      expect(calculateWordScore(mockWords[0])).toBe(30); // 3 * 10
      expect(calculateWordScore(mockWords[1])).toBe(40); // 4 * 10
      expect(calculateWordScore(mockWords[2])).toBe(50); // 5 * 10
    });
  });

  describe('calculateTotalScore', () => {
    it('应该计算所有单词的总分', () => {
      expect(calculateTotalScore(mockWords)).toBe(120); // 30 + 40 + 50
    });

    it('应该处理空数组', () => {
      expect(calculateTotalScore([])).toBe(0);
    });
  });

  describe('calculateStars', () => {
    it('应该根据时间返回正确的星级', () => {
      // 2分钟内三星
      expect(calculateStars(60)).toBe(3);
      expect(calculateStars(120)).toBe(3);
      
      // 2-3分钟两星
      expect(calculateStars(121)).toBe(2);
      expect(calculateStars(180)).toBe(2);
      
      // 超过3分钟一星
      expect(calculateStars(181)).toBe(1);
      expect(calculateStars(300)).toBe(1);
    });
  });

  describe('calculatePKScore', () => {
    it('应该正确计算胜利得分', () => {
      // 5个单词 * 10分 + 胜利奖励3分
      expect(calculatePKScore(5, 'win')).toBe(53);
    });

    it('应该正确计算平局得分', () => {
      // 5个单词 * 10分 + 平局奖励1分
      expect(calculatePKScore(5, 'draw')).toBe(51);
    });

    it('应该正确计算失败得分', () => {
      // 5个单词 * 10分，无额外奖励
      expect(calculatePKScore(5, 'lose')).toBe(50);
    });
  });

  describe('calculateCampaignResult', () => {
    it('应该正确计算三星结果', () => {
      const result = calculateCampaignResult(mockWords, 100);
      expect(result.stars).toBe(3);
      expect(result.bonus).toBe(60); // 120 * 0.5
      expect(result.score).toBe(180); // 120 + 60
    });

    it('应该正确计算两星结果', () => {
      const result = calculateCampaignResult(mockWords, 150);
      expect(result.stars).toBe(2);
      expect(result.bonus).toBe(24); // 120 * 0.2
      expect(result.score).toBe(144); // 120 + 24
    });

    it('应该正确计算一星结果', () => {
      const result = calculateCampaignResult(mockWords, 300);
      expect(result.stars).toBe(1);
      expect(result.bonus).toBe(0);
      expect(result.score).toBe(120);
    });
  });

  describe('formatScore', () => {
    it('应该正确格式化分数', () => {
      expect(formatScore(0)).toBe('0');
      expect(formatScore(1000)).toBe('1,000');
      expect(formatScore(1234567)).toBe('1,234,567');
    });
  });

  describe('getStarsDescription', () => {
    it('应该返回正确的描述', () => {
      expect(getStarsDescription(3)).toBe('完美！');
      expect(getStarsDescription(2)).toBe('优秀！');
      expect(getStarsDescription(1)).toBe('及格');
      expect(getStarsDescription(0)).toBe('');
    });
  });

  describe('getStarsEmoji', () => {
    it('应该返回正确的星级 emoji', () => {
      expect(getStarsEmoji(0)).toBe('');
      expect(getStarsEmoji(1)).toBe('⭐');
      expect(getStarsEmoji(2)).toBe('⭐⭐');
      expect(getStarsEmoji(3)).toBe('⭐⭐⭐');
      expect(getStarsEmoji(5)).toBe('⭐⭐⭐'); // 最多3星
    });
  });
});
