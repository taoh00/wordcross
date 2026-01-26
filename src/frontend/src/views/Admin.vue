<template>
  <div class="admin-screen">
    <!-- 标题区 -->
    <div class="header-section">
      <div class="logo-area">
        <h1 class="title">🛠️ 后台管理</h1>
      </div>
      <p class="subtitle">WordCross 数据统计中心</p>
    </div>

    <!-- 主卡片 -->
    <div class="main-card">
      <!-- 返回按钮 -->
      <div class="nav-row">
        <router-link to="/" class="back-btn">← 返回首页</router-link>
        <button @click="refreshData" :disabled="loading" class="refresh-btn-small">
          🔄 刷新
        </button>
      </div>

      <!-- 管理员验证 -->
      <div v-if="!isAuthed" class="auth-section">
        <h3>🔐 管理员验证</h3>
        <div class="auth-form">
          <input 
            v-model="adminToken" 
            type="password" 
            placeholder="请输入管理员密钥"
            class="auth-input"
            @keyup.enter="authenticate"
          />
          <button @click="authenticate" class="auth-btn">验证</button>
        </div>
        <p v-if="authError" class="auth-error">{{ authError }}</p>
      </div>

      <!-- 已验证：显示数据 -->
      <template v-else>
        <!-- 选项卡 -->
        <div class="tabs">
          <button 
            v-for="tab in tabs" 
            :key="tab.code"
            @click="currentTab = tab.code"
            :class="['tab-btn', { active: currentTab === tab.code }]"
          >
            {{ tab.icon }} {{ tab.name }}
          </button>
        </div>

        <!-- 加载中 -->
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner">⏳</div>
          <p>加载中...</p>
        </div>

        <!-- 概览 -->
        <div v-else-if="currentTab === 'overview'" class="tab-content">
          <h3 class="section-title">📊 整体概览</h3>
          <div class="stats-grid-4">
            <div class="stat-card blue">
              <div class="stat-value">{{ overview.total_users }}</div>
              <div class="stat-label">总用户数</div>
            </div>
            <div class="stat-card green">
              <div class="stat-value">{{ overview.today_active_users }}</div>
              <div class="stat-label">今日活跃</div>
            </div>
            <div class="stat-card purple">
              <div class="stat-value">{{ overview.total_games }}</div>
              <div class="stat-label">总游戏次数</div>
            </div>
            <div class="stat-card orange">
              <div class="stat-value">{{ overview.today_games }}</div>
              <div class="stat-label">今日游戏</div>
            </div>
          </div>
          
          <div class="stats-grid-2">
            <div class="stat-card pink">
              <div class="stat-value">{{ formatNumber(overview.total_score) }}</div>
              <div class="stat-label">总积分</div>
            </div>
            <div class="stat-card teal">
              <div class="stat-value">{{ formatNumber(overview.total_words) }}</div>
              <div class="stat-label">完成单词</div>
            </div>
          </div>

          <h3 class="section-title">🎮 各模式统计</h3>
          <div class="mode-stats-list">
            <div v-for="mode in modeStats" :key="mode.game_mode" class="mode-stat-row">
              <span class="mode-name">{{ getModeIcon(mode.game_mode) }} {{ getModeName(mode.game_mode) }}</span>
              <span class="mode-value">{{ mode.game_count }} 局 / {{ mode.user_count }} 人</span>
              <span class="mode-score">{{ formatNumber(mode.total_score) }} 分</span>
            </div>
          </div>
        </div>

        <!-- 用户列表 -->
        <div v-else-if="currentTab === 'users'" class="tab-content">
          <h3 class="section-title">👥 用户列表 ({{ userTotal }}人)</h3>
          <div class="users-list">
            <div v-for="user in users" :key="user.id" class="user-row">
              <span class="user-avatar">{{ user.avatar }}</span>
              <div class="user-info">
                <div class="user-name">{{ user.nickname }}</div>
                <div class="user-id">{{ user.id.substring(0, 8) }}...</div>
              </div>
              <div class="user-meta">
                <div class="user-plays">{{ user.total_play_count }} 局</div>
                <div class="user-date">{{ formatDate(user.created_at) }}</div>
              </div>
            </div>
          </div>
          
          <!-- 分页 -->
          <div class="pagination" v-if="userTotal > pageSize">
            <button @click="prevPage" :disabled="currentPage === 0">上一页</button>
            <span>第 {{ currentPage + 1 }} / {{ Math.ceil(userTotal / pageSize) }} 页</span>
            <button @click="nextPage" :disabled="(currentPage + 1) * pageSize >= userTotal">下一页</button>
          </div>
        </div>

        <!-- 每日统计 -->
        <div v-else-if="currentTab === 'daily'" class="tab-content">
          <h3 class="section-title">📅 每日统计 (近30天)</h3>
          <div class="daily-list">
            <div class="daily-header">
              <span>日期</span>
              <span>游戏次数</span>
              <span>活跃用户</span>
              <span>总积分</span>
              <span>单词数</span>
            </div>
            <div v-for="day in dailyStats" :key="day.date" class="daily-row">
              <span>{{ day.date }}</span>
              <span>{{ day.game_count }}</span>
              <span>{{ day.active_users }}</span>
              <span>{{ formatNumber(day.total_score) }}</span>
              <span>{{ day.total_words }}</span>
            </div>
          </div>
        </div>

        <!-- 功能使用 -->
        <div v-else-if="currentTab === 'features'" class="tab-content">
          <h3 class="section-title">🔧 功能使用统计</h3>
          <div class="feature-list">
            <div v-for="feature in featureStats" :key="feature.feature_name" class="feature-row">
              <span class="feature-name">{{ getFeatureName(feature.feature_name) }}</span>
              <span class="feature-users">{{ feature.user_count }} 人使用</span>
              <span class="feature-count">{{ feature.total_usage }} 次</span>
            </div>
          </div>
        </div>

        <!-- 分组统计 -->
        <div v-else-if="currentTab === 'groups'" class="tab-content">
          <h3 class="section-title">📚 分组统计</h3>
          <div class="group-stats-list">
            <div v-for="group in groupStats" :key="group.vocab_group" class="group-stat-row">
              <span class="group-name">{{ getGroupName(group.vocab_group) }}</span>
              <span class="group-games">{{ group.game_count }} 局</span>
              <span class="group-users">{{ group.user_count }} 人</span>
              <span class="group-score">{{ formatNumber(group.total_score) }} 分</span>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || ''

