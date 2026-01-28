/**
 * 游戏状态管理测试
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Mock API模块
vi.mock('../../src/api/index.js', () => ({
  gameApi: {
    getEndlessPuzzle: vi.fn(),
    getTimedPuzzle: vi.fn(),
    submitScore: vi.fn(),
  },
  staticApi: {
    getLevelsSummary: vi.fn(),
    getLevelData: vi.fn(),
  },
  buildUrl: vi.fn((path) => path),
}))

describe('游戏状态管理', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应该有正确的初始状态', async () => {
      const { useGameStore } = await import('../../src/stores/game.js')
      const store = useGameStore()
      
      expect(store.currentGroup).toBe('primary')
      expect(store.currentMode).toBe('campaign')
      expect(store.currentLevel).toBe(1)
      expect(store.puzzle).toBeNull()
      expect(store.score).toBe(0)
      expect(store.timer).toBe(0)
      expect(store.isPlaying).toBe(false)
    })

    it('应该有词库组别列表', async () => {
      const { useGameStore } = await import('../../src/stores/game.js')
      const store = useGameStore()
      
      expect(store.groups).toBeDefined()
      expect(store.groups.length).toBeGreaterThan(0)
      
      // 检查主要分类
      const primaryGroup = store.groups.find(g => g.code === 'primary')
      expect(primaryGroup).toBeDefined()
      expect(primaryGroup.name).toBe('小学词汇')
      expect(primaryGroup.hasSubGroups).toBe(true)
    })
  })

  describe('计算属性', () => {
    it('gridSize 应该返回默认值', async () => {
      const { useGameStore } = await import('../../src/stores/game.js')
      const store = useGameStore()
      
      expect(store.gridSize).toBe(5)
    })

    it('progress 应该在没有谜题时返回 0', async () => {
      const { useGameStore } = await import('../../src/stores/game.js')
      const store = useGameStore()
      
      expect(store.progress).toBe(0)
    })

    it('isLevelComplete 应该在没有谜题时返回 false', async () => {
      const { useGameStore } = await import('../../src/stores/game.js')
      const store = useGameStore()
      
      expect(store.isLevelComplete).toBe(false)
    })

    it('formattedTimer 应该正确格式化', async () => {
      const { useGameStore } = await import('../../src/stores/game.js')
      const store = useGameStore()
      
      expect(store.formattedTimer).toBe('00:00')
      
      store.timer = 125
      expect(store.formattedTimer).toBe('02:05')
    })
  })

  describe('词库组别', () => {
    it('应该包含小学词库子分组', async () => {
      const { useGameStore } = await import('../../src/stores/game.js')
      const store = useGameStore()
      
      const primary = store.groups.find(g => g.code === 'primary')
      expect(primary.subGroups).toBeDefined()
      expect(primary.subGroups.length).toBeGreaterThan(0)
      
      // 检查子分组
      const grade3 = primary.subGroups.find(sg => sg.code === 'grade3_1')
      expect(grade3).toBeDefined()
      expect(grade3.name).toBe('三年级上册')
    })

    it('应该包含初中词库子分组', async () => {
      const { useGameStore } = await import('../../src/stores/game.js')
      const store = useGameStore()
      
      const junior = store.groups.find(g => g.code === 'junior')
      expect(junior.subGroups).toBeDefined()
      expect(junior.subGroups.find(sg => sg.code === 'junior7_1')).toBeDefined()
    })

    it('应该包含高中词库子分组', async () => {
      const { useGameStore } = await import('../../src/stores/game.js')
      const store = useGameStore()
      
      const senior = store.groups.find(g => g.code === 'senior')
      expect(senior.subGroups).toBeDefined()
      expect(senior.subGroups.find(sg => sg.code === 'senior1')).toBeDefined()
    })

    it('应该包含考试词库', async () => {
      const { useGameStore } = await import('../../src/stores/game.js')
      const store = useGameStore()
      
      const examGroups = ['ket', 'pet', 'cet4', 'cet6', 'ielts', 'toefl', 'gre']
      
      examGroups.forEach(code => {
        const group = store.groups.find(g => g.code === code)
        expect(group).toBeDefined()
      })
    })
  })
})
