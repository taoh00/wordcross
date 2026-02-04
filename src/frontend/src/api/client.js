/**
 * API 客户端封装
 * 统一处理HTTP请求、错误处理、认证等
 */
import axios from 'axios'
import { API_BASE, ENDPOINTS, getFullUrl, buildUrl } from './endpoints.js'

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  timeout: 15000, // 15秒超时，防止请求无限等待
  headers: {
    'Content-Type': 'application/json',
  },
})

// 添加响应拦截器处理超时和网络错误
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      console.error('请求超时:', error.config?.url)
      error.message = '请求超时，请检查网络连接'
    } else if (!error.response) {
      console.error('网络错误:', error.message)
      error.message = '网络连接失败，请稍后重试'
    }
    return Promise.reject(error)
  }
)

// 带超时的 fetch 封装（供非 axios 请求使用）
async function fetchWithTimeout(url, options = {}, timeout = 10000) {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)
  
  try {
    const response = await fetch(url, { ...options, signal: controller.signal })
    clearTimeout(timeoutId)
    return response
  } catch (error) {
    clearTimeout(timeoutId)
    if (error.name === 'AbortError') {
      throw new Error('请求超时')
    }
    throw error
  }
}

// ============ 用户模块 ============

export const userApi = {
  /** 获取用户信息 */
  async getInfo() {
    const response = await apiClient.get(ENDPOINTS.USER_INFO)
    return response.data
  },

  /** 注册用户 */
  async register(nickname, avatar = '😊') {
    const response = await apiClient.post(ENDPOINTS.USER_REGISTER, {
      nickname,
      avatar,
    })
    return response.data
  },

  /** 更新用户信息 */
  async update(nickname, avatar) {
    const response = await apiClient.put(ENDPOINTS.USER_UPDATE, {
      nickname,
      avatar,
    })
    return response.data
  },

  /** 退出登录 */
  async logout() {
    const response = await apiClient.delete(ENDPOINTS.USER_LOGOUT)
    return response.data
  },

  /** 获取用户统计 */
  async getStats() {
    const response = await apiClient.get(ENDPOINTS.USER_STATS)
    return response.data
  },
}

// ============ 体力模块 ============

export const energyApi = {
  /** 获取体力 */
  async get() {
    try {
      const response = await fetchWithTimeout(getFullUrl(ENDPOINTS.USER_ENERGY), {
        credentials: 'include',
      }, 10000)
      return response.json()
    } catch (error) {
      console.error('获取体力失败:', error.message)
      return null
    }
  },

  /** 更新体力 */
  async update(energy) {
    try {
      const response = await fetchWithTimeout(getFullUrl(ENDPOINTS.USER_ENERGY), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ energy }),
      }, 10000)
      return response.ok
    } catch (error) {
      console.error('更新体力失败:', error.message)
      return false
    }
  },

  /** 消耗体力 */
  async consume(mode) {
    try {
      const response = await fetchWithTimeout(`${getFullUrl(ENDPOINTS.ENERGY_CONSUME)}?mode=${mode}`, {
        method: 'POST',
        credentials: 'include',
      }, 10000)
      return response.ok
    } catch (error) {
      console.error('消耗体力失败:', error.message)
      return false
    }
  },

  /** 领取免费体力 */
  async claimFree(amount = 30) {
    try {
      const response = await fetchWithTimeout(getFullUrl(ENDPOINTS.CLAIM_FREE_ENERGY), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ amount }),
      }, 10000)
      if (response.ok) {
        return response.json()
      }
      return null
    } catch (error) {
      console.error('领取体力失败:', error.message)
      return null
    }
  },
}

// ============ 道具模块 ============

export const propsApi = {
  /** 获取道具 */
  async get() {
    try {
      const response = await fetchWithTimeout(getFullUrl(ENDPOINTS.USER_PROPS), {
        credentials: 'include',
      }, 10000)
      if (response.ok) {
        return response.json()
      }
      return null
    } catch (error) {
      console.error('获取道具失败:', error.message)
      return null
    }
  },

  /** 更新道具 */
  async update(hintLetterCount, showTranslationCount) {
    try {
      const response = await fetchWithTimeout(getFullUrl(ENDPOINTS.USER_PROPS), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          hintLetterCount,
          showTranslationCount,
        }),
      }, 10000)
      return response.ok
    } catch (error) {
      console.error('更新道具失败:', error.message)
      return false
    }
  },
}

