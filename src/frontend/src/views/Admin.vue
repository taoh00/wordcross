<template>
  <div class="admin-screen">
    <!-- 标题区 -->
    <div class="header-section">
      <div class="logo-area">
        <h1 class="title">WordCross</h1>
      </div>
      <p class="subtitle">管理后台</p>
    </div>

    <!-- 主卡片 -->
    <div class="main-card">
      <!-- 返回按钮 -->
      <div class="nav-row">
        <router-link to="/" class="back-btn">← 返回</router-link>
        <button @click="refreshData" :disabled="loading" class="refresh-btn-small">
          {{ loading ? '刷新中...' : '刷新' }}
        </button>
      </div>

      <!-- 管理员验证 -->
      <div v-if="!isAuthed" class="auth-section">
        <h3>管理员验证</h3>
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
        <!-- 选项卡 - 滚动容器 -->
        <div class="tabs-container">
          <div class="tabs">
            <button 
              v-for="tab in tabs" 
              :key="tab.code"
              @click="currentTab = tab.code"
              :class="['tab-btn', { active: currentTab === tab.code }]"
            >
              <span class="tab-icon">{{ tab.icon }}</span>
              <span class="tab-name">{{ tab.name }}</span>
            </button>
          </div>
        </div>

        <!-- 加载中 -->
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <p>加载中...</p>
        </div>

        <!-- 概览 -->
        <div v-else-if="currentTab === 'overview'" class="tab-content">
          <h3 class="section-title">整体概览</h3>
          <div class="stats-grid">
            <div class="stat-card blue">
              <div class="stat-icon">👥</div>
              <div class="stat-value">{{ overview.total_users || 0 }}</div>
              <div class="stat-label">总用户数</div>
            </div>
            <div class="stat-card green">
              <div class="stat-icon">🔥</div>
              <div class="stat-value">{{ overview.today_active_users || 0 }}</div>
              <div class="stat-label">今日活跃</div>
            </div>
            <div class="stat-card purple">
              <div class="stat-icon">🎮</div>
              <div class="stat-value">{{ formatNumber(overview.total_games) }}</div>
              <div class="stat-label">总游戏次数</div>
            </div>
            <div class="stat-card orange">
              <div class="stat-icon">📈</div>
              <div class="stat-value">{{ overview.today_games || 0 }}</div>
              <div class="stat-label">今日游戏</div>
            </div>
            <div class="stat-card pink">
              <div class="stat-icon">⭐</div>
              <div class="stat-value">{{ formatNumber(overview.total_score) }}</div>
              <div class="stat-label">总积分</div>
            </div>
            <div class="stat-card teal">
              <div class="stat-icon">📝</div>
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
          <h3 class="section-title">用户列表 ({{ userTotal }}人)</h3>
          <div class="users-list">
            <div v-for="user in users" :key="user.id" class="user-row" @click="showUserDetail(user)">
              <span class="user-avatar">{{ user.avatar }}</span>
              <div class="user-info">
                <div class="user-name">{{ user.nickname }}</div>
                <div class="user-id">{{ user.id.substring(0, 8) }}...</div>
              </div>
              <div class="user-meta">
                <div class="user-plays">{{ user.total_play_count || 0 }} 局</div>
                <div class="user-date">{{ formatDate(user.created_at) }}</div>
              </div>
              <span class="arrow">›</span>
            </div>
          </div>
          
          <!-- 分页 -->
          <div class="pagination" v-if="userTotal > pageSize">
            <button @click="prevPage" :disabled="currentPage === 0">上一页</button>
            <span>{{ currentPage + 1 }} / {{ Math.ceil(userTotal / pageSize) }}</span>
            <button @click="nextPage" :disabled="(currentPage + 1) * pageSize >= userTotal">下一页</button>
          </div>
        </div>

        <!-- 顶级玩家 -->
        <div v-else-if="currentTab === 'top'" class="tab-content">
          <h3 class="section-title">顶级玩家 TOP 20</h3>
          <div class="top-players-list">
            <div v-for="(player, index) in topPlayers" :key="player.id" class="player-row">
              <div class="player-rank" :class="{ gold: index === 0, silver: index === 1, bronze: index === 2 }">
                {{ index + 1 }}
              </div>
              <span class="player-avatar">{{ player.avatar }}</span>
              <div class="player-info">
                <div class="player-name">{{ player.nickname }}</div>
                <div class="player-games">{{ player.game_count }} 局</div>
              </div>
              <div class="player-score">{{ formatNumber(player.total_score) }} 分</div>
            </div>
          </div>
        </div>

        <!-- 终端统计 -->
        <div v-else-if="currentTab === 'platform'" class="tab-content">
          <h3 class="section-title">平台分布</h3>
          <div v-if="platformStats.platform && platformStats.platform.length" class="platform-list">
            <div v-for="p in platformStats.platform" :key="p.platform" class="platform-row">
              <span class="platform-icon">{{ getPlatformIcon(p.platform) }}</span>
              <span class="platform-name">{{ getPlatformName(p.platform) }}</span>
              <span class="platform-count">{{ p.session_count }} 次会话</span>
              <span class="platform-users">{{ p.user_count }} 用户</span>
            </div>
          </div>
          <div v-else class="empty-state">暂无平台数据</div>

          <h3 class="section-title">设备类型</h3>
          <div v-if="platformStats.device && platformStats.device.length" class="device-list">
            <div v-for="d in platformStats.device" :key="d.device_type" class="device-row">
              <span class="device-icon">{{ getDeviceIcon(d.device_type) }}</span>
              <span class="device-name">{{ d.device_type || '未知' }}</span>
              <span class="device-count">{{ d.count }} 次</span>
            </div>
          </div>
          <div v-else class="empty-state">暂无设备数据</div>

          <h3 class="section-title">浏览器分布</h3>
          <div v-if="platformStats.browser && platformStats.browser.length" class="browser-list">
            <div v-for="b in platformStats.browser" :key="b.browser" class="browser-row">
              <span class="browser-name">{{ b.browser || '未知' }}</span>
              <span class="browser-count">{{ b.count }} 次</span>
            </div>
          </div>
          <div v-else class="empty-state">暂无浏览器数据</div>

          <h3 class="section-title">操作系统</h3>
          <div v-if="platformStats.os && platformStats.os.length" class="os-list">
            <div v-for="o in platformStats.os" :key="o.os" class="os-row">
              <span class="os-name">{{ o.os || '未知' }}</span>
              <span class="os-count">{{ o.count }} 次</span>
            </div>
          </div>
          <div v-else class="empty-state">暂无系统数据</div>
        </div>

        <!-- 行为分析 -->
        <div v-else-if="currentTab === 'behavior'" class="tab-content">
          <h3 class="section-title">体力领取统计</h3>
          <div v-if="energyStats.by_type && energyStats.by_type.length" class="energy-stats">
            <div v-for="e in energyStats.by_type" :key="e.claim_type" class="energy-row">
              <span class="energy-type">{{ getClaimTypeName(e.claim_type) }}</span>
              <span class="energy-count">{{ e.claim_count }} 次</span>
              <span class="energy-amount">+{{ e.total_amount }} 体力</span>
              <span class="energy-users">{{ e.user_count }} 人</span>
            </div>
          </div>
          <div v-else class="empty-state">暂无体力领取数据</div>

          <h3 class="section-title">道具使用统计</h3>
          <div v-if="propsStats.by_type && propsStats.by_type.length" class="props-stats">
            <div v-for="p in propsStats.by_type" :key="p.prop_type" class="prop-row">
              <span class="prop-icon">{{ getPropIcon(p.prop_type) }}</span>
              <span class="prop-name">{{ getPropName(p.prop_type) }}</span>
              <span class="prop-count">{{ p.usage_count }} 次</span>
              <span class="prop-users">{{ p.user_count }} 人</span>
            </div>
          </div>
          <div v-else class="empty-state">暂无道具使用数据</div>

          <h3 class="section-title">事件统计</h3>
          <div v-if="eventStats.stats && eventStats.stats.length" class="event-stats">
            <div v-for="e in eventStats.stats" :key="e.event_type" class="event-row">
              <span class="event-name">{{ getEventName(e.event_type) }}</span>
              <span class="event-count">{{ e.total_count }} 次</span>
              <span class="event-users">{{ e.user_count }} 人</span>
            </div>
          </div>
          <div v-else class="empty-state">暂无事件数据</div>
        </div>

        <!-- 关卡留存 -->
        <div v-else-if="currentTab === 'retention'" class="tab-content">
          <h3 class="section-title">关卡流失分析 TOP 10</h3>
          <p class="section-desc">以下关卡的玩家流失率最高</p>
          <div v-if="retentionStats.dropoff_analysis && retentionStats.dropoff_analysis.length" class="dropoff-list">
            <div v-for="(d, i) in retentionStats.dropoff_analysis" :key="i" class="dropoff-row">
              <div class="dropoff-levels">第 {{ d.from_level }} → {{ d.to_level }} 关</div>
              <div class="dropoff-stats">
                <span class="dropoff-players">{{ d.from_players }} → {{ d.to_players }} 人</span>
                <span class="dropoff-rate" :class="{ high: d.dropoff_rate > 30 }">
                  流失 {{ d.dropoff_rate }}%
                </span>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">暂无流失数据</div>

          <h3 class="section-title">关卡通过人数</h3>
          <div v-if="retentionStats.retention && retentionStats.retention.length" class="retention-list">
            <div v-for="r in retentionStats.retention.slice(0, 20)" :key="r.level" class="retention-row">
              <span class="retention-level">第 {{ r.level }} 关</span>
              <span class="retention-players">{{ r.player_count }} 人通过</span>
              <span class="retention-stars">平均 {{ (r.avg_stars || 0).toFixed(1) }} 星</span>
            </div>
          </div>
          <div v-else class="empty-state">暂无留存数据</div>
        </div>

        <!-- 每日统计 -->
        <div v-else-if="currentTab === 'daily'" class="tab-content">
          <h3 class="section-title">每日统计 (近30天)</h3>
          <div class="daily-list">
            <div class="daily-header">
              <span>日期</span>
              <span>游戏</span>
              <span>活跃</span>
              <span>积分</span>
            </div>
            <div v-for="day in dailyStats" :key="day.date" class="daily-row">
              <span>{{ day.date }}</span>
              <span>{{ day.game_count }}</span>
              <span>{{ day.active_users }}</span>
              <span>{{ formatNumber(day.total_score) }}</span>
            </div>
          </div>
        </div>

        <!-- 词库统计 -->
        <div v-else-if="currentTab === 'vocab'" class="tab-content">
          <h3 class="section-title">词库使用分析</h3>
          <div class="vocab-list">
            <div v-for="v in vocabAnalysis" :key="v.vocab_group" class="vocab-row">
              <div class="vocab-info">
                <span class="vocab-name">{{ getGroupName(v.vocab_group) }}</span>
                <span class="vocab-code">({{ v.vocab_group }})</span>
              </div>
              <div class="vocab-stats">
                <span class="vocab-games">{{ v.total_games }} 局</span>
                <span class="vocab-users">{{ v.unique_players }} 人</span>
                <span class="vocab-words">{{ v.total_words }} 词</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 活跃时段 -->
        <div v-else-if="currentTab === 'hourly'" class="tab-content">
          <h3 class="section-title">每小时活跃分布 (近7天)</h3>
          <div class="hourly-chart">
            <div v-for="h in hourlyStats" :key="h.hour" class="hour-bar">
              <div class="hour-fill" :style="{ height: getHourHeight(h.game_count) + '%' }"></div>
              <span class="hour-label">{{ h.hour }}时</span>
              <span class="hour-value">{{ h.game_count }}</span>
            </div>
          </div>
        </div>

        <!-- 设置 -->
        <div v-else-if="currentTab === 'settings'" class="tab-content">
          <h3 class="section-title">修改管理员密码</h3>
          <div class="password-form">
            <div class="form-group">
              <label>当前密码</label>
              <input 
                v-model="passwordForm.oldPassword" 
                type="password" 
                placeholder="请输入当前密码"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label>新密码</label>
              <input 
                v-model="passwordForm.newPassword" 
                type="password" 
                placeholder="请输入新密码（至少6位）"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label>确认新密码</label>
              <input 
                v-model="passwordForm.confirmPassword" 
                type="password" 
                placeholder="请再次输入新密码"
                class="form-input"
              />
            </div>
            <p v-if="passwordError" class="error-msg">{{ passwordError }}</p>
            <p v-if="passwordSuccess" class="success-msg">{{ passwordSuccess }}</p>
            <button 
              @click="changePassword" 
              :disabled="passwordLoading"
              class="submit-btn"
            >
              {{ passwordLoading ? '修改中...' : '修改密码' }}
            </button>
          </div>

          <h3 class="section-title">密码状态</h3>
          <div class="password-status">
            <span v-if="passwordStatus.has_custom_password" class="status-badge custom">已设置自定义密码</span>
            <span v-else class="status-badge default">使用默认密码</span>
          </div>
        </div>
      </template>
    </div>

    <!-- 用户详情弹窗 -->
    <div v-if="selectedUser" class="modal-overlay" @click.self="selectedUser = null">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-avatar">{{ selectedUser.avatar }}</span>
          <div class="modal-user-info">
            <h3>{{ selectedUser.nickname }}</h3>
            <p>{{ selectedUser.id }}</p>
          </div>
          <button class="modal-close" @click="selectedUser = null">×</button>
        </div>
        <div class="modal-body">
          <div v-if="userDetailLoading" class="loading-state">
            <div class="loading-spinner"></div>
            <p>加载中...</p>
          </div>
          <template v-else-if="userDetail">
            <h4>游戏统计</h4>
            <div class="detail-stats">
              <div class="detail-stat">
                <span class="label">闯关最高</span>
                <span class="value">{{ userDetail.stats?.campaign?.max_level || 0 }} 关</span>
              </div>
              <div class="detail-stat">
                <span class="label">闯关积分</span>
                <span class="value">{{ userDetail.stats?.campaign?.total_score || 0 }}</span>
              </div>
              <div class="detail-stat">
                <span class="label">无限最高</span>
                <span class="value">{{ userDetail.stats?.endless?.max_level || 0 }} 关</span>
              </div>
              <div class="detail-stat">
                <span class="label">计时最多</span>
                <span class="value">{{ userDetail.stats?.timed?.max_words || 0 }} 词</span>
              </div>
              <div class="detail-stat">
                <span class="label">PK胜场</span>
                <span class="value">{{ userDetail.stats?.pk?.wins || 0 }} 场</span>
              </div>
              <div class="detail-stat">
                <span class="label">PK胜率</span>
                <span class="value">{{ getPkWinRate(userDetail.stats?.pk) }}%</span>
              </div>
            </div>

            <h4>功能使用</h4>
            <div v-if="userDetail.feature_usage && userDetail.feature_usage.length" class="feature-list">
              <div v-for="f in userDetail.feature_usage" :key="f.feature_name" class="feature-row">
                <span>{{ getFeatureName(f.feature_name) }}</span>
                <span>{{ f.usage_count }} 次</span>
              </div>
            </div>
            <div v-else class="empty-state">暂无使用记录</div>

            <h4>最近游戏</h4>
            <div v-if="userDetail.recent_records && userDetail.recent_records.length" class="records-list">
              <div v-for="r in userDetail.recent_records.slice(0, 5)" :key="r.id" class="record-row">
                <span class="record-mode">{{ getModeIcon(r.game_mode) }}</span>
                <span class="record-group">{{ getGroupName(r.vocab_group) }}</span>
                <span class="record-score">{{ r.score }} 分</span>
                <span class="record-date">{{ formatDateTime(r.created_at) }}</span>
              </div>
            </div>
            <div v-else class="empty-state">暂无游戏记录</div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { adminApi } from '../api/index.js'

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
const platformStats = ref({})
const energyStats = ref({})
const propsStats = ref({})
const eventStats = ref({})
const retentionStats = ref({})
const hourlyStats = ref([])
const topPlayers = ref([])
const vocabAnalysis = ref([])

