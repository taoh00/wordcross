<template>
  <div class="leaderboard-screen">
    <!-- 标题区 -->
    <div class="header-section">
      <div class="logo-area">
        <h1 class="title">🏆 排行榜</h1>
      </div>
      <p class="subtitle">看看谁是单词达人！</p>
    </div>

    <!-- 主卡片 -->
    <div class="main-card">
      <!-- 返回按钮 -->
      <div class="nav-row">
        <router-link to="/" class="back-btn">← 返回首页</router-link>
      </div>

      <!-- 榜单类型选择 -->
      <div class="selection-section">
        <h3 class="section-label">📊 榜单类型</h3>
        <div class="type-grid">
          <button
            v-for="type in leaderboardTypes"
            :key="type.code"
            @click="selectType(type.code)"
            :class="['type-btn', { active: selectedType === type.code }]"
          >
            <span class="type-icon">{{ getTypeIcon(type.code) }}</span>
            <span class="type-name">{{ type.name }}</span>
          </button>
        </div>
      </div>

      <!-- 分组选择 -->
      <div class="selection-section">
        <h3 class="section-label">📚 词库分组</h3>
        <div class="group-tabs">
          <button
            @click="selectedGroup = 'all'"
            :class="['group-tab', { active: selectedGroup === 'all' }]"
          >
            全部
          </button>
          <button
            v-for="group in groupCategories"
            :key="group.code"
            @click="selectGroupCategory(group.code)"
            :class="['group-tab', { active: selectedGroupCategory === group.code }]"
          >
            {{ group.name }}
          </button>
        </div>
        
        <!-- 细分组（如果选择了分类） -->
        <div v-if="selectedGroupCategory && subGroups.length > 0" class="subgroup-row">
          <button
            v-for="sub in subGroups"
            :key="sub.code"
            @click="selectedGroup = sub.code"
            :class="['subgroup-btn', { active: selectedGroup === sub.code }]"
          >
            {{ sub.name }}
          </button>
        </div>
      </div>

      <!-- 排行榜列表 -->
      <div class="leaderboard-section">
        <!-- 加载中 -->
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner">⏳</div>
          <p>加载中...</p>
        </div>

        <!-- 无数据 -->
        <div v-else-if="leaderboard.length === 0" class="empty-state">
          <div class="empty-icon">📭</div>
          <p class="empty-text">暂无排行数据</p>
          <p class="empty-hint">快去玩游戏，成为第一名吧！</p>
        </div>

        <!-- 排行榜条目 -->
        <div v-else class="leaderboard-list">
          <div
            v-for="entry in leaderboard"
            :key="entry.user_id + entry.rank"
            :class="['leaderboard-row', getRankClass(entry.rank)]"
          >
            <!-- 排名 -->
            <div class="rank-col">
              <span v-if="entry.rank <= 3" class="rank-medal">{{ getRankEmoji(entry.rank) }}</span>
              <span v-else class="rank-num">{{ entry.rank }}</span>
            </div>

            <!-- 用户信息 -->
            <div class="user-col">
              <span class="user-avatar">{{ entry.avatar }}</span>
              <div class="user-info">
                <div class="user-name">{{ entry.nickname }}</div>
                <div class="user-group">{{ entry.group_name }}</div>
              </div>
            </div>

            <!-- 数值 -->
            <div class="value-col">
              <div class="value-main">{{ formatValue(entry.value) }}</div>
              <div class="value-label">{{ getValueLabel() }}</div>
              <!-- 额外信息 -->
              <div v-if="entry.extra && Object.keys(entry.extra).length > 0" class="value-extra">
                <span v-if="entry.extra.wins !== undefined">{{ entry.extra.wins }}胜</span>
                <span v-if="entry.extra.games !== undefined">/{{ entry.extra.games }}场</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 刷新按钮 -->
      <div class="action-row">
        <button @click="loadLeaderboard" :disabled="loading" class="refresh-btn">
          🔄 刷新排行榜
        </button>
      </div>
    </div>

    <!-- 我的记录 -->
    <div class="my-stats-card">
      <h3 class="stats-title">📊 我的记录</h3>
      
      <div class="stats-grid">
        <div class="stat-item purple">
          <div class="stat-value">{{ myStats.campaignLevel }}</div>
          <div class="stat-label">闯关进度</div>
        </div>
        <div class="stat-item green">
          <div class="stat-value">{{ myStats.totalScore }}</div>
          <div class="stat-label">总积分</div>
        </div>
        <div class="stat-item orange">
          <div class="stat-value">{{ myStats.totalWords }}</div>
          <div class="stat-label">完成单词</div>
        </div>
        <div class="stat-item blue">
          <div class="stat-value">{{ myStats.pkWins }}</div>
          <div class="stat-label">PK胜场</div>
        </div>
      </div>
      
      <!-- 我的排名 -->
      <div v-if="myRankings" class="my-rankings">
        <h4 class="rankings-title">我的排名</h4>
        <div class="rankings-list">
          <div v-for="(ranking, typeCode) in myRankings" :key="typeCode" class="ranking-item">
            <span class="ranking-type">{{ ranking.name }}</span>
            <span v-if="ranking.groups && ranking.groups.all" class="ranking-rank">
              第{{ ranking.groups.all.rank }}名 / {{ ranking.groups.all.total }}人
            </span>
            <span v-else class="ranking-rank">暂无</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部装饰 -->
    <div class="footer-decoration">
      <span class="footer-icon">🥇</span>
      <span class="footer-icon">🥈</span>
      <span class="footer-icon">🥉</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || ''

