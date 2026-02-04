/**
 * 游戏场景
 * 填字游戏核心界面：网格、键盘、单词列表
 */

var config = require('../config')
var render = require('../utils/render')

var COLORS = config.COLORS
var KEYBOARD_LAYOUT = config.KEYBOARD_LAYOUT
var getEndlessTimeLimit = config.getEndlessTimeLimit

/**
 * 游戏场景类
 */
function GameScene(main) {
  this.main = main
  this.ctx = main.ctx
  this.screenWidth = main.screenWidth
  this.screenHeight = main.screenHeight
  this.dataManager = main.dataManager
  this.audioManager = main.audioManager
  
  // 游戏状态
  this.mode = 'campaign'
  this.group = 'grade3_1'
  this.level = 1
  this.difficulty = 'medium'
  this.duration = 60
  
  // 谜题数据
  this.puzzle = null
  this.gridSize = 5
  this.cells = []
  this.words = []
  this.prefilled = {}
  
  // 用户答案
  this.userAnswers = {}
  this.prefilledCells = {}
  this.completedWords = []
  
  // 当前选择
  this.selectedWord = null
  this.currentRow = 0
  this.currentCol = 0
  
  // 计时器
  this.timer = 0
  this.timerInterval = null
  this.isPlaying = false
  
  // 分数
  this.score = 0
  this.sessionScore = 0
  this.sessionLevelCount = 0
  this.sessionWordsCount = 0
  
  // 道具状态
  this.hintActive = false
  this.hintWordId = null
  this.speakActive = false  // 发音道具激活状态
  
  // 弹窗状态
  this.showCompleteModal = false
  this.showEnergyModal = false
  this.showWordDetailModal = false
  this.detailWord = null
  this.earnedRewards = []
  this.rewardClaimed = false
  this.timedModeEnded = false
  
  // 加载状态
  this.loading = true
  
  // UI元素
  this.buttons = []
  
  // 单词列表滚动
  this.wordsScrollY = 0
  this.wordsMaxScrollY = 0
}

/**
 * 初始化游戏
 */
GameScene.prototype.init = function(params) {
  params = params || {}
  
  this.mode = params.mode || 'campaign'
  this.group = params.group || this.dataManager.currentGroup
  this.level = params.level || this.dataManager.currentLevel
  this.difficulty = params.difficulty || this.dataManager.currentDifficulty
  this.duration = params.duration || this.dataManager.currentDuration
  
  // 重置状态
  this.resetGameState()
  
  // 检查体力
  var energyResult = this.dataManager.consumeEnergy(this.mode)
  if (!energyResult.success) {
    this.showEnergyModal = true
    this.energyInfo = energyResult
    this.loading = false
    return
  }
  
  // 加载关卡
  this.loadLevel()
}

/**
 * 重置游戏状态
 */
GameScene.prototype.resetGameState = function() {
  this.puzzle = null
  this.userAnswers = {}
  this.prefilledCells = {}
  this.completedWords = []
  this.selectedWord = null
  this.currentRow = 0
  this.currentCol = 0
  this.timer = 0
  this.score = 0
  this.hintActive = false
  this.hintWordId = null
  this.speakActive = false
  this.showCompleteModal = false
  this.showWordDetailModal = false
  this.timedModeEnded = false
  this.rewardClaimed = false
  this.earnedRewards = []
  this.loading = true
  this.buttons = []
}

/**
 * 加载关卡
 */
GameScene.prototype.loadLevel = function() {
  var self = this
  
  if (this.mode === 'campaign') {
    // 闯关模式：加载指定关卡
    this.dataManager.loadLevelData(this.group, this.level, function(err, data) {
      if (err) {
        console.error('加载关卡失败:', err)
        wx.showToast({ title: '加载失败', icon: 'none' })
        self.main.showScene('home')
        return
      }
      self.initPuzzle(data)
    })
  } else {
    // 无限/计时模式：从后端API获取随机关卡
    this.loadRandomPuzzle()
  }
}

/**
 * 加载随机关卡（无限/计时模式）
 */
GameScene.prototype.loadRandomPuzzle = function() {
  var self = this
  var url = config.API_BASE + '/api/endless/puzzle?group=' + this.group + '&difficulty=' + this.difficulty
  
  wx.request({
    url: url,
    header: { 'X-User-Id': this.dataManager.userId },
    success: function(res) {
      if (res.statusCode === 200 && res.data) {
        self.initPuzzle(res.data)
      } else {
        console.error('获取随机关卡失败')
        // 使用本地备用关卡
        self.dataManager.loadLevelData(self.group, 1, function(err, data) {
          if (!err && data) {
            self.initPuzzle(data)
          } else {
            wx.showToast({ title: '加载失败', icon: 'none' })
            self.main.showScene('home')
          }
        })
      }
    },
    fail: function(err) {
      console.error('请求关卡失败:', err)
      self.main.showScene('home')
    }
  })
}

/**
 * 初始化谜题
 */
GameScene.prototype.initPuzzle = function(data) {
  this.puzzle = data
  this.gridSize = data.grid_size || 5
  this.cells = data.cells || []
  this.words = data.words || []
  this.prefilled = data.prefilled || {}
  
  // 初始化预填字母
  for (var key in this.prefilled) {
    this.prefilledCells[key] = true
    this.userAnswers[key] = this.prefilled[key]
  }
  
  // 检查预填是否完成某些单词
  this.checkAllWords()
  
  // 选择第一个未完成的单词
  this.selectFirstUnfinishedWord()
  
  // 启动计时器
  this.startTimer()
  
  // 播放背景音乐
  if (this.dataManager.settings.bgMusic) {
    this.audioManager.playBgMusic()
  }
  
  this.loading = false
}

/**
 * 启动计时器
 */
GameScene.prototype.startTimer = function() {
  var self = this
  
  if (this.timerInterval) {
    clearInterval(this.timerInterval)
  }
  
  // 设置初始时间
  if (this.mode === 'timed') {
    this.timer = this.duration
  } else if (this.mode === 'endless') {
    // 无限模式：根据网格大小计算时间 30 + (size - 4) * 10
    this.timer = getEndlessTimeLimit(this.gridSize)
  } else {
    this.timer = 0
  }
  
  this.isPlaying = true
  
  this.timerInterval = setInterval(function() {
    if (self.mode === 'campaign') {
      // 正计时
      self.timer++
    } else {
      // 倒计时
      self.timer--
      if (self.timer <= 0) {
        self.timer = 0
        self.handleTimeUp()
      }
    }
  }, 1000)
}

/**
 * 停止计时器
 */
GameScene.prototype.stopTimer = function() {
  if (this.timerInterval) {
    clearInterval(this.timerInterval)
    this.timerInterval = null
  }
  this.isPlaying = false
}

/**
 * 处理时间到
 */
