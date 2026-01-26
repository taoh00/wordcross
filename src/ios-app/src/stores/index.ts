/**
 * Redux Store 配置
 */

import { configureStore } from '@reduxjs/toolkit';
import userReducer from './userSlice';
import gameReducer from './gameSlice';
import settingsReducer from './settingsSlice';

export const store = configureStore({
  reducer: {
    user: userReducer,
    game: gameReducer,
    settings: settingsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
