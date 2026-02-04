/**
 * 设置场景
 */

var config = require('../config')
var render = require('../utils/render')

var COLORS = config.COLORS
var AVATAR_OPTIONS = config.AVATAR_OPTIONS
var DEV_CONFIG = config.DEV_CONFIG

/**
 * 设置场景类
 */
function SettingsScene(main) {
  this.main = main
  this.ctx = main.ctx
  this.screenWidth = main.screenWidth
  this.screenHeight = main.screenHeight
  this.dataManager = main.dataManager
  this.audioManager = main.audioManager
  
  this.buttons = []
  
  // 头像选项
  this.avatarOptions = AVATAR_OPTIONS
  
  // 开发模式状态
  this.versionClickCount = 0
  this.versionClickTimer = null
  this.showDevOptions = false
  
  // 设置项（与网页版一致）
  this.settingItems = [
    { key: 'autoSpeak', name: '自动发音', desc: '填对单词后自动播放发音', icon: '🔊', section: 'voice' },
    { key: 'voiceType', name: '发音类型', desc: '选择美式或英式发音', icon: '🎤', type: 'select', section: 'voice' },
    { key: 'testSpeak', name: '测试发音', desc: '点击播放 "Hello"', icon: '🔊', type: 'button', section: 'voice' },
    { key: 'showTranslation', name: '显示翻译', desc: '在单词列表中显示中文翻译', icon: '📝', section: 'translate' },
    { key: 'bgMusic', name: '背景音乐', desc: '游戏时播放轻松的背景音乐', icon: '🎵', section: 'audio' },
    { key: 'soundEffect', name: '游戏音效', desc: '按键、正确、通关等音效', icon: '🔔', section: 'audio' },
    { key: 'vibration', name: '震动反馈', desc: '移动端按键震动反馈', icon: '📳', section: 'audio' }
  ]
}

/**
 * 渲染场景
 */
SettingsScene.prototype.render = function(ctx) {
  this.buttons = []
  
  // 背景
  ctx.fillStyle = COLORS.background
  ctx.fillRect(0, 0, this.screenWidth, this.screenHeight)
  
  var padding = 20
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
  render.drawTitle(ctx, centerX, 100, '⚙️ 设置', { fontSize: 28, color: COLORS.primary })
  
  // 分组渲染设置项
  var currentY = 140
  var sections = [
    { key: 'voice', title: '🔊 发音设置' },
    { key: 'translate', title: '📝 翻译设置' },
    { key: 'audio', title: '🎵 音效设置' }
  ]
  
  for (var s = 0; s < sections.length; s++) {
    var section = sections[s]
    var sectionItems = this.settingItems.filter(function(item) {
      return item.section === section.key
    })
    
    if (sectionItems.length === 0) continue
    
    // 分组标题
    ctx.fillStyle = COLORS.text
    ctx.font = 'bold 14px sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText(section.title, padding + 5, currentY)
    currentY += 25
    
    // 分组卡片
    var cardHeight = sectionItems.length * 60 + 15
    render.drawCard(ctx, padding, currentY, this.screenWidth - padding * 2, cardHeight, {
      radius: 16,
      bgColor: COLORS.white,
      borderColor: COLORS.primaryLight,
      shadowColor: COLORS.primary,
      shadowOffset: 3
    })
    
    // 分组内设置项
    var itemY = currentY + 10
    for (var i = 0; i < sectionItems.length; i++) {
      var item = sectionItems[i]
      this.renderSettingItem(ctx, padding + 12, itemY, 
        this.screenWidth - padding * 2 - 24, 50, item)
      itemY += 60
    }
    
    currentY += cardHeight + 15
  }
  
  // 用户信息分组标题
  ctx.fillStyle = COLORS.text
  ctx.font = 'bold 14px sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('👤 用户信息', padding + 5, currentY)
  currentY += 25
  
  // 用户信息卡片
  this.renderUserCard(ctx, padding, currentY, this.screenWidth - padding * 2, 80)
  
  // 头像选择网格
  var avatarY = currentY + 95
  this.renderAvatarGrid(ctx, padding, avatarY, this.screenWidth - padding * 2)
  
  // 重置按钮
  var resetY = avatarY + 70
  this.buttons.push(render.drawButton(ctx, padding, resetY, this.screenWidth - padding * 2, 50, '🔄 重置全部数据', {
    bgColor: COLORS.errorLight,
    shadowColor: COLORS.error,
    textColor: '#7f1d1d',
    fontSize: 15
  }))
  this.buttons[this.buttons.length - 1].action = 'reset'
  
  // 关于信息分组
  var aboutY = resetY + 70
  ctx.fillStyle = COLORS.text
  ctx.font = 'bold 14px sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('ℹ️ 关于', padding + 5, aboutY)
  
  render.drawCard(ctx, padding, aboutY + 20, this.screenWidth - padding * 2, 60, {
    radius: 12,
    bgColor: COLORS.white,
    borderColor: COLORS.borderNeutral,
    shadowColor: COLORS.borderNeutral,
    shadowOffset: 2
  })
  
  ctx.fillStyle = COLORS.textLight
  ctx.font = '12px sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('版本 v1.0.0', padding + 15, aboutY + 45)
  ctx.fillText('词库 31个 | 关卡 8954+', padding + 15, aboutY + 62)
  
  // 版本号点击区域（用于开发模式后门）
  this.versionRect = {
    x: padding, y: aboutY + 20,
    width: this.screenWidth - padding * 2, height: 60
  }
}