// 用户详情
const selectedUser = ref(null)
const userDetail = ref(null)
const userDetailLoading = ref(false)

// 分页
const pageSize = 20
const currentPage = ref(0)

// 选项卡
const tabs = [
  { code: 'overview', name: '概览', icon: '📊' },
  { code: 'users', name: '用户', icon: '👥' },
  { code: 'top', name: '排行', icon: '🏆' },
  { code: 'platform', name: '终端', icon: '📱' },
  { code: 'behavior', name: '行为', icon: '🔍' },
  { code: 'retention', name: '留存', icon: '📉' },
  { code: 'vocab', name: '词库', icon: '📚' },
  { code: 'hourly', name: '时段', icon: '⏰' },
  { code: 'daily', name: '每日', icon: '📅' },
  { code: 'settings', name: '设置', icon: '⚙️' },
]

// 密码修改相关
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})
const passwordLoading = ref(false)
const passwordError = ref('')
const passwordSuccess = ref('')
const passwordStatus = ref({ has_custom_password: false })

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
  junior: '初中词汇', junior_all: '初中全部',
  junior7_1: '七年级上册', junior7_2: '七年级下册',
  junior8_1: '八年级上册', junior8_2: '八年级下册',
  junior9: '九年级全册',
  senior: '高中词汇', senior_all: '高中全部',
  senior1: '必修1', senior2: '必修2', senior3: '必修3',
  senior4: '必修4', senior5: '必修5',
  ket: 'KET考试', pet: 'PET考试',
  cet4: '大学四级', cet6: '大学六级',
  postgrad: '考研词汇', ielts: '雅思',
  toefl: '托福', gre: 'GRE',
  primary: '小学词汇', primary_all: '小学全部'
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

