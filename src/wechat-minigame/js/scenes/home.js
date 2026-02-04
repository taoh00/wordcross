/**
 * 首页场景
 * 模式选择、词库选择、关卡选择
 */

var config = require('../config')
var render = require('../utils/render')

var COLORS = config.COLORS
var VOCAB_GROUPS = config.VOCAB_GROUPS
var DIFFICULTY_OPTIONS = config.DIFFICULTY_OPTIONS
var DURATION_OPTIONS = config.DURATION_OPTIONS
var GAME_MODES = config.GAME_MODES
var DEV_CONFIG = config.DEV_CONFIG
var FONT_SIZES = config.FONT_SIZES

/**
 * 首页场景类
 */
function HomeScene(main) {
  this.main = main
  this.ctx = main.ctx
  this.screenWidth = main.screenWidth
  this.screenHeight = main.screenHeight
  this.dataManager = main.dataManager
  this.audioManager = main.audioManager
  
  // 当前步骤: mode -> duration(计时) -> difficulty(无限/计时) -> group -> subgroup -> level
  this.currentStep = 'mode'
  
  // 选择状态
  this.selectedMode = null
  this.selectedDuration = 60
  this.selectedDifficulty = 'medium'
  this.selectedGroup = null
  this.selectedGroupData = null
  this.selectedSubGroup = null
  
  // 关卡分页（小游戏屏幕限制：每页20关）
  // 网页版每页100关但有滚动，小游戏需要分页显示
  this.currentPage = 1
  this.levelsPerPage = 20  // 每页20关（5行×4列）
  this.maxLevels = 0
  
  // 词库关卡数缓存
  this.groupLevelCounts = {}
  
  // UI元素列表（用于点击检测）
  this.buttons = []
  
  // 滚动偏移
  this.scrollY = 0
  this.maxScrollY = 0
  
  // 开发模式状态
  this.devModeEnabled = false
  this.versionClickCount = 0
  this.versionClickTimer = null
  this.versionRect = null  // 版本号点击区域
  
  // 从本地存储加载开发模式状态
  try {
    this.devModeEnabled = wx.getStorageSync('dev_mode') === 'true'
  } catch (e) {
    this.devModeEnabled = false
  }
  
  this.init()
}

/**
 * 初始化
 */
HomeScene.prototype.init = function() {
  // 加载关卡汇总
  this.loadLevelsSummary()
}

/**
 * 加载关卡汇总
 */
HomeScene.prototype.loadLevelsSummary = function() {
  var self = this
  this.dataManager.loadLevelsSummary(function(err, data) {
    if (!err && data && data.groups) {
      for (var i = 0; i < data.groups.length; i++) {
        var group = data.groups[i]
        self.groupLevelCounts[group.group_code] = group.level_count || 0
      }
    }
  })
}

/**
 * 渲染场景
 */
HomeScene.prototype.render = function(ctx) {
  this.buttons = []
  
  // 波点背景（马卡龙风格）
  render.drawDotBackground(ctx, this.screenWidth, this.screenHeight)
  
  // 根据当前步骤渲染不同内容
  switch (this.currentStep) {
    case 'mode':
      this.renderModeSelection(ctx)
      break
    case 'duration':
      this.renderDurationSelection(ctx)
      break
    case 'difficulty':
      this.renderDifficultySelection(ctx)
      break
    case 'group':
      this.renderGroupSelection(ctx)
      break
    case 'subgroup':
      this.renderSubgroupSelection(ctx)
      break
    case 'level':
      this.renderLevelSelection(ctx)
      break
  }
}

/**
 * 渲染模式选择
 */
