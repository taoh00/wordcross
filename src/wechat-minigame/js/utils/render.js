/**
 * UI渲染工具类
 * 提供通用的UI组件绘制方法
 */

var config = require('../config')
var COLORS = config.COLORS

/**
 * 绘制圆角矩形
 */
function drawRoundRect(ctx, x, y, width, height, radius, fill, stroke) {
  ctx.beginPath()
  ctx.moveTo(x + radius, y)
  ctx.lineTo(x + width - radius, y)
  ctx.arcTo(x + width, y, x + width, y + radius, radius)
  ctx.lineTo(x + width, y + height - radius)
  ctx.arcTo(x + width, y + height, x + width - radius, y + height, radius)
  ctx.lineTo(x + radius, y + height)
  ctx.arcTo(x, y + height, x, y + height - radius, radius)
  ctx.lineTo(x, y + radius)
  ctx.arcTo(x, y, x + radius, y, radius)
  ctx.closePath()
  
  if (fill) {
    ctx.fillStyle = fill
    ctx.fill()
  }
  if (stroke) {
    ctx.strokeStyle = stroke
    ctx.stroke()
  }
}

/**
 * 绘制带阴影的卡片
 */
function drawCard(ctx, x, y, width, height, options) {
  options = options || {}
  var radius = options.radius || 16
  var bgColor = options.bgColor || COLORS.white
  var borderColor = options.borderColor || COLORS.primaryLight
  var shadowColor = options.shadowColor || COLORS.primary
  var shadowOffset = options.shadowOffset || 4
  var borderWidth = options.borderWidth || 2
  
  // 阴影
  if (shadowOffset > 0) {
    ctx.fillStyle = shadowColor
    drawRoundRect(ctx, x, y + shadowOffset, width, height, radius, shadowColor, null)
  }
  
  // 主体
  ctx.lineWidth = borderWidth
  drawRoundRect(ctx, x, y, width, height, radius, bgColor, borderColor)
}

/**
 * 绘制按钮
 */
function drawButton(ctx, x, y, width, height, text, options) {
  options = options || {}
  var radius = options.radius || 12
  var bgColor = options.bgColor || COLORS.primary
  var textColor = options.textColor || COLORS.white
  var shadowColor = options.shadowColor || COLORS.primaryLight
  var fontSize = options.fontSize || 16
  var icon = options.icon || null
  
  // 阴影
  ctx.fillStyle = shadowColor
  drawRoundRect(ctx, x, y + 4, width, height, radius, shadowColor, null)
  
  // 按钮主体
  drawRoundRect(ctx, x, y, width, height, radius, bgColor, null)
  
  // 文字
  ctx.fillStyle = textColor
  ctx.font = 'bold ' + fontSize + 'px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  
  if (icon) {
    var iconWidth = fontSize + 4
    ctx.fillText(icon, x + width / 2 - 20, y + height / 2)
    ctx.fillText(text, x + width / 2 + 10, y + height / 2)
  } else {
    ctx.fillText(text, x + width / 2, y + height / 2)
  }
  
  // 返回按钮区域（用于点击检测）
  return { x: x, y: y, width: width, height: height }
}

/**
 * 绘制图标按钮
 */
function drawIconButton(ctx, x, y, size, icon, options) {
  options = options || {}
  var bgColor = options.bgColor || COLORS.lemon
  var borderColor = options.borderColor || COLORS.warning
  var shadowColor = options.shadowColor || COLORS.warningDark
  
  // 阴影
  ctx.beginPath()
  ctx.arc(x + size / 2, y + size / 2 + 3, size / 2, 0, Math.PI * 2)
  ctx.fillStyle = shadowColor
  ctx.fill()
  
  // 主体
  ctx.beginPath()
  ctx.arc(x + size / 2, y + size / 2, size / 2, 0, Math.PI * 2)
  ctx.fillStyle = bgColor
  ctx.fill()
  ctx.strokeStyle = borderColor
  ctx.lineWidth = 2
  ctx.stroke()
  
  // 图标
  ctx.fillStyle = COLORS.text
  ctx.font = Math.floor(size * 0.5) + 'px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(icon, x + size / 2, y + size / 2)
  
  return { x: x, y: y, width: size, height: size }
}

/**
 * 绘制标题文字
 */
function drawTitle(ctx, x, y, text, options) {
  options = options || {}
  var fontSize = options.fontSize || 36
  var color = options.color || COLORS.primary
  var align = options.align || 'center'
  
  ctx.fillStyle = color
  ctx.font = 'bold ' + fontSize + 'px sans-serif'
  ctx.textAlign = align
  ctx.textBaseline = 'middle'
  ctx.fillText(text, x, y)
}

/**
 * 绘制副标题
 */
function drawSubtitle(ctx, x, y, text, options) {
  options = options || {}
  var fontSize = options.fontSize || 18
  var color = options.color || COLORS.textLight
  
  ctx.fillStyle = color
  ctx.font = fontSize + 'px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(text, x, y)
}

/**
 * 绘制用户信息栏
 */
