/**
 * API 接口封装
 * 与后端 API 交互的统一入口
 */

const { request, get, post } = require('./request')

/**
 * 用户相关 API
 */
const userApi = {
  // 微信登录
  wxLogin: (code) => post('/api/user/wx-login', { code }),
  
  // 获取用户信息
  getInfo: () => get('/api/user/info'),
  
  // 更新用户信息
  update: (data) => post('/api/user/update', data),
  
  // 获取用户统计
  getStats: () => get('/api/user/stats'),
}

/**
 * 体力相关 API
 */
const energyApi = {
  // 获取体力
  get: () => get('/api/user/energy'),
  
  // 更新体力
  update: (energy) => post('/api/user/energy', { energy }),
  
  // 消耗体力
  consume: (mode) => post('/api/user/energy/consume', { mode }),
  
  // 领取免费体力
  claimFree: (amount = 30) => post('/api/user/energy/claim-free', { amount }),
}

/**
 * 道具相关 API
 */
const propsApi = {
  // 获取道具
  get: () => get('/api/user/props'),
  
  // 更新道具
  update: (hintCount, speakCount) => post('/api/user/props', {
    hintLetterCount: hintCount,
    showTranslationCount: speakCount,
  }),
}

/**
 * 游戏相关 API
 */
const gameApi = {
  // 获取闯关关卡
  getCampaignLevel: (level, group) => 
    get(`/api/campaign/level/${level}?group=${group}`),
  
  // 获取无限模式谜题
  getEndlessPuzzle: (group, difficulty) =>
    get(`/api/endless/puzzle?group=${group}&difficulty=${difficulty}`),
  
  // 获取计时模式谜题
  getTimedPuzzle: (group, duration, difficulty) =>
    get(`/api/timed/puzzle?group=${group}&duration=${duration}&difficulty=${difficulty}`),
  
  // 提交游戏数据
  submit: (data) => post('/api/game/submit', data),
  
  // 提交分数
  submitScore: (score, group, level) => 
    post('/api/game/score', { score, group, level }),
  
  // 生成奖励
  generateReward: () => get('/api/game/generate-reward'),
  
  // 领取奖励
  claimReward: (level, group, stars, time, rewards) =>
    post('/api/game/claim-reward', { level, group, stars, time, rewards }),
  
  // 提交PK结果
  submitPkResult: (group, result, wordsCount, timeSeconds) =>
    post('/api/game/pk-result', { group, result, words_count: wordsCount, time_seconds: timeSeconds }),
}

/**
 * 排行榜相关 API
 */
const leaderboardApi = {
  // 获取排行榜
  get: (type, group = 'all', limit = 50) =>
    get(`/api/leaderboard/${type}?group=${group}&limit=${limit}`),
  
  // 提交分数
  submit: (type, data) => post(`/api/leaderboard/${type}/submit`, data),
  
  // 获取用户排名
  getUserRankings: (userId) => get(`/api/leaderboard/user/${userId}`),
}

/**
 * 静态资源 API
 */
const staticApi = {
  // 获取关卡数据
  getLevelData: (group, level) => {
    const app = getApp()
    const baseUrl = app?.globalData?.apiBase || 'https://superhe.art:10010'
    
    return new Promise((resolve, reject) => {
      wx.request({
        url: `${baseUrl}/data/levels/${group}/${level}.json`,
        method: 'GET',
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(res.data)
          } else {
            reject(new Error('关卡数据加载失败'))
          }
        },
        fail: reject,
      })
    })
  },
  
  // 获取词库元数据
  getLevelMeta: (group) => {
    const app = getApp()
    const baseUrl = app?.globalData?.apiBase || 'https://superhe.art:10010'
    
    return new Promise((resolve, reject) => {
      wx.request({
        url: `${baseUrl}/data/levels/${group}/meta.json`,
        method: 'GET',
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(res.data)
          } else {
            reject(new Error('词库元数据加载失败'))
          }
        },
        fail: reject,
      })
    })
  },
  
  // 获取关卡汇总
  getLevelsSummary: () => {
    const app = getApp()
    const baseUrl = app?.globalData?.apiBase || 'https://superhe.art:10010'
    
    return new Promise((resolve, reject) => {
      wx.request({
        url: `${baseUrl}/data/levels_summary.json`,
        method: 'GET',
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(res.data)
          } else {
            reject(new Error('关卡汇总加载失败'))
          }
        },
        fail: reject,
      })
    })
  },
  
  // 获取音频URL
  getAudioUrl: (word, type = 'us') => {
    const app = getApp()
    const baseUrl = app?.globalData?.apiBase || 'https://superhe.art:10010'
    return `${baseUrl}/data/audio/${type}/${word.toLowerCase()}.mp3`
  },
}

