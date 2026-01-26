/**
 * 格式化工具函数
 * 三端共用的显示格式化
 */

/**
 * 格式化时间显示
 * @param seconds 秒数
 * @returns "MM:SS" 格式
 */
export function formatTime(seconds: number): string {
  const mins = Math.floor(Math.abs(seconds) / 60);
  const secs = Math.abs(seconds) % 60;
  const sign = seconds < 0 ? '-' : '';
  return `${sign}${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * 格式化时间显示（带小时）
 * @param seconds 秒数
 * @returns "HH:MM:SS" 或 "MM:SS" 格式
 */
export function formatTimeLong(seconds: number): string {
  const hours = Math.floor(Math.abs(seconds) / 3600);
  const mins = Math.floor((Math.abs(seconds) % 3600) / 60);
  const secs = Math.abs(seconds) % 60;

  if (hours > 0) {
    return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * 格式化日期显示
 * @param dateStr ISO 日期字符串
 * @returns 本地化日期 "YYYY-MM-DD"
 */
export function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

/**
 * 格式化日期时间显示
 * @param dateStr ISO 日期字符串
 * @returns 本地化日期时间 "YYYY-MM-DD HH:MM"
 */
export function formatDateTime(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

/**
 * 格式化数字（带千分位）
 * @param num 数字
 * @returns 格式化字符串
 */
export function formatNumber(num: number): string {
  return num.toLocaleString('zh-CN');
}

/**
 * 格式化百分比
 * @param value 值 (0-1 或 0-100)
 * @param decimal 小数位数
 * @returns 百分比字符串
 */
export function formatPercent(value: number, decimal: number = 1): string {
  const percent = value > 1 ? value : value * 100;
  return `${percent.toFixed(decimal)}%`;
}

/**
 * 格式化排名显示
 * @param rank 排名
 * @returns 带后缀的排名（中文格式）
 */
export function formatRank(rank: number): string {
  if (rank <= 0) return '-';
  return `第${rank}名`;
}

/**
 * 格式化简短排名
 * @param rank 排名
 * @returns 简短排名 "#1"
 */
export function formatRankShort(rank: number): string {
  if (rank <= 0) return '-';
  return `#${rank}`;
}

/**
 * 截断文本
 * @param text 原文本
 * @param maxLength 最大长度
 * @param suffix 截断后缀
 * @returns 截断后的文本
 */
export function truncateText(
  text: string,
  maxLength: number,
  suffix: string = '...'
): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - suffix.length) + suffix;
}