HomeScene.prototype.renderModeSelection = function(ctx) {
  var padding = 20
  var centerX = this.screenWidth / 2
  
  // 标题
  render.drawTitle(ctx, centerX, 80, '🌟 我爱填单词 🌟', { fontSize: 32, color: COLORS.primary })
  render.drawSubtitle(ctx, centerX, 120, 'WordCross · 趣味英语学习', { fontSize: 16 })
  
  // 用户信息栏
  var userInfo = this.dataManager.getUserSummary()
  render.drawUserInfoBar(ctx, padding, 150, this.screenWidth - padding * 2, 50, userInfo)
  
  // 模式选择标题
  render.drawTitle(ctx, centerX, 230, '🎮 选择游戏模式', { fontSize: 20, color: COLORS.text })
  
  // 模式按钮 - 2列布局
  var buttonWidth = (this.screenWidth - padding * 3) / 2
  var buttonHeight = 80
  var startY = 260
  var gap = 15
  
  // 闯关模式
  this.buttons.push(this.renderModeButton(ctx, padding, startY, buttonWidth, buttonHeight, 
    'campaign', GAME_MODES.campaign, 
    { bgColor: '#FFB6C1', shadowColor: '#FF69B4', borderColor: '#FFB6C1' }))
  
  // 无限模式
  this.buttons.push(this.renderModeButton(ctx, padding + buttonWidth + gap, startY, buttonWidth, buttonHeight,
    'endless', GAME_MODES.endless,
    { bgColor: '#98FB98', shadowColor: '#3CB371', borderColor: '#98FB98' }))
  
  // 计时模式
  this.buttons.push(this.renderModeButton(ctx, padding, startY + buttonHeight + gap, buttonWidth, buttonHeight,
    'timed', GAME_MODES.timed,
    { bgColor: '#87CEEB', shadowColor: '#4682B4', borderColor: '#87CEEB' }))
  
  // 排行榜
  this.buttons.push(this.renderModeButton(ctx, padding + buttonWidth + gap, startY + buttonHeight + gap, buttonWidth, buttonHeight,
    'leaderboard', { name: '排行榜', icon: '🏆', desc: '看看排名' },
    { bgColor: '#FFFACD', shadowColor: '#F0E68C', borderColor: '#FFFACD' }))
  
  // 开发模式按钮区（仅开发模式下显示）
  var devY = startY + (buttonHeight + gap) * 2 + 10
  if (this.devModeEnabled) {
    var devBtnWidth = (this.screenWidth - padding * 3) / 2
    
    // 测试模式按钮
    this.buttons.push(render.drawButton(ctx, padding, devY, devBtnWidth, 40, '🧪 测试模式', {
      bgColor: COLORS.lemon,
      shadowColor: COLORS.warningDark,
      textColor: '#92400e',
      fontSize: 13
    }))
    this.buttons[this.buttons.length - 1].action = 'testMode'
    
    // 重置全部按钮
    this.buttons.push(render.drawButton(ctx, padding + devBtnWidth + gap, devY, devBtnWidth, 40, '🔄 重置全部', {
      bgColor: COLORS.errorLight,
      shadowColor: COLORS.error,
      textColor: '#7f1d1d',
      fontSize: 13
    }))
    this.buttons[this.buttons.length - 1].action = 'resetAll'
    
    devY += 50
  }
  
  // 设置入口
  var settingsY = devY + 10
  this.buttons.push(render.drawButton(ctx, padding, settingsY, this.screenWidth - padding * 2, 50, '⚙️ 设置', {
    bgColor: '#DDA0DD',
    shadowColor: '#BA55D3',
    textColor: COLORS.text,
    fontSize: 16
  }))
  this.buttons[this.buttons.length - 1].action = 'settings'
  
  // 版本号（可点击开启开发模式）
  var versionY = this.screenHeight - 30
  ctx.fillStyle = COLORS.textLight
  ctx.font = '12px sans-serif'
  ctx.textAlign = 'center'
  var versionText = '我爱填单词 v1.0.0' + (this.devModeEnabled ? ' (Dev)' : '')
  ctx.fillText(versionText, centerX, versionY)
  
  // 保存版本号点击区域
  this.versionRect = { 
    x: centerX - 80, 
    y: versionY - 15, 
    width: 160, 
    height: 30 
  }
  
  // 底部装饰
  this.renderFooterDecoration(ctx)
}

/**
 * 渲染模式按钮
 */
HomeScene.prototype.renderModeButton = function(ctx, x, y, width, height, mode, modeInfo, colors) {
  // 阴影
  render.drawRoundRect(ctx, x, y + 4, width, height, 16, colors.shadowColor, null)
  
  // 主体
  render.drawRoundRect(ctx, x, y, width, height, 16, colors.bgColor, colors.borderColor)
  ctx.lineWidth = 2
  
  // 图标
  ctx.font = '32px sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'
  ctx.fillText(modeInfo.icon, x + 15, y + height / 2)
  
  // 标题
  ctx.fillStyle = COLORS.text
  ctx.font = 'bold 16px sans-serif'
  ctx.fillText(modeInfo.name, x + 55, y + height / 2 - 10)
  
  // 描述
  ctx.font = '12px sans-serif'
  ctx.fillStyle = COLORS.textLight
  ctx.fillText(modeInfo.desc, x + 55, y + height / 2 + 10)
  
  return { x: x, y: y, width: width, height: height, action: 'mode', mode: mode }
}

