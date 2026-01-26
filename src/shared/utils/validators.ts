/**
 * 验证工具函数
 * 三端共用的输入验证
 */

/**
 * 验证用户昵称
 * @param nickname 昵称
 * @returns 是否有效
 */
export function isValidNickname(nickname: string): boolean {
  const trimmed = nickname.trim();
  return trimmed.length >= 1 && trimmed.length <= 20;
}

/**
 * 验证单词字母
 * @param letter 单个字母
 * @returns 是否为有效的英文字母
 */
export function isValidLetter(letter: string): boolean {
  return /^[A-Za-z]$/.test(letter);
}

/**
 * 验证单词
 * @param word 单词
 * @returns 是否为有效的英文单词
 */
export function isValidWord(word: string): boolean {
  return /^[A-Za-z]+$/.test(word);
}

/**
 * 验证用户 ID 格式（UUID）
 * @param id 用户 ID
 * @returns 是否有效
 */
export function isValidUserId(id: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(id);
}

/**
 * 验证关卡号
 * @param level 关卡号
 * @param maxLevel 最大关卡号
 * @returns 是否有效
 */
export function isValidLevel(level: number, maxLevel: number = 2000): boolean {
  return Number.isInteger(level) && level >= 1 && level <= maxLevel;
}

/**
 * 验证体力值
 * @param energy 体力值
 * @param maxEnergy 最大体力值
 * @returns 是否有效
 */
export function isValidEnergy(energy: number, maxEnergy: number = 200): boolean {
  return Number.isInteger(energy) && energy >= 0 && energy <= maxEnergy;
}

/**
 * 清理用户输入（去除非法字符）
 * @param input 用户输入
 * @returns 清理后的字符串
 */
export function sanitizeInput(input: string): string {
  return input.trim().replace(/[<>]/g, '');
}

/**
 * 标准化单词（大写）
 * @param word 单词
 * @returns 大写的单词
 */
export function normalizeWord(word: string): string {
  return word.toUpperCase().trim();
}
