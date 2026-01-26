/**
 * 设置状态管理
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface SettingsState {
  // 音效
  soundEnabled: boolean;
  
  // 音频类型
  audioType: 'us' | 'uk';
  
  // 自动发音
  autoSpeak: boolean;
  
  // 显示翻译
  showTranslation: boolean;
  
  // 震动反馈
  hapticEnabled: boolean;
  
  // 主题
  theme: 'light' | 'dark' | 'system';
}

const initialState: SettingsState = {
  soundEnabled: true,
  audioType: 'us',
  autoSpeak: true,
  showTranslation: true,
  hapticEnabled: true,
  theme: 'system',
};

const STORAGE_KEY = 'wordcross_settings';

// 异步 thunks

/** 加载设置 */
export const loadSettings = createAsyncThunk(
  'settings/load',
  async () => {
    const saved = await AsyncStorage.getItem(STORAGE_KEY);
    if (saved) {
      return JSON.parse(saved) as Partial<SettingsState>;
    }
    return {};
  }
);

/** 保存设置 */
export const saveSettings = createAsyncThunk(
  'settings/save',
  async (settings: SettingsState) => {
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }
);

// Slice
const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    toggleSound: (state) => {
      state.soundEnabled = !state.soundEnabled;
    },
    setAudioType: (state, action: PayloadAction<'us' | 'uk'>) => {
      state.audioType = action.payload;
    },
    toggleAutoSpeak: (state) => {
      state.autoSpeak = !state.autoSpeak;
    },
    toggleShowTranslation: (state) => {
      state.showTranslation = !state.showTranslation;
    },
    toggleHaptic: (state) => {
      state.hapticEnabled = !state.hapticEnabled;
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'system'>) => {
      state.theme = action.payload;
    },
    resetSettings: () => initialState,
  },
  extraReducers: (builder) => {
    builder.addCase(loadSettings.fulfilled, (state, action) => {
      Object.assign(state, action.payload);
    });
  },
});

export const {
  toggleSound,
  setAudioType,
  toggleAutoSpeak,
  toggleShowTranslation,
  toggleHaptic,
  setTheme,
  resetSettings,
} = settingsSlice.actions;

export default settingsSlice.reducer;
