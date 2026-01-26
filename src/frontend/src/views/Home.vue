<template>
  <div class="home-screen">
    <!-- 标题区 - 卡通风格 -->
    <div class="header-section">
      <div class="logo-area">
        <div class="stars-left">🌟</div>
        <h1 class="title">我爱填单词</h1>
        <div class="stars-right">🌟</div>
      </div>
      <p class="subtitle">WordCross · 趣味英语学习</p>
      
      <!-- 用户信息栏 -->
      <div class="user-info-bar">
        <div class="user-avatar">{{ userAvatar }}</div>
        <div class="user-name">{{ userName }}</div>
        <div class="user-stats">
          <span class="stat-item" title="体力">⚡{{ userEnergy }}</span>
          <span class="stat-item" title="提示道具">💡{{ hintCount }}</span>
          <span class="stat-item" title="翻译道具">📖{{ translateCount }}</span>
        </div>
      </div>
    </div>

    <!-- 主卡片 -->
    <div class="main-card">
      <!-- 第一步：选择游戏模式 -->
      <div v-if="currentStep === 'mode'" class="mode-selection">
        <h2 class="section-title">🎮 选择游戏模式</h2>
        <div class="mode-grid">
          <!-- 闯关模式 -->
          <button @click="selectMode('campaign')" class="mode-btn campaign">
            <span class="mode-icon">🏰</span>
            <div class="mode-info">
              <div class="mode-name">闯关模式</div>
              <div class="mode-desc">词库闯关</div>
            </div>
          </button>

          <!-- 无限模式 -->
          <button @click="selectMode('endless')" class="mode-btn endless">
            <span class="mode-icon">♾️</span>
            <div class="mode-info">
              <div class="mode-name">无限模式</div>
              <div class="mode-desc">随机关卡</div>
            </div>
          </button>

          <!-- 计时模式 -->
          <button @click="selectMode('timed')" class="mode-btn timed">
            <span class="mode-icon">⏱️</span>
            <div class="mode-info">
              <div class="mode-name">计时模式</div>
              <div class="mode-desc">限时挑战</div>
            </div>
          </button>

          <!-- PK模式 -->
          <button @click="selectMode('pk')" class="mode-btn pk">
            <span class="mode-icon">⚔️</span>
            <div class="mode-info">
              <div class="mode-name">PK模式</div>
              <div class="mode-desc">在线对战</div>
            </div>
          </button>
        </div>
        
        <!-- 测试模式和重置按钮并排 -->
        <div class="test-reset-row">
          <router-link to="/test-mode" class="test-mode-card">
            <span class="test-mode-icon">🧪</span>
            <span class="test-mode-text">测试模式</span>
            <span class="test-mode-arrow">›</span>
          </router-link>
          <button @click="resetAllData" class="reset-all-btn">
            <span class="reset-icon">🔄</span>
            <span class="reset-text">重置全部</span>
          </button>
        </div>
        
        <!-- 排行榜入口 - 放在主卡片内 -->
        <router-link to="/leaderboard" class="leaderboard-card">
          <span class="leaderboard-icon">🏆</span>
          <span class="leaderboard-text">排行榜</span>
          <span class="leaderboard-arrow">›</span>
        </router-link>
        
        <!-- 设置入口 -->
        <router-link to="/settings" class="settings-card">
          <span class="settings-icon">⚙️</span>
          <span class="settings-text">设置</span>
          <span class="settings-arrow">›</span>
        </router-link>
      </div>

      <!-- 第二步：选择时间（计时/PK模式） -->
      <div v-else-if="currentStep === 'duration'" class="duration-selection">
        <div class="selection-header">
          <button @click="goBack" class="back-btn">← 返回</button>
          <h2 class="section-title">⏱️ 选择时间</h2>
        </div>

        <div class="duration-grid">
          <button
            v-for="opt in durationOptions"
            :key="opt.value"
            @click="selectDuration(opt.value)"
            :class="['duration-btn', { active: selectedDuration === opt.value }]"
          >
            <span class="duration-icon">{{ opt.icon }}</span>
            <span class="duration-label">{{ opt.label }}</span>
          </button>
        </div>

        <div class="duration-hint">
          <span class="hint-icon">💡</span>
          <span class="hint-text">选择游戏总时长</span>
        </div>
      </div>

      <!-- 第三步：选择难度（无限/计时/PK模式） -->
      <div v-else-if="currentStep === 'difficulty'" class="difficulty-selection">
        <div class="selection-header">
          <button @click="goBack" class="back-btn">← 返回</button>
          <h2 class="section-title">⚡ 选择难度</h2>
        </div>

        <!-- 显示已选时间（计时/PK模式） -->
        <div v-if="selectedMode === 'timed' || selectedMode === 'pk'" class="selected-duration-banner">
          <span class="banner-label">已选时间：</span>
          <span class="banner-value duration">
            {{ durationOptions.find(d => d.value === selectedDuration)?.label }}
          </span>
        </div>

        <div class="difficulty-grid">
          <button
            v-for="diff in difficultyOptions"
            :key="diff.code"
            @click="selectDifficulty(diff.code)"
            :class="['difficulty-btn', diff.code]"
          >
            <span class="diff-icon">{{ diff.icon }}</span>
            <div class="diff-info">
              <div class="diff-name">{{ diff.name }}</div>
              <div class="diff-desc">{{ diff.desc }}</div>
            </div>
          </button>
        </div>

        <div class="difficulty-hint">
          <span class="hint-icon">💡</span>
          <span class="hint-text">难度决定单词长度范围</span>
        </div>
      </div>

      <!-- 第三步：选择词库 -->
      <div v-else-if="currentStep === 'group'" class="group-selection">
        <div class="selection-header">
          <button @click="goBack" class="back-btn">← 返回</button>
          <h2 class="section-title">📚 选择词库</h2>
        </div>
        
        <!-- 显示已选难度（无限/计时/PK模式） -->
        <div v-if="needsDifficultyFirst" class="selected-difficulty-banner">
          <span class="banner-label">已选难度：</span>
          <span :class="['banner-value', selectedDifficulty]">
            {{ difficultyOptions.find(d => d.code === selectedDifficulty)?.name }}
          </span>
        </div>

        <div class="group-grid">
          <button
            v-for="group in gameStore.groups"
            :key="group.code"
            @click="selectGroup(group)"
            class="group-btn"
          >
            <span class="group-icon">{{ group.icon }}</span>
            <span class="group-name">{{ group.name }}</span>
            <span v-if="group.hasSubGroups && canSelectSubGroup" class="group-arrow">›</span>
          </button>
        </div>
      </div>

      <!-- 第二步半：选择细分类（仅闯关/无限模式） -->
      <div v-else-if="currentStep === 'subgroup'" class="group-selection">
        <div class="selection-header">
          <button @click="goBack" class="back-btn">← 返回</button>
          <h2 class="section-title">📂 选择{{ selectedGroupData?.name }}细分</h2>
        </div>

        <div class="group-grid subgroup-grid">
          <button
            v-for="sub in selectedGroupData?.subGroups || []"
            :key="sub.code"
            @click="selectSubGroup(sub.code)"
            :class="['group-btn', { 'all-btn': sub.code.endsWith('_all') }]"
          >
            <span class="group-icon">{{ sub.icon }}</span>
            <span class="group-name">{{ sub.name }}</span>
          </button>
        </div>
      </div>

      <!-- 第三步：闯关模式 - 选择关卡 -->
      <div v-else-if="currentStep === 'level'" class="level-selection">
        <div class="selection-header">
          <button @click="goBack" class="back-btn">← 返回</button>
          <h2 class="section-title">🏰 选择关卡</h2>
        </div>
        
        <div class="level-info-banner">
          <span class="banner-icon">📚</span>
          <span class="banner-text">{{ getGroupName(selectedGroup) }}</span>
          <span class="banner-progress">{{ getCurrentProgress }}</span>
        </div>

        <!-- 关卡主区域：左右翻页按钮 + 中间滚动区 -->
        <div class="level-main-area">
          <!-- 上一页按钮 -->
          <button 
            class="page-nav-btn prev" 
            @click="prevPage"
            :disabled="currentPage <= 1"
          >
            ‹
          </button>
          
          <!-- 关卡滚动区域（每屏20关，共5屏=100关） -->
          <div class="level-scroll-container">
            <div class="level-grid">
              <button
                v-for="level in currentPageLevels"
                :key="level"
                @click="startCampaignLevel(level)"
                :class="['level-btn', getLevelClass(level)]"
              >
                <span class="level-number">{{ level }}</span>
                <span class="level-stars">{{ getLevelStars(level) }}</span>
                <span class="level-status">{{ getLevelStatus(level) }}</span>
              </button>
            </div>
          </div>
          
          <!-- 下一页按钮 -->
          <button 
            class="page-nav-btn next" 
            @click="nextPage"
            :disabled="currentPage >= totalPages"
          >
            ›
          </button>
        </div>

        <!-- 底部范围分页器 -->
        <div class="range-pagination">
          <span class="range-label">{{ getRangeLabel }}</span>
          <div class="range-buttons">
            <!-- 第一个范围 -->
            <button 
              v-if="showFirstRange"
              @click="currentPage = 1"
              :class="['range-btn', { active: currentPage === 1 }]"
            >1-100</button>
            
            <!-- 左侧省略号 -->
            <span v-if="showLeftEllipsis" class="range-ellipsis">...</span>
            
            <!-- 中间的范围按钮 -->
            <button 
              v-for="page in visiblePages"
              :key="page"
              @click="currentPage = page"
              :class="['range-btn', { active: currentPage === page }]"
            >{{ getRangeText(page) }}</button>
            
            <!-- 右侧省略号 -->
            <span v-if="showRightEllipsis" class="range-ellipsis">...</span>
            
            <!-- 最后一个范围 -->
            <button 
              v-if="showLastRange"
              @click="currentPage = totalPages"
              :class="['range-btn', { active: currentPage === totalPages }]"
            >{{ getRangeText(totalPages) }}</button>
          </div>
        </div>
      </div>

    </div>

    <!-- 底部装饰 -->
    <div class="footer-decoration">
      <span class="footer-icon">🎨</span>
      <span class="footer-icon">📖</span>
      <span class="footer-icon">✏️</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'