GameScene.prototype.handleTimeUp = function() {
  if (this.timedModeEnded) return
  this.timedModeEnded = true
  
  this.stopTimer()
  this.audioManager.playLevelCompleteSound()
  
  // 累加分数
  this.sessionScore += this.score
  this.sessionWordsCount += this.completedWords.length
  
  // 从后端获取随机奖励
  var self = this
  this.generateRewardFromBackend(function(rewards) {
    self.earnedRewards = rewards
    self.showCompleteModal = true
  })
}

/**
 * 渲染场景
 */
GameScene.prototype.render = function(ctx) {
  this.buttons = []
  
  // 背景
  ctx.fillStyle = COLORS.background
  ctx.fillRect(0, 0, this.screenWidth, this.screenHeight)
  
  if (this.loading) {
    this.renderLoading(ctx)
    return
  }
  
  if (this.showEnergyModal) {
    this.renderEnergyModal(ctx)
    return
  }
  
  // 顶部信息栏
  this.renderTopBar(ctx)
  
  // 游戏网格
  this.renderGrid(ctx)
  
  // 单词列表
  this.renderWordsList(ctx)
  
  // 键盘
  this.renderKeyboard(ctx)
  
  // 弹窗
  if (this.showCompleteModal) {
    this.renderCompleteModal(ctx)
  }
  
  if (this.showWordDetailModal) {
    this.renderWordDetailModal(ctx)
  }
}

/**
 * 渲染加载中
 */
GameScene.prototype.renderLoading = function(ctx) {
  ctx.fillStyle = COLORS.text
  ctx.font = '40px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText('⏳', this.screenWidth / 2, this.screenHeight / 2 - 20)
  
  ctx.font = '16px sans-serif'
  ctx.fillText('正在加载关卡...', this.screenWidth / 2, this.screenHeight / 2 + 30)
}

/**
 * 渲染顶部信息栏
 */
GameScene.prototype.renderTopBar = function(ctx) {
  var padding = 10
  var barHeight = 90
  
  // 卡片背景
  render.drawCard(ctx, padding, padding, this.screenWidth - padding * 2, barHeight, {
    radius: 16,
    bgColor: COLORS.white,
    borderColor: COLORS.primaryLight,
    shadowColor: COLORS.primary,
    shadowOffset: 3
  })
  
  // 第一行：返回按钮、用户信息、体力道具
  var row1Y = padding + 12
  
  // 返回按钮
  this.buttons.push(render.drawButton(ctx, padding + 8, row1Y, 50, 28, '← ', {
    bgColor: COLORS.white,
    shadowColor: COLORS.border,
    textColor: COLORS.textLight,
    fontSize: 12
  }))
  this.buttons[this.buttons.length - 1].action = 'back'
  
  // 用户信息
  var userInfo = this.dataManager.getUserSummary()
  ctx.font = '20px sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText(userInfo.avatar, padding + 65, row1Y + 14)
  ctx.fillStyle = COLORS.text
  ctx.font = 'bold 13px sans-serif'
  ctx.fillText(userInfo.nickname, padding + 90, row1Y + 14)
  
  // 体力和道具（与网页版游戏页一致：体力+提示+发音）
  var statsX = this.screenWidth - padding - 10
  ctx.textAlign = 'right'
  ctx.font = '12px sans-serif'
  ctx.fillStyle = COLORS.text
  ctx.fillText('🔊' + userInfo.speakCount, statsX, row1Y + 14)
  ctx.fillText('💡' + userInfo.hintCount, statsX - 50, row1Y + 14)
  ctx.fillText('⚡' + userInfo.energy, statsX - 100, row1Y + 14)
  
  // 第二行：模式、计时器、分数、进度
  var row2Y = row1Y + 36
  
  // 模式标签
  var modeInfo = config.GAME_MODES[this.mode] || { icon: '🎮', name: '游戏' }
  var modeText = modeInfo.icon + ' ' + modeInfo.name
  if (this.mode === 'campaign') {
    modeText += ' L' + this.level
  }
  
  render.drawRoundRect(ctx, padding + 8, row2Y, 80, 26, 8, COLORS.primaryBg, COLORS.primaryLight)
  ctx.fillStyle = COLORS.primary
  ctx.font = 'bold 11px sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText(modeText, padding + 48, row2Y + 13)
  
  // 计时器
  var timerText = '⏱️' + render.formatTime(this.timer)
  var timerBg = this.timer < 60 && this.mode !== 'campaign' ? COLORS.errorLight : '#f3f4f6'
  var timerColor = this.timer < 60 && this.mode !== 'campaign' ? COLORS.error : COLORS.text
  render.drawRoundRect(ctx, padding + 95, row2Y, 70, 26, 8, timerBg, null)
  ctx.fillStyle = timerColor
  ctx.font = 'bold 12px sans-serif'
  ctx.fillText(timerText, padding + 130, row2Y + 13)
  
  // 累计分数（计时/无限模式）
  if (this.mode === 'timed' || this.mode === 'endless') {
    render.drawRoundRect(ctx, padding + 170, row2Y, 55, 26, 8, '#d1fae5', null)
    ctx.fillStyle = '#059669'
    ctx.fillText('🏆' + this.sessionScore, padding + 197, row2Y + 13)
  }
  
  // 当关分数
  var scoreX = this.mode === 'campaign' ? padding + 170 : padding + 230
  render.drawRoundRect(ctx, scoreX, row2Y, 50, 26, 8, COLORS.lemon, null)
  ctx.fillStyle = COLORS.warningDark
  ctx.fillText('🌟' + this.score, scoreX + 25, row2Y + 13)
  
  // 进度条
  var progressX = scoreX + 55
  var progressWidth = this.screenWidth - progressX - padding - 40
  var progress = this.words.length > 0 ? (this.completedWords.length / this.words.length * 100) : 0
  
  render.drawProgressBar(ctx, progressX, row2Y + 5, progressWidth, 16, progress, {
    bgColor: COLORS.border,
    fillColor: COLORS.success
  })
  
  // 进度文字
  ctx.fillStyle = COLORS.text
  ctx.font = 'bold 11px sans-serif'
  ctx.textAlign = 'right'
  ctx.fillText(this.completedWords.length + '/' + this.words.length, this.screenWidth - padding - 12, row2Y + 13)
}

/**
 * 渲染游戏网格
 */
GameScene.prototype.renderGrid = function(ctx) {
  if (!this.cells || this.cells.length === 0) return
  
  var padding = 15
  var topOffset = 110
  var gridAreaHeight = this.screenHeight * 0.35
  
  // 计算格子大小
  var maxCellSize = Math.min(
    (this.screenWidth - padding * 2) / this.gridSize,
    gridAreaHeight / this.gridSize
  )
  var cellSize = Math.min(maxCellSize, 45)
  var gap = 3
  
  var gridWidth = this.gridSize * (cellSize + gap) - gap
  var gridHeight = this.gridSize * (cellSize + gap) - gap
  var startX = (this.screenWidth - gridWidth) / 2
  var startY = topOffset + (gridAreaHeight - gridHeight) / 2
  
  // 绘制每个格子
  for (var row = 0; row < this.gridSize; row++) {
    for (var col = 0; col < this.gridSize; col++) {
      var cell = this.cells[row] ? this.cells[row][col] : null
      var x = startX + col * (cellSize + gap)
      var y = startY + row * (cellSize + gap)
      
      this.renderCell(ctx, x, y, cellSize, row, col, cell)
    }
  }
  
  this.gridRect = { x: startX, y: startY, width: gridWidth, height: gridHeight, cellSize: cellSize, gap: gap }
}

