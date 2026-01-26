<template>
  <div class="test-mode-screen">
    <!-- 顶部栏 -->
    <div class="top-bar">
      <button @click="goBack" class="back-btn">← 返回</button>
      <h1 class="page-title">📋 关卡数据查看</h1>
      <button @click="loadLevelsSummary" :disabled="summaryLoading" class="refresh-btn">
        <span :class="{ spinning: summaryLoading }">🔄</span>
        刷新
      </button>
    </div>

    <!-- 汇总统计 -->
    <div v-if="levelsSummary" class="summary-stats">
      <div class="stat-card">
        <div class="stat-icon">📚</div>
        <div class="stat-value">{{ levelsSummary.total_groups || 0 }}</div>
        <div class="stat-label">词库分组</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🎮</div>
        <div class="stat-value">{{ levelsSummary.total_levels || 0 }}</div>
        <div class="stat-label">总关卡数</div>
      </div>
      <div class="stat-card success">
        <div class="stat-icon">✅</div>
        <div class="stat-value">{{ levelsSummary.success_count || 0 }}</div>
        <div class="stat-label">成功生成</div>
      </div>
    </div>

    <!-- 词库分类选择 -->
    <div class="category-tabs">
      <button 
        v-for="cat in categories" 
        :key="cat.code"
        :class="['category-tab', { active: selectedCategory === cat.code }]"
        @click="selectedCategory = cat.code"
      >
        {{ cat.icon }} {{ cat.name }}
      </button>
    </div>

    <!-- 词库列表 -->
    <div class="group-selector">
      <button 
        v-for="group in filteredGroups" 
        :key="group.code"
        :class="['group-btn', { active: selectedGroup === group.code }]"
        @click="selectGroup(group.code)"
      >
        <span class="group-name">{{ group.name }}</span>
        <span class="group-stats">{{ group.levels }}关 · {{ group.coverage }}%</span>
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner">⏳</div>
      <p>正在加载关卡数据...</p>
    </div>

    <!-- 关卡列表 -->
    <div v-else-if="currentLevels.length > 0" class="levels-container">
      <div class="levels-header">
        <span class="levels-title">📚 {{ currentGroupName }} · 共 {{ currentLevels.length }} 关</span>
        <div class="page-controls">
          <button @click="prevPage" :disabled="currentPage === 1" class="page-btn">‹</button>
          <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
          <button @click="nextPage" :disabled="currentPage === totalPages" class="page-btn">›</button>
        </div>
      </div>

      <!-- 关卡网格 -->
      <div class="levels-grid">
        <div 
          v-for="level in paginatedLevels" 
          :key="level.level" 
          :class="['level-card', { expanded: expandedLevel === level.level }]"
          @click="toggleLevel(level.level)"
        >
          <!-- 关卡头部 -->
          <div class="level-header">
            <div class="level-info">
              <span class="level-num">第{{ level.level }}关</span>
              <span class="grid-badge">{{ level.grid_size }}×{{ level.grid_size }}</span>
              <span class="word-badge">{{ level.word_count }}词</span>
            </div>
            <span class="expand-icon">{{ expandedLevel === level.level ? '▼' : '▶' }}</span>
          </div>
          
          <!-- 展开的答案详情 -->
          <div v-if="expandedLevel === level.level" class="level-details" @click.stop>
            <!-- 答案网格 -->
            <div class="answer-section">
              <div class="section-title">📝 答案网格</div>
              <div class="grid-legend">
                <span class="legend-item prefilled">🟡 预填</span>
                <span class="legend-item normal">🟣 待填</span>
              </div>
              <div 
                class="answer-grid"
                :style="{ gridTemplateColumns: `repeat(${level.grid_size}, 1fr)` }"
              >
                <div 
                  v-for="(row, rowIdx) in level.answer_grid" 
                  :key="'row-' + rowIdx"
                  class="grid-row"
                >
                  <div 
                    v-for="(cell, colIdx) in row" 
                    :key="'cell-' + rowIdx + '-' + colIdx"
                    :class="['grid-cell', { 
                      empty: cell === null,
                      prefilled: level.prefilled && level.prefilled[rowIdx + '-' + colIdx]
                    }]"
                  >
                    {{ cell || '' }}
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 单词列表 -->
            <div class="words-section">
              <div class="words-group">
                <div class="words-title">→ 横向 ({{ level.across_words?.length || 0 }})</div>
                <div class="words-list">
                  <div v-for="word in level.across_words" :key="'a-' + word.id" class="word-item">
                    <span class="word-num">{{ word.clue_number }}.</span>
                    <span class="word-text">{{ word.word }}</span>
                    <span class="word-def">{{ word.definition }}</span>
                  </div>
                </div>
              </div>
              
              <div class="words-group">
                <div class="words-title">↓ 纵向 ({{ level.down_words?.length || 0 }})</div>
                <div class="words-list">
                  <div v-for="word in level.down_words" :key="'d-' + word.id" class="word-item">
                    <span class="word-num">{{ word.clue_number }}.</span>
                    <span class="word-text">{{ word.word }}</span>
                    <span class="word-def">{{ word.definition }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 无数据提示 -->
    <div v-else class="empty-state">
      <div class="empty-icon">📭</div>
      <p>请选择一个词库查看关卡数据</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { staticApi } from '../api/index.js'

const router = useRouter()

const loading = ref(false)
const summaryLoading = ref(false)
const expandedLevel = ref(null)

// 汇总数据
const levelsSummary = ref(null)

// 分类和词库
const categories = [
  { code: 'primary', name: '小学', icon: '📚' },
  { code: 'junior', name: '初中', icon: '📖' },
  { code: 'senior', name: '高中', icon: '📕' },
  { code: 'exam', name: '考试', icon: '🎯' }
]

const selectedCategory = ref('primary')
const selectedGroup = ref('')

// 所有词库数据
const allGroups = ref([])

// 当前关卡数据
const currentLevels = ref([])

// 分页
const currentPage = ref(1)
const pageSize = 20

// API基础路径
const API_BASE = import.meta.env.VITE_API_BASE || ''

// 分类映射
const categoryMap = {
  '小学': 'primary',
  '初中': 'junior',
  '高中': 'senior',
  '考试': 'exam'
}

// 按分类筛选的词库
const filteredGroups = computed(() => {
  return allGroups.value.filter(g => g.category === selectedCategory.value)
})

// 当前选中词库名称
const currentGroupName = computed(() => {
  const group = allGroups.value.find(g => g.code === selectedGroup.value)
  return group ? group.name : ''
})

// 总页数
const totalPages = computed(() => {
  return Math.ceil(currentLevels.value.length / pageSize)
})

// 当前页的关卡
const paginatedLevels = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return currentLevels.value.slice(start, start + pageSize)
})

