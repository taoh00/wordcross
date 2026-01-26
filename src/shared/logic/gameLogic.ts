/**
 * 游戏核心逻辑
 * 三端共用的纯函数，不依赖任何平台 API
 */

import type { Puzzle, Word, WordDirection, GameState } from '../api/types';

/**
 * 检查单词是否正确
 * @param puzzle 谜题数据
 * @param userAnswers 用户答案 { "row-col": "A" }
 * @param wordId 要检查的单词 ID
 * @returns 是否正确
 */
export function checkWord(
  puzzle: Puzzle,
  userAnswers: Record<string, string>,
  wordId: number
): boolean {
  const word = puzzle.words.find((w) => w.id === wordId);
  if (!word) return false;

  let userWord = '';
  for (let i = 0; i < word.length; i++) {
    const row = word.direction === 'across' ? word.start_row : word.start_row + i;
    const col = word.direction === 'across' ? word.start_col + i : word.start_col;
    const key = `${row}-${col}`;
    userWord += userAnswers[key] || '';
  }

  return userWord.toUpperCase() === word.word.toUpperCase();
}

/**
 * 获取单词所占的格子坐标
 * @param word 单词信息
 * @returns 格子坐标数组 [{ row, col }, ...]
 */
export function getWordCells(word: Word): Array<{ row: number; col: number }> {
  const cells: Array<{ row: number; col: number }> = [];
  for (let i = 0; i < word.length; i++) {
    if (word.direction === 'across') {
      cells.push({ row: word.start_row, col: word.start_col + i });
    } else {
      cells.push({ row: word.start_row + i, col: word.start_col });
    }
  }
  return cells;
}

/**
 * 检查格子是否属于某个单词
 * @param word 单词信息
 * @param row 行号
 * @param col 列号
 * @returns 是否属于该单词
 */
export function isCellInWord(word: Word, row: number, col: number): boolean {
  if (word.direction === 'across') {
    return (
      row === word.start_row &&
      col >= word.start_col &&
      col < word.start_col + word.length
    );
  } else {
    return (
      col === word.start_col &&
      row >= word.start_row &&
      row < word.start_row + word.length
    );
  }
}

/**
 * 获取包含指定格子的所有单词
 * @param puzzle 谜题数据
 * @param row 行号
 * @param col 列号
 * @returns 包含该格子的单词列表
 */
export function getWordsAtCell(puzzle: Puzzle, row: number, col: number): Word[] {
  return puzzle.words.filter((word) => isCellInWord(word, row, col));
}

/**
 * 检查谜题是否完成
 * @param puzzle 谜题数据
 * @param completedWords 已完成的单词列表
 * @returns 是否完成
 */
export function isLevelComplete(puzzle: Puzzle, completedWords: Word[]): boolean {
  return completedWords.length === puzzle.words.length;
}

/**
 * 计算完成进度（百分比）
 * @param puzzle 谜题数据
 * @param completedWords 已完成的单词列表
 * @returns 进度百分比 0-100
 */
export function calculateProgress(puzzle: Puzzle, completedWords: Word[]): number {
  if (!puzzle?.words?.length) return 0;
  return Math.round((completedWords.length / puzzle.words.length) * 100);
}

/**
 * 格式化计时器显示
 * @param seconds 秒数
 * @returns 格式化字符串 "MM:SS"
 */
export function formatTimer(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * 构建格子键名
 * @param row 行号
 * @param col 列号
 * @returns 键名 "row-col"
 */
export function cellKey(row: number, col: number): string {
  return `${row}-${col}`;
}

/**
 * 解析格子键名
 * @param key 键名 "row-col"
 * @returns { row, col }
 */
export function parseKey(key: string): { row: number; col: number } {
  const [row, col] = key.split('-').map(Number);
  return { row, col };
}

/**
 * 检查格子是否被阻挡（空白格）
 * @param puzzle 谜题数据
 * @param row 行号
 * @param col 列号
 * @returns 是否被阻挡
 */
export function isCellBlocked(puzzle: Puzzle, row: number, col: number): boolean {
  if (!puzzle?.cells) return true;
  if (row < 0 || row >= puzzle.grid_size) return true;
  if (col < 0 || col >= puzzle.grid_size) return true;
  return puzzle.cells[row][col] === null;
}

/**
 * 获取下一个可输入的格子
 * @param puzzle 谜题数据
 * @param currentRow 当前行
 * @param currentCol 当前列
 * @param direction 当前方向
 * @returns 下一个格子坐标，或 null 如果到末尾
 */
export function getNextCell(
  puzzle: Puzzle,
  currentRow: number,
  currentCol: number,
  direction: WordDirection
): { row: number; col: number } | null {
  let nextRow = currentRow;
  let nextCol = currentCol;

  if (direction === 'across') {
    nextCol++;
  } else {
    nextRow++;
  }

  if (isCellBlocked(puzzle, nextRow, nextCol)) {
    return null;
  }

  return { row: nextRow, col: nextCol };
}

/**
 * 获取上一个可输入的格子
 * @param puzzle 谜题数据
 * @param currentRow 当前行
 * @param currentCol 当前列
 * @param direction 当前方向
 * @returns 上一个格子坐标，或 null 如果到开头
 */
export function getPrevCell(
  puzzle: Puzzle,
  currentRow: number,
  currentCol: number,
  direction: WordDirection
): { row: number; col: number } | null {
  let prevRow = currentRow;
  let prevCol = currentCol;

  if (direction === 'across') {
    prevCol--;
  } else {
    prevRow--;
  }

  if (isCellBlocked(puzzle, prevRow, prevCol)) {
    return null;
  }

  return { row: prevRow, col: prevCol };
}

/**
 * 初始化游戏状态
 * @param puzzle 谜题数据
 * @returns 初始游戏状态
 */
export function initGameState(puzzle: Puzzle): GameState {
  const userAnswers: Record<string, string> = {};

  // 填充预填字母
  if (puzzle.prefilled) {
    for (const [key, letter] of Object.entries(puzzle.prefilled)) {
      userAnswers[key] = letter;
    }
  }

  return {
    puzzle,
    userAnswers,
    completedWords: [],
    score: 0,
    timer: 0,
    isPlaying: false,
  };
}

/**
 * 获取单词起始格子的线索编号
 * @param puzzle 谜题数据
 * @param row 行号
 * @param col 列号
 * @returns 线索编号，如果没有则返回 undefined
 */
export function getClueNumber(
  puzzle: Puzzle,
  row: number,
  col: number
): number | undefined {
  const word = puzzle.words.find(
    (w) => w.start_row === row && w.start_col === col
  );
  return word?.clue_number;
}

/**
 * 按方向分组单词
 * @param words 单词列表
 * @returns { across: Word[], down: Word[] }
 */
export function groupWordsByDirection(words: Word[]): {
  across: Word[];
  down: Word[];
} {
  return {
    across: words
      .filter((w) => w.direction === 'across')
      .sort((a, b) => (a.clue_number || 0) - (b.clue_number || 0)),
    down: words
      .filter((w) => w.direction === 'down')
      .sort((a, b) => (a.clue_number || 0) - (b.clue_number || 0)),
  };
}