/**
 * 渲染单个格子
 */
GameScene.prototype.renderCell = function(ctx, x, y, size, row, col, cell) {
  var key = row + '-' + col
  var isPrefilled = this.prefilledCells[key]
  var isCompleted = this.isCellInCompletedWord(row, col)
  var isActive = row === this.currentRow && col === this.currentCol
  var isInWord = this.isCellInSelectedWord(row, col)
  
  // 确定样式
  var bgColor = COLORS.white
  var borderColor = COLORS.skyBlue
  var shadowColor = COLORS.skyBlue
  var textColor = '#4c1d95'
  
  if (cell === null) {
    // 空格子
    bgColor = '#F0F8FF'
    borderColor = '#E0E0E0'
    shadowColor = 'transparent'
  } else if (isCompleted) {
    bgColor = '#6ee7b7'
    borderColor = '#10b981'
    shadowColor = '#059669'
    textColor = COLORS.white
  } else if (isPrefilled) {
    bgColor = '#fde68a'
    borderColor = '#f59e0b'
    shadowColor = '#d97706'
    textColor = '#92400e'
  } else if (isActive) {
    bgColor = COLORS.primaryBg
    borderColor = COLORS.primaryLight
    shadowColor = COLORS.primary
  } else if (isInWord) {
    bgColor = '#f5f3ff'
    borderColor = COLORS.skyBlue
  }
  
  // 绘制阴影
  if (shadowColor !== 'transparent' && cell !== null) {
    render.drawRoundRect(ctx, x, y + 3, size, size, 8, shadowColor, null)
  }
  
  // 绘制格子
  ctx.lineWidth = 2
  render.drawRoundRect(ctx, x, y, size, size, 8, bgColor, borderColor)
  
  // 绘制线索编号
  var clueNumber = this.getClueNumber(row, col)
  if (clueNumber) {
    ctx.fillStyle = COLORS.textLight
    ctx.font = '9px sans-serif'
    ctx.textAlign = 'left'
    ctx.textBaseline = 'top'
    ctx.fillText(clueNumber.toString(), x + 3, y + 2)
  }
  
  // 绘制字母
  if (cell !== null) {
    var letter = this.userAnswers[key] || ''
    if (letter) {
      ctx.fillStyle = textColor
      ctx.font = 'bold ' + Math.floor(size * 0.5) + 'px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(letter, x + size / 2, y + size / 2)
    }
    
    // 记录格子区域用于点击检测
    this.buttons.push({
      x: x, y: y, width: size, height: size,
      action: 'cell', row: row, col: col
    })
  }
}

/**
 * 获取线索编号
 */
GameScene.prototype.getClueNumber = function(row, col) {
  for (var i = 0; i < this.words.length; i++) {
    var word = this.words[i]
    if (word.start_row === row && word.start_col === col) {
      return word.clue_number || (i + 1)
    }
  }
  return null
}

/**
 * 渲染单词列表
 */
GameScene.prototype.renderWordsList = function(ctx) {
  var padding = 10
  var topOffset = this.screenHeight * 0.50
  var listHeight = this.screenHeight * 0.22
  
  // 卡片背景
  render.drawCard(ctx, padding, topOffset, this.screenWidth - padding * 2, listHeight, {
    radius: 14,
    bgColor: COLORS.white,
    borderColor: COLORS.primaryLight,
    shadowColor: COLORS.primary,
    shadowOffset: 3
  })
  
  // 单词列表
  var itemHeight = 40
  var itemPadding = 6
  var startY = topOffset + 8
  var listWidth = this.screenWidth - padding * 2 - 16
  
  // 排序单词
  var sortedWords = this.words.slice().sort(function(a, b) {
    var clueA = a.clue_number || 999
    var clueB = b.clue_number || 999
    if (clueA !== clueB) return clueA - clueB
    return a.direction === 'across' ? -1 : 1
  })
  
  // 绘制可见的单词
  var visibleCount = Math.floor((listHeight - 16) / (itemHeight + itemPadding))
  var scrollOffset = Math.floor(this.wordsScrollY / (itemHeight + itemPadding))
  
  for (var i = 0; i < Math.min(visibleCount, sortedWords.length); i++) {
    var wordIdx = i + scrollOffset
    if (wordIdx >= sortedWords.length) break
    
    var word = sortedWords[wordIdx]
    var y = startY + i * (itemHeight + itemPadding)
    
    this.renderWordItem(ctx, padding + 8, y, listWidth, itemHeight, word, wordIdx)
  }
  
  // 保存列表区域
  this.wordsListRect = { x: padding, y: topOffset, width: this.screenWidth - padding * 2, height: listHeight }
  this.wordsMaxScrollY = Math.max(0, (sortedWords.length - visibleCount) * (itemHeight + itemPadding))
}

/**
 * 渲染单词项
 */
GameScene.prototype.renderWordItem = function(ctx, x, y, width, height, word, index) {
  var isCompleted = this.completedWords.some(function(w) { return w.id === word.id })
  var isSelected = this.selectedWord && this.selectedWord.id === word.id
  
  var bgColor = COLORS.white
  var borderColor = '#FFF0F5'
  
  if (isCompleted) {
    bgColor = '#E0FBE0'
    borderColor = '#3CB371'
  } else if (isSelected) {
    bgColor = '#E0FBE0'
    borderColor = '#98FB98'
  }
  
  // 背景
  render.drawRoundRect(ctx, x, y, width, height, 10, bgColor, borderColor)
  ctx.lineWidth = 2
  
  // 序号
  var numSize = 28
  ctx.beginPath()
  ctx.arc(x + 20, y + height / 2, numSize / 2, 0, Math.PI * 2)
  ctx.fillStyle = isCompleted ? '#98FB98' : '#F0F8FF'
  ctx.fill()
  ctx.strokeStyle = isCompleted ? '#3CB371' : COLORS.primaryLight
  ctx.stroke()
  
  ctx.fillStyle = isCompleted ? '#2E8B57' : '#4682B4'
  ctx.font = 'bold 12px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText((word.clue_number || index + 1).toString(), x + 20, y + height / 2)
  
  // 方向标签
  var dirLabel = word.direction === 'across' ? '横' : '竖'
  render.drawRoundRect(ctx, x + 38, y + height / 2 - 10, 22, 20, 4, COLORS.lemon, COLORS.warning)
  ctx.fillStyle = '#92400e'
  ctx.font = 'bold 10px sans-serif'
  ctx.fillText(dirLabel, x + 49, y + height / 2)
  
  // 单词/提示
  ctx.textAlign = 'left'
  if (isCompleted) {
    ctx.fillStyle = '#065f46'
    ctx.font = 'bold 14px sans-serif'
    ctx.fillText(word.word.toUpperCase(), x + 68, y + height / 2 - 5)
    
    if (this.dataManager.settings.showTranslation) {
      ctx.fillStyle = '#047857'
      ctx.font = '11px sans-serif'
      ctx.fillText(word.definition, x + 68, y + height / 2 + 12)
    }
  } else {
    // 显示提示字母
    var hint = this.getWordHint(word)
    ctx.fillStyle = '#94a3b8'
    ctx.font = 'bold 14px sans-serif'
    ctx.fillText(hint.join(' '), x + 68, y + height / 2 - 5)
    
    if (this.dataManager.settings.showTranslation) {
      ctx.fillStyle = '#dc2626'
      ctx.font = '11px sans-serif'
      var defText = word.definition.length > 12 ? word.definition.substr(0, 12) + '...' : word.definition
      ctx.fillText(defText, x + 68, y + height / 2 + 12)
    }
  }
  
  // 点击区域
  this.buttons.push({
    x: x, y: y, width: width, height: height,
    action: 'word', word: word, completed: isCompleted
  })
}