// 加载汇总数据（从静态数据）
async function loadLevelsSummary() {
  summaryLoading.value = true
  
  try {
    const data = await staticApi.getLevelsSummary()
    
    if (data && data.groups) {
      levelsSummary.value = { available: true, ...data }
      
      // 整理词库列表
      allGroups.value = data.groups.map(g => ({
        code: g.group_code,
        name: g.group_name,
        category: categoryMap[g.category] || 'exam',
        levels: g.level_count,
        words: g.word_count,
        coverage: g.coverage || 0
      }))
      
      // 默认选择第一个词库
      if (filteredGroups.value.length > 0 && !selectedGroup.value) {
        selectGroup(filteredGroups.value[0].code)
      }
    }
  } catch (e) {
    console.error('加载汇总数据失败:', e)
  } finally {
    summaryLoading.value = false
  }
}

// 选择词库
async function selectGroup(code) {
  selectedGroup.value = code
  currentPage.value = 1
  expandedLevel.value = null
  await loadGroupLevels(code)
}

// 加载词库关卡数据 - 按需加载每关（分页模式）
// 新目录结构: /data/levels/{group}/{level}.json
async function loadGroupLevels(code) {
  loading.value = true
  currentLevels.value = []
  
  try {
    // 先从meta.json获取关卡数量
    const meta = await staticApi.getLevelMeta(code)
    if (!meta) {
      throw new Error('无法加载词库元数据')
    }
    const levelCount = meta.level_count || 0
    
    // 为每个关卡创建占位对象，包含基本信息
    const levels = []
    for (let i = 1; i <= levelCount; i++) {
      levels.push({
        level: i,
        loaded: false,  // 标记是否已加载详情
        words: [],
        grid_size: 0
      })
    }
    currentLevels.value = levels
    
    // 加载当前页的关卡详情
    await loadCurrentPageLevels(code)
  } catch (e) {
    console.error('加载关卡数据失败:', e)
  } finally {
    loading.value = false
  }
}

