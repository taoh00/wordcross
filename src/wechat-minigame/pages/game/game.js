// pages/game/game.js
const { storage } = require('../../utils/storage')
const { staticApi, gameApi, energyApi, trackApi } = require('../../utils/api')
const { audio } = require('../../utils/audio')

Page({
  data: {
    // 加载状态
    loading: true,
    
    // 游戏模式
    mode: 'campaign',
    currentLevel: 1,
    currentGroup: 'primary',
    
    // 用户信息
    userAvatar: '😊',
    userName: '游客',
    energy: 200,
    hintCount: 20,
    speakCount: 20,
    
    // 网格数据
    gridSize: 8,
    cells: [],
    words: [],
    prefilled: {},
    clueNumbers: {},
    answers: {},
    completedWords: [],
    
    // 选中状态
    selectedWord: null,
    currentRow: 0,
    currentCol: 0,
    
    // 道具状态
    hintActive: false,
    speakActive: false,
    hintActiveWordId: null,
    
    // 计时器
    timer: 0,
    timerInterval: null,
    isCountdown: false,
    
    // 分数
    score: 0,
    
    // 累计状态（计时/PK/无限模式）
    sessionScore: 0,
    sessionLevelCount: 0,
    sessionWordsCount: 0,
    
    // 弹窗状态
    showCompleteModal: false,
    showEnergyModal: false,
    energyRequired: 10,
    timedModeEnded: false,
    isLastLevel: false,
    currentStars: 3,
    earnedRewards: [],
    rewardClaimed: false,
    
    // 计算属性
    modeIcon: '🏰',
    modeName: '闯关',
    formattedTimer: '00:00',
    progress: 0,
    completedWordsCount: 0,
    wordsCount: 0,
    showSessionScore: false,
    isTimeWarning: false,
    sortedWords: [],
    maxLevels: 180,
  },

  onLoad(options) {
    const app = getApp()
    
    // 获取参数
    const mode = options.mode || 'campaign'
    const group = options.group || app.globalData.currentGroup || 'primary'
    const level = parseInt(options.level) || 1
    
    // 设置模式信息
    const modeInfo = {
      campaign: { icon: '🏰', name: '闯关' },
      endless: { icon: '♾️', name: '无限' },
      timed: { icon: '⏱️', name: '计时' },
      pk: { icon: '⚔️', name: 'PK' },
    }
    
    this.setData({
      mode,
      currentLevel: level,
      currentGroup: group,
      modeIcon: modeInfo[mode]?.icon || '🎮',
      modeName: modeInfo[mode]?.name || '游戏',
      showSessionScore: mode === 'timed' || mode === 'pk' || mode === 'endless',
      energy: app.globalData.energy,
      hintCount: app.globalData.hintCount,
      speakCount: app.globalData.speakCount,
    })
    
    // 加载用户信息
    this.loadUserInfo()
    
    // 检查体力并开始游戏
    this.checkEnergyAndStart()
  },

  onUnload() {
    // 停止计时器
    this.stopTimer()
    // 停止音频
    audio.stopSpeak()
    audio.stopBgMusic()
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

  // 检查体力并开始游戏
  async checkEnergyAndStart() {
    const app = getApp()
    const { mode } = this.data
    const cost = app.globalData.energyCost[mode] || 10
    
    if (app.globalData.energy < cost) {
      this.setData({
        loading: false,
        showEnergyModal: true,
        energyRequired: cost,
      })
      return
    }
    
    // 扣除体力
    app.saveEnergy(app.globalData.energy - cost)
    this.setData({ energy: app.globalData.energy })
    
    // 加载游戏
    await this.loadGame()
  },

  // 加载游戏数据
  async loadGame() {
    const { mode, currentLevel, currentGroup } = this.data
    
    try {
      let puzzleData
      const difficulty = storage.get('game_difficulty') || 'medium'
      
      if (mode === 'campaign') {
        // 闯关模式：加载静态关卡数据
        puzzleData = await staticApi.getLevelData(currentGroup, currentLevel)
        
        // 加载最大关卡数
        const meta = await staticApi.getLevelMeta(currentGroup)
        if (meta && meta.level_count) {
          this.setData({ maxLevels: meta.level_count })
        }
      } else if (mode === 'endless') {
        puzzleData = await gameApi.getEndlessPuzzle(currentGroup, difficulty)
      } else if (mode === 'timed') {
        const duration = storage.get('timed_duration') || 180
        puzzleData = await gameApi.getTimedPuzzle(currentGroup, duration, difficulty)
      } else {
        puzzleData = await gameApi.getEndlessPuzzle(currentGroup, difficulty)
      }
      
      if (!puzzleData) {
        throw new Error('关卡数据为空')
      }
      
      // 解析关卡数据
      this.parsePuzzleData(puzzleData)
      
      // 初始化游戏状态
      this.initGameState()
      
      // 启动计时器
      this.startTimer()
      
      // 选择第一个未完成的单词
      this.selectFirstUnfinishedWord()
      
      this.setData({ loading: false })
    } catch (e) {
      console.error('加载游戏失败:', e)
      wx.showToast({ title: '加载失败', icon: 'error' })
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
    }
  },

  // 解析关卡数据
  parsePuzzleData(data) {
    const gridSize = data.grid_size || 8
    const words = data.words || []
    const prefilled = data.prefilled || {}
    
    // 初始化网格
    const cells = []
    for (let i = 0; i < gridSize; i++) {
      cells.push(new Array(gridSize).fill(null))
    }
    
    // 填充单词位置
    words.forEach(word => {
      for (let i = 0; i < word.length; i++) {
        let row = word.start_row
        let col = word.start_col
        
        if (word.direction === 'across') {
          col += i
        } else {
          row += i
        }
        
        if (row < gridSize && col < gridSize) {
          cells[row][col] = word.word[i]
        }
      }
    })
    
    // 生成线索编号
    const clueNumbers = {}
    let clueNum = 1
    
    // 收集所有起始位置
    const startPositions = new Map()
    words.forEach(word => {
      const key = `${word.start_row}-${word.start_col}`
      if (!startPositions.has(key)) {
        startPositions.set(key, clueNum++)
      }
      word.clue_number = startPositions.get(key)
    })
    
    // 填充线索编号网格
    for (let i = 0; i < gridSize; i++) {
      clueNumbers[i] = {}
    }
    startPositions.forEach((num, key) => {
      const [row, col] = key.split('-').map(Number)
      clueNumbers[row][col] = num
    })
    
    // 初始化答案
    const answers = {}
    Object.entries(prefilled).forEach(([key, value]) => {
      answers[key] = value
    })
    
    // 排序单词
    const sortedWords = [...words].sort((a, b) => {
      if (a.clue_number !== b.clue_number) {
        return a.clue_number - b.clue_number
      }
      return a.direction === 'across' ? -1 : 1
    })
    
    this.setData({
      gridSize,
      cells,
      words,
      prefilled,
      clueNumbers,
      answers,
      sortedWords,
      wordsCount: words.length,
    })
  },

  // 初始化游戏状态
  initGameState() {
    this.setData({
      completedWords: [],
      score: 0,
      completedWordsCount: 0,
      progress: 0,
      showCompleteModal: false,
      timedModeEnded: false,
      rewardClaimed: false,
      earnedRewards: [],
    })
    
    // 检查预填完成的单词
    this.checkAllWords()
  },

  // 启动计时器
  startTimer() {
    const { mode } = this.data
    let initialTime = 0
    let isCountdown = false
    
    if (mode === 'timed' || mode === 'pk') {
      initialTime = storage.get('timed_duration') || 180
      isCountdown = true
    } else if (mode === 'endless') {
      initialTime = 180 // 每关3分钟
      isCountdown = true
    }
    
    this.setData({
      timer: initialTime,
      isCountdown,
    })
    
    this.timerInterval = setInterval(() => {
      let { timer, isCountdown, mode } = this.data
      
      if (isCountdown) {
        timer--
        if (timer <= 0) {
          this.handleTimeUp()
          return
        }
      } else {
        timer++
      }
      
      // 更新计时器显示
      const minutes = Math.floor(Math.abs(timer) / 60)
      const seconds = Math.abs(timer) % 60
      const formattedTimer = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
      
      this.setData({
        timer,
        formattedTimer,
        isTimeWarning: isCountdown && timer < 60,
      })
    }, 1000)
  },

  // 停止计时器
  stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval)
      this.timerInterval = null
    }
  },

  // 时间到
  handleTimeUp() {
    this.stopTimer()
    
    // 播放音效
    audio.playSound('complete')
    
    // 计算最终得分
    const wordsCompleted = this.data.completedWords.length
    const scoreEarned = wordsCompleted * 10
    
    this.setData({
      timedModeEnded: true,
      sessionScore: this.data.sessionScore + scoreEarned,
      sessionWordsCount: this.data.sessionWordsCount + wordsCompleted,
    })
    
    // 获取奖励
    this.fetchRewards()
    
    setTimeout(() => {
      this.setData({ showCompleteModal: true })
    }, 300)
  },

  // 获取奖励
  async fetchRewards() {
    try {
      const result = await gameApi.generateReward()
      if (result && result.rewards) {
        this.setData({ earnedRewards: result.rewards })
      }
    } catch (e) {
      console.warn('获取奖励失败:', e)
      this.setData({
        earnedRewards: [
          { type: 'energy', name: '体力', icon: '⚡', value: 5 },
          { type: 'hint', name: '提示', icon: '💡', value: 1 },
        ],
      })
    }
  },

  // 点击格子
  handleCellClick(e) {
    const { row, col } = e.currentTarget.dataset
    const cell = this.data.cells[row]?.[col]
    
    if (cell === null) return
    if (this.isCellLocked(row, col)) return
    
    this.setData({
      currentRow: row,
      currentCol: col,
    })
    
    this.selectWordAtCell(row, col)
  },

  // 选择格子所在的单词
  selectWordAtCell(row, col) {
    const { words } = this.data
    
    // 优先选择横向单词
    for (const word of words) {
      if (word.direction === 'across') {
        if (row === word.start_row && 
            col >= word.start_col && 
            col < word.start_col + word.length) {
          this.setData({ selectedWord: word })
          return
        }
      }
    }
    
    // 再选择纵向单词
    for (const word of words) {
      if (word.direction === 'down') {
        if (col === word.start_col && 
            row >= word.start_row && 
            row < word.start_row + word.length) {
          this.setData({ selectedWord: word })
          return
        }
      }
    }
  },

  // 选择单词
  selectWord(e) {
    const word = e.currentTarget.dataset.word
    if (this.isWordCompleted(word.id)) return
    
    this.setData({ selectedWord: word })
    
    // 移动到单词的第一个未锁定格子
    for (let i = 0; i < word.length; i++) {
      let r = word.start_row
      let c = word.start_col
      if (word.direction === 'across') {
        c += i
      } else {
        r += i
      }
      if (!this.isCellLocked(r, c)) {
        this.setData({ currentRow: r, currentCol: c })
        return
      }
    }
    
    this.setData({
      currentRow: word.start_row,
      currentCol: word.start_col,
    })
  },

  // 选择第一个未完成的单词
  selectFirstUnfinishedWord() {
    const { sortedWords, completedWords } = this.data
    const unfinished = sortedWords.find(w => !completedWords.some(c => c.id === w.id))
    if (unfinished) {
      this.setData({ selectedWord: unfinished })
      
      // 设置起始位置
      this.setData({
        currentRow: unfinished.start_row,
        currentCol: unfinished.start_col,
      })
    }
  },

  // 输入字母
  inputLetter(e) {
    const letter = e.currentTarget.dataset.letter
    const { currentRow, currentCol } = this.data
    
    if (this.isCellLocked(currentRow, currentCol)) return
    
    // 设置答案
    const key = `${currentRow}-${currentCol}`
    const answers = { ...this.data.answers }
    answers[key] = letter
    
    this.setData({ answers })
    
    // 播放音效
    audio.playSound('type')
    
    // 检查单词
    this.checkWordsAtCell(currentRow, currentCol)
    
    // 移动到下一个格子
    this.moveToNextCell()
  },

  // 删除字母
  deleteLetter() {
    const { currentRow, currentCol, selectedWord } = this.data
    
    if (this.isCellLocked(currentRow, currentCol)) {
      this.moveToPrevCell()
      return
    }
    
    audio.playSound('delete')
    
    const key = `${currentRow}-${currentCol}`
    const answers = { ...this.data.answers }
    
    if (answers[key]) {
      delete answers[key]
      this.setData({ answers })
    } else {
      this.moveToPrevCell()
      const newKey = `${this.data.currentRow}-${this.data.currentCol}`
      if (!this.isCellLocked(this.data.currentRow, this.data.currentCol)) {
        delete answers[newKey]
        this.setData({ answers })
      }
    }
  },

  // 移动到下一个格子
  moveToNextCell() {
    const { selectedWord, currentRow, currentCol } = this.data
    if (!selectedWord) return
    
    if (selectedWord.direction === 'across') {
      let nextCol = currentCol + 1
      while (nextCol < selectedWord.start_col + selectedWord.length) {
        if (!this.isCellLocked(selectedWord.start_row, nextCol)) {
          this.setData({ currentCol: nextCol })
          return
        }
        nextCol++
      }
    } else {
      let nextRow = currentRow + 1
      while (nextRow < selectedWord.start_row + selectedWord.length) {
        if (!this.isCellLocked(nextRow, selectedWord.start_col)) {
          this.setData({ currentRow: nextRow })
          return
        }
        nextRow++
      }
    }
    
    // 到达末尾，选择下一个未完成的单词
    this.selectNextUnfinishedWord()
  },

  // 移动到上一个格子
  moveToPrevCell() {
    const { selectedWord, currentRow, currentCol } = this.data
    if (!selectedWord) return
    
    if (selectedWord.direction === 'across') {
      let prevCol = currentCol - 1
      while (prevCol >= selectedWord.start_col) {
        if (!this.isCellLocked(selectedWord.start_row, prevCol)) {
          this.setData({ currentCol: prevCol })
          return
        }
        prevCol--
      }
    } else {
      let prevRow = currentRow - 1
      while (prevRow >= selectedWord.start_row) {
        if (!this.isCellLocked(prevRow, selectedWord.start_col)) {
          this.setData({ currentRow: prevRow })
          return
        }
        prevRow--
      }
    }
  },

  // 选择下一个未完成的单词
  selectNextUnfinishedWord() {
    const { sortedWords, completedWords, selectedWord } = this.data
    const unfinished = sortedWords.filter(w => !completedWords.some(c => c.id === w.id))
    
    if (unfinished.length > 0) {
      const currentIndex = unfinished.findIndex(w => w.id === selectedWord?.id)
      const nextIndex = (currentIndex + 1) % unfinished.length
      const nextWord = unfinished[nextIndex]
      
      this.setData({
        selectedWord: nextWord,
        currentRow: nextWord.start_row,
        currentCol: nextWord.start_col,
      })
    }
  },

  // 检查格子所在的所有单词
  checkWordsAtCell(row, col) {
    const { words, completedWords, answers } = this.data
    let anyCorrect = false
    const newCompletedWords = [...completedWords]
    
    for (const word of words) {
      if (completedWords.some(w => w.id === word.id)) continue
      
      // 检查单词是否完成
      let userWord = ''
      for (let i = 0; i < word.length; i++) {
        let r = word.start_row
        let c = word.start_col
        if (word.direction === 'across') {
          c += i
        } else {
          r += i
        }
        const key = `${r}-${c}`
        userWord += answers[key] || ''
      }
      
      if (userWord.toUpperCase() === word.word.toUpperCase()) {
        anyCorrect = true
        newCompletedWords.push(word)
      }
    }
    
    if (anyCorrect) {
      audio.playSound('correct')
      
      const completedWordsCount = newCompletedWords.length
      const progress = Math.round((completedWordsCount / this.data.wordsCount) * 100)
      const score = completedWordsCount * 10
      
      this.setData({
        completedWords: newCompletedWords,
        completedWordsCount,
        progress,
        score,
      })
      
      // 检查是否全部完成
      if (completedWordsCount === this.data.wordsCount) {
        this.handleLevelComplete()
      } else {
        // 如果当前选中的单词完成了，选择下一个
        if (newCompletedWords.some(w => w.id === this.data.selectedWord?.id)) {
          setTimeout(() => {
            this.selectFirstUnfinishedWord()
          }, 100)
        }
      }
    }
  },

  // 检查所有单词（预填完成）
  checkAllWords() {
    const { words, answers } = this.data
    const completedWords = []
    
    for (const word of words) {
      let userWord = ''
      for (let i = 0; i < word.length; i++) {
        let r = word.start_row
        let c = word.start_col
        if (word.direction === 'across') {
          c += i
        } else {
          r += i
        }
        const key = `${r}-${c}`
        userWord += answers[key] || ''
      }
      
      if (userWord.toUpperCase() === word.word.toUpperCase()) {
        completedWords.push(word)
      }
    }
    
    const completedWordsCount = completedWords.length
    const progress = Math.round((completedWordsCount / this.data.wordsCount) * 100)
    const score = completedWordsCount * 10
    
    this.setData({
      completedWords,
      completedWordsCount,
      progress,
      score,
    })
  },

  // 关卡完成
  handleLevelComplete() {
    this.stopTimer()
    audio.playSound('complete')
    
    const { mode, currentLevel, currentGroup, timer, completedWords, score, sessionScore, sessionLevelCount, sessionWordsCount } = this.data
    
    // 计算星级
    let stars = 1
    if (timer <= 120) stars = 3
    else if (timer <= 180) stars = 2
    
    // 埋点：记录关卡完成
    trackApi.trackLevelComplete(currentGroup, currentLevel, stars, score, timer, 'wechat')
    
    if (mode === 'timed' || mode === 'pk' || mode === 'endless') {
      // 连续模式：累加并自动下一关
      const newSessionScore = sessionScore + score
      const newSessionLevelCount = sessionLevelCount + 1
      const newSessionWordsCount = sessionWordsCount + completedWords.length
      
      this.setData({
        sessionScore: newSessionScore,
        sessionLevelCount: newSessionLevelCount,
        sessionWordsCount: newSessionWordsCount,
      })
      
      // 自动加载下一关
      this.loadNextLevel()
    } else {
      // 闯关模式：显示通关弹窗
      this.setData({
        currentStars: stars,
        isLastLevel: currentLevel >= this.data.maxLevels,
      })
      
      // 保存进度
      this.saveLevelProgress()
      
      // 获取奖励
      this.fetchRewards()
      
      setTimeout(() => {
        this.setData({ showCompleteModal: true })
      }, 500)
    }
  },

  // 保存关卡进度
  saveLevelProgress() {
    const { currentLevel, currentGroup, currentStars } = this.data
    const key = `campaign_progress_${currentGroup}`
    
    let progress = storage.get(key) || { unlocked: 1, completed: {} }
    
    // 更新完成状态
    const existing = progress.completed[currentLevel]
    if (!existing || existing.stars < currentStars) {
      progress.completed[currentLevel] = {
        stars: currentStars,
        time: this.data.timer,
      }
    }
    
    // 解锁下一关
    if (currentLevel >= progress.unlocked) {
      progress.unlocked = currentLevel + 1
    }
    
    storage.set(key, progress)
  },

  // 加载下一关
  async loadNextLevel() {
    const { mode, currentLevel, currentGroup } = this.data
    
    // 如果是无限模式，重置计时器
    if (mode === 'endless') {
      this.stopTimer()
    }
    
    this.setData({
      loading: true,
      currentLevel: mode === 'campaign' ? currentLevel + 1 : currentLevel,
    })
    
    await this.loadGame()
    
    if (mode === 'endless') {
      this.startTimer()
    }
  },

  // 下一关
  async goNextLevel() {
    const app = getApp()
    const { mode } = this.data
    
    // 检查体力
    const cost = app.globalData.energyCost[mode] || 10
    if (app.globalData.energy < cost) {
      this.setData({
        showCompleteModal: false,
        showEnergyModal: true,
        energyRequired: cost,
      })
      return
    }
    
    // 扣除体力
    app.saveEnergy(app.globalData.energy - cost)
    this.setData({ energy: app.globalData.energy })
    
    this.setData({
      showCompleteModal: false,
      rewardClaimed: false,
      earnedRewards: [],
    })
    
    if (this.data.timedModeEnded) {
      // 重新开始
      this.setData({
        sessionScore: 0,
        sessionLevelCount: 0,
        sessionWordsCount: 0,
        timedModeEnded: false,
      })
    }
    
    await this.loadNextLevel()
  },

  // 重玩关卡
  replayLevel() {
    this.setData({
      showCompleteModal: false,
      rewardClaimed: false,
      earnedRewards: [],
    })
    
    this.loadGame()
  },

  // 领取奖励
  async claimRewards() {
    if (this.data.rewardClaimed) return
    
    const app = getApp()
    const { earnedRewards } = this.data
    
    this.setData({ rewardClaimed: true })
    
    for (const reward of earnedRewards) {
      if (reward.type === 'energy') {
        const newEnergy = Math.min(200, app.globalData.energy + reward.value)
        app.saveEnergy(newEnergy)
        this.setData({ energy: newEnergy })
      } else if (reward.type === 'hint') {
        app.globalData.hintCount += reward.value
        this.setData({ hintCount: app.globalData.hintCount })
      } else if (reward.type === 'speak') {
        app.globalData.speakCount += reward.value
        this.setData({ speakCount: app.globalData.speakCount })
      }
    }
    
    app.saveProps()
    
    wx.showToast({ title: '领取成功', icon: 'success' })
  },

  // 使用提示道具
  useHintProp() {
    const app = getApp()
    if (app.globalData.hintCount <= 0) {
      wx.showToast({ title: '提示道具不足', icon: 'none' })
      return
    }
    if (!this.data.selectedWord) {
      wx.showToast({ title: '请先选择一个单词', icon: 'none' })
      return
    }
    
    app.globalData.hintCount--
    app.saveProps()
    
    // 埋点：记录道具使用
    trackApi.trackPropUsage('hint_letter', this.data.mode, this.data.currentGroup, this.data.currentLevel, 'wechat')
    
    this.setData({
      hintCount: app.globalData.hintCount,
      hintActive: true,
      hintActiveWordId: this.data.selectedWord.id,
    })
  },

  // 使用发音道具
  useSpeakProp() {
    const app = getApp()
    if (app.globalData.speakCount <= 0) {
      wx.showToast({ title: '发音道具不足', icon: 'none' })
      return
    }
    if (!this.data.selectedWord) {
      wx.showToast({ title: '请先选择一个单词', icon: 'none' })
      return
    }
    
    app.globalData.speakCount--
    app.saveProps()
    
    // 埋点：记录道具使用
    trackApi.trackPropUsage('speak', this.data.mode, this.data.currentGroup, this.data.currentLevel, 'wechat')
    
    this.setData({
      speakCount: app.globalData.speakCount,
      speakActive: true,
    })
    
    // 播放发音3次
    const word = this.data.selectedWord.word
    this.speakWordRepeat(word, 3, 0)
  },

  // 重复发音
  speakWordRepeat(word, times, count) {
    if (count >= times) {
      this.setData({ speakActive: false })
      return
    }
    
    audio.speakWord(word)
    
    setTimeout(() => {
      this.speakWordRepeat(word, times, count + 1)
    }, 1200)
  },

  // 发音单词
  speakWord(e) {
    const word = e.currentTarget.dataset.word
    audio.speakWord(word)
  },

  // 领取免费体力
  async claimFreeEnergy() {
    const app = getApp()
    const bonus = 30
    
    try {
      // 使用带埋点的体力领取API
      await trackApi.claimFreeEnergyTracked(bonus, 'wechat')
    } catch (e) {
      console.warn('领取体力失败:', e)
    }
    
    const newEnergy = Math.min(200, app.globalData.energy + bonus)
    app.saveEnergy(newEnergy)
    
    this.setData({ energy: newEnergy })
    
    // 检查是否足够
    const cost = this.data.energyRequired
    if (newEnergy >= cost) {
      this.setData({ showEnergyModal: false })
      await this.checkEnergyAndStart()
    }
  },

  // 关闭体力弹窗并返回
  closeEnergyModalAndGoBack() {
    this.setData({ showEnergyModal: false })
    wx.navigateBack()
  },

  // 返回
  goBack() {
    wx.navigateBack()
  },

  // ============ 辅助方法 ============
  
  // 获取答案
  getAnswer(row, col) {
    const key = `${row}-${col}`
    return this.data.answers[key] || ''
  },

  // 获取线索编号
  getClueNumber(row, col) {
    return this.data.clueNumbers[row]?.[col] || null
  },

  // 获取格子样式
  getCellClass(row, col, cell) {
    if (cell === null) return 'empty'
    
    const { completedWords, currentRow, currentCol, selectedWord, prefilled } = this.data
    const key = `${row}-${col}`
    
    // 检查是否已完成
    const isCompleted = completedWords.some(word => {
      if (word.direction === 'across') {
        return row === word.start_row && col >= word.start_col && col < word.start_col + word.length
      } else {
        return col === word.start_col && row >= word.start_row && row < word.start_row + word.length
      }
    })
    
    if (isCompleted) return 'locked'
    if (prefilled[key]) return 'prefilled'
    if (row === currentRow && col === currentCol) return 'active'
    
    // 检查是否在选中单词中
    if (selectedWord) {
      if (selectedWord.direction === 'across') {
        if (row === selectedWord.start_row && 
            col >= selectedWord.start_col && 
            col < selectedWord.start_col + selectedWord.length) {
          return 'in-word'
        }
      } else {
        if (col === selectedWord.start_col && 
            row >= selectedWord.start_row && 
            row < selectedWord.start_row + selectedWord.length) {
          return 'in-word'
        }
      }
    }
    
    return ''
  },

  // 格子是否锁定
  isCellLocked(row, col) {
    const key = `${row}-${col}`
    return !!this.data.prefilled[key]
  },

  // 单词是否完成
  isWordCompleted(wordId) {
    return this.data.completedWords.some(w => w.id === wordId)
  },

  // 字母是否需要高亮
  isLetterNeeded(letter) {
    const { hintActive, selectedWord, hintActiveWordId } = this.data
    if (!hintActive || !selectedWord) return false
    if (selectedWord.id !== hintActiveWordId) return false
    return selectedWord.word.toUpperCase().includes(letter)
  },

  // 获取单词提示
  getWordHint(word) {
    const result = []
    for (let i = 0; i < word.length; i++) {
      let row = word.start_row
      let col = word.start_col
      if (word.direction === 'across') {
        col += i
      } else {
        row += i
      }
      const key = `${row}-${col}`
      const answer = this.data.answers[key]
      result.push(answer || '_')
    }
    return result
  },
})
