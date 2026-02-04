/**
 * 微信小游戏适配器
 * 模拟浏览器环境，使 Canvas API 能正常工作
 */

// 获取系统信息
var systemInfo = wx.getSystemInfoSync()

// Canvas 适配
var sharedCanvas = wx.createCanvas()
sharedCanvas.width = systemInfo.windowWidth
sharedCanvas.height = systemInfo.windowHeight

// 导出全局 canvas（使用安全的方式）
if (typeof GameGlobal !== 'undefined') {
  GameGlobal.canvas = sharedCanvas
  GameGlobal.screenWidth = systemInfo.windowWidth
  GameGlobal.screenHeight = systemInfo.windowHeight
}

// 注意：不要尝试覆盖 window 对象，微信小游戏已内置且只读
// 如果需要扩展 window，使用 Object.assign 或逐个属性添加

// 模拟 Image 类（如果不存在）
if (typeof GameGlobal !== 'undefined' && typeof GameGlobal.Image === 'undefined') {
  GameGlobal.Image = function() {
    return wx.createImage()
  }
}

// 模拟 Audio 类（如果不存在）
if (typeof GameGlobal !== 'undefined' && typeof GameGlobal.Audio === 'undefined') {
  GameGlobal.Audio = function() {
    return wx.createInnerAudioContext()
  }
}

// 确保 requestAnimationFrame 可用
if (typeof requestAnimationFrame === 'undefined') {
  var requestAnimationFrame = function(callback) {
    return setTimeout(callback, 16)
  }
}

if (typeof cancelAnimationFrame === 'undefined') {
  var cancelAnimationFrame = function(id) {
    clearTimeout(id)
  }
}

module.exports = sharedCanvas