// 状态
const loading = ref(false)
const isAuthed = ref(false)
const adminToken = ref('')
const authError = ref('')
const currentTab = ref('overview')

// 数据
const overview = ref({})
const modeStats = ref([])
const groupStats = ref([])
const users = ref([])
const userTotal = ref(0)
const dailyStats = ref([])
const featureStats = ref([])

// 分页
const pageSize = 20
const currentPage = ref(0)

// 选项卡
const tabs = [
  { code: 'overview', name: '概览', icon: '📊' },
  { code: 'users', name: '用户', icon: '👥' },
  { code: 'daily', name: '每日', icon: '📅' },
  { code: 'groups', name: '分组', icon: '📚' },
  { code: 'features', name: '功能', icon: '🔧' }
]

// 模式名称映射
const modeNames = {
  campaign: '闯关模式',
  endless: '无限模式',
  timed: '计时模式',
  pk: 'PK模式'
}

const modeIcons = {
  campaign: '🏰',
  endless: '♾️',
  timed: '⏱️',
  pk: '⚔️'
}

// 分组名称映射
const groupNames = {
  grade3_1: '三年级上册', grade3_2: '三年级下册',
  grade4_1: '四年级上册', grade4_2: '四年级下册',
  grade5_1: '五年级上册', grade5_2: '五年级下册',
  grade6_1: '六年级上册', grade6_2: '六年级下册',
  junior: '初中词汇', senior: '高中词汇',
  ket: 'KET考试', pet: 'PET考试',
  cet4: '大学四级', cet6: '大学六级',
  postgrad: '考研词汇', ielts: '雅思',
  toefl: '托福', gre: 'GRE'
}