// ============ 游戏模块 ============

export const gameApi = {
  /** 获取无限模式谜题 */
  async getEndlessPuzzle(group, difficulty) {
    const url = buildUrl.endlessPuzzle(group, difficulty)
    const response = await apiClient.get(url)
    return response.data
  },

  /** 获取计时模式谜题 */
  async getTimedPuzzle(group, duration, difficulty) {
    const url = buildUrl.timedPuzzle(group, duration, difficulty)
    const response = await apiClient.get(url)
    return response.data
  },

  /** 提交分数 */
  async submitScore(score, vocabGroup, level) {
    const response = await fetch(getFullUrl(ENDPOINTS.GAME_SCORE), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ score, vocab_group: vocabGroup, level }),
    })
    return response.ok
  },

  /** 提交游戏数据 */
  async submit(data) {
    const response = await apiClient.post(ENDPOINTS.GAME_SUBMIT, data)
    return response.data
  },

  /** 生成奖励 */
  async generateReward() {
    const response = await apiClient.post(ENDPOINTS.GENERATE_REWARD, {})
    return response.data
  },

  /** 领取奖励 */
  async claimReward(level, vocabGroup, stars, timeSeconds, rewards) {
    const response = await apiClient.post(ENDPOINTS.CLAIM_REWARD, {
      level,
      vocab_group: vocabGroup,
      stars,
      time_seconds: timeSeconds,
      rewards,
    })
    return response.data
  },

  /** 提交PK结果 */
  async submitPkResult(vocabGroup, result, wordsCount, durationSeconds) {
    const response = await apiClient.post(ENDPOINTS.PK_RESULT, {
      vocab_group: vocabGroup,
      result,
      words_count: wordsCount,
      duration_seconds: durationSeconds,
    })
    return response.data
  },
}

// ============ 排行榜模块 ============

export const leaderboardApi = {
  /** 获取排行榜 */
  async get(type, group = 'all', limit = 50) {
    const response = await apiClient.get(ENDPOINTS.ROOT + `/leaderboard/${type}`, {
      params: { group, limit },
    })
    return response.data
  },

  /** 提交分数 */
  async submit(type, data) {
    const url = buildUrl.leaderboardSubmit(type)
    const response = await apiClient.post(url, data)
    return response.data
  },

  /** 获取用户排名 */
  async getUserRankings(userId) {
    const url = buildUrl.userRankings(userId)
    const response = await apiClient.get(url)
    return response.data
  },
}

// ============ 静态数据模块 ============

export const staticApi = {
  /** 获取关卡汇总 */
  async getLevelsSummary() {
    try {
      const response = await fetchWithTimeout(buildUrl.levelsSummary, {}, 10000)
      if (response.ok) {
        return response.json()
      }
      return null
    } catch (error) {
      console.error('加载关卡汇总失败:', error.message)
      return null
    }
  },

  /** 获取单关数据 */
  async getLevelData(group, level) {
    const url = buildUrl.levelData(group, level)
    try {
      const response = await fetchWithTimeout(url, {}, 10000)
      if (response.ok) {
        return response.json()
      }
      return null
    } catch (error) {
      console.error(`加载关卡 ${group}/${level} 失败:`, error.message)
      return null
    }
  },

  /** 获取词库元数据 */
  async getLevelMeta(group) {
    const url = buildUrl.levelMeta(group)
    try {
      const response = await fetchWithTimeout(url, {}, 10000)
      if (response.ok) {
        return response.json()
      }
      return null
    } catch (error) {
      console.error(`加载词库元数据 ${group} 失败:`, error.message)
      return null
    }
  },
}

// ============ 管理员模块 ============

