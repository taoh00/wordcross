/**
 * 设置页面
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Switch,
  Alert,
  TextInput,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAppDispatch, useAppSelector } from '../stores/hooks';
import { updateUser } from '../stores/userSlice';
import {
  toggleSound,
  setAudioType,
  toggleAutoSpeak,
  toggleShowTranslation,
  toggleHaptic,
  setTheme,
  saveSettings,
  loadSettings,
} from '../stores/settingsSlice';

/** 设置项组件 */
interface SettingItemProps {
  icon: string;
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
  onPress?: () => void;
}

function SettingItem({ icon, title, subtitle, right, onPress }: SettingItemProps) {
  const content = (
    <View style={styles.settingItem}>
      <Text style={styles.settingIcon}>{icon}</Text>
      <View style={styles.settingInfo}>
        <Text style={styles.settingTitle}>{title}</Text>
        {subtitle && <Text style={styles.settingSubtitle}>{subtitle}</Text>}
      </View>
      {right}
    </View>
  );
  
  if (onPress) {
    return (
      <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
        {content}
      </TouchableOpacity>
    );
  }
  
  return content;
}

/** 设置分组组件 */
function SettingGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.settingGroup}>
      <Text style={styles.groupTitle}>{title}</Text>
      <View style={styles.groupContent}>{children}</View>
    </View>
  );
}