import { useUserStore } from '../stores/user'
import axios from 'axios'

const router = useRouter()
const gameStore = useGameStore()
const userStore = useUserStore()

// 用户信息
const userAvatar = computed(() => userStore.avatar || '😊')
const userName = computed(() => userStore.nickname || '游客')

// 体力值
const userEnergy = ref(100)

// 道具数量
const hintCount = ref(20)
const translateCount = ref(20)

// 加载用户数据（含体力恢复：每分钟发放1点）
async function loadUserData() {
  const now = Date.now()
  
  // 加载体力（含恢复计算：每分钟发放1点）
  try {
    const saved = localStorage.getItem('user_energy')
    if (saved) {
      const energy = JSON.parse(saved)
      let currentEnergy = energy.value ?? 200
      const lastGrantTime = energy.lastGrantTime || energy.lastUpdate || now
      
      // 计算距离上次发放的时间差（毫秒）
      const timeDiff = now - lastGrantTime
      const minutesPassed = Math.floor(timeDiff / (1000 * 60))  // 完整分钟数
      
      // 每分钟发放1点体力
      if (minutesPassed >= 1) {
        const energyToGrant = minutesPassed  // 每分钟1点
        const newEnergy = Math.min(currentEnergy + energyToGrant, 200)  // 体力上限200
        
        // 如果有恢复，更新体力
        if (newEnergy > currentEnergy) {
          console.log(`距上次发放${minutesPassed}分钟，恢复${newEnergy - currentEnergy}点体力`)
          currentEnergy = newEnergy
          
          // 保存到本地（更新发放时间）
          localStorage.setItem('user_energy', JSON.stringify({
            value: currentEnergy,
            lastGrantTime: now  // 记录本次发放时间
          }))
          
          // 同步到服务器
          try {
            await fetch('/api/user/energy', {
              method: 'PUT',
              headers: { 'Content-Type': 'application/json' },
              credentials: 'include',
              body: JSON.stringify({ energy: currentEnergy })
            })
          } catch (e) {
            console.error('同步恢复的体力到服务器失败:', e)
          }
        }
      }
      
      userEnergy.value = currentEnergy
    } else {
      // 首次使用，初始化为200点
      userEnergy.value = 200
      localStorage.setItem('user_energy', JSON.stringify({
        value: 200,
        lastGrantTime: now
      }))
    }
  } catch (e) {
    userEnergy.value = 200
  }
  
  // 加载道具
  try {
    const saved = localStorage.getItem('game_props')
    if (saved) {
      const props = JSON.parse(saved)
      hintCount.value = props.hintLetterCount ?? 20
      translateCount.value = props.showTranslationCount ?? 20
    }
  } catch (e) {
    hintCount.value = 20
    translateCount.value = 20
  }
}

