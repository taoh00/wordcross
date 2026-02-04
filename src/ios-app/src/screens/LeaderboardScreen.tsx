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
import { leaderboardApi, userApi } from '../api';
import { useAppSelector } from '../stores/hooks';

/** 排行榜类型 */
const LEADERBOARD_TYPES = [
  { code: 'campaign_level', name: '闯关等级', icon: '🏆' },
  { code: 'campaign_score', name: '闯关积分', icon: '⭐' },
  { code: 'endless_level', name: '无限关卡', icon: '♾️' },
  { code: 'endless_score', name: '无限积分', icon: '💎' },
  { code: 'timed_words', name: '计时单词', icon: '⏱️' },
  { code: 'timed_score', name: '计时积分', icon: '🎯' },
];

interface LeaderboardEntry {
  rank: number;
  user_id: string;
  nickname: string;
  avatar: string;
  value: number;
  extra?: {
    total_score?: number;
    max_level?: number;
    max_words?: number;
    wins?: number;
    games?: number;
  };
}

interface MyStats {
  campaignLevel: number;
  totalScore: number;
  totalWords: number;
  playCount: number;
}

interface MyRanking {
  type: string;
  name: string;
  rank: number;
  total: number;
}

export default function LeaderboardScreen() {
  const { id: currentUserId } = useAppSelector((state) => state.user);
  
  // Tab状态: 'leaderboard' | 'mystats'
  const [activeTab, setActiveTab] = useState<'leaderboard' | 'mystats'>('leaderboard');
  
  const [selectedType, setSelectedType] = useState(LEADERBOARD_TYPES[0].code);
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 我的统计
  const [myStats, setMyStats] = useState<MyStats>({
    campaignLevel: 1,
    totalScore: 0,
    totalWords: 0,
    playCount: 0,
  });
  const [myRankings, setMyRankings] = useState<MyRanking[]>([]);
  const [loadingStats, setLoadingStats] = useState(false);
  
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
      setEntries(result.entries || []);
    } catch (err) {
      setError('加载排行榜失败');
      console.warn('加载排行榜失败:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedType]);
  
  // 加载我的统计
  const loadMyStats = useCallback(async () => {
    setLoadingStats(true);
    try {
      const data = await userApi.getStats();
      if (data.registered && data.stats) {
        const stats = data.stats;
        setMyStats({
          campaignLevel: stats.campaign?.max_level || 1,
          totalScore:
            (stats.campaign?.total_score || 0) +
            (stats.endless?.total_score || 0) +
            (stats.timed?.total_score || 0),
          totalWords: stats.campaign?.total_words || 0,
          playCount:
            (stats.campaign?.play_count || 0) +
            (stats.endless?.play_count || 0) +
            (stats.timed?.play_count || 0),
        });
      }
    } catch (err) {
      console.warn('加载统计失败:', err);
    } finally {
      setLoadingStats(false);
    }
    
    // 加载我的排名
    loadMyRankings();
  }, [currentUserId]);
  
  // 加载我的各榜排名（含总人数）
  const loadMyRankings = useCallback(async () => {
    if (!currentUserId) return;
    
    const rankings: MyRanking[] = [];
    const mainTypes = ['campaign_level', 'campaign_score', 'timed_words', 'endless_level'];
    
    for (const typeCode of mainTypes) {
      try {
        const data = await leaderboardApi.get(typeCode, 'all', 100);
        const entries = data.entries || [];
        const total = entries.length;
        const myIndex = entries.findIndex((e: LeaderboardEntry) => e.user_id === currentUserId);
        
        if (myIndex >= 0) {
          const typeInfo = LEADERBOARD_TYPES.find((t) => t.code === typeCode);
          rankings.push({
            type: typeCode,
            name: typeInfo?.name || typeCode,
            rank: myIndex + 1,
            total: total,
          });
        }
      } catch (err) {
        console.warn('获取排名失败:', typeCode, err);
      }
    }
    
    setMyRankings(rankings);
  }, [currentUserId]);
  
  useEffect(() => {
    loadLeaderboard();
  }, [selectedType]);
  
  useEffect(() => {
    if (activeTab === 'mystats') {
      loadMyStats();
    }
  }, [activeTab]);
  
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
        <View style={styles.scoreContainer}>
          <Text style={styles.userScore}>{item.value.toLocaleString()}</Text>
          {item.extra?.total_score !== undefined && (
            <Text style={styles.totalScore}>总分:{item.extra.total_score.toLocaleString()}</Text>
          )}
        </View>
      </View>
    );
  };
  
  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      {/* Tab切换 */}
      <View style={styles.tabHeader}>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'leaderboard' && styles.tabButtonActive]}
          onPress={() => setActiveTab('leaderboard')}
        >
          <Text style={[styles.tabButtonText, activeTab === 'leaderboard' && styles.tabButtonTextActive]}>
            📊 排行榜
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'mystats' && styles.tabButtonActive]}
          onPress={() => setActiveTab('mystats')}
        >
          <Text style={[styles.tabButtonText, activeTab === 'mystats' && styles.tabButtonTextActive]}>
            📈 我的记录
          </Text>
        </TouchableOpacity>
      </View>
      
      {/* 排行榜Tab内容 */}
      {activeTab === 'leaderboard' && (
        <>
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
              <ActivityIndicator size="large" color="#FF69B4" />
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
        </>
      )}
      
      {/* 我的记录Tab内容 */}
      {activeTab === 'mystats' && (
        <ScrollView
          style={styles.myStatsContainer}
          refreshControl={
            <RefreshControl refreshing={loadingStats} onRefresh={loadMyStats} />
          }
        >
          <Text style={styles.statsTitle}>📊 我的统计</Text>
          
          <View style={styles.statsGrid}>
            <View style={[styles.statItem, styles.statPurple]}>
              <Text style={styles.statValue}>{myStats.campaignLevel}</Text>
              <Text style={styles.statLabel}>闯关进度</Text>
            </View>
            <View style={[styles.statItem, styles.statGreen]}>
              <Text style={styles.statValue}>{myStats.totalScore}</Text>
              <Text style={styles.statLabel}>总积分</Text>
            </View>
            <View style={[styles.statItem, styles.statOrange]}>
              <Text style={styles.statValue}>{myStats.totalWords}</Text>
              <Text style={styles.statLabel}>完成单词</Text>
            </View>
            <View style={[styles.statItem, styles.statBlue]}>
              <Text style={styles.statValue}>{myStats.playCount}</Text>
              <Text style={styles.statLabel}>游戏次数</Text>
            </View>
          </View>
          
          {/* 我的排名 */}
          {myRankings.length > 0 && (
            <View style={styles.myRankingsSection}>
              <Text style={styles.rankingsTitle}>🏅 我的排名</Text>
              {myRankings.map((ranking) => (
                <View key={ranking.type} style={styles.rankingItem}>
                  <Text style={styles.rankingType}>{ranking.name}</Text>
                  <Text style={styles.rankingRank}>
                    第{ranking.rank}/{ranking.total}名
                  </Text>
                </View>
              ))}
            </View>
          )}
          
          {/* 刷新按钮 */}
          <TouchableOpacity style={styles.refreshButton} onPress={loadMyStats}>
            <Text style={styles.refreshButtonText}>🔄 刷新记录</Text>
          </TouchableOpacity>
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FDFDFD',
  },
  tabHeader: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    padding: 12,
    gap: 10,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#FDFDFD',
    borderRadius: 12,
    alignItems: 'center',
  },
  tabButtonActive: {
    backgroundColor: '#FF69B4',
  },
  tabButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#888888',
  },
  tabButtonTextActive: {
    color: '#fff',
  },
  typeSelector: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#FFB6C1',
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
    backgroundColor: '#FDFDFD',
  },
  typeButtonActive: {
    backgroundColor: '#FF69B4',
  },
  typeIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  typeName: {
    fontSize: 14,
    color: '#888888',
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
    borderBottomColor: '#FFB6C1',
  },
  headerIcon: {
    fontSize: 24,
    marginRight: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#5D5D5D',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#888888',
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
    color: '#888888',
    marginBottom: 24,
  },
  retryButton: {
    backgroundColor: '#FF69B4',
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
    color: '#5D5D5D',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#888888',
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
    backgroundColor: '#FFF0F5',
    borderWidth: 2,
    borderColor: '#FF69B4',
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
    color: '#888888',
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
    color: '#5D5D5D',
  },
  currentUserName: {
    color: '#FF69B4',
    fontWeight: '600',
  },
  scoreContainer: {
    alignItems: 'flex-end',
  },
  userScore: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FF69B4',
  },
  totalScore: {
    fontSize: 12,
    fontWeight: '600',
    color: '#3CB371',
    marginTop: 2,
  },
  // 我的统计样式
  myStatsContainer: {
    flex: 1,
    padding: 16,
  },
  statsTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#5D5D5D',
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 24,
  },
  statItem: {
    flex: 1,
    minWidth: '45%',
    padding: 16,
    borderRadius: 16,
    alignItems: 'center',
  },
  statPurple: {
    backgroundColor: '#F3E6F3',
  },
  statGreen: {
    backgroundColor: '#E0FBE0',
  },
  statOrange: {
    backgroundColor: '#FFFACD',
  },
  statBlue: {
    backgroundColor: '#DBEAFE',
  },
  statValue: {
    fontSize: 28,
    fontWeight: '800',
    color: '#5D5D5D',
  },
  statLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#888888',
    marginTop: 4,
  },
  myRankingsSection: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 24,
  },
  rankingsTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#888888',
    marginBottom: 12,
  },
  rankingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#FDFDFD',
    borderRadius: 12,
    marginBottom: 8,
  },
  rankingType: {
    fontSize: 15,
    fontWeight: '600',
    color: '#5D5D5D',
  },
  rankingRank: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FF69B4',
  },
  refreshButton: {
    backgroundColor: '#FF69B4',
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
    alignSelf: 'center',
  },
  refreshButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
});
