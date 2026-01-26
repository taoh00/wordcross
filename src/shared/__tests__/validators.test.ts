/**
 * 验证工具单元测试
 */

import {
  isValidNickname,
  isValidLetter,
  isValidWord,
  isValidUserId,
  isValidLevel,
  isValidEnergy,
  sanitizeInput,
  normalizeWord,
} from '../utils/validators';

describe('validators', () => {
  describe('isValidNickname', () => {
    it('应该接受有效的昵称', () => {
      expect(isValidNickname('张三')).toBe(true);
      expect(isValidNickname('A')).toBe(true);
      expect(isValidNickname('12345678901234567890')).toBe(true); // 20字符
    });

    it('应该拒绝无效的昵称', () => {
      expect(isValidNickname('')).toBe(false);
      expect(isValidNickname('   ')).toBe(false);
      expect(isValidNickname('123456789012345678901')).toBe(false); // 21字符
    });
  });

  describe('isValidLetter', () => {
    it('应该接受有效的字母', () => {
      expect(isValidLetter('A')).toBe(true);
      expect(isValidLetter('z')).toBe(true);
    });

    it('应该拒绝无效的输入', () => {
      expect(isValidLetter('')).toBe(false);
      expect(isValidLetter('AB')).toBe(false);
      expect(isValidLetter('1')).toBe(false);
      expect(isValidLetter('中')).toBe(false);
    });
  });

  describe('isValidWord', () => {
    it('应该接受有效的单词', () => {
      expect(isValidWord('CAT')).toBe(true);
      expect(isValidWord('hello')).toBe(true);
      expect(isValidWord('MixedCase')).toBe(true);
    });

    it('应该拒绝无效的单词', () => {
      expect(isValidWord('')).toBe(false);
      expect(isValidWord('cat1')).toBe(false);
      expect(isValidWord('cat-dog')).toBe(false);
      expect(isValidWord('cat dog')).toBe(false);
    });
  });

  describe('isValidUserId', () => {
    it('应该接受有效的 UUID', () => {
      expect(isValidUserId('550e8400-e29b-41d4-a716-446655440000')).toBe(true);
      expect(isValidUserId('6ba7b810-9dad-41d4-80b4-00c04fd430c8')).toBe(true);
    });

    it('应该拒绝无效的 UUID', () => {
      expect(isValidUserId('')).toBe(false);
      expect(isValidUserId('not-a-uuid')).toBe(false);
      expect(isValidUserId('550e8400-e29b-11d4-a716-446655440000')).toBe(false); // 版本不对
    });
  });

  describe('isValidLevel', () => {
    it('应该接受有效的关卡号', () => {
      expect(isValidLevel(1)).toBe(true);
      expect(isValidLevel(100)).toBe(true);
      expect(isValidLevel(2000)).toBe(true);
    });

    it('应该拒绝无效的关卡号', () => {
      expect(isValidLevel(0)).toBe(false);
      expect(isValidLevel(-1)).toBe(false);
      expect(isValidLevel(2001)).toBe(false);
      expect(isValidLevel(1.5)).toBe(false);
    });

    it('应该支持自定义最大关卡', () => {
      expect(isValidLevel(100, 100)).toBe(true);
      expect(isValidLevel(101, 100)).toBe(false);
    });
  });

  describe('isValidEnergy', () => {
    it('应该接受有效的体力值', () => {
      expect(isValidEnergy(0)).toBe(true);
      expect(isValidEnergy(100)).toBe(true);
      expect(isValidEnergy(200)).toBe(true);
    });

    it('应该拒绝无效的体力值', () => {
      expect(isValidEnergy(-1)).toBe(false);
      expect(isValidEnergy(201)).toBe(false);
      expect(isValidEnergy(50.5)).toBe(false);
    });
  });

  describe('sanitizeInput', () => {
    it('应该移除危险字符', () => {
      expect(sanitizeInput('<script>alert(1)</script>')).toBe('scriptalert(1)/script');
      expect(sanitizeInput('  hello  ')).toBe('hello');
    });
  });

  describe('normalizeWord', () => {
    it('应该转换为大写并去除空白', () => {
      expect(normalizeWord('cat')).toBe('CAT');
      expect(normalizeWord('  hello  ')).toBe('HELLO');
      expect(normalizeWord('MixedCase')).toBe('MIXEDCASE');
    });
  });
});
