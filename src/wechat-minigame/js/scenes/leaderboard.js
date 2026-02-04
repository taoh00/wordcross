/**
 * 排行榜场景
 */

var config = require('../config')
var render = require('../utils/render')

var COLORS = config.COLORS
var VOCAB_GROUPS = config.VOCAB_GROUPS
var API_BASE = config.API_BASE
var LEADERBOARD_TYPES = config.LEADERBOARD_TYPES
var GROUP_CATEGORIES = config.GROUP_CATEGORIES
var FONT_SIZES = config.FONT_SIZES

/**
 * 排行榜场景类
 */
function LeaderboardScene(main) {
  this.main = main
  this.ctx = main.ctx
  this.screenWidth = main.screenWidth
  this.screenHeight = main.screenHeight
  this.dataManager = main.dataManager
  this.audioManager = main.audioManager
  
  this.buttons = []
  
  // 使用配置中的排行榜类型
  this.leaderboardTypes = LEADERBOARD_TYPES
  
  // 词库分类
  this.groupCategories = GROUP_CATEGORIES
  
  // 当前选中的类型、分类和词库
  this.selectedType = 'campaign_level'
  this.selectedCategory = null  // 词库分类：primary/junior/senior/exam
  this.selectedGroup = 'all'    // 默认全部
  
  // 当前Tab: leaderboard / mystats
  this.activeTab = 'leaderboard'
  
  // 排行榜数据
  this.leaderboardData = []
  this.loading = true
  this.myRank = null
  
  // 我的统计数据
  this.myStats = null
  
  // 加载排行榜
  this.loadLeaderboard()
}

/**
 * 加载排行榜数据
 */
LeaderboardScene.prototype.loadLeaderboard = function() {
  var self = this
  this.loading = true
  
  var url = API_BASE + '/api/leaderboard/' + this.selectedType + '?group=' + this.selectedGroup + '&limit=50'
  
  wx.request({
    url: url,
    header: { 'X-User-Id': this.dataManager.userId },
    success: function(res) {
      if (res.statusCode === 200 && res.data) {
        self.leaderboardData = res.data.entries || []
        self.myRank = res.data.my_rank || null
      } else {
        self.leaderboardData = []
      }
      self.loading = false
    },
    fail: function(err) {
      console.error('加载排行榜失败:', err)
      self.leaderboardData = []
      self.loading = false
    }
  })
}

/**
 * 渲染场景
 */
