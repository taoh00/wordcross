<template>
  <div class="game-screen">
    <!-- 顶部信息栏 - 两行紧凑布局 -->
    <div class="top-bar">
      <div class="game-card-compact">
        <!-- 第一行：用户信息 + 返回 -->
        <div class="top-row-1">
          <button @click="goBack" class="back-btn-icon" title="返回">
            ←
          </button>
          <div class="user-info-mini">
            <span class="mini-avatar">{{ userAvatar }}</span>
            <span class="mini-name">{{ userName }}</span>
          </div>
          <div class="mini-stats">
            <span class="mini-stat" title="体力">⚡{{ userEnergy }}</span>
            <span class="mini-stat" title="提示">💡{{ hintLetterCount }}</span>
            <span class="mini-stat" title="发音">🔊{{ speakPropCount }}</span>
          </div>
        </div>
        
        <!-- 第二行：游戏状态 -->
        <div class="top-row-2">
          <div class="game-mode-badge">
            {{ modeIcon }} {{ modeName }}
            <span v-if="gameStore.currentMode === 'campaign'" class="level-badge">
              L{{ gameStore.currentLevel }}
            </span>
          </div>
          <div :class="['timer-mini', { warning: isTimeWarning }]">
            ⏱️{{ gameStore.formattedTimer }}
          </div>
          <div class="score-mini">🌟{{ gameStore.score }}</div>
          <div class="progress-mini">
            <!-- 累计分数显示在进度条左侧（计时/PK/无限模式） -->
            <span v-if="showSessionScore && sessionScore > 0" class="session-score-mini">+{{ sessionScore }}</span>
            <div class="progress-bar-mini">
              <div 
                class="progress-fill-mini"
                :style="{ width: gameStore.progress + '%' }"
              ></div>
            </div>
            <span class="progress-text-mini">{{ gameStore.completedWords.length }}/{{ gameStore.words.length }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 游戏网格区 -->
      <div class="game-card-main">
        <!-- 网格 -->
        <div class="grid-wrapper">
          <div 
            class="grid-container"
            :style="{ 
              gridTemplateColumns: `repeat(${gameStore.gridSize}, minmax(0, 1fr))`
            }"
            :data-grid-size="gameStore.gridSize"
          >
            <div
              v-for="(row, rowIndex) in gameStore.cells"
              v-bind:key="'row-' + rowIndex"
              class="contents"
            >
              <div
                v-for="(cell, colIndex) in row"
                :key="`${rowIndex}-${colIndex}`"
                :class="getCellClass(rowIndex, colIndex, cell)"
                @click="handleCellClick(rowIndex, colIndex, cell)"
              >
                <!-- 线索编号（左上角小数字） -->
                <span v-if="getClueNumber(rowIndex, colIndex)" class="clue-number">
                  {{ getClueNumber(rowIndex, colIndex) }}
                </span>
                <span v-if="cell !== null" class="cell-letter">
                  {{ gameStore.getAnswer(rowIndex, colIndex) }}
                </span>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- 单词列表 - 显示所有单词（已完成和待填）- 按clue_number排序 -->
      <div class="words-section">
        <div class="words-list">
          <div 
            v-for="(word, index) in sortedWords" 
            :key="word.id"
            :ref="el => { if (el) wordItemRefs[word.id] = el }"
            :class="['word-item', { 
              'completed': isWordCompleted(word.id),
              'selected': selectedWord?.id === word.id
            }]"
            @click="!isWordCompleted(word.id) && selectWord(word)"
          >
            <!-- 序号（使用填字游戏标准编号 + 方向） -->
            <span class="word-index">{{ word.clue_number || (index + 1) }}</span>
            <span class="word-direction-badge">{{ word.direction === 'across' ? '横' : '竖' }}</span>
            
            <!-- 已完成：显示单词和释义 -->
            <template v-if="isWordCompleted(word.id)">
              <span class="word-text" @click.stop="openWordDetail(getCompletedWordInfo(word.id))">
                {{ word.word }}
              </span>
              <span v-if="settingsStore.showTranslation" class="word-definition">{{ word.definition }}</span>
              <button @click.stop="openWordDetail(getCompletedWordInfo(word.id))" class="detail-btn" title="查看详情">
                📖
              </button>
              <button @click.stop="speakWord(word.word)" class="speak-btn" title="发音">
                🔊
              </button>
            </template>
            
            <!-- 未完成：显示字母提示 + 翻译（根据设置显示） -->
            <template v-else>
              <span class="word-placeholder">
                <span v-for="(char, i) in getWordHint(word)" :key="i" :class="['placeholder-char', { 'hint-letter': char !== '_' }]">{{ char }}</span>
              </span>
              <!-- 翻译默认显示（根据设置） -->
              <span v-if="settingsStore.showTranslation" class="word-translation-hint">
                {{ word.definition }}
              </span>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部键盘区 - 固定在底部，三行满屏对齐 -->
    <div class="keyboard-section">
      <div class="keyboard-wrapper">
        <div class="keyboard-container">
          <!-- 第一行：QWERTYUIOP (10键) -->
          <div class="keyboard-row">
            <button 
              v-for="letter in 'QWERTYUIOP'" 
              :key="letter"
              @click="inputLetter(letter)"
              :class="['keyboard-key-new', { 'key-highlight': isLetterNeeded(letter) }]"
            >
              {{ letter }}
            </button>
          </div>
          <!-- 第二行：ASDFGHJKL + 删除键 (10键) -->
          <div class="keyboard-row">
            <button 
              v-for="letter in 'ASDFGHJKL'" 
              :key="letter"
              @click="inputLetter(letter)"
              :class="['keyboard-key-new', { 'key-highlight': isLetterNeeded(letter) }]"
            >
              {{ letter }}
            </button>
            <button @click="deleteLetter" class="keyboard-key-new delete-key">
              ⌫
            </button>
          </div>
          <!-- 第三行：ZXCVBNM + 提示(1.5格) + 翻译(1.5格) -->
          <div class="keyboard-row">
            <button 
              v-for="letter in 'ZXCVBNM'" 
              :key="letter"
              @click="inputLetter(letter)"
              :class="['keyboard-key-new', { 'key-highlight': isLetterNeeded(letter) }]"
            >
              {{ letter }}
            </button>
            <!-- 右侧道具按钮 - 横着1.5格宽度 -->
            <button 
              @click="useHintLetterProp" 
              :disabled="hintLetterCount <= 0"
              :class="['keyboard-prop-btn', { 'active': hintLetterActive }]"
            >
              <span class="prop-emoji">💡</span>
              <span class="prop-num">{{ hintLetterCount }}</span>
            </button>
            <button 
              @click="useSpeakProp" 
              :disabled="speakPropCount <= 0 || !selectedWord"
              :class="['keyboard-prop-btn', { 'active': speakPropActive }]"
            >
              <span class="prop-emoji">🔊</span>
              <span class="prop-num">{{ speakPropCount }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 通关弹窗 - 萌系卡通风格 -->
    <div v-if="showCompleteModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="complete-modal animate-bounce-in">
        <!-- 庆祝动画 -->
        <div class="confetti-container">
          <span v-for="i in 12" :key="i" class="confetti" :style="{ '--delay': i * 0.1 + 's', '--x': (Math.random() * 200 - 100) + 'px' }">🎊</span>
        </div>
        
        <!-- 计时/PK/无限模式结束 - 显示时间到图标 -->
        <template v-if="timedModeEnded && (gameStore.currentMode === 'timed' || gameStore.currentMode === 'pk' || gameStore.currentMode === 'endless')">
          <div class="trophy-area">
            <div class="trophy-emoji">{{ gameStore.currentMode === 'endless' ? '♾️' : '⏰' }}</div>
            <div class="timed-result">
              <span class="timed-words-count">{{ sessionLevelCount }}</span>
              <span class="timed-words-label">关</span>
              <span class="timed-words-count" style="margin-left: 12px">{{ sessionWordsCount }}</span>
              <span class="timed-words-label">词</span>
            </div>
          </div>
          
          <!-- 标题 -->
          <h2 class="complete-title">
            {{ gameStore.currentMode === 'endless' ? '⏱️ 时间用尽！' : '⏱️ 时间到！' }}
          </h2>
          
          <!-- 统计数据 -->
          <div class="stats-inline">
            🌟{{ sessionScore }}分 · 📝{{ sessionWordsCount }}词 · 🎯{{ sessionLevelCount }}关
          </div>
          
          <!-- 奖励展示区 -->
          <div v-if="showRewardChoice && earnedRewards.length > 0" class="reward-display">
            <div class="reward-title">🎁 获得奖励</div>
            <div class="reward-items">
              <div v-for="(reward, idx) in earnedRewards" :key="idx" class="reward-item">
                <span class="reward-icon">{{ reward.icon }}</span>
                <span class="reward-value">+{{ reward.value }}</span>
                <span class="reward-name">{{ reward.name }}</span>
              </div>
            </div>
          </div>
          
          <!-- 按钮 - 返回、领奖、再玩一次 -->
          <div class="modal-btns three-btns">
            <button @click="goBack" class="modal-btn secondary small">
              返回
            </button>
            <button 
              @click="claimRewards" 
              class="modal-btn reward small"
              :disabled="rewardClaimed"
              :class="{ claimed: rewardClaimed }"
            >
              {{ rewardClaimed ? '已领取' : '领奖' }}
            </button>
            <button @click="playAgain" class="modal-btn primary small">
              再玩一次
            </button>
          </div>
        </template>
        
        <!-- 正常通关模式 -->
        <template v-else>
          <!-- 奖杯/星星 - 根据用时显示不同星级 -->
          <div class="trophy-area">
            <div class="trophy-emoji">{{ isLastLevel ? '🏆' : '🎉' }}</div>
            <div class="stars-row">
              <span :class="['star', { earned: currentStars >= 1 }]">{{ currentStars >= 1 ? '⭐' : '☆' }}</span>
              <span :class="['star', 'big', { earned: currentStars >= 2 }]">{{ currentStars >= 2 ? '⭐' : '☆' }}</span>
              <span :class="['star', { earned: currentStars >= 3 }]">{{ currentStars >= 3 ? '⭐' : '☆' }}</span>
            </div>
            <div class="stars-hint">
              {{ currentStars === 3 ? '完美！' : currentStars === 2 ? '很棒！' : '继续加油！' }}
            </div>
          </div>
          
          <!-- 标题 -->
          <h2 class="complete-title">
            {{ isLastLevel ? '恭喜全部通关！' : `第${gameStore.currentLevel}关 通关！` }}
          </h2>
          
          <!-- 统计数据 - 一行紧凑显示 -->
          <div class="stats-inline">
            ⏱️{{ gameStore.formattedTimer }} · 🌟{{ gameStore.score }}分 · 📝{{ gameStore.completedWords.length }}词
          </div>
          
          <!-- 奖励展示区 -->
          <div v-if="showRewardChoice && earnedRewards.length > 0" class="reward-display">
            <div class="reward-title">🎁 获得奖励</div>
            <div class="reward-items">
              <div v-for="(reward, idx) in earnedRewards" :key="idx" class="reward-item">
                <span class="reward-icon">{{ reward.icon }}</span>
                <span class="reward-value">+{{ reward.value }}</span>
                <span class="reward-name">{{ reward.name }}</span>
              </div>
            </div>
          </div>
          
          <p v-if="isLastLevel" class="all-complete-msg">🌟 太棒了！你已完成全部关卡！</p>
          
          <!-- 按钮 - 三个并排：返回、领奖、下一关 -->
          <div class="modal-btns three-btns">
            <button @click="goBack" class="modal-btn secondary small">
              返回
            </button>
            
            <template v-if="!isLastLevel">
              <button 
                @click="claimRewards" 
                class="modal-btn reward small"
                :disabled="rewardClaimed"
                :class="{ claimed: rewardClaimed }"
              >
                {{ rewardClaimed ? '已领取' : '领奖' }}
              </button>
              <button @click="goNextLevel" class="modal-btn primary small">
                下一关
              </button>
            </template>
            
            <button 
              v-else
              @click="replayLevel" 
              class="modal-btn success small"
            >
              再玩一次
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- 单词详情卡片弹窗 -->
    <div v-if="showWordDetail && detailWord" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="closeWordDetail">
      <div class="word-detail-card animate-bounce-in">
        <!-- 关闭按钮 -->
        <button @click="closeWordDetail" class="detail-close-btn">×</button>
        
        <!-- 单词 -->
        <div class="detail-word">{{ detailWord.word?.toUpperCase() }}</div>
        
        <!-- 音标（如有） -->
        <div v-if="detailWord.phonetic" class="detail-phonetic">{{ detailWord.phonetic }}</div>
        
        <!-- 发音按钮 -->
        <div class="detail-speak-btns">
          <button @click="speakWord(detailWord.word, 'us')" class="detail-speak-btn us">
            🔊 美音
          </button>
          <button @click="speakWord(detailWord.word, 'uk')" class="detail-speak-btn uk">
            🔊 英音
          </button>
        </div>
        
        <!-- 释义 -->
        <div class="detail-section">
          <div class="detail-label">📖 释义</div>
          <div class="detail-content">{{ detailWord.definition }}</div>
        </div>
        
        <!-- 例句（如有） -->
        <div v-if="detailWord.example" class="detail-section">
          <div class="detail-label">📝 例句</div>
          <div class="detail-content example">{{ detailWord.example }}</div>
        </div>
        
        <!-- 单词长度信息 -->
        <div class="detail-meta">
          <span class="meta-badge">{{ detailWord.length }} 字母</span>
          <span class="meta-badge">{{ detailWord.direction === 'across' ? '横向 →' : '纵向 ↓' }}</span>
        </div>
      </div>
    </div>

    <!-- 体力不足弹窗 -->
    <div v-if="showEnergyModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="energy-modal animate-bounce-in">
        <div class="energy-modal-icon">😴</div>
        <h3 class="energy-modal-title">体力不足</h3>
        <p class="energy-modal-text">
          当前体力不足以开始游戏
        </p>
        <div class="energy-modal-info">
          <span class="energy-current">当前体力: ⚡{{ energyModalInfo.current }}</span>
          <span class="energy-need">需要: ⚡{{ energyModalInfo.required }}</span>
        </div>
        <div class="energy-modal-buttons">
          <button @click="claimFreeEnergy" class="energy-modal-btn energy-claim-btn">
            🎁 领取体力 +30
          </button>
          <button @click="closeEnergyModalAndGoBack" class="energy-modal-btn energy-rest-btn">
            休息一下
          </button>
        </div>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="game-card text-center">
        <div class="text-4xl animate-spin mb-4">⏳</div>
        <p class="text-gray-600">正在加载关卡...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick, defineExpose } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'
