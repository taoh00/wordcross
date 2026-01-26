/**
 * 排行榜页面
 */

import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  FlatList,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { leaderboardApi } from '../api';
import { useAppSelector } from '../stores/hooks';

/** 排行榜类型 */
const LEADERBOARD_TYPES = [
  { code: 'campaign_level', name: '闯关等级', icon: '🏆' },
  { code: 'campaign_score', name: '闯关积分', icon: '⭐' },
  { code: 'endless_level', name: '无限关卡', icon: '♾️' },
  { code: 'endless_score', name: '无限积分', icon: '💎' },
  { code: 'timed_words', name: '计时单词', icon: '⏱️' },
  { code: 'timed_score', name: '计时积分', icon: '🎯' },
  { code: 'pk_wins', name: 'PK胜场', icon: '⚔️' },
  { code: 'pk_score', name: 'PK积分', icon: '🥇' },
];

interface LeaderboardEntry {
  rank: number;
  user_id: string;
  nickname: string;
  avatar: string;
  value: number;
}

export default function LeaderboardScreen() {
  const { id: currentUserId } = useAppSelector((state) => state.user);
  
  const [selectedType, setSelectedType] = useState(LEADERBOARD_TYPES[0].code);
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 加载排行榜
  const loadLeaderboard = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);
    
    try {
      const result = await leaderboardApi.get(selectedType, 'all', 100);
      setEntries(result.entries);
    } catch (err) {
      setError('加载排行榜失败');
      console.warn('加载排行榜失败:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedType]);
  
  useEffect(() => {
    loadLeaderboard();
  }, [selectedType]);
  
  // 获取当前类型信息
  const currentTypeInfo = LEADERBOARD_TYPES.find((t) => t.code === selectedType);
  
  // 渲染排名项
  const renderItem = ({ item }: { item: LeaderboardEntry }) => {
    const isCurrentUser = item.user_id === currentUserId;
    const rankColors: Record<number, string> = {
      1: '#FFD700',
      2: '#C0C0C0',
      3: '#CD7F32',
    };
    
    return (
      <View style={[styles.rankItem, isCurrentUser && styles.currentUserItem]}>
        {/* 排名 */}
        <View style={styles.rankBadge}>
          {item.rank <= 3 ? (
            <Text style={styles.rankMedal}>
              {item.rank === 1 ? '🥇' : item.rank === 2 ? '🥈' : '🥉'}
            </Text>
          ) : (
            <Text style={styles.rankNumber}>{item.rank}</Text>
          )}
        </View>
        
        {/* 用户信息 */}
        <Text style={styles.userAvatar}>{item.avatar || '👤'}</Text>
        <View style={styles.userInfo}>
          <Text style={[styles.userName, isCurrentUser && styles.currentUserName]}>
            {item.nickname}
            {isCurrentUser && ' (我)'}
          </Text>
        </View>
        
        {/* 分数 */}
        <Text style={styles.userScore}>{item.value.toLocaleString()}</Text>
      </View>
    );
  };
  
  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      {/* 类型选择器 */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.typeSelector}
        contentContainerStyle={styles.typeSelectorContent}
      >
        {LEADERBOARD_TYPES.map((type) => (
          <TouchableOpacity
            key={type.code}
            style={[
              styles.typeButton,
              selectedType === type.code && styles.typeButtonActive,
            ]}
            onPress={() => setSelectedType(type.code)}
          >
            <Text style={styles.typeIcon}>{type.icon}</Text>
            <Text
              style={[
                styles.typeName,
                selectedType === type.code && styles.typeNameActive,
              ]}
            >
              {type.name}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
      
      {/* 排行榜标题 */}
      <View style={styles.header}>
        <Text style={styles.headerIcon}>{currentTypeInfo?.icon}</Text>
        <Text style={styles.headerTitle}>{currentTypeInfo?.name}排行榜</Text>
      </View>
      
      {/* 排行榜列表 */}
      {loading && !refreshing ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#4F46E5" />
          <Text style={styles.loadingText}>加载中...</Text>
        </View>
      ) : error ? (
        <View style={styles.errorContainer}>
          <Text style={styles.errorIcon}>😕</Text>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={() => loadLeaderboard()}>
            <Text style={styles.retryButtonText}>重试</Text>
          </TouchableOpacity>
        </View>
      ) : entries.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>🏆</Text>
          <Text style={styles.emptyText}>暂无排行数据</Text>
          <Text style={styles.emptySubtext}>快来成为第一名吧！</Text>
        </View>
      ) : (
        <FlatList
          data={entries}
          keyExtractor={(item) => `${item.rank}-${item.user_id}`}
          renderItem={renderItem}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => loadLeaderboard(true)}
            />
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F3F4F6',
  },
  typeSelector: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  typeSelectorContent: {
    padding: 12,
  },
  typeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 8,
    marginRight: 8,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
  },
  typeButtonActive: {
    backgroundColor: '#4F46E5',
  },
  typeIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  typeName: {
    fontSize: 14,
    color: '#6B7280',
  },
  typeNameActive: {
    color: '#fff',
    fontWeight: '600',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerIcon: {
    fontSize: 24,
    marginRight: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
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
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#6B7280',
  },
  listContent: {
    padding: 16,
  },
  rankItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  currentUserItem: {
    backgroundColor: '#EEF2FF',
    borderWidth: 2,
    borderColor: '#4F46E5',
  },
  rankBadge: {
    width: 36,
    alignItems: 'center',
  },
  rankMedal: {
    fontSize: 24,
  },
  rankNumber: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
  },
  userAvatar: {
    fontSize: 28,
    marginHorizontal: 12,
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#1F2937',
  },
  currentUserName: {
    color: '#4F46E5',
    fontWeight: '600',
  },
  userScore: {
    fontSize: 18,
    fontWeight: '700',
    color: '#4F46E5',
  },
});