// 状态
const loading = ref(false)
const selectedType = ref('campaign_level')
const selectedGroup = ref('all')
const selectedGroupCategory = ref(null)
const leaderboard = ref([])
const myRankings = ref(null)

// 排行榜类型
const leaderboardTypes = ref([
  { code: 'campaign_level', name: '闯关关卡榜' },
  { code: 'campaign_score', name: '闯关积分榜' },
  { code: 'endless_level', name: '无限关卡榜' },
  { code: 'endless_score', name: '无限积分榜' },
  { code: 'timed_words', name: '计时单词榜' },
  { code: 'timed_score', name: '计时积分榜' },
  { code: 'pk_wins', name: 'PK获胜榜' },
  { code: 'pk_score', name: 'PK积分榜' }
])

// 分组大类
const groupCategories = [
  { code: 'primary', name: '小学' },
  { code: 'middle', name: '初高中' },
  { code: 'exam', name: '考试' }
]

// 细分组映射
const subGroupsMap = {
  primary: [
    { code: 'grade3_1', name: '三上' },
    { code: 'grade3_2', name: '三下' },
    { code: 'grade4_1', name: '四上' },
    { code: 'grade4_2', name: '四下' },
    { code: 'grade5_1', name: '五上' },
    { code: 'grade5_2', name: '五下' },
    { code: 'grade6_1', name: '六上' },
    { code: 'grade6_2', name: '六下' }
  ],
  middle: [
    { code: 'junior', name: '初中' },
    { code: 'senior', name: '高中' }
  ],
  exam: [
    { code: 'ket', name: 'KET' },
    { code: 'pet', name: 'PET' },
    { code: 'cet4', name: '四级' },
    { code: 'cet6', name: '六级' },
    { code: 'postgrad', name: '考研' },
    { code: 'ielts', name: '雅思' },
    { code: 'toefl', name: '托福' },
    { code: 'gre', name: 'GRE' }
  ]
}

// 计算细分组
const subGroups = computed(() => {
  if (!selectedGroupCategory.value) return []
  return subGroupsMap[selectedGroupCategory.value] || []
})

// 类型图标
function getTypeIcon(code) {
  const icons = {
    'campaign_level': '🏰',
    'campaign_score': '⭐',
    'endless_level': '♾️',
    'endless_score': '🌟',
    'timed_words': '⏱️',
    'timed_score': '💫',
    'pk_wins': '⚔️',
    'pk_score': '🏅'
  }
  return icons[code] || '📊'
}

// 数值标签
function getValueLabel() {
  const labels = {
    'campaign_level': '关',
    'campaign_score': '分',
    'endless_level': '关',
    'endless_score': '分',
    'timed_words': '词',
    'timed_score': '分',
    'pk_wins': '胜',
    'pk_score': '分'
  }
  return labels[selectedType.value] || ''
}

// 格式化数值
function formatValue(value) {
  if (value >= 10000) {
    return (value / 10000).toFixed(1) + '万'
  }
  return value
}