import { useSettingsStore } from '../stores/settings'
import { useUserStore } from '../stores/user'
import { playTypeSound, playDeleteSound, playCorrectSound, playLevelCompleteSound, startBgMusic, stopBgMusic } from '../utils/audio'
import { energyApi, propsApi, gameApi, leaderboardApi, trackApi } from '../api/index.js'

const route = useRoute()
const router = useRouter()
const gameStore = useGameStore()
const settingsStore = useSettingsStore()
const userStore = useUserStore()

// 用户信息
const userAvatar = computed(() => userStore.avatar || '😊')
const userName = computed(() => userStore.nickname || '游客')

// 体力值
const userEnergy = ref(100)

// 各模式体力消耗配置（闯关10点，其他模式30点）
const ENERGY_COST = {
  campaign: 10,   // 闯关模式
  timed: 30,      // 计时模式
  pk: 30,         // PK模式
  endless: 30,    // 无限模式
}

// 加载用户体力（从本地存储读取）
function loadUserEnergy() {
  try {
    const saved = localStorage.getItem('user_energy')
    if (saved) {
      const energy = JSON.parse(saved)
      userEnergy.value = energy.value ?? 200
    } else {
      // 首次使用，初始化为200点
      userEnergy.value = 200
      localStorage.setItem('user_energy', JSON.stringify({
        value: 200,
        lastGrantTime: Date.now()
      }))
    }
  } catch (e) {
    userEnergy.value = 200
  }
}

// 保存用户体力到本地和后端（统一入口，只调用一次）
async function saveUserEnergy(value) {
  // 更新本地状态
  userEnergy.value = value
  
  // 保存到本地（使用lastGrantTime记录发放时间）
  try {
    const energy = {
      value: value,
      lastGrantTime: Date.now()
    }
    localStorage.setItem('user_energy', JSON.stringify(energy))
  } catch (e) {
    console.error('保存体力失败:', e)
  }
  
  // 异步同步到后端（不阻塞）
  energyApi.update(value).catch(e => {
    console.error('同步体力到后端失败:', e)
  })
}

// 消耗体力进入游戏
async function consumeEnergy(mode) {
  const cost = ENERGY_COST[mode] || 10
  
  console.log(`[体力] 尝试消耗体力: 模式=${mode}, 消耗=${cost}, 当前体力=${userEnergy.value}`)
  
  if (userEnergy.value < cost) {
    // 使用游戏内弹窗替代alert
    console.log(`[体力] 体力不足: 需要${cost}, 当前${userEnergy.value}`)
    energyModalInfo.value = { required: cost, current: userEnergy.value }
    showEnergyModal.value = true
    return false
  }
  
  // 扣除体力
  const newEnergy = userEnergy.value - cost
  console.log(`[体力] 扣除体力: ${userEnergy.value} - ${cost} = ${newEnergy}`)
  await saveUserEnergy(newEnergy)
  
  // 同时调用后端消耗接口记录（仅记录，不扣费）
  try {
    await energyApi.consume(mode)
  } catch (e) {
    console.error('后端记录体力消耗失败:', e)
  }
  
  return true
}

// 关闭体力不足弹窗并返回首页
function closeEnergyModalAndGoBack() {
  showEnergyModal.value = false
  gameStore.resetGame()
  router.push('/')
}

// 领取免费体力（观看广告等可扩展）
async function claimFreeEnergy() {
  const BONUS_ENERGY = 30
  
  try {
    // 调用后端API增加体力（带埋点追踪）
    const data = await trackApi.claimFreeEnergyTracked(BONUS_ENERGY, 'web')
    
    if (data) {
      userEnergy.value = data.energy
      localStorage.setItem('user_energy', JSON.stringify({ 
        value: data.energy, 
        lastGrantTime: Date.now()
      }))
    } else {
      // 后端失败时本地增加体力
      const newEnergy = Math.min(200, userEnergy.value + BONUS_ENERGY)
      userEnergy.value = newEnergy
      localStorage.setItem('user_energy', JSON.stringify({ 
        value: newEnergy, 
        lastGrantTime: Date.now()
      }))
    }
  } catch (e) {
    console.error('领取体力失败:', e)
    // 网络错误时本地增加体力
    const newEnergy = Math.min(200, userEnergy.value + BONUS_ENERGY)
    userEnergy.value = newEnergy
    localStorage.setItem('user_energy', JSON.stringify({ 
      value: newEnergy, 
      lastGrantTime: Date.now()
    }))
  }
  
  // 检查体力是否足够进入游戏
  const mode = route.params.mode || 'campaign'
  const cost = ENERGY_COST[mode] || 10
  
  if (userEnergy.value >= cost) {
    // 体力足够，关闭弹窗
    showEnergyModal.value = false
    
    // 调用统一的体力消耗函数（只扣一次，避免重复）
    const canPlay = await consumeEnergy(mode)
    if (canPlay) {
      // 继续加载游戏
      await continueGameInit(mode)
    }
  } else {
    // 体力仍不足，更新弹窗信息，保持弹窗显示，允许继续领取
    energyModalInfo.value = { required: cost, current: userEnergy.value }
  }
}

// 继续游戏初始化（体力检查通过后）
async function continueGameInit(mode) {
  // 优先从 localStorage 恢复词库
  const savedGroup = localStorage.getItem('current_group')
  const group = savedGroup || gameStore.currentGroup || 'primary'
  gameStore.currentGroup = group
  let level = 1
  
  // 启动背景音乐（如果设置开启）
  if (settingsStore.bgMusic) {
    startBgMusic(mode)
  }
  
  // 加载词库的关卡总数
  if (mode === 'campaign') {
    await loadMaxLevelCount(group)
  }
  
  // 获取本地存储的进度
  if (mode === 'campaign') {
    const savedLevel = localStorage.getItem(`campaign_level_${group}`)
    if (savedLevel) {
      level = parseInt(savedLevel)
    }
  } else if (mode === 'endless') {
    const savedLevel = localStorage.getItem('endless_level')
    if (savedLevel) {
      level = parseInt(savedLevel)
    }
  }
  
  // 获取难度设置
  const difficulty = localStorage.getItem('game_difficulty') || 'medium'
  
  // 计时/PK模式读取用户选择的时间
  let timerSeconds = 180  // 默认3分钟
  if (mode === 'timed' || mode === 'pk') {
    const savedDuration = localStorage.getItem('timed_duration')
    timerSeconds = savedDuration ? parseInt(savedDuration) : 180
  } else if (mode === 'endless') {
    timerSeconds = ENDLESS_TIME_PER_LEVEL
  }
  
  await gameStore.loadPuzzle(mode, level, group, timerSeconds, difficulty)
  
  loading.value = false
  
  // 初始化时检查已预填完成的单词
  gameStore.checkAllWords()
  
  // 启动计时器
  if (mode === 'timed' || mode === 'pk') {
    gameStore.startTimer(timerSeconds)
  } else if (mode === 'endless') {
    gameStore.startTimer(ENDLESS_TIME_PER_LEVEL)
  } else {
    gameStore.startTimer(0)
  }
  
  // 选择第一个未完成的单词
  selectFirstUnfinishedWord()
}

// 状态
const loading = ref(true)
const selectedWord = ref(null)
const currentRow = ref(0)
const currentCol = ref(0)
const showCompleteModal = ref(false)
const wordItemRefs = ref({})
const showWordDetail = ref(false)
const detailWord = ref(null)
const showEnergyModal = ref(false)  // 体力不足弹窗
const energyModalInfo = ref({ required: 5, current: 0 })  // 弹窗信息

// 道具状态
const hintLetterActive = ref(false)  // 提示字母道具 - 仅对当前选中单词有效
const speakPropActive = ref(false)  // 发音道具 - 正在播放发音
const hintLetterCount = ref(20)  // 提示字母道具剩余次数，每个账号初始20个
const speakPropCount = ref(20)  // 发音道具剩余次数，每个账号初始20个
const hintActiveWordId = ref(null)  // 提示生效的单词ID
const speakRepeatCount = ref(0)  // 发音重复计数
let speakRepeatTimeout = null  // 发音重复的定时器引用

// 计时/PK/无限模式的累计状态
const sessionScore = ref(0)  // 本局累计积分
const sessionLevelCount = ref(0)  // 本局过关数
const sessionWordsCount = ref(0)  // 本局完成单词数
const sessionStarted = ref(false)  // 本局是否已开始

// 无限模式每关时间限制（秒）
const ENDLESS_TIME_PER_LEVEL = 180  // 每关3分钟

// 计算属性
const modeTitle = computed(() => {
  const titles = {
    campaign: '🏰 闯关',
    endless: '♾️ 无限',
    timed: '⏱️ 计时',
    pk: '⚔️ PK'
  }
  return titles[gameStore.currentMode] || '游戏'
})

// 是否显示累计分数（计时/PK/无限模式）
const showSessionScore = computed(() => {
  return gameStore.currentMode === 'timed' || 
         gameStore.currentMode === 'pk' || 
         gameStore.currentMode === 'endless'
})

const modeIcon = computed(() => {
  const icons = {
    campaign: '🏰',
    endless: '♾️',
    timed: '⏱️',
    pk: '⚔️'
  }
  return icons[gameStore.currentMode] || '🎮'
})

const modeName = computed(() => {
  const names = {
    campaign: '闯关',
    endless: '无限',
    timed: '计时',
    pk: 'PK'
  }
  return names[gameStore.currentMode] || '游戏'
})

const isTimeWarning = computed(() => {
  if (gameStore.currentMode === 'timed' || gameStore.currentMode === 'pk') {
    return gameStore.timer < 60
  }
  return false
})

// 按clue_number排序的单词列表
const sortedWords = computed(() => {
  if (!gameStore.words || gameStore.words.length === 0) return []
  
  // 复制数组并排序
  return [...gameStore.words].sort((a, b) => {
    // 首先按clue_number排序
    const clueA = a.clue_number || 999
    const clueB = b.clue_number || 999
    if (clueA !== clueB) return clueA - clueB
    
    // 如果clue_number相同，横向优先于纵向
    if (a.direction !== b.direction) {
      return a.direction === 'across' ? -1 : 1
    }
    
    return 0
  })
})

// 计算当前星级（根据用时）
const currentStars = computed(() => {
  const seconds = gameStore.timer
  if (seconds <= 120) return 3  // 2分钟内三星
  if (seconds <= 180) return 2  // 3分钟内两星
  return 1  // 5分钟以上一星（3分钟以上也算1星）
})

// 最大关卡数（根据词库动态获取）
const maxLevelCount = ref(180)

const isLastLevel = computed(() => {
  // 使用动态获取的最大关卡数
  return gameStore.currentMode === 'campaign' && gameStore.currentLevel >= maxLevelCount.value
})

// 奖励状态
const showRewardChoice = ref(false)  // 显示奖励选择
const rewardClaimed = ref(false)  // 奖励是否已领取
const earnedRewards = ref([])  // 获得的奖励列表

// 从后端获取随机奖励（三品类随机两个，由后端计算，防止前端篡改）
async function fetchRewardsFromBackend() {
  try {
    const data = await gameApi.generateReward()
    if (data.success) {
      return data.rewards
    }
  } catch (error) {
    console.error('获取奖励失败:', error)
  }
  // 如果后端请求失败，返回默认奖励
  return [
    { type: 'energy', name: '体力', icon: '⚡', value: 5 },
    { type: 'hint', name: '提示', icon: '💡', value: 1 }
  ]
}