// 功能名称映射
const featureNames = {
  game_campaign: '闯关模式',
  game_endless: '无限模式',
  game_timed: '计时模式',
  game_pk: 'PK模式'
}

function getModeIcon(mode) {
  return modeIcons[mode] || '🎮'
}

function getModeName(mode) {
  return modeNames[mode] || mode
}

function getGroupName(group) {
  return groupNames[group] || group
}

function getFeatureName(feature) {
  return featureNames[feature] || feature
}

function formatNumber(num) {
  if (!num) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toLocaleString()
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return dateStr.split('T')[0]
}

async function authenticate() {
  authError.value = ''
  try {
    // 测试认证
    const response = await axios.get(`${API_BASE}/api/admin/stats/overview`, {
      params: { token: adminToken.value }
    })
    isAuthed.value = true
    localStorage.setItem('admin_token', adminToken.value)
    await loadAllData()
  } catch (error) {
    if (error.response?.status === 403) {
      authError.value = '密钥错误，请重新输入'
    } else {
      authError.value = '验证失败: ' + (error.message || '未知错误')
    }
  }
}

async function loadAllData() {
  loading.value = true
  try {
    const token = adminToken.value || localStorage.getItem('admin_token')
    
    // 加载概览
    const overviewRes = await axios.get(`${API_BASE}/api/admin/stats/overview`, {
      params: { token }
    })
    overview.value = overviewRes.data.overview || {}
    modeStats.value = overviewRes.data.mode_stats || []
    groupStats.value = overviewRes.data.group_stats || []
    
    // 加载用户
    await loadUsers()
    
    // 加载每日统计
    const dailyRes = await axios.get(`${API_BASE}/api/admin/stats/daily`, {
      params: { token, days: 30 }
    })
    dailyStats.value = dailyRes.data.stats || []
    
    // 加载功能统计
    const featureRes = await axios.get(`${API_BASE}/api/admin/stats/feature-usage`, {
      params: { token }
    })
    featureStats.value = featureRes.data.features || []
    
  } catch (error) {
    console.error('加载数据失败:', error)
    if (error.response?.status === 403) {
      isAuthed.value = false
      authError.value = '认证已过期，请重新验证'
    }
  } finally {
    loading.value = false
  }
}

async function loadUsers() {
  const token = adminToken.value || localStorage.getItem('admin_token')
  const usersRes = await axios.get(`${API_BASE}/api/admin/users`, {
    params: { 
      token, 
      limit: pageSize, 
      offset: currentPage.value * pageSize 
    }
  })
  users.value = usersRes.data.users || []
  userTotal.value = usersRes.data.total || 0
}

function prevPage() {
  if (currentPage.value > 0) {
    currentPage.value--
    loadUsers()
  }
}

function nextPage() {
  if ((currentPage.value + 1) * pageSize < userTotal.value) {
    currentPage.value++
    loadUsers()
  }
}

async function refreshData() {
  await loadAllData()
}

onMounted(() => {
  // 检查是否有保存的token
  const savedToken = localStorage.getItem('admin_token')
  if (savedToken) {
    adminToken.value = savedToken
    authenticate()
  }
})
</script>

<style scoped>
.admin-screen {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 16px;
  box-sizing: border-box;
}

.header-section {
  text-align: center;
  padding: 20px 16px 12px;
}

.title {
  font-size: 2rem;
  font-weight: 900;
  color: white;
  text-shadow: 0 4px 0 rgba(0,0,0,0.15);
  margin: 0;
}

.subtitle {
  font-size: 0.9rem;
  color: rgba(255,255,255,0.9);
  margin: 4px 0 0;
}

.main-card {
  flex: 1;
  background: rgba(255,255,255,0.98);
  border-radius: 24px;
  padding: 16px;
  box-shadow: 0 8px 0 rgba(0,0,0,0.08);
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
  overflow: hidden;
}