/**
 * 渲染设置项
 */
SettingsScene.prototype.renderSettingItem = function(ctx, x, y, width, height, item) {
  var settings = this.dataManager.settings
  var value = settings[item.key]
  
  // 图标
  ctx.font = '24px sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'
  ctx.fillText(item.icon, x, y + height / 2)
  
  // 名称
  ctx.fillStyle = COLORS.text
  ctx.font = 'bold 15px sans-serif'
  ctx.fillText(item.name, x + 40, y + height / 2 - 8)
  
  // 描述
  ctx.fillStyle = COLORS.textLight
  ctx.font = '11px sans-serif'
  ctx.fillText(item.desc, x + 40, y + height / 2 + 12)
  
  // 控件
  var controlX = x + width - 60
  
  if (item.type === 'select') {
    // 选择器（发音类型 - 使用国旗图标）
    var isUS = value === 'us'
    
    // US按钮 🇺🇸
    var usBg = isUS ? COLORS.primary : COLORS.white
    var usColor = isUS ? COLORS.white : COLORS.text
    render.drawRoundRect(ctx, controlX - 35, y + height / 2 - 14, 50, 28, 6, usBg, COLORS.border)
    ctx.fillStyle = usColor
    ctx.font = '12px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('🇺🇸美音', controlX - 10, y + height / 2)
    this.buttons.push({ x: controlX - 35, y: y + height / 2 - 14, width: 50, height: 28, action: 'voiceUS' })
    
    // UK按钮 🇬🇧
    var ukBg = !isUS ? COLORS.primary : COLORS.white
    var ukColor = !isUS ? COLORS.white : COLORS.text
    render.drawRoundRect(ctx, controlX + 20, y + height / 2 - 14, 50, 28, 6, ukBg, COLORS.border)
    ctx.fillStyle = ukColor
    ctx.fillText('🇬🇧英音', controlX + 45, y + height / 2)
    this.buttons.push({ x: controlX + 20, y: y + height / 2 - 14, width: 50, height: 28, action: 'voiceUK' })
  } else if (item.type === 'button') {
    // 按钮类型（测试发音）
    this.buttons.push(render.drawButton(ctx, controlX - 20, y + height / 2 - 14, 90, 28, '🔊 测试 Hello', {
      bgColor: COLORS.skyBlueLight,
      shadowColor: COLORS.skyBlue,
      textColor: COLORS.skyBlueDark,
      fontSize: 11
    }))
    this.buttons[this.buttons.length - 1].action = 'testSpeak'
  } else {
    // 开关
    var switchWidth = 50
    var switchHeight = 28
    var switchX = controlX + 10
    var switchY = y + height / 2 - switchHeight / 2
    
    var switchBg = value ? COLORS.success : COLORS.borderNeutral
    render.drawRoundRect(ctx, switchX, switchY, switchWidth, switchHeight, switchHeight / 2, switchBg, null)
    
    // 滑块
    var knobX = value ? switchX + switchWidth - switchHeight + 2 : switchX + 2
    ctx.beginPath()
    ctx.arc(knobX + (switchHeight - 4) / 2, switchY + switchHeight / 2, (switchHeight - 6) / 2, 0, Math.PI * 2)
    ctx.fillStyle = COLORS.white
    ctx.fill()
    ctx.strokeStyle = value ? '#059669' : COLORS.borderNeutralDark
    ctx.lineWidth = 2
    ctx.stroke()
    
    this.buttons.push({ 
      x: switchX, y: switchY, width: switchWidth, height: switchHeight, 
      action: 'toggle', key: item.key 
    })
  }
  
  // 分割线
  if (this.settingItems.indexOf(item) < this.settingItems.length - 1) {
    ctx.strokeStyle = COLORS.borderNeutral
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(x + 40, y + height)
    ctx.lineTo(x + width - 10, y + height)
    ctx.stroke()
  }
}

/**
 * 渲染头像选择网格
 */
