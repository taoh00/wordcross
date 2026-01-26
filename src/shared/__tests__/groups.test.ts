/**
 * 词库配置单元测试
 */

import {
  VOCAB_GROUPS,
  ALL_GROUP_CODES,
  GROUP_NAMES,
  getGroupName,
  isValidGroupCode,
  getGroupCategory,
} from '../constants/groups';

describe('groups', () => {
  describe('VOCAB_GROUPS', () => {
    it('应该包含主要词库分类', () => {
      const codes = VOCAB_GROUPS.map((g) => g.code);
      expect(codes).toContain('primary');
      expect(codes).toContain('junior');
      expect(codes).toContain('senior');
      expect(codes).toContain('cet4');
      expect(codes).toContain('gre');
    });

    it('小学词库应该有子分组', () => {
      const primary = VOCAB_GROUPS.find((g) => g.code === 'primary');
      expect(primary?.hasSubGroups).toBe(true);
      expect(primary?.subGroups?.length).toBeGreaterThan(0);
    });
  });

  describe('ALL_GROUP_CODES', () => {
    it('应该包含所有词库代码', () => {
      expect(ALL_GROUP_CODES).toContain('grade3_1');
      expect(ALL_GROUP_CODES).toContain('junior');
      expect(ALL_GROUP_CODES).toContain('senior1');
      expect(ALL_GROUP_CODES).toContain('cet4');
      expect(ALL_GROUP_CODES).toContain('gre');
    });

    it('应该有正确的数量', () => {
      expect(ALL_GROUP_CODES.length).toBeGreaterThan(20);
    });
  });

  describe('getGroupName', () => {
    it('应该返回正确的词库名称', () => {
      expect(getGroupName('grade3_1')).toBe('三年级上册');
      expect(getGroupName('junior')).toBe('初中词汇');
      expect(getGroupName('cet4')).toBe('大学四级');
      expect(getGroupName('gre')).toBe('GRE');
    });

    it('应该处理未知代码', () => {
      expect(getGroupName('unknown')).toBe('unknown');
    });
  });

  describe('isValidGroupCode', () => {
    it('应该正确验证词库代码', () => {
      expect(isValidGroupCode('grade3_1')).toBe(true);
      expect(isValidGroupCode('junior')).toBe(true);
      expect(isValidGroupCode('cet4')).toBe(true);
      expect(isValidGroupCode('unknown')).toBe(false);
      expect(isValidGroupCode('')).toBe(false);
    });
  });

  describe('getGroupCategory', () => {
    it('应该返回正确的分类', () => {
      expect(getGroupCategory('grade3_1')).toBe('小学');
      expect(getGroupCategory('primary_all')).toBe('小学');
      expect(getGroupCategory('junior')).toBe('初中');
      expect(getGroupCategory('junior7_1')).toBe('初中');
      expect(getGroupCategory('senior')).toBe('高中');
      expect(getGroupCategory('senior1')).toBe('高中');
      expect(getGroupCategory('cet4')).toBe('考试');
      expect(getGroupCategory('gre')).toBe('考试');
    });

    it('应该处理未知代码', () => {
      expect(getGroupCategory('unknown')).toBe('其他');
    });
  });
});