/**
 * 渲染时间选择（计时模式）
 */
HomeScene.prototype.renderDurationSelection = function(ctx) {
  var padding = 20
  var centerX = this.screenWidth / 2
  
  // 返回按钮
  this.buttons.push(this.renderBackButton(ctx, padding, 40))
  
  // 标题
  render.drawTitle(ctx, centerX, 100, '⏱️ 选择时间', { fontSize: 24, color: COLORS.primary })
  
  // 时间选项
  var buttonWidth = this.screenWidth - padding * 2
  var buttonHeight = 60
  var startY = 150
  var gap = 15
  
  for (var i = 0; i < DURATION_OPTIONS.length; i++) {
    var opt = DURATION_OPTIONS[i]
    var y = startY + i * (buttonHeight + gap)
    var isActive = this.selectedDuration === opt.value
    
    this.buttons.push(render.drawButton(ctx, padding, y, buttonWidth, buttonHeight, 
      opt.icon + ' ' + opt.label, {
        bgColor: isActive ? COLORS.primary : COLORS.white,
        shadowColor: isActive ? COLORS.primaryLight : COLORS.border,
        textColor: isActive ? COLORS.white : COLORS.text,
        fontSize: 18
      }))
    this.buttons[this.buttons.length - 1].action = 'duration'
    this.buttons[this.buttons.length - 1].value = opt.value
  }
  
  // 提示
  this.renderHint(ctx, '💡 选择游戏总时长', startY + DURATION_OPTIONS.length * (buttonHeight + gap) + 20)
}

/**
 * 渲染难度选择
 */
HomeScene.prototype.renderDifficultySelection = function(ctx) {
  var padding = 20
  var centerX = this.screenWidth / 2
  
  // 返回按钮
  this.buttons.push(this.renderBackButton(ctx, padding, 40))
  
  // 标题
  render.drawTitle(ctx, centerX, 100, '⚡ 选择难度', { fontSize: 24, color: COLORS.primary })
  
  // 已选时间提示（计时模式）
  if (this.selectedMode === 'timed') {
    var durationText = DURATION_OPTIONS.find(function(d) { return d.value === this.selectedDuration }.bind(this))
    if (durationText) {
      this.renderBanner(ctx, padding, 130, '已选时间：' + durationText.label, COLORS.primaryBg, COLORS.primary)
    }
  }
  
  // 难度选项
  var buttonWidth = this.screenWidth - padding * 2
  var buttonHeight = 70
  var startY = this.selectedMode === 'timed' ? 180 : 150
  var gap = 15
  
  var diffColors = {
    low: { bg: '#a7f3d0', shadow: '#10b981' },
    medium: { bg: '#fde68a', shadow: '#d97706' },
    high: { bg: '#fca5a5', shadow: '#dc2626' }
  }
  
  for (var i = 0; i < DIFFICULTY_OPTIONS.length; i++) {
    var opt = DIFFICULTY_OPTIONS[i]
    var y = startY + i * (buttonHeight + gap)
    var colors = diffColors[opt.code]
    
    this.buttons.push(this.renderDifficultyButton(ctx, padding, y, buttonWidth, buttonHeight, opt, colors))
  }
  
  // 提示
  this.renderHint(ctx, '💡 难度决定单词长度范围', startY + DIFFICULTY_OPTIONS.length * (buttonHeight + gap) + 20)
}

/**
 * 渲染难度按钮
 */
HomeScene.prototype.renderDifficultyButton = function(ctx, x, y, width, height, opt, colors) {
  // 阴影
  render.drawRoundRect(ctx, x, y + 4, width, height, 16, colors.shadow, null)
  
  // 主体
  render.drawRoundRect(ctx, x, y, width, height, 16, colors.bg, null)
  
  // 图标
  ctx.font = '28px sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'
  ctx.fillText(opt.icon, x + 20, y + height / 2)
  
  // 标题
  ctx.fillStyle = COLORS.text
  ctx.font = 'bold 18px sans-serif'
  ctx.fillText(opt.name, x + 60, y + height / 2 - 10)
  
  // 描述
  ctx.font = '12px sans-serif'
  ctx.fillStyle = COLORS.textLight
  ctx.fillText(opt.desc, x + 60, y + height / 2 + 12)
  
  return { x: x, y: y, width: width, height: height, action: 'difficulty', code: opt.code }
}