// 领取奖励（调用后端API完成领取，在本地值基础上累加奖励）
async function claimRewards() {
  if (rewardClaimed.value) return
  if (earnedRewards.value.length === 0) return
  
  try {
    // 先标记为已领取，防止重复点击
    rewardClaimed.value = true
    
    // 计算新的体力值（累加所有体力奖励）
    let totalEnergyReward = 0
    
    // 直接使用已显示的 earnedRewards 来累加（确保"所见即所得"）
    for (const reward of earnedRewards.value) {
      if (reward.type === 'energy') {
        totalEnergyReward += reward.value
        console.log(`领取体力奖励 +${reward.value}`)
      } else if (reward.type === 'hint') {
        // 提示道具累加
        hintLetterCount.value += reward.value
        console.log(`领取提示 +${reward.value}，当前提示: ${hintLetterCount.value}`)
      } else if (reward.type === 'speak') {
        // 发音道具累加
        speakPropCount.value += reward.value
        console.log(`领取发音 +${reward.value}，当前发音: ${speakPropCount.value}`)
      }
    }
    
    // 如果有体力奖励，统一调用 saveUserEnergy 更新（确保本地+后端同步）
    if (totalEnergyReward > 0) {
      const newEnergy = Math.min(200, userEnergy.value + totalEnergyReward)
      console.log(`[体力] 领奖增加体力: ${userEnergy.value} + ${totalEnergyReward} = ${newEnergy}`)
      await saveUserEnergy(newEnergy)  // 统一使用 saveUserEnergy，确保同步
    }
    
    // 保存道具次数到本地
    savePropCounts()
    
    // 同步积分到后端
    await syncScoreToBackend(gameStore.score)
    
    // 通知后端记录领取（传入前端的奖励列表，后端使用相同数据更新）
    gameApi.claimReward(
      gameStore.currentLevel,
      gameStore.currentGroup,
      currentStars.value,
      gameStore.timer,
      earnedRewards.value
    ).catch(e => console.warn('后端记录领取失败:', e))
    
  } catch (error) {
    console.error('领取奖励失败:', error)
  }
}

// 进入下一关（闯关模式扣除10点体力）
async function goNextLevel() {
  // 检查并消耗体力（闯关模式每关10点）
  const canPlay = await consumeEnergy('campaign')
  if (!canPlay) {
    // 体力不足，显示弹窗
    return
  }
  
  showCompleteModal.value = false
  showRewardChoice.value = false
  rewardClaimed.value = false
  earnedRewards.value = []
  resetLevelProps()
  gameStore.nextLevel()
  
  // 下一关开始后选择第一个未完成的单词
  nextTick(() => {
    selectFirstUnfinishedWord()
  })
}

// 选择第一个未完成的单词（使用排序后的列表）
function selectFirstUnfinishedWord() {
  const unfinishedWords = sortedWords.value.filter(w => !isWordCompleted(w.id))
  if (unfinishedWords.length > 0) {
    selectWord(unfinishedWords[0])
  }
}

// 判断字母是否被需要（高亮提示）- 只对使用道具时选中的单词生效
function isLetterNeeded(letter) {
  if (!hintLetterActive.value) return false  // 道具未激活时不高亮
  if (!selectedWord.value) return false
  // 只有当前选中的单词是使用道具时的单词才高亮
  if (selectedWord.value.id !== hintActiveWordId.value) return false
  const word = selectedWord.value.word?.toUpperCase() || ''
  return word.includes(letter)
}

// 使用提示字母道具 - 仅对当前选中单词有效
function useHintLetterProp() {
  if (hintLetterCount.value <= 0) return
  if (!selectedWord.value) return  // 必须先选中一个单词
  hintLetterActive.value = true
  hintActiveWordId.value = selectedWord.value.id  // 记录生效的单词ID
  hintLetterCount.value--
  savePropCounts()  // 保存道具次数到账号
  
  // 埋点：记录道具使用
  trackApi.trackPropUsage('hint_letter', gameStore.currentMode, gameStore.currentGroup, gameStore.currentLevel, 'web')
}

// 使用发音道具 - 朗读当前选中单词发音三遍
function useSpeakProp() {
  if (speakPropCount.value <= 0) return
  if (!selectedWord.value) return  // 必须先选中一个单词
  if (speakPropActive.value) return  // 正在播放中，不重复触发
  
  speakPropActive.value = true
  speakPropCount.value--
  savePropCounts()  // 保存道具次数到账号
  
  // 埋点：记录道具使用
  trackApi.trackPropUsage('speak', gameStore.currentMode, gameStore.currentGroup, gameStore.currentLevel, 'web')
  
  // 朗读当前单词三遍
  const word = selectedWord.value.word
  speakRepeatCount.value = 0
  speakWordRepeated(word, 3)
}

// 重复朗读单词
function speakWordRepeated(word, times) {
  if (speakRepeatCount.value >= times) {
    speakPropActive.value = false
    speakRepeatCount.value = 0
    speakRepeatTimeout = null
    return
  }
  
  speakRepeatCount.value++
  
  // 使用游戏store的发音功能
  gameStore.speakWord(word)
  
  // 延迟后继续下一遍（给发音留出时间）
  speakRepeatTimeout = setTimeout(() => {
    speakWordRepeated(word, times)
  }, 1200)
}

// 停止发音重复（清理资源）
function stopSpeakRepeat() {
  if (speakRepeatTimeout) {
    clearTimeout(speakRepeatTimeout)
    speakRepeatTimeout = null
  }
  speakPropActive.value = false
  speakRepeatCount.value = 0
}

// 从账号加载道具次数（每个账号初始20个，用完即止）
function loadPropCounts() {
  try {
    const saved = localStorage.getItem('game_props')
    if (saved) {
      const props = JSON.parse(saved)
      // 如果有存储值则使用存储值，否则初始化为20
      hintLetterCount.value = props.hintLetterCount ?? 20
      speakPropCount.value = props.speakPropCount ?? 20
    } else {
      // 首次使用，初始化为20个并保存
      hintLetterCount.value = 20
      speakPropCount.value = 20
      savePropCounts()
    }
  } catch (e) {
    // 使用默认值20
    hintLetterCount.value = 20
    speakPropCount.value = 20
  }
}

// 保存道具次数到账号
function savePropCounts() {
  try {
    const props = {
      hintLetterCount: hintLetterCount.value,
      speakPropCount: speakPropCount.value
    }
    localStorage.setItem('game_props', JSON.stringify(props))
  } catch (e) {
    // 忽略保存错误
  }
}

// 同步道具到后端
async function syncPropsToBackend() {
  try {
    await propsApi.update(hintLetterCount.value, speakPropCount.value)
    console.log('道具同步成功')
  } catch (e) {
    console.error('同步道具到后端失败:', e)
  }
}

// 同步积分到后端
async function syncScoreToBackend(score) {
  try {
    await gameApi.submitScore(score, gameStore.currentGroup, gameStore.currentLevel)
    console.log('积分同步成功')
  } catch (e) {
    console.error('同步积分到后端失败:', e)
  }
}

// 从后端加载用户数据（体力、道具、积分）- 仅在游戏结束时调用同步
async function loadUserDataFromBackend() {
  try {
    // 加载体力（仅当后端数据比本地新时更新）
    const energyData = await energyApi.get()
    if (energyData && energyData.energy !== undefined) {
      // 只有后端数据更大时才更新（防止覆盖刚扣除的体力）
      if (energyData.energy > userEnergy.value) {
        userEnergy.value = energyData.energy
        localStorage.setItem('user_energy', JSON.stringify({ 
          value: energyData.energy, 
          lastUpdate: Date.now() 
        }))
      }
    }
    
    // 加载道具
    const propsData = await propsApi.get()
    if (propsData && propsData.hintLetterCount !== undefined) {
      // 只有后端数据更大时才更新
      if (propsData.hintLetterCount > hintLetterCount.value) {
        hintLetterCount.value = propsData.hintLetterCount
      }
      if ((propsData.showTranslationCount || 20) > speakPropCount.value) {
        speakPropCount.value = propsData.showTranslationCount || 20
      }
      savePropCounts()
    }
  } catch (e) {
    console.warn('从后端加载用户数据失败，使用本地数据:', e)
  }
}

// 重置当关道具效果（但不重置次数）
function resetLevelProps() {
  hintLetterActive.value = false
  speakPropActive.value = false
  hintActiveWordId.value = null
  speakRepeatCount.value = 0
}

// 获取单词提示（基于网格中实际显示的内容，包含共用格子的字母）
function getWordHint(word) {
  const len = word.length
  const result = []
  
  // 遍历单词的每个位置，检查格子中是否有字母（无论来源）
  for (let i = 0; i < len; i++) {
    let row = word.start_row
    let col = word.start_col
    
    if (word.direction === 'across') {
      col += i
    } else {
      row += i
    }
    
    // 获取该格子的当前答案（包括预填和共用格子的字母）
    const answer = gameStore.getAnswer(row, col)
    // 如果格子有内容（预填或其他单词填入的共用字母），显示该字母
    if (answer) {
      result.push(answer)
    } else {
      result.push('_')
    }
  }
  
  return result
}

// 数字转中文
function chineseNumber(num) {
  const chars = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
  if (num <= 10) return chars[num]
  if (num < 20) return '十' + (num % 10 === 0 ? '' : chars[num % 10])
  if (num < 100) {
    const tens = Math.floor(num / 10)
    const ones = num % 10
    return chars[tens] + '十' + (ones === 0 ? '' : chars[ones])
  }
  return num.toString()
}

// 获取格子的线索编号
function getClueNumber(row, col) {
  const clueNumbers = gameStore.clueNumbers
  if (!clueNumbers || !clueNumbers[row]) return null
  return clueNumbers[row][col]
}

// 方法
function getCellClass(row, col, cell) {
  const classes = ['letter-cell-new']
  
  if (cell === null) {
    classes.push('empty')
    return classes.join(' ')
  }
  
  // 检查是否是预填字母
  const isPrefilled = gameStore.isPrefilledCell(row, col)
  
  // 检查是否属于已完成的单词
  const isCompleted = isCellInCompletedWord(row, col)
  
  if (isCompleted) {
    classes.push('locked')
  } else if (isPrefilled) {
    classes.push('prefilled')
  } else if (isCurrentCell(row, col)) {
    classes.push('active')
  } else if (isCellInSelectedWord(row, col)) {
    classes.push('in-word')
  }
  
  return classes.join(' ')
}

// 检查格子是否属于已完成的单词
function isCellInCompletedWord(row, col) {
  for (const word of gameStore.completedWords) {
    if (word.direction === 'across') {
      if (row === word.start_row && 
          col >= word.start_col && 
          col < word.start_col + word.length) {
        return true
      }
    } else {
      if (col === word.start_col && 
          row >= word.start_row && 
          row < word.start_row + word.length) {
        return true
      }
    }
  }
  return false
}

function isCurrentCell(row, col) {
  return row === currentRow.value && col === currentCol.value
}

function isCellInSelectedWord(row, col) {
  if (!selectedWord.value) return false
  
  const word = selectedWord.value
  if (word.direction === 'across') {
    return row === word.start_row && 
           col >= word.start_col && 
           col < word.start_col + word.length
  } else {
    return col === word.start_col && 
           row >= word.start_row && 
           row < word.start_row + word.length
  }
}

// 检查格子是否锁定（只锁定预填字母，已完成单词可以修改）
function isCellLocked(row, col) {
  // 只有预填字母是锁定的
  if (gameStore.isPrefilledCell(row, col)) {
    return true
  }
  // 已完成的单词不再锁定，允许用户修改
  return false
}

function isWordCompleted(wordId) {
  return gameStore.completedWords.some(w => w.id === wordId)
}

function getCompletedWordInfo(wordId) {
  const completed = gameStore.completedWords.find(w => w.id === wordId)
  return completed || {}
}

function handleCellClick(row, col, cell) {
  if (cell === null) return
  // 如果格子已锁定，不能选择编辑
  if (isCellLocked(row, col)) return
  
  currentRow.value = row
  currentCol.value = col
  
  // 选择该格子所属的单词
  selectWordAtCell(row, col)
}

function selectWordAtCell(row, col) {
  // 优先选择横向单词
  for (const word of gameStore.words) {
    if (word.direction === 'across') {
      if (row === word.start_row && 
          col >= word.start_col && 
          col < word.start_col + word.length) {
        selectedWord.value = word
        return
      }
    }
  }
  
  // 再选择纵向单词
  for (const word of gameStore.words) {
    if (word.direction === 'down') {
      if (col === word.start_col && 
          row >= word.start_row && 
          row < word.start_row + word.length) {
        selectedWord.value = word
        return
      }
    }
  }
}

function selectWord(word) {
  selectedWord.value = word
  
  // 滚动到选中的单词项
  nextTick(() => {
    const el = wordItemRefs.value[word.id]
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  })
  
  // 移动到单词的第一个未锁定的格子
  for (let i = 0; i < word.length; i++) {
    let r = word.start_row
    let c = word.start_col
    if (word.direction === 'across') {
      c += i
    } else {
      r += i
    }
    if (!isCellLocked(r, c)) {
      currentRow.value = r
      currentCol.value = c
      return
    }
  }
  // 如果所有格子都锁定了，选第一个
  currentRow.value = word.start_row
  currentCol.value = word.start_col
}

function inputLetter(letter) {
  // 如果当前格子已锁定，不允许输入
  if (isCellLocked(currentRow.value, currentCol.value)) return
  
  gameStore.setAnswer(currentRow.value, currentCol.value, letter)
  playSound('type')
  checkWordsAtCell(currentRow.value, currentCol.value)
  moveToNextCell()
}

