import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  // 默认设置
  const defaultSettings = {
    autoSpeak: true,       // 单词填对后自动播放发音
    voiceType: 'us',       // 发音类型: 'us' 或 'uk'
    bgMusic: true,         // 背景音乐（默认开启）
    soundEffect: true,     // 音效
    vibration: true,       // 震动反馈
    showTranslation: true  // 显示翻译（默认打开）
  }

  // 设置状态
  const autoSpeak = ref(defaultSettings.autoSpeak)
  const voiceType = ref(defaultSettings.voiceType)
  const bgMusic = ref(defaultSettings.bgMusic)
  const soundEffect = ref(defaultSettings.soundEffect)
  const vibration = ref(defaultSettings.vibration)
  const showTranslation = ref(defaultSettings.showTranslation)

  // 从 localStorage 加载设置
  function loadSettings() {
    try {
      const saved = localStorage.getItem('game_settings')
      if (saved) {
        const settings = JSON.parse(saved)
        autoSpeak.value = settings.autoSpeak ?? defaultSettings.autoSpeak
        voiceType.value = settings.voiceType ?? defaultSettings.voiceType
        bgMusic.value = settings.bgMusic ?? defaultSettings.bgMusic
        soundEffect.value = settings.soundEffect ?? defaultSettings.soundEffect
        vibration.value = settings.vibration ?? defaultSettings.vibration
        showTranslation.value = settings.showTranslation ?? defaultSettings.showTranslation
      }
    } catch (e) {
      console.warn('加载设置失败:', e)
    }
  }

  // 保存设置到 localStorage
  function saveSettings() {
    try {
      const settings = {
        autoSpeak: autoSpeak.value,
        voiceType: voiceType.value,
        bgMusic: bgMusic.value,
        soundEffect: soundEffect.value,
        vibration: vibration.value,
        showTranslation: showTranslation.value
      }
      localStorage.setItem('game_settings', JSON.stringify(settings))
    } catch (e) {
      console.warn('保存设置失败:', e)
    }
  }

  // 监听变化自动保存
  watch([autoSpeak, voiceType, bgMusic, soundEffect, vibration, showTranslation], () => {
    saveSettings()
  })

  // 初始化加载
  loadSettings()

  // 切换发音类型
  function toggleVoiceType() {
    voiceType.value = voiceType.value === 'us' ? 'uk' : 'us'
  }

  return {
    autoSpeak,
    voiceType,
    bgMusic,
    soundEffect,
    vibration,
    showTranslation,
    loadSettings,
    saveSettings,
    toggleVoiceType
  }
})