/**
 * 渲染词库选择
 */
HomeScene.prototype.renderGroupSelection = function(ctx) {
  var padding = 20
  var centerX = this.screenWidth / 2
  
  // 返回按钮
  this.buttons.push(this.renderBackButton(ctx, padding, 40))
  
  // 标题
  render.drawTitle(ctx, centerX, 100, '📚 选择词库', { fontSize: 24, color: COLORS.primary })
  
  // 已选难度提示
  if (this.selectedMode !== 'campaign') {
    var diffText = DIFFICULTY_OPTIONS.find(function(d) { return d.code === this.selectedDifficulty }.bind(this))
    if (diffText) {
      this.renderBanner(ctx, padding, 130, '已选难度：' + diffText.name, '#e0f2fe', '#0369a1')
    }
  }
  
  // 词库网格 - 3列
  var cols = 3
  var gap = 10
  var buttonSize = (this.screenWidth - padding * 2 - gap * (cols - 1)) / cols
  var startY = this.selectedMode !== 'campaign' ? 180 : 150
  
  for (var i = 0; i < VOCAB_GROUPS.length; i++) {
    var group = VOCAB_GROUPS[i]
    var col = i % cols
    var row = Math.floor(i / cols)
    var x = padding + col * (buttonSize + gap)
    var y = startY + row * (buttonSize + gap)
    
    this.buttons.push(this.renderGroupButton(ctx, x, y, buttonSize, buttonSize, group))
  }
}

/**
 * 渲染词库按钮
 */
HomeScene.prototype.renderGroupButton = function(ctx, x, y, width, height, group) {
  // 卡片
  render.drawCard(ctx, x, y, width, height, {
    radius: 14,
    bgColor: COLORS.white,
    borderColor: COLORS.border,
    shadowColor: COLORS.borderDark,
    shadowOffset: 3
  })
  
  // 图标
  ctx.font = '24px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(group.icon, x + width / 2, y + height / 2 - 10)
  
  // 名称
  ctx.fillStyle = COLORS.text
  ctx.font = 'bold 11px sans-serif'
  ctx.fillText(group.name, x + width / 2, y + height / 2 + 18)
  
  // 箭头（有子分组）
  if (group.hasSubGroups && (this.selectedMode === 'campaign' || this.selectedMode === 'endless')) {
    ctx.fillStyle = COLORS.primary
    ctx.font = '14px sans-serif'
    ctx.textAlign = 'right'
    ctx.fillText('›', x + width - 8, y + height / 2)
  }
  
  return { x: x, y: y, width: width, height: height, action: 'group', group: group }
}

/**
 * 渲染子分组选择
 */
HomeScene.prototype.renderSubgroupSelection = function(ctx) {
  var padding = 20
  var centerX = this.screenWidth / 2
  
  // 返回按钮
  this.buttons.push(this.renderBackButton(ctx, padding, 40))
  
  // 标题
  var groupName = this.selectedGroupData ? this.selectedGroupData.name : ''
  render.drawTitle(ctx, centerX, 100, '📂 选择' + groupName + '细分', { fontSize: 20, color: COLORS.primary })
  
  if (!this.selectedGroupData || !this.selectedGroupData.subGroups) return
  
  // 子分组网格 - 3列
  var subGroups = this.selectedGroupData.subGroups
  var cols = 3
  var gap = 10
  var buttonSize = (this.screenWidth - padding * 2 - gap * (cols - 1)) / cols
  var startY = 140
  
  for (var i = 0; i < subGroups.length; i++) {
    var sub = subGroups[i]
    var col = i % cols
    var row = Math.floor(i / cols)
    var x = padding + col * (buttonSize + gap)
    var y = startY + row * (buttonSize + gap)
    
    var isAll = sub.code.endsWith('_all')
    this.buttons.push(this.renderSubgroupButton(ctx, x, y, buttonSize, buttonSize, sub, isAll))
  }
}

/**
 * 渲染子分组按钮
 */