/**
 * 获取单词提示
 */
GameScene.prototype.getWordHint = function(word) {
  var result = []
  for (var i = 0; i < word.length; i++) {
    var row = word.start_row
    var col = word.start_col
    
    if (word.direction === 'across') {
      col += i
    } else {
      row += i
    }
    
    var key = row + '-' + col
    var answer = this.userAnswers[key]
    result.push(answer || '_')
  }
  return result
}

/**
 * 渲染键盘
 */
GameScene.prototype.renderKeyboard = function(ctx) {
  var padding = 6
  var keyboardY = this.screenHeight * 0.74
  var keyboardHeight = this.screenHeight * 0.25 - padding
  var rowHeight = keyboardHeight / 3
  
  // 键盘背景
  ctx.fillStyle = COLORS.white
  ctx.fillRect(0, keyboardY, this.screenWidth, keyboardHeight + padding)
  ctx.strokeStyle = COLORS.primaryLight
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(0, keyboardY)
  ctx.lineTo(this.screenWidth, keyboardY)
  ctx.stroke()
  
  var rows = KEYBOARD_LAYOUT
  
  for (var r = 0; r < rows.length; r++) {
    var row = rows[r]
    var y = keyboardY + padding + r * rowHeight
    
    // 计算该行按键宽度
    var totalKeys = row.length
    // 第三行有道具按钮
    if (r === 2) totalKeys += 2  // 两个道具按钮
    
    var keyWidth = (this.screenWidth - padding * 2 - (totalKeys - 1) * 4) / totalKeys
    var keyHeight = rowHeight - 8
    
    var x = padding
    
    for (var k = 0; k < row.length; k++) {
      var key = row[k]
      
      // 判断是否高亮（提示道具激活）
      var isHighlight = this.hintActive && this.selectedWord && 
                        this.selectedWord.word.toUpperCase().indexOf(key) >= 0 &&
                        this.selectedWord.id === this.hintWordId
      
      this.renderKey(ctx, x, y, keyWidth, keyHeight, key, isHighlight)
      x += keyWidth + 4
    }
    
    // 第三行添加道具按钮（与网页版游戏页一致：提示💡 + 发音🔊）
    if (r === 2) {
      var propWidth = keyWidth * 1.2
      
      // 提示道具
      this.renderPropButton(ctx, x, y, propWidth, keyHeight, '💡', this.dataManager.hintCount, this.hintActive)
      this.buttons[this.buttons.length - 1].action = 'hint'
      x += propWidth + 4
      
      // 发音道具
      this.renderPropButton(ctx, x, y, propWidth, keyHeight, '🔊', this.dataManager.speakCount, this.speakActive)
      this.buttons[this.buttons.length - 1].action = 'speak'
    }
  }
}

/**
 * 渲染按键
 */
GameScene.prototype.renderKey = function(ctx, x, y, width, height, key, isHighlight) {
  var isDelete = key === '⌫'
  
  var bgColor = isHighlight ? COLORS.lemon : (isDelete ? COLORS.errorLight : COLORS.white)
  var borderColor = isHighlight ? COLORS.warning : (isDelete ? COLORS.error : COLORS.borderNeutralDark)
  var shadowColor = isHighlight ? COLORS.warningDark : (isDelete ? '#b91c1c' : '#94a3b8')
  var textColor = isDelete ? COLORS.white : COLORS.text
  
  // 阴影
  render.drawRoundRect(ctx, x, y + 3, width, height, 8, shadowColor, null)
  
  // 主体
  ctx.lineWidth = 2
  render.drawRoundRect(ctx, x, y, width, height, 8, bgColor, borderColor)
  
  // 文字
  ctx.fillStyle = textColor
  ctx.font = 'bold ' + (isDelete ? 18 : 16) + 'px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(key, x + width / 2, y + height / 2)
  
  this.buttons.push({
    x: x, y: y, width: width, height: height,
    action: isDelete ? 'delete' : 'key',
    key: key
  })
}

/**
 * 渲染道具按钮
 */
GameScene.prototype.renderPropButton = function(ctx, x, y, width, height, icon, count, active) {
  var bgColor = active ? '#a7f3d0' : COLORS.lemon
  var borderColor = active ? '#10b981' : COLORS.warning
  var shadowColor = active ? '#059669' : COLORS.warningDark
  
  // 阴影
  render.drawRoundRect(ctx, x, y + 3, width, height, 8, shadowColor, null)
  
  // 主体
  ctx.lineWidth = 2
  render.drawRoundRect(ctx, x, y, width, height, 8, bgColor, borderColor)
  
  // 图标
  ctx.font = '18px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(icon, x + width / 2 - 10, y + height / 2)
  
  // 数量
  ctx.beginPath()
  ctx.arc(x + width / 2 + 14, y + height / 2, 10, 0, Math.PI * 2)
  ctx.fillStyle = active ? '#10b981' : '#f59e0b'
  ctx.fill()
  
  ctx.fillStyle = COLORS.white
  ctx.font = 'bold 10px sans-serif'
  ctx.fillText(count.toString(), x + width / 2 + 14, y + height / 2)
  
  this.buttons.push({ x: x, y: y, width: width, height: height })
}

/**
 * 渲染通关弹窗
 */