// 步骤：mode -> duration(计时/PK) -> difficulty(无限/计时/PK) -> group -> subgroup(可选) -> level (仅闯关模式)
const currentStep = ref('mode')
const selectedMode = ref(null)
const selectedGroup = ref(null)
const selectedGroupData = ref(null) // 选中的大分类对象
const selectedSubGroup = ref(null)  // 选中的细分类
const selectedDuration = ref(180)  // 默认3分钟
const selectedDifficulty = ref('medium')  // 难度：low/medium/high

// 时间选项（计时/PK模式）
const durationOptions = [
  { value: 180, label: '3分钟', icon: '⏱️' },
  { value: 300, label: '5分钟', icon: '⏳' },
  { value: 600, label: '10分钟', icon: '🕐' }
]

// 关卡进度 (从localStorage读取)
const levelProgress = ref({})

// 难度选项
const difficultyOptions = [
  { code: 'low', name: '简单', desc: '2-4字母短词', icon: '🌱' },
  { code: 'medium', name: '中等', desc: '3-6字母词汇', icon: '🌿' },
  { code: 'high', name: '困难', desc: '5-10字母长词', icon: '🌲' }
]

// 是否需要先选难度（无限/计时/PK模式）
const needsDifficultyFirst = computed(() => {
  return selectedMode.value === 'endless' || 
         selectedMode.value === 'timed' || 
         selectedMode.value === 'pk'
})

// 关卡分页
const currentPage = ref(1)
const levelsPerPage = 100  // 每页100关（5屏滚动，每屏20关=5行x4列）

// 每个分类的关卡数量（从API获取，默认180关上限）
const groupLevelCounts = ref({})
const maxLevelsLimit = 180  // 每个分类上限180关

// 是否可以选择细分类（仅闯关/无限模式）
const canSelectSubGroup = computed(() => {
  return selectedMode.value === 'campaign' || selectedMode.value === 'endless'
})

// 获取当前分类的关卡数
const maxLevels = computed(() => {
  const groupCode = selectedGroup.value
  if (!groupCode) return 0
  // 从API获取的关卡数
  return groupLevelCounts.value[groupCode] || 0
})

// 总页数
const totalPages = computed(() => {
  return Math.ceil(maxLevels.value / levelsPerPage)
})

// 当前页的关卡列表
const currentPageLevels = computed(() => {
  const start = (currentPage.value - 1) * levelsPerPage + 1
  const end = Math.min(currentPage.value * levelsPerPage, maxLevels.value)
  const levels = []
  for (let i = start; i <= end; i++) {
    levels.push(i)
  }
  return levels
})

// 翻页函数
function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

// 获取范围文本
function getRangeText(page) {
  const start = (page - 1) * levelsPerPage + 1
  const end = Math.min(page * levelsPerPage, maxLevels.value)
  return `${start}-${end}`
}

// 当前范围标签
const getRangeLabel = computed(() => {
  const start = (currentPage.value - 1) * levelsPerPage + 1
  const end = Math.min(currentPage.value * levelsPerPage, maxLevels.value)
  return `当前: ${start}-${end}`
})

// 分页器显示逻辑（类似 1 ... 3 4 5 ... 10 的设计）
const showFirstRange = computed(() => {
  return totalPages.value > 1 && currentPage.value > 2
})

const showLastRange = computed(() => {
  return totalPages.value > 1 && currentPage.value < totalPages.value - 1
})

const showLeftEllipsis = computed(() => {
  return currentPage.value > 3
})

const showRightEllipsis = computed(() => {
  return currentPage.value < totalPages.value - 2
})

// 可见的页码（当前页前后各1页）
const visiblePages = computed(() => {
  const pages = []
  const start = Math.max(1, currentPage.value - 1)
  const end = Math.min(totalPages.value, currentPage.value + 1)
  
  for (let i = start; i <= end; i++) {
    // 如果已经显示了第一个或最后一个，跳过
    if (showFirstRange.value && i === 1) continue
    if (showLastRange.value && i === totalPages.value) continue
    pages.push(i)
  }
  return pages
})

// 当前进度
const getCurrentProgress = computed(() => {
  const groupCode = selectedGroup.value
  const progress = levelProgress.value[groupCode] || { unlocked: 1, completed: {} }
  const completedCount = Object.keys(progress.completed).length
  return `${completedCount}/${maxLevels.value}关`
})

// 加载关卡进度
onMounted(async () => {
  loadLevelProgress()
  await loadUserData()  // 异步加载用户数据（含离线体力恢复）
  loadDebugMode()
  loadGroupLevelCounts()
})

function loadLevelProgress() {
  // 从localStorage加载每个词库的关卡进度
  const loadForGroup = (code) => {
    const key = `campaign_progress_${code}`
    const saved = localStorage.getItem(key)
    if (saved) {
      levelProgress.value[code] = JSON.parse(saved)
    } else {
      levelProgress.value[code] = { unlocked: 1, completed: {} }
    }
  }
  
  gameStore.groups.forEach(group => {
    loadForGroup(group.code)
    // 也加载子分类的进度
    if (group.subGroups) {
      group.subGroups.forEach(sub => loadForGroup(sub.code))
    }
  })
}

function getGroupName(code) {
  // 先在大分类中查找
  let group = gameStore.groups.find(g => g.code === code)
  if (group) return `${group.icon} ${group.name}`
  
  // 再在子分类中查找
  for (const g of gameStore.groups) {
    if (g.subGroups) {
      const sub = g.subGroups.find(s => s.code === code)
      if (sub) return `${sub.icon} ${sub.name}`
    }
  }
  
  return code
}

function getLevelClass(level) {
  if (!selectedGroup.value) return ''
  const progress = levelProgress.value[selectedGroup.value] || { unlocked: 1, completed: {} }
  
  if (progress.completed[level]) {
    return 'completed'
  } else if (level <= progress.unlocked || debugMode.value) {
    // Debug模式下所有关卡都显示为可选
    return 'current'
  } else {
    return 'locked'
  }
}