LeaderboardScene.prototype.render = function(ctx) {
  this.buttons = []
  
  // 背景
  ctx.fillStyle = COLORS.background
  ctx.fillRect(0, 0, this.screenWidth, this.screenHeight)
  
  var padding = 15
  var centerX = this.screenWidth / 2
  
  // 返回按钮
  this.buttons.push(render.drawButton(ctx, padding, 40, 70, 36, '← 返回', {
    bgColor: COLORS.white,
    shadowColor: COLORS.border,
    textColor: COLORS.textLight,
    fontSize: 14
  }))
  this.buttons[this.buttons.length - 1].action = 'back'
  
  // 标题
  render.drawTitle(ctx, centerX, 100, '🏆 排行榜', { fontSize: 28, color: COLORS.primary })
  
  // 刷新按钮
  this.buttons.push(render.drawButton(ctx, this.screenWidth - padding - 60, 40, 60, 36, '🔄', {
    bgColor: COLORS.primaryLight,
    shadowColor: COLORS.primary,
    textColor: COLORS.primary,
    fontSize: 18
  }))
  this.buttons[this.buttons.length - 1].action = 'refresh'
  
  // Tab切换（排行榜 / 我的记录）
  var tabWidth = (this.screenWidth - padding * 3) / 2
  var tabY = 125
  
  // 排行榜Tab
  var tab1Active = this.activeTab === 'leaderboard'
  this.buttons.push(render.drawButton(ctx, padding, tabY, tabWidth, 32, '📊 排行榜', {
    bgColor: tab1Active ? COLORS.primary : COLORS.white,
    shadowColor: tab1Active ? COLORS.primaryDark : COLORS.border,
    textColor: tab1Active ? COLORS.white : COLORS.text,
    fontSize: 13
  }))
  this.buttons[this.buttons.length - 1].action = 'tabLeaderboard'
  
  // 我的记录Tab
  var tab2Active = this.activeTab === 'mystats'
  this.buttons.push(render.drawButton(ctx, padding + tabWidth + padding, tabY, tabWidth, 32, '📈 我的记录', {
    bgColor: tab2Active ? COLORS.primary : COLORS.white,
    shadowColor: tab2Active ? COLORS.primaryDark : COLORS.border,
    textColor: tab2Active ? COLORS.white : COLORS.text,
    fontSize: 13
  }))
  this.buttons[this.buttons.length - 1].action = 'tabMystats'
  
  if (this.activeTab === 'leaderboard') {
    // 类型选择标签（6个类型，2行，每行3个）
    var typeY = 165
    this.renderTypeSelector(ctx, padding, typeY)
    
    // 词库选择（类型选择器占80高度：2行 × (32高+8间距) = 80）
    var groupY = typeY + 85
    this.renderGroupSelector(ctx, padding, groupY)
    
    // 排行榜列表（词库选择器占35高度）
    var listY = groupY + 40
    this.renderLeaderboardList(ctx, padding, listY)
    
    // 我的排名
    if (this.myRank) {
      this.renderMyRank(ctx, padding, this.screenHeight - 80)
    }
  } else {
    // 我的记录页
    this.renderMyStats(ctx, padding, 165)
  }
}

/**
 * 渲染类型选择器（5个类型，两行布局）
 */
LeaderboardScene.prototype.renderTypeSelector = function(ctx, x, y) {
  var types = this.leaderboardTypes
  var cols = 3
  var gap = 8
  var btnWidth = (this.screenWidth - x * 2 - gap * (cols - 1)) / cols
  var btnHeight = 32
  var rowGap = 8
  
  for (var i = 0; i < types.length; i++) {
    var type = types[i]
    var row = Math.floor(i / cols)
    var col = i % cols
    var btnX = x + col * (btnWidth + gap)
    var btnY = y + row * (btnHeight + rowGap)
    var isActive = this.selectedType === type.code
    
    var bgColor = isActive ? COLORS.primary : COLORS.white
    var textColor = isActive ? COLORS.white : COLORS.text
    var shadowColor = isActive ? COLORS.primaryLight : COLORS.border
    
    render.drawRoundRect(ctx, btnX, btnY + 2, btnWidth, btnHeight, 8, shadowColor, null)
    render.drawRoundRect(ctx, btnX, btnY, btnWidth, btnHeight, 8, bgColor, null)
    
    ctx.fillStyle = textColor
    ctx.font = 'bold 11px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(type.icon + ' ' + type.name, btnX + btnWidth / 2, btnY + btnHeight / 2)
    
    this.buttons.push({
      x: btnX, y: btnY, width: btnWidth, height: btnHeight,
      action: 'selectType', code: type.code
    })
  }
  
  // 返回选择器高度
  return Math.ceil(types.length / cols) * (btnHeight + rowGap)
}

/**
 * 渲染词库选择器
 */
