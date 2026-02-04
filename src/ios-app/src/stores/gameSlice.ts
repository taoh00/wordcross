/**
 * 游戏状态管理
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { staticApi, gameApi } from '../api';

interface Word {
  id: number;
  word: string;
  definition: string;
  direction: 'across' | 'down';
  start_row: number;
  start_col: number;
  length: number;
}

interface Puzzle {
  grid_size: number;
  cells: (string | null)[][];
  words: Word[];
  prefilled: Record<string, string>;
}

interface GameState {
  // 游戏模式
  mode: 'campaign' | 'endless' | 'timed' | null;
  
  // 词库
  vocabGroup: string;
  vocabGroupName: string;
  
  // 关卡
  currentLevel: number;
  maxLevel: number;
  
  // 谜题
  puzzle: Puzzle | null;
  
  // 用户答案
  userAnswers: Record<string, string>;
  
  // 已完成单词
  completedWords: number[];
  
  // 当前选中
  selectedCell: { row: number; col: number } | null;
  selectedWord: Word | null;
  
  // 计分
  score: number;
  stars: number;
  
  // 计时
  timer: number;
  timerRunning: boolean;
  
  // 状态
  loading: boolean;
  error: string | null;
  gameCompleted: boolean;
}

const initialState: GameState = {
  mode: null,
  vocabGroup: 'grade3_1',
  vocabGroupName: '三年级上册',
  currentLevel: 1,
  maxLevel: 81,
  puzzle: null,
  userAnswers: {},
  completedWords: [],
  selectedCell: null,
  selectedWord: null,
  score: 0,
  stars: 0,
  timer: 0,
  timerRunning: false,
  loading: false,
  error: null,
  gameCompleted: false,
};

// 异步 thunks

/** 加载关卡 */
export const loadLevel = createAsyncThunk(
  'game/loadLevel',
  async ({ group, level }: { group: string; level: number }) => {
    const puzzle = await staticApi.getLevel(group, level);
    return { puzzle, level };
  }
);

/** 加载词库信息 */
export const loadVocabMeta = createAsyncThunk(
  'game/loadVocabMeta',
  async (group: string) => {
    const meta = await staticApi.getMeta(group);
    return {
      group: meta.group_code,
      groupName: meta.group_name,
      levelCount: meta.level_count,
    };
  }
);

/** 提交游戏结果 */
export const submitGame = createAsyncThunk(
  'game/submit',
  async (data: {
    mode: string;
    group: string;
    score: number;
    wordsCount: number;
    levelReached: number;
    duration?: number;
    result?: string;
  }) => {
    await gameApi.submit({
      game_mode: data.mode,
      vocab_group: data.group,
      score: data.score,
      words_count: data.wordsCount,
      level_reached: data.levelReached,
      duration_seconds: data.duration,
      result: data.result,
    });
    return true;
  }
);

/** 生成奖励 */
export const generateReward = createAsyncThunk(
  'game/generateReward',
  async ({ mode, level }: { mode: string; level?: number }) => {
    const result = await gameApi.generateReward(mode, level);
    return result.rewards;
  }
);

/** 领取奖励 */
export const claimReward = createAsyncThunk(
  'game/claimReward',
  async (rewards: Array<{ type: string; value: number }>) => {
    await gameApi.claimReward(rewards);
    return true;
  }
);

// 辅助函数

/** 检查单词是否完成 */
function checkWordComplete(
  word: Word,
  userAnswers: Record<string, string>,
  puzzle: Puzzle
): boolean {
  for (let i = 0; i < word.length; i++) {
    const row = word.direction === 'across' ? word.start_row : word.start_row + i;
    const col = word.direction === 'across' ? word.start_col + i : word.start_col;
    const key = `${row}-${col}`;
    
    // 检查预填字母
    if (puzzle.prefilled[key]) continue;
    
    // 检查用户输入
    const userLetter = userAnswers[key]?.toUpperCase();
    const correctLetter = word.word[i]?.toUpperCase();
    
    if (!userLetter || userLetter !== correctLetter) {
      return false;
    }
  }
  return true;
}

/** 计算星级（1分钟模式，30秒内三星，45秒内二星） */
function calculateStars(seconds: number): number {
  if (seconds <= 30) return 3;
  if (seconds <= 45) return 2;
  return 1;
}