// 个人统计
const myStats = ref({
  campaignLevel: 1,
  totalScore: 0,
  totalWords: 0,
  pkWins: 0,
  endlessLevel: 0,
  timedWords: 0,
  playCount: 0
})

// 方法
async function loadLeaderboard() {
  loading.value = true
  try {
    const response = await axios.get(`${API_BASE}/api/leaderboard/${selectedType.value}`, {
      params: {
        group: selectedGroup.value,
        limit: 50
      }
    })
    leaderboard.value = response.data.entries || []
  } catch (error) {
    console.error('加载排行榜失败:', error)
    // 显示空列表
    leaderboard.value = []
  } finally {
    loading.value = false
  }
}

async function loadMyRankings() {
  try {
    const userId = getUserId()
    if (!userId) return
    
    const response = await axios.get(`${API_BASE}/api/leaderboard/user/${userId}`)
    myRankings.value = response.data.rankings
  } catch (error) {
    console.error('加载我的排名失败:', error)
  }
}

function getUserId() {
  // 从cookie或localStorage获取用户ID
  const match = document.cookie.match(/user_id=([^;]+)/)
  return match ? match[1] : null
}


function getRankClass(rank) {
  if (rank === 1) return 'rank-gold'
  if (rank === 2) return 'rank-silver'
  if (rank === 3) return 'rank-bronze'
  return ''
}

function getRankEmoji(rank) {
  const emojis = { 1: '🥇', 2: '🥈', 3: '🥉' }
  return emojis[rank] || ''
}

function selectType(type) {
  selectedType.value = type
}

function selectGroupCategory(category) {
  if (selectedGroupCategory.value === category) {
    // 点击同一个分类，取消选择
    selectedGroupCategory.value = null
    selectedGroup.value = 'all'
  } else {
    selectedGroupCategory.value = category
    // 默认选择第一个子分组
    const subs = subGroupsMap[category]
    if (subs && subs.length > 0) {
      selectedGroup.value = subs[0].code
    }
  }
}

async function loadMyStats() {
  try {
    // 优先从API获取真实统计
    const response = await axios.get(`${API_BASE}/api/user/stats`, {
      withCredentials: true
    })
    
    if (response.data.registered && response.data.stats) {
      const stats = response.data.stats
      myStats.value.campaignLevel = stats.campaign?.max_level || 1
      myStats.value.totalScore = (stats.campaign?.total_score || 0) + 
                                  (stats.endless?.total_score || 0) + 
                                  (stats.timed?.total_score || 0) +
                                  (stats.pk?.total_score || 0)
      myStats.value.totalWords = stats.campaign?.total_words || 0
      myStats.value.pkWins = stats.pk?.wins || 0
      myStats.value.endlessLevel = stats.endless?.max_level || 0
      myStats.value.timedWords = stats.timed?.max_words || 0
      myStats.value.playCount = (stats.campaign?.play_count || 0) +
                                (stats.endless?.play_count || 0) +
                                (stats.timed?.play_count || 0) +
                                (stats.pk?.play_count || 0)
      return
    }
  } catch (e) {
    console.log('API统计获取失败，回退到本地存储:', e)
  }
  
  // 回退：从本地存储读取个人统计
  try {
    const progressKeys = Object.keys(localStorage).filter(k => k.startsWith('campaign_progress_'))
    let maxLevel = 1
    let totalCompleted = 0
    
    progressKeys.forEach(key => {
      const progress = JSON.parse(localStorage.getItem(key) || '{}')
      const completed = Object.keys(progress.completed || {}).length
      totalCompleted += completed
      if (progress.unlocked > maxLevel) {
        maxLevel = progress.unlocked
      }
    })
    
    myStats.value.campaignLevel = maxLevel
    myStats.value.totalWords = totalCompleted * 5
    myStats.value.totalScore = myStats.value.totalWords * 10
    
    const pkStats = localStorage.getItem('pk_stats')
    if (pkStats) {
      const stats = JSON.parse(pkStats)
      myStats.value.pkWins = stats.wins || 0
    }
  } catch (e) {
    console.error('加载统计失败:', e)
  }
}

// 监听筛选条件变化
watch([selectedType, selectedGroup], () => {
  loadLeaderboard()
})

// 初始化
onMounted(() => {
  loadLeaderboard()
  loadMyStats()
  loadMyRankings()
})
</script>

