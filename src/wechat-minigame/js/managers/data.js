/**
 * 数据管理器
 * 管理用户数据、体力、道具、进度、设置等
 */

var config = require('../config')

var ENERGY_CONFIG = config.ENERGY_CONFIG
var PROPS_CONFIG = config.PROPS_CONFIG
var API_BASE = config.API_BASE

/**
 * 数据管理器类
 */
function DataManager() {
  // 用户信息
  this.userId = ''
  this.nickname = '游客'
  this.avatar = '😊'
  
  // 体力系统
  this.energy = ENERGY_CONFIG.initial
  this.lastEnergyGrantTime = Date.now()
  
  // 道具系统（与网页版游戏页一致：提示💡 + 发音🔊）
  this.hintCount = PROPS_CONFIG.initial.hint
  this.speakCount = PROPS_CONFIG.initial.speak
  
  // 进度系统
  this.progress = {}  // { groupCode: { unlocked: 1, completed: { 1: { stars: 3, score: 100, time: 45 } } } }
  
  // 设置
  this.settings = {
    autoSpeak: true,
    voiceType: 'us',
    bgMusic: true,
    soundEffect: true,
    showTranslation: true
  }
  
  // 当前游戏状态
  this.currentGroup = 'grade3_1'
  this.currentMode = 'campaign'
  this.currentLevel = 1
  this.currentDifficulty = 'medium'
  this.currentDuration = 60
}

/**
 * 初始化数据管理器
 */
DataManager.prototype.init = function() {
  this.loadUserId()
  this.loadEnergy()
  this.loadProps()
  this.loadProgress()
  this.loadSettings()
  this.loadGameState()
  
  // 计算离线期间恢复的体力
  this.recoverOfflineEnergy()
  
  // 启动体力实时恢复定时器
  this.startEnergyRecoveryTimer()
}

/**
 * 获取或创建用户ID
 */
DataManager.prototype.loadUserId = function() {
  try {
    var userId = wx.getStorageSync('user_id')
    if (!userId) {
      userId = 'wx_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
      wx.setStorageSync('user_id', userId)
    }
    this.userId = userId
    
    // 加载用户信息
    var userInfo = wx.getStorageSync('user_info')
    if (userInfo) {
      var info = JSON.parse(userInfo)
      this.nickname = info.nickname || '游客'
      this.avatar = info.avatar || '😊'
    }
  } catch (e) {
    console.error('加载用户ID失败:', e)
  }
}

/**
 * 保存用户信息
 */
DataManager.prototype.saveUserInfo = function(nickname, avatar) {
  this.nickname = nickname || this.nickname
  this.avatar = avatar || this.avatar
  
  try {
    wx.setStorageSync('user_info', JSON.stringify({
      nickname: this.nickname,
      avatar: this.avatar
    }))
  } catch (e) {
    console.error('保存用户信息失败:', e)
  }
}

/**
 * 加载体力
 */
DataManager.prototype.loadEnergy = function() {
  try {
    var saved = wx.getStorageSync('user_energy')
    if (saved) {
      var data = JSON.parse(saved)
      this.energy = data.value || ENERGY_CONFIG.initial
      this.lastEnergyGrantTime = data.lastGrantTime || Date.now()
    }
  } catch (e) {
    console.error('加载体力失败:', e)
  }
}

/**
 * 保存体力
 */
DataManager.prototype.saveEnergy = function() {
  try {
    wx.setStorageSync('user_energy', JSON.stringify({
      value: this.energy,
      lastGrantTime: this.lastEnergyGrantTime
    }))
  } catch (e) {
    console.error('保存体力失败:', e)
  }
}

/**
 * 计算离线体力恢复
 */
DataManager.prototype.recoverOfflineEnergy = function() {
  var now = Date.now()
  var timeDiff = now - this.lastEnergyGrantTime
  var minutesPassed = Math.floor(timeDiff / (1000 * 60))
  
  if (minutesPassed >= 1 && this.energy < ENERGY_CONFIG.max) {
    var recovered = Math.min(minutesPassed * ENERGY_CONFIG.recoveryPerMinute, ENERGY_CONFIG.max - this.energy)
    this.energy += recovered
    this.lastEnergyGrantTime = now
    this.saveEnergy()
    console.log('离线恢复体力:', recovered, '当前体力:', this.energy)
  }
}

/**
 * 启动体力实时恢复定时器（每分钟检查一次）
 */
DataManager.prototype.startEnergyRecoveryTimer = function() {
  var self = this
  
  // 清除已有定时器
  if (this.energyRecoveryTimer) {
    clearInterval(this.energyRecoveryTimer)
  }
  
  // 每分钟检查一次体力恢复
  this.energyRecoveryTimer = setInterval(function() {
    self.checkAndRecoverEnergy()
  }, 60 * 1000)
}

