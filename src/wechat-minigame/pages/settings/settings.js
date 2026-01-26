// pages/settings/settings.js
const { storage } = require('../../utils/storage')

Page({
  data: {
    soundEnabled: true,
    bgMusicEnabled: true,
    showTranslation: true,
    voiceType: 'us',
    
    totalGames: 0,
    totalWords: 0,
    totalScore: 0,
    campaignLevel: 1,
  },

  onLoad() {
    this.loadSettings()
    this.loadStats()
  },

  loadSettings() {
    const settings = storage.get('game_settings') || {}
    this.setData({
      soundEnabled: settings.soundEnabled !== false,
      bgMusicEnabled: settings.bgMusicEnabled !== false,
      showTranslation: settings.showTranslation !== false,
      voiceType: settings.voiceType || 'us',
    })
  },

  loadStats() {
    const stats = storage.get('myStats') || {}
    this.setData({
      totalGames: stats.totalGames || 0,
      totalWords: stats.totalWords || 0,
      totalScore: stats.totalScore || 0,
      campaignLevel: stats.campaignLevel || 1,
    })
  },

  saveSettings() {
    storage.set('game_settings', {
      soundEnabled: this.data.soundEnabled,
      bgMusicEnabled: this.data.bgMusicEnabled,
      showTranslation: this.data.showTranslation,
      voiceType: this.data.voiceType,
    })
  },

  toggleSound(e) {
    this.setData({ soundEnabled: e.detail.value })
    this.saveSettings()
  },

  toggleBgMusic(e) {
    this.setData({ bgMusicEnabled: e.detail.value })
    this.saveSettings()
  },

  toggleTranslation(e) {
    this.setData({ showTranslation: e.detail.value })
    this.saveSettings()
  },

  setVoiceType(e) {
    const type = e.currentTarget.dataset.type
    this.setData({ voiceType: type })
    this.saveSettings()
  },

  resetAllData() {
    wx.showModal({
      title: '确认重置',
      content: '将重置所有游戏进度和道具，此操作不可恢复！',
      confirmText: '确认重置',
      confirmColor: '#dc2626',
      success: (res) => {
        if (res.confirm) {
          const app = getApp()
          
          // 重置体力和道具
          app.globalData.energy = 200
          app.globalData.hintCount = 20
          app.globalData.speakCount = 20
          app.saveEnergy(200)
          app.saveProps()
          
          // 清除统计和进度
          storage.remove('myStats')
          
          // 清除所有词库进度
          const keys = storage.getInfo().keys || []
          keys.forEach(key => {
            if (key.startsWith('campaign_progress_')) {
              storage.remove(key)
            }
          })
          
          this.loadStats()
          
          wx.showToast({ title: '重置成功', icon: 'success' })
        }
      },
    })
  },
})
