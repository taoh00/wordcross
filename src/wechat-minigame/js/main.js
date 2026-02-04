/**
 * 我爱填单词 - 小游戏主模块
 * 管理场景切换、渲染循环、事件分发
 */

var DataManager = require('./managers/data')
var AudioManager = require('./managers/audio')
var HomeScene = require('./scenes/home')
var GameScene = require('./scenes/game')
var SettingsScene = require('./scenes/settings')
var LeaderboardScene = require('./scenes/leaderboard')
var config = require('./config')

/**
 * 主应用类
 */
function Main() {
  // 获取屏幕尺寸
  var systemInfo = wx.getSystemInfoSync()
  this.screenWidth = systemInfo.windowWidth
  this.screenHeight = systemInfo.windowHeight
  
  // 创建主画布（第一个 createCanvas 是主屏幕画布）
  this.canvas = wx.createCanvas()
  this.ctx = this.canvas.getContext('2d')
  
  // 设置画布尺寸
  this.canvas.width = this.screenWidth
  this.canvas.height = this.screenHeight
  
  console.log('[Main] 画布初始化:', this.screenWidth, 'x', this.screenHeight)
  
  // 初始化管理器
  this.dataManager = new DataManager()
  this.dataManager.init()
  
  this.audioManager = new AudioManager()
  this.audioManager.init(this.dataManager.settings)
  
  // 当前场景
  this.currentScene = null
  this.scenes = {}
  
  // 初始化场景
  this.initScenes()
  
  // 绑定事件
  this.bindEvents()
  
  // 显示首页
  this.showScene('home')
  
  // 开始渲染循环
  this.startLoop()
  
  console.log('游戏启动完成')
}

/**
 * 初始化所有场景
 */
Main.prototype.initScenes = function() {
  console.log('初始化场景...')
  this.scenes.home = new HomeScene(this)
  this.scenes.game = new GameScene(this)
  this.scenes.settings = new SettingsScene(this)
  this.scenes.leaderboard = new LeaderboardScene(this)
  console.log('场景初始化完成')
}

/**
 * 切换场景
 */
Main.prototype.showScene = function(sceneName, params) {
  console.log('切换场景:', sceneName)
  
  // 销毁当前场景
  if (this.currentScene && typeof this.currentScene.destroy === 'function') {
    this.currentScene.destroy()
  }
  
  // 切换场景
  var scene = this.scenes[sceneName]
  if (!scene) {
    console.error('场景不存在:', sceneName)
    return
  }
  
  this.currentScene = scene
  
  // 初始化场景
  if (typeof scene.init === 'function') {
    scene.init(params)
  }
}

/**
 * 绑定事件
 */
Main.prototype.bindEvents = function() {
  var self = this
  
  // 触摸结束事件
  wx.onTouchEnd(function(e) {
    if (self.currentScene && typeof self.currentScene.onTouchEnd === 'function') {
      self.currentScene.onTouchEnd(e)
    }
  })
  
  // 触摸移动事件（用于滚动等）
  wx.onTouchMove(function(e) {
    if (self.currentScene && typeof self.currentScene.onTouchMove === 'function') {
      self.currentScene.onTouchMove(e)
    }
  })
  
  // 触摸开始事件
  wx.onTouchStart(function(e) {
    if (self.currentScene && typeof self.currentScene.onTouchStart === 'function') {
      self.currentScene.onTouchStart(e)
    }
  })
}

/**
 * 开始渲染循环
 */
Main.prototype.startLoop = function() {
  var self = this
  
  function loop() {
    self.render()
    requestAnimationFrame(loop)
  }
  
  loop()
}

/**
 * 渲染
 */
Main.prototype.render = function() {
  // 清空画布（使用背景色填充）
  this.ctx.fillStyle = '#FFFAF0'
  this.ctx.fillRect(0, 0, this.screenWidth, this.screenHeight)
  
  // 渲染当前场景
  if (this.currentScene && typeof this.currentScene.render === 'function') {
    try {
      this.currentScene.render(this.ctx)
    } catch (e) {
      console.error('[Main] 渲染错误:', e)
      // 显示错误信息
      this.ctx.fillStyle = '#FF0000'
      this.ctx.font = '14px sans-serif'
      this.ctx.textAlign = 'center'
      this.ctx.fillText('渲染错误: ' + e.message, this.screenWidth / 2, this.screenHeight / 2)
    }
  }
}

// 导出并启动
module.exports = Main
