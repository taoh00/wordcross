/**
 * 音频播放工具
 */

import { Audio } from 'expo-av';
import { API_BASE } from '../api';

let currentSound: Audio.Sound | null = null;

/**
 * 播放单词发音
 * @param word 单词
 * @param type 发音类型 (us/uk)
 */
export async function speakWord(word: string, type: 'us' | 'uk' = 'us'): Promise<void> {
  try {
    // 停止并卸载当前音频
    if (currentSound) {
      await currentSound.stopAsync();
      await currentSound.unloadAsync();
      currentSound = null;
    }
    
    // 构建音频 URL
    const audioUrl = `${API_BASE}/data/audio/${type}/${word.toLowerCase()}.mp3`;
    
    // 加载并播放
    const { sound } = await Audio.Sound.createAsync(
      { uri: audioUrl },
      { shouldPlay: true }
    );
    
    currentSound = sound;
    
    // 播放完成后清理
    sound.setOnPlaybackStatusUpdate((status) => {
      if (status.isLoaded && status.didJustFinish) {
        sound.unloadAsync();
        if (currentSound === sound) {
          currentSound = null;
        }
      }
    });
  } catch (error) {
    console.warn('音频播放失败:', error);
    // 尝试使用在线 TTS API
    await speakWordOnline(word, type);
  }
}

/**
 * 使用在线 TTS API
 */
async function speakWordOnline(word: string, type: 'us' | 'uk'): Promise<void> {
  try {
    const ttsUrl = type === 'us'
      ? `https://dict.youdao.com/dictvoice?audio=${encodeURIComponent(word)}&type=2`
      : `https://dict.youdao.com/dictvoice?audio=${encodeURIComponent(word)}&type=1`;
    
    const { sound } = await Audio.Sound.createAsync(
      { uri: ttsUrl },
      { shouldPlay: true }
    );
    
    currentSound = sound;
    
    sound.setOnPlaybackStatusUpdate((status) => {
      if (status.isLoaded && status.didJustFinish) {
        sound.unloadAsync();
        if (currentSound === sound) {
          currentSound = null;
        }
      }
    });
  } catch (error) {
    console.warn('在线发音失败:', error);
  }
}

/**
 * 播放音效
 * @param soundName 音效名称
 */
export async function playSound(soundName: 'correct' | 'wrong' | 'complete' | 'click'): Promise<void> {
  // TODO: 添加本地音效文件
  // 暂时不实现
}

/**
 * 停止当前播放
 */
export async function stopAudio(): Promise<void> {
  if (currentSound) {
    try {
      await currentSound.stopAsync();
      await currentSound.unloadAsync();
    } catch (error) {
      // 忽略错误
    }
    currentSound = null;
  }
}

/**
 * 初始化音频模块
 */
export async function initAudio(): Promise<void> {
  try {
    await Audio.setAudioModeAsync({
      allowsRecordingIOS: false,
      playsInSilentModeIOS: true,
      staysActiveInBackground: false,
      shouldDuckAndroid: true,
    });
  } catch (error) {
    console.warn('音频初始化失败:', error);
  }
}