// 加载当前页的关卡详情
async function loadCurrentPageLevels(code) {
  const startIndex = (currentPage.value - 1) * pageSize
  const endIndex = Math.min(startIndex + pageSize, currentLevels.value.length)
  
  // 并行加载当前页的所有关卡
  const promises = []
  for (let i = startIndex; i < endIndex; i++) {
    const level = currentLevels.value[i]
    if (level && !level.loaded) {
      promises.push(loadSingleLevelDetail(code, level.level, i))
    }
  }
  
  if (promises.length > 0) {
    await Promise.all(promises)
  }
}

// 加载单关详情
async function loadSingleLevelDetail(code, levelNum, index) {
  try {
    const data = await staticApi.getLevelData(code, levelNum)
    if (!data) return
    
    if (currentLevels.value[index]) {
      // 转换数据格式：将 cells/words 转换为模板期望的格式
      const gridSize = data.grid_size || 0
      const words = data.words || []
      
      // 构建答案网格（从 cells 和 words 中提取字母）
      const answerGrid = []
      for (let row = 0; row < gridSize; row++) {
        const rowData = []
        for (let col = 0; col < gridSize; col++) {
          const cell = data.cells?.[row]?.[col]
          rowData.push(cell === null ? null : '')  // null是黑格，空字符串是待填格
        }
        answerGrid.push(rowData)
      }
      
      // 用单词填充答案网格
      words.forEach(word => {
        const startRow = word.start_row
        const startCol = word.start_col
        for (let i = 0; i < word.word.length; i++) {
          if (word.direction === 'across') {
            if (answerGrid[startRow]) {
              answerGrid[startRow][startCol + i] = word.word[i]
            }
          } else {
            if (answerGrid[startRow + i]) {
              answerGrid[startRow + i][startCol] = word.word[i]
            }
          }
        }
      })
      
      // 分离横向和纵向单词
      const acrossWords = words.filter(w => w.direction === 'across')
        .sort((a, b) => a.clue_number - b.clue_number)
      const downWords = words.filter(w => w.direction === 'down')
        .sort((a, b) => a.clue_number - b.clue_number)
      
      // 转换预填信息格式
      const prefilled = {}
      if (data.prefilled) {
        Object.keys(data.prefilled).forEach(key => {
          prefilled[key] = true
        })
      }
      
      // 更新关卡数据
      currentLevels.value[index] = {
        level: data.level,
        grid_size: gridSize,
        word_count: words.length,
        answer_grid: answerGrid,
        across_words: acrossWords,
        down_words: downWords,
        prefilled: prefilled,
        difficulty: data.difficulty,
        loaded: true
      }
    }
  } catch (e) {
    console.warn(`加载关卡 ${code}/${levelNum} 失败:`, e)
  }
}

// 切换分类时重新加载
watch(selectedCategory, () => {
  if (filteredGroups.value.length > 0) {
    selectGroup(filteredGroups.value[0].code)
  } else {
    selectedGroup.value = ''
    currentLevels.value = []
  }
})

// 展开/收起关卡
function toggleLevel(levelNum) {
  expandedLevel.value = expandedLevel.value === levelNum ? null : levelNum
}