function getLevelStars(level) {
  if (!selectedGroup.value) return ''
  const progress = levelProgress.value[selectedGroup.value] || { unlocked: 1, completed: {} }
  
  if (progress.completed[level]) {
    const stars = progress.completed[level].stars || 3
    return '⭐'.repeat(stars)
  }
  return ''
}

function getLevelStatus(level) {
  if (!selectedGroup.value) return ''
  const progress = levelProgress.value[selectedGroup.value] || { unlocked: 1, completed: {} }
  
  if (progress.completed[level]) {
    return '已通关'
  } else if (level <= progress.unlocked || debugMode.value) {
    return '挑战'
  } else {
    return '🔒'
  }
}

function selectMode(mode) {
  selectedMode.value = mode
  // 计时/PK模式先选时间，无限模式直接选难度，闯关模式直接选词库
  if (mode === 'timed' || mode === 'pk') {
    currentStep.value = 'duration'
  } else if (mode === 'endless') {
    currentStep.value = 'difficulty'
  } else {
    currentStep.value = 'group'
  }
}

// 选择时间（计时/PK模式）
function selectDuration(duration) {
  selectedDuration.value = duration
  currentStep.value = 'difficulty'
}

function selectDifficulty(difficulty) {
  selectedDifficulty.value = difficulty
  currentStep.value = 'group'
}

async function selectGroup(group) {
  selectedGroupData.value = group
  
  // 如果有细分类，且当前模式支持选细分
  if (group.hasSubGroups && canSelectSubGroup.value) {
    currentStep.value = 'subgroup'
  } else {
    // 没有细分类或计时/PK模式，直接使用大分类
    selectedGroup.value = group.code
    gameStore.currentGroup = group.code
    
    if (selectedMode.value === 'campaign') {
      // 进入关卡选择前，预加载该词库的关卡数据
      await preloadGroupLevels(group.code)
      currentStep.value = 'level'
    } else {
      startGame()
    }
  }
}

async function selectSubGroup(subCode) {
  selectedSubGroup.value = subCode
  selectedGroup.value = subCode
  gameStore.currentGroup = subCode
  
  if (selectedMode.value === 'campaign') {
    // 进入关卡选择前，预加载该词库的关卡数据
    await preloadGroupLevels(subCode)
    currentStep.value = 'level'
  } else {
    startGame()
  }
}

function startGame() {
  // 保存选择的难度
  if (selectedMode.value !== 'campaign') {
    localStorage.setItem('game_difficulty', selectedDifficulty.value)
  }
  
  // 保存选择的时间（计时/PK模式）
  if (selectedMode.value === 'timed' || selectedMode.value === 'pk') {
    localStorage.setItem('timed_duration', selectedDuration.value.toString())
  }
  
  // 保存当前词库到 localStorage（用于页面刷新后恢复）
  if (selectedGroup.value) {
    localStorage.setItem('current_group', selectedGroup.value)
  }
  
  router.push(`/game/${selectedMode.value}`)
}

// Debug模式 - 可以在设置中开启
const debugMode = ref(false)

// 关卡数据加载状态
const loadingLevels = ref(false)

// 加载debug模式设置
function loadDebugMode() {
  try {
    const saved = localStorage.getItem('game_debug_mode')
    debugMode.value = saved === 'true'
  } catch (e) {
    debugMode.value = false
  }
}

// 加载每个分类的关卡数量（从静态数据）
async function loadGroupLevelCounts() {
  try {
    const response = await fetch('/data/levels_summary.json')
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const data = await response.json()
    
    if (data && data.groups) {
      // 将分类关卡数存入groupLevelCounts
      for (const group of data.groups) {
        groupLevelCounts.value[group.group_code] = group.level_count || 0
      }
      console.log('关卡数量加载完成:', groupLevelCounts.value)
    } else {
      console.warn('levels-summary 数据格式异常:', data)
    }
  } catch (e) {
    console.warn('加载关卡数量失败:', e)
    // 使用默认值（从游戏store中按需加载）
  }
}

// 预加载指定词库的关卡数量（不再加载所有关卡数据，仅获取数量）
async function preloadGroupLevels(groupCode) {
  if (!groupCode) return
  
  loadingLevels.value = true
  try {
    // 关卡数量已经从 loadGroupLevelCounts 获取，这里只做验证
    const count = groupLevelCounts.value[groupCode]
    if (!count) {
      // 如果没有缓存，重新获取
      const levelCount = await gameStore.getGroupLevelCount(groupCode)
      if (levelCount > 0) {
        groupLevelCounts.value[groupCode] = levelCount
      }
      console.log(`词库 ${groupCode} 关卡数：${levelCount}`)
    } else {
      console.log(`词库 ${groupCode} 关卡数（已缓存）：${count}`)
    }
  } catch (e) {
    console.warn(`获取词库 ${groupCode} 关卡数失败:`, e)
  } finally {
    loadingLevels.value = false
  }
}

function startCampaignLevel(level) {
  const groupCode = selectedGroup.value
  const progress = levelProgress.value[groupCode] || { unlocked: 1, completed: {} }
  
  // Debug模式下可以选择任意关卡
  if (!debugMode.value && level > progress.unlocked) {
    return // 未解锁
  }
  
  // 保存选择的关卡和词库到 localStorage（用于页面刷新后恢复）
  localStorage.setItem(`campaign_level_${groupCode}`, level.toString())
  localStorage.setItem('current_group', groupCode)
  
  router.push(`/game/campaign`)
}

// 重置全部数据（能量+道具）- 同步到服务器
async function resetAllData() {
  // 重置能量为200点
  localStorage.setItem('user_energy', JSON.stringify({
    value: 200,
    lastGrantTime: Date.now()
  }))
  userEnergy.value = 200
  
  // 重置道具各20个
  localStorage.setItem('game_props', JSON.stringify({
    hintLetterCount: 20,
    showTranslationCount: 20
  }))
  hintCount.value = 20
  translateCount.value = 20
  
  // 同步到服务器
  try {
    await fetch('/api/user/energy', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ energy: 200 })
    })
    
    await fetch('/api/user/props', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        hintLetterCount: 20,
        showTranslationCount: 20
      })
    })
    console.log('重置数据已同步到服务器')
  } catch (e) {
    console.error('同步重置数据到服务器失败:', e)
  }
  
  alert('✅ 已重置：体力200点，道具各20个')
}