function deleteLetter() {
  // 如果当前格子已锁定，不允许删除
  if (isCellLocked(currentRow.value, currentCol.value)) {
    moveToPrevCell()
    return
  }
  
  playSound('delete')
  
  const currentAnswer = gameStore.getAnswer(currentRow.value, currentCol.value)
  if (currentAnswer) {
    gameStore.setAnswer(currentRow.value, currentCol.value, '')
  } else {
    moveToPrevCell()
    if (!isCellLocked(currentRow.value, currentCol.value)) {
      gameStore.setAnswer(currentRow.value, currentCol.value, '')
    }
  }
}

function moveToNextCell() {
  if (!selectedWord.value) {
    return
  }
  
  const word = selectedWord.value
  if (word.direction === 'across') {
    // 横向单词，向右移动，跳过锁定格子
    let nextCol = currentCol.value + 1
    while (nextCol < word.start_col + word.length && isCellLocked(word.start_row, nextCol)) {
      nextCol++
    }
    if (nextCol < word.start_col + word.length) {
      currentCol.value = nextCol
    } else {
      // 到达单词末尾，尝试移动到下一个未完成的单词
      moveToNextUnfinishedWord()
    }
  } else {
    // 纵向单词，向下移动，跳过锁定格子
    let nextRow = currentRow.value + 1
    while (nextRow < word.start_row + word.length && isCellLocked(nextRow, word.start_col)) {
      nextRow++
    }
    if (nextRow < word.start_row + word.length) {
      currentRow.value = nextRow
    } else {
      moveToNextUnfinishedWord()
    }
  }
}

function moveToPrevCell() {
  if (!selectedWord.value) {
    return
  }
  
  const word = selectedWord.value
  if (word.direction === 'across') {
    let prevCol = currentCol.value - 1
    while (prevCol >= word.start_col && isCellLocked(word.start_row, prevCol)) {
      prevCol--
    }
    if (prevCol >= word.start_col) {
      currentCol.value = prevCol
    }
  } else {
    let prevRow = currentRow.value - 1
    while (prevRow >= word.start_row && isCellLocked(prevRow, word.start_col)) {
      prevRow--
    }
    if (prevRow >= word.start_row) {
      currentRow.value = prevRow
    }
  }
}

function moveToNextUnfinishedWord() {
  // 找到下一个未完成的单词（使用排序后的列表）
  const unfinishedWords = sortedWords.value.filter(w => !isWordCompleted(w.id))
  if (unfinishedWords.length > 0) {
    const currentIndex = unfinishedWords.findIndex(w => w.id === selectedWord.value?.id)
    const nextIndex = (currentIndex + 1) % unfinishedWords.length
    selectWord(unfinishedWords[nextIndex])
  }
}

function checkWordsAtCell(row, col) {
  // 每次输入字母后扫描所有未完成的单词
  // 因为一个格子可能影响多个单词（横纵交叉）
  let anyCorrect = false
  let completedWordIds = []
  
  for (const word of gameStore.words) {
    if (isWordCompleted(word.id)) continue
    
    const isCorrect = gameStore.checkWord(word.id)
    if (isCorrect) {
      anyCorrect = true
      completedWordIds.push(word.id)
    }
  }
  
  if (anyCorrect) {
    playSound('correct')
    
    // 如果当前选中的单词刚被完成，自动选择下一个未完成的单词
    if (selectedWord.value && completedWordIds.includes(selectedWord.value.id)) {
      nextTick(() => {
        selectFirstUnfinishedWord()
      })
    }
  }
}

function speakWord(text, voiceType = null) {
  gameStore.speakWord(text, voiceType)
}

// 打开单词详情卡片
function openWordDetail(word) {
  detailWord.value = word
  showWordDetail.value = true
}

// 关闭单词详情卡片
function closeWordDetail() {
  showWordDetail.value = false
  detailWord.value = null
}

function playSound(type) {
  switch (type) {
    case 'type':
      playTypeSound()
      break
    case 'correct':
      playCorrectSound()
      break
    case 'delete':
      playDeleteSound()
      break
    case 'levelComplete':
      playLevelCompleteSound()
      break
  }
}

function goBack() {
  gameStore.resetGame()
  router.push('/')
}

// 跳转到排行榜
function goToLeaderboard() {
  gameStore.resetGame()
  router.push('/leaderboard')
}

// 旧的nextLevel保留给其他模式使用
async function nextLevel() {
  showCompleteModal.value = false
  showRewardChoice.value = false
  rewardClaimed.value = false
  earnedRewards.value = []
  resetLevelProps()  // 重置道具效果
  await gameStore.nextLevel()
  
  // 下一关开始后选择第一个未完成的单词
  nextTick(() => {
    selectFirstUnfinishedWord()
  })
}

function replayLevel() {
  showCompleteModal.value = false
  // 重新加载当前关卡
  gameStore.loadPuzzle('campaign', gameStore.currentLevel, gameStore.currentGroup)
  gameStore.startTimer()
  // 选择第一个单词
  if (gameStore.words.length > 0) {
    selectWord(gameStore.words[0])
  }
}

// 再玩一次（计时/PK/无限模式 - 需要扣除体力）
async function playAgain() {
  const mode = gameStore.currentMode
  
  // 检查并消耗体力
  const canPlay = await consumeEnergy(mode)
  if (!canPlay) {
    // 体力不足，显示弹窗（consumeEnergy 已处理）
    return
  }
  
  // 重置累计状态
  sessionScore.value = 0
  sessionLevelCount.value = 0
  sessionWordsCount.value = 0
  sessionStarted.value = true
  timedModeEnded.value = false
  
  showCompleteModal.value = false
  showRewardChoice.value = false
  rewardClaimed.value = false
  earnedRewards.value = []
  resetLevelProps()
  
  // 获取难度设置
  const difficulty = localStorage.getItem('game_difficulty') || 'medium'
  
  // 根据模式设置计时
  let timerSeconds = 180  // 默认3分钟
  if (mode === 'endless') {
    timerSeconds = ENDLESS_TIME_PER_LEVEL
  } else if (mode === 'pk' || mode === 'timed') {
    // 读取用户选择的时间（再来一次使用相同时间）
    const savedDuration = localStorage.getItem('timed_duration')
    timerSeconds = savedDuration ? parseInt(savedDuration) : 180
  }
  
  // 加载新关卡
  await gameStore.loadPuzzle(mode, 0, gameStore.currentGroup, timerSeconds, difficulty)
  
  // 检查预填完成的单词
  gameStore.checkAllWords()
  
  // 启动计时器
  if (mode === 'timed' || mode === 'pk') {
    gameStore.startTimer(timerSeconds)  // 倒计时
  } else if (mode === 'endless') {
    gameStore.startTimer(ENDLESS_TIME_PER_LEVEL)  // 倒计时
  }
  
  // 选择第一个未完成的单词
  nextTick(() => {
    selectFirstUnfinishedWord()
  })
}

// 计时模式时间到结束标记
const timedModeEnded = ref(false)

// 监听计时器 - 计时/PK/无限模式倒计时结束自动结束游戏
watch(() => gameStore.timer, async (newTimer) => {
  const mode = gameStore.currentMode
  
  // 计时/PK模式检查总时间结束
  if (mode === 'timed' || mode === 'pk') {
    if (newTimer <= 0 && !timedModeEnded.value && !showCompleteModal.value) {
      timedModeEnded.value = true
      await handleTimedModeEnd()
    }
  }
  
  // 无限模式检查每关时间结束
  if (mode === 'endless') {
    if (newTimer <= 0 && !timedModeEnded.value && !showCompleteModal.value) {
      timedModeEnded.value = true
      await handleEndlessModeTimeUp()
    }
  }
})

// 处理无限模式单关时间用尽
async function handleEndlessModeTimeUp() {
  gameStore.stopTimer()
  playSound('levelComplete')
  
  // 包含当前未完成的单词数也计入统计
  const wordsCompleted = gameStore.completedWords.length
  const scoreEarned = wordsCompleted * 10
  sessionScore.value += scoreEarned
  sessionWordsCount.value += wordsCompleted
  
  // 提交游戏数据
  await submitGameData('endless', sessionWordsCount.value, sessionScore.value)
  
  // 提交排行榜
  await submitLeaderboardScore('endless_level', sessionLevelCount.value)
  await submitLeaderboardScore('endless_score', sessionScore.value)
  
  // 更新本地统计
  updateLocalStats(sessionWordsCount.value, sessionScore.value)
  
  // 从后端获取奖励
  earnedRewards.value = await fetchRewardsFromBackend()
  showRewardChoice.value = true
  rewardClaimed.value = false
  
  setTimeout(() => {
    showCompleteModal.value = true
  }, 300)
}

// 处理计时/PK模式时间到
async function handleTimedModeEnd() {
  gameStore.stopTimer()
  playSound('levelComplete')
  
  // 包含当前未完成的单词数也计入统计
  const wordsCompleted = gameStore.completedWords.length
  const scoreEarned = wordsCompleted * 10
  sessionScore.value += scoreEarned
  sessionWordsCount.value += wordsCompleted
  
  // 提交游戏数据到数据库
  const mode = gameStore.currentMode
  await submitGameData(mode, sessionWordsCount.value, sessionScore.value)
  
  // 提交排行榜
  if (mode === 'timed') {
    await submitLeaderboardScore('timed_words', sessionWordsCount.value)
    await submitLeaderboardScore('timed_score', sessionScore.value)
  } else if (mode === 'pk') {
    await submitLeaderboardScore('pk_words', sessionWordsCount.value)
    await submitLeaderboardScore('pk_score', sessionScore.value)
  }
  
  // 更新本地统计
  updateLocalStats(wordsCompleted, scoreEarned)
  
  // 从后端获取奖励（计时/PK模式结束后也显示奖励）
  earnedRewards.value = await fetchRewardsFromBackend()
  showRewardChoice.value = true
  rewardClaimed.value = false
  
  setTimeout(() => {
    showCompleteModal.value = true
  }, 300)
}

// 监听关卡完成
watch(() => gameStore.isLevelComplete, async (complete) => {
  if (complete) {
    // 计算本关分数（每个单词10分）
    const wordsCompleted = gameStore.completedWords.length
    const scoreEarned = wordsCompleted * 10
    
    // 埋点：记录关卡完成
    const elapsedSeconds = gameStore.getElapsedSeconds ? gameStore.getElapsedSeconds() : null
    trackApi.trackLevelComplete(
      gameStore.currentGroup, 
      gameStore.currentLevel, 
      3, // 默认3星
      scoreEarned, 
      elapsedSeconds, 
      'web'
    )
    
    // 根据模式处理不同逻辑
    const mode = gameStore.currentMode
    
    if (mode === 'timed' || mode === 'pk') {
      // 计时/PK模式：不停止计时，累加分数，自动续下一关
      playSound('levelComplete')
      sessionScore.value += scoreEarned
      sessionLevelCount.value++
      sessionWordsCount.value += wordsCompleted
      
      // 更新本地统计（不显示弹窗）
      updateLocalStats(wordsCompleted, scoreEarned)
      
      // 自动加载下一关（不停止计时器，不显示弹窗）
      await autoNextLevel()
      
    } else if (mode === 'endless') {
      // 无限模式：停止计时，累加分数，重置计时器，自动续下一关
      gameStore.stopTimer()
      playSound('levelComplete')
      sessionScore.value += scoreEarned
      sessionLevelCount.value++
      sessionWordsCount.value += wordsCompleted
      
      // 更新无限模式进度
      updateEndlessProgress()
      updateLocalStats(wordsCompleted, scoreEarned)
      
      // 自动加载下一关并重置计时器
      await autoNextLevel()
      // 重新启动计时器（每关独立计时）
      gameStore.startTimer(ENDLESS_TIME_PER_LEVEL)
      
    } else {
      // 闯关模式：保持原有逻辑，显示通关弹窗
      gameStore.stopTimer()
      playSound('levelComplete')
      
      // 提交游戏数据到数据库
      await submitGameData(mode, wordsCompleted, scoreEarned)
      
      // 保存进度
      gameStore.saveLevelProgress(gameStore.currentLevel)
      // 提交排行榜
      await submitLeaderboardScore('campaign_level', gameStore.currentLevel)
      await submitLeaderboardScore('campaign_score', scoreEarned)
      
      // 更新本地统计
      updateLocalStats(wordsCompleted, scoreEarned)
      
      // 从后端获取奖励
      earnedRewards.value = await fetchRewardsFromBackend()
      showRewardChoice.value = true
      rewardClaimed.value = false
      
      setTimeout(() => {
        showCompleteModal.value = true
      }, 500)
    }
  }
})

// 自动加载下一关（用于计时/PK/无限模式的连续游戏）
async function autoNextLevel() {
  // 重置游戏状态
  resetLevelProps()
  
  // 获取难度设置
  const difficulty = localStorage.getItem('game_difficulty') || 'medium'
  
  // 加载新关卡（使用相同的词库和难度）
  await gameStore.loadPuzzle(
    gameStore.currentMode, 
    0,  // 随机关卡
    gameStore.currentGroup, 
    gameStore.currentMode === 'endless' ? ENDLESS_TIME_PER_LEVEL : 180, 
    difficulty
  )
  
  // 检查预填完成的单词
  gameStore.checkAllWords()
  
  // 选择第一个未完成的单词
  nextTick(() => {
    selectFirstUnfinishedWord()
  })
}

// 无限模式关卡计数
const endlessLevelCount = ref(1)

// 更新无限模式进度
function updateEndlessProgress() {
  endlessLevelCount.value++
  localStorage.setItem('endless_level_count', endlessLevelCount.value.toString())
}