LeaderboardScene.prototype.renderGroupSelector = function(ctx, x, y) {
  // 分类选择（全部 + 3个分类 = 4个按钮）
  var categories = [{ code: 'all', name: '全部' }].concat(this.groupCategories)
  var cols = 4
  var gap = 8
  var btnWidth = (this.screenWidth - x * 2 - gap * (cols - 1)) / cols
  var btnHeight = 28
  
  for (var i = 0; i < categories.length; i++) {
    var cat = categories[i]
    var btnX = x + i * (btnWidth + gap)
    var isActive = (this.selectedGroup === 'all' && cat.code === 'all') || 
                   this.selectedCategory === cat.code
    
    var bgColor = isActive ? COLORS.primary : COLORS.white
    var textColor = isActive ? COLORS.white : COLORS.text
    
    render.drawRoundRect(ctx, btnX, y, btnWidth, btnHeight, 6, bgColor, COLORS.borderNeutral)
    
    ctx.fillStyle = textColor
    ctx.font = 'bold 11px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(cat.name, btnX + btnWidth / 2, y + btnHeight / 2)
    
    this.buttons.push({
      x: btnX, y: y, width: btnWidth, height: btnHeight,
      action: 'selectCategory', code: cat.code
    })
  }
}

/**
 * 根据分类获取子词库列表
 */
LeaderboardScene.prototype.getSubGroupsByCategory = function(category) {
  if (category === 'primary') {
    return [
      { code: 'grade3_1', name: '三上' }, { code: 'grade3_2', name: '三下' },
      { code: 'grade4_1', name: '四上' }, { code: 'grade4_2', name: '四下' },
      { code: 'grade5_1', name: '五上' }, { code: 'grade5_2', name: '五下' },
      { code: 'grade6_1', name: '六上' }, { code: 'grade6_2', name: '六下' }
    ]
  } else if (category === 'secondary') {
    // 初高中合并
    return [
      { code: 'junior7_1', name: '七上' }, { code: 'junior7_2', name: '七下' },
      { code: 'junior8_1', name: '八上' }, { code: 'junior8_2', name: '八下' },
      { code: 'junior9', name: '九年级' },
      { code: 'senior1', name: '必修1' }, { code: 'senior2', name: '必修2' },
      { code: 'senior3', name: '必修3' }, { code: 'senior4', name: '必修4' },
      { code: 'senior5', name: '必修5' }
    ]
  } else if (category === 'exam') {
    return [
      { code: 'ket', name: 'KET' }, { code: 'pet', name: 'PET' },
      { code: 'cet4', name: '四级' }, { code: 'cet6', name: '六级' },
      { code: 'postgrad', name: '考研' }, { code: 'ielts', name: '雅思' },
      { code: 'toefl', name: '托福' }, { code: 'gre', name: 'GRE' }
    ]
  }
  return []
}

/**
 * 渲染排行榜列表
 */
LeaderboardScene.prototype.renderLeaderboardList = function(ctx, x, y) {
  var listHeight = this.screenHeight - y - 100
  var itemHeight = 50
  
  // 列表背景
  render.drawCard(ctx, x, y, this.screenWidth - x * 2, listHeight, {
    radius: 16,
    bgColor: COLORS.white,
    borderColor: COLORS.primaryLight,
    shadowColor: COLORS.primary,
    shadowOffset: 3
  })
  
  if (this.loading) {
    ctx.fillStyle = COLORS.textLight
    ctx.font = '14px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText('加载中...', this.screenWidth / 2, y + listHeight / 2)
    return
  }
  
  if (this.leaderboardData.length === 0) {
    ctx.fillStyle = COLORS.textLight
    ctx.font = '14px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText('暂无数据', this.screenWidth / 2, y + listHeight / 2)
    return
  }
  
  // 渲染列表项
  var visibleCount = Math.floor((listHeight - 20) / itemHeight)
  
  for (var i = 0; i < Math.min(visibleCount, this.leaderboardData.length); i++) {
    var entry = this.leaderboardData[i]
    var itemY = y + 10 + i * itemHeight
    this.renderLeaderboardItem(ctx, x + 10, itemY, this.screenWidth - x * 2 - 20, itemHeight - 5, entry, i + 1)
  }
}

/**
 * 渲染排行榜项
 */