function drawUserInfoBar(ctx, x, y, width, height, userInfo) {
  // 绘制卡片背景
  drawCard(ctx, x, y, width, height, {
    radius: 20,
    bgColor: COLORS.white,
    borderColor: COLORS.primaryLight,
    shadowColor: COLORS.primary,
    shadowOffset: 4
  })
  
  var padding = 12
  var iconSize = 32
  
  // 头像
  ctx.font = iconSize + 'px sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'
  ctx.fillText(userInfo.avatar || '😊', x + padding, y + height / 2)
  
  // 昵称
  ctx.fillStyle = COLORS.text
  ctx.font = 'bold 16px sans-serif'
  ctx.fillText(userInfo.nickname || '游客', x + padding + iconSize + 8, y + height / 2)
  
  // 统计信息
  var statsX = x + width - padding
  var statWidth = 60
  
  // 体力
  drawStatBadge(ctx, statsX - statWidth * 3, y + 8, statWidth, height - 16, '⚡', userInfo.energy || 0)
  // 提示道具
  drawStatBadge(ctx, statsX - statWidth * 2 + 4, y + 8, statWidth, height - 16, '💡', userInfo.hintCount || 0)
  // 翻译道具（与网页版首页一致：📖）
  drawStatBadge(ctx, statsX - statWidth + 8, y + 8, statWidth, height - 16, '📖', userInfo.translateCount || 0)
}

/**
 * 绘制统计徽章
 */
function drawStatBadge(ctx, x, y, width, height, icon, value) {
  drawRoundRect(ctx, x, y, width, height, 10, COLORS.lemon, COLORS.lemonDark)
  
  ctx.font = '14px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillStyle = COLORS.text
  ctx.fillText(icon + value, x + width / 2, y + height / 2)
}

/**
 * 绘制进度条
 */
function drawProgressBar(ctx, x, y, width, height, progress, options) {
  options = options || {}
  var bgColor = options.bgColor || COLORS.border
  var fillColor = options.fillColor || COLORS.success
  var radius = options.radius || height / 2
  
  // 背景
  drawRoundRect(ctx, x, y, width, height, radius, bgColor, null)
  
  // 进度
  if (progress > 0) {
    var fillWidth = Math.max(width * (progress / 100), height)
    drawRoundRect(ctx, x, y, fillWidth, height, radius, fillColor, null)
  }
}

/**
 * 绘制模态弹窗背景
 */
function drawModalBackground(ctx, screenWidth, screenHeight) {
  ctx.fillStyle = 'rgba(0, 0, 0, 0.5)'
  ctx.fillRect(0, 0, screenWidth, screenHeight)
}

/**
 * 绘制模态弹窗卡片
 */
function drawModal(ctx, x, y, width, height, options) {
  options = options || {}
  var radius = options.radius || 24
  var borderColor = options.borderColor || COLORS.warning
  
  drawCard(ctx, x, y, width, height, {
    radius: radius,
    bgColor: COLORS.white,
    borderColor: borderColor,
    shadowColor: 'rgba(0,0,0,0.2)',
    shadowOffset: 8,
    borderWidth: 3
  })
}

/**
 * 检查点击是否在区域内
 */
function isPointInRect(point, rect) {
  return point.x >= rect.x && 
         point.x <= rect.x + rect.width &&
         point.y >= rect.y && 
         point.y <= rect.y + rect.height
}

/**
 * 格式化时间
 */
function formatTime(seconds) {
  var mins = Math.floor(seconds / 60)
  var secs = seconds % 60
  return (mins < 10 ? '0' : '') + mins + ':' + (secs < 10 ? '0' : '') + secs
}

/**
 * 绘制波点背景（马卡龙风格）
 */
function drawDotBackground(ctx, screenWidth, screenHeight) {
  // 奶白色底
  ctx.fillStyle = COLORS.background
  ctx.fillRect(0, 0, screenWidth, screenHeight)
  
  // 绘制波点纹理
  var dotSize = 3
  var spacing = 40
  var colors = [COLORS.primaryLight, COLORS.mintLight]
  
  ctx.globalAlpha = 0.3
  for (var x = 0; x < screenWidth; x += spacing) {
    for (var y = 0; y < screenHeight; y += spacing) {
      // 第一层波点（粉色）
      ctx.fillStyle = colors[0]
      ctx.beginPath()
      ctx.arc(x, y, dotSize, 0, Math.PI * 2)
      ctx.fill()
      
      // 第二层波点（绿色，偏移）
      ctx.fillStyle = colors[1]
      ctx.beginPath()
      ctx.arc(x + spacing / 2, y + spacing / 2, dotSize, 0, Math.PI * 2)
      ctx.fill()
    }
  }
  ctx.globalAlpha = 1
}

/**
 * 绘制设置入口卡片
 */
function drawSettingsCard(ctx, x, y, width, height) {
  drawCard(ctx, x, y, width, height, {
    radius: 14,
    bgColor: COLORS.white,
    borderColor: COLORS.primaryLight,
    shadowColor: COLORS.border,
    shadowOffset: 3
  })
  
  ctx.fillStyle = COLORS.text
  ctx.font = 'bold 14px sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'
  ctx.fillText('⚙️ 设置', x + 15, y + height / 2)
  
  ctx.fillStyle = COLORS.textLight
  ctx.textAlign = 'right'
  ctx.fillText('›', x + width - 15, y + height / 2)
  
  return { x: x, y: y, width: width, height: height, action: 'settings' }
}

module.exports = {
  drawRoundRect: drawRoundRect,
  drawCard: drawCard,
  drawButton: drawButton,
  drawIconButton: drawIconButton,
  drawTitle: drawTitle,
  drawSubtitle: drawSubtitle,
  drawUserInfoBar: drawUserInfoBar,
  drawStatBadge: drawStatBadge,
  drawProgressBar: drawProgressBar,
  drawModalBackground: drawModalBackground,
  drawModal: drawModal,
  isPointInRect: isPointInRect,
  formatTime: formatTime,
  drawDotBackground: drawDotBackground,
  drawSettingsCard: drawSettingsCard
}
