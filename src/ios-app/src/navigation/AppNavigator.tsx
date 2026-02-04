/**
 * 应用导航配置
 */

import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Text, View, StyleSheet } from 'react-native';

// 页面
import HomeScreen from '../screens/HomeScreen';
import GameScreen from '../screens/GameScreen';
import SettingsScreen from '../screens/SettingsScreen';
import LeaderboardScreen from '../screens/LeaderboardScreen';
import LevelSelectScreen from '../screens/LevelSelectScreen';
import VocabSelectScreen from '../screens/VocabSelectScreen';

// 类型定义
export type RootStackParamList = {
  MainTabs: undefined;
  Game: {
    mode: 'campaign' | 'endless' | 'timed' | 'pk';
    group: string;
    groupName: string;
    level?: number;
  };
  LevelSelect: {
    group: string;
    groupName: string;
  };
  VocabSelect: {
    mode: 'campaign' | 'endless' | 'timed' | 'pk';
  };
};

export type TabParamList = {
  Home: undefined;
  Leaderboard: undefined;
  Settings: undefined;
};

const Stack = createStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<TabParamList>();

/** Tab 图标 */
function TabIcon({ name, focused }: { name: string; focused: boolean }) {
  const icons: Record<string, string> = {
    Home: '🏠',
    Leaderboard: '🏆',
    Settings: '⚙️',
  };
  
  return (
    <View style={styles.tabIcon}>
      <Text style={[styles.tabIconText, focused && styles.tabIconActive]}>
        {icons[name] || '📱'}
      </Text>
    </View>
  );
}

/** 底部 Tab 导航 */
function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarIcon: ({ focused }) => (
          <TabIcon name={route.name} focused={focused} />
        ),
        tabBarActiveTintColor: '#FF69B4',
        tabBarInactiveTintColor: '#9CA3AF',
        tabBarStyle: styles.tabBar,
        tabBarLabelStyle: styles.tabLabel,
      })}
    >
      <Tab.Screen 
        name="Home" 
        component={HomeScreen}
        options={{ tabBarLabel: '首页' }}
      />
      <Tab.Screen 
        name="Leaderboard" 
        component={LeaderboardScreen}
        options={{ tabBarLabel: '排行榜' }}
      />
      <Tab.Screen 
        name="Settings" 
        component={SettingsScreen}
        options={{ tabBarLabel: '设置' }}
      />
    </Tab.Navigator>
  );
}

/** 根导航器 */
export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerStyle: {
            backgroundColor: '#FF69B4',
          },
          headerTintColor: '#fff',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        }}
      >
        <Stack.Screen
          name="MainTabs"
          component={MainTabs}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="VocabSelect"
          component={VocabSelectScreen}
          options={{ title: '选择词库' }}
        />
        <Stack.Screen
          name="LevelSelect"
          component={LevelSelectScreen}
          options={({ route }) => ({ 
            title: route.params.groupName 
          })}
        />
        <Stack.Screen
          name="Game"
          component={GameScreen}
          options={({ route }) => ({
            title: route.params.groupName,
            headerBackTitle: '返回',
          })}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    height: 60,
    paddingBottom: 8,
    paddingTop: 8,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#FFB6C1',
  },
  tabLabel: {
    fontSize: 12,
    fontWeight: '500',
  },
  tabIcon: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabIconText: {
    fontSize: 24,
    opacity: 0.6,
  },
  tabIconActive: {
    opacity: 1,
  },
});
