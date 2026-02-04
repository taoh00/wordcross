/**
 * 填字网格组件 (Kawaii Style)
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Dimensions, Platform } from 'react-native';
import { COLORS, SHADOWS, LAYOUT } from '../utils/theme';

interface Word {
  id: number;
  word: string;
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

interface GridProps {
  puzzle: Puzzle;
  userAnswers: Record<string, string>;
  completedWords: number[];
  selectedWord: Word | null;
  onCellPress: (row: number, col: number) => void;
}

const { width: screenWidth } = Dimensions.get('window');
const MAX_GRID_WIDTH = Math.min(screenWidth - 32, 400); // 限制最大宽度，适配iPad

export default function Grid({
  puzzle,
  userAnswers,
  completedWords,
  selectedWord,
  onCellPress,
}: GridProps) {
  const { grid_size, cells, prefilled, words } = puzzle;
  
  // 计算格子大小
  // 留出边距: padding(16) + gap(4 * (size-1))
  const gapSize = 4;
  const totalGap = gapSize * (grid_size - 1);
  const availableWidth = MAX_GRID_WIDTH - 32; // 容器padding
  const cellSize = Math.floor((availableWidth - totalGap) / grid_size);
  
  // 判断格子是否属于选中单词
  const isCellInSelectedWord = (row: number, col: number): boolean => {
    if (!selectedWord) return false;
    
    const { direction, start_row, start_col, length } = selectedWord;
    
    if (direction === 'across') {
      return row === start_row && col >= start_col && col < start_col + length;
    } else {
      return col === start_col && row >= start_row && row < start_row + length;
    }
  };
  
  // 判断格子是否属于已完成单词
  const isCellInCompletedWord = (row: number, col: number): boolean => {
    return words.some((word) => {
      if (!completedWords.includes(word.id)) return false;
      
      const { direction, start_row, start_col, length } = word;
      
      if (direction === 'across') {
        return row === start_row && col >= start_col && col < start_col + length;
      } else {
        return col === start_col && row >= start_row && row < start_row + length;
      }
    });
  };
  
  // 获取格子的线索编号
  const getClueNumber = (row: number, col: number): number | null => {
    const word = words.find(
      (w) => w.start_row === row && w.start_col === col
    );
    return word ? word.id : null;
  };
  
  // 渲染单个格子
  const renderCell = (row: number, col: number) => {
    const key = `${row}-${col}`;
    const cellValue = cells[row]?.[col];
    
    // 空白格子（阻挡格）- 透明或极淡
    if (cellValue === null) {
      return (
        <View
          key={key}
          style={[
            styles.cell,
            styles.blockedCell,
            { width: cellSize, height: cellSize },
          ]}
        />
      );
    }
    
    const isPrefilled = !!prefilled[key];
    const userLetter = userAnswers[key] || '';
    const displayLetter = isPrefilled ? prefilled[key] : userLetter;
    const isSelected = isCellInSelectedWord(row, col);
    const isCompleted = isCellInCompletedWord(row, col);
    const clueNumber = getClueNumber(row, col);
    
    // 动态样式
    const cellStyles = [
      styles.cell,
      { width: cellSize, height: cellSize },
    ];
    
    if (isSelected) cellStyles.push(styles.selectedCell);
    else if (isCompleted) cellStyles.push(styles.completedCell);
    else if (isPrefilled) cellStyles.push(styles.prefilledCell);
    else cellStyles.push(styles.validCell);
    
    return (
      <TouchableOpacity
        key={key}
        style={cellStyles}
        onPress={() => onCellPress(row, col)}
        activeOpacity={0.8}
      >
        {/* 线索编号 */}
        {clueNumber && (
          <Text style={[styles.clueNumber, { fontSize: Math.max(8, cellSize * 0.25) }]}>
            {clueNumber}
          </Text>
        )}
        
        {/* 字母 */}
        <Text
          style={[
            styles.letter,
            { fontSize: cellSize * 0.55 },
            isPrefilled && styles.prefilledLetter,
            isCompleted && styles.completedLetter,
            isSelected && styles.selectedLetter,
          ]}
        >
          {displayLetter}
        </Text>
      </TouchableOpacity>
    );
  };
  
  return (
    <View style={styles.gridContainer}>
      {Array.from({ length: grid_size }).map((_, row) => (
        <View key={row} style={styles.row}>
          {Array.from({ length: grid_size }).map((_, col) => renderCell(row, col))}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  gridContainer: {
    backgroundColor: COLORS.white,
    padding: 16,
    borderRadius: LAYOUT.radiusLg,
    // 3D Shadow
    shadowColor: COLORS.blue.main,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
    borderWidth: 2,
    borderColor: COLORS.blue.light,
    alignSelf: 'center',
  },
  row: {
    flexDirection: 'row',
    marginBottom: 4,
  },
  cell: {
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 2,
    borderRadius: 8, // 圆角格子
    position: 'relative',
  },
  blockedCell: {
    backgroundColor: 'transparent',
  },
  validCell: {
    backgroundColor: COLORS.white,
    borderWidth: 2,
    borderColor: COLORS.border,
    // Soft inner shadow effect via border
  },
  selectedCell: {
    backgroundColor: COLORS.yellow.light,
    borderColor: COLORS.yellow.dark,
    borderWidth: 2,
    transform: [{ translateY: -2 }], // 浮起效果
    zIndex: 10,
    ...Platform.select({
      ios: {
        shadowColor: COLORS.yellow.dark,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.5,
        shadowRadius: 2,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  completedCell: {
    backgroundColor: COLORS.mint.light,
    borderColor: COLORS.mint.main,
    borderWidth: 2,
  },
  prefilledCell: {
    backgroundColor: '#FDFDFD', // Cool gray 50
    borderColor: '#FFB6C1', // Cool gray 200
    borderWidth: 2,
  },
  clueNumber: {
    position: 'absolute',
    top: 2,
    left: 4,
    color: COLORS.textLight,
    fontWeight: '700',
  },
  letter: {
    fontWeight: '800',
    color: COLORS.textMain,
    textTransform: 'uppercase',
    fontFamily: Platform.OS === 'ios' ? 'Nunito-ExtraBold' : 'sans-serif-black',
  },
  prefilledLetter: {
    color: COLORS.blue.dark,
  },
  completedLetter: {
    color: COLORS.mint.dark,
  },
  selectedLetter: {
    color: '#DAA520', // amber-700
  },
});
