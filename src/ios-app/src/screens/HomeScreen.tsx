/**
 * 首页 - 游戏模式选择 (Kawaii Style)
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { useAppDispatch, useAppSelector } from '../stores/hooks';
import { initUser, refreshEnergy, refreshProps, claimFreeEnergy } from '../stores/userSlice';
import { RootStackParamList } from '../navigation/AppNavigator';
import { trackApi } from '../api';
import { COLORS, SHADOWS, LAYOUT } from '../utils/theme';

type NavigationProp = StackNavigationProp<RootStackParamList>;

/** 游戏模式卡片 */
interface ModeCardProps {
  title: string;
  icon: string;
  description: string;
  color: string;
  borderColor: string;
  shadowColor: string;
  onPress: () => void;
}

function ModeCard({ title, icon, description, color, borderColor, shadowColor, onPress }: ModeCardProps) {
  return (
    <TouchableOpacity
      style={[
        styles.modeCard, 
        { 
          backgroundColor: color,
          borderColor: borderColor,
          shadowColor: shadowColor 
        }
      ]}
      onPress={onPress}
      activeOpacity={0.85}
    >
      <View style={styles.iconContainer}>
        <Text style={styles.modeIcon}>{icon}</Text>
      </View>
      <View style={styles.modeInfo}>
        <Text style={styles.modeTitle}>{title}</Text>
        <Text style={styles.modeDesc}>{description}</Text>
      </View>
      <Text style={styles.modeArrow}>›</Text>
    </TouchableOpacity>
  );
}

