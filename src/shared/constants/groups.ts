/**
 * 词库分组配置
 * 三端共用的词库常量
 */

import type { VocabGroup } from '../api/types';

/** 词库分组列表 */
export const VOCAB_GROUPS: VocabGroup[] = [
  {
    code: 'primary',
    name: '小学词汇',
    icon: '📚',
    hasSubGroups: true,
    subGroups: [
      { code: 'primary_all', name: '全部', icon: '📚' },
      { code: 'grade3_1', name: '三年级上册', icon: '🌱' },
      { code: 'grade3_2', name: '三年级下册', icon: '🌿' },
      { code: 'grade4_1', name: '四年级上册', icon: '🌲' },
      { code: 'grade4_2', name: '四年级下册', icon: '🌳' },
      { code: 'grade5_1', name: '五年级上册', icon: '🌴' },
      { code: 'grade5_2', name: '五年级下册', icon: '🌵' },
      { code: 'grade6_1', name: '六年级上册', icon: '🎄' },
      { code: 'grade6_2', name: '六年级下册', icon: '🎋' },
    ],
  },
  {
    code: 'junior',
    name: '初中词汇',
    icon: '📖',
    hasSubGroups: true,
    subGroups: [
      { code: 'junior_all', name: '全部', icon: '📖' },
      { code: 'junior7_1', name: '七年级上册', icon: '🌱' },
      { code: 'junior7_2', name: '七年级下册', icon: '🌿' },
      { code: 'junior8_1', name: '八年级上册', icon: '🌲' },
      { code: 'junior8_2', name: '八年级下册', icon: '🌳' },
      { code: 'junior9', name: '九年级全册', icon: '🌴' },
    ],
  },
  {
    code: 'senior',
    name: '高中词汇',
    icon: '📕',
    hasSubGroups: true,
    subGroups: [
      { code: 'senior_all', name: '全部', icon: '📕' },
      { code: 'senior1', name: '必修1', icon: '📗' },
      { code: 'senior2', name: '必修2', icon: '📘' },
      { code: 'senior3', name: '必修3', icon: '📙' },
      { code: 'senior4', name: '必修4', icon: '📔' },
      { code: 'senior5', name: '必修5', icon: '📓' },
    ],
  },
  { code: 'ket', name: 'KET考试', icon: '🎯' },
  { code: 'pet', name: 'PET考试', icon: '🎓' },
  { code: 'cet4', name: '大学四级', icon: '🏛️' },
  { code: 'cet6', name: '大学六级', icon: '🎖️' },
  { code: 'postgrad', name: '考研词汇', icon: '🔬' },
  { code: 'ielts', name: '雅思', icon: '✈️' },
  { code: 'toefl', name: '托福', icon: '🗽' },
  { code: 'gre', name: 'GRE', icon: '🎩' },
];

/** 所有词库代码（扁平化） */
export const ALL_GROUP_CODES: string[] = [
  // 小学
  'grade3_1', 'grade3_2', 'grade4_1', 'grade4_2',
  'grade5_1', 'grade5_2', 'grade6_1', 'grade6_2',
  'primary_all',
  // 初中
  'junior7_1', 'junior7_2', 'junior8_1', 'junior8_2', 'junior9',
  'junior', 'junior_all',
  // 高中
  'senior1', 'senior2', 'senior3', 'senior4', 'senior5',
  'senior', 'senior_all',
  // 考试
  'ket', 'pet', 'cet4', 'cet6', 'postgrad', 'ielts', 'toefl', 'gre',
];

/** 词库代码到名称的映射 */
export const GROUP_NAMES: Record<string, string> = {
  // 小学
  grade3_1: '三年级上册',
  grade3_2: '三年级下册',
  grade4_1: '四年级上册',
  grade4_2: '四年级下册',
  grade5_1: '五年级上册',
  grade5_2: '五年级下册',
  grade6_1: '六年级上册',
  grade6_2: '六年级下册',
  primary_all: '小学全部',
  // 初中
  junior7_1: '七年级上册',
  junior7_2: '七年级下册',
  junior8_1: '八年级上册',
  junior8_2: '八年级下册',
  junior9: '九年级全册',
  junior: '初中词汇',
  junior_all: '初中全部',
  // 高中
  senior1: '必修1',
  senior2: '必修2',
  senior3: '必修3',
  senior4: '必修4',
  senior5: '必修5',
  senior: '高中词汇',
  senior_all: '高中全部',
  // 考试
  ket: 'KET考试',
  pet: 'PET考试',
  cet4: '大学四级',
  cet6: '大学六级',
  postgrad: '考研词汇',
  ielts: '雅思',
  toefl: '托福',
  gre: 'GRE',
};

/** 获取词库名称 */
export function getGroupName(code: string): string {
  return GROUP_NAMES[code] || code;
}

/** 检查是否为有效的词库代码 */
export function isValidGroupCode(code: string): boolean {
  return ALL_GROUP_CODES.includes(code);
}

/** 获取词库分类（小学/初中/高中/考试） */
export function getGroupCategory(code: string): string {
  if (code.startsWith('grade') || code === 'primary_all') return '小学';
  if (code.startsWith('junior')) return '初中';
  if (code.startsWith('senior')) return '高中';
  if (['ket', 'pet', 'cet4', 'cet6', 'postgrad', 'ielts', 'toefl', 'gre'].includes(code)) {
    return '考试';
  }
  return '其他';
}
