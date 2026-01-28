/**
 * 工具函数测试
 */
import { describe, it, expect } from 'vitest'

describe('工具函数', () => {
  describe('格式化时间', () => {
    it('应该正确格式化秒数', () => {
      const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60)
        const secs = seconds % 60
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
      }
      
      expect(formatTime(0)).toBe('00:00')
      expect(formatTime(59)).toBe('00:59')
      expect(formatTime(60)).toBe('01:00')
      expect(formatTime(125)).toBe('02:05')
      expect(formatTime(3661)).toBe('61:01')
    })
  })

  describe('单词验证', () => {
    it('应该验证纯字母单词', () => {
      const isPureAlpha = (word) => /^[a-zA-Z]+$/.test(word)
      
      expect(isPureAlpha('hello')).toBe(true)
      expect(isPureAlpha('WORLD')).toBe(true)
      expect(isPureAlpha('hello-world')).toBe(false)
      expect(isPureAlpha("it's")).toBe(false)
      expect(isPureAlpha('')).toBe(false)
    })
  })

  describe('格子键值转换', () => {
    it('应该正确生成格子键', () => {
      const cellKey = (row, col) => `${row}-${col}`
      
      expect(cellKey(0, 0)).toBe('0-0')
      expect(cellKey(5, 10)).toBe('5-10')
    })

    it('应该正确解析格子键', () => {
      const parseKey = (key) => {
        const [row, col] = key.split('-').map(Number)
        return { row, col }
      }
      
      expect(parseKey('0-0')).toEqual({ row: 0, col: 0 })
      expect(parseKey('5-10')).toEqual({ row: 5, col: 10 })
    })
  })

  describe('进度计算', () => {
    it('应该正确计算进度', () => {
      const calculateProgress = (completed, total) => {
        if (total === 0) return 0
        return Math.round((completed / total) * 100)
      }
      
      expect(calculateProgress(0, 10)).toBe(0)
      expect(calculateProgress(5, 10)).toBe(50)
      expect(calculateProgress(10, 10)).toBe(100)
      expect(calculateProgress(0, 0)).toBe(0)
    })
  })

  describe('UUID验证', () => {
    it('应该验证UUID格式', () => {
      const isValidUUID = (str) => {
        const regex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
        return regex.test(str)
      }
      
      expect(isValidUUID('123e4567-e89b-12d3-a456-426614174000')).toBe(true)
      expect(isValidUUID('not-a-uuid')).toBe(false)
      expect(isValidUUID('')).toBe(false)
    })
  })

  describe('昵称验证', () => {
    it('应该验证昵称长度', () => {
      const isValidNickname = (name) => {
        const trimmed = name?.trim() || ''
        return trimmed.length >= 1 && trimmed.length <= 20
      }
      
      expect(isValidNickname('玩家')).toBe(true)
      expect(isValidNickname('')).toBe(false)
      expect(isValidNickname('   ')).toBe(false)
      expect(isValidNickname('a'.repeat(21))).toBe(false)
    })
  })

  describe('关卡号验证', () => {
    it('应该验证关卡号范围', () => {
      const isValidLevel = (level, maxLevel = 999) => {
        return Number.isInteger(level) && level >= 1 && level <= maxLevel
      }
      
      expect(isValidLevel(1)).toBe(true)
      expect(isValidLevel(100)).toBe(true)
      expect(isValidLevel(0)).toBe(false)
      expect(isValidLevel(-1)).toBe(false)
      expect(isValidLevel(1.5)).toBe(false)
    })
  })
})