LeaderboardScene.prototype.renderLeaderboardItem = function(ctx, x, y, width, height, entry, rank) {
  var isMe = entry.user_id === this.dataManager.userId
  
  // 背景
  var bgColor = isMe ? '#E0FBE0' : COLORS.white
  render.drawRoundRect(ctx, x, y, width, height, 10, bgColor, isMe ? '#3CB371' : '#F0F0F0')
  
  // 排名
  var rankText = rank.toString()
  var rankBg = COLORS.borderNeutral
  var rankColor = COLORS.text
  
  if (rank === 1) {
    rankBg = '#ffd700'
    rankColor = '#92400e'
    rankText = '🥇'
  } else if (rank === 2) {
    rankBg = '#c0c0c0'
    rankColor = '#374151'
    rankText = '🥈'
  } else if (rank === 3) {
    rankBg = '#cd7f32'
    rankColor = COLORS.white
    rankText = '🥉'
  }
  
  if (rank <= 3) {
    ctx.font = '20px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(rankText, x + 22, y + height / 2)
  } else {
    ctx.beginPath()
    ctx.arc(x + 22, y + height / 2, 14, 0, Math.PI * 2)
    ctx.fillStyle = rankBg
    ctx.fill()
    
    ctx.fillStyle = rankColor
    ctx.font = 'bold 12px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(rankText, x + 22, y + height / 2)
  }
  
  // 头像
  ctx.font = '24px sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText(entry.avatar || '😊', x + 45, y + height / 2)
  
  // 昵称
  ctx.fillStyle = COLORS.text
  ctx.font = 'bold 13px sans-serif'
  var nickname = entry.nickname || '游客'
  if (nickname.length > 6) nickname = nickname.substr(0, 6) + '...'
  ctx.fillText(nickname, x + 75, y + height / 2)
  
  // 分数/值
  ctx.fillStyle = COLORS.primary
  ctx.font = 'bold 16px sans-serif'
  ctx.textAlign = 'right'
  
  var valueText = ''
  if (this.selectedType === 'campaign_level') {
    valueText = 'L' + entry.value
  } else if (this.selectedType === 'endless_level') {
    valueText = entry.value + '关'
  } else {
    valueText = entry.value + '词'
  }
  
  ctx.fillText(valueText, x + width - 10, y + height / 2)
}

/**
 * 渲染我的排名
 */
LeaderboardScene.prototype.renderMyRank = function(ctx, x, y) {
  var width = this.screenWidth - x * 2
  
  render.drawCard(ctx, x, y, width, 60, {
    radius: 14,
    bgColor: '#E0FBE0',
    borderColor: '#3CB371',
    shadowColor: '#2E8B57',
    shadowOffset: 3
  })
  
  // 我的排名标签
  ctx.fillStyle = '#065f46'
  ctx.font = 'bold 14px sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'
  ctx.fillText('我的排名', x + 15, y + 30)
  
  // 排名值
  ctx.fillStyle = COLORS.primary
  ctx.font = 'bold 20px sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('#' + this.myRank.rank, x + width / 2, y + 30)
  
  // 分数
  ctx.textAlign = 'right'
  ctx.fillText(this.myRank.value, x + width - 15, y + 30)
}

/**
 * 触摸结束事件
 */