export const adminApi = {
  /** 获取概览统计 */
  async getOverview(token) {
    const response = await apiClient.get(ENDPOINTS.ADMIN_STATS_OVERVIEW, {
      params: { token },
    })
    return response.data
  },

  /** 获取每日统计 */
  async getDailyStats(token, days = 30) {
    const response = await apiClient.get(ENDPOINTS.ADMIN_STATS_DAILY, {
      params: { token, days },
    })
    return response.data
  },

  /** 获取功能使用统计 */
  async getFeatureUsage(token) {
    const response = await apiClient.get(ENDPOINTS.ADMIN_STATS_FEATURE, {
      params: { token },
    })
    return response.data
  },

  /** 获取用户列表 */
  async getUsers(token, page = 1, pageSize = 20, search = '') {
    const response = await apiClient.get(ENDPOINTS.ADMIN_USERS, {
      params: { token, limit: pageSize, offset: (page - 1) * pageSize },
    })
    return response.data
  },

  /** 获取平台统计 */
  async getPlatformStats(token, days = 30) {
    const response = await apiClient.get(ENDPOINTS.ADMIN_STATS_PLATFORM, {
      params: { token, days },
    })
    return response.data
  },

  /** 获取事件统计 */
  async getEventStats(token, eventType = null, days = 30) {
    const response = await apiClient.get(ENDPOINTS.ADMIN_STATS_EVENTS, {
      params: { token, event_type: eventType, days },
    })
    return response.data
  },

  /** 获取体力领取统计 */
  async getEnergyStats(token, days = 30) {
    const response = await apiClient.get(ENDPOINTS.ADMIN_STATS_ENERGY, {
      params: { token, days },
    })
    return response.data
  },

  /** 获取道具使用统计 */
  async getPropsStats(token, days = 30) {
    const response = await apiClient.get(ENDPOINTS.ADMIN_STATS_PROPS, {
      params: { token, days },
    })
    return response.data
  },

  /** 获取关卡留存分析 */
  async getRetentionStats(token, vocabGroup = null) {
    const response = await apiClient.get(ENDPOINTS.ADMIN_STATS_RETENTION, {
      params: { token, vocab_group: vocabGroup },
    })
    return response.data
  },

  /** 获取每小时活跃度 */
  async getHourlyStats(token, days = 7) {
    const response = await apiClient.get(ENDPOINTS.ADMIN_STATS_HOURLY, {
      params: { token, days },
    })
    return response.data
  },

  /** 获取用户留存分析 */
  async getUserRetention(token, days = 30) {
    const response = await apiClient.get(ENDPOINTS.ADMIN_STATS_USER_RETENTION, {
      params: { token, days },
    })
    return response.data
  },

  /** 获取顶级玩家 */
  async getTopPlayers(token, limit = 20) {
    const response = await apiClient.get(ENDPOINTS.ADMIN_STATS_TOP_PLAYERS, {
      params: { token, limit },
    })
    return response.data
  },

  /** 获取词库分析 */
  async getVocabAnalysis(token) {
    const response = await apiClient.get(ENDPOINTS.ADMIN_STATS_VOCAB, {
      params: { token },
    })
    return response.data
  },

  /** 获取用户详情 */
  async getUserDetail(token, userId) {
    const response = await apiClient.get(`${ENDPOINTS.ADMIN_USER_DETAIL}/${userId}`, {
      params: { token },
    })
    return response.data
  },

  /** 修改管理员密码 */
  async changePassword(oldPassword, newPassword) {
    const response = await apiClient.post(ENDPOINTS.ADMIN_CHANGE_PASSWORD, {
      old_password: oldPassword,
      new_password: newPassword,
    })
    return response.data
  },

  /** 获取密码状态 */
  async getPasswordStatus() {
    const response = await apiClient.get(ENDPOINTS.ADMIN_PASSWORD_STATUS)
    return response.data
  },
}

// ============ 行为追踪模块 ============