GameScene.prototype.renderCompleteModal = function(ctx) {
  render.drawModalBackground(ctx, this.screenWidth, this.screenHeight)
  
  var modalWidth = this.screenWidth * 0.85
  var modalHeight = 360
  var modalX = (this.screenWidth - modalWidth) / 2
  var modalY = (this.screenHeight - modalHeight) / 2
  
  render.drawModal(ctx, modalX, modalY, modalWidth, modalHeight)
  
  var centerX = this.screenWidth / 2
  var y = modalY + 30
  
  if (this.timedModeEnded) {
    // 计时/无限模式结束
    ctx.font = '48px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(this.mode === 'endless' ? '♾️' : '⏰', centerX, y + 30)
    
    y += 80
    ctx.fillStyle = COLORS.primary
    ctx.font = 'bold 22px sans-serif'
    ctx.fillText('⏱️ 时间到！', centerX, y)
    
    y += 40
    ctx.fillStyle = COLORS.text
    ctx.font = 'bold 32px sans-serif'
    ctx.fillText(this.sessionLevelCount + ' 关  ' + this.sessionWordsCount + ' 词', centerX, y)
    
    y += 35
    ctx.font = '14px sans-serif'
    ctx.fillStyle = COLORS.textLight
    ctx.fillText('🌟' + this.sessionScore + '分 · 📝' + this.sessionWordsCount + '词 · 🎯' + this.sessionLevelCount + '关', centerX, y)
  } else {
    // 闯关模式通关
    // 星级
    var stars = this.calculateStars()
    ctx.font = '48px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('🎉', centerX, y + 30)
    
    y += 60
    var starText = ''
    for (var i = 0; i < 3; i++) {
      starText += i < stars ? '⭐' : '☆'
    }
    ctx.font = '28px sans-serif'
    ctx.fillText(starText, centerX, y)
    
    y += 35
    ctx.fillStyle = COLORS.primary
    ctx.font = 'bold 22px sans-serif'
    ctx.fillText('第' + this.level + '关 通关！', centerX, y)
    
    y += 35
    ctx.font = '14px sans-serif'
    ctx.fillStyle = COLORS.textLight
    ctx.fillText('⏱️' + render.formatTime(this.timer) + ' · 🌟' + this.score + '分 · 📝' + this.completedWords.length + '词', centerX, y)
  }
  
  // 奖励展示
  if (this.earnedRewards.length > 0) {
    y += 40
    render.drawRoundRect(ctx, modalX + 20, y, modalWidth - 40, 60, 12, COLORS.lemon, COLORS.warning)
    
    ctx.fillStyle = '#92400e'
    ctx.font = 'bold 12px sans-serif'
    ctx.fillText('🎁 获得奖励', centerX, y + 16)
    
    var rewardX = centerX - 40
    for (var r = 0; r < this.earnedRewards.length; r++) {
      var reward = this.earnedRewards[r]
      ctx.font = '20px sans-serif'
      ctx.fillText(reward.icon, rewardX + r * 80, y + 42)
      ctx.font = 'bold 12px sans-serif'
      ctx.fillStyle = '#059669'
      ctx.fillText('+' + reward.value, rewardX + r * 80 + 20, y + 42)
    }
    y += 70
  }
  
  // 按钮
  y = modalY + modalHeight - 70
  var btnWidth = (modalWidth - 60) / 3
  var btnX = modalX + 20
  
  // 返回按钮
  this.buttons.push(render.drawButton(ctx, btnX, y, btnWidth, 45, '返回', {
    bgColor: COLORS.borderNeutral,
    shadowColor: COLORS.borderNeutralDark,
    textColor: COLORS.textLight,
    fontSize: 14
  }))
  this.buttons[this.buttons.length - 1].action = 'backToHome'
  
  // 领奖按钮
  btnX += btnWidth + 10
  var claimBg = this.rewardClaimed ? COLORS.border : COLORS.lemon
  var claimText = this.rewardClaimed ? '已领取' : '领奖'
  this.buttons.push(render.drawButton(ctx, btnX, y, btnWidth, 45, claimText, {
    bgColor: claimBg,
    shadowColor: this.rewardClaimed ? COLORS.borderNeutralDark : COLORS.warningDark,
    textColor: this.rewardClaimed ? COLORS.textLight : '#92400e',
    fontSize: 14
  }))
  this.buttons[this.buttons.length - 1].action = 'claimReward'
  
  // 下一关/再玩一次
  btnX += btnWidth + 10
  var nextText = this.timedModeEnded ? '再玩一次' : '下一关'
  this.buttons.push(render.drawButton(ctx, btnX, y, btnWidth, 45, nextText, {
    bgColor: COLORS.primary,
    shadowColor: COLORS.primaryLight,
    textColor: COLORS.white,
    fontSize: 14
  }))
  this.buttons[this.buttons.length - 1].action = 'nextLevel'
}

/**
 * 渲染体力不足弹窗
 */
GameScene.prototype.renderEnergyModal = function(ctx) {
  render.drawModalBackground(ctx, this.screenWidth, this.screenHeight)
  
  var modalWidth = this.screenWidth * 0.8
  var modalHeight = 280
  var modalX = (this.screenWidth - modalWidth) / 2
  var modalY = (this.screenHeight - modalHeight) / 2
  
  render.drawModal(ctx, modalX, modalY, modalWidth, modalHeight)
  
  var centerX = this.screenWidth / 2
  var y = modalY + 40
  
  ctx.font = '50px sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('😴', centerX, y + 20)
  
  y += 70
  ctx.fillStyle = COLORS.error
  ctx.font = 'bold 22px sans-serif'
  ctx.fillText('体力不足', centerX, y)
  
  y += 35
  ctx.fillStyle = COLORS.text
  ctx.font = '14px sans-serif'
  ctx.fillText('当前体力不足以开始游戏', centerX, y)
  
  y += 35
  ctx.font = 'bold 13px sans-serif'
  ctx.fillStyle = COLORS.error
  ctx.fillText('当前: ⚡' + (this.energyInfo ? this.energyInfo.current : 0), centerX - 50, y)
  ctx.fillStyle = '#1e40af'
  ctx.fillText('需要: ⚡' + (this.energyInfo ? this.energyInfo.required : 10), centerX + 50, y)
  
  // 按钮
  y = modalY + modalHeight - 70
  var btnWidth = (modalWidth - 50) / 2
  
  this.buttons.push(render.drawButton(ctx, modalX + 15, y, btnWidth, 45, '🎁 领取体力 +30', {
    bgColor: COLORS.success,
    shadowColor: '#059669',
    textColor: COLORS.white,
    fontSize: 13
  }))
  this.buttons[this.buttons.length - 1].action = 'claimEnergy'
  
  this.buttons.push(render.drawButton(ctx, modalX + 25 + btnWidth, y, btnWidth, 45, '休息一下', {
    bgColor: COLORS.borderNeutral,
    shadowColor: COLORS.borderNeutralDark,
    textColor: COLORS.textLight,
    fontSize: 13
  }))
  this.buttons[this.buttons.length - 1].action = 'backToHome'
}

/**
 * 渲染单词详情弹窗
 */
