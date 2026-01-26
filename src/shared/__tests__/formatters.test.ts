/**
 * 格式化工具单元测试
 */

import {
  formatTime,
  formatTimeLong,
  formatDate,
  formatDateTime,
  formatNumber,
  formatPercent,
  formatRank,
  formatRankShort,
  truncateText,
} from '../utils/formatters';

describe('formatters', () => {
  describe('formatTime', () => {
    it('应该正确格式化时间', () => {
      expect(formatTime(0)).toBe('00:00');
      expect(formatTime(59)).toBe('00:59');
      expect(formatTime(60)).toBe('01:00');
      expect(formatTime(125)).toBe('02:05');
      expect(formatTime(3661)).toBe('61:01');
    });

    it('应该处理负数', () => {
      expect(formatTime(-60)).toBe('-01:00');
    });
  });

  describe('formatTimeLong', () => {
    it('应该正确格式化短时间', () => {
      expect(formatTimeLong(0)).toBe('00:00');
      expect(formatTimeLong(125)).toBe('02:05');
    });

    it('应该正确格式化长时间（带小时）', () => {
      expect(formatTimeLong(3600)).toBe('1:00:00');
      expect(formatTimeLong(3661)).toBe('1:01:01');
      expect(formatTimeLong(7325)).toBe('2:02:05');
    });
  });

  describe('formatDate', () => {
    it('应该正确格式化日期', () => {
      // 注意：这个测试依赖于本地时区
      const result = formatDate('2026-01-26T12:00:00Z');
      expect(result).toMatch(/2026/);
      expect(result).toMatch(/01/);
    });
  });

  describe('formatNumber', () => {
    it('应该正确格式化数字', () => {
      expect(formatNumber(0)).toBe('0');
      expect(formatNumber(1000)).toBe('1,000');
      expect(formatNumber(1234567)).toBe('1,234,567');
    });
  });

  describe('formatPercent', () => {
    it('应该正确格式化百分比（0-1）', () => {
      expect(formatPercent(0.5)).toBe('50.0%');
      expect(formatPercent(0.123)).toBe('12.3%');
      expect(formatPercent(1)).toBe('100.0%');
    });

    it('应该正确格式化百分比（0-100）', () => {
      expect(formatPercent(50)).toBe('50.0%');
      expect(formatPercent(85.5)).toBe('85.5%');
    });

    it('应该支持自定义小数位', () => {
      expect(formatPercent(0.5555, 2)).toBe('55.55%');
      expect(formatPercent(0.5, 0)).toBe('50%');
    });
  });

  describe('formatRank', () => {
    it('应该正确格式化排名', () => {
      expect(formatRank(1)).toBe('第1名');
      expect(formatRank(10)).toBe('第10名');
      expect(formatRank(100)).toBe('第100名');
    });

    it('应该处理无效排名', () => {
      expect(formatRank(0)).toBe('-');
      expect(formatRank(-1)).toBe('-');
    });
  });

  describe('formatRankShort', () => {
    it('应该正确格式化简短排名', () => {
      expect(formatRankShort(1)).toBe('#1');
      expect(formatRankShort(100)).toBe('#100');
    });

    it('应该处理无效排名', () => {
      expect(formatRankShort(0)).toBe('-');
    });
  });

  describe('truncateText', () => {
    it('应该正确截断文本', () => {
      expect(truncateText('Hello World', 5)).toBe('He...');
      expect(truncateText('Hello', 10)).toBe('Hello');
    });

    it('应该支持自定义后缀', () => {
      expect(truncateText('Hello World', 8, '…')).toBe('Hello W…');
    });
  });
});