// 加载无限模式进度
function loadEndlessProgress() {
  const saved = localStorage.getItem('endless_level_count')
  if (saved) {
    endlessLevelCount.value = parseInt(saved) || 1
  }
}

// 提交排行榜分数
async function submitLeaderboardScore(lbType, value) {
  try {
    const userId = getUserId()
    const userInfo = getUserInfo()
    
    if (!userId) return
    
    await leaderboardApi.submit(lbType, {
      user_id: userId,
      nickname: userInfo.nickname || '游客',
      avatar: userInfo.avatar || '😊',
      group: gameStore.currentGroup,
      value: value,
      extra: {
        time: gameStore.timer,
        level: gameStore.currentLevel
      }
    })
    console.log(`排行榜提交成功: ${lbType} = ${value}`)
  } catch (error) {
    console.error('排行榜提交失败:', error)
  }
}

// 提交PK结果
async function submitPKResult(result) {
  try {
    const userId = getUserId()
    const userInfo = getUserInfo()
    
    if (!userId) return
    
    // 新API：提交到数据库
    await gameApi.submitPkResult(
      gameStore.currentGroup,
      result,
      gameStore.completedWords.length,
      gameStore.timer
    )
    
    // 兼容旧API
    await leaderboardApi.submit('pk', {
      user_id: userId,
      nickname: userInfo.nickname || '游客',
      avatar: userInfo.avatar || '😊',
      group: gameStore.currentGroup,
      result: result  // "win", "lose", "draw"
    })
    
    // 更新本地PK统计
    updatePKStats(result)
    console.log(`PK结果提交成功: ${result}`)
  } catch (error) {
    console.error('PK结果提交失败:', error)
  }
}

// 提交游戏数据到数据库
async function submitGameData(gameMode, wordsCompleted, scoreEarned) {
  try {
    // 根据模式计算关卡数
    let levelReached = 0
    if (gameMode === 'campaign') {
      levelReached = gameStore.currentLevel
    } else if (gameMode === 'endless') {
      levelReached = endlessLevelCount.value
    }
    
    await gameApi.submit({
      game_mode: gameMode,
      vocab_group: gameStore.currentGroup,
      score: scoreEarned,
      words_count: wordsCompleted,
      level_reached: levelReached,
      duration_seconds: gameStore.timer,
      result: null,
      extra_data: {
        grid_size: gameStore.gridSize,
        difficulty: gameStore.currentDifficulty
      }
    })
    
    console.log(`游戏数据提交成功: ${gameMode}, 分数=${scoreEarned}`)
  } catch (error) {
    console.error('游戏数据提交失败:', error)
  }
}

// 获取用户ID
function getUserId() {
  const match = document.cookie.match(/user_id=([^;]+)/)
  return match ? match[1] : null
}

// 获取用户信息
function getUserInfo() {
  try {
    const saved = localStorage.getItem('user_info')
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {}
  return { nickname: '游客', avatar: '😊' }
}

// 更新本地统计
function updateLocalStats(wordsCompleted, scoreEarned) {
  try {
    const key = 'myStats'
    let stats = {
      totalGames: 0,
      totalWords: 0,
      totalScore: 0,
      highScore: 0,
      campaignLevel: 1
    }
    
    const saved = localStorage.getItem(key)
    if (saved) {
      stats = JSON.parse(saved)
    }
    
    stats.totalGames = (stats.totalGames || 0) + 1
    stats.totalWords = (stats.totalWords || 0) + wordsCompleted
    stats.totalScore = (stats.totalScore || 0) + scoreEarned
    
    if (scoreEarned > (stats.highScore || 0)) {
      stats.highScore = scoreEarned
    }
    
    if (gameStore.currentMode === 'campaign' && gameStore.currentLevel > (stats.campaignLevel || 1)) {
      stats.campaignLevel = gameStore.currentLevel
    }
    
    localStorage.setItem(key, JSON.stringify(stats))
  } catch (e) {
    console.error('保存统计失败:', e)
  }
}

// 更新PK统计
function updatePKStats(result) {
  try {
    const key = 'pk_stats'
    let stats = { wins: 0, draws: 0, losses: 0, games: 0 }
    
    const saved = localStorage.getItem(key)
    if (saved) {
      stats = JSON.parse(saved)
    }
    
    stats.games = (stats.games || 0) + 1
    if (result === 'win') {
      stats.wins = (stats.wins || 0) + 1
    } else if (result === 'draw') {
      stats.draws = (stats.draws || 0) + 1
    } else {
      stats.losses = (stats.losses || 0) + 1
    }
    
    localStorage.setItem(key, JSON.stringify(stats))
  } catch (e) {
    console.error('保存PK统计失败:', e)
  }
}

// 暴露PK结果提交方法给外部使用
defineExpose({ submitPKResult })

// 加载词库的关卡总数（从静态数据）
async function loadMaxLevelCount(group) {
  try {
    // 使用gameStore的方法从静态数据获取
    const count = await gameStore.getGroupLevelCount(group)
    if (count > 0) {
      maxLevelCount.value = count
    } else {
      // 默认180关
      maxLevelCount.value = 180
    }
  } catch (e) {
    console.warn('获取关卡总数失败，使用默认值', e)
    maxLevelCount.value = 180
  }
}

// 初始化
onMounted(async () => {
  loading.value = true
  
  // 先从本地加载道具和体力（快速响应）
  loadPropCounts()
  loadUserEnergy()
  
  // 后台静默同步后端数据（不阻塞游戏加载）
  loadUserDataFromBackend().catch(e => console.warn('后台同步用户数据:', e))
  
  // 加载无限模式进度
  loadEndlessProgress()
  
  // 重置当关道具效果
  resetLevelProps()
  
  // 重置奖励状态
  showRewardChoice.value = false
  rewardClaimed.value = false
  earnedRewards.value = []
  
  // 重置计时模式结束标记
  timedModeEnded.value = false
  
  // 重置累计状态（计时/PK/无限模式）
  sessionScore.value = 0
  sessionLevelCount.value = 0
  sessionWordsCount.value = 0
  sessionStarted.value = true
  
  const mode = route.params.mode
  // 优先从 localStorage 恢复词库，防止页面刷新后丢失
  const savedGroup = localStorage.getItem('current_group')
  const group = savedGroup || gameStore.currentGroup || 'primary'
  // 同步到 store
  gameStore.currentGroup = group
  let level = 1
  
  // 检查并消耗体力
  const canPlay = await consumeEnergy(mode)
  if (!canPlay) {
    // 体力不足，显示弹窗等待用户操作（不要立即跳转）
    loading.value = false
    // 弹窗已在 consumeEnergy 中设置，等用户点击按钮后再跳转
    return
  }
  
  // 启动背景音乐（如果设置开启），根据模式使用不同音乐
  if (settingsStore.bgMusic) {
    startBgMusic(mode)
  }
  
  // 加载词库的关卡总数
  if (mode === 'campaign') {
    await loadMaxLevelCount(group)
  }
  
  // 获取本地存储的进度
  if (mode === 'campaign') {
    const savedLevel = localStorage.getItem(`campaign_level_${group}`)
    if (savedLevel) {
      level = parseInt(savedLevel)
    }
  } else if (mode === 'endless') {
    // 无限模式 - 读取选择的关卡
    const savedLevel = localStorage.getItem('endless_level')
    if (savedLevel) {
      level = parseInt(savedLevel)
    }
  }
  
  // 获取难度设置（无限/计时/PK模式）
  const difficulty = localStorage.getItem('game_difficulty') || 'medium'
  
  // 根据模式设置计时
  let timerSeconds = 180  // 默认3分钟
  if (mode === 'pk' || mode === 'timed') {
    // 读取用户选择的时间（3分/5分/10分）
    const savedDuration = localStorage.getItem('timed_duration')
    timerSeconds = savedDuration ? parseInt(savedDuration) : 180
  } else if (mode === 'endless') {
    timerSeconds = ENDLESS_TIME_PER_LEVEL  // 无限模式每关时间
  }
  
  await gameStore.loadPuzzle(mode, level, group, timerSeconds, difficulty)
  
  loading.value = false
  
  // 初始化时检查已预填完成的单词（有些单词可能因为预填字母已经全部显示）
  gameStore.checkAllWords()
  
  // 启动计时器
  if (mode === 'timed' || mode === 'pk') {
    // 计时/PK模式使用倒计时
    gameStore.startTimer(timerSeconds)
  } else if (mode === 'endless') {
    // 无限模式每关倒计时
    gameStore.startTimer(ENDLESS_TIME_PER_LEVEL)
  } else {
    // 闯关模式使用正计时，从0开始
    gameStore.startTimer(0)
  }
  
  // 选择第一个未完成的单词
  selectFirstUnfinishedWord()
})

onUnmounted(() => {
  // 停止游戏计时器
  gameStore.stopTimer()
  // 停止背景音乐
  stopBgMusic()
  // 停止发音重复定时器
  stopSpeakRepeat()
  // 清理 DOM 引用
  wordItemRefs.value = {}
  // 重置弹窗状态
  showCompleteModal.value = false
  showEnergyModal.value = false
  showWordDetail.value = false
})
</script>

<style scoped>
/* 游戏屏幕整体布局 - 使用flex分配空间，键盘固定底部，满屏显示 */
.game-screen {
  height: 100vh;
  height: 100dvh;
  width: 100%;
  max-width: 100vw;
  display: flex;
  flex-direction: column;
  padding: clamp(4px, 1vw, 10px);
  padding-bottom: 0;
  box-sizing: border-box;
  position: relative;
  z-index: 1;
  overflow: hidden;
  margin: 0 auto;
}

/* 顶部栏 - 全屏宽 */
.top-bar {
  flex-shrink: 0;
  width: 100%;
  max-width: 100%;
  margin: 0 auto clamp(4px, 1vw, 10px);
  padding: 0 clamp(2px, 0.5vw, 6px);
  box-sizing: border-box;
}

/* 主内容区域 - 占用剩余空间，全屏宽 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: flex-start;
  gap: clamp(6px, 1vw, 12px);
  overflow: hidden;
  min-height: 0; /* 关键：让flex子元素可以缩小 */
  width: 100%;
  padding: 0 clamp(2px, 0.5vw, 6px);
  box-sizing: border-box;
}

/* 键盘区固定在底部 - 透明风格，全屏宽 */
.keyboard-section {
  flex-shrink: 0;
  width: 100%;
  max-width: 100%;
  background: rgba(255, 255, 255, 0.70);
  backdrop-filter: blur(15px);
  padding: clamp(6px, 1vw, 12px) clamp(4px, 0.8vw, 10px);
  padding-bottom: max(clamp(6px, 1vw, 12px), env(safe-area-inset-bottom));
  border-top: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.06);
  box-sizing: border-box;
}

/* 键盘整体包装 - 全屏宽 */
.keyboard-wrapper {
  display: flex;
  align-items: stretch;
  justify-content: center;
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
  padding: 0;
}

/* 道具按钮 - 横向1.5格宽度，更大尺寸 */
.keyboard-prop-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: clamp(4px, 0.8vw, 8px);
  flex: 1.5;
  height: clamp(44px, 7vh, 60px);
  min-height: 42px;
  padding: 0 clamp(6px, 1.2vw, 12px);
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  border: clamp(2px, 0.4vw, 3px) solid #fbbf24;
  border-radius: clamp(8px, 1.5vw, 12px);
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 clamp(3px, 0.5vw, 5px) 0 #d97706;
}

.keyboard-prop-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 0 #d97706;
}

.keyboard-prop-btn:active:not(:disabled) {
  transform: translateY(2px);
  box-shadow: 0 1px 0 #d97706;
}