GameScene.prototype.renderWordDetailModal = function(ctx) {
  if (!this.detailWord) return
  
  render.drawModalBackground(ctx, this.screenWidth, this.screenHeight)
  
  var modalWidth = this.screenWidth * 0.85
  var modalHeight = this.detailWord.example ? 360 : 280  // 有例句时高度更高
  var modalX = (this.screenWidth - modalWidth) / 2
  var modalY = (this.screenHeight - modalHeight) / 2
  
  render.drawModal(ctx, modalX, modalY, modalWidth, modalHeight, { borderColor: COLORS.border })
  
  var centerX = this.screenWidth / 2
  var y = modalY + 40
  
  // 关闭按钮
  ctx.beginPath()
  ctx.arc(modalX + modalWidth - 25, modalY + 25, 16, 0, Math.PI * 2)
  ctx.fillStyle = COLORS.border
  ctx.fill()
  ctx.fillStyle = COLORS.textLight
  ctx.font = 'bold 18px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText('×', modalX + modalWidth - 25, modalY + 25)
  this.buttons.push({
    x: modalX + modalWidth - 41, y: modalY + 9, width: 32, height: 32,
    action: 'closeDetail'
  })
  
  // 单词
  ctx.fillStyle = COLORS.primary
  ctx.font = 'bold 28px sans-serif'
  ctx.fillText(this.detailWord.word.toUpperCase(), centerX, y)
  
  // 音标（如果有）
  if (this.detailWord.phonetic) {
    y += 30
    ctx.fillStyle = COLORS.textLight
    ctx.font = '14px sans-serif'
    ctx.fillText('/' + this.detailWord.phonetic + '/', centerX, y)
  }
  
  // 发音按钮
  y += 35
  var speakBtnWidth = 80
  this.buttons.push(render.drawButton(ctx, centerX - speakBtnWidth - 10, y, speakBtnWidth, 36, '🔊 美音', {
    bgColor: '#dbeafe',
    shadowColor: '#3b82f6',
    textColor: '#1e40af',
    fontSize: 12
  }))
  this.buttons[this.buttons.length - 1].action = 'speakUS'
  this.buttons[this.buttons.length - 1].word = this.detailWord.word
  
  this.buttons.push(render.drawButton(ctx, centerX + 10, y, speakBtnWidth, 36, '🔊 英音', {
    bgColor: '#fce7f3',
    shadowColor: '#ec4899',
    textColor: '#9d174d',
    fontSize: 12
  }))
  this.buttons[this.buttons.length - 1].action = 'speakUK'
  this.buttons[this.buttons.length - 1].word = this.detailWord.word
  
  // 释义
  y += 55
  ctx.fillStyle = COLORS.primary
  ctx.font = 'bold 12px sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('📖 释义', modalX + 25, y)
  
  y += 25
  render.drawRoundRect(ctx, modalX + 20, y, modalWidth - 40, 40, 8, '#f9fafb', COLORS.border)
  ctx.fillStyle = COLORS.text
  ctx.font = '14px sans-serif'
  ctx.fillText(this.detailWord.definition, modalX + 30, y + 24)
  
  // 例句（如果有）
  if (this.detailWord.example) {
    y += 55
    ctx.fillStyle = COLORS.primary
    ctx.font = 'bold 12px sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText('📝 例句', modalX + 25, y)
    
    y += 25
    render.drawRoundRect(ctx, modalX + 20, y, modalWidth - 40, 50, 8, '#f0fdf4', COLORS.borderNeutral)
    ctx.fillStyle = COLORS.text
    ctx.font = '12px sans-serif'
    // 例句可能较长，简单截断处理
    var exampleText = this.detailWord.example
    if (exampleText.length > 40) {
      exampleText = exampleText.substring(0, 40) + '...'
    }
    ctx.fillText(exampleText, modalX + 30, y + 30)
    y += 15
  }
  
  // 信息标签
  y += 55
  ctx.textAlign = 'center'
  render.drawRoundRect(ctx, centerX - 70, y, 60, 26, 12, COLORS.primaryBg, COLORS.primaryLight)
  ctx.fillStyle = COLORS.primary
  ctx.font = 'bold 11px sans-serif'
  ctx.fillText(this.detailWord.length + ' 字母', centerX - 40, y + 13)
  
  var dirText = this.detailWord.direction === 'across' ? '横向 →' : '纵向 ↓'
  render.drawRoundRect(ctx, centerX + 10, y, 60, 26, 12, COLORS.primaryBg, COLORS.primaryLight)
  ctx.fillText(dirText, centerX + 40, y + 13)
}

/**
 * 计算星级
 */
GameScene.prototype.calculateStars = function() {
  var seconds = this.timer
  if (seconds <= 30) return 3
  if (seconds <= 45) return 2
  return 1
}

/**
 * 检查格子是否在已完成的单词中
 */
GameScene.prototype.isCellInCompletedWord = function(row, col) {
  for (var i = 0; i < this.completedWords.length; i++) {
    var word = this.completedWords[i]
    if (word.direction === 'across') {
      if (row === word.start_row && col >= word.start_col && col < word.start_col + word.length) {
        return true
      }
    } else {
      if (col === word.start_col && row >= word.start_row && row < word.start_row + word.length) {
        return true
      }
    }
  }
  return false
}

/**
 * 检查格子是否在选中的单词中
 */
GameScene.prototype.isCellInSelectedWord = function(row, col) {
  if (!this.selectedWord) return false
  var word = this.selectedWord
  
  if (word.direction === 'across') {
    return row === word.start_row && col >= word.start_col && col < word.start_col + word.length
  } else {
    return col === word.start_col && row >= word.start_row && row < word.start_row + word.length
  }
}

/**
 * 选择第一个未完成的单词
 */
GameScene.prototype.selectFirstUnfinishedWord = function() {
  for (var i = 0; i < this.words.length; i++) {
    var word = this.words[i]
    if (!this.completedWords.some(function(w) { return w.id === word.id })) {
      this.selectWord(word)
      return
    }
  }
}

/**
 * 选择单词
 */
GameScene.prototype.selectWord = function(word) {
  this.selectedWord = word
  
  // 移动到第一个未锁定的格子
  for (var i = 0; i < word.length; i++) {
    var row = word.start_row
    var col = word.start_col
    if (word.direction === 'across') {
      col += i
    } else {
      row += i
    }
    
    var key = row + '-' + col
    if (!this.prefilledCells[key]) {
      this.currentRow = row
      this.currentCol = col
      return
    }
  }
  
  this.currentRow = word.start_row
  this.currentCol = word.start_col
}

/**
 * 输入字母
 */
GameScene.prototype.inputLetter = function(letter) {
  var key = this.currentRow + '-' + this.currentCol
  
  // 不能修改预填格子
  if (this.prefilledCells[key]) return
  
  this.userAnswers[key] = letter.toUpperCase()
  this.audioManager.playTypeSound()
  
  // 检查单词完成
  this.checkWordsAtCell(this.currentRow, this.currentCol)
  
  // 移动到下一个格子
  this.moveToNextCell()
}

/**
 * 删除字母
 */