export default function HomeScreen() {
  const navigation = useNavigation<NavigationProp>();
  const dispatch = useAppDispatch();
  const { nickname, avatar, energy, maxEnergy, hintCount, speakCount, loading } = useAppSelector(
    (state) => state.user
  );
  
  const [refreshing, setRefreshing] = useState(false);
  
  // 初始化
  useEffect(() => {
    dispatch(initUser());
  }, [dispatch]);
  
  // 刷新数据
  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        dispatch(refreshEnergy()),
        dispatch(refreshProps()),
      ]);
    } catch (error) {
      console.warn('刷新失败:', error);
    }
    setRefreshing(false);
  };
  
  // 领取免费体力
  const handleClaimEnergy = async () => {
    try {
      const result = await dispatch(claimFreeEnergy()).unwrap();
      Alert.alert('领取成功', `获得 ${result.amount} 点体力！`);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '领取失败';
      Alert.alert('提示', message);
    }
  };
  
  // 选择模式
  const handleModeSelect = (mode: 'campaign' | 'endless' | 'timed') => {
    // 埋点：记录模式选择事件
    trackApi.trackEvent('select_mode', { mode }, 'ios');
    
    navigation.navigate('VocabSelect', { mode });
  };
  
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={{ paddingBottom: 40 }}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.pink.dark} />
        }
      >
        {/* 头部区域 */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>我爱填单词</Text>
          <View style={styles.userInfo}>
            <View style={styles.avatarContainer}>
              <Text style={styles.avatar}>{avatar || '😊'}</Text>
            </View>
            <View>
              <Text style={styles.nickname}>{nickname || '游客'}</Text>
              <View style={styles.levelBadge}>
                <Text style={styles.levelText}>Lv.1 初学乍练</Text>
              </View>
            </View>
          </View>
        </View>
        
        {/* 资源栏 */}
        <View style={styles.resourceContainer}>
          <TouchableOpacity style={styles.resourceItem} onPress={handleClaimEnergy}>
            <Text style={styles.resourceIcon}>⚡</Text>
            <Text style={styles.resourceValue}>{energy}/{maxEnergy}</Text>
            <Text style={styles.resourceLabel}>体力</Text>
          </TouchableOpacity>
          
          <View style={styles.resourceDivider} />
          
          <View style={styles.resourceItem}>
            <Text style={styles.resourceIcon}>💡</Text>
            <Text style={styles.resourceValue}>{hintCount}</Text>
            <Text style={styles.resourceLabel}>提示</Text>
          </View>
          
          <View style={styles.resourceDivider} />
          
          <View style={styles.resourceItem}>
            <Text style={styles.resourceIcon}>🔊</Text>
            <Text style={styles.resourceValue}>{speakCount}</Text>
            <Text style={styles.resourceLabel}>发音</Text>
          </View>
        </View>
        
        {/* 游戏模式 */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🎮 选择游戏模式</Text>
          
          <View style={styles.gridContainer}>
            {/* 闯关模式 */}
            <ModeCard
              title="闯关模式"
              icon="🏰"
              description="逐关挑战"
              color={COLORS.pink.light}
              borderColor={COLORS.pink.main}
              shadowColor={COLORS.pink.dark}
              onPress={() => handleModeSelect('campaign')}
            />
            
            {/* 无限模式 */}
            <ModeCard
              title="无限模式"
              icon="♾️"
              description="随机生成"
              color={COLORS.mint.light}
              borderColor={COLORS.mint.main}
              shadowColor={COLORS.mint.dark}
              onPress={() => handleModeSelect('endless')}
            />
            
            {/* 计时模式 */}
            <ModeCard
              title="计时模式"
              icon="⏱️"
              description="限时挑战"
              color={COLORS.blue.light}
              borderColor={COLORS.blue.main}
              shadowColor={COLORS.blue.dark}
              onPress={() => handleModeSelect('timed')}
            />
            
            {/* 排行榜 */}
            <ModeCard
              title="排行榜"
              icon="🏆"
              description="查看排名"
              color={COLORS.yellow.light}
              borderColor={COLORS.yellow.main}
              shadowColor={COLORS.yellow.dark}
              onPress={() => navigation.navigate('Leaderboard')}
            />
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollView: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 24,
    paddingTop: 20,
    paddingBottom: 40,
    backgroundColor: COLORS.white,
    borderBottomLeftRadius: 32,
    borderBottomRightRadius: 32,
    ...SHADOWS.soft,
    zIndex: 1,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '900',
    color: COLORS.textMain,
    textAlign: 'center',
    marginBottom: 20,
    letterSpacing: 1,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.blue.light,
    padding: 12,
    borderRadius: 24,
    borderWidth: 2,
    borderColor: COLORS.blue.main,
    alignSelf: 'center',
  },
  avatarContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.white,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
    borderWidth: 2,
    borderColor: COLORS.white,
  },
  avatar: {
    fontSize: 28,
  },
  nickname: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.textMain,
  },
  levelBadge: {
    backgroundColor: COLORS.white,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    marginTop: 4,
    alignSelf: 'flex-start',
  },
  levelText: {
    fontSize: 10,
    fontWeight: '700',
    color: COLORS.blue.dark,
  },
  
  /* 资源栏 - 浮动卡片 */
  resourceContainer: {
    flexDirection: 'row',
    backgroundColor: COLORS.white,
    marginHorizontal: 20,
    marginTop: -24,
    borderRadius: 24,
    padding: 16,
    ...SHADOWS.soft,
    borderWidth: 2,
    borderColor: COLORS.border,
    zIndex: 2,
  },
  resourceItem: {
    flex: 1,
    alignItems: 'center',
  },
  resourceIcon: {
    fontSize: 20,
    marginBottom: 4,
  },
  resourceValue: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.textMain,
  },
  resourceLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.textLight,
    marginTop: 2,
  },
  resourceDivider: {
    width: 2,
    backgroundColor: COLORS.border,
    marginVertical: 8,
    borderRadius: 1,
  },
  
  /* 模式选择 */
  section: {
    paddingHorizontal: 20,
    marginTop: 32,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '900',
    color: COLORS.textMain,
    marginBottom: 16,
    textAlign: 'center',
  },
  gridContainer: {
    gap: 16,
  },
  modeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 24,
    borderWidth: 3,
    marginBottom: 4,
    // 3D Shadow effect manually
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 1,
    shadowRadius: 0,
    elevation: 0, 
  },
  iconContainer: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: COLORS.white,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
    borderWidth: 2,
    borderColor: COLORS.pink.main,
  },
  modeIcon: {
    fontSize: 32,
  },
  modeInfo: {
    flex: 1,
  },
  modeTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: COLORS.textMain,
    marginBottom: 4,
  },
  modeDesc: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.textLight,
  },
  modeArrow: {
    fontSize: 24,
    fontWeight: '800',
    color: COLORS.textLight,
  },
});
