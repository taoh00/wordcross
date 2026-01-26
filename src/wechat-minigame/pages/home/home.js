// pages/home/home.js
const { storage } = require('../../utils/storage')
const { staticApi, trackApi } = require('../../utils/api')

Page({
  data: {
    // 用户信息
    userAvatar: '😊',
    userName: '游客',
    energy: 200,
    hintCount: 20,
    speakCount: 20,
    
    // 步骤：mode -> duration -> difficulty -> group -> subgroup -> level
    currentStep: 'mode',
    selectedMode: null,
    selectedDuration: 180,
    selectedDifficulty: 'medium',
    selectedGroup: null,
    selectedGroupData: null,
    
    // 词库配置
    vocabGroups: [],
    difficultyOptions: [],
    durationOptions: [],
    
    // 关卡相关
    maxLevels: 0,
    levelProgress: {},
    currentPage: 1,
    levelsPerPage: 100,
    groupLevelCounts: {},
    
    // 计算属性
    currentGroupName: '',
    completedLevels: 0,
  },

  onLoad() {
    const app = getApp()
    
    // 从全局数据加载配置
    this.setData({
      vocabGroups: app.globalData.vocabGroups,
      difficultyOptions: app.globalData.difficultyOptions,
      durationOptions: app.globalData.durationOptions,
      energy: app.globalData.energy,
      hintCount: app.globalData.hintCount,
      speakCount: app.globalData.speakCount,
    })
    
    // 加载用户信息
    this.loadUserInfo()
    
    // 加载关卡数量
    this.loadGroupLevelCounts()
    
    // 加载关卡进度
    this.loadLevelProgress()
  },

  onShow() {
    // 刷新体力和道具
    const app = getApp()
    this.setData({
      energy: app.globalData.energy,
      hintCount: app.globalData.hintCount,
      speakCount: app.globalData.speakCount,
    })
  },

  // 加载用户信息
  loadUserInfo() {
    const userInfo = storage.get('user_info')
    if (userInfo) {
      this.setData({
        userAvatar: userInfo.avatar || '😊',
        userName: userInfo.nickname || '游客',
      })
    }
  },

  // 加载关卡数量
  async loadGroupLevelCounts() {
    try {
      const data = await staticApi.getLevelsSummary()
      if (data && data.groups) {
        const counts = {}
        for (const group of data.groups) {
          counts[group.group_code] = group.level_count || 0
        }
        this.setData({ groupLevelCounts: counts })
      }
    } catch (e) {
      console.warn('加载关卡数量失败:', e)
    }
  },

  // 加载关卡进度
  loadLevelProgress() {
    const progress = {}
    const { vocabGroups } = this.data
    
    const loadForGroup = (code) => {
      const key = `campaign_progress_${code}`
      const saved = storage.get(key)
      progress[code] = saved || { unlocked: 1, completed: {} }
    }
    
    vocabGroups.forEach(group => {
      loadForGroup(group.code)
      if (group.subGroups) {
        group.subGroups.forEach(sub => loadForGroup(sub.code))
      }
    })
    
    this.setData({ levelProgress: progress })
  },

  // 选择模式
  selectMode(e) {
    const mode = e.currentTarget.dataset.mode
    this.setData({ selectedMode: mode })
    
    // 埋点：记录模式选择事件
    trackApi.trackEvent('select_mode', { mode }, 'wechat')
    
    if (mode === 'timed' || mode === 'pk') {
      this.setData({ currentStep: 'duration' })
    } else if (mode === 'endless') {
      this.setData({ currentStep: 'difficulty' })
    } else {
      this.setData({ currentStep: 'group' })
    }
  },

  // 选择时间
  selectDuration(e) {
    const value = parseInt(e.currentTarget.dataset.value)
    this.setData({
      selectedDuration: value,
      currentStep: 'difficulty',
    })
  },

  // 选择难度
  selectDifficulty(e) {
    const code = e.currentTarget.dataset.code
    this.setData({
      selectedDifficulty: code,
      currentStep: 'group',
    })
  },

  // 选择词库
  selectGroup(e) {
    const group = e.currentTarget.dataset.group
    this.setData({ selectedGroupData: group })
    
    if (group.hasSubGroups && this.canSelectSubGroup()) {
      this.setData({ currentStep: 'subgroup' })
    } else {
      this.setData({ selectedGroup: group.code })
      this.onGroupSelected(group.code)
    }
  },

  // 选择细分类
  selectSubGroup(e) {
    const code = e.currentTarget.dataset.code
    this.setData({ selectedGroup: code })
    this.onGroupSelected(code)
  },

  // 词库选择完成
  onGroupSelected(groupCode) {
    const app = getApp()
    app.globalData.currentGroup = groupCode
    storage.set('current_group', groupCode)
    
    if (this.data.selectedMode === 'campaign') {
      // 加载关卡数量
      const maxLevels = this.data.groupLevelCounts[groupCode] || 180
      const progress = this.data.levelProgress[groupCode] || { completed: {} }
      const completedLevels = Object.keys(progress.completed).length
      
      this.setData({
        maxLevels,
        completedLevels,
        currentGroupName: this.getGroupName(groupCode),
        currentStep: 'level',
        currentPage: 1,
      })
    } else {
      this.startGame()
    }
  },

  // 获取词库名称
  getGroupName(code) {
    const { vocabGroups } = this.data
    
    // 在大分类中查找
    let group = vocabGroups.find(g => g.code === code)
    if (group) return `${group.icon} ${group.name}`
    
    // 在子分类中查找
    for (const g of vocabGroups) {
      if (g.subGroups) {
        const sub = g.subGroups.find(s => s.code === code)
        if (sub) return `${sub.icon} ${sub.name}`
      }
    }
    
    return code
  },

  // 是否可以选细分类
  canSelectSubGroup() {
    const { selectedMode } = this.data
    return selectedMode === 'campaign' || selectedMode === 'endless'
  },

  // 是否需要先选难度
  get needsDifficultyFirst() {
    const { selectedMode } = this.data
    return selectedMode === 'endless' || selectedMode === 'timed' || selectedMode === 'pk'
  },

  // 开始游戏
  startGame() {
    const { selectedMode, selectedGroup, selectedDifficulty, selectedDuration } = this.data
    
    // 保存设置
    storage.set('game_difficulty', selectedDifficulty)
    if (selectedMode === 'timed' || selectedMode === 'pk') {
      storage.set('timed_duration', selectedDuration)
    }
    
    // 埋点：记录游戏开始事件
    trackApi.trackEvent('start_game', { 
      mode: selectedMode, 
      vocab_group: selectedGroup,
      difficulty: selectedDifficulty,
      duration: selectedDuration
    }, 'wechat')
    
    // 跳转到游戏页
    wx.navigateTo({
      url: `/pages/game/game?mode=${selectedMode}&group=${selectedGroup}`,
    })
  },

  // 选择关卡开始游戏
  startLevel(e) {
    const level = e.currentTarget.dataset.level
    const { selectedGroup, levelProgress } = this.data
    const progress = levelProgress[selectedGroup] || { unlocked: 1 }
    
    // 检查是否解锁
    if (level > progress.unlocked) {
      wx.showToast({ title: '关卡未解锁', icon: 'none' })
      return
    }
    
    // 保存选择
    storage.set(`campaign_level_${selectedGroup}`, level)
    
    // 跳转到游戏页
    wx.navigateTo({
      url: `/pages/game/game?mode=campaign&group=${selectedGroup}&level=${level}`,
    })
  },

  // 获取关卡样式
  getLevelClass(level) {
    const { selectedGroup, levelProgress } = this.data
    const progress = levelProgress[selectedGroup] || { unlocked: 1, completed: {} }
    
    if (progress.completed[level]) {
      return 'completed'
    } else if (level <= progress.unlocked) {
      return 'current'
    } else {
      return 'locked'
    }
  },

  // 获取关卡星星
  getLevelStars(level) {
    const { selectedGroup, levelProgress } = this.data
    const progress = levelProgress[selectedGroup] || { completed: {} }
    
    if (progress.completed[level]) {
      const stars = progress.completed[level].stars || 3
      return '⭐'.repeat(stars)
    }
    return ''
  },

  // 获取关卡状态
  getLevelStatus(level) {
    const { selectedGroup, levelProgress } = this.data
    const progress = levelProgress[selectedGroup] || { unlocked: 1, completed: {} }
    
    if (progress.completed[level]) {
      return '已通关'
    } else if (level <= progress.unlocked) {
      return '挑战'
    } else {
      return '🔒'
    }
  },

  // 分页相关
  get currentPageLevels() {
    const { currentPage, levelsPerPage, maxLevels } = this.data
    const start = (currentPage - 1) * levelsPerPage + 1
    const end = Math.min(currentPage * levelsPerPage, maxLevels)
    const levels = []
    for (let i = start; i <= end; i++) {
      levels.push(i)
    }
    return levels
  },

  get totalPages() {
    const { maxLevels, levelsPerPage } = this.data
    return Math.ceil(maxLevels / levelsPerPage)
  },

  get rangeLabel() {
    const { currentPage, levelsPerPage, maxLevels } = this.data
    const start = (currentPage - 1) * levelsPerPage + 1
    const end = Math.min(currentPage * levelsPerPage, maxLevels)
    return `当前: ${start}-${end}`
  },

  get visibleRanges() {
    const totalPages = this.totalPages
    if (totalPages <= 5) {
      return Array.from({ length: totalPages }, (_, i) => i + 1)
    }
    
    const { currentPage } = this.data
    const pages = []
    const start = Math.max(1, currentPage - 2)
    const end = Math.min(totalPages, currentPage + 2)
    
    for (let i = start; i <= end; i++) {
      pages.push(i)
    }
    return pages
  },

  getRangeText(page) {
    const { levelsPerPage, maxLevels } = this.data
    const start = (page - 1) * levelsPerPage + 1
    const end = Math.min(page * levelsPerPage, maxLevels)
    return `${start}-${end}`
  },

  prevPage() {
    if (this.data.currentPage > 1) {
      this.setData({ currentPage: this.data.currentPage - 1 })
    }
  },

  nextPage() {
    if (this.data.currentPage < this.totalPages) {
      this.setData({ currentPage: this.data.currentPage + 1 })
    }
  },

  goToPage(e) {
    const page = e.currentTarget.dataset.page
    this.setData({ currentPage: page })
  },

  // 返回上一步
  goBack() {
    const { currentStep, selectedMode, selectedGroupData } = this.data
    
    switch (currentStep) {
      case 'level':
        if (selectedGroupData?.hasSubGroups && this.canSelectSubGroup()) {
          this.setData({ currentStep: 'subgroup', selectedGroup: null })
        } else {
          this.setData({ currentStep: 'group', selectedGroup: null, selectedGroupData: null })
        }
        break
      case 'subgroup':
        this.setData({ currentStep: 'group', selectedGroupData: null })
        break
      case 'group':
        if (this.needsDifficultyFirst) {
          this.setData({ currentStep: 'difficulty' })
        } else {
          this.setData({ currentStep: 'mode', selectedMode: null })
        }
        break
      case 'difficulty':
        if (selectedMode === 'timed' || selectedMode === 'pk') {
          this.setData({ currentStep: 'duration' })
        } else {
          this.setData({ currentStep: 'mode', selectedMode: null })
        }
        break
      case 'duration':
        this.setData({ currentStep: 'mode', selectedMode: null })
        break
    }
  },

  // 快捷入口
  goToLeaderboard() {
    wx.navigateTo({ url: '/pages/leaderboard/leaderboard' })
  },

  goToSettings() {
    wx.navigateTo({ url: '/pages/settings/settings' })
  },

  // 计算属性获取
  get selectedDurationLabel() {
    const { selectedDuration, durationOptions } = this.data
    const opt = durationOptions.find(d => d.value === selectedDuration)
    return opt ? opt.label : ''
  },

  get selectedDifficultyName() {
    const { selectedDifficulty, difficultyOptions } = this.data
    const opt = difficultyOptions.find(d => d.code === selectedDifficulty)
    return opt ? opt.name : ''
  },
})