function goBack() {
  if (currentStep.value === 'level') {
    // 如果有细分，回到细分选择，否则回到大分类
    if (selectedGroupData.value?.hasSubGroups && canSelectSubGroup.value) {
      currentStep.value = 'subgroup'
      selectedGroup.value = null
      selectedSubGroup.value = null
    } else {
      currentStep.value = 'group'
      selectedGroup.value = null
      selectedGroupData.value = null
    }
  } else if (currentStep.value === 'subgroup') {
    currentStep.value = 'group'
    selectedGroupData.value = null
    selectedSubGroup.value = null
  } else if (currentStep.value === 'group') {
    // 如果是需要选难度的模式，返回难度选择
    if (needsDifficultyFirst.value) {
      currentStep.value = 'difficulty'
      selectedGroupData.value = null
    } else {
      currentStep.value = 'mode'
      selectedMode.value = null
      selectedGroupData.value = null
    }
  } else if (currentStep.value === 'difficulty') {
    // 如果是计时/PK模式，返回时间选择；无限模式返回模式选择
    if (selectedMode.value === 'timed' || selectedMode.value === 'pk') {
      currentStep.value = 'duration'
    } else {
      currentStep.value = 'mode'
      selectedMode.value = null
    }
    selectedDifficulty.value = 'medium'
  } else if (currentStep.value === 'duration') {
    currentStep.value = 'mode'
    selectedMode.value = null
    selectedDuration.value = 180
  }
}
</script>

<style scoped>
/* 首页整体布局 - 确保一屏显示 */
.home-screen {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  padding: 16px;
  box-sizing: border-box;
  position: relative;
  z-index: 1;
}

/* 标题区 - 卡通风格 */
.header-section {
  flex-shrink: 0;
  text-align: center;
  padding: 24px 20px 16px;
}

.logo-area {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 6px;
}

.stars-left, .stars-right {
  font-size: 2rem;
  animation: bounce 2s ease-in-out infinite;
}

.stars-right {
  animation-delay: 1s;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-8px) rotate(10deg); }
}

.title {
  font-size: 2.2rem;
  font-weight: 900;
  color: white;
  text-shadow: 
    0 4px 0 rgba(0,0,0,0.15),
    0 6px 20px rgba(0, 0, 0, 0.25);
  margin: 0;
  letter-spacing: 3px;
  font-family: 'Nunito', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  white-space: nowrap;
}

.subtitle {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.95);
  margin: 6px 0 0;
  font-weight: 600;
  letter-spacing: 1px;
  white-space: nowrap;
}

.header-decoration {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 12px;
}

.deco-icon {
  font-size: 1.2rem;
  animation: wiggle 3s ease-in-out infinite;
}

.deco-icon:last-child {
  animation-delay: 1.5s;
}

@keyframes wiggle {
  0%, 100% { transform: rotate(-5deg); }
  50% { transform: rotate(5deg); }
}

.deco-line {
  width: 50px;
  height: 3px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
  border-radius: 2px;
}

/* 用户信息栏 */
.user-info-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 12px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  border: 2px solid rgba(255, 255, 255, 0.4);
}

.user-avatar {
  font-size: 1.6rem;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}

.user-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: white;
  text-shadow: 0 1px 3px rgba(0,0,0,0.3);
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-stats {
  display: flex;
  gap: 8px;
  margin-left: 6px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 0.8rem;
  font-weight: 700;
  color: white;
  background: rgba(0, 0, 0, 0.2);
  padding: 4px 8px;
  border-radius: 12px;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

/* 主卡片 - 卡通风格 */
.main-card {
  flex: 1;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 28px;
  padding: 18px;
  box-shadow: 
    0 10px 0 rgba(0, 0, 0, 0.08),
    0 15px 40px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  max-width: 420px;
  width: 100%;
  margin: 0 auto;
  overflow: hidden;
  border: 3px solid rgba(255, 255, 255, 0.9);
}

.section-title {
  font-size: 1.1rem;
  font-weight: 800;
  color: #5b21b6;
  margin: 0 0 14px;
  text-align: center;
  font-family: 'Nunito', sans-serif;
}

/* 模式选择 - 卡通风格 */
.mode-selection {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.mode-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.mode-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 12px;
  border: none;
  border-radius: 18px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  box-shadow: 0 4px 0 rgba(0,0,0,0.15);
  position: relative;
  overflow: hidden;
}

.mode-btn::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 40%;
  background: linear-gradient(180deg, rgba(255,255,255,0.3), transparent);
  border-radius: 18px 18px 0 0;
  pointer-events: none;
}

.mode-btn:active {
  transform: translateY(3px);
  box-shadow: 0 1px 0 rgba(0,0,0,0.15);
}