HomeScene.prototype.renderSubgroupButton = function(ctx, x, y, width, height, sub, isAll) {
  var bgColor = isAll ? COLORS.lemon : COLORS.white
  var borderColor = isAll ? COLORS.warning : COLORS.primaryLight
  var shadowColor = isAll ? COLORS.warningDark : COLORS.border
  
  render.drawCard(ctx, x, y, width, height, {
    radius: 14,
    bgColor: bgColor,
    borderColor: borderColor,
    shadowColor: shadowColor,
    shadowOffset: 3
  })
  
  // 图标
  ctx.font = '22px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(sub.icon, x + width / 2, y + height / 2 - 10)
  
  // 名称
  ctx.fillStyle = isAll ? COLORS.warningDark : COLORS.text
  ctx.font = 'bold 10px sans-serif'
  ctx.fillText(sub.name, x + width / 2, y + height / 2 + 16)
  
  return { x: x, y: y, width: width, height: height, action: 'subgroup', code: sub.code }
}

/**
 * 渲染关卡选择
 */
HomeScene.prototype.renderLevelSelection = function(ctx) {
  var padding = 20
  var centerX = this.screenWidth / 2
  
  // 返回按钮
  this.buttons.push(this.renderBackButton(ctx, padding, 40))
  
  // 标题
  render.drawTitle(ctx, centerX, 100, '🏰 选择关卡', { fontSize: 24, color: COLORS.primary })
  
  // 词库信息横幅
  var groupName = this.getGroupName(this.selectedGroup)
  var progress = this.dataManager.getGroupProgress(this.selectedGroup)
  var completedCount = Object.keys(progress.completed).length
  var maxLevels = this.groupLevelCounts[this.selectedGroup] || 180
  this.maxLevels = maxLevels
  
  this.renderBanner(ctx, padding, 130, '📚 ' + groupName + '  ' + completedCount + '/' + maxLevels + '关', 
    COLORS.primaryBg, COLORS.primary)
  
  // 关卡网格 - 4列
  var cols = 4
  var gap = 8
  var buttonSize = (this.screenWidth - padding * 2 - gap * (cols - 1)) / cols
  var startY = 180
  
  // 计算当前页关卡
  var startLevel = (this.currentPage - 1) * this.levelsPerPage + 1
  var endLevel = Math.min(this.currentPage * this.levelsPerPage, maxLevels)
  
  for (var level = startLevel; level <= endLevel; level++) {
    var idx = level - startLevel
    var col = idx % cols
    var row = Math.floor(idx / cols)
    var x = padding + col * (buttonSize + gap)
    var y = startY + row * (buttonSize + gap)
    
    this.buttons.push(this.renderLevelButton(ctx, x, y, buttonSize, buttonSize, level, progress))
  }
  
  // 分页控制
  var totalPages = Math.ceil(maxLevels / this.levelsPerPage)
  if (totalPages > 1) {
    this.renderPagination(ctx, padding, this.screenHeight - 80, totalPages)
  }
}

/**
 * 渲染关卡按钮
 */
HomeScene.prototype.renderLevelButton = function(ctx, x, y, width, height, level, progress) {
  var isCompleted = progress.completed[level]
  var isUnlocked = level <= progress.unlocked
  
  var bgColor = COLORS.white
  var borderColor = COLORS.primaryLight
  var shadowColor = COLORS.border
  var textColor = COLORS.text
  
  if (isCompleted) {
    bgColor = '#d1fae5'
    borderColor = '#34d399'
    shadowColor = '#10b981'
    textColor = '#065f46'
  } else if (isUnlocked) {
    bgColor = '#fef3c7'
    borderColor = '#fbbf24'
    shadowColor = '#d97706'
    textColor = '#92400e'
  } else {
    bgColor = '#e5e7eb'
    borderColor = '#9ca3af'
    shadowColor = '#6b7280'
    textColor = '#6b7280'
  }
  
  render.drawCard(ctx, x, y, width, height, {
    radius: 10,
    bgColor: bgColor,
    borderColor: borderColor,
    shadowColor: shadowColor,
    shadowOffset: 3
  })
  
  // 关卡号 - 使用标准字体大小
  ctx.fillStyle = textColor
  ctx.font = 'bold ' + FONT_SIZES.levelButton + 'px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(level.toString(), x + width / 2, y + height / 2 - 8)
  
  // 星级或锁定状态
  ctx.font = '10px sans-serif'
  if (isCompleted) {
    var stars = progress.completed[level].stars || 3
    ctx.fillText('⭐'.repeat(stars), x + width / 2, y + height / 2 + 12)
  } else if (isUnlocked) {
    ctx.fillStyle = COLORS.warningDark
    ctx.fillText('挑战', x + width / 2, y + height / 2 + 12)
  } else {
    ctx.fillText('🔒', x + width / 2, y + height / 2 + 12)
  }
  
  return { 
    x: x, y: y, width: width, height: height, 
    action: 'level', 
    level: level, 
    unlocked: isUnlocked 
  }
}