.nav-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.back-btn {
  padding: 8px 14px;
  background: linear-gradient(180deg, #f3f4f6, #e5e7eb);
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 700;
  color: #6b7280;
  text-decoration: none;
}

.refresh-btn-small {
  padding: 8px 14px;
  background: linear-gradient(180deg, #a78bfa, #8b5cf6);
  border: none;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 700;
  color: white;
  cursor: pointer;
}

/* 认证区 */
.auth-section {
  text-align: center;
  padding: 40px 20px;
}

.auth-section h3 {
  font-size: 1.2rem;
  margin-bottom: 20px;
}

.auth-form {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.auth-input {
  padding: 10px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 1rem;
  width: 200px;
}

.auth-btn {
  padding: 10px 24px;
  background: linear-gradient(180deg, #60a5fa, #3b82f6);
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 700;
  color: white;
  cursor: pointer;
}

.auth-error {
  color: #ef4444;
  margin-top: 12px;
}

/* 选项卡 */
.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 8px 14px;
  background: #f3f4f6;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.tab-btn.active {
  background: linear-gradient(180deg, #a78bfa, #8b5cf6);
  border-color: #7c3aed;
  color: white;
}

/* 加载中 */
.loading-state {
  text-align: center;
  padding: 40px;
}

.loading-spinner {
  font-size: 2rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 内容区 */
.tab-content {
  max-height: 60vh;
  overflow-y: auto;
}

.section-title {
  font-size: 1rem;
  font-weight: 700;
  color: #374151;
  margin: 16px 0 12px;
}

.section-title:first-child {
  margin-top: 0;
}

/* 统计卡片 */
.stats-grid-4 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.stats-grid-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.stat-card {
  text-align: center;
  padding: 16px 10px;
  border-radius: 12px;
}

.stat-card.blue { background: linear-gradient(135deg, #dbeafe, #bfdbfe); }
.stat-card.green { background: linear-gradient(135deg, #d1fae5, #a7f3d0); }
.stat-card.purple { background: linear-gradient(135deg, #ede9fe, #ddd6fe); }
.stat-card.orange { background: linear-gradient(135deg, #fed7aa, #fdba74); }
.stat-card.pink { background: linear-gradient(135deg, #fce7f3, #fbcfe8); }
.stat-card.teal { background: linear-gradient(135deg, #ccfbf1, #99f6e4); }

.stat-value {
  font-size: 1.5rem;
  font-weight: 900;
  color: #374151;
}

.stat-label {
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 4px;
}

/* 模式统计列表 */
.mode-stats-list, .group-stats-list, .feature-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mode-stat-row, .group-stat-row, .feature-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 10px;
}

.mode-name, .group-name, .feature-name {
  font-weight: 600;
  color: #374151;
}

.mode-value, .group-games, .feature-users {
  font-size: 0.85rem;
  color: #6b7280;
}

.mode-score, .group-score, .feature-count {
  font-weight: 700;
  color: #7c3aed;
}

/* 用户列表 */
.users-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.user-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 10px;
}

.user-avatar {
  font-size: 1.5rem;
}

.user-info {
  flex: 1;
}

.user-name {
  font-weight: 600;
  color: #374151;
}

.user-id {
  font-size: 0.7rem;
  color: #9ca3af;
  font-family: monospace;
}

.user-meta {
  text-align: right;
}

.user-plays {
  font-weight: 600;
  color: #7c3aed;
}

.user-date {
  font-size: 0.7rem;
  color: #9ca3af;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
}

.pagination button {
  padding: 8px 16px;
  background: #f3f4f6;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 每日统计 */
.daily-list {
  font-size: 0.85rem;
}

.daily-header, .daily-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr 1fr;
  gap: 8px;
  padding: 8px 12px;
}

.daily-header {
  background: #e5e7eb;
  border-radius: 8px;
  font-weight: 700;
  color: #374151;
}

.daily-row {
  background: #f9fafb;
  border-radius: 6px;
  margin-top: 4px;
}

.daily-row:nth-child(even) {
  background: #f3f4f6;
}

/* 响应式 */
@media (max-width: 600px) {
  .stats-grid-4 {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .tabs {
    justify-content: center;
  }
  
  .daily-header, .daily-row {
    font-size: 0.75rem;
    grid-template-columns: 1.2fr 1fr 1fr 1fr 1fr;
  }
}
</style>