GameScene.prototype.deleteLetter = function() {
  this.audioManager.playDeleteSound()
  
  var key = this.currentRow + '-' + this.currentCol
  
  if (this.prefilledCells[key]) {
    this.moveToPrevCell()
    return
  }
  
  var currentAnswer = this.userAnswers[key]
  if (currentAnswer) {
    this.userAnswers[key] = ''
  } else {
    this.moveToPrevCell()
    key = this.currentRow + '-' + this.currentCol
    if (!this.prefilledCells[key]) {
      this.userAnswers[key] = ''
    }
  }
}

/**
 * 移动到下一个格子
 */
GameScene.prototype.moveToNextCell = function() {
  if (!this.selectedWord) return
  
  var word = this.selectedWord
  if (word.direction === 'across') {
    var nextCol = this.currentCol + 1
    while (nextCol < word.start_col + word.length) {
      var key = word.start_row + '-' + nextCol
      if (!this.prefilledCells[key]) {
        this.currentCol = nextCol
        return
      }
      nextCol++
    }
  } else {
    var nextRow = this.currentRow + 1
    while (nextRow < word.start_row + word.length) {
      var key = nextRow + '-' + word.start_col
      if (!this.prefilledCells[key]) {
        this.currentRow = nextRow
        return
      }
      nextRow++
    }
  }
  
  // 到达末尾，移动到下一个未完成的单词
  this.moveToNextUnfinishedWord()
}

/**
 * 移动到上一个格子
 */
GameScene.prototype.moveToPrevCell = function() {
  if (!this.selectedWord) return
  
  var word = this.selectedWord
  if (word.direction === 'across') {
    var prevCol = this.currentCol - 1
    while (prevCol >= word.start_col) {
      var key = word.start_row + '-' + prevCol
      if (!this.prefilledCells[key]) {
        this.currentCol = prevCol
        return
      }
      prevCol--
    }
  } else {
    var prevRow = this.currentRow - 1
    while (prevRow >= word.start_row) {
      var key = prevRow + '-' + word.start_col
      if (!this.prefilledCells[key]) {
        this.currentRow = prevRow
        return
      }
      prevRow--
    }
  }
}

/**
 * 移动到下一个未完成的单词
 */
GameScene.prototype.moveToNextUnfinishedWord = function() {
  var currentIdx = -1
  for (var i = 0; i < this.words.length; i++) {
    if (this.selectedWord && this.words[i].id === this.selectedWord.id) {
      currentIdx = i
      break
    }
  }
  
  for (var j = 1; j <= this.words.length; j++) {
    var idx = (currentIdx + j) % this.words.length
    var word = this.words[idx]
    if (!this.completedWords.some(function(w) { return w.id === word.id })) {
      this.selectWord(word)
      return
    }
  }
}

/**
 * 检查格子所在的单词
 */
GameScene.prototype.checkWordsAtCell = function(row, col) {
  var self = this
  var anyCorrect = false
  var completedIds = []
  
  for (var i = 0; i < this.words.length; i++) {
    var word = this.words[i]
    if (this.completedWords.some(function(w) { return w.id === word.id })) continue
    
    var isCorrect = this.checkWord(word)
    if (isCorrect) {
      anyCorrect = true
      completedIds.push(word.id)
    }
  }
  
  if (anyCorrect) {
    this.audioManager.playCorrectSound()
    
    // 如果当前选中的单词完成了，选择下一个
    if (this.selectedWord && completedIds.indexOf(this.selectedWord.id) >= 0) {
      setTimeout(function() {
        self.selectFirstUnfinishedWord()
      }, 100)
    }
    
    // 检查是否全部完成
    if (this.completedWords.length === this.words.length) {
      this.handleLevelComplete()
    }
  }
}

/**
 * 检查单词是否正确
 */
GameScene.prototype.checkWord = function(word) {
  var userWord = ''
  for (var i = 0; i < word.length; i++) {
    var row = word.start_row
    var col = word.start_col
    if (word.direction === 'across') {
      col += i
    } else {
      row += i
    }
    var key = row + '-' + col
    userWord += this.userAnswers[key] || ''
  }
  
  if (userWord.toUpperCase() === word.word.toUpperCase()) {
    this.completedWords.push(word)
    this.score += word.length * 10
    
    // 自动发音
    if (this.dataManager.settings.autoSpeak) {
      this.audioManager.playWordAudio(word.word)
    }
    
    return true
  }
  
  return false
}

/**
 * 检查所有单词
 */
GameScene.prototype.checkAllWords = function() {
  for (var i = 0; i < this.words.length; i++) {
    var word = this.words[i]
    if (!this.completedWords.some(function(w) { return w.id === word.id })) {
      this.checkWord(word)
    }
  }
}

/**
 * 处理关卡完成
 */
GameScene.prototype.handleLevelComplete = function() {
  this.stopTimer()
  this.audioManager.playLevelCompleteSound()
  
  if (this.mode === 'campaign') {
    // 保存进度
    var stars = this.calculateStars()
    this.dataManager.saveLevelComplete(this.group, this.level, stars, this.score, this.timer)
  } else {
    // 计时/无限模式
    this.sessionScore += this.score
    this.sessionLevelCount++
    this.sessionWordsCount += this.completedWords.length
    
    if (this.mode === 'endless' && !this.timedModeEnded) {
      // 无限模式自动下一关
      this.autoNextLevel()
      return
    }
  }
  
  // 从后端获取随机奖励
  var self = this
  this.generateRewardFromBackend(function(rewards) {
    self.earnedRewards = rewards
    self.showCompleteModal = true
  })
}

/**
 * 自动下一关（无限模式）
 */
GameScene.prototype.autoNextLevel = function() {
  var self = this
  
  // 重置状态
  this.resetGameState()
  this.loading = true
  
  // 加载新关卡
  this.loadRandomPuzzle()
}

/**
 * 触摸结束事件
 */
GameScene.prototype.onTouchEnd = function(e) {
  var touch = e.changedTouches[0]
  var x = touch.clientX
  var y = touch.clientY
  
  // 检查按钮点击
  for (var i = this.buttons.length - 1; i >= 0; i--) {
    var btn = this.buttons[i]
    if (render.isPointInRect({ x: x, y: y }, btn)) {
      this.handleButtonClick(btn)
      return
    }
  }
}

/**
 * 处理按钮点击
 */
GameScene.prototype.handleButtonClick = function(btn) {
  this.audioManager.playClickSound()
  
  switch (btn.action) {
    case 'back':
      this.goBack()
      break
    case 'cell':
      this.handleCellClick(btn.row, btn.col)
      break
    case 'word':
      if (!btn.completed) {
        this.selectWord(btn.word)
      } else {
        this.detailWord = btn.word
        this.showWordDetailModal = true
      }
      break
    case 'key':
      this.inputLetter(btn.key)
      break
    case 'delete':
      this.deleteLetter()
      break
    case 'hint':
      this.useHintProp()
      break
    case 'speak':
      this.useSpeakProp()
      break
    case 'backToHome':
      this.goBack()
      break
    case 'claimReward':
      this.claimReward()
      break
    case 'nextLevel':
      this.goNextLevel()
      break
    case 'claimEnergy':
      this.claimEnergy()
      break
    case 'closeDetail':
      this.showWordDetailModal = false
      this.detailWord = null
      break
    case 'speakUS':
      this.audioManager.playWordAudio(btn.word, 'us')
      break
    case 'speakUK':
      this.audioManager.playWordAudio(btn.word, 'uk')
      break
  }
}