.keyboard-prop-btn.active {
  background: linear-gradient(180deg, #a7f3d0, #6ee7b7);
  border-color: #10b981;
  box-shadow: 0 3px 0 #059669;
  animation: pulse-prop 1s ease-in-out infinite;
}

.keyboard-prop-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.keyboard-prop-btn .prop-emoji {
  font-size: clamp(1.2rem, 3vw, 1.6rem);
}

.keyboard-prop-btn .prop-num {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: clamp(22px, 4vw, 28px);
  height: clamp(22px, 4vw, 28px);
  background: linear-gradient(180deg, #f59e0b, #d97706);
  border-radius: 50%;
  font-size: clamp(0.75rem, 1.8vw, 0.95rem);
  font-weight: 800;
  color: white;
}

.keyboard-prop-btn.active .prop-num {
  background: linear-gradient(180deg, #10b981, #059669);
}


.animate-bounce-in {
  animation: bounceIn 0.5s ease-out;
}

@keyframes bounceIn {
  0% { transform: scale(0.5); opacity: 0; }
  70% { transform: scale(1.05); }
  100% { transform: scale(1); opacity: 1; }
}

.contents {
  display: contents;
}

/* 紧凑的顶部卡片 - 透明卡通风格，全屏宽 */
.game-card-compact {
  padding: clamp(6px, 1vw, 12px) clamp(10px, 2vw, 20px);
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(12px);
  border-radius: clamp(12px, 2vw, 20px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.6);
  width: 100%;
  box-sizing: border-box;
}

/* 顶部两行布局 */
.top-row-1 {
  display: flex;
  align-items: center;
  gap: clamp(6px, 1.2vw, 12px);
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  margin-bottom: 4px;
  justify-content: flex-start;
}

.top-row-2 {
  display: flex;
  align-items: center;
  gap: clamp(6px, 1vw, 12px);
  flex-wrap: nowrap;
  justify-content: flex-start;
}

/* 返回按钮图标 */
.back-btn-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #f3f4f6, #e5e7eb);
  border: 2px solid #d1d5db;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 700;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 2px 0 #9ca3af;
  flex-shrink: 0;
}

.back-btn-icon:hover {
  background: linear-gradient(180deg, #fee2e2, #fecaca);
  border-color: #f87171;
  color: #dc2626;
}

.back-btn-icon:active {
  transform: translateY(2px);
  box-shadow: 0 0 0 #9ca3af;
}

/* 用户信息迷你版 */
.user-info-mini {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.mini-avatar {
  font-size: clamp(1.3rem, 3vw, 1.8rem);
}

.mini-name {
  font-size: var(--font-md, clamp(0.9rem, 2.2vw, 1.2rem));
  font-weight: 700;
  color: #374151;
  max-width: clamp(60px, 15vw, 120px);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 迷你状态栏 - 右对齐 */
.mini-stats {
  display: flex;
  gap: clamp(6px, 1vw, 12px);
  flex-shrink: 0;
  margin-left: auto;
}

.mini-stat {
  font-size: var(--font-sm, clamp(0.85rem, 1.8vw, 1.05rem));
  font-weight: 700;
  color: #4b5563;
  background: linear-gradient(180deg, #f9fafb, #f3f4f6);
  padding: clamp(4px, 0.8vw, 8px) clamp(8px, 1.2vw, 14px);
  border-radius: clamp(6px, 1vw, 10px);
  border: 1px solid #e5e7eb;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: clamp(4px, 0.6vw, 6px);
}

/* 游戏模式标签 */
.game-mode-badge {
  display: flex;
  align-items: center;
  gap: clamp(3px, 0.5vw, 6px);
  font-size: var(--font-sm, clamp(0.8rem, 1.6vw, 0.95rem));
  font-weight: 800;
  color: #5b21b6;
  background: linear-gradient(180deg, #ede9fe, #ddd6fe);
  padding: clamp(4px, 0.6vw, 7px) clamp(8px, 1.2vw, 12px);
  border-radius: clamp(6px, 1vw, 10px);
  border: 1px solid #c4b5fd;
  white-space: nowrap;
  flex-shrink: 0;
}

.level-badge {
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  color: #92400e;
  padding: 1px 4px;
  border-radius: 4px;
  font-size: clamp(0.6rem, 1.2vw, 0.75rem);
  border: 1px solid #fbbf24;
  margin-left: 2px;
}

/* 计时器迷你版 */
.timer-mini {
  font-size: var(--font-sm, clamp(0.85rem, 1.8vw, 1rem));
  font-weight: 800;
  font-family: 'Nunito', monospace;
  color: #374151;
  background: linear-gradient(180deg, #f9fafb, #f3f4f6);
  padding: clamp(4px, 0.6vw, 7px) clamp(8px, 1.2vw, 12px);
  border-radius: clamp(6px, 1vw, 10px);
  border: 1px solid #e5e7eb;
  white-space: nowrap;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: clamp(3px, 0.5vw, 5px);
}

.timer-mini.warning {
  color: #dc2626;
  background: linear-gradient(180deg, #fee2e2, #fecaca);
  border-color: #f87171;
  animation: pulse 0.5s ease-in-out infinite;
}

/* 分数迷你版 */
.score-mini {
  font-size: var(--font-sm, clamp(0.85rem, 1.8vw, 1rem));
  font-weight: 800;
  color: #d97706;
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  padding: clamp(4px, 0.6vw, 7px) clamp(8px, 1.2vw, 12px);
  border-radius: clamp(6px, 1vw, 10px);
  border: 1px solid #fbbf24;
  white-space: nowrap;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: clamp(3px, 0.5vw, 5px);
}

/* 进度迷你版 - 占满右侧剩余空间但不超过中心 */
.progress-mini {
  display: flex;
  align-items: center;
  gap: clamp(6px, 1vw, 10px);
  margin-left: auto;
  flex: 1;
  min-width: 0;
  /* 最大宽度为父容器的50%，确保不超过屏幕中心 */
  max-width: 50%;
}

.progress-bar-mini {
  flex: 1;
  height: clamp(8px, 1.5vw, 12px);
  background: #e5e7eb;
  border-radius: clamp(4px, 0.8vw, 6px);
  overflow: hidden;
  min-width: 60px;
}

.progress-fill-mini {
  height: 100%;
  background: linear-gradient(90deg, #34d399, #10b981);
  border-radius: clamp(4px, 0.8vw, 6px);
  transition: width 0.5s ease;
}

.progress-text-mini {
  font-size: var(--font-md, clamp(0.9rem, 2vw, 1.15rem));
  font-weight: 800;
  color: #374151;
  white-space: nowrap;
  flex-shrink: 0;
  background: linear-gradient(180deg, #d1fae5, #a7f3d0);
  padding: clamp(3px, 0.5vw, 6px) clamp(8px, 1.2vw, 12px);
  border-radius: clamp(6px, 1vw, 10px);
  border: 1px solid #34d399;
}

/* 累计分数（计时/PK/无限模式） */
.session-score-mini {
  font-size: clamp(0.65rem, 1.3vw, 0.8rem);
  font-weight: 800;
  color: #059669;
  background: linear-gradient(180deg, #d1fae5, #a7f3d0);
  padding: 2px clamp(4px, 0.8vw, 8px);
  border-radius: clamp(4px, 0.8vw, 8px);
  border: 1px solid #34d399;
  white-space: nowrap;
  flex-shrink: 0;
  animation: pulse-score 1s ease-in-out infinite;
}

@keyframes pulse-score {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* 老的back-btn样式保留兼容 */
.back-btn {
  display: flex;
  align-items: center;
  gap: 2px;
  color: #4b5563;
  font-size: 0.85rem;
  white-space: nowrap;
  flex-shrink: 0;
  padding: 4px 8px;
  border-radius: 8px;
  transition: all 0.15s ease;
}

.back-btn:hover {
  color: #1f2937;
  background: rgba(0, 0, 0, 0.05);
}

/* 模式标题 - 防止换行 */
.mode-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: #7c3aed;
  white-space: nowrap;
  flex-shrink: 0;
}

.mode-title .level-num {
  color: #6b7280;
  margin-left: 4px;
}

/* 主游戏卡片 - 透明卡通风格，全屏宽 */
.game-card-main {
  padding: clamp(10px, 2vw, 18px);
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(15px);
  border-radius: clamp(14px, 2.5vw, 24px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  width: 100%;
  max-width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-sizing: border-box;
}

/* 网格包装容器 - 居中显示 */
.grid-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

/* 单词列表区 - 动态高度，全屏宽 */
.words-section {
  width: 100%;
  max-width: 100%;
  flex: 1;
  min-height: 0; /* 关键：让flex子元素可以缩小 */
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(12px);
  border-radius: clamp(12px, 2vw, 18px);
  padding: clamp(8px, 1.2vw, 14px) clamp(10px, 1.8vw, 18px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.5);
  overflow: hidden;
  margin-bottom: clamp(4px, 0.8vw, 8px);
  box-sizing: border-box;
}

.words-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  /* 自定义滚动条 */
  scrollbar-width: thin;
  scrollbar-color: #c4b5fd #f3f4f6;
}

.words-list::-webkit-scrollbar {
  width: 6px;
}

.words-list::-webkit-scrollbar-track {
  background: #f3f4f6;
  border-radius: 3px;
}

.words-list::-webkit-scrollbar-thumb {
  background: #c4b5fd;
  border-radius: 3px;
}

.words-list::-webkit-scrollbar-thumb:hover {
  background: #a78bfa;
}

.word-item {
  display: flex;
  align-items: center;
  gap: clamp(8px, 1.5vw, 14px);
  padding: clamp(10px, 1.8vw, 16px) clamp(12px, 2vw, 18px);
  background: rgba(248, 250, 252, 0.7);
  border-radius: clamp(12px, 2vw, 16px);
  font-size: var(--word-font, 0.95rem);
  cursor: pointer;
  transition: all 0.15s ease;
  border: 1px solid rgba(203, 213, 225, 0.6);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
}

.word-item:hover:not(.completed) {
  background: rgba(237, 233, 254, 0.75);
  border-color: rgba(167, 139, 250, 0.7);
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(139, 92, 246, 0.15);
}

.word-item.selected {
  background: rgba(219, 234, 254, 0.8);
  border-color: rgba(96, 165, 250, 0.7);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
}

.word-item.completed {
  background: rgba(209, 250, 229, 0.75);
  border-color: rgba(52, 211, 153, 0.6);
  box-shadow: 0 2px 6px rgba(16, 185, 129, 0.1);
  cursor: default;
}

.word-index {
  display: flex;
  align-items: center;
  justify-content: center;
  width: clamp(30px, 6vw, 42px);
  height: clamp(30px, 6vw, 42px);
  background: linear-gradient(180deg, #e0e7ff, #c7d2fe);
  border-radius: 50%;
  font-size: var(--font-md, clamp(0.9rem, 2vw, 1.2rem));
  font-weight: 800;
  color: #4338ca;
  flex-shrink: 0;
  border: 2px solid #a5b4fc;
}

.word-direction-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: clamp(22px, 4vw, 30px);
  height: clamp(22px, 4vw, 30px);
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  border-radius: clamp(4px, 0.8vw, 6px);
  font-size: var(--font-xs, clamp(0.65rem, 1.5vw, 0.9rem));
  font-weight: 800;
  color: #92400e;
  flex-shrink: 0;
  border: 1px solid #fbbf24;
}

.word-item.completed .word-index {
  background: linear-gradient(180deg, #a7f3d0, #6ee7b7);
  border-color: #34d399;
  color: #065f46;
}

.word-text {
  font-weight: 800;
  color: #065f46;
  text-transform: uppercase;
  min-width: clamp(70px, 15vw, 130px);
  font-family: 'Nunito', sans-serif;
  font-size: var(--font-lg, clamp(1rem, 2.5vw, 1.35rem));
}

.alt-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  border: 1px solid #fbbf24;
  border-radius: 8px;
  font-size: 0.6rem;
  font-weight: 700;
  color: #92400e;
  margin-left: 4px;
}

.word-definition {
  flex: 1;
  color: #047857;
  font-size: var(--font-md, clamp(0.9rem, 2.2vw, 1.2rem));
  font-weight: 600;
}

.word-placeholder {
  display: flex;
  gap: 3px;
  min-width: 60px;
}

.placeholder-char {
  color: #94a3b8;
  font-weight: 800;
  font-size: var(--font-md, clamp(1rem, 2.2vw, 1.25rem));
  min-width: clamp(14px, 3vw, 20px);
  text-align: center;
}

.placeholder-char.hint-letter {
  color: #7c3aed;
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  border-radius: 4px;
  padding: 1px 3px;
  font-size: 0.85rem;
}

.word-hint {
  flex: 1;
  color: #6b7280;
  font-size: 0.75rem;
  font-weight: 600;
}

/* 道具激活时显示的翻译（红字） */
.word-translation-hint {
  flex: 1;
  color: #dc2626;
  font-size: var(--font-md, clamp(0.9rem, 2vw, 1.15rem));
  font-weight: 700;
}

/* 道具区域样式 */
.props-section {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 12px;
  padding: 10px;
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  border-radius: 14px;
  border: 2px solid #fbbf24;
}

.prop-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: linear-gradient(180deg, #ffffff, #f1f5f9);
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 3px 0 #cbd5e1;
}

.prop-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 0 #cbd5e1;
}

.prop-btn:active:not(:disabled) {
  transform: translateY(2px);
  box-shadow: 0 1px 0 #cbd5e1;
}

.prop-btn.active {
  background: linear-gradient(180deg, #a7f3d0, #6ee7b7);
  border-color: #10b981;
  box-shadow: 0 3px 0 #059669;
  animation: pulse-prop 1s ease-in-out infinite;
}

@keyframes pulse-prop {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.prop-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.prop-icon {
  font-size: 1.1rem;
}

.prop-name {
  font-size: 0.8rem;
  font-weight: 700;
  color: #374151;
}

.prop-count {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: linear-gradient(180deg, #fbbf24, #f59e0b);
  border-radius: 50%;
  font-size: 0.7rem;
  font-weight: 800;
  color: white;
}

.speak-btn {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  border: 2px solid #fbbf24;
  border-radius: 50%;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.15s ease;
  box-shadow: 0 2px 0 #d97706;
}

/* 未完成单词列表中的小发音按钮 */
.speak-btn-small {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #dbeafe, #93c5fd);
  border: 2px solid #3b82f6;
  border-radius: 50%;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.15s ease;
  box-shadow: 0 2px 0 #2563eb;
  flex-shrink: 0;
  animation: pulse-speak 1.5s ease-in-out infinite;
}

.speak-btn-small:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 0 #2563eb;
}

.speak-btn-small:active {
  transform: translateY(1px);
  box-shadow: 0 1px 0 #2563eb;
}

@keyframes pulse-speak {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.speak-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 0 #d97706;
}

.speak-btn:active {
  transform: translateY(1px);
  box-shadow: 0 1px 0 #d97706;
}

.detail-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #e0f2fe, #bae6fd);
  border: 2px solid #38bdf8;
  border-radius: 50%;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.15s ease;
  box-shadow: 0 2px 0 #0284c7;
}

.detail-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 0 #0284c7;
}

/* 单词详情卡片样式 */
.word-detail-card {
  background: white;
  border-radius: 24px;
  padding: 24px;
  max-width: 340px;
  width: 90%;
  position: relative;
  box-shadow: 0 10px 0 rgba(0, 0, 0, 0.1), 0 20px 50px rgba(0, 0, 0, 0.2);
  border: 3px solid #e2e8f0;
}

.detail-close-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #f3f4f6, #e5e7eb);
  border: 2px solid #d1d5db;
  border-radius: 50%;
  font-size: 1.2rem;
  font-weight: bold;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 2px 0 #9ca3af;
}

.detail-close-btn:hover {
  background: linear-gradient(180deg, #fee2e2, #fecaca);
  border-color: #f87171;
  color: #dc2626;
}

.detail-word {
  font-size: 2rem;
  font-weight: 900;
  color: #5b21b6;
  text-align: center;
  margin-bottom: 4px;
  font-family: 'Nunito', sans-serif;
  letter-spacing: 2px;
}

.detail-phonetic {
  font-size: 1rem;
  color: #6b7280;
  text-align: center;
  margin-bottom: 16px;
  font-style: italic;
}

.detail-speak-btns {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 20px;
}

.detail-speak-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border: none;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.detail-speak-btn.us {
  background: linear-gradient(180deg, #dbeafe, #bfdbfe);
  color: #1e40af;
  box-shadow: 0 3px 0 #3b82f6;
  border: 2px solid #60a5fa;
}

.detail-speak-btn.uk {
  background: linear-gradient(180deg, #fce7f3, #fbcfe8);
  color: #9d174d;
  box-shadow: 0 3px 0 #ec4899;
  border: 2px solid #f472b6;
}

.detail-speak-btn:hover {
  transform: translateY(-2px);
}

.detail-speak-btn:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0;
}

.detail-section {
  margin-bottom: 16px;
}

.detail-label {
  font-size: 0.85rem;
  font-weight: 700;
  color: #7c3aed;
  margin-bottom: 6px;
}

.detail-content {
  font-size: 1rem;
  color: #374151;
  line-height: 1.5;
  padding: 10px 14px;
  background: linear-gradient(180deg, #f9fafb, #f3f4f6);
  border-radius: 10px;
  border: 2px solid #e5e7eb;
}

.detail-content.example {
  font-style: italic;
  color: #4b5563;
}

.detail-meta {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 16px;
}

.meta-badge {
  padding: 6px 12px;
  background: linear-gradient(180deg, #ede9fe, #ddd6fe);
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  color: #5b21b6;
  border: 2px solid #c4b5fd;
}

/* 通关弹窗样式 */
.complete-modal {
  background: white;
  border-radius: clamp(24px, 4vw, 32px);
  padding: clamp(24px, 4vw, 36px) clamp(20px, 3.5vw, 32px);
  max-width: min(90%, 420px);
  width: 90%;
  text-align: center;
  position: relative;
  box-shadow: 0 12px 0 rgba(0, 0, 0, 0.1), 0 25px 60px rgba(0, 0, 0, 0.25);
  border: 4px solid #fbbf24;
  overflow: hidden;
}

.confetti-container {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  pointer-events: none;
}

.confetti {
  position: absolute;
  font-size: 1.5rem;
  animation: confetti-fall 2s ease-out forwards;
  animation-delay: var(--delay);
  opacity: 0;
}

@keyframes confetti-fall {
  0% { 
    transform: translateY(-20px) translateX(0) rotate(0deg); 
    opacity: 1;
  }
  100% { 
    transform: translateY(100px) translateX(var(--x)) rotate(360deg); 
    opacity: 0;
  }
}

.trophy-area {
  margin-bottom: 16px;
}

.trophy-emoji {
  font-size: 4rem;
  animation: trophy-bounce 0.6s ease-out;
}

@keyframes trophy-bounce {
  0% { transform: scale(0) rotate(-20deg); }
  60% { transform: scale(1.2) rotate(10deg); }
  100% { transform: scale(1) rotate(0deg); }
}

.stars-row {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
}

.star {
  font-size: 1.5rem;
  animation: star-pop 0.4s ease-out backwards;
}

.star:nth-child(1) { animation-delay: 0.3s; }
.star:nth-child(2) { animation-delay: 0.5s; }
.star:nth-child(3) { animation-delay: 0.7s; }

.star.big {
  font-size: 2rem;
}

@keyframes star-pop {
  0% { transform: scale(0); opacity: 0; }
  60% { transform: scale(1.3); }
  100% { transform: scale(1); opacity: 1; }
}

.complete-title {
  font-size: var(--font-2xl, clamp(1.5rem, 4vw, 2rem));
  font-weight: 900;
  color: #5b21b6;
  margin-bottom: clamp(12px, 2vw, 18px);
}

/* 一行紧凑的统计数据 */
.stats-inline {
  font-size: var(--font-md, clamp(1rem, 2.5vw, 1.25rem));
  color: #6b7280;
  margin-bottom: clamp(14px, 2.5vw, 20px);
  padding: clamp(8px, 1.5vw, 12px) clamp(14px, 2.5vw, 20px);
  background: #f3f4f6;
  border-radius: clamp(16px, 2.5vw, 24px);
  display: inline-block;
}

.all-complete-msg {
  color: #059669;
  font-weight: 700;
  margin-bottom: 16px;
  padding: 10px;
  background: linear-gradient(180deg, #d1fae5, #a7f3d0);
  border-radius: 10px;
  border: 2px solid #34d399;
}

.modal-btns {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.modal-btns.three-btns {
  gap: 8px;
}

.modal-btns.two-btns {
  gap: 12px;
}

.modal-btn {
  padding: clamp(14px, 2.5vw, 20px) clamp(24px, 4vw, 36px);
  border-radius: clamp(14px, 2vw, 18px);
  font-size: var(--font-lg, clamp(1.1rem, 2.5vw, 1.35rem));
  font-weight: 800;
  cursor: pointer;
  transition: all 0.15s ease;
  border: none;
}

.modal-btn.small {
  padding: clamp(12px, 2vw, 18px) clamp(16px, 3vw, 26px);
  font-size: var(--font-md, clamp(1rem, 2.2vw, 1.2rem));
  border-radius: clamp(12px, 1.8vw, 16px);
}

.modal-btn.claimed {
  opacity: 0.6;
  cursor: not-allowed;
}

.modal-btn.secondary {
  background: linear-gradient(180deg, #f3f4f6, #e5e7eb);
  color: #6b7280;
  box-shadow: 0 4px 0 #d1d5db;
  border: 2px solid #d1d5db;
}

.modal-btn.primary {
  background: linear-gradient(180deg, #a78bfa, #8b5cf6);
  color: white;
  box-shadow: 0 4px 0 #6d28d9;
  border: 2px solid #7c3aed;
}

.modal-btn.success {
  background: linear-gradient(180deg, #34d399, #10b981);
  color: white;
  box-shadow: 0 4px 0 #059669;
  border: 2px solid #10b981;
}

.modal-btn:hover {
  transform: translateY(-2px);
}

.modal-btn:active {
  transform: translateY(3px);
  box-shadow: 0 1px 0;
}

.modal-btn.reward {
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  color: #92400e;
  box-shadow: 0 4px 0 #d97706;
  border: 2px solid #fbbf24;
}

/* 星星未获得样式 */
.star:not(.earned) {
  opacity: 0.3;
  filter: grayscale(100%);
}

.stars-hint {
  font-size: 0.75rem;
  color: #f59e0b;
  font-weight: 700;
  margin-top: 4px;
}

/* 计时模式结果显示 */
.timed-result {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
  margin-top: 8px;
}

.timed-words-count {
  font-size: 2.5rem;
  font-weight: 900;
  color: #5b21b6;
  font-family: 'Nunito', sans-serif;
}

.timed-words-label {
  font-size: 1rem;
  font-weight: 700;
  color: #6b7280;
}

/* 奖励展示区 */
.reward-display {
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  border: 2px solid #fbbf24;
  border-radius: clamp(14px, 2.5vw, 20px);
  padding: clamp(14px, 2.5vw, 20px) clamp(18px, 3vw, 26px);
  margin-bottom: clamp(16px, 2.5vw, 22px);
  animation: rewardPop 0.4s ease-out;
}

@keyframes rewardPop {
  0% { transform: scale(0.8); opacity: 0; }
  60% { transform: scale(1.05); }
  100% { transform: scale(1); opacity: 1; }
}

.reward-title {
  font-size: var(--font-md, clamp(1rem, 2.2vw, 1.25rem));
  font-weight: 800;
  color: #92400e;
  text-align: center;
  margin-bottom: clamp(10px, 1.8vw, 16px);
}

.reward-items {
  display: flex;
  justify-content: center;
  gap: clamp(14px, 2.5vw, 22px);
}

.reward-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: clamp(4px, 0.8vw, 8px);
  padding: clamp(10px, 1.8vw, 16px) clamp(16px, 3vw, 24px);
  background: white;
  border-radius: clamp(12px, 2vw, 16px);
  border: 2px solid #f59e0b;
  box-shadow: 0 3px 0 #d97706;
}

.reward-icon {
  font-size: clamp(1.8rem, 4vw, 2.4rem);
}

.reward-value {
  font-size: var(--font-lg, clamp(1.2rem, 3vw, 1.5rem));
  font-weight: 900;
  color: #059669;
}

.reward-name {
  font-size: var(--font-sm, clamp(0.85rem, 1.8vw, 1.05rem));
  color: #92400e;
  font-weight: 600;
}

/* 紧凑计时器 - 卡通风格 */
.timer-compact {
  font-size: 1rem;
  font-weight: 900;
  font-family: 'Nunito', sans-serif;
  color: #5b21b6;
  padding: 4px 12px;
  background: linear-gradient(180deg, #ede9fe, #ddd6fe);
  border-radius: 10px;
  border: 2px solid #a78bfa;
  box-shadow: 0 2px 0 #8b5cf6;
}

.timer-compact.warning {
  color: #b91c1c;
  background: linear-gradient(180deg, #fee2e2, #fecaca);
  border-color: #f87171;
  box-shadow: 0 2px 0 #dc2626;
  animation: pulse 0.5s ease-in-out infinite;
}

/* 网格容器 - 居中且紧凑 */
.grid-container {
  display: grid;
  gap: var(--cell-gap, clamp(3px, 0.6vw, 6px));
  width: fit-content;
  max-width: 100%;
  margin: 0 auto;
  justify-content: center;
}

/* 根据网格尺寸调整格子大小 */
.grid-container[data-grid-size="5"] .letter-cell-new { width: clamp(42px, 12vw, 64px); height: clamp(42px, 12vw, 64px); }
.grid-container[data-grid-size="6"] .letter-cell-new { width: clamp(38px, 10vw, 58px); height: clamp(38px, 10vw, 58px); }
.grid-container[data-grid-size="7"] .letter-cell-new { width: clamp(34px, 9vw, 52px); height: clamp(34px, 9vw, 52px); }
.grid-container[data-grid-size="8"] .letter-cell-new { width: clamp(32px, 8vw, 48px); height: clamp(32px, 8vw, 48px); }
.grid-container[data-grid-size="9"] .letter-cell-new { width: clamp(30px, 7.5vw, 44px); height: clamp(30px, 7.5vw, 44px); }
.grid-container[data-grid-size="10"] .letter-cell-new { width: clamp(28px, 7vw, 40px); height: clamp(28px, 7vw, 40px); }

/* 格子样式 - 卡通风格 + 固定尺寸确保紧凑 */
.letter-cell-new {
  /* 固定宽高，由父容器的 data-grid-size 决定具体尺寸 */
  width: clamp(34px, 9vw, 50px);
  height: clamp(34px, 9vw, 50px);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #ffffff, #f1f5f9);
  border: clamp(2px, 0.4vw, 3px) solid #c7d2fe;
  border-radius: clamp(8px, 1.5vw, 14px);
  box-shadow: 0 clamp(2px, 0.5vw, 4px) 0 #a5b4fc, inset 0 2px 0 rgba(255,255,255,0.8);
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
  position: relative;
  flex-shrink: 0;
}

.letter-cell-new .cell-letter {
  font-size: var(--font-grid, 1.25rem);
  font-weight: 900;
  color: #4c1d95;
  text-transform: uppercase;
  font-family: 'Nunito', sans-serif;
  text-shadow: 0 1px 0 rgba(255,255,255,0.8);
}

/* 线索编号（左上角小数字） */
.clue-number {
  position: absolute;
  top: 1px;
  left: 3px;
  font-size: 0.55rem;
  font-weight: 700;
  color: #6b7280;
  z-index: 1;
}

.letter-cell-new.empty {
  background: rgba(241, 245, 249, 0.2);
  border-color: transparent;
  box-shadow: none;
  cursor: default;
}

.letter-cell-new.active {
  border-color: #8b5cf6;
  background: linear-gradient(180deg, #ede9fe, #ddd6fe);
  box-shadow: 0 4px 0 #7c3aed, 0 0 0 3px rgba(139, 92, 246, 0.3);
  transform: translateY(-2px);
}

.letter-cell-new.in-word {
  border-color: #a5b4fc;
  background: linear-gradient(180deg, #f5f3ff, #ede9fe);
}

/* 预填字母 - 特殊样式 */
.letter-cell-new.prefilled {
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  border-color: #f59e0b;
  box-shadow: 0 4px 0 #d97706, inset 0 2px 0 rgba(255,255,255,0.6);
  cursor: default;
}

.letter-cell-new.prefilled .cell-letter {
  color: #92400e;
  text-shadow: 0 1px 0 rgba(255,255,255,0.5);
}

/* 已完成锁定 - 绿色 */
.letter-cell-new.locked {
  background: linear-gradient(180deg, #6ee7b7, #34d399);
  border-color: #10b981;
  box-shadow: 0 4px 0 #059669, inset 0 2px 0 rgba(255,255,255,0.4);
  cursor: default;
}

.letter-cell-new.locked .cell-letter {
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* 键盘容器 - 全屏三行 */
.keyboard-container {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: clamp(4px, 0.8vw, 8px);
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
}

.keyboard-row {
  display: flex;
  justify-content: stretch;
  gap: clamp(3px, 0.6vw, 6px);
  flex-wrap: nowrap;
  width: 100%;
}

/* 键盘按键样式 - 全屏对齐，更大尺寸 */
.keyboard-key-new {
  flex: 1;
  height: clamp(44px, 7vh, 60px);
  min-height: 42px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-key, 1rem);
  font-weight: 800;
  background: linear-gradient(180deg, #ffffff, #e2e8f0);
  border: clamp(2px, 0.4vw, 3px) solid #cbd5e1;
  border-radius: clamp(8px, 1.5vw, 12px);
  box-shadow: 0 clamp(3px, 0.5vw, 5px) 0 #94a3b8;
  color: #374151;
  cursor: pointer;
  transition: all 0.1s ease;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
  font-family: 'Nunito', sans-serif;
}

.keyboard-key-new:hover {
  transform: translateY(-2px);
  background: linear-gradient(180deg, #ffffff, #ddd6fe);
  border-color: #a78bfa;
  box-shadow: 0 6px 0 #7c3aed;
  color: #5b21b6;
}

.keyboard-key-new:active {
  transform: translateY(3px);
  box-shadow: 0 1px 0 #94a3b8;
}

.keyboard-key-new.key-highlight {
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  border-color: #fbbf24;
  color: #92400e;
  box-shadow: 0 4px 0 #d97706;
}

.keyboard-key-new.delete-key {
  flex: 1;
  background: linear-gradient(180deg, #fecaca, #f87171);
  border-color: #ef4444;
  color: white;
  box-shadow: 0 3px 0 #b91c1c;
  font-size: 1.3rem;
}

.keyboard-key-new.delete-key:hover {
  background: linear-gradient(180deg, #fef2f2, #fecaca);
  color: #b91c1c;
  box-shadow: 0 5px 0 #dc2626;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

/* 体力不足弹窗样式 */
.energy-modal {
  background: white;
  border-radius: clamp(24px, 4vw, 32px);
  padding: clamp(24px, 4vw, 36px) clamp(20px, 3.5vw, 32px);
  max-width: min(85%, 400px);
  width: 85%;
  text-align: center;
  box-shadow: 0 12px 0 rgba(0, 0, 0, 0.1), 0 25px 60px rgba(0, 0, 0, 0.25);
  border: 4px solid #fbbf24;
}

.energy-modal-icon {
  font-size: clamp(3.5rem, 8vw, 5rem);
  margin-bottom: clamp(12px, 2vw, 18px);
  animation: sleepy 2s ease-in-out infinite;
}

@keyframes sleepy {
  0%, 100% { transform: rotate(-5deg); }
  50% { transform: rotate(5deg); }
}

.energy-modal-title {
  font-size: var(--font-2xl, clamp(1.5rem, 4vw, 2rem));
  font-weight: 900;
  color: #dc2626;
  margin-bottom: clamp(10px, 1.8vw, 16px);
}

.energy-modal-text {
  font-size: var(--font-md, clamp(1rem, 2.5vw, 1.3rem));
  color: #4b5563;
  margin-bottom: clamp(14px, 2.5vw, 22px);
}

.energy-modal-info {
  display: flex;
  justify-content: center;
  gap: clamp(12px, 2vw, 20px);
  margin-bottom: clamp(12px, 2vw, 18px);
}

.energy-current, .energy-need {
  padding: clamp(8px, 1.5vw, 12px) clamp(14px, 2.5vw, 20px);
  border-radius: clamp(12px, 2vw, 16px);
  font-size: var(--font-md, clamp(1rem, 2.2vw, 1.2rem));
  font-weight: 700;
}

.energy-current {
  background: linear-gradient(180deg, #fee2e2, #fecaca);
  color: #dc2626;
  border: 2px solid #f87171;
}

.energy-need {
  background: linear-gradient(180deg, #dbeafe, #bfdbfe);
  color: #1e40af;
  border: 2px solid #60a5fa;
}

.energy-modal-buttons {
  display: flex;
  flex-direction: column;
  gap: clamp(12px, 2vw, 18px);
  margin-top: clamp(18px, 3vw, 26px);
}

.energy-modal-btn {
  width: 100%;
  padding: clamp(14px, 2.5vw, 20px) clamp(24px, 4vw, 36px);
  color: white;
  border: none;
  border-radius: clamp(14px, 2.5vw, 20px);
  font-size: var(--font-lg, clamp(1.1rem, 2.5vw, 1.35rem));
  font-weight: 800;
  cursor: pointer;
  transition: all 0.15s ease;
}

.energy-claim-btn {
  background: linear-gradient(180deg, #34d399, #10b981);
  box-shadow: 0 4px 0 #059669;
}

.energy-claim-btn:hover {
  transform: translateY(-2px);
}

.energy-claim-btn:active {
  transform: translateY(3px);
  box-shadow: 0 1px 0 #059669;
}

.energy-rest-btn {
  background: linear-gradient(180deg, #9ca3af, #6b7280);
  box-shadow: 0 4px 0 #4b5563;
}

.energy-rest-btn:hover {
  transform: translateY(-2px);
}

.energy-rest-btn:active {
  transform: translateY(3px);
  box-shadow: 0 1px 0 #4b5563;
}

/* 小屏幕手机优化 (iPhone SE, 小屏Android) */
@media (max-width: 375px) {
  .game-screen {
    padding: 3px;
    padding-bottom: 0;
  }
  
  .letter-cell-new {
    width: clamp(28px, 9vw, 34px);
    height: clamp(28px, 9vw, 34px);
    border-radius: 8px;
    border-width: 2px;
  }
  
  .letter-cell-new .cell-letter {
    font-size: clamp(0.9rem, 4vw, 1.1rem);
  }
  
  .keyboard-key-new {
    height: clamp(38px, 7vh, 44px);
    font-size: clamp(0.85rem, 3vw, 1rem);
  }
  
  .keyboard-prop-btn {
    height: clamp(38px, 7vh, 44px);
  }
}

/* 普通手机优化 */
@media (min-width: 376px) and (max-width: 480px) {
  .game-screen {
    padding: 4px;
    padding-bottom: 0;
  }
  
  .letter-cell-new {
    width: clamp(32px, 8.5vw, 40px);
    height: clamp(32px, 8.5vw, 40px);
    border-radius: 10px;
    border-width: 2px;
  }
  
  .letter-cell-new .cell-letter {
    font-size: clamp(1rem, 3.5vw, 1.2rem);
  }
  
  .keyboard-key-new {
    height: clamp(42px, 6.5vh, 48px);
    font-size: clamp(0.95rem, 2.8vw, 1.1rem);
    border-radius: 6px;
  }
  
  .keyboard-prop-btn {
    height: clamp(42px, 6.5vh, 48px);
    border-radius: 6px;
  }
  
  .word-item {
    padding: clamp(6px, 1.2vw, 10px) clamp(8px, 1.5vw, 12px);
    font-size: clamp(0.7rem, 2vw, 0.8rem);
  }
}

/* iPad Mini / 小平板 (竖屏) */
@media (min-width: 481px) and (max-width: 768px) {
  .letter-cell-new {
    width: clamp(40px, 7vw, 50px);
    height: clamp(40px, 7vw, 50px);
    border-radius: 12px;
    border-width: 3px;
  }
  
  .letter-cell-new .cell-letter {
    font-size: clamp(1.2rem, 3vw, 1.4rem);
  }
  
  .keyboard-key-new {
    height: clamp(48px, 6vh, 56px);
    font-size: clamp(1.05rem, 2.5vw, 1.2rem);
    border-radius: 9px;
  }
  
  .keyboard-prop-btn {
    height: clamp(48px, 6vh, 56px);
    border-radius: 9px;
  }
  
  .words-section {
    max-width: 450px;
  }
}

/* iPad / iPad Air (竖屏) - 使用全局CSS变量 */
@media (min-width: 769px) and (max-width: 1024px) {
  .keyboard-key-new {
    height: clamp(54px, 6vh, 66px);
    border-radius: 12px;
  }
  
  .keyboard-prop-btn {
    height: clamp(54px, 6vh, 66px);
    border-radius: 12px;
    gap: 10px;
  }
  
  .keyboard-prop-btn .prop-emoji {
    font-size: var(--font-xl);
  }
  
  .keyboard-prop-btn .prop-num {
    min-width: 28px;
    height: 28px;
    font-size: var(--font-sm);
  }
  
  .word-item {
    padding: clamp(12px, 2vw, 18px) clamp(14px, 2.5vw, 22px);
  }
  
  .word-index {
    width: clamp(30px, 5vw, 38px);
    height: clamp(30px, 5vw, 38px);
  }
  
  /* 格子在iPad上更大 */
  .grid-container[data-grid-size="5"] .letter-cell-new { width: clamp(52px, 10vw, 70px); height: clamp(52px, 10vw, 70px); }
  .grid-container[data-grid-size="6"] .letter-cell-new { width: clamp(48px, 9vw, 64px); height: clamp(48px, 9vw, 64px); }
  .grid-container[data-grid-size="7"] .letter-cell-new { width: clamp(44px, 8vw, 58px); height: clamp(44px, 8vw, 58px); }
  .grid-container[data-grid-size="8"] .letter-cell-new { width: clamp(40px, 7vw, 54px); height: clamp(40px, 7vw, 54px); }
  .grid-container[data-grid-size="9"] .letter-cell-new { width: clamp(38px, 6.5vw, 50px); height: clamp(38px, 6.5vw, 50px); }
  .grid-container[data-grid-size="10"] .letter-cell-new { width: clamp(36px, 6vw, 46px); height: clamp(36px, 6vw, 46px); }
}

/* iPad Pro / 大平板 / 桌面端 - 使用全局CSS变量 */
@media (min-width: 1025px) {
  .keyboard-key-new {
    height: clamp(58px, 6vh, 70px);
    border-radius: 14px;
  }
  
  .keyboard-prop-btn {
    height: clamp(58px, 6vh, 70px);
    border-radius: 14px;
    gap: 12px;
  }
  
  .keyboard-prop-btn .prop-emoji {
    font-size: var(--font-2xl);
  }
  
  .keyboard-prop-btn .prop-num {
    min-width: 30px;
    height: 30px;
    font-size: var(--font-md);
  }
  
  .word-item {
    padding: 16px 22px;
  }
  
  .word-index {
    width: 36px;
    height: 36px;
  }
  
  /* 格子在iPad Pro上更大 */
  .grid-container[data-grid-size="5"] .letter-cell-new { width: clamp(56px, 9vw, 76px); height: clamp(56px, 9vw, 76px); }
  .grid-container[data-grid-size="6"] .letter-cell-new { width: clamp(52px, 8vw, 70px); height: clamp(52px, 8vw, 70px); }
  .grid-container[data-grid-size="7"] .letter-cell-new { width: clamp(48px, 7vw, 64px); height: clamp(48px, 7vw, 64px); }
  .grid-container[data-grid-size="8"] .letter-cell-new { width: clamp(44px, 6.5vw, 58px); height: clamp(44px, 6.5vw, 58px); }
  .grid-container[data-grid-size="9"] .letter-cell-new { width: clamp(42px, 6vw, 54px); height: clamp(42px, 6vw, 54px); }
  .grid-container[data-grid-size="10"] .letter-cell-new { width: clamp(40px, 5.5vw, 50px); height: clamp(40px, 5.5vw, 50px); }
}

/* 横屏模式优化 - 防止内容过大 */
@media (orientation: landscape) and (max-height: 500px) {
  .game-screen {
    padding: 2px;
  }
  
  .letter-cell-new {
    width: clamp(28px, 6vh, 38px);
    height: clamp(28px, 6vh, 38px);
  }
  
  .keyboard-key-new {
    height: clamp(36px, 9vh, 46px);
  }
  
  .keyboard-prop-btn {
    height: clamp(36px, 9vh, 46px);
  }
  
  .words-section {
    max-height: 30vh;
  }
}

/* iPad 横屏 */
@media (orientation: landscape) and (min-width: 1024px) and (max-height: 834px) {
  .letter-cell-new {
    width: clamp(38px, 5vh, 50px);
    height: clamp(38px, 5vh, 50px);
  }
  
  .keyboard-key-new {
    height: clamp(46px, 6vh, 56px);
  }
  
  .keyboard-prop-btn {
    height: clamp(46px, 6vh, 56px);
  }
}
</style>