export const trackApi = {
  /** 开始会话 */
  async startSession(sessionId, deviceInfo = {}) {
    try {
      const response = await apiClient.post(ENDPOINTS.TRACK_SESSION_START, {
        session_id: sessionId,
        platform: deviceInfo.platform || 'web',
        device_type: deviceInfo.deviceType,
        browser: deviceInfo.browser,
        os: deviceInfo.os,
        screen_width: deviceInfo.screenWidth,
        screen_height: deviceInfo.screenHeight,
      })
      return response.data
    } catch (e) {
      console.warn('会话追踪失败:', e)
      return null
    }
  },

  /** 结束会话 */
  async endSession(sessionId) {
    try {
      const response = await apiClient.post(ENDPOINTS.TRACK_SESSION_END, null, {
        params: { session_id: sessionId },
      })
      return response.data
    } catch (e) {
      console.warn('会话结束追踪失败:', e)
      return null
    }
  },

  /** 记录事件 */
  async trackEvent(eventType, eventData = null, platform = 'web') {
    try {
      const response = await apiClient.post(ENDPOINTS.TRACK_EVENT, {
        event_type: eventType,
        event_data: eventData,
        platform,
      })
      return response.data
    } catch (e) {
      console.warn('事件追踪失败:', e)
      return null
    }
  },

  /** 记录道具使用 */
  async trackPropUsage(propType, gameMode = null, vocabGroup = null, level = null, platform = 'web') {
    try {
      const response = await apiClient.post(ENDPOINTS.TRACK_PROP_USAGE, {
        prop_type: propType,
        game_mode: gameMode,
        vocab_group: vocabGroup,
        level,
        platform,
      })
      return response.data
    } catch (e) {
      console.warn('道具追踪失败:', e)
      return null
    }
  },

  /** 记录关卡完成 */
  async trackLevelComplete(vocabGroup, level, stars = 0, score = 0, durationSeconds = null, platform = 'web') {
    try {
      const response = await apiClient.post(ENDPOINTS.TRACK_LEVEL_COMPLETE, {
        vocab_group: vocabGroup,
        level,
        stars,
        score,
        duration_seconds: durationSeconds,
        platform,
      })
      return response.data
    } catch (e) {
      console.warn('关卡完成追踪失败:', e)
      return null
    }
  },

  /** 领取免费体力（带追踪） */
  async claimFreeEnergyTracked(amount = 30, platform = 'web') {
    try {
      const response = await apiClient.post(ENDPOINTS.CLAIM_FREE_ENERGY_TRACKED, 
        { amount },
        { params: { platform } }
      )
      return response.data
    } catch (e) {
      console.warn('领取体力追踪失败:', e)
      return null
    }
  },

  /** 获取设备信息 */
  getDeviceInfo() {
    const ua = navigator.userAgent
    let deviceType = 'desktop'
    let browser = 'unknown'
    let os = 'unknown'

    // 检测设备类型
    if (/Mobile|Android|iPhone|iPad/i.test(ua)) {
      deviceType = /iPad/i.test(ua) ? 'tablet' : 'mobile'
    }

    // 检测浏览器
    if (/Chrome/i.test(ua)) browser = 'Chrome'
    else if (/Firefox/i.test(ua)) browser = 'Firefox'
    else if (/Safari/i.test(ua)) browser = 'Safari'
    else if (/Edge/i.test(ua)) browser = 'Edge'
    else if (/MSIE|Trident/i.test(ua)) browser = 'IE'

    // 检测操作系统
    if (/Windows/i.test(ua)) os = 'Windows'
    else if (/Mac OS/i.test(ua)) os = 'macOS'
    else if (/Linux/i.test(ua)) os = 'Linux'
    else if (/Android/i.test(ua)) os = 'Android'
    else if (/iOS|iPhone|iPad/i.test(ua)) os = 'iOS'

    return {
      platform: 'web',
      deviceType,
      browser,
      os,
      screenWidth: window.screen.width,
      screenHeight: window.screen.height,
    }
  },

  /** 生成会话ID */
  generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
  },
}

// 默认导出
export default {
  user: userApi,
  energy: energyApi,
  props: propsApi,
  game: gameApi,
  leaderboard: leaderboardApi,
  static: staticApi,
  admin: adminApi,
  track: trackApi,
}
