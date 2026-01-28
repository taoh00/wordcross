/**
 * 设置状态管理测试
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Mock localStorage
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn((key) => { delete store[key] }),
    clear: vi.fn(() => { store = {} }),
  }
})()

Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock })

describe('设置状态管理', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应该有正确的默认设置', async () => {
      const { useSettingsStore } = await import('../../src/stores/settings.js')
      const store = useSettingsStore()
      
      // 检查默认设置
      expect(store.autoSpeak).toBe(true)
      expect(store.voiceType).toBe('us')
      expect(store.showTranslation).toBe(true)
      expect(store.bgMusic).toBe(true)
      expect(store.soundEffect).toBe(true)
      expect(store.vibration).toBe(true)
    })
  })

  describe('设置切换', () => {
    it('应该可以直接修改自动发音设置', async () => {
      const { useSettingsStore } = await import('../../src/stores/settings.js')
      const store = useSettingsStore()
      
      expect(store.autoSpeak).toBe(true)
      store.autoSpeak = false
      expect(store.autoSpeak).toBe(false)
    })

    it('应该可以直接修改翻译显示设置', async () => {
      const { useSettingsStore } = await import('../../src/stores/settings.js')
      const store = useSettingsStore()
      
      expect(store.showTranslation).toBe(true)
      store.showTranslation = false
      expect(store.showTranslation).toBe(false)
    })
  })

  describe('发音类型', () => {
    it('应该可以切换发音类型', async () => {
      const { useSettingsStore } = await import('../../src/stores/settings.js')
      const store = useSettingsStore()
      
      expect(store.voiceType).toBe('us')
      store.toggleVoiceType()
      expect(store.voiceType).toBe('uk')
      store.toggleVoiceType()
      expect(store.voiceType).toBe('us')
    })

    it('应该可以直接设置发音类型', async () => {
      const { useSettingsStore } = await import('../../src/stores/settings.js')
      const store = useSettingsStore()
      
      store.voiceType = 'uk'
      expect(store.voiceType).toBe('uk')
    })
  })

  describe('设置保存', () => {
    it('应该有保存设置方法', async () => {
      const { useSettingsStore } = await import('../../src/stores/settings.js')
      const store = useSettingsStore()
      
      expect(typeof store.saveSettings).toBe('function')
    })

    it('应该有加载设置方法', async () => {
      const { useSettingsStore } = await import('../../src/stores/settings.js')
      const store = useSettingsStore()
      
      expect(typeof store.loadSettings).toBe('function')
    })
  })
})