/**
 * 渲染分页控制（范围分页器：1-100, 101-200等）
 */
HomeScene.prototype.renderPagination = function(ctx, x, y, totalPages) {
  var centerX = this.screenWidth / 2
  var padding = 15
  var maxBtns = 5  // 最多显示5个页码按钮
  
  // 计算要显示的页码范围
  var startPage = Math.max(1, this.currentPage - Math.floor(maxBtns / 2))
  var endPage = Math.min(totalPages, startPage + maxBtns - 1)
  startPage = Math.max(1, endPage - maxBtns + 1)
  
  var btnCount = endPage - startPage + 1
  var btnWidth = 60
  var gap = 6
  var totalWidth = btnCount * btnWidth + (btnCount - 1) * gap
  var startX = centerX - totalWidth / 2
  
  // 渲染页码按钮（范围形式：1-100）
  for (var i = startPage; i <= endPage; i++) {
    var btnX = startX + (i - startPage) * (btnWidth + gap)
    var isActive = i === this.currentPage
    var rangeStart = (i - 1) * this.levelsPerPage + 1
    var rangeEnd = Math.min(i * this.levelsPerPage, this.maxLevels)
    var label = rangeStart + '-' + rangeEnd
    
    this.buttons.push(render.drawButton(ctx, btnX, y, btnWidth, 32, label, {
      bgColor: isActive ? COLORS.primary : COLORS.white,
      shadowColor: isActive ? COLORS.primaryDark : COLORS.border,
      textColor: isActive ? COLORS.white : COLORS.text,
      fontSize: 11
    }))
    this.buttons[this.buttons.length - 1].action = 'gotoPage'
    this.buttons[this.buttons.length - 1].page = i
  }
  
  // 如果页码太多，添加首页/末页按钮
  if (startPage > 1) {
    this.buttons.push(render.drawButton(ctx, padding, y, 36, 32, '«', {
      bgColor: COLORS.white,
      shadowColor: COLORS.border,
      textColor: COLORS.text,
      fontSize: 16
    }))
    this.buttons[this.buttons.length - 1].action = 'gotoPage'
    this.buttons[this.buttons.length - 1].page = 1
  }
  
  if (endPage < totalPages) {
    this.buttons.push(render.drawButton(ctx, this.screenWidth - padding - 36, y, 36, 32, '»', {
      bgColor: COLORS.white,
      shadowColor: COLORS.border,
      textColor: COLORS.text,
      fontSize: 16
    }))
    this.buttons[this.buttons.length - 1].action = 'gotoPage'
    this.buttons[this.buttons.length - 1].page = totalPages
  }
}

/**
 * 渲染返回按钮
 */
HomeScene.prototype.renderBackButton = function(ctx, x, y) {
  return render.drawButton(ctx, x, y, 70, 36, '← 返回', {
    bgColor: COLORS.white,
    shadowColor: COLORS.border,
    textColor: COLORS.textLight,
    fontSize: 14
  })
}

/**
 * 渲染提示文字
 */
HomeScene.prototype.renderHint = function(ctx, text, y) {
  var padding = 20
  var width = this.screenWidth - padding * 2
  
  render.drawRoundRect(ctx, padding, y, width, 40, 10, '#f0f9ff', '#7dd3fc')
  
  ctx.fillStyle = '#0369a1'
  ctx.font = '13px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(text, this.screenWidth / 2, y + 20)
}

/**
 * 渲染横幅
 */
HomeScene.prototype.renderBanner = function(ctx, x, y, text, bgColor, textColor) {
  var width = this.screenWidth - x * 2
  
  render.drawRoundRect(ctx, x, y, width, 36, 10, bgColor, null)
  
  ctx.fillStyle = textColor
  ctx.font = 'bold 13px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(text, x + width / 2, y + 18)
}

/**
 * 渲染底部装饰
 */
HomeScene.prototype.renderFooterDecoration = function(ctx) {
  var y = this.screenHeight - 40
  var icons = ['🎨', '📖', '✏️']
  var gap = 40
  var startX = this.screenWidth / 2 - gap
  
  ctx.font = '24px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  
  for (var i = 0; i < icons.length; i++) {
    ctx.fillText(icons[i], startX + i * gap, y)
  }
}

/**
 * 获取词库名称
 */