// 翻页
async function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    expandedLevel.value = null
    // 加载新页的关卡详情
    await loadCurrentPageLevels(selectedGroup.value)
  }
}

async function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    expandedLevel.value = null
    // 加载新页的关卡详情
    await loadCurrentPageLevels(selectedGroup.value)
  }
}

// 返回首页
function goBack() {
  router.push('/')
}

onMounted(() => {
  loadLevelsSummary()
})
</script>

<style scoped>
.test-mode-screen {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  padding: 12px;
  box-sizing: border-box;
}

/* 顶部栏 */
.top-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 4px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 12px;
}

.back-btn {
  padding: 8px 14px;
  background: linear-gradient(180deg, #f3f4f6, #e5e7eb);
  border: none;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 700;
  color: #6b7280;
  cursor: pointer;
  box-shadow: 0 2px 0 #d1d5db;
}

.back-btn:active {
  transform: translateY(2px);
  box-shadow: none;
}

.page-title {
  flex: 1;
  font-size: 1.1rem;
  font-weight: 800;
  color: #0369a1;
  margin: 0;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: linear-gradient(180deg, #34d399, #10b981);
  border: none;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 700;
  color: white;
  cursor: pointer;
  box-shadow: 0 3px 0 #059669;
}

.refresh-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.spinning {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 汇总统计 */
.summary-stats {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.stat-card {
  flex: 1;
  padding: 12px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 14px;
  text-align: center;
  box-shadow: 0 3px 0 rgba(0, 0, 0, 0.08);
  border: 2px solid #e5e7eb;
}

.stat-card.success {
  background: linear-gradient(180deg, #d1fae5, #a7f3d0);
  border-color: #34d399;
}

.stat-card .stat-icon {
  font-size: 1.3rem;
  margin-bottom: 2px;
}

.stat-card .stat-value {
  font-size: 1.4rem;
  font-weight: 900;
  color: #374151;
}

.stat-card.success .stat-value {
  color: #065f46;
}

.stat-card .stat-label {
  font-size: 0.7rem;
  color: #6b7280;
  font-weight: 600;
}

/* 分类标签 */
.category-tabs {
  display: flex;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 14px;
  box-shadow: 0 3px 0 rgba(0, 0, 0, 0.08);
  margin-bottom: 10px;
}

.category-tab {
  flex: 1;
  padding: 10px 12px;
  background: linear-gradient(180deg, #f3f4f6, #e5e7eb);
  border: 2px solid #d1d5db;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 700;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.category-tab.active {
  background: linear-gradient(180deg, #8b5cf6, #7c3aed);
  border-color: #5b21b6;
  color: white;
  box-shadow: 0 2px 0 #5b21b6;
}

/* 词库选择器 */
.group-selector {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding: 12px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 14px;
  box-shadow: 0 3px 0 rgba(0, 0, 0, 0.08);
  margin-bottom: 12px;
}

.group-btn {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 14px;
  background: linear-gradient(180deg, #ffffff, #f3f4f6);
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 100px;
}

.group-btn:hover {
  border-color: #a5b4fc;
}

.group-btn.active {
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  border-color: #fbbf24;
  box-shadow: 0 2px 0 #d97706;
}

.group-name {
  font-weight: 700;
  color: #374151;
}

.group-btn.active .group-name {
  color: #92400e;
}

.group-stats {
  font-size: 0.7rem;
  color: #6b7280;
}

.group-btn.active .group-stats {
  color: #b45309;
}

/* 加载状态 */
.loading-state,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #6b7280;
}

.spinner {
  font-size: 3rem;
  animation: spin 2s linear infinite;
}

.empty-icon {
  font-size: 3rem;
}

/* 关卡容器 */
.levels-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.levels-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  margin-bottom: 10px;
  box-shadow: 0 2px 0 rgba(0, 0, 0, 0.08);
}

.levels-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: #374151;
}

.page-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #f3f4f6, #e5e7eb);
  border: 2px solid #d1d5db;
  border-radius: 8px;
  font-size: 1.2rem;
  font-weight: 700;
  color: #6b7280;
  cursor: pointer;
}

.page-btn:hover:not(:disabled) {
  background: linear-gradient(180deg, #8b5cf6, #7c3aed);
  border-color: #5b21b6;
  color: white;
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  font-size: 0.8rem;
  font-weight: 700;
  color: #5b21b6;
  min-width: 60px;
  text-align: center;
}

/* 关卡网格 */
.levels-grid {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-bottom: 16px;
}

/* 关卡卡片 */
.level-card {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 14px;
  box-shadow: 0 3px 0 rgba(0, 0, 0, 0.08);
  overflow: hidden;
  cursor: pointer;
  border: 2px solid #e5e7eb;
  transition: all 0.2s;
}

.level-card:hover {
  border-color: #a5b4fc;
}

.level-card.expanded {
  border-color: #8b5cf6;
}

.level-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
}

.level-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.level-num {
  font-size: 1rem;
  font-weight: 800;
  color: #374151;
}

.grid-badge, .word-badge {
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
}

.grid-badge {
  background: #dbeafe;
  color: #1e40af;
}

.word-badge {
  background: #d1fae5;
  color: #065f46;
}

.expand-icon {
  font-size: 0.8rem;
  color: #9ca3af;
}

/* 关卡详情 */
.level-details {
  padding: 0 14px 14px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
  cursor: default;
}

.answer-section {
  padding: 12px 0;
}

.section-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: #374151;
  margin-bottom: 8px;
}

.grid-legend {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 8px;
  font-size: 0.7rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
}

.legend-item.prefilled { color: #92400e; }
.legend-item.normal { color: #4c1d95; }

.answer-grid {
  display: grid;
  gap: 2px;
  max-width: 280px;
  margin: 0 auto;
}

.grid-row {
  display: contents;
}

.grid-cell {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #ffffff, #f1f5f9);
  border: 2px solid #c7d2fe;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 800;
  color: #4c1d95;
  text-transform: uppercase;
}

.grid-cell.prefilled {
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  border-color: #f59e0b;
  color: #92400e;
}

.grid-cell.empty {
  background: #374151;
  border-color: #1f2937;
}

/* 单词列表 */
.words-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 10px;
}

.words-group {
  background: white;
  border-radius: 10px;
  padding: 10px;
  border: 1px solid #e5e7eb;
}

.words-title {
  font-size: 0.8rem;
  font-weight: 700;
  color: #5b21b6;
  margin-bottom: 6px;
}

.words-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.word-item {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: 0.75rem;
  padding: 4px 6px;
  background: #f9fafb;
  border-radius: 4px;
}

.word-num {
  font-weight: 700;
  color: #6b7280;
  min-width: 18px;
}

.word-text {
  font-weight: 800;
  color: #065f46;
  text-transform: uppercase;
  min-width: 60px;
}

.word-def {
  flex: 1;
  color: #4b5563;
  font-size: 0.7rem;
}

/* 移动端优化 */
@media (max-width: 480px) {
  .test-mode-screen {
    padding: 8px;
  }
  
  .top-bar {
    padding: 10px 12px;
    gap: 8px;
  }
  
  .page-title {
    font-size: 0.95rem;
  }
  
  .refresh-btn {
    padding: 8px 12px;
    font-size: 0.75rem;
  }
  
  .summary-stats {
    gap: 6px;
  }
  
  .stat-card {
    padding: 8px;
  }
  
  .stat-card .stat-icon {
    font-size: 1rem;
  }
  
  .stat-card .stat-value {
    font-size: 1.1rem;
  }
  
  .category-tab {
    padding: 8px 10px;
    font-size: 0.75rem;
  }
  
  .group-btn {
    padding: 8px 10px;
    min-width: 80px;
  }
  
  .group-name {
    font-size: 0.8rem;
  }
  
  .grid-cell {
    font-size: 0.65rem;
    border-width: 1px;
  }
  
  .word-item {
    flex-wrap: wrap;
  }
  
  .word-def {
    width: 100%;
    margin-left: 24px;
  }
}
</style>