// Slice
const gameSlice = createSlice({
  name: 'game',
  initialState,
  reducers: {
    // 设置游戏模式
    setMode: (state, action: PayloadAction<'campaign' | 'endless' | 'timed' | 'pk'>) => {
      state.mode = action.payload;
    },
    
    // 设置词库
    setVocabGroup: (state, action: PayloadAction<{ code: string; name: string }>) => {
      state.vocabGroup = action.payload.code;
      state.vocabGroupName = action.payload.name;
    },
    
    // 设置当前关卡
    setCurrentLevel: (state, action: PayloadAction<number>) => {
      state.currentLevel = action.payload;
    },
    
    // 选择格子
    selectCell: (state, action: PayloadAction<{ row: number; col: number } | null>) => {
      state.selectedCell = action.payload;
      
      // 自动选择包含此格子的单词
      if (action.payload && state.puzzle) {
        const { row, col } = action.payload;
        const word = state.puzzle.words.find(w => {
          if (w.direction === 'across') {
            return row === w.start_row && col >= w.start_col && col < w.start_col + w.length;
          } else {
            return col === w.start_col && row >= w.start_row && row < w.start_row + w.length;
          }
        });
        state.selectedWord = word || null;
      }
    },
    
    // 选择单词
    selectWord: (state, action: PayloadAction<Word | null>) => {
      state.selectedWord = action.payload;
      
      // 自动选择单词的第一个格子
      if (action.payload) {
        state.selectedCell = {
          row: action.payload.start_row,
          col: action.payload.start_col,
        };
      }
    },
    
    // 输入字母
    inputLetter: (state, action: PayloadAction<string>) => {
      if (!state.selectedCell || !state.puzzle) return;
      
      const { row, col } = state.selectedCell;
      const key = `${row}-${col}`;
      
      // 不能修改预填字母
      if (state.puzzle.prefilled[key]) return;
      
      // 更新答案
      state.userAnswers[key] = action.payload.toUpperCase();
      
      // 检查所有单词完成状态
      state.puzzle.words.forEach(word => {
        const isComplete = checkWordComplete(word, state.userAnswers, state.puzzle!);
        const wasComplete = state.completedWords.includes(word.id);
        
        if (isComplete && !wasComplete) {
          state.completedWords.push(word.id);
          state.score += word.length * 10;
        }
      });
      
      // 检查游戏是否完成
      if (state.completedWords.length === state.puzzle.words.length) {
        state.gameCompleted = true;
        state.timerRunning = false;
        state.stars = calculateStars(state.timer);
      }
      
      // 自动移动到下一个格子
      if (state.selectedWord) {
        const word = state.selectedWord;
        const isAcross = word.direction === 'across';
        
        let nextRow = row;
        let nextCol = col;
        
        if (isAcross) {
          nextCol = col + 1;
          if (nextCol >= word.start_col + word.length) {
            nextCol = word.start_col; // 回到开头
          }
        } else {
          nextRow = row + 1;
          if (nextRow >= word.start_row + word.length) {
            nextRow = word.start_row; // 回到开头
          }
        }
        
        // 跳过预填字母
        const nextKey = `${nextRow}-${nextCol}`;
        if (!state.puzzle.prefilled[nextKey]) {
          state.selectedCell = { row: nextRow, col: nextCol };
        }
      }
    },
    
    // 删除字母
    deleteLetter: (state) => {
      if (!state.selectedCell || !state.puzzle) return;
      
      const { row, col } = state.selectedCell;
      const key = `${row}-${col}`;
      
      // 不能删除预填字母
      if (state.puzzle.prefilled[key]) return;
      
      // 删除答案
      delete state.userAnswers[key];
      
      // 更新完成状态
      state.puzzle.words.forEach(word => {
        const isComplete = checkWordComplete(word, state.userAnswers, state.puzzle!);
        const index = state.completedWords.indexOf(word.id);
        
        if (!isComplete && index !== -1) {
          state.completedWords.splice(index, 1);
        }
      });
      
      state.gameCompleted = false;
    },
    
    // 使用提示
    useHint: (state) => {
      if (!state.selectedCell || !state.selectedWord || !state.puzzle) return;
      
      const word = state.selectedWord;
      const { row, col } = state.selectedCell;
      
      // 计算字母索引
      let letterIndex: number;
      if (word.direction === 'across') {
        letterIndex = col - word.start_col;
      } else {
        letterIndex = row - word.start_row;
      }
      
      // 填入正确字母
      const correctLetter = word.word[letterIndex];
      if (correctLetter) {
        const key = `${row}-${col}`;
        state.userAnswers[key] = correctLetter.toUpperCase();
      }
    },
    
    // 计时器增加
    tickTimer: (state) => {
      if (state.timerRunning) {
        state.timer += 1;
      }
    },
    
    // 开始计时
    startTimer: (state) => {
      state.timerRunning = true;
    },
    
    // 停止计时
    stopTimer: (state) => {
      state.timerRunning = false;
    },
    
    // 重置游戏
    resetGame: (state) => {
      state.userAnswers = {};
      state.completedWords = [];
      state.selectedCell = null;
      state.selectedWord = null;
      state.score = 0;
      state.stars = 0;
      state.timer = 0;
      state.timerRunning = false;
      state.gameCompleted = false;
    },
    
    // 清除错误
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // loadLevel
      .addCase(loadLevel.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loadLevel.fulfilled, (state, action) => {
        state.loading = false;
        state.puzzle = action.payload.puzzle as Puzzle;
        state.currentLevel = action.payload.level;
        state.userAnswers = {};
        state.completedWords = [];
        state.selectedCell = null;
        state.selectedWord = null;
        state.score = 0;
        state.timer = 0;
        state.gameCompleted = false;
      })
      .addCase(loadLevel.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '加载关卡失败';
      })
      
      // loadVocabMeta
      .addCase(loadVocabMeta.fulfilled, (state, action) => {
        state.vocabGroup = action.payload.group;
        state.vocabGroupName = action.payload.groupName;
        state.maxLevel = action.payload.levelCount;
      });
  },
});

export const {
  setMode,
  setVocabGroup,
  setCurrentLevel,
  selectCell,
  selectWord,
  inputLetter,
  deleteLetter,
  useHint,
  tickTimer,
  startTimer,
  stopTimer,
  resetGame,
  clearError,
} = gameSlice.actions;

export default gameSlice.reducer;
