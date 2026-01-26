/**
 * 填单词游戏 iOS 应用
 * React Native + Expo
 */

import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { Provider } from 'react-redux';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { StyleSheet } from 'react-native';

import { store } from './src/stores';
import AppNavigator from './src/navigation/AppNavigator';
import { initAudio } from './src/utils/audio';

export default function App() {
  // 初始化
  useEffect(() => {
    initAudio();
  }, []);

  return (
    <GestureHandlerRootView style={styles.container}>
      <Provider store={store}>
        <SafeAreaProvider>
          <StatusBar style="auto" />
          <AppNavigator />
        </SafeAreaProvider>
      </Provider>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
