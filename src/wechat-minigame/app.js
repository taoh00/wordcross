/**
 * 我爱填单词 - 微信小程序入口
 */
const { request } = require('./utils/request')
const { storage } = require('./utils/storage')
const { trackApi } = require('./utils/api')

App({
  globalData: {
    // 用户信息
    userInfo: null,
    userId: null,
    
    // 游戏状态
    currentGroup: 'primary',
    currentMode: 'campaign',
    currentLevel: 1,
    
    // 体力与道具
    energy: 200,
    hintCount: 20,
    speakCount: 20,
    
    // API配置
    apiBase: 'https://superhe.art:10010',
    
    // 词库配置
    vocabGroups: [
      {
        code: 'primary',
        name: '小学词汇',
        icon: '📚',
        hasSubGroups: true,
        subGroups: [
          { code: 'primary_all', name: '全部', icon: '📚' },
          { code: 'grade3_1', name: '三年级上册', icon: '🌱' },
          { code: 'grade3_2', name: '三年级下册', icon: '🌿' },
          { code: 'grade4_1', name: '四年级上册', icon: '🌲' },
          { code: 'grade4_2', name: '四年级下册', icon: '🌳' },
          { code: 'grade5_1', name: '五年级上册', icon: '🌴' },
          { code: 'grade5_2', name: '五年级下册', icon: '🌵' },
          { code: 'grade6_1', name: '六年级上册', icon: '🎄' },
          { code: 'grade6_2', name: '六年级下册', icon: '🎋' },
        ],
      },
      {
        code: 'junior',
        name: '初中词汇',
        icon: '📖',
        hasSubGroups: true,
        subGroups: [
          { code: 'junior_all', name: '全部', icon: '📖' },
          { code: 'junior7_1', name: '七年级上册', icon: '🌱' },
          { code: 'junior7_2', name: '七年级下册', icon: '🌿' },
          { code: 'junior8_1', name: '八年级上册', icon: '🌲' },
          { code: 'junior8_2', name: '八年级下册', icon: '🌳' },
          { code: 'junior9', name: '九年级全册', icon: '🌴' },
        ],
      },
      {
        code: 'senior',
        name: '高中词汇',
        icon: '📕',
        hasSubGroups: true,
        subGroups: [
          { code: 'senior_all', name: '全部', icon: '📕' },
          { code: 'senior1', name: '必修1', icon: '📗' },
          { code: 'senior2', name: '必修2', icon: '📘' },
          { code: 'senior3', name: '必修3', icon: '📙' },
          { code: 'senior4', name: '必修4', icon: '📔' },
          { code: 'senior5', name: '必修5', icon: '📓' },
        ],
      },
      { code: 'ket', name: 'KET考试', icon: '🎯' },
      { code: 'pet', name: 'PET考试', icon: '🎓' },
      { code: 'cet4', name: '大学四级', icon: '🏛️' },
      { code: 'cet6', name: '大学六级', icon: '🎖️' },
      { code: 'postgrad', name: '考研词汇', icon: '🔬' },
      { code: 'ielts', name: '雅思', icon: '✈️' },
      { code: 'toefl', name: '托福', icon: '🗽' },
      { code: 'gre', name: 'GRE', icon: '🎩' },
    ],
    
    // 难度选项
    difficultyOptions: [
      { code: 'low', name: '简单', desc: '2-4字母短词', icon: '🌱' },
      { code: 'medium', name: '中等', desc: '3-6字母词汇', icon: '🌿' },
      { code: 'high', name: '困难', desc: '5-10字母长词', icon: '🌲' },
    ],
    
    // 时间选项
    durationOptions: [
      { value: 180, label: '3分钟', icon: '⏱️' },
      { value: 300, label: '5分钟', icon: '⏳' },
      { value: 600, label: '10分钟', icon: '🕐' },
    ],
    
    // 体力消耗配置
    energyCost: {
      campaign: 10,
      timed: 30,
      pk: 30,
      endless: 30,
    },
  },

  onLaunch() {
    console.log('我爱填单词 启动')
    
    // 初始化用户数据
    this.initUserData()
    
    // 静默登录
    this.silentLogin()
    
    // 启动会话追踪（延迟执行，等待登录完成）
    setTimeout(() => {
      this.startSessionTracking()
    }, 1000)
  },
  
  // 启动会话追踪
  startSessionTracking() {
    const sessionId = trackApi.generateSessionId()
    this.globalData.sessionId = sessionId
    const deviceInfo = trackApi.getDeviceInfo()
    trackApi.startSession(sessionId, deviceInfo)
  },
  
  onHide() {
    // 应用隐藏时结束会话
    if (this.globalData.sessionId) {
      trackApi.endSession(this.globalData.sessionId)
    }
  },
  
  onShow() {
    // 应用重新显示时开启新会话
    if (this.globalData.sessionId) {
      this.startSessionTracking()
    }
  },

  // 初始化用户数据（从本地存储恢复）
  initUserData() {
    const app = this
    
    // 恢复体力
    const energy = storage.get('user_energy')
    if (energy) {
      // 计算离线恢复的体力
      const now = Date.now()
      const lastGrantTime = energy.lastGrantTime || now
      const minutesPassed = Math.floor((now - lastGrantTime) / (1000 * 60))
      
      if (minutesPassed >= 1) {
        const recoveredEnergy = Math.min(minutesPassed, 200 - energy.value)
        app.globalData.energy = Math.min(energy.value + recoveredEnergy, 200)
        
        // 保存更新后的体力
        storage.set('user_energy', {
          value: app.globalData.energy,
          lastGrantTime: now,
        })
      } else {
        app.globalData.energy = energy.value
      }
    }
    
    // 恢复道具
    const props = storage.get('game_props')
    if (props) {
      app.globalData.hintCount = props.hintLetterCount ?? 20
      app.globalData.speakCount = props.speakPropCount ?? 20
    }
    
    // 恢复词库选择
    const currentGroup = storage.get('current_group')
    if (currentGroup) {
      app.globalData.currentGroup = currentGroup
    }
    
    // 恢复用户信息
    const userInfo = storage.get('user_info')
    if (userInfo) {
      app.globalData.userInfo = userInfo
    }
    
    const userId = storage.get('user_id')
    if (userId) {
      app.globalData.userId = userId
    }
  },

  // 静默登录
  silentLogin() {
    const app = this
    
    wx.login({
      success: async (res) => {
        if (res.code) {
          try {
            // 发送 code 到后端换取 openid
            const result = await request({
              url: '/api/user/wx-login',
              method: 'POST',
              data: { code: res.code },
            })
            
            if (result && result.user_id) {
              app.globalData.userId = result.user_id
              app.globalData.userInfo = result.user_info || {}
              
              storage.set('user_id', result.user_id)
              storage.set('user_info', result.user_info || {})
            }
          } catch (e) {
            console.warn('微信登录失败，使用匿名模式:', e)
            // 使用本地生成的匿名ID
            if (!app.globalData.userId) {
              const anonymousId = 'anon_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
              app.globalData.userId = anonymousId
              storage.set('user_id', anonymousId)
            }
          }
        }
      },
      fail: (err) => {
        console.warn('wx.login 失败:', err)
      },
    })
  },

  // 保存体力
  saveEnergy(value) {
    this.globalData.energy = value
    storage.set('user_energy', {
      value: value,
      lastGrantTime: Date.now(),
    })
    
    // 同步到后端
    request({
      url: '/api/user/energy',
      method: 'POST',
      data: { energy: value },
    }).catch(e => console.warn('同步体力失败:', e))
  },

  // 保存道具
  saveProps() {
    storage.set('game_props', {
      hintLetterCount: this.globalData.hintCount,
      speakPropCount: this.globalData.speakCount,
    })
    
    // 同步到后端
    request({
      url: '/api/user/props',
      method: 'POST',
      data: {
        hintLetterCount: this.globalData.hintCount,
        showTranslationCount: this.globalData.speakCount,
      },
    }).catch(e => console.warn('同步道具失败:', e))
  },

  // 消耗体力
  consumeEnergy(mode) {
    const cost = this.globalData.energyCost[mode] || 10
    
    if (this.globalData.energy < cost) {
      return false
    }
    
    this.saveEnergy(this.globalData.energy - cost)
    return true
  },
})