SettingsScene.prototype.renderAvatarGrid = function(ctx, x, y, width) {
  var currentAvatar = this.dataManager.getUserSummary().avatar
  var cols = 6
  var gap = 8
  var btnSize = (width - gap * (cols - 1)) / cols
  
  // 标题
  ctx.fillStyle = COLORS.text
  ctx.font = 'bold 12px sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('选择头像', x, y)
  
  var gridY = y + 20
  
  for (var i = 0; i < this.avatarOptions.length; i++) {
    var avatar = this.avatarOptions[i]
    var row = Math.floor(i / cols)
    var col = i % cols
    var btnX = x + col * (btnSize + gap)
    var btnY = gridY + row * (btnSize + gap)
    
    var isActive = currentAvatar === avatar
    var bgColor = isActive ? COLORS.primaryBg : COLORS.white
    var borderColor = isActive ? COLORS.primary : COLORS.borderNeutral
    
    render.drawRoundRect(ctx, btnX, btnY, btnSize, btnSize, 8, bgColor, borderColor)
    ctx.lineWidth = isActive ? 2 : 1
    
    ctx.font = '24px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(avatar, btnX + btnSize / 2, btnY + btnSize / 2)
    
    this.buttons.push({
      x: btnX, y: btnY, width: btnSize, height: btnSize,
      action: 'selectAvatar', avatar: avatar
    })
  }
}

/**
 * 渲染用户信息卡片
 */
SettingsScene.prototype.renderUserCard = function(ctx, x, y, width, height) {
  render.drawCard(ctx, x, y, width, height, {
    radius: 16,
    bgColor: COLORS.white,
    borderColor: COLORS.primaryLight,
    shadowColor: COLORS.primary,
    shadowOffset: 3
  })
  
  var userInfo = this.dataManager.getUserSummary()
  
  // 头像
  ctx.font = '40px sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'
  ctx.fillText(userInfo.avatar, x + 20, y + height / 2)
  
  // 昵称
  ctx.fillStyle = COLORS.text
  ctx.font = 'bold 18px sans-serif'
  ctx.fillText(userInfo.nickname, x + 75, y + height / 2 - 10)
  
  // ID
  ctx.fillStyle = COLORS.textLight
  ctx.font = '11px sans-serif'
  var shortId = userInfo.userId.length > 20 ? userInfo.userId.substr(0, 20) + '...' : userInfo.userId
  ctx.fillText('ID: ' + shortId, x + 75, y + height / 2 + 14)
  
  // 编辑按钮
  this.buttons.push(render.drawButton(ctx, x + width - 80, y + height / 2 - 16, 60, 32, '编辑', {
    bgColor: COLORS.primaryBg,
    shadowColor: COLORS.primaryLight,
    textColor: COLORS.primary,
    fontSize: 13
  }))
  this.buttons[this.buttons.length - 1].action = 'editProfile'
}

/**
 * 触摸结束事件
 */
SettingsScene.prototype.onTouchEnd = function(e) {
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
SettingsScene.prototype.handleButtonClick = function(btn) {
  this.audioManager.playClickSound()
  
  switch (btn.action) {
    case 'back':
      this.main.showScene('home')
      break
    case 'toggle':
      var currentValue = this.dataManager.settings[btn.key]
      this.dataManager.updateSetting(btn.key, !currentValue)
      
      // 同步音频管理器
      if (btn.key === 'bgMusic' || btn.key === 'soundEffect' || btn.key === 'autoSpeak') {
        this.audioManager.updateSettings(this.dataManager.settings)
      }
      break
    case 'voiceUS':
      this.dataManager.updateSetting('voiceType', 'us')
      this.audioManager.updateSettings({ voiceType: 'us' })
      break
    case 'voiceUK':
      this.dataManager.updateSetting('voiceType', 'uk')
      this.audioManager.updateSettings({ voiceType: 'uk' })
      break
    case 'testSpeak':
      // 测试发音 "Hello"
      this.audioManager.playWordAudio('hello', this.dataManager.settings.voiceType)
      break
    case 'selectAvatar':
      // 选择头像
      if (btn.avatar) {
        this.dataManager.saveUserInfo(null, btn.avatar)
      }
      break
    case 'editProfile':
      this.showEditProfileDialog()
      break
    case 'reset':
      this.showResetConfirmDialog()
      break
  }
}

/**
 * 显示编辑资料对话框
 */
SettingsScene.prototype.showEditProfileDialog = function() {
  var self = this
  
  wx.showModal({
    title: '修改昵称',
    editable: true,
    placeholderText: '请输入新昵称',
    success: function(res) {
      if (res.confirm && res.content) {
        self.dataManager.saveUserInfo(res.content, null)
      }
    }
  })
}

/**
 * 显示重置确认对话框
 */
SettingsScene.prototype.showResetConfirmDialog = function() {
  var self = this
  
  wx.showModal({
    title: '确认重置',
    content: '将清除所有进度和数据，此操作不可恢复！',
    confirmText: '重置',
    confirmColor: '#ef4444',
    success: function(res) {
      if (res.confirm) {
        self.resetAllData()
      }
    }
  })
}

/**
 * 重置所有数据
 */
SettingsScene.prototype.resetAllData = function() {
  // 清除所有本地存储
  try {
    wx.clearStorageSync()
    
    // 重新初始化数据管理器
    this.dataManager.init()
    
    wx.showToast({ title: '重置成功', icon: 'success' })
  } catch (e) {
    console.error('重置失败:', e)
    wx.showToast({ title: '重置失败', icon: 'none' })
  }
}

module.exports = SettingsScene