HomeScene.prototype.getGroupName = function(code) {
  for (var i = 0; i < VOCAB_GROUPS.length; i++) {
    var group = VOCAB_GROUPS[i]
    if (group.code === code) return group.icon + ' ' + group.name
    if (group.subGroups) {
      for (var j = 0; j < group.subGroups.length; j++) {
        var sub = group.subGroups[j]
        if (sub.code === code) return sub.icon + ' ' + sub.name
      }
    }
  }
  return code
}

/**
 * 触摸结束事件
 */
HomeScene.prototype.onTouchEnd = function(e) {
  var touch = e.changedTouches[0]
  var x = touch.clientX
  var y = touch.clientY
  
  // 检查版本号点击（开启开发模式后门）
  if (this.currentStep === 'mode' && this.versionRect && 
      render.isPointInRect({ x: x, y: y }, this.versionRect)) {
    this.handleVersionClick()
    return
  }
  
  // 检查按钮点击
  for (var i = 0; i < this.buttons.length; i++) {
    var btn = this.buttons[i]
    if (render.isPointInRect({ x: x, y: y }, btn)) {
      this.handleButtonClick(btn)
      return
    }
  }
}

/**
 * 处理版本号点击（开发模式后门）
 */
HomeScene.prototype.handleVersionClick = function() {
  var self = this
  
  this.versionClickCount++
  
  // 清除之前的定时器
  if (this.versionClickTimer) {
    clearTimeout(this.versionClickTimer)
  }
  
  // 设置超时重置
  this.versionClickTimer = setTimeout(function() {
    self.versionClickCount = 0
  }, DEV_CONFIG.clickTimeout)
  
  // 达到阈值切换开发模式
  if (this.versionClickCount >= DEV_CONFIG.clickThreshold) {
    this.versionClickCount = 0
    this.devModeEnabled = !this.devModeEnabled
    
    // 保存状态
    try {
      wx.setStorageSync('dev_mode', this.devModeEnabled ? 'true' : 'false')
    } catch (e) {}
    
    // 提示
    wx.showToast({
      title: this.devModeEnabled ? '🔓 开发模式已开启' : '🔒 开发模式已关闭',
      icon: 'none'
    })
  } else if (this.versionClickCount >= DEV_CONFIG.clickThreshold - 3) {
    // 剩余3次时给提示
    var remaining = DEV_CONFIG.clickThreshold - this.versionClickCount
    wx.showToast({
      title: '再点击' + remaining + '次' + (this.devModeEnabled ? '关闭' : '开启') + '开发模式',
      icon: 'none',
      duration: 1000
    })
  }
}

/**
 * 处理按钮点击
 */
HomeScene.prototype.handleButtonClick = function(btn) {
  this.audioManager.playClickSound()
  
  switch (btn.action) {
    case 'mode':
      this.selectMode(btn.mode)
      break
    case 'duration':
      this.selectDuration(btn.value)
      break
    case 'difficulty':
      this.selectDifficulty(btn.code)
      break
    case 'group':
      this.selectGroup(btn.group)
      break
    case 'subgroup':
      this.selectSubgroup(btn.code)
      break
    case 'level':
      if (btn.unlocked) {
        this.startCampaignLevel(btn.level)
      }
      break
    case 'prevPage':
      this.currentPage--
      break
    case 'nextPage':
      this.currentPage++
      break
    case 'gotoPage':
      this.currentPage = btn.page
      break
    case 'settings':
      this.main.showScene('settings')
      break
    case 'leaderboard':
      this.main.showScene('leaderboard')
      break
    case 'testMode':
      // 测试模式 - 显示提示（暂未实现完整功能）
      wx.showToast({ title: '测试模式开发中...', icon: 'none' })
      break
    case 'resetAll':
      // 重置全部数据
      this.showResetConfirmDialog()
      break
    default:
      // 返回按钮
      this.goBack()
  }
}

/**
 * 显示重置确认对话框
 */