/**
 * 处理格子点击
 */
GameScene.prototype.handleCellClick = function(row, col) {
  var key = row + '-' + col
  var cell = this.cells[row] ? this.cells[row][col] : null
  
  if (cell === null) return
  if (this.prefilledCells[key]) return
  
  this.currentRow = row
  this.currentCol = col
  
  // 选择该格子所属的单词
  this.selectWordAtCell(row, col)
}

/**
 * 选择格子所属的单词
 */
GameScene.prototype.selectWordAtCell = function(row, col) {
  // 优先横向
  for (var i = 0; i < this.words.length; i++) {
    var word = this.words[i]
    if (word.direction === 'across') {
      if (row === word.start_row && col >= word.start_col && col < word.start_col + word.length) {
        this.selectedWord = word
        return
      }
    }
  }
  
  // 再纵向
  for (var j = 0; j < this.words.length; j++) {
    var word = this.words[j]
    if (word.direction === 'down') {
      if (col === word.start_col && row >= word.start_row && row < word.start_row + word.length) {
        this.selectedWord = word
        return
      }
    }
  }
}

/**
 * 使用提示道具
 */
GameScene.prototype.useHintProp = function() {
  if (!this.selectedWord) return
  if (this.dataManager.hintCount <= 0) return
  
  this.dataManager.useHintProp()
  this.hintActive = true
  this.hintWordId = this.selectedWord.id
  
  // 3秒后关闭高亮
  var self = this
  setTimeout(function() {
    self.hintActive = false
    self.hintWordId = null
  }, 3000)
}

/**
 * 使用发音道具（朗读当前单词三遍）
 */
GameScene.prototype.useSpeakProp = function() {
  if (!this.selectedWord) return
  if (this.dataManager.speakCount <= 0) return
  if (this.speakActive) return  // 正在播放中不重复触发
  
  this.dataManager.useSpeakProp()
  this.speakActive = true
  
  // 朗读当前单词三遍
  var self = this
  this.audioManager.playWordAudioRepeated(this.selectedWord.word, 3, function() {
    self.speakActive = false
  })
}

/**
 * 领取奖励
 */
GameScene.prototype.claimReward = function() {
  if (this.rewardClaimed) return
  
  this.rewardClaimed = true
  
  // 累加奖励
  for (var i = 0; i < this.earnedRewards.length; i++) {
    var reward = this.earnedRewards[i]
    if (reward.type === 'energy') {
      this.dataManager.addEnergy(reward.value)
    } else if (reward.type === 'hint') {
      this.dataManager.addProps(reward.value, 0)
    } else if (reward.type === 'speak') {
      this.dataManager.addProps(0, reward.value)
    }
  }
  
  // 同步道具到后端
  this.dataManager.syncPropsToBackend()
  
  // 领取奖励到后端记录
  var self = this
  wx.request({
    url: config.API_BASE + '/api/game/claim-reward',
    method: 'POST',
    header: { 'X-User-Id': this.dataManager.userId, 'Content-Type': 'application/json' },
    data: {
      level: this.level,
      vocab_group: this.dataManager.currentGroup,
      stars: this.stars,
      time_seconds: this.timerElapsed || 0,
      rewards: this.earnedRewards
    }
  })
}

/**
 * 从后端生成随机奖励
 */
GameScene.prototype.generateRewardFromBackend = function(callback) {
  var self = this
  
  wx.request({
    url: config.API_BASE + '/api/game/generate-reward',
    method: 'POST',
    header: { 'X-User-Id': this.dataManager.userId, 'Content-Type': 'application/json' },
    data: {},
    success: function(res) {
      if (res.data && res.data.rewards) {
        // 转换奖励格式
        var rewards = res.data.rewards.map(function(r) {
          var icons = { energy: '⚡', hint: '💡', speak: '🔊' }
          var names = { energy: '体力', hint: '提示', speak: '发音' }
          return {
            type: r.type,
            name: names[r.type] || r.type,
            icon: icons[r.type] || '🎁',
            value: r.value
          }
        })
        callback(rewards)
      } else {
        // 后端无响应时使用默认奖励
        callback([
          { type: 'energy', name: '体力', icon: '⚡', value: 5 },
          { type: 'hint', name: '提示', icon: '💡', value: 1 }
        ])
      }
    },
    fail: function() {
      // 网络错误时使用默认奖励
      callback([
        { type: 'energy', name: '体力', icon: '⚡', value: 5 },
        { type: 'hint', name: '提示', icon: '💡', value: 1 }
      ])
    }
  })
}

/**
 * 进入下一关
 */
GameScene.prototype.goNextLevel = function() {
  var self = this
  
  if (this.timedModeEnded) {
    // 再玩一次
    this.timedModeEnded = false
    this.sessionScore = 0
    this.sessionLevelCount = 0
    this.sessionWordsCount = 0
  }
  
  // 检查体力
  var energyResult = this.dataManager.consumeEnergy(this.mode)
  if (!energyResult.success) {
    this.showCompleteModal = false
    this.showEnergyModal = true
    this.energyInfo = energyResult
    return
  }
  
  this.showCompleteModal = false
  this.rewardClaimed = false
  this.earnedRewards = []
  
  if (this.mode === 'campaign') {
    this.level++
    this.dataManager.currentLevel = this.level
    this.dataManager.saveGameState()
  }
  
  this.resetGameState()
  this.loadLevel()
}

/**
 * 领取体力
 */
GameScene.prototype.claimEnergy = function() {
  var self = this
  
  // 埋点追踪：领取免费体力
  wx.request({
    url: config.API_BASE + '/api/track/energy-claim',
    method: 'POST',
    header: { 'X-User-Id': this.dataManager.userId, 'Content-Type': 'application/json' },
    data: {
      claim_type: 'free_claim',
      amount: 30,
      platform: 'wechat-minigame'
    }
  })
  
  this.dataManager.claimFreeEnergy()
  
  // 检查是否足够
  var energyResult = this.dataManager.consumeEnergy(this.mode)
  if (energyResult.success) {
    this.showEnergyModal = false
    this.loadLevel()
  } else {
    this.energyInfo = energyResult
  }
}

/**
 * 返回首页
 */
GameScene.prototype.goBack = function() {
  this.stopTimer()
  this.audioManager.stopBgMusic()
  this.main.showScene('home')
}

/**
 * 销毁场景
 */
GameScene.prototype.destroy = function() {
  this.stopTimer()
}

module.exports = GameScene