/**
 * 词库相关 API
 */
const vocabularyApi = {
  // 获取词库列表
  getGroups: () => get('/api/vocabulary/groups'),
}

/**
 * 行为追踪 API（埋点）
 */
const trackApi = {
  // 会话ID
  _sessionId: null,
  
  // 生成会话ID
  generateSessionId() {
    this._sessionId = 'wxsession_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    return this._sessionId
  },
  
  // 获取设备信息
  getDeviceInfo() {
    try {
      const systemInfo = wx.getSystemInfoSync()
      return {
        platform: 'wechat',
        deviceType: systemInfo.platform === 'ios' || systemInfo.platform === 'android' ? 'mobile' : 'desktop',
        browser: 'WeChat',
        os: systemInfo.platform,
        screenWidth: systemInfo.screenWidth,
        screenHeight: systemInfo.screenHeight,
        model: systemInfo.model,
        system: systemInfo.system,
        version: systemInfo.version,
      }
    } catch (e) {
      return { platform: 'wechat', deviceType: 'mobile' }
    }
  },
  
  // 开始会话
  startSession(sessionId, deviceInfo = {}) {
    return post('/api/track/session/start', {
      session_id: sessionId,
      platform: deviceInfo.platform || 'wechat',
      device_type: deviceInfo.deviceType,
      browser: deviceInfo.browser || 'WeChat',
      os: deviceInfo.os,
      screen_width: deviceInfo.screenWidth,
      screen_height: deviceInfo.screenHeight,
    }).catch(e => console.warn('会话追踪失败:', e))
  },
  
  // 结束会话
  endSession(sessionId) {
    return post('/api/track/session/end?session_id=' + sessionId)
      .catch(e => console.warn('会话结束追踪失败:', e))
  },
  
  // 记录事件
  trackEvent(eventType, eventData = null, platform = 'wechat') {
    return post('/api/track/event', {
      event_type: eventType,
      event_data: eventData,
      platform,
    }).catch(e => console.warn('事件追踪失败:', e))
  },
  
  // 记录道具使用
  trackPropUsage(propType, gameMode = null, vocabGroup = null, level = null, platform = 'wechat') {
    return post('/api/track/prop-usage', {
      prop_type: propType,
      game_mode: gameMode,
      vocab_group: vocabGroup,
      level,
      platform,
    }).catch(e => console.warn('道具追踪失败:', e))
  },
  
  // 记录关卡完成
  trackLevelComplete(vocabGroup, level, stars = 0, score = 0, durationSeconds = null, platform = 'wechat') {
    return post('/api/track/level-complete', {
      vocab_group: vocabGroup,
      level,
      stars,
      score,
      duration_seconds: durationSeconds,
      platform,
    }).catch(e => console.warn('关卡完成追踪失败:', e))
  },
  
  // 领取免费体力（带追踪）
  claimFreeEnergyTracked(amount = 30, platform = 'wechat') {
    return post('/api/user/energy/claim-free-tracked?platform=' + platform, { amount })
      .catch(e => {
        console.warn('领取体力追踪失败:', e)
        return null
      })
  },
}

module.exports = {
  userApi,
  energyApi,
  propsApi,
  gameApi,
  leaderboardApi,
  staticApi,
  vocabularyApi,
  trackApi,
}