<style scoped>
/* 整体布局 */
.leaderboard-screen {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  padding: 16px;
  box-sizing: border-box;
}

/* 标题区 */
.header-section {
  flex-shrink: 0;
  text-align: center;
  padding: 20px 16px 12px;
}

.logo-area {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 4px;
}

.title {
  font-size: 2rem;
  font-weight: 900;
  color: white;
  text-shadow: 0 4px 0 rgba(0,0,0,0.15), 0 6px 20px rgba(0,0,0,0.25);
  margin: 0;
}

.subtitle {
  font-size: 0.9rem;
  color: rgba(255,255,255,0.9);
  margin: 4px 0 0;
  font-weight: 600;
}

/* 主卡片 */
.main-card {
  flex: 1;
  background: rgba(255,255,255,0.98);
  border-radius: 24px;
  padding: 16px;
  box-shadow: 0 8px 0 rgba(0,0,0,0.08), 0 12px 30px rgba(0,0,0,0.15);
  max-width: 480px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.nav-row {
  margin-bottom: 12px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  padding: 8px 14px;
  background: linear-gradient(180deg, #f3f4f6, #e5e7eb);
  border: none;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 700;
  color: #6b7280;
  text-decoration: none;
  box-shadow: 0 2px 0 #d1d5db;
  transition: all 0.15s ease;
}

.back-btn:active {
  transform: translateY(2px);
  box-shadow: 0 0 0 #d1d5db;
}

/* 选择区域 */
.selection-section {
  margin-bottom: 12px;
}

.section-label {
  font-size: 0.85rem;
  font-weight: 700;
  color: #5b21b6;
  margin: 0 0 8px;
}

/* 类型网格 */
.type-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
}

.type-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 4px;
  background: linear-gradient(180deg, #f9fafb, #f3f4f6);
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 2px 0 #d1d5db;
}

.type-btn:active {
  transform: translateY(2px);
  box-shadow: 0 0 0 #d1d5db;
}

.type-btn.active {
  background: linear-gradient(180deg, #a78bfa, #8b5cf6);
  border-color: #7c3aed;
  box-shadow: 0 2px 0 #6d28d9;
}

.type-btn.active .type-name {
  color: white;
}

.type-icon {
  font-size: 1.2rem;
}

.type-name {
  font-size: 0.65rem;
  font-weight: 700;
  color: #6b7280;
  text-align: center;
  line-height: 1.2;
}

/* 分组标签 */
.group-tabs {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.group-tab {
  padding: 6px 12px;
  background: linear-gradient(180deg, #f9fafb, #f3f4f6);
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  font-size: 0.8rem;
  font-weight: 700;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s ease;
}

.group-tab.active {
  background: linear-gradient(180deg, #60a5fa, #3b82f6);
  border-color: #2563eb;
  color: white;
}

.subgroup-row {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 8px;
  padding: 8px;
  background: #f9fafb;
  border-radius: 10px;
}

.subgroup-btn {
  padding: 4px 10px;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s ease;
}

.subgroup-btn.active {
  background: linear-gradient(180deg, #a78bfa, #8b5cf6);
  border-color: #7c3aed;
  color: white;
}

/* 排行榜区域 */
.leaderboard-section {
  flex: 1;
  overflow-y: auto;
  min-height: 200px;
  max-height: 35vh;
}

.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  text-align: center;
}

.loading-spinner {
  font-size: 2.5rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 12px;
}

.empty-text {
  font-size: 1rem;
  font-weight: 700;
  color: #6b7280;
  margin: 0 0 4px;
}

.empty-hint {
  font-size: 0.85rem;
  color: #9ca3af;
  margin: 0;
}

/* 排行榜列表 */
.leaderboard-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.leaderboard-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: linear-gradient(135deg, #f9fafb, #f3f4f6);
  border-radius: 12px;
  border: 2px solid #e5e7eb;
}

.leaderboard-row.rank-gold {
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  border-color: #fbbf24;
}

.leaderboard-row.rank-silver {
  background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
  border-color: #94a3b8;
}

.leaderboard-row.rank-bronze {
  background: linear-gradient(135deg, #fed7aa, #fdba74);
  border-color: #f97316;
}

.rank-col {
  width: 36px;
  text-align: center;
}

.rank-medal {
  font-size: 1.5rem;
}

.rank-num {
  font-size: 1rem;
  font-weight: 900;
  color: #6b7280;
}

.user-col {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.user-avatar {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.user-info {
  min-width: 0;
}

.user-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-group {
  font-size: 0.7rem;
  color: #9ca3af;
}

.value-col {
  text-align: right;
  flex-shrink: 0;
}

.value-main {
  font-size: 1.1rem;
  font-weight: 900;
  color: #7c3aed;
}

.value-label {
  font-size: 0.65rem;
  color: #9ca3af;
}

.value-extra {
  font-size: 0.65rem;
  color: #6b7280;
}

/* 操作按钮 */
.action-row {
  margin-top: 12px;
  text-align: center;
}

.refresh-btn {
  padding: 10px 24px;
  background: linear-gradient(180deg, #a78bfa, #8b5cf6);
  border: none;
  border-radius: 14px;
  font-size: 0.9rem;
  font-weight: 700;
  color: white;
  cursor: pointer;
  box-shadow: 0 4px 0 #6d28d9;
  transition: all 0.15s ease;
}

.refresh-btn:active {
  transform: translateY(3px);
  box-shadow: 0 1px 0 #6d28d9;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 我的记录卡片 */
.my-stats-card {
  background: rgba(255,255,255,0.98);
  border-radius: 20px;
  padding: 16px;
  margin-top: 12px;
  max-width: 480px;
  width: 100%;
  margin-left: auto;
  margin-right: auto;
  box-shadow: 0 6px 0 rgba(0,0,0,0.08), 0 10px 25px rgba(0,0,0,0.12);
}

.stats-title {
  font-size: 1rem;
  font-weight: 800;
  color: #374151;
  margin: 0 0 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.stat-item {
  text-align: center;
  padding: 10px 6px;
  border-radius: 12px;
}

.stat-item.purple { background: linear-gradient(135deg, #ede9fe, #ddd6fe); }
.stat-item.green { background: linear-gradient(135deg, #d1fae5, #a7f3d0); }
.stat-item.orange { background: linear-gradient(135deg, #fed7aa, #fdba74); }
.stat-item.blue { background: linear-gradient(135deg, #dbeafe, #bfdbfe); }

.stat-value {
  font-size: 1.3rem;
  font-weight: 900;
  color: #374151;
}

.stat-label {
  font-size: 0.65rem;
  font-weight: 600;
  color: #6b7280;
  margin-top: 2px;
}

/* 我的排名 */
.my-rankings {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 2px dashed #e5e7eb;
}

.rankings-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: #6b7280;
  margin: 0 0 8px;
}

.rankings-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ranking-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  background: #f9fafb;
  border-radius: 8px;
}

.ranking-type {
  font-size: 0.8rem;
  font-weight: 600;
  color: #374151;
}

.ranking-rank {
  font-size: 0.75rem;
  font-weight: 700;
  color: #7c3aed;
}

/* 底部装饰 */
.footer-decoration {
  flex-shrink: 0;
  text-align: center;
  padding: 12px 0;
  display: flex;
  justify-content: center;
  gap: 16px;
}

.footer-icon {
  font-size: 1.5rem;
  animation: bounce 2s ease-in-out infinite;
}

.footer-icon:nth-child(2) { animation-delay: 0.5s; }
.footer-icon:nth-child(3) { animation-delay: 1s; }

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

/* 小屏幕优化 */
@media (max-height: 700px) {
  .header-section { padding: 12px 12px 8px; }
  .title { font-size: 1.6rem; }
  .main-card { padding: 12px; }
  .type-grid { gap: 4px; }
  .type-btn { padding: 6px 2px; }
  .type-icon { font-size: 1rem; }
  .type-name { font-size: 0.6rem; }
  .leaderboard-section { max-height: 30vh; }
  .stats-grid { gap: 6px; }
  .stat-item { padding: 8px 4px; }
  .stat-value { font-size: 1.1rem; }
}

/* 大屏幕优化 */
@media (min-width: 768px) {
  .main-card { max-width: 560px; }
  .type-grid { grid-template-columns: repeat(4, 1fr); gap: 8px; }
  .type-btn { padding: 10px 8px; }
  .type-icon { font-size: 1.4rem; }
  .type-name { font-size: 0.75rem; }
  .leaderboard-section { max-height: 40vh; }
}
</style>
