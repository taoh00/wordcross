/**
 * 游戏主页面
 */

import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAppDispatch, useAppSelector } from '../stores/hooks';
import {
  loadLevel,
  selectCell,
  selectWord,
  inputLetter,
  deleteLetter,
  useHint,
  tickTimer,
  startTimer,
  stopTimer,
  resetGame,
  submitGame,
} from '../stores/gameSlice';
import { consumeEnergy, useProp } from '../stores/userSlice';
import { RootStackParamList } from '../navigation/AppNavigator';
import { speakWord } from '../utils/audio';
import { trackApi } from '../api';
import Grid from '../components/Grid';
import Keyboard from '../components/Keyboard';
import WordList from '../components/WordList';

type NavigationProp = StackNavigationProp<RootStackParamList, 'Game'>;
type RouteType = RouteProp<RootStackParamList, 'Game'>;

export default function GameScreen() {
  const navigation = useNavigation<NavigationProp>();
  const route = useRoute<RouteType>();
  const dispatch = useAppDispatch();
  
  const { mode, group, groupName, level = 1 } = route.params;
  
  const {
    puzzle,
    userAnswers,
    completedWords,
    selectedWord,
    score,
    stars,
    timer,
    timerRunning,
    loading,
    error,
    gameCompleted,
  } = useAppSelector((state) => state.game);
  
  const { energy, hintCount, speakCount } = useAppSelector((state) => state.user);
  const { showTranslation, autoSpeak } = useAppSelector((state) => state.settings);
  
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  
  // 加载关卡
  useEffect(() => {
    loadGameLevel();
    
    return () => {
      // 清理计时器
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      dispatch(stopTimer());
    };
  }, [group, level]);
  
  // 计时器
  useEffect(() => {
    if (timerRunning && !timerRef.current) {
      timerRef.current = setInterval(() => {
        dispatch(tickTimer());
      }, 1000);
    } else if (!timerRunning && timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [timerRunning]);
  
  // 游戏完成
  useEffect(() => {
    if (gameCompleted) {
      handleGameComplete();
    }
  }, [gameCompleted]);
  
  // 自动发音
  useEffect(() => {
    if (autoSpeak && selectedWord) {
      speakWord(selectedWord.word);
    }
  }, [selectedWord?.id]);
  
  const loadGameLevel = async () => {
    dispatch(resetGame());
    
    // 消耗体力
    const energyCost = mode === 'campaign' ? 10 : 30;
    if (energy < energyCost) {
      Alert.alert('体力不足', `需要 ${energyCost} 点体力`, [
        { text: '返回', onPress: () => navigation.goBack() },
      ]);
      return;
    }
    
    try {
      await dispatch(consumeEnergy({ amount: energyCost, mode }));
      await dispatch(loadLevel({ group, level })).unwrap();
      dispatch(startTimer());
    } catch (err) {
      Alert.alert('加载失败', '无法加载关卡数据', [
        { text: '返回', onPress: () => navigation.goBack() },
      ]);
    }
  };
  
  const handleGameComplete = async () => {
    dispatch(stopTimer());
    
    // 埋点：记录关卡完成
    trackApi.trackLevelComplete(group, level, stars, score, timer, 'ios');
    
    // 保存进度
    if (mode === 'campaign') {
      const progressKey = `progress_${group}`;
      const savedProgress = await AsyncStorage.getItem(progressKey);
      const progress = savedProgress ? JSON.parse(savedProgress) : { unlocked: 1, completed: {} };
      
      progress.unlocked = Math.max(progress.unlocked, level + 1);
      progress.completed[level] = Math.max(progress.completed[level] || 0, stars);
      
      await AsyncStorage.setItem(progressKey, JSON.stringify(progress));
    }
    
    // 提交成绩
    try {
      await dispatch(submitGame({
        mode,
        group,
        score,
        wordsCount: completedWords.length,
        levelReached: level,
        duration: timer,
      }));
    } catch (err) {
      console.warn('提交成绩失败:', err);
    }
    
    // 显示结果
    Alert.alert(
      '🎉 恭喜通关！',
      `用时: ${formatTime(timer)}\n得分: ${score}\n星级: ${'⭐'.repeat(stars)}`,
      [
        { text: '返回', onPress: () => navigation.goBack() },
        {
          text: '下一关',
          onPress: () => {
            navigation.replace('Game', {
              mode,
              group,
              groupName,
              level: level + 1,
            });
          },
        },
      ]
    );
  };
  
  // 使用提示道具
  const handleUseHint = async () => {
    if (hintCount <= 0) {
      Alert.alert('提示', '提示道具不足');
      return;
    }
    
    if (!selectedWord) {
      Alert.alert('提示', '请先选择一个单词');
      return;
    }
    
    try {
      await dispatch(useProp({ propType: 'hint' }));
      dispatch(useHint());
      
      // 埋点：记录道具使用
      trackApi.trackPropUsage('hint_letter', mode, group, level, 'ios');
    } catch (err) {
      Alert.alert('错误', '使用道具失败');
    }
  };
  
  // 发音
  const handleSpeak = async () => {
    if (!selectedWord) {
      Alert.alert('提示', '请先选择一个单词');
      return;
    }
    
    // 使用发音道具
    if (speakCount > 0) {
      await dispatch(useProp({ propType: 'speak' }));
      
      // 埋点：记录道具使用
      trackApi.trackPropUsage('speak', mode, group, level, 'ios');
    }
    
    speakWord(selectedWord.word);
  };
  
  // 格式化时间
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  
  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#4F46E5" />
          <Text style={styles.loadingText}>加载关卡...</Text>
        </View>
      </SafeAreaView>
    );
  }
  
  if (error || !puzzle) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorIcon}>😕</Text>
          <Text style={styles.errorText}>{error || '加载失败'}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={loadGameLevel}>
            <Text style={styles.retryButtonText}>重试</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }
  
  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      {/* 顶部信息栏 */}
      <View style={styles.topBar}>
        <View style={styles.topBarItem}>
          <Text style={styles.topBarIcon}>📊</Text>
          <Text style={styles.topBarValue}>{score}</Text>
        </View>
        <View style={styles.topBarItem}>
          <Text style={styles.topBarIcon}>⏱️</Text>
          <Text style={styles.topBarValue}>{formatTime(timer)}</Text>
        </View>
        <View style={styles.topBarItem}>
          <Text style={styles.topBarIcon}>✅</Text>
          <Text style={styles.topBarValue}>
            {completedWords.length}/{puzzle.words.length}
          </Text>
        </View>
      </View>
      
      {/* 填字网格 */}
      <View style={styles.gridContainer}>
        <Grid
          puzzle={puzzle}
          userAnswers={userAnswers}
          completedWords={completedWords}
          selectedWord={selectedWord}
          onCellPress={(row, col) => dispatch(selectCell({ row, col }))}
        />
      </View>
      
      {/* 当前单词信息 */}
      {selectedWord && (
        <View style={styles.wordInfoCard}>
          <View style={styles.wordInfoHeader}>
            <Text style={styles.wordClue}>
              {selectedWord.direction === 'across' ? '横' : '竖'} {selectedWord.id}
            </Text>
            <TouchableOpacity onPress={handleSpeak} style={styles.speakButton}>
              <Text style={styles.speakButtonText}>🔊</Text>
            </TouchableOpacity>
          </View>
          {showTranslation && (
            <Text style={styles.wordDefinition}>{selectedWord.definition}</Text>
          )}
        </View>
      )}
      
      {/* 道具栏 */}
      <View style={styles.propsBar}>
        <TouchableOpacity style={styles.propButton} onPress={handleUseHint}>
          <Text style={styles.propIcon}>💡</Text>
          <Text style={styles.propCount}>{hintCount}</Text>
        </TouchableOpacity>
      </View>
      
      {/* 单词列表 */}
      <WordList
        words={puzzle.words}
        completedWords={completedWords}
        selectedWord={selectedWord}
        showTranslation={showTranslation}
        onWordPress={(word) => dispatch(selectWord(word))}
      />
      
      {/* 键盘 */}
      <Keyboard
        onKeyPress={(key) => dispatch(inputLetter(key))}
        onDelete={() => dispatch(deleteLetter())}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F3F4F6',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#6B7280',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  errorIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 24,
  },
  retryButton: {
    backgroundColor: '#4F46E5',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  topBarItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  topBarIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  topBarValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
  },
  gridContainer: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  wordInfoCard: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
  },
  wordInfoHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  wordClue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4F46E5',
  },
  speakButton: {
    padding: 4,
  },
  speakButtonText: {
    fontSize: 20,
  },
  wordDefinition: {
    fontSize: 15,
    color: '#374151',
    marginTop: 8,
    lineHeight: 22,
  },
  propsBar: {
    flexDirection: 'row',
    justifyContent: 'center',
    paddingVertical: 8,
  },
  propButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  propIcon: {
    fontSize: 20,
    marginRight: 6,
  },
  propCount: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
});
