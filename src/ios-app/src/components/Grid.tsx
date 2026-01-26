/**
 * 填字网格组件
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';

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
const MAX_GRID_WIDTH = screenWidth - 32;

export default function Grid({
  puzzle,
  userAnswers,
  completedWords,
  selectedWord,
  onCellPress,
}: GridProps) {
  const { grid_size, cells, prefilled, words } = puzzle;
  
  // 计算格子大小
  const cellSize = Math.min(MAX_GRID_WIDTH / grid_size, 40);
  const gridWidth = cellSize * grid_size;
  
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
    
    // 空白格子（阻挡格）
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
    
    return (
      <TouchableOpacity
        key={key}
        style={[
          styles.cell,
          { width: cellSize, height: cellSize },
          isSelected && styles.selectedCell,
          isCompleted && styles.completedCell,
          isPrefilled && styles.prefilledCell,
        ]}
        onPress={() => onCellPress(row, col)}
        activeOpacity={0.7}
      >
        {/* 线索编号 */}
        {clueNumber && (
          <Text style={[styles.clueNumber, { fontSize: cellSize * 0.25 }]}>
            {clueNumber}
          </Text>
        )}
        
        {/* 字母 */}
        <Text
          style={[
            styles.letter,
            { fontSize: cellSize * 0.5 },
            isPrefilled && styles.prefilledLetter,
            isCompleted && styles.completedLetter,
          ]}
        >
          {displayLetter}
        </Text>
      </TouchableOpacity>
    );
  };
  
  return (
    <View style={[styles.grid, { width: gridWidth }]}>
      {Array.from({ length: grid_size }).map((_, row) => (
        <View key={row} style={styles.row}>
          {Array.from({ length: grid_size }).map((_, col) => renderCell(row, col))}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    backgroundColor: '#1F2937',
    padding: 2,
    borderRadius: 8,
  },
  row: {
    flexDirection: 'row',
  },
  cell: {
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    margin: 1,
    borderRadius: 2,
    position: 'relative',
  },
  blockedCell: {
    backgroundColor: '#1F2937',
  },
  selectedCell: {
    backgroundColor: '#DBEAFE',
  },
  completedCell: {
    backgroundColor: '#D1FAE5',
  },
  prefilledCell: {
    backgroundColor: '#F3F4F6',
  },
  clueNumber: {
    position: 'absolute',
    top: 2,
    left: 2,
    color: '#6B7280',
    fontWeight: '500',
  },
  letter: {
    fontWeight: '600',
    color: '#1F2937',
    textTransform: 'uppercase',
  },
  prefilledLetter: {
    color: '#6B7280',
  },
  completedLetter: {
    color: '#059669',
  },
});
