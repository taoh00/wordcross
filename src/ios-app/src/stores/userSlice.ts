/**
 * 用户状态管理
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { userApi, energyApi, propsApi, trackApi } from '../api';

interface UserState {
  // 用户信息
  id: string | null;
  nickname: string;
  avatar: string;
  registered: boolean;
  
  // 体力
  energy: number;
  maxEnergy: number;
  
  // 道具
  hintCount: number;
  speakCount: number;
  
  // 状态
  loading: boolean;
  error: string | null;
}

const initialState: UserState = {
  id: null,
  nickname: '游客',
  avatar: '👤',
  registered: false,
  energy: 100,
  maxEnergy: 100,
  hintCount: 3,
  speakCount: 3,
  loading: false,
  error: null,
};

// 异步 thunks

/** 初始化用户 */
export const initUser = createAsyncThunk(
  'user/init',
  async (_, { dispatch }) => {
    // 尝试从本地获取用户 ID
    const userId = await AsyncStorage.getItem('userId');
    
    if (userId) {
      // 获取用户信息
      const info = await userApi.getInfo();
      if (info.registered && info.id) {
        // 同时获取体力和道具
        const [energyData, propsData] = await Promise.all([
          energyApi.get(),
          propsApi.get(),
        ]);
        
        return {
          id: info.id,
          nickname: info.nickname || '用户',
          avatar: info.avatar || '👤',
          registered: true,
          energy: energyData.energy,
          maxEnergy: energyData.max_energy,
          hintCount: propsData.hintLetterCount,
          speakCount: propsData.showTranslationCount,
        };
      }
    }
    
    // 未注册，创建新用户
    const randomId = `guest_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    await AsyncStorage.setItem('userId', randomId);
    
    return {
      id: randomId,
      nickname: '游客',
      avatar: '👤',
      registered: false,
      energy: 100,
      maxEnergy: 100,
      hintCount: 3,
      speakCount: 3,
    };
  }
);

/** 注册用户 */
export const registerUser = createAsyncThunk(
  'user/register',
  async ({ nickname, avatar }: { nickname: string; avatar?: string }) => {
    const result = await userApi.register(nickname, avatar);
    await AsyncStorage.setItem('userId', result.id);
    return {
      id: result.id,
      nickname: result.nickname,
      avatar: result.avatar,
      registered: true,
    };
  }
);

/** 更新用户信息 */
export const updateUser = createAsyncThunk(
  'user/update',
  async ({ nickname, avatar }: { nickname?: string; avatar?: string }) => {
    await userApi.update(nickname, avatar);
    return { nickname, avatar };
  }
);

/** 刷新体力 */
export const refreshEnergy = createAsyncThunk(
  'user/refreshEnergy',
  async () => {
    const data = await energyApi.get();
    return { energy: data.energy, maxEnergy: data.max_energy };
  }
);

/** 消耗体力 */
export const consumeEnergy = createAsyncThunk(
  'user/consumeEnergy',
  async ({ amount, mode }: { amount: number; mode: string }) => {
    const result = await energyApi.consume(amount, mode);
    return { energy: result.energy };
  }
);

/** 领取免费体力（带埋点） */
export const claimFreeEnergy = createAsyncThunk(
  'user/claimFreeEnergy',
  async () => {
    // 使用带埋点的API
    const result = await trackApi.claimFreeEnergyTracked(30, 'ios');
    if (!result) {
      // 回退到普通API
      const fallbackResult = await energyApi.claimFree();
      return { energy: fallbackResult.energy, amount: fallbackResult.amount_claimed };
    }
    return { energy: result.energy, amount: 30 };
  }
);

/** 刷新道具 */
export const refreshProps = createAsyncThunk(
  'user/refreshProps',
  async () => {
    const data = await propsApi.get();
    return {
      hintCount: data.hintLetterCount,
      speakCount: data.showTranslationCount,
    };
  }
);

/** 使用道具 */
export const useProp = createAsyncThunk(
  'user/useProp',
  async ({ propType, amount = 1 }: { propType: string; amount?: number }) => {
    const result = await propsApi.use(propType, amount);
    return { propType, remaining: result.remaining };
  }
);

// Slice
const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setEnergy: (state, action: PayloadAction<number>) => {
      state.energy = action.payload;
    },
    setProps: (state, action: PayloadAction<{ hintCount?: number; speakCount?: number }>) => {
      if (action.payload.hintCount !== undefined) {
        state.hintCount = action.payload.hintCount;
      }
      if (action.payload.speakCount !== undefined) {
        state.speakCount = action.payload.speakCount;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      // initUser
      .addCase(initUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(initUser.fulfilled, (state, action) => {
        state.loading = false;
        Object.assign(state, action.payload);
      })
      .addCase(initUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '初始化失败';
      })
      
      // registerUser
      .addCase(registerUser.fulfilled, (state, action) => {
        Object.assign(state, action.payload);
      })
      
      // updateUser
      .addCase(updateUser.fulfilled, (state, action) => {
        if (action.payload.nickname) state.nickname = action.payload.nickname;
        if (action.payload.avatar) state.avatar = action.payload.avatar;
      })
      
      // refreshEnergy
      .addCase(refreshEnergy.fulfilled, (state, action) => {
        state.energy = action.payload.energy;
        state.maxEnergy = action.payload.maxEnergy;
      })
      
      // consumeEnergy
      .addCase(consumeEnergy.fulfilled, (state, action) => {
        state.energy = action.payload.energy;
      })
      
      // claimFreeEnergy
      .addCase(claimFreeEnergy.fulfilled, (state, action) => {
        state.energy = action.payload.energy;
      })
      
      // refreshProps
      .addCase(refreshProps.fulfilled, (state, action) => {
        state.hintCount = action.payload.hintCount;
        state.speakCount = action.payload.speakCount;
      })
      
      // useProp
      .addCase(useProp.fulfilled, (state, action) => {
        if (action.payload.propType === 'hint') {
          state.hintCount = action.payload.remaining;
        } else if (action.payload.propType === 'speak') {
          state.speakCount = action.payload.remaining;
        }
      });
  },
});

export const { clearError, setEnergy, setProps } = userSlice.actions;
export default userSlice.reducer;
