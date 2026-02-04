/**
 * 关卡选择页面
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import { staticApi } from '../api';
import AsyncStorage from '@react-native-async-storage/async-storage';

type NavigationProp = StackNavigationProp<RootStackParamList, 'LevelSelect'>;
type RouteType = RouteProp<RootStackParamList, 'LevelSelect'>;

const { width } = Dimensions.get('window');
const COLUMNS = 5;
const ITEM_SIZE = (width - 48 - (COLUMNS - 1) * 8) / COLUMNS;

export default function LevelSelectScreen() {
  const navigation = useNavigation<NavigationProp>();
  const route = useRoute<RouteType>();
  const { group, groupName } = route.params;
  
  const [loading, setLoading] = useState(true);
  const [levelCount, setLevelCount] = useState(0);
  const [unlockedLevel, setUnlockedLevel] = useState(1);
  const [completedLevels, setCompletedLevels] = useState<Record<number, number>>({});
  
  // 加载数据
  useEffect(() => {
    loadData();
  }, [group]);
  
  const loadData = async () => {
    try {
      // 加载词库元数据
      const meta = await staticApi.getMeta(group);
      setLevelCount(meta.level_count);
      
      // 加载用户进度
      const progressKey = `progress_${group}`;
      const savedProgress = await AsyncStorage.getItem(progressKey);
      if (savedProgress) {
        const progress = JSON.parse(savedProgress);
        setUnlockedLevel(progress.unlocked || 1);
        setCompletedLevels(progress.completed || {});
      }
    } catch (error) {
      console.warn('加载关卡数据失败:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // 选择关卡
  const handleSelectLevel = (level: number) => {
    if (level > unlockedLevel) {
      return; // 锁定的关卡不能点击
    }
    
    navigation.navigate('Game', {
      mode: 'campaign',
      group,
      groupName,
      level,
    });
  };
  
  // 渲染关卡按钮
  const renderLevelButton = (level: number) => {
    const isLocked = level > unlockedLevel;
    const isCompleted = completedLevels[level] !== undefined;
    const stars = completedLevels[level] || 0;
    
    return (
      <TouchableOpacity
        key={level}
        style={[
          styles.levelButton,
          isLocked && styles.levelLocked,
          isCompleted && styles.levelCompleted,
        ]}
        onPress={() => handleSelectLevel(level)}
        disabled={isLocked}
        activeOpacity={0.7}
      >
        {isLocked ? (
          <Text style={styles.lockIcon}>🔒</Text>
        ) : (
          <>
            <Text style={[styles.levelNumber, isCompleted && styles.levelNumberCompleted]}>
              {level}
            </Text>
            {isCompleted && (
              <View style={styles.starsContainer}>
                {[1, 2, 3].map((s) => (
                  <Text
                    key={s}
                    style={[styles.star, s <= stars && styles.starActive]}
                  >
                    ★
                  </Text>
                ))}
              </View>
            )}
          </>
        )}
      </TouchableOpacity>
    );
  };
  
  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#FF69B4" />
        <Text style={styles.loadingText}>加载关卡...</Text>
      </View>
    );
  }
  
  // 分组显示（每10关一组）
  const groups: number[][] = [];
  for (let i = 0; i < levelCount; i += 10) {
    groups.push(
      Array.from({ length: Math.min(10, levelCount - i) }, (_, j) => i + j + 1)
    );
  }
  
  return (
    <ScrollView style={styles.container}>
      {/* 进度信息 */}
      <View style={styles.progressCard}>
        <View style={styles.progressItem}>
          <Text style={styles.progressValue}>{unlockedLevel - 1}</Text>
          <Text style={styles.progressLabel}>已通关</Text>
        </View>
        <View style={styles.progressDivider} />
        <View style={styles.progressItem}>
          <Text style={styles.progressValue}>{levelCount}</Text>
          <Text style={styles.progressLabel}>总关卡</Text>
        </View>
        <View style={styles.progressDivider} />
        <View style={styles.progressItem}>
          <Text style={styles.progressValue}>
            {Math.round(((unlockedLevel - 1) / levelCount) * 100)}%
          </Text>
          <Text style={styles.progressLabel}>完成度</Text>
        </View>
      </View>
      
      {/* 关卡列表 */}
      {groups.map((group, groupIndex) => (
        <View key={groupIndex} style={styles.levelGroup}>
          <Text style={styles.groupTitle}>
            第 {groupIndex * 10 + 1} - {groupIndex * 10 + group.length} 关
          </Text>
          <View style={styles.levelGrid}>
            {group.map((level) => renderLevelButton(level))}
          </View>
        </View>
      ))}
      
      <View style={styles.bottomSpacer} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FDFDFD',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FDFDFD',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#6B7280',
  },
  progressCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  progressItem: {
    flex: 1,
    alignItems: 'center',
  },
  progressValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FF69B4',
  },
  progressLabel: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 4,
  },
  progressDivider: {
    width: 1,
    backgroundColor: '#FFB6C1',
    marginVertical: 4,
  },
  levelGroup: {
    marginTop: 20,
    marginHorizontal: 16,
  },
  groupTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 12,
  },
  levelGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  levelButton: {
    width: ITEM_SIZE,
    height: ITEM_SIZE,
    backgroundColor: '#fff',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  levelLocked: {
    backgroundColor: '#FFB6C1',
  },
  levelCompleted: {
    backgroundColor: '#FFF0F5',
    borderWidth: 2,
    borderColor: '#FF69B4',
  },
  lockIcon: {
    fontSize: 18,
  },
  levelNumber: {
    fontSize: 18,
    fontWeight: '600',
    color: '#5D5D5D',
  },
  levelNumberCompleted: {
    color: '#FF69B4',
  },
  starsContainer: {
    flexDirection: 'row',
    marginTop: 2,
  },
  star: {
    fontSize: 10,
    color: '#FFB6C1',
  },
  starActive: {
    color: '#DAA520',
  },
  bottomSpacer: {
    height: 32,
  },
});
