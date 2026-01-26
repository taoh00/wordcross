/**
 * 游戏核心逻辑单元测试
 */

import {
  checkWord,
  getWordCells,
  isCellInWord,
  getWordsAtCell,
  isLevelComplete,
  calculateProgress,
  formatTimer,
  cellKey,
  parseKey,
  isCellBlocked,
  getNextCell,
  getPrevCell,
  initGameState,
  groupWordsByDirection,
} from '../logic/gameLogic';
import type { Puzzle, Word } from '../api/types';

// 测试用的模拟数据
const mockPuzzle: Puzzle = {
  grid_size: 5,
  cells: [
    ['C', 'A', 'T', null, null],
    [null, null, 'E', null, null],
    [null, null, 'S', null, null],
    [null, null, 'T', null, null],
    [null, null, null, null, null],
  ],
  words: [
    {
      id: 1,
      word: 'CAT',
      definition: '猫',
      direction: 'across',
      start_row: 0,
      start_col: 0,
      length: 3,
      clue_number: 1,
    },
    {
      id: 2,
      word: 'TEST',
      definition: '测试',
      direction: 'down',
      start_row: 0,
      start_col: 2,
      length: 4,
      clue_number: 2,
    },
  ],
  prefilled: {
    '0-0': 'C',
  },
};

