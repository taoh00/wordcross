/**
 * 首页 - 游戏模式选择
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

type NavigationProp = StackNavigationProp<RootStackParamList>;

/** 游戏模式卡片 */
interface ModeCardProps {
  title: string;
  icon: string;
  description: string;
  color: string;
  onPress: () => void;
}

function ModeCard({ title, icon, description, color, onPress }: ModeCardProps) {
  return (
    <TouchableOpacity
      style={[styles.modeCard, { borderLeftColor: color }]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <Text style={styles.modeIcon}>{icon}</Text>
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
  const handleModeSelect = (mode: 'campaign' | 'endless' | 'timed' | 'pk') => {
    // 埋点：记录模式选择事件
    trackApi.trackEvent('select_mode', { mode }, 'ios');
    
    navigation.navigate('VocabSelect', { mode });
  };
  
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* 头部用户信息 */}
        <View style={styles.header}>
          <View style={styles.userInfo}>
            <Text style={styles.avatar}>{avatar}</Text>
            <View>
              <Text style={styles.nickname}>{nickname}</Text>
              <Text style={styles.welcome}>欢迎回来</Text>
            </View>
          </View>
        </View>
        
        {/* 资源栏 */}
        <View style={styles.resourceBar}>
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
          <Text style={styles.sectionTitle}>选择游戏模式</Text>
          
          <ModeCard
            title="闯关模式"
            icon="📚"
            description="按照词库顺序，逐关挑战"
            color="#4F46E5"
            onPress={() => handleModeSelect('campaign')}
          />
          
          <ModeCard
            title="无限模式"
            icon="♾️"
            description="无尽挑战，看你能走多远"
            color="#10B981"
            onPress={() => handleModeSelect('endless')}
          />
          
          <ModeCard
            title="计时模式"
            icon="⏱️"
            description="限时挑战，分秒必争"
            color="#F59E0B"
            onPress={() => handleModeSelect('timed')}
          />
          
          <ModeCard
            title="PK对战"
            icon="⚔️"
            description="与其他玩家实时对战"
            color="#EF4444"
            onPress={() => handleModeSelect('pk')}
          />
        </View>
        
        {/* 底部留白 */}
        <View style={styles.bottomSpacer} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F3F4F6',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    backgroundColor: '#4F46E5',
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 24,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatar: {
    fontSize: 48,
    marginRight: 16,
  },
  nickname: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  welcome: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 4,
  },
  resourceBar: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginTop: -16,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  resourceItem: {
    flex: 1,
    alignItems: 'center',
  },
  resourceIcon: {
    fontSize: 24,
    marginBottom: 4,
  },
  resourceValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1F2937',
  },
  resourceLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  resourceDivider: {
    width: 1,
    backgroundColor: '#E5E7EB',
    marginVertical: 4,
  },
  section: {
    paddingHorizontal: 16,
    marginTop: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 16,
  },
  modeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  modeIcon: {
    fontSize: 36,
    marginRight: 16,
  },
  modeInfo: {
    flex: 1,
  },
  modeTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
  },
  modeDesc: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 4,
  },
  modeArrow: {
    fontSize: 24,
    color: '#9CA3AF',
    fontWeight: '300',
  },
  bottomSpacer: {
    height: 24,
  },
});