export default function SettingsScreen() {
  const dispatch = useAppDispatch();
  const { nickname, avatar } = useAppSelector((state) => state.user);
  const settings = useAppSelector((state) => state.settings);
  
  const [editingNickname, setEditingNickname] = useState(false);
  const [tempNickname, setTempNickname] = useState(nickname);
  
  // 加载设置
  useEffect(() => {
    dispatch(loadSettings());
  }, []);
  
  // 保存设置
  const handleSaveSettings = () => {
    dispatch(saveSettings(settings));
  };
  
  // 修改昵称
  const handleUpdateNickname = async () => {
    if (!tempNickname.trim()) {
      Alert.alert('提示', '昵称不能为空');
      return;
    }
    
    try {
      await dispatch(updateUser({ nickname: tempNickname.trim() })).unwrap();
      setEditingNickname(false);
      Alert.alert('成功', '昵称已更新');
    } catch (error) {
      Alert.alert('失败', '更新昵称失败');
    }
  };
  
  // 切换发音类型
  const handleToggleAudioType = () => {
    const newType = settings.audioType === 'us' ? 'uk' : 'us';
    dispatch(setAudioType(newType));
    handleSaveSettings();
  };
  
  // 清除缓存
  const handleClearCache = () => {
    Alert.alert(
      '清除缓存',
      '确定要清除所有本地缓存数据吗？这不会影响您的游戏进度。',
      [
        { text: '取消', style: 'cancel' },
        {
          text: '确定',
          style: 'destructive',
          onPress: async () => {
            // 保留重要数据
            const userId = await AsyncStorage.getItem('userId');
            const progressKeys = (await AsyncStorage.getAllKeys()).filter(
              (k) => k.startsWith('progress_')
            );
            const progressData: Record<string, string> = {};
            for (const key of progressKeys) {
              const value = await AsyncStorage.getItem(key);
              if (value) progressData[key] = value;
            }
            
            // 清除所有数据
            await AsyncStorage.clear();
            
            // 恢复重要数据
            if (userId) await AsyncStorage.setItem('userId', userId);
            for (const [key, value] of Object.entries(progressData)) {
              await AsyncStorage.setItem(key, value);
            }
            
            Alert.alert('成功', '缓存已清除');
          },
        },
      ]
    );
  };
  
  // 重置进度
  const handleResetProgress = () => {
    Alert.alert(
      '重置进度',
      '确定要重置所有游戏进度吗？此操作不可恢复！',
      [
        { text: '取消', style: 'cancel' },
        {
          text: '确定重置',
          style: 'destructive',
          onPress: async () => {
            const allKeys = await AsyncStorage.getAllKeys();
            const progressKeys = allKeys.filter((k) => k.startsWith('progress_'));
            await AsyncStorage.multiRemove(progressKeys);
            Alert.alert('成功', '游戏进度已重置');
          },
        },
      ]
    );
  };
  
  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView style={styles.scrollView}>
        {/* 用户信息 */}
        <SettingGroup title="用户信息">
          <SettingItem
            icon={avatar}
            title="头像"
            subtitle="点击更换头像"
            onPress={() => {
              const avatars = ['👤', '😀', '😎', '🤓', '🦊', '🐱', '🐶', '🦁', '🐼', '🐨'];
              const currentIndex = avatars.indexOf(avatar);
              const nextAvatar = avatars[(currentIndex + 1) % avatars.length];
              dispatch(updateUser({ avatar: nextAvatar }));
            }}
            right={<Text style={styles.arrowIcon}>›</Text>}
          />
          
          {editingNickname ? (
            <View style={styles.settingItem}>
              <Text style={styles.settingIcon}>✏️</Text>
              <TextInput
                style={styles.nicknameInput}
                value={tempNickname}
                onChangeText={setTempNickname}
                placeholder="输入昵称"
                maxLength={12}
                autoFocus
              />
              <TouchableOpacity onPress={handleUpdateNickname}>
                <Text style={styles.saveButton}>保存</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <SettingItem
              icon="✏️"
              title="昵称"
              subtitle={nickname}
              onPress={() => {
                setTempNickname(nickname);
                setEditingNickname(true);
              }}
              right={<Text style={styles.arrowIcon}>›</Text>}
            />
          )}
        </SettingGroup>
        
        {/* 游戏设置 */}
        <SettingGroup title="游戏设置">
          <SettingItem
            icon="🔊"
            title="音效"
            subtitle="开启游戏音效"
            right={
              <Switch
                value={settings.soundEnabled}
                onValueChange={() => {
                  dispatch(toggleSound());
                  handleSaveSettings();
                }}
                trackColor={{ false: '#E5E7EB', true: '#4F46E5' }}
              />
            }
          />
          
          <SettingItem
            icon="🗣️"
            title="自动发音"
            subtitle="选中单词时自动播放发音"
            right={
              <Switch
                value={settings.autoSpeak}
                onValueChange={() => {
                  dispatch(toggleAutoSpeak());
                  handleSaveSettings();
                }}
                trackColor={{ false: '#E5E7EB', true: '#4F46E5' }}
              />
            }
          />
          
          <SettingItem
            icon="🌍"
            title="发音类型"
            subtitle={settings.audioType === 'us' ? '美式发音' : '英式发音'}
            onPress={handleToggleAudioType}
            right={<Text style={styles.arrowIcon}>›</Text>}
          />
          
          <SettingItem
            icon="📝"
            title="显示翻译"
            subtitle="显示单词的中文释义"
            right={
              <Switch
                value={settings.showTranslation}
                onValueChange={() => {
                  dispatch(toggleShowTranslation());
                  handleSaveSettings();
                }}
                trackColor={{ false: '#E5E7EB', true: '#4F46E5' }}
              />
            }
          />
          
          <SettingItem
            icon="📳"
            title="震动反馈"
            subtitle="操作时触发震动"
            right={
              <Switch
                value={settings.hapticEnabled}
                onValueChange={() => {
                  dispatch(toggleHaptic());
                  handleSaveSettings();
                }}
                trackColor={{ false: '#E5E7EB', true: '#4F46E5' }}
              />
            }
          />
        </SettingGroup>
        
        {/* 数据管理 */}
        <SettingGroup title="数据管理">
          <SettingItem
            icon="🗑️"
            title="清除缓存"
            subtitle="清除本地缓存数据"
            onPress={handleClearCache}
            right={<Text style={styles.arrowIcon}>›</Text>}
          />
          
          <SettingItem
            icon="🔄"
            title="重置进度"
            subtitle="重置所有游戏进度"
            onPress={handleResetProgress}
            right={<Text style={[styles.arrowIcon, styles.dangerText]}>›</Text>}
          />
        </SettingGroup>
        
        {/* 关于 */}
        <SettingGroup title="关于">
          <SettingItem
            icon="ℹ️"
            title="版本"
            subtitle="1.0.0"
          />
          
          <SettingItem
            icon="📧"
            title="反馈"
            subtitle="问题反馈与建议"
            onPress={() => Alert.alert('反馈', '请发送邮件至 feedback@wordcross.app')}
            right={<Text style={styles.arrowIcon}>›</Text>}
          />
        </SettingGroup>
        
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
  settingGroup: {
    marginTop: 24,
    marginHorizontal: 16,
  },
  groupTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 8,
    marginLeft: 4,
  },
  groupContent: {
    backgroundColor: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  settingIcon: {
    fontSize: 24,
    marginRight: 14,
  },
  settingInfo: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    color: '#1F2937',
  },
  settingSubtitle: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 2,
  },
  arrowIcon: {
    fontSize: 20,
    color: '#9CA3AF',
  },
  nicknameInput: {
    flex: 1,
    fontSize: 16,
    color: '#1F2937',
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 6,
    marginRight: 12,
  },
  saveButton: {
    fontSize: 16,
    color: '#4F46E5',
    fontWeight: '600',
  },
  dangerText: {
    color: '#EF4444',
  },
  bottomSpacer: {
    height: 40,
  },
});
