/**
 * 音频管理器
 * 管理背景音乐、音效和单词发音
 */

var config = require('../config')
var API_BASE = config.API_BASE

/**
 * 音频管理器类
 */
function AudioManager() {
  // 音频开关（从设置读取）
  this.bgMusicEnabled = true
  this.soundEffectEnabled = true
  this.voiceType = 'us'  // 'us' 或 'uk'
  
  // 背景音乐实例
  this.bgMusic = null
  
  // 当前播放的单词音频
  this.currentWordAudio = null
}

/**
 * 初始化音频管理器
 */
AudioManager.prototype.init = function(settings) {
  if (settings) {
    this.bgMusicEnabled = settings.bgMusic !== false
    this.soundEffectEnabled = settings.soundEffect !== false
    this.voiceType = settings.voiceType || 'us'
  }
}

/**
 * 更新设置
 */
AudioManager.prototype.updateSettings = function(settings) {
  if (settings.bgMusic !== undefined) {
    this.bgMusicEnabled = settings.bgMusic
    if (!this.bgMusicEnabled) {
      this.stopBgMusic()
    }
  }
  if (settings.soundEffect !== undefined) {
    this.soundEffectEnabled = settings.soundEffect
  }
  if (settings.voiceType !== undefined) {
    this.voiceType = settings.voiceType
  }
}

/**
 * 播放背景音乐
 */
AudioManager.prototype.playBgMusic = function() {
  if (!this.bgMusicEnabled) return
  
  // 停止现有音乐
  this.stopBgMusic()
  
  // 创建新的背景音乐实例
  this.bgMusic = wx.createInnerAudioContext()
  this.bgMusic.src = API_BASE + '/audio/bgm/game.mp3'
  this.bgMusic.loop = true
  this.bgMusic.volume = 0.3
  
  this.bgMusic.onCanplay(function() {
    this.bgMusic.play()
  }.bind(this))
  
  this.bgMusic.onError(function(err) {
    console.warn('背景音乐播放失败:', err)
  })
}

/**
 * 停止背景音乐
 */
AudioManager.prototype.stopBgMusic = function() {
  if (this.bgMusic) {
    this.bgMusic.stop()
    this.bgMusic.destroy()
    this.bgMusic = null
  }
}

/**
 * 暂停背景音乐
 */
AudioManager.prototype.pauseBgMusic = function() {
  if (this.bgMusic) {
    this.bgMusic.pause()
  }
}

/**
 * 恢复背景音乐
 */
AudioManager.prototype.resumeBgMusic = function() {
  if (this.bgMusic && this.bgMusicEnabled) {
    this.bgMusic.play()
  }
}

/**
 * 播放按键音效
 */
AudioManager.prototype.playTypeSound = function() {
  if (!this.soundEffectEnabled) return
  this.playSound('/audio/sfx/type.mp3')
}

/**
 * 播放删除音效
 */
AudioManager.prototype.playDeleteSound = function() {
  if (!this.soundEffectEnabled) return
  this.playSound('/audio/sfx/delete.mp3')
}

/**
 * 播放正确音效
 */
AudioManager.prototype.playCorrectSound = function() {
  if (!this.soundEffectEnabled) return
  this.playSound('/audio/sfx/correct.mp3')
}

/**
 * 播放错误音效
 */
AudioManager.prototype.playWrongSound = function() {
  if (!this.soundEffectEnabled) return
  this.playSound('/audio/sfx/wrong.mp3')
}

/**
 * 播放通关音效
 */
AudioManager.prototype.playLevelCompleteSound = function() {
  if (!this.soundEffectEnabled) return
  this.playSound('/audio/sfx/level_complete.mp3')
}

/**
 * 播放点击音效
 */
AudioManager.prototype.playClickSound = function() {
  if (!this.soundEffectEnabled) return
  this.playSound('/audio/sfx/click.mp3')
}

/**
 * 播放音效（内部方法）
 */
AudioManager.prototype.playSound = function(path) {
  var audio = wx.createInnerAudioContext()
  audio.src = API_BASE + path
  audio.volume = 0.7
  
  audio.onCanplay(function() {
    audio.play()
  })
  
  audio.onEnded(function() {
    audio.destroy()
  })
  
  audio.onError(function(err) {
    console.warn('音效播放失败:', path, err)
    audio.destroy()
  })
}

/**
 * 播放单词发音
 */
AudioManager.prototype.playWordAudio = function(word, voiceType) {
  var self = this
  var type = voiceType || this.voiceType
  var wordLower = word.toLowerCase().trim()
  
  if (!wordLower) return
  
  // 停止当前播放的单词
  this.stopWordAudio()
  
  // 创建音频实例
  this.currentWordAudio = wx.createInnerAudioContext()
  this.currentWordAudio.src = API_BASE + '/data/audio/' + type + '/' + wordLower + '.mp3'
  this.currentWordAudio.volume = 1.0
  
  this.currentWordAudio.onCanplay(function() {
    self.currentWordAudio.play()
  })
  
  this.currentWordAudio.onEnded(function() {
    self.stopWordAudio()
  })
  
  this.currentWordAudio.onError(function(err) {
    console.warn('单词发音失败，尝试有道API:', word, err)
    self.playWordAudioOnline(wordLower, type)
  })
}

/**
 * 使用有道API播放单词发音（备用）
 */
AudioManager.prototype.playWordAudioOnline = function(word, voiceType) {
  var self = this
  
  // 停止当前音频
  this.stopWordAudio()
  
  // 有道API: type=1 英音, type=2 美音
  var youdaoType = voiceType === 'uk' ? 1 : 2
  var url = 'https://dict.youdao.com/dictvoice?audio=' + encodeURIComponent(word) + '&type=' + youdaoType
  
  this.currentWordAudio = wx.createInnerAudioContext()
  this.currentWordAudio.src = url
  this.currentWordAudio.volume = 1.0
  
  this.currentWordAudio.onCanplay(function() {
    self.currentWordAudio.play()
  })
  
  this.currentWordAudio.onEnded(function() {
    self.stopWordAudio()
  })
  
  this.currentWordAudio.onError(function(err) {
    console.warn('有道发音也失败:', word, err)
    self.stopWordAudio()
  })
}

/**
 * 停止当前单词发音
 */
AudioManager.prototype.stopWordAudio = function() {
  if (this.currentWordAudio) {
    this.currentWordAudio.stop()
    this.currentWordAudio.destroy()
    this.currentWordAudio = null
  }
}

/**
 * 播放单词发音多遍
 */
AudioManager.prototype.playWordAudioRepeated = function(word, times, callback) {
  var self = this
  var count = 0
  
  function playNext() {
    if (count >= times) {
      if (callback) callback()
      return
    }
    
    count++
    self.playWordAudio(word)
    
    // 延迟后播放下一遍
    setTimeout(playNext, 1200)
  }
  
  playNext()
}

/**
 * 销毁所有音频资源
 */
AudioManager.prototype.destroy = function() {
  this.stopBgMusic()
  this.stopWordAudio()
}

module.exports = AudioManager