function getPlatformIcon(platform) {
  const icons = { web: '🌐', wechat: '💬', ios: '📱', android: '🤖' }
  return icons[platform] || '📱'
}

function getPlatformName(platform) {
  const names = { web: '网页版', wechat: '微信小程序', ios: 'iOS App', android: 'Android App' }
  return names[platform] || platform
}

function getDeviceIcon(device) {
  const icons = { desktop: '💻', mobile: '📱', tablet: '📋' }
  return icons[device] || '📱'
}

function getPropIcon(prop) {
  const icons = { hint: '💡', speak: '🔊', translation: '📖' }
  return icons[prop] || '🎁'
}

function getPropName(prop) {
  const names = { hint: '提示字母', speak: '发音道具', translation: '显示翻译' }
  return names[prop] || prop
}

function getClaimTypeName(type) {
  const names = { free_claim: '免费领取', ad_reward: '广告奖励', daily_bonus: '每日奖励', level_reward: '通关奖励' }
  return names[type] || type
}

function getEventName(event) {
  const names = {
    claim_energy: '领取体力',
    use_prop_hint: '使用提示',
    use_prop_speak: '使用发音',
    complete_level: '完成关卡',
    start_game: '开始游戏'
  }
  return names[event] || event
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

function formatDateTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`
}

function getPkWinRate(pk) {
  if (!pk) return 0
  const total = (pk.wins || 0) + (pk.draws || 0) + (pk.losses || 0)
  if (total === 0) return 0
  return Math.round((pk.wins || 0) / total * 100)
}

function getHourHeight(count) {
  const max = Math.max(...hourlyStats.value.map(h => h.game_count || 0), 1)
  return Math.round((count / max) * 100)
}

async function authenticate() {
  authError.value = ''
  try {
    await adminApi.getOverview(adminToken.value)
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
    
    // 并行加载所有数据
    const [
      overviewData,
      usersData,
      dailyData,
      platformData,
      energyData,
      propsData,
      eventData,
      retentionData,
      hourlyData,
      topData,
      vocabData
    ] = await Promise.all([
      adminApi.getOverview(token).catch(() => ({})),
      adminApi.getUsers(token, 1, pageSize).catch(() => ({ users: [], total: 0 })),
      adminApi.getDailyStats(token, 30).catch(() => ({ stats: [] })),
      adminApi.getPlatformStats(token).catch(() => ({})),
      adminApi.getEnergyStats(token).catch(() => ({})),
      adminApi.getPropsStats(token).catch(() => ({})),
      adminApi.getEventStats(token).catch(() => ({ stats: [] })),
      adminApi.getRetentionStats(token).catch(() => ({})),
      adminApi.getHourlyStats(token).catch(() => ({ hourly: [] })),
      adminApi.getTopPlayers(token).catch(() => ({ players: [] })),
      adminApi.getVocabAnalysis(token).catch(() => ({ vocab_groups: [] })),
    ])
    
    overview.value = overviewData.overview || {}
    modeStats.value = overviewData.mode_stats || []
    groupStats.value = overviewData.group_stats || []
    users.value = usersData.users || []
    userTotal.value = usersData.total || 0
    dailyStats.value = dailyData.stats || []
    platformStats.value = platformData || {}
    energyStats.value = energyData || {}
    propsStats.value = propsData || {}
    eventStats.value = eventData || {}
    retentionStats.value = retentionData || {}
    hourlyStats.value = hourlyData.hourly || []
    topPlayers.value = topData.players || []
    vocabAnalysis.value = vocabData.vocab_groups || []
    
    // 加载密码状态
    await loadPasswordStatus()
    
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
  const usersData = await adminApi.getUsers(token, currentPage.value + 1, pageSize)
  users.value = usersData.users || []
  userTotal.value = usersData.total || 0
}

async function showUserDetail(user) {
  selectedUser.value = user
  userDetailLoading.value = true
  userDetail.value = null
  
  try {
    const token = adminToken.value || localStorage.getItem('admin_token')
    userDetail.value = await adminApi.getUserDetail(token, user.id)
  } catch (e) {
    console.error('加载用户详情失败:', e)
  } finally {
    userDetailLoading.value = false
  }
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

async function loadPasswordStatus() {
  try {
    passwordStatus.value = await adminApi.getPasswordStatus()
  } catch (e) {
    console.error('获取密码状态失败:', e)
  }
}

async function changePassword() {
  passwordError.value = ''
  passwordSuccess.value = ''

  // 验证
  if (!passwordForm.value.oldPassword) {
    passwordError.value = '请输入当前密码'
    return
  }
  if (!passwordForm.value.newPassword) {
    passwordError.value = '请输入新密码'
    return
  }
  if (passwordForm.value.newPassword.length < 6) {
    passwordError.value = '新密码至少6位'
    return
  }
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    passwordError.value = '两次输入的新密码不一致'
    return
  }

  passwordLoading.value = true
  try {
    await adminApi.changePassword(
      passwordForm.value.oldPassword,
      passwordForm.value.newPassword
    )
    passwordSuccess.value = '密码修改成功！请使用新密码重新登录'
    
    // 清空表单
    passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
    
    // 更新本地存储的 token
    localStorage.setItem('admin_token', passwordForm.value.newPassword)
    adminToken.value = passwordForm.value.newPassword
    
    // 刷新密码状态
    await loadPasswordStatus()
  } catch (e) {
    if (e.response?.data?.detail) {
      passwordError.value = e.response.data.detail
    } else {
      passwordError.value = '修改失败: ' + (e.message || '未知错误')
    }
  } finally {
    passwordLoading.value = false
  }
}

onMounted(() => {
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
  padding: 12px;
  box-sizing: border-box;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.header-section {
  text-align: center;
  padding: 16px 12px 8px;
}

.title {
  font-size: 1.8rem;
  font-weight: 900;
  color: #5D5D5D;
  text-shadow: 0 3px 0 rgba(0,0,0,0.15);
  margin: 0;
}

.subtitle {
  font-size: 0.85rem;
  color: rgba(255,255,255,0.9);
  margin: 4px 0 0;
}

.main-card {
  flex: 1;
  background: rgba(255,255,255,0.98);
  border-radius: 20px;
  padding: 12px;
  box-shadow: 0 8px 0 rgba(0,0,0,0.08);
  max-width: 600px;
  width: 100%;
  margin: 0 auto;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.nav-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.back-btn {
  padding: 8px 12px;
  background: linear-gradient(180deg, #f3f4f6, #e5e7eb);
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 700;
  color: #6b7280;
  text-decoration: none;
}

.refresh-btn-small {
  padding: 8px 12px;
  background: linear-gradient(180deg, #FFB6C1, #FFB6C1);
  border: none;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 700;
  color: #5D5D5D;
  cursor: pointer;
}

.refresh-btn-small:disabled {
  opacity: 0.6;
}

/* 认证区 */
.auth-section {
  text-align: center;
  padding: 40px 16px;
}

.auth-section h3 {
  font-size: 1.1rem;
  margin-bottom: 16px;
  color: #374151;
}

.auth-form {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
}

.auth-input {
  padding: 10px 14px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 1rem;
  width: 180px;
}

.auth-btn {
  padding: 10px 20px;
  background: linear-gradient(180deg, #60a5fa, #3b82f6);
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 700;
  color: #5D5D5D;
  cursor: pointer;
}

.auth-error {
  color: #ef4444;
  margin-top: 12px;
  font-size: 0.85rem;
}

/* 选项卡 - 可滚动 */
.tabs-container {
  overflow-x: auto;
  margin: 0 -12px 12px;
  padding: 0 12px;
  -webkit-overflow-scrolling: touch;
}

.tabs {
  display: flex;
  gap: 6px;
  min-width: max-content;
}

.tab-btn {
  padding: 8px 12px;
  background: #f3f4f6;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  min-width: 50px;
}

.tab-icon {
  font-size: 1.1rem;
}

.tab-name {
  font-size: 0.65rem;
}

.tab-btn.active {
  background: linear-gradient(180deg, #FFB6C1, #FFB6C1);
  border-color: #FF69B4;
  color: #5D5D5D;
}

/* 加载中 */
.loading-state {
  text-align: center;
  padding: 40px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #FFB6C1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 内容区 */
.tab-content {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 20px;
}

.section-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: #374151;
  margin: 16px 0 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.section-title:first-child {
  margin-top: 0;
}

.section-desc {
  font-size: 0.75rem;
  color: #6b7280;
  margin: -6px 0 10px;
}

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.stat-card {
  text-align: center;
  padding: 12px 8px;
  border-radius: 10px;
}

.stat-icon {
  font-size: 1.2rem;
  margin-bottom: 4px;
}

.stat-card.blue { background: linear-gradient(135deg, #dbeafe, #bfdbfe); }
.stat-card.green { background: linear-gradient(135deg, #d1fae5, #a7f3d0); }
.stat-card.purple { background: linear-gradient(135deg, #ede9fe, #ddd6fe); }
.stat-card.orange { background: linear-gradient(135deg, #fed7aa, #fdba74); }
.stat-card.pink { background: linear-gradient(135deg, #fce7f3, #fbcfe8); }
.stat-card.teal { background: linear-gradient(135deg, #ccfbf1, #99f6e4); }

.stat-value {
  font-size: 1.3rem;
  font-weight: 900;
  color: #374151;
}

.stat-label {
  font-size: 0.65rem;
  color: #6b7280;
  margin-top: 2px;
}

/* 模式统计列表 */
.mode-stats-list, .group-stats-list, .feature-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mode-stat-row {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 10px;
  flex-wrap: nowrap;
  gap: 8px;
}

.group-stat-row, .feature-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 10px;
}

.mode-name {
  flex: 0 0 auto;
  font-weight: 600;
  color: #374151;
  font-size: 0.85rem;
  white-space: nowrap;
}

.mode-value {
  flex: 1 1 auto;
  text-align: center;
  font-size: 0.8rem;
  color: #6b7280;
  white-space: nowrap;
}

.mode-score {
  flex: 0 0 auto;
  text-align: right;
  font-weight: 700;
  color: #FF69B4;
  font-size: 0.8rem;
  white-space: nowrap;
}

.group-name, .feature-name {
  font-weight: 600;
  color: #374151;
}

.group-games, .feature-users {
  font-size: 0.85rem;
  color: #6b7280;
}

.group-score, .feature-count {
  font-weight: 700;
  color: #FF69B4;
}

/* 用户列表 */
.users-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.user-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #f9fafb;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.user-row:active {
  background: #e5e7eb;
}

.user-avatar {
  font-size: 1.5rem;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  color: #374151;
  font-size: 0.85rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-id {
  font-size: 0.65rem;
  color: #9ca3af;
  font-family: monospace;
}

.user-meta {
  text-align: right;
}

.user-plays {
  font-weight: 600;
  color: #FF69B4;
  font-size: 0.8rem;
}

.user-date {
  font-size: 0.65rem;
  color: #9ca3af;
}

.arrow {
  color: #9ca3af;
  font-size: 1.2rem;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}

.pagination button {
  padding: 6px 12px;
  background: #f3f4f6;
  border: 2px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination span {
  font-size: 0.8rem;
  color: #6b7280;
}

/* 顶级玩家 */
.top-players-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.player-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #f9fafb;
  border-radius: 8px;
}

.player-rank {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-weight: 700;
  font-size: 0.75rem;
  background: #e5e7eb;
  color: #6b7280;
}

.player-rank.gold { background: #fef3c7; color: #d97706; }
.player-rank.silver { background: #e5e7eb; color: #6b7280; }
.player-rank.bronze { background: #fed7aa; color: #c2410c; }

.player-avatar {
  font-size: 1.3rem;
}

.player-info {
  flex: 1;
}

.player-name {
  font-weight: 600;
  font-size: 0.85rem;
}

.player-games {
  font-size: 0.7rem;
  color: #6b7280;
}

.player-score {
  font-weight: 700;
  color: #FF69B4;
  font-size: 0.85rem;
}

/* 平台/设备/浏览器/系统列表 */
.platform-list, .device-list, .browser-list, .os-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.platform-row, .device-row, .browser-row, .os-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: #f9fafb;
  border-radius: 8px;
  font-size: 0.8rem;
}

.platform-icon, .device-icon {
  font-size: 1.1rem;
}

.platform-name, .device-name, .browser-name, .os-name {
  flex: 1;
  font-weight: 600;
}

.platform-count, .device-count, .browser-count, .os-count {
  color: #6b7280;
}

.platform-users {
  color: #FF69B4;
  font-weight: 600;
}

/* 体力/道具/事件统计 */
.energy-stats, .props-stats, .event-stats {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.energy-row, .prop-row, .event-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: #f9fafb;
  border-radius: 8px;
  font-size: 0.8rem;
}

.energy-type, .prop-name, .event-name {
  flex: 1;
  font-weight: 600;
}

.prop-icon {
  font-size: 1.1rem;
}

.energy-count, .prop-count, .event-count {
  color: #6b7280;
}

.energy-amount {
  color: #10b981;
  font-weight: 600;
}

.energy-users, .prop-users, .event-users {
  color: #FF69B4;
}

/* 留存分析 */
.dropoff-list, .retention-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.dropoff-row, .retention-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  background: #f9fafb;
  border-radius: 8px;
  font-size: 0.8rem;
}

.dropoff-levels {
  font-weight: 600;
}

.dropoff-stats {
  display: flex;
  gap: 12px;
}

.dropoff-players {
  color: #6b7280;
}

.dropoff-rate {
  color: #f59e0b;
  font-weight: 600;
}

.dropoff-rate.high {
  color: #ef4444;
}

.retention-level {
  font-weight: 600;
}

.retention-players {
  color: #6b7280;
}

.retention-stars {
  color: #f59e0b;
}

/* 每日统计 */
.daily-list {
  font-size: 0.75rem;
}

.daily-header, .daily-row {
  display: grid;
  grid-template-columns: 1.2fr 1fr 1fr 1fr;
  gap: 6px;
  padding: 6px 8px;
}

.daily-header {
  background: #e5e7eb;
  border-radius: 6px;
  font-weight: 700;
  color: #374151;
}

.daily-row {
  background: #f9fafb;
  border-radius: 4px;
  margin-top: 3px;
}

/* 词库统计 */
.vocab-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.vocab-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  background: #f9fafb;
  border-radius: 8px;
  font-size: 0.8rem;
}

.vocab-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.vocab-name {
  font-weight: 600;
}

.vocab-code {
  font-size: 0.7rem;
  color: #9ca3af;
}

.vocab-stats {
  display: flex;
  gap: 10px;
  font-size: 0.75rem;
  color: #6b7280;
}

.vocab-games {
  color: #FF69B4;
  font-weight: 600;
}

/* 每小时活跃图 */
.hourly-chart {
  display: flex;
  gap: 4px;
  height: 150px;
  align-items: flex-end;
  padding: 10px 0;
  overflow-x: auto;
}

.hour-bar {
  flex: 1;
  min-width: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  height: 100%;
}

.hour-fill {
  width: 100%;
  background: linear-gradient(180deg, #FFB6C1, #FFB6C1);
  border-radius: 4px 4px 0 0;
  position: absolute;
  bottom: 36px;
  transition: height 0.3s;
}

.hour-label {
  position: absolute;
  bottom: 18px;
  font-size: 0.6rem;
  color: #6b7280;
}

.hour-value {
  position: absolute;
  bottom: 0;
  font-size: 0.6rem;
  color: #FF69B4;
  font-weight: 600;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 20px;
  color: #9ca3af;
  font-size: 0.85rem;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.modal-content {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 400px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #5D5D5D;
}

.modal-avatar {
  font-size: 2rem;
}

.modal-user-info {
  flex: 1;
}

.modal-user-info h3 {
  margin: 0;
  font-size: 1.1rem;
}

.modal-user-info p {
  margin: 4px 0 0;
  font-size: 0.7rem;
  opacity: 0.8;
  font-family: monospace;
}

.modal-close {
  background: none;
  border: none;
  color: #5D5D5D;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.modal-body {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.modal-body h4 {
  font-size: 0.9rem;
  margin: 16px 0 8px;
  color: #374151;
}

.modal-body h4:first-child {
  margin-top: 0;
}

.detail-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.detail-stat {
  padding: 10px;
  background: #f9fafb;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}

.detail-stat .label {
  font-size: 0.7rem;
  color: #6b7280;
}

.detail-stat .value {
  font-size: 1rem;
  font-weight: 700;
  color: #374151;
}

.feature-list, .records-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.feature-row, .record-row {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  background: #f9fafb;
  border-radius: 6px;
  font-size: 0.8rem;
}

.record-row {
  display: grid;
  grid-template-columns: auto 1fr auto auto;
  gap: 8px;
  align-items: center;
}

.record-mode {
  font-size: 1rem;
}

.record-group {
  font-size: 0.75rem;
  color: #6b7280;
}

.record-score {
  font-weight: 600;
  color: #FF69B4;
}

.record-date {
  font-size: 0.7rem;
  color: #9ca3af;
}

/* 密码修改表单 */
.password-form {
  background: #f9fafb;
  border-radius: 12px;
  padding: 16px;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.9rem;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #FFB6C1;
}

.error-msg {
  color: #ef4444;
  font-size: 0.8rem;
  margin: 8px 0;
}

.success-msg {
  color: #10b981;
  font-size: 0.8rem;
  margin: 8px 0;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background: linear-gradient(180deg, #FFB6C1, #FFB6C1);
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 700;
  color: #5D5D5D;
  cursor: pointer;
  margin-top: 8px;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.password-status {
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
}

.status-badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
}

.status-badge.custom {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.default {
  background: #fef3c7;
  color: #92400e;
}

/* 响应式 - 中等屏幕 */
@media (max-width: 400px) {
  .mode-stat-row {
    padding: 8px 10px;
    gap: 6px;
  }
  
  .mode-name {
    font-size: 0.8rem;
  }
  
  .mode-value {
    font-size: 0.75rem;
  }
  
  .mode-score {
    font-size: 0.75rem;
  }
}

/* 响应式 - 窄屏幕 */
@media (max-width: 360px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .stat-value {
    font-size: 1.1rem;
  }
  
  .tabs {
    gap: 4px;
  }
  
  .tab-btn {
    padding: 6px 8px;
    min-width: 42px;
  }
  
  .mode-stat-row {
    padding: 6px 8px;
    gap: 4px;
  }
  
  .mode-name {
    font-size: 0.75rem;
  }
  
  .mode-value {
    font-size: 0.7rem;
  }
  
  .mode-score {
    font-size: 0.7rem;
  }
}

/* 响应式 - 超窄屏幕 */
@media (max-width: 320px) {
  .mode-stat-row {
    padding: 5px 6px;
    gap: 3px;
  }
  
  .mode-name {
    font-size: 0.7rem;
  }
  
  .mode-value {
    font-size: 0.65rem;
  }
  
  .mode-score {
    font-size: 0.65rem;
    min-width: 50px;
  }
}
</style>
