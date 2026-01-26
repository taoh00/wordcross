/**
 * 词库选择页面
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import { staticApi } from '../api';

type NavigationProp = StackNavigationProp<RootStackParamList, 'VocabSelect'>;
type RouteType = RouteProp<RootStackParamList, 'VocabSelect'>;

/** 词库分组配置 */
const VOCAB_GROUPS = [
  {
    category: '小学词汇',
    icon: '📚',
    groups: [
      { code: 'grade3_1', name: '三年级上册', icon: '🌱' },
      { code: 'grade3_2', name: '三年级下册', icon: '🌿' },
      { code: 'grade4_1', name: '四年级上册', icon: '🌲' },
      { code: 'grade4_2', name: '四年级下册', icon: '🌳' },
      { code: 'grade5_1', name: '五年级上册', icon: '🌴' },
      { code: 'grade5_2', name: '五年级下册', icon: '🌵' },
      { code: 'grade6_1', name: '六年级上册', icon: '🎋' },
      { code: 'grade6_2', name: '六年级下册', icon: '🎍' },
      { code: 'primary_all', name: '小学全部', icon: '📚' },
    ],
  },
  {
    category: '初中词汇',
    icon: '📖',
    groups: [
      { code: 'junior7_1', name: '七年级上册', icon: '📗' },
      { code: 'junior7_2', name: '七年级下册', icon: '📘' },
      { code: 'junior8_1', name: '八年级上册', icon: '📙' },
      { code: 'junior8_2', name: '八年级下册', icon: '📕' },
      { code: 'junior9', name: '九年级全册', icon: '📓' },
      { code: 'junior', name: '初中词汇', icon: '📔' },
      { code: 'junior_all', name: '初中全部', icon: '📖' },
    ],
  },
  {
    category: '高中词汇',
    icon: '📕',
    groups: [
      { code: 'senior1', name: '必修1', icon: '1️⃣' },
      { code: 'senior2', name: '必修2', icon: '2️⃣' },
      { code: 'senior3', name: '必修3', icon: '3️⃣' },
      { code: 'senior4', name: '必修4', icon: '4️⃣' },
      { code: 'senior5', name: '必修5', icon: '5️⃣' },
      { code: 'senior', name: '高中词汇', icon: '📚' },
      { code: 'senior_all', name: '高中全部', icon: '📕' },
    ],
  },
  {
    category: '考试词汇',
    icon: '🎯',
    groups: [
      { code: 'ket', name: 'KET考试', icon: '🅰️' },
      { code: 'pet', name: 'PET考试', icon: '🅱️' },
      { code: 'cet4', name: '大学四级', icon: '4️⃣' },
      { code: 'cet6', name: '大学六级', icon: '6️⃣' },
      { code: 'postgrad', name: '考研词汇', icon: '🎓' },
      { code: 'ielts', name: '雅思', icon: '🌍' },
      { code: 'toefl', name: '托福', icon: '🗽' },
      { code: 'gre', name: 'GRE', icon: '🎖️' },
    ],
  },
];

export default function VocabSelectScreen() {
  const navigation = useNavigation<NavigationProp>();
  const route = useRoute<RouteType>();
  const { mode } = route.params;
  
  const [loading, setLoading] = useState(true);
  const [levelCounts, setLevelCounts] = useState<Record<string, number>>({});
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);
  
  // 加载词库信息
  useEffect(() => {
    loadVocabInfo();
  }, []);
  
  const loadVocabInfo = async () => {
    try {
      const summary = await staticApi.getSummary();
      const counts: Record<string, number> = {};
      summary.groups.forEach((g) => {
        counts[g.group_code] = g.level_count;
      });
      setLevelCounts(counts);
    } catch (error) {
      console.warn('加载词库信息失败:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // 选择词库
  const handleSelectGroup = (code: string, name: string) => {
    if (mode === 'campaign') {
      // 闯关模式进入关卡选择
      navigation.navigate('LevelSelect', { group: code, groupName: name });
    } else {
      // 其他模式直接开始游戏
      navigation.navigate('Game', {
        mode,
        group: code,
        groupName: name,
        level: 1,
      });
    }
  };
  
  // 切换分类展开
  const toggleCategory = (category: string) => {
    setExpandedCategory(expandedCategory === category ? null : category);
  };
  
  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4F46E5" />
        <Text style={styles.loadingText}>加载词库...</Text>
      </View>
    );
  }
  
  return (
    <ScrollView style={styles.container}>
      {VOCAB_GROUPS.map((category) => (
        <View key={category.category} style={styles.categoryContainer}>
          {/* 分类标题 */}
          <TouchableOpacity
            style={styles.categoryHeader}
            onPress={() => toggleCategory(category.category)}
          >
            <Text style={styles.categoryIcon}>{category.icon}</Text>
            <Text style={styles.categoryTitle}>{category.category}</Text>
            <Text style={styles.categoryArrow}>
              {expandedCategory === category.category ? '▼' : '▶'}
            </Text>
          </TouchableOpacity>
          
          {/* 词库列表 */}
          {expandedCategory === category.category && (
            <View style={styles.groupList}>
              {category.groups.map((group) => (
                <TouchableOpacity
                  key={group.code}
                  style={styles.groupItem}
                  onPress={() => handleSelectGroup(group.code, group.name)}
                >
                  <Text style={styles.groupIcon}>{group.icon}</Text>
                  <View style={styles.groupInfo}>
                    <Text style={styles.groupName}>{group.name}</Text>
                    <Text style={styles.groupLevels}>
                      {levelCounts[group.code] || 0} 关
                    </Text>
                  </View>
                  <Text style={styles.groupArrow}>›</Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </View>
      ))}
      
      <View style={styles.bottomSpacer} />
    </ScrollView>
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
    backgroundColor: '#F3F4F6',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#6B7280',
  },
  categoryContainer: {
    marginTop: 16,
    marginHorizontal: 16,
  },
  categoryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  categoryIcon: {
    fontSize: 28,
    marginRight: 12,
  },
  categoryTitle: {
    flex: 1,
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
  },
  categoryArrow: {
    fontSize: 14,
    color: '#9CA3AF',
  },
  groupList: {
    marginTop: 8,
    backgroundColor: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
  },
  groupItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  groupIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  groupInfo: {
    flex: 1,
  },
  groupName: {
    fontSize: 16,
    color: '#1F2937',
  },
  groupLevels: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 2,
  },
  groupArrow: {
    fontSize: 20,
    color: '#9CA3AF',
  },
  bottomSpacer: {
    height: 32,
  },
});
