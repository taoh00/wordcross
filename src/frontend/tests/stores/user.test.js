/**
 * 用户状态管理测试
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

// Mock API模块
vi.mock('../../src/api/client.js', () => ({
  userApi: {
    getInfo: vi.fn(() => Promise.resolve({ registered: false })),
    register: vi.fn((name, avatar) => Promise.resolve({
      id: 'test-uuid',
      nickname: name,
      avatar: avatar,
      created_at: new Date().toISOString()
    })),
    update: vi.fn(() => Promise.resolve({ success: true })),
    logout: vi.fn(() => Promise.resolve({ success: true })),
  },
}))

describe('用户状态管理', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应该有正确的初始状态', async () => {
      const { useUserStore } = await import('../../src/stores/user.js')
      const store = useUserStore()
      
      expect(store.nickname).toBe('')
      expect(store.avatar).toBe('😊')
      expect(store.loading).toBe(false)
    })

    it('应该有头像选项列表', async () => {
      const { useUserStore } = await import('../../src/stores/user.js')
      const store = useUserStore()
      
      expect(store.avatarOptions).toBeDefined()
      expect(store.avatarOptions.length).toBeGreaterThan(0)
      expect(store.avatarOptions).toContain('😊')
    })
  })

  describe('isRegistered 计算属性', () => {
    it('未注册时应该返回 false', async () => {
      const { useUserStore } = await import('../../src/stores/user.js')
      const store = useUserStore()
      
      expect(store.isRegistered).toBe(false)
    })

    it('有昵称时应该返回 true', async () => {
      const { useUserStore } = await import('../../src/stores/user.js')
      const store = useUserStore()
      
      store.nickname = '测试用户'
      expect(store.isRegistered).toBe(true)
    })

    it('空白昵称应该返回 false', async () => {
      const { useUserStore } = await import('../../src/stores/user.js')
      const store = useUserStore()
      
      store.nickname = '   '
      expect(store.isRegistered).toBe(false)
    })
  })

  describe('注册功能', () => {
    it('应该正确注册用户', async () => {
      const { useUserStore } = await import('../../src/stores/user.js')
      const store = useUserStore()
      
      const result = await store.register('测试玩家', '🎮')
      
      expect(result).toBe(true)
      expect(store.nickname).toBe('测试玩家')
      expect(store.avatar).toBe('🎮')
      expect(store.id).toBeTruthy()
    })
  })

  describe('头像更新', () => {
    it('应该正确更新头像', async () => {
      const { useUserStore } = await import('../../src/stores/user.js')
      const store = useUserStore()
      
      store.nickname = '测试用户'
      await store.updateAvatar('🐼')
      
      expect(store.avatar).toBe('🐼')
    })
  })

  describe('退出登录', () => {
    it('应该清除用户信息', async () => {
      const { useUserStore } = await import('../../src/stores/user.js')
      const store = useUserStore()
      
      // 先设置用户信息
      store.id = 'test-id'
      store.nickname = '测试用户'
      store.avatar = '🎮'
      
      await store.logout()
      
      expect(store.id).toBe('')
      expect(store.nickname).toBe('')
      expect(store.avatar).toBe('😊')
    })
  })
})