.mode-btn.campaign {
  background: linear-gradient(180deg, #c4b5fd, #8b5cf6);
  color: white;
}

.mode-btn.endless {
  background: linear-gradient(180deg, #6ee7b7, #10b981);
  color: white;
}

.mode-btn.timed {
  background: linear-gradient(180deg, #f9a8d4, #ec4899);
  color: white;
}

.mode-btn.pk {
  background: linear-gradient(180deg, #fdba74, #f97316);
  color: white;
}

.mode-icon {
  font-size: 1.6rem;
  filter: drop-shadow(0 2px 2px rgba(0,0,0,0.15));
}

.mode-info {
  flex: 1;
}

.mode-name {
  font-size: 0.95rem;
  font-weight: 800;
  text-shadow: 0 1px 2px rgba(0,0,0,0.15);
}

.mode-desc {
  font-size: 0.7rem;
  opacity: 0.9;
  margin-top: 2px;
  font-weight: 600;
}

/* 排行榜卡片 - 在主卡片内 */
.leaderboard-card {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  padding: 14px 18px;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  border-radius: 16px;
  text-decoration: none;
  color: #92400e;
  box-shadow: 0 4px 0 #d97706;
  transition: all 0.2s ease;
  border: 2px solid #fbbf24;
}

.leaderboard-card:active {
  transform: translateY(3px);
  box-shadow: 0 1px 0 #d97706;
}

/* 测试模式和重置按钮并排 */
.test-reset-row {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.test-mode-card {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  padding: 10px 14px;
  background: linear-gradient(135deg, #e0f2fe, #bae6fd);
  border-radius: 14px;
  text-decoration: none;
  color: #0369a1;
  box-shadow: 0 3px 0 #0284c7;
  transition: all 0.2s ease;
  border: 2px solid #38bdf8;
}

.test-mode-card:active {
  transform: translateY(3px);
  box-shadow: 0 1px 0 #0284c7;
}

.test-mode-icon {
  font-size: 1.2rem;
}

.test-mode-text {
  font-size: 0.9rem;
  font-weight: 800;
  flex: 1;
}

.test-mode-arrow {
  font-size: 1.2rem;
  font-weight: 700;
  color: #0284c7;
}

/* 重置全部按钮 */
.reset-all-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  background: linear-gradient(135deg, #d1fae5, #a7f3d0);
  border-radius: 14px;
  border: 2px solid #34d399;
  color: #047857;
  box-shadow: 0 3px 0 #10b981;
  transition: all 0.2s ease;
  cursor: pointer;
  font-family: inherit;
}

.reset-all-btn:active {
  transform: translateY(3px);
  box-shadow: 0 1px 0 #10b981;
}

.reset-icon {
  font-size: 1.1rem;
}

.reset-text {
  font-size: 0.85rem;
  font-weight: 800;
}

.leaderboard-icon {
  font-size: 1.5rem;
}

.leaderboard-text {
  flex: 1;
  font-size: 1rem;
  font-weight: 800;
}

.leaderboard-arrow {
  font-size: 1.5rem;
  font-weight: 700;
  color: #b45309;
}

/* 设置入口 */
.settings-card {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
  padding: 12px 18px;
  background: linear-gradient(135deg, #e0e7ff, #c7d2fe);
  border-radius: 14px;
  text-decoration: none;
  color: #4338ca;
  box-shadow: 0 3px 0 #6366f1;
  transition: all 0.2s ease;
  border: 2px solid #818cf8;
}

.settings-card:active {
  transform: translateY(3px);
  box-shadow: 0 1px 0 #6366f1;
}

.settings-icon {
  font-size: 1.3rem;
}

.settings-text {
  flex: 1;
  font-size: 0.95rem;
  font-weight: 800;
}

.settings-arrow {
  font-size: 1.3rem;
  font-weight: 700;
  color: #4f46e5;
}

/* 词库选择 - 卡通风格 */
.group-selection,
.level-selection {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.selection-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.selection-header .section-title {
  margin: 0;
  flex: 1;
  text-align: left;
}

.back-btn {
  padding: 8px 14px;
  background: linear-gradient(180deg, #f3f4f6, #e5e7eb);
  border: none;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 700;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 3px 0 #d1d5db;
}

.back-btn:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0 #d1d5db;
}

/* 时长选择 */
.time-options {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  padding: 12px 14px;
  background: linear-gradient(135deg, #fdf2f8, #fce7f3);
  border-radius: 14px;
  border: 2px solid #f9a8d4;
}

.time-label {
  font-size: 0.85rem;
  color: #9d174d;
  font-weight: 700;
}

.time-btn {
  padding: 8px 14px;
  background: white;
  border: 2px solid #f9a8d4;
  border-radius: 10px;
  font-size: 0.8rem;
  font-weight: 700;
  color: #be185d;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 2px 0 #f9a8d4;
}

.time-btn.active {
  background: linear-gradient(180deg, #f9a8d4, #ec4899);
  border-color: #ec4899;
}

/* 时间选择样式 */
.duration-selection {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.duration-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.duration-btn {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  border: none;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  background: linear-gradient(180deg, #fce7f3, #fbcfe8);
  color: #9d174d;
  box-shadow: 0 4px 0 #ec4899;
  position: relative;
  overflow: hidden;
}

.duration-btn::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 40%;
  background: linear-gradient(180deg, rgba(255,255,255,0.3), transparent);
  border-radius: 16px 16px 0 0;
  pointer-events: none;
}

.duration-btn:active {
  transform: translateY(3px);
  box-shadow: 0 1px 0 #ec4899;
}

.duration-btn.active {
  background: linear-gradient(180deg, #f472b6, #ec4899);
  color: white;
  box-shadow: 0 4px 0 #be185d;
}

.duration-icon {
  font-size: 1.8rem;
  filter: drop-shadow(0 2px 2px rgba(0,0,0,0.15));
}

.duration-label {
  font-size: 1.2rem;
  font-weight: 800;
  text-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.duration-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px;
  background: linear-gradient(135deg, #fdf2f8, #fce7f3);
  border-radius: 12px;
  border: 2px solid #f9a8d4;
}

/* 已选时间横幅 */
.selected-duration-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #fdf2f8, #fce7f3);
  border-radius: 12px;
  border: 2px solid #f9a8d4;
}

.banner-value.duration {
  background: linear-gradient(180deg, #f472b6, #ec4899);
  color: white;
}

/* 难度选择样式 */
.difficulty-selection {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.difficulty-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.difficulty-btn {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  border: none;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  box-shadow: 0 4px 0 rgba(0,0,0,0.15);
  position: relative;
  overflow: hidden;
}

.difficulty-btn::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 40%;
  background: linear-gradient(180deg, rgba(255,255,255,0.3), transparent);
  border-radius: 16px 16px 0 0;
  pointer-events: none;
}

.difficulty-btn:active {
  transform: translateY(3px);
  box-shadow: 0 1px 0 rgba(0,0,0,0.15);
}

.difficulty-btn.low {
  background: linear-gradient(180deg, #a7f3d0, #6ee7b7);
  color: #065f46;
  box-shadow: 0 4px 0 #10b981;
}

.difficulty-btn.medium {
  background: linear-gradient(180deg, #fde68a, #fbbf24);
  color: #92400e;
  box-shadow: 0 4px 0 #d97706;
}

.difficulty-btn.high {
  background: linear-gradient(180deg, #fca5a5, #f87171);
  color: #7f1d1d;
  box-shadow: 0 4px 0 #dc2626;
}

.diff-icon {
  font-size: 1.8rem;
  filter: drop-shadow(0 2px 2px rgba(0,0,0,0.15));
}

.diff-info {
  flex: 1;
}

.diff-name {
  font-size: 1.1rem;
  font-weight: 800;
  text-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.diff-desc {
  font-size: 0.8rem;
  opacity: 0.8;
  margin-top: 2px;
  font-weight: 600;
}

.difficulty-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px;
  background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
  border-radius: 12px;
  border: 2px solid #7dd3fc;
}

.hint-icon {
  font-size: 1.2rem;
}

.hint-text {
  font-size: 0.85rem;
  font-weight: 600;
  color: #0369a1;
}

/* 已选难度横幅 */
.selected-difficulty-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
  border-radius: 12px;
  border: 2px solid #7dd3fc;
}

.banner-label {
  font-size: 0.85rem;
  color: #0369a1;
  font-weight: 600;
}

.banner-value {
  font-size: 0.9rem;
  font-weight: 800;
  padding: 4px 10px;
  border-radius: 8px;
}

.banner-value.low {
  background: linear-gradient(180deg, #a7f3d0, #6ee7b7);
  color: #065f46;
}

.banner-value.medium {
  background: linear-gradient(180deg, #fde68a, #fbbf24);
  color: #92400e;
}

.banner-value.high {
  background: linear-gradient(180deg, #fca5a5, #f87171);
  color: #7f1d1d;
  color: white;
  box-shadow: 0 2px 0 #be185d;
}

/* 词库网格 - 卡通风格 */
.group-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  flex: 1;
  overflow-y: auto;
}

.group-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 14px 8px;
  background: linear-gradient(180deg, #ffffff, #f1f5f9);
  border: 3px solid #e2e8f0;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 0 #cbd5e1;
}

.group-btn:hover {
  border-color: #c4b5fd;
  background: linear-gradient(180deg, #faf5ff, #ede9fe);
  transform: translateY(-2px);
  box-shadow: 0 6px 0 #a78bfa;
}

.group-btn:active {
  transform: translateY(3px);
  box-shadow: 0 1px 0 #cbd5e1;
}

.group-icon {
  font-size: 1.5rem;
  filter: drop-shadow(0 2px 2px rgba(0,0,0,0.1));
}

.group-name {
  font-size: 0.75rem;
  font-weight: 700;
  color: #4b5563;
  text-align: center;
}

.group-arrow {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1.2rem;
  font-weight: 700;
  color: #a78bfa;
}

.group-btn {
  position: relative;
}

/* 细分类网格 */
.subgroup-grid {
  grid-template-columns: repeat(3, 1fr);
}

.subgroup-grid .group-btn.all-btn {
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  border-color: #fbbf24;
  box-shadow: 0 4px 0 #d97706;
}

.subgroup-grid .group-btn.all-btn .group-name {
  color: #92400e;
  font-weight: 800;
}

/* 底部装饰 */
.footer-decoration {
  flex-shrink: 0;
  text-align: center;
  padding: 12px 0;
  display: flex;
  justify-content: center;
  gap: 20px;
}

.footer-icon {
  font-size: 1.5rem;
  animation: float 3s ease-in-out infinite;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}

.footer-icon:nth-child(2) {
  animation-delay: 1s;
}

.footer-icon:nth-child(3) {
  animation-delay: 2s;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

/* 小屏幕优化 */
@media (max-height: 700px) {
  .header-section {
    padding: 12px 12px 8px;
  }
  
  .title {
    font-size: 1.8rem;
  }
  
  .stars-left, .stars-right {
    font-size: 1.4rem;
  }
  
  .subtitle {
    font-size: 0.8rem;
  }
  
  .user-info-bar {
    margin-top: 8px;
    padding: 6px 12px;
    gap: 8px;
  }
  
  .user-avatar {
    font-size: 1.3rem;
  }
  
  .user-name {
    font-size: 0.8rem;
    max-width: 60px;
  }
  
  .stat-item {
    font-size: 0.7rem;
    padding: 3px 6px;
  }
  
  .header-decoration {
    margin-top: 8px;
  }
  
  .deco-icon {
    font-size: 1rem;
  }
  
  .main-card {
    padding: 14px;
  }
  
  .mode-btn {
    padding: 10px 10px;
  }
  
  .mode-icon {
    font-size: 1.3rem;
  }
  
  .mode-name {
    font-size: 0.85rem;
  }
  
  .mode-desc {
    font-size: 0.65rem;
  }
  
  .group-btn {
    padding: 10px 6px;
  }
  
  .group-icon {
    font-size: 1.2rem;
  }
  
  .leaderboard-card {
    padding: 10px 14px;
    margin-top: 12px;
  }
  
  .footer-decoration {
    padding: 8px 0;
  }
  
  .footer-icon {
    font-size: 1.2rem;
  }
}

/* 关卡选择样式 */
.level-info-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #ede9fe, #ddd6fe);
  border-radius: 12px;
  margin-bottom: 14px;
  border: 2px solid #a78bfa;
}

.banner-icon {
  font-size: 1.2rem;
}

.banner-text {
  font-size: 0.9rem;
  font-weight: 700;
  color: #5b21b6;
  flex: 1;
}

.banner-progress {
  font-size: 0.8rem;
  font-weight: 600;
  color: #059669;
  background: #d1fae5;
  padding: 2px 8px;
  border-radius: 10px;
}

/* 关卡主区域：左右按钮 + 中间滚动区 */
.level-main-area {
  display: flex;
  align-items: stretch;
  gap: 6px;
  flex: 1;
  min-height: 0;
}

/* 左右翻页按钮 */
.page-nav-btn {
  width: 28px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #f3f4f6, #e5e7eb);
  border: 2px solid #d1d5db;
  border-radius: 10px;
  font-size: 1.5rem;
  font-weight: 700;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 2px 0 #9ca3af;
}

.page-nav-btn:hover:not(:disabled) {
  background: linear-gradient(180deg, #a78bfa, #8b5cf6);
  border-color: #7c3aed;
  color: white;
  box-shadow: 0 2px 0 #6d28d9;
}

.page-nav-btn:active:not(:disabled) {
  transform: translateY(2px);
  box-shadow: 0 0 0 #9ca3af;
}

.page-nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* 底部范围分页器 */
.range-pagination {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 6px 10px;
  background: #f9fafb;
  border-radius: 10px;
  flex-wrap: wrap;
  justify-content: center;
}

.range-label {
  font-size: 0.7rem;
  font-weight: 700;
  color: #5b21b6;
  background: linear-gradient(180deg, #ede9fe, #ddd6fe);
  padding: 3px 8px;
  border-radius: 6px;
  white-space: nowrap;
}

.range-buttons {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: center;
}

.range-btn {
  padding: 4px 8px;
  background: linear-gradient(180deg, #ffffff, #f3f4f6);
  border: 1.5px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.65rem;
  font-weight: 700;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.range-btn:hover:not(.active) {
  background: linear-gradient(180deg, #ede9fe, #ddd6fe);
  border-color: #a78bfa;
  color: #5b21b6;
}

.range-btn.active {
  background: linear-gradient(180deg, #a78bfa, #8b5cf6);
  border-color: #7c3aed;
  color: white;
}

.range-ellipsis {
  font-size: 0.7rem;
  color: #9ca3af;
  padding: 0 2px;
}

/* 关卡滚动容器 - 每页100关，5屏滚动 */
.level-scroll-container {
  flex: 1;
  overflow-y: auto;
  max-height: 42vh;  /* 限制高度以启用滚动 */
  padding: 2px 4px 2px 2px;
}

.level-scroll-container::-webkit-scrollbar {
  width: 6px;
}

.level-scroll-container::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.level-scroll-container::-webkit-scrollbar-thumb {
  background: #a78bfa;
  border-radius: 3px;
}

.level-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);  /* 每行4个 */
  gap: 8px;
}

.level-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
  padding: 6px 2px;
  background: linear-gradient(180deg, #ffffff, #f1f5f9);
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 0 #cbd5e1;
  min-height: 50px;
}

.level-btn:hover:not(.locked) {
  transform: translateY(-2px);
  box-shadow: 0 6px 0 #a78bfa;
}

.level-btn:active:not(.locked) {
  transform: translateY(3px);
  box-shadow: 0 1px 0 #cbd5e1;
}

.level-btn.completed {
  background: linear-gradient(180deg, #d1fae5, #a7f3d0);
  border-color: #34d399;
  box-shadow: 0 4px 0 #10b981;
}

.level-btn.current {
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  border-color: #fbbf24;
  box-shadow: 0 4px 0 #d97706;
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 4px 0 #d97706, 0 0 0 0 rgba(251, 191, 36, 0.4); }
  50% { box-shadow: 0 4px 0 #d97706, 0 0 0 6px rgba(251, 191, 36, 0); }
}

.level-btn.locked {
  background: linear-gradient(180deg, #e5e7eb, #d1d5db);
  border-color: #9ca3af;
  box-shadow: 0 4px 0 #6b7280;
  cursor: not-allowed;
  opacity: 0.7;
}

.level-number {
  font-size: 1.2rem;
  font-weight: 900;
  color: #4b5563;
  font-family: 'Nunito', sans-serif;
}

.level-btn.completed .level-number {
  color: #065f46;
}

.level-btn.current .level-number {
  color: #92400e;
}

.level-btn.locked .level-number {
  color: #6b7280;
}

.level-stars {
  font-size: 0.65rem;
  min-height: 14px;
}

.level-status {
  font-size: 0.65rem;
  font-weight: 700;
  color: #6b7280;
}

.level-btn.completed .level-status {
  color: #047857;
}

.level-btn.current .level-status {
  color: #b45309;
}

.level-legend {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 10px;
  padding: 8px;
  background: #f9fafb;
  border-radius: 10px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 600;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid;
}

.legend-dot.completed {
  background: #a7f3d0;
  border-color: #34d399;
}

.legend-dot.current {
  background: #fde68a;
  border-color: #fbbf24;
}

.legend-dot.locked {
  background: #d1d5db;
  border-color: #9ca3af;
}

.legend-dot.sparse {
  background: #fef3c7;
  border-color: #fbbf24;
}

.legend-dot.dense {
  background: #d1fae5;
  border-color: #10b981;
}

.endless-banner {
  background: linear-gradient(135deg, #d1fae5, #a7f3d0);
  border-color: #10b981;
}

.endless-banner .banner-text {
  color: #047857;
}

.level-type {
  font-size: 0.6rem;
  font-weight: 700;
  color: #6b7280;
  background: rgba(0,0,0,0.05);
  padding: 2px 6px;
  border-radius: 4px;
}

/* 大屏幕优化 */
@media (min-width: 768px) {
  .header-section {
    padding: 36px 24px 24px;
  }
  
  .title {
    font-size: 3rem;
    letter-spacing: 6px;
  }
  
  .stars-left, .stars-right {
    font-size: 2.2rem;
  }
  
  .subtitle {
    font-size: 1.1rem;
    margin-top: 10px;
  }
  
  .main-card {
    max-width: 480px;
  }
  
  .mode-btn {
    padding: 18px 16px;
  }
  
  .mode-icon {
    font-size: 1.8rem;
  }
  
  .mode-name {
    font-size: 1rem;
  }
  
  .group-grid {
    grid-template-columns: repeat(4, 1fr);
  }
  
  .leaderboard-card {
    padding: 16px 20px;
  }
  
  .level-grid {
    grid-template-columns: repeat(4, 1fr);  /* 大屏幕保持每行4个，每屏20关 */
    gap: 10px;
  }
  
  .level-scroll-container {
    max-height: 48vh;
  }
  
  .level-btn {
    min-height: 70px;
    padding: 10px 6px;
  }
  
  .level-number {
    font-size: 1.4rem;
  }
  
  .page-nav-btn {
    width: 36px;
    font-size: 1.8rem;
  }
  
  .range-btn {
    padding: 5px 10px;
    font-size: 0.7rem;
  }
}

/* 小屏幕优化 */
@media (max-width: 400px) {
  .level-grid {
    grid-template-columns: repeat(4, 1fr);  /* 小屏幕每行4个 */
    gap: 5px;
  }
  
  .level-scroll-container {
    max-height: 38vh;
  }
  
  .level-btn {
    min-height: 50px;
    padding: 5px 2px;
    border-radius: 8px;
  }
  
  .level-number {
    font-size: 1rem;
  }
  
  .level-stars {
    font-size: 0.5rem;
  }
  
  .level-status {
    font-size: 0.5rem;
  }
  
  .page-nav-btn {
    width: 24px;
    font-size: 1.2rem;
  }
  
  .range-pagination {
    padding: 4px 6px;
  }
  
  .range-label {
    font-size: 0.6rem;
    padding: 2px 6px;
  }
  
  .range-btn {
    padding: 3px 6px;
    font-size: 0.55rem;
  }
  
  .range-ellipsis {
    font-size: 0.6rem;
  }
}
</style>