HomeScene.prototype.showResetConfirmDialog = function() {
  var self = this
  var API_BASE = config.API_BASE
  
  wx.showModal({
    title: '确认重置',
    content: '将清除所有进度和数据，此操作不可恢复！',
    confirmText: '重置',
    confirmColor: '#ef4444',
    success: function(res) {
      if (res.confirm) {
        try {
          // 清除本地存储
          wx.clearStorageSync()
          
          // 重新初始化数据管理器（设为初始值）
          self.dataManager.init()
          
          // 同步到服务器
          var userId = self.dataManager.userId
          
          // 同步体力（重置为200）
          wx.request({
            url: API_BASE + '/api/user/energy',
            method: 'PUT',
            header: { 'X-User-Id': userId, 'Content-Type': 'application/json' },
            data: { energy: 200 },
            success: function() { console.log('体力同步成功') },
            fail: function(e) { console.warn('体力同步失败:', e) }
          })
          
          // 同步道具（重置为20/20）
          wx.request({
            url: API_BASE + '/api/user/props',
            method: 'PUT',
            header: { 'X-User-Id': userId, 'Content-Type': 'application/json' },
            data: { hintLetterCount: 20, showTranslationCount: 20 },
            success: function() { console.log('道具同步成功') },
            fail: function(e) { console.warn('道具同步失败:', e) }
          })
          
          wx.showToast({ title: '重置成功', icon: 'success' })
        } catch (e) {
          console.error('重置失败:', e)
          wx.showToast({ title: '重置失败', icon: 'none' })
        }
      }
    }
  })
}

/**
 * 选择模式
 */
HomeScene.prototype.selectMode = function(mode) {
  if (mode === 'leaderboard') {
    this.main.showScene('leaderboard')
    return
  }
  
  this.selectedMode = mode
  this.dataManager.currentMode = mode
  
  if (mode === 'timed') {
    this.currentStep = 'duration'
  } else if (mode === 'endless') {
    this.currentStep = 'difficulty'
  } else {
    this.currentStep = 'group'
  }
}

/**
 * 选择时间
 */
HomeScene.prototype.selectDuration = function(duration) {
  this.selectedDuration = duration
  this.dataManager.currentDuration = duration
  this.currentStep = 'difficulty'
}

/**
 * 选择难度
 */
HomeScene.prototype.selectDifficulty = function(difficulty) {
  this.selectedDifficulty = difficulty
  this.dataManager.currentDifficulty = difficulty
  this.currentStep = 'group'
}

/**
 * 选择词库
 */
HomeScene.prototype.selectGroup = function(group) {
  this.selectedGroupData = group
  
  if (group.hasSubGroups && (this.selectedMode === 'campaign' || this.selectedMode === 'endless')) {
    this.currentStep = 'subgroup'
  } else {
    this.selectedGroup = group.code
    this.dataManager.currentGroup = group.code
    
    if (this.selectedMode === 'campaign') {
      this.currentPage = 1
      this.currentStep = 'level'
    } else {
      this.startGame()
    }
  }
}

/**
 * 选择子分组
 */
HomeScene.prototype.selectSubgroup = function(code) {
  this.selectedSubGroup = code
  this.selectedGroup = code
  this.dataManager.currentGroup = code
  
  if (this.selectedMode === 'campaign') {
    this.currentPage = 1
    this.currentStep = 'level'
  } else {
    this.startGame()
  }
}

/**
 * 开始闯关关卡
 */
HomeScene.prototype.startCampaignLevel = function(level) {
  this.dataManager.currentLevel = level
  this.dataManager.saveGameState()
  this.main.showScene('game', {
    mode: 'campaign',
    group: this.selectedGroup,
    level: level
  })
}

/**
 * 开始游戏（无限/计时模式）
 */
HomeScene.prototype.startGame = function() {
  this.dataManager.saveGameState()
  this.main.showScene('game', {
    mode: this.selectedMode,
    group: this.selectedGroup,
    difficulty: this.selectedDifficulty,
    duration: this.selectedDuration
  })
}

/**
 * 返回上一步
 */
HomeScene.prototype.goBack = function() {
  switch (this.currentStep) {
    case 'level':
      if (this.selectedGroupData && this.selectedGroupData.hasSubGroups) {
        this.currentStep = 'subgroup'
        this.selectedGroup = null
      } else {
        this.currentStep = 'group'
        this.selectedGroup = null
        this.selectedGroupData = null
      }
      break
    case 'subgroup':
      this.currentStep = 'group'
      this.selectedGroupData = null
      break
    case 'group':
      if (this.selectedMode === 'endless' || this.selectedMode === 'timed') {
        this.currentStep = 'difficulty'
      } else {
        this.currentStep = 'mode'
        this.selectedMode = null
      }
      break
    case 'difficulty':
      if (this.selectedMode === 'timed') {
        this.currentStep = 'duration'
      } else {
        this.currentStep = 'mode'
        this.selectedMode = null
      }
      break
    case 'duration':
      this.currentStep = 'mode'
      this.selectedMode = null
      break
  }
}

module.exports = HomeScene
