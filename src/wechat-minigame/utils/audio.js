/**
 * 音频播放封装
 * 使用 wx.createInnerAudioContext
 */

let audioContext = null
let bgMusicContext = null

const audio = {
  /**
   * 播放单词发音
   * @param {string} word 单词
   * @param {string} type 发音类型：'us' 美音，'uk' 英音
   */
  speakWord(word, type = 'us') {
    if (!word) return
    
    // 停止之前的播放
    this.stopSpeak()
    
    const app = getApp()
    const baseUrl = app?.globalData?.apiBase || 'https://superhe.art:10010'
    const url = `${baseUrl}/data/audio/${type}/${word.toLowerCase()}.mp3`
    
    audioContext = wx.createInnerAudioContext()
    audioContext.src = url
    audioContext.play()
    
    audioContext.onError((err) => {
      console.warn('音频播放失败:', err)
      // 尝试使用备用方案
      this.speakWordFallback(word)
    })
  },

  /**
   * 备用发音方案（使用在线TTS）
   * @param {string} word 单词
   */
  speakWordFallback(word) {
    // 使用有道词典API作为备用
    const url = `https://dict.youdao.com/dictvoice?audio=${encodeURIComponent(word)}&type=1`
    
    if (audioContext) {
      audioContext.destroy()
    }
    
    audioContext = wx.createInnerAudioContext()
    audioContext.src = url
    audioContext.play()
  },

  /**
   * 停止发音
   */
  stopSpeak() {
    if (audioContext) {
      audioContext.stop()
      audioContext.destroy()
      audioContext = null
    }
  },

  /**
   * 播放音效
   * @param {string} type 音效类型：'type', 'delete', 'correct', 'complete'
   */
  playSound(type) {
    const sounds = {
      type: '/audio/type.mp3',
      delete: '/audio/delete.mp3',
      correct: '/audio/correct.mp3',
      complete: '/audio/complete.mp3',
    }
    
    const src = sounds[type]
    if (!src) return
    
    const ctx = wx.createInnerAudioContext()
    ctx.src = src
    ctx.volume = 0.5
    ctx.play()
    
    ctx.onEnded(() => {
      ctx.destroy()
    })
    
    ctx.onError(() => {
      ctx.destroy()
    })
  },

  /**
   * 播放背景音乐
   * @param {string} mode 游戏模式
   */
  startBgMusic(mode = 'campaign') {
    this.stopBgMusic()
    
    // 不同模式使用不同背景音乐
    const musicMap = {
      campaign: '/audio/bg_campaign.mp3',
      endless: '/audio/bg_endless.mp3',
      timed: '/audio/bg_timed.mp3',
      pk: '/audio/bg_pk.mp3',
    }
    
    const src = musicMap[mode] || musicMap.campaign
    
    bgMusicContext = wx.createInnerAudioContext()
    bgMusicContext.src = src
    bgMusicContext.loop = true
    bgMusicContext.volume = 0.3
    bgMusicContext.play()
    
    bgMusicContext.onError(() => {
      console.warn('背景音乐播放失败')
    })
  },

  /**
   * 停止背景音乐
   */
  stopBgMusic() {
    if (bgMusicContext) {
      bgMusicContext.stop()
      bgMusicContext.destroy()
      bgMusicContext = null
    }
  },

  /**
   * 设置背景音乐音量
   * @param {number} volume 音量 0-1
   */
  setBgMusicVolume(volume) {
    if (bgMusicContext) {
      bgMusicContext.volume = volume
    }
  },
}

module.exports = {
  audio,
}