LeaderboardScene.prototype.onTouchEnd = function(e) {
  var touch = e.changedTouches[0]
  var x = touch.clientX
  var y = touch.clientY
  
  for (var i = 0; i < this.buttons.length; i++) {
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
LeaderboardScene.prototype.handleButtonClick = function(btn) {
  this.audioManager.playClickSound()
  
  switch (btn.action) {
    case 'back':
      this.main.showScene('home')
      break
    case 'selectType':
      if (this.selectedType !== btn.code) {
        this.selectedType = btn.code
        this.loadLeaderboard()
      }
      break
    case 'selectCategory':
      if (btn.code === 'all') {
        this.selectedCategory = null
        this.selectedGroup = 'all'
      } else {
        this.selectedCategory = btn.code
        // 选择该分类的第一个词库
        var subs = this.getSubGroupsByCategory(btn.code)
        if (subs.length > 0) {
          this.selectedGroup = subs[0].code
        }
      }
      this.loadLeaderboard()
      break
    case 'selectGroup':
      if (this.selectedGroup !== btn.code) {
        this.selectedGroup = btn.code
        this.loadLeaderboard()
      }
      break
    case 'refresh':
      this.loadLeaderboard()
      wx.showToast({ title: '刷新中...', icon: 'none', duration: 1000 })
      break
    case 'tabLeaderboard':
      this.activeTab = 'leaderboard'
      break
    case 'tabMystats':
      this.activeTab = 'mystats'
      this.loadMyStats()
      break
  }
}

/**
 * 加载我的统计数据
 */
LeaderboardScene.prototype.loadMyStats = function() {
  var self = this
  
  // 获取用户统计
  wx.request({
    url: API_BASE + '/api/user/stats',
    method: 'GET',
    header: { 'X-User-Id': this.dataManager.userId },
    success: function(res) {
      if (res.data) {
        self.myStats = res.data
      }
    }
  })
}

/**
 * 渲染我的记录页
 */
LeaderboardScene.prototype.renderMyStats = function(ctx, x, y) {
  var cardWidth = this.screenWidth - x * 2
  var centerX = this.screenWidth / 2
  
  // 我的统计卡片
  ctx.fillStyle = COLORS.text
  ctx.font = 'bold 14px sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('📊 我的统计', x + 5, y)
  y += 25
  
  render.drawCard(ctx, x, y, cardWidth, 100, {
    radius: 12,
    bgColor: COLORS.white,
    borderColor: COLORS.primaryLight,
    shadowColor: COLORS.primary,
    shadowOffset: 3
  })
  
  // 统计数据
  var stats = this.myStats || {}
  var statItems = [
    { label: '闯关进度', value: (stats.campaign_level || 1) + '关' },
    { label: '总积分', value: stats.total_score || 0 },
    { label: '完成单词', value: stats.words_completed || 0 },
    { label: '游戏次数', value: stats.games_played || 0 }
  ]
  
  var statWidth = (cardWidth - 20) / 4
  ctx.font = '11px sans-serif'
  ctx.textAlign = 'center'
  
  for (var i = 0; i < statItems.length; i++) {
    var statX = x + 10 + statWidth * i + statWidth / 2
    
    ctx.fillStyle = COLORS.textLight
    ctx.fillText(statItems[i].label, statX, y + 30)
    
    ctx.fillStyle = COLORS.primary
    ctx.font = 'bold 18px sans-serif'
    ctx.fillText(statItems[i].value, statX, y + 55)
    ctx.font = '11px sans-serif'
  }
  
  y += 120
  
  // 我的各类排名
  ctx.fillStyle = COLORS.text
  ctx.font = 'bold 14px sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('🏅 我的排名', x + 5, y)
  y += 25
  
  render.drawCard(ctx, x, y, cardWidth, 180, {
    radius: 12,
    bgColor: COLORS.white,
    borderColor: COLORS.mintLight,
    shadowColor: COLORS.mintDark,
    shadowOffset: 3
  })
  
  // 各类型排名（简化显示）
  var rankItems = this.leaderboardTypes.slice(0, 5)
  var itemHeight = 32
  ctx.font = '12px sans-serif'
  
  for (var j = 0; j < rankItems.length; j++) {
    var itemY = y + 15 + j * itemHeight
    
    ctx.fillStyle = COLORS.text
    ctx.textAlign = 'left'
    ctx.fillText(rankItems[j].icon + ' ' + rankItems[j].name, x + 15, itemY + 16)
    
    ctx.fillStyle = COLORS.primary
    ctx.textAlign = 'right'
    ctx.font = 'bold 14px sans-serif'
    ctx.fillText('暂无', x + cardWidth - 15, itemY + 16)
    ctx.font = '12px sans-serif'
  }
}

module.exports = LeaderboardScene