/**
 * 检查并恢复体力（实时恢复）
 */
DataManager.prototype.checkAndRecoverEnergy = function() {
  var now = Date.now()
  var timeDiff = now - this.lastEnergyGrantTime
  var minutesPassed = Math.floor(timeDiff / (1000 * 60))
  
  if (minutesPassed >= 1 && this.energy < ENERGY_CONFIG.max) {
    var recovered = Math.min(minutesPassed * ENERGY_CONFIG.recoveryPerMinute, ENERGY_CONFIG.max - this.energy)
    this.energy += recovered
    this.lastEnergyGrantTime = now
    this.saveEnergy()
    console.log('[实时恢复] 体力+' + recovered + ', 当前:' + this.energy)
  }
}

/**
 * 停止体力恢复定时器
 */
DataManager.prototype.stopEnergyRecoveryTimer = function() {
  if (this.energyRecoveryTimer) {
    clearInterval(this.energyRecoveryTimer)
    this.energyRecoveryTimer = null
  }
}

/**
 * 消耗体力
 */
DataManager.prototype.consumeEnergy = function(mode) {
  var cost = ENERGY_CONFIG.cost[mode] || 10
  
  if (this.energy < cost) {
    return { success: false, required: cost, current: this.energy }
  }
  
  this.energy -= cost
  this.lastEnergyGrantTime = Date.now()
  this.saveEnergy()
  
  return { success: true, remaining: this.energy }
}

/**
 * 增加体力
 */
DataManager.prototype.addEnergy = function(amount) {
  this.energy = Math.min(this.energy + amount, ENERGY_CONFIG.max)
  this.lastEnergyGrantTime = Date.now()
  this.saveEnergy()
  return this.energy
}

/**
 * 领取免费体力
 */
DataManager.prototype.claimFreeEnergy = function() {
  return this.addEnergy(ENERGY_CONFIG.freeClaimAmount)
}

/**
 * 加载道具
 */
DataManager.prototype.loadProps = function() {
  try {
    var saved = wx.getStorageSync('game_props')
    if (saved) {
      var data = JSON.parse(saved)
      this.hintCount = data.hintCount !== undefined ? data.hintCount : PROPS_CONFIG.initial.hint
      this.speakCount = data.speakCount !== undefined ? data.speakCount : PROPS_CONFIG.initial.speak
    }
  } catch (e) {
    console.error('加载道具失败:', e)
  }
}

/**
 * 保存道具
 */
DataManager.prototype.saveProps = function() {
  try {
    wx.setStorageSync('game_props', JSON.stringify({
      hintCount: this.hintCount,
      speakCount: this.speakCount
    }))
  } catch (e) {
    console.error('保存道具失败:', e)
  }
}

/**
 * 同步道具到后端
 */
DataManager.prototype.syncPropsToBackend = function() {
  var self = this
  
  wx.request({
    url: API_BASE + '/api/user/props',
    method: 'PUT',
    header: { 'X-User-Id': this.userId, 'Content-Type': 'application/json' },
    data: { 
      hintLetterCount: this.hintCount, 
      showTranslationCount: this.speakCount  // 后端字段名
    },
    success: function() { console.log('[同步] 道具同步成功') },
    fail: function(e) { console.warn('[同步] 道具同步失败:', e) }
  })
}

/**
 * 使用提示道具
 */
DataManager.prototype.useHintProp = function() {
  if (this.hintCount <= 0) return false
  this.hintCount--
  this.saveProps()
  return true
}

/**
 * 使用发音道具
 */
DataManager.prototype.useSpeakProp = function() {
  if (this.speakCount <= 0) return false
  this.speakCount--
  this.saveProps()
  return true
}

/**
 * 增加道具
 */
DataManager.prototype.addProps = function(hint, speak) {
  this.hintCount += hint || 0
  this.speakCount += speak || 0
  this.saveProps()
}

/**
 * 加载进度
 */
DataManager.prototype.loadProgress = function() {
  try {
    var saved = wx.getStorageSync('campaign_progress')
    if (saved) {
      this.progress = JSON.parse(saved)
    }
  } catch (e) {
    console.error('加载进度失败:', e)
  }
}

/**
 * 保存进度
 */
DataManager.prototype.saveProgress = function() {
  try {
    wx.setStorageSync('campaign_progress', JSON.stringify(this.progress))
  } catch (e) {
    console.error('保存进度失败:', e)
  }
}

/**
 * 获取词库进度
 */
DataManager.prototype.getGroupProgress = function(groupCode) {
  if (!this.progress[groupCode]) {
    this.progress[groupCode] = { unlocked: 1, completed: {} }
  }
  return this.progress[groupCode]
}