describe('gameLogic', () => {
  describe('checkWord', () => {
    it('应该正确检测完全匹配的单词', () => {
      const userAnswers = {
        '0-0': 'C',
        '0-1': 'A',
        '0-2': 'T',
      };
      expect(checkWord(mockPuzzle, userAnswers, 1)).toBe(true);
    });

    it('应该正确检测不匹配的单词', () => {
      const userAnswers = {
        '0-0': 'C',
        '0-1': 'A',
        '0-2': 'R', // 错误
      };
      expect(checkWord(mockPuzzle, userAnswers, 1)).toBe(false);
    });

    it('应该正确处理大小写', () => {
      const userAnswers = {
        '0-0': 'c',
        '0-1': 'a',
        '0-2': 't',
      };
      expect(checkWord(mockPuzzle, userAnswers, 1)).toBe(true);
    });

    it('应该正确检测纵向单词', () => {
      const userAnswers = {
        '0-2': 'T',
        '1-2': 'E',
        '2-2': 'S',
        '3-2': 'T',
      };
      expect(checkWord(mockPuzzle, userAnswers, 2)).toBe(true);
    });

    it('应该处理不存在的单词 ID', () => {
      expect(checkWord(mockPuzzle, {}, 999)).toBe(false);
    });
  });

  describe('getWordCells', () => {
    it('应该返回横向单词的所有格子', () => {
      const word = mockPuzzle.words[0];
      const cells = getWordCells(word);
      expect(cells).toEqual([
        { row: 0, col: 0 },
        { row: 0, col: 1 },
        { row: 0, col: 2 },
      ]);
    });

    it('应该返回纵向单词的所有格子', () => {
      const word = mockPuzzle.words[1];
      const cells = getWordCells(word);
      expect(cells).toEqual([
        { row: 0, col: 2 },
        { row: 1, col: 2 },
        { row: 2, col: 2 },
        { row: 3, col: 2 },
      ]);
    });
  });

  describe('isCellInWord', () => {
    it('应该正确判断格子是否在横向单词中', () => {
      const word = mockPuzzle.words[0];
      expect(isCellInWord(word, 0, 0)).toBe(true);
      expect(isCellInWord(word, 0, 1)).toBe(true);
      expect(isCellInWord(word, 0, 2)).toBe(true);
      expect(isCellInWord(word, 0, 3)).toBe(false);
      expect(isCellInWord(word, 1, 0)).toBe(false);
    });

    it('应该正确判断格子是否在纵向单词中', () => {
      const word = mockPuzzle.words[1];
      expect(isCellInWord(word, 0, 2)).toBe(true);
      expect(isCellInWord(word, 1, 2)).toBe(true);
      expect(isCellInWord(word, 4, 2)).toBe(false);
      expect(isCellInWord(word, 0, 3)).toBe(false);
    });
  });

  describe('getWordsAtCell', () => {
    it('应该返回包含指定格子的所有单词', () => {
      // (0, 2) 是两个单词的交叉点
      const words = getWordsAtCell(mockPuzzle, 0, 2);
      expect(words.length).toBe(2);
      expect(words.map((w) => w.word)).toContain('CAT');
      expect(words.map((w) => w.word)).toContain('TEST');
    });

    it('应该返回空数组如果格子不在任何单词中', () => {
      const words = getWordsAtCell(mockPuzzle, 4, 4);
      expect(words.length).toBe(0);
    });
  });

  describe('isLevelComplete', () => {
    it('应该在所有单词完成时返回 true', () => {
      expect(isLevelComplete(mockPuzzle, mockPuzzle.words)).toBe(true);
    });

    it('应该在部分单词完成时返回 false', () => {
      expect(isLevelComplete(mockPuzzle, [mockPuzzle.words[0]])).toBe(false);
    });

    it('应该在没有单词完成时返回 false', () => {
      expect(isLevelComplete(mockPuzzle, [])).toBe(false);
    });
  });

  describe('calculateProgress', () => {
    it('应该正确计算进度百分比', () => {
      expect(calculateProgress(mockPuzzle, [])).toBe(0);
      expect(calculateProgress(mockPuzzle, [mockPuzzle.words[0]])).toBe(50);
      expect(calculateProgress(mockPuzzle, mockPuzzle.words)).toBe(100);
    });

    it('应该处理空谜题', () => {
      const emptyPuzzle = { ...mockPuzzle, words: [] };
      expect(calculateProgress(emptyPuzzle, [])).toBe(0);
    });
  });

  describe('formatTimer', () => {
    it('应该正确格式化时间', () => {
      expect(formatTimer(0)).toBe('00:00');
      expect(formatTimer(59)).toBe('00:59');
      expect(formatTimer(60)).toBe('01:00');
      expect(formatTimer(125)).toBe('02:05');
      expect(formatTimer(3661)).toBe('61:01');
    });
  });

  describe('cellKey and parseKey', () => {
    it('应该正确生成和解析格子键名', () => {
      expect(cellKey(0, 0)).toBe('0-0');
      expect(cellKey(5, 10)).toBe('5-10');
      expect(parseKey('0-0')).toEqual({ row: 0, col: 0 });
      expect(parseKey('5-10')).toEqual({ row: 5, col: 10 });
    });
  });

  describe('isCellBlocked', () => {
    it('应该正确判断阻挡格子', () => {
      expect(isCellBlocked(mockPuzzle, 0, 0)).toBe(false);
      expect(isCellBlocked(mockPuzzle, 0, 3)).toBe(true); // null
      expect(isCellBlocked(mockPuzzle, -1, 0)).toBe(true); // 越界
      expect(isCellBlocked(mockPuzzle, 0, 5)).toBe(true); // 越界
    });
  });

  describe('getNextCell', () => {
    it('应该返回横向的下一个格子', () => {
      expect(getNextCell(mockPuzzle, 0, 0, 'across')).toEqual({ row: 0, col: 1 });
    });

    it('应该返回纵向的下一个格子', () => {
      expect(getNextCell(mockPuzzle, 0, 2, 'down')).toEqual({ row: 1, col: 2 });
    });

    it('应该在遇到阻挡时返回 null', () => {
      expect(getNextCell(mockPuzzle, 0, 2, 'across')).toBe(null); // (0,3) 是 null
    });
  });

  describe('getPrevCell', () => {
    it('应该返回横向的上一个格子', () => {
      expect(getPrevCell(mockPuzzle, 0, 1, 'across')).toEqual({ row: 0, col: 0 });
    });

    it('应该返回纵向的上一个格子', () => {
      expect(getPrevCell(mockPuzzle, 1, 2, 'down')).toEqual({ row: 0, col: 2 });
    });

    it('应该在越界时返回 null', () => {
      expect(getPrevCell(mockPuzzle, 0, 0, 'across')).toBe(null);
    });
  });

  describe('initGameState', () => {
    it('应该正确初始化游戏状态', () => {
      const state = initGameState(mockPuzzle);
      expect(state.puzzle).toBe(mockPuzzle);
      expect(state.userAnswers).toEqual({ '0-0': 'C' }); // 预填字母
      expect(state.completedWords).toEqual([]);
      expect(state.score).toBe(0);
      expect(state.timer).toBe(0);
      expect(state.isPlaying).toBe(false);
    });
  });

  describe('groupWordsByDirection', () => {
    it('应该正确按方向分组单词', () => {
      const grouped = groupWordsByDirection(mockPuzzle.words);
      expect(grouped.across.length).toBe(1);
      expect(grouped.down.length).toBe(1);
      expect(grouped.across[0].word).toBe('CAT');
      expect(grouped.down[0].word).toBe('TEST');
    });
  });
});
