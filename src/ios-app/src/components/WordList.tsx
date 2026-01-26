/**
 * 单词列表组件
 */

import React from 'react';
import { View, Text, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';

interface Word {
  id: number;
  word: string;
  definition: string;
  direction: 'across' | 'down';
  start_row: number;
  start_col: number;
  length: number;
}

interface WordListProps {
  words: Word[];
  completedWords: number[];
  selectedWord: Word | null;
  showTranslation: boolean;
  onWordPress: (word: Word) => void;
}

export default function WordList({
  words,
  completedWords,
  selectedWord,
  showTranslation,
  onWordPress,
}: WordListProps) {
  // 按方向分组
  const acrossWords = words.filter((w) => w.direction === 'across');
  const downWords = words.filter((w) => w.direction === 'down');
  
  const renderWordItem = (word: Word) => {
    const isCompleted = completedWords.includes(word.id);
    const isSelected = selectedWord?.id === word.id;
    
    return (
      <TouchableOpacity
        key={word.id}
        style={[
          styles.wordItem,
          isSelected && styles.selectedWordItem,
          isCompleted && styles.completedWordItem,
        ]}
        onPress={() => onWordPress(word)}
        activeOpacity={0.7}
      >
        <View style={styles.wordHeader}>
          <Text style={[styles.wordNumber, isCompleted && styles.completedText]}>
            {word.id}.
          </Text>
          {isCompleted && <Text style={styles.checkMark}>✓</Text>}
        </View>
        {showTranslation && (
          <Text
            style={[styles.wordDefinition, isCompleted && styles.completedText]}
            numberOfLines={2}
          >
            {word.definition}
          </Text>
        )}
      </TouchableOpacity>
    );
  };
  
  return (
    <ScrollView
      style={styles.container}
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.scrollContent}
    >
      {/* 横向单词 */}
      <View style={styles.column}>
        <View style={styles.columnHeader}>
          <Text style={styles.columnTitle}>横向 →</Text>
        </View>
        {acrossWords.map(renderWordItem)}
      </View>
      
      {/* 纵向单词 */}
      <View style={styles.column}>
        <View style={styles.columnHeader}>
          <Text style={styles.columnTitle}>纵向 ↓</Text>
        </View>
        {downWords.map(renderWordItem)}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  scrollContent: {
    padding: 12,
  },
  column: {
    width: 180,
    marginRight: 16,
  },
  columnHeader: {
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    marginBottom: 8,
  },
  columnTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4F46E5',
  },
  wordItem: {
    paddingVertical: 8,
    paddingHorizontal: 10,
    marginBottom: 6,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  selectedWordItem: {
    backgroundColor: '#EEF2FF',
    borderColor: '#4F46E5',
  },
  completedWordItem: {
    backgroundColor: '#F0FDF4',
    borderColor: '#10B981',
  },
  wordHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  wordNumber: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  checkMark: {
    fontSize: 14,
    color: '#10B981',
    fontWeight: '600',
  },
  wordDefinition: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 4,
    lineHeight: 18,
  },
  completedText: {
    color: '#10B981',
  },
});
