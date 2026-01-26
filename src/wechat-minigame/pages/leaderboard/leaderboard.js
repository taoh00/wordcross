// pages/leaderboard/leaderboard.js
const { leaderboardApi } = require('../../utils/api')
const { storage } = require('../../utils/storage')

Page({
  data: {
    currentType: 'campaign_level',
    currentUnit: '关',
    loading: true,
    rankings: [],
    myRank: null,
    
    leaderboardTypes: [
      { code: 'campaign_level', name: '闯关进度', icon: '🏰', unit: '关' },
      { code: 'campaign_score', name: '闯关积分', icon: '🌟', unit: '分' },
      { code: 'timed_words', name: '计时单词', icon: '⏱️', unit: '词' },
      { code: 'timed_score', name: '计时积分', icon: '💯', unit: '分' },
      { code: 'endless_level', name: '无限关卡', icon: '♾️', unit: '关' },
      { code: 'endless_score', name: '无限积分', icon: '🔥', unit: '分' },
    ],
  },

  onLoad() {
    this.loadRankings()
  },

  onPullDownRefresh() {
    this.loadRankings().finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  async loadRankings() {
    const { currentType, leaderboardTypes } = this.data
    
    this.setData({ loading: true })
    
    try {
      const data = await leaderboardApi.get(currentType, 'all', 50)
      
      const app = getApp()
      const userId = app.globalData.userId
      
      // 标记自己
      const rankings = (data.rankings || []).map((item, index) => ({
        ...item,
        rank: index + 1,
        is_me: item.user_id === userId,
      }))
      
      // 找到自己的排名
      const myRank = rankings.find(r => r.is_me)
      
      // 获取单位
      const typeInfo = leaderboardTypes.find(t => t.code === currentType)
      
      this.setData({
        rankings,
        myRank,
        currentUnit: typeInfo?.unit || '',
        loading: false,
      })
    } catch (e) {
      console.error('加载排行榜失败:', e)
      this.setData({
        rankings: [],
        loading: false,
      })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  selectType(e) {
    const code = e.currentTarget.dataset.code
    this.setData({ currentType: code })
    this.loadRankings()
  },
})