/**
 * 保存关卡完成
 */
DataManager.prototype.saveLevelComplete = function(groupCode, level, stars, score, time) {
  var groupProgress = this.getGroupProgress(groupCode)
  
  // 只保存更高的星级
  var existing = groupProgress.completed[level]
  if (!existing || stars > existing.stars) {
    groupProgress.completed[level] = { stars: stars, score: score, time: time }
  }
  
  // 解锁下一关
  if (level >= groupProgress.unlocked) {
    groupProgress.unlocked = level + 1
  }
  
  this.saveProgress()
}

/**
 * 加载设置
 */
DataManager.prototype.loadSettings = function() {
  try {
    var saved = wx.getStorageSync('game_settings')
    if (saved) {
      var data = JSON.parse(saved)
      for (var key in data) {
        if (this.settings.hasOwnProperty(key)) {
          this.settings[key] = data[key]
        }
      }
    }
  } catch (e) {
    console.error('加载设置失败:', e)
  }
}

/**
 * 保存设置
 */
DataManager.prototype.saveSettings = function() {
  try {
    wx.setStorageSync('game_settings', JSON.stringify(this.settings))
  } catch (e) {
    console.error('保存设置失败:', e)
  }
}

/**
 * 更新设置
 */
DataManager.prototype.updateSetting = function(key, value) {
  if (this.settings.hasOwnProperty(key)) {
    this.settings[key] = value
    this.saveSettings()
  }
}

/**
 * 加载游戏状态
 */
DataManager.prototype.loadGameState = function() {
  try {
    var group = wx.getStorageSync('current_group')
    if (group) this.currentGroup = group
    
    var mode = wx.getStorageSync('current_mode')
    if (mode) this.currentMode = mode
    
    var difficulty = wx.getStorageSync('game_difficulty')
    if (difficulty) this.currentDifficulty = difficulty
    
    var duration = wx.getStorageSync('timed_duration')
    if (duration) this.currentDuration = parseInt(duration)
    
    // 加载当前关卡
    var levelKey = 'campaign_level_' + this.currentGroup
    var level = wx.getStorageSync(levelKey)
    if (level) this.currentLevel = parseInt(level)
  } catch (e) {
    console.error('加载游戏状态失败:', e)
  }
}

/**
 * 保存游戏状态
 */
DataManager.prototype.saveGameState = function() {
  try {
    wx.setStorageSync('current_group', this.currentGroup)
    wx.setStorageSync('current_mode', this.currentMode)
    wx.setStorageSync('game_difficulty', this.currentDifficulty)
    wx.setStorageSync('timed_duration', this.currentDuration.toString())
    wx.setStorageSync('campaign_level_' + this.currentGroup, this.currentLevel.toString())
  } catch (e) {
    console.error('保存游戏状态失败:', e)
  }
}

/**
 * 获取用户数据摘要（用于UI显示）
 */
DataManager.prototype.getUserSummary = function() {
  return {
    userId: this.userId,
    nickname: this.nickname,
    avatar: this.avatar,
    energy: this.energy,
    hintCount: this.hintCount,
    speakCount: this.speakCount,
    translateCount: this.speakCount  // 首页显示翻译道具（与speakCount共享）
  }
}

/**
 * 加载关卡数据
 */
DataManager.prototype.loadLevelData = function(groupCode, levelNum, callback) {
  var url = API_BASE + '/data/levels/' + groupCode + '/' + levelNum + '.json'
  
  wx.request({
    url: url,
    success: function(res) {
      if (res.statusCode === 200 && res.data) {
        callback(null, res.data)
      } else {
        callback(new Error('关卡数据不存在'))
      }
    },
    fail: function(err) {
      callback(err)
    }
  })
}

/**
 * 加载词库元数据
 */
DataManager.prototype.loadGroupMeta = function(groupCode, callback) {
  var url = API_BASE + '/data/levels/' + groupCode + '/meta.json'
  
  wx.request({
    url: url,
    success: function(res) {
      if (res.statusCode === 200 && res.data) {
        callback(null, res.data)
      } else {
        callback(new Error('词库元数据不存在'))
      }
    },
    fail: function(err) {
      callback(err)
    }
  })
}

/**
 * 加载关卡汇总
 */
DataManager.prototype.loadLevelsSummary = function(callback) {
  var url = API_BASE + '/data/levels_summary.json'
  
  wx.request({
    url: url,
    success: function(res) {
      if (res.statusCode === 200 && res.data) {
        callback(null, res.data)
      } else {
        callback(new Error('关卡汇总不存在'))
      }
    },
    fail: function(err) {
      callback(err)
    }
  })
}

module.exports = DataManager
