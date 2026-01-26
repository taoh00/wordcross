import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { gameApi, staticApi, buildUrl } from '../api/index.js'

export const useGameStore = defineStore('game', () => {
  // 状态
  const currentGroup = ref('primary')
  const currentMode = ref('campaign')
  const currentLevel = ref(1)
  const puzzle = ref(null)
  const userAnswers = ref({})
  const prefilledCells = ref({}) // 预填字母的位置
  const completedWords = ref([])
  const score = ref(0)
  const timer = ref(0)
  const isPlaying = ref(false)
  const timerInterval = ref(null)
  
  // 缓存的关卡数据（按词库分组缓存）- key格式: {group}_{level}
  const cachedLevels = ref({})
  // 缓存的关卡汇总数据
  const cachedLevelsSummary = ref(null)
  
  // 词汇组别列表（含细分类）
  const groups = ref([
    { 
      code: 'primary', 
      name: '小学词汇', 
      icon: '📚',
      hasSubGroups: true,
      subGroups: [
        { code: 'primary_all', name: '全部', icon: '📚' },
        { code: 'grade3_1', name: '三年级上册', icon: '🌱' },
        { code: 'grade3_2', name: '三年级下册', icon: '🌿' },
        { code: 'grade4_1', name: '四年级上册', icon: '🌲' },
        { code: 'grade4_2', name: '四年级下册', icon: '🌳' },
        { code: 'grade5_1', name: '五年级上册', icon: '🌴' },
        { code: 'grade5_2', name: '五年级下册', icon: '🌵' },
        { code: 'grade6_1', name: '六年级上册', icon: '🎄' },
        { code: 'grade6_2', name: '六年级下册', icon: '🎋' },
      ]
    },
    { 
      code: 'junior', 
      name: '初中词汇', 
      icon: '📖',
      hasSubGroups: true,
      subGroups: [
        { code: 'junior_all', name: '全部', icon: '📖' },
        { code: 'junior7_1', name: '七年级上册', icon: '🌱' },
        { code: 'junior7_2', name: '七年级下册', icon: '🌿' },
        { code: 'junior8_1', name: '八年级上册', icon: '🌲' },
        { code: 'junior8_2', name: '八年级下册', icon: '🌳' },
        { code: 'junior9', name: '九年级全册', icon: '🌴' },
      ]
    },
    { 
      code: 'senior', 
      name: '高中词汇', 
      icon: '📕',
      hasSubGroups: true,
      subGroups: [
        { code: 'senior_all', name: '全部', icon: '📕' },
        { code: 'senior1', name: '必修1', icon: '📗' },
        { code: 'senior2', name: '必修2', icon: '📘' },
        { code: 'senior3', name: '必修3', icon: '📙' },
        { code: 'senior4', name: '必修4', icon: '📔' },
        { code: 'senior5', name: '必修5', icon: '📓' },
      ]
    },
    { code: 'ket', name: 'KET考试', icon: '🎯' },
    { code: 'pet', name: 'PET考试', icon: '🎓' },
    { code: 'cet4', name: '大学四级', icon: '🏛️' },
    { code: 'cet6', name: '大学六级', icon: '🎖️' },
    { code: 'postgrad', name: '考研词汇', icon: '🔬' },
    { code: 'ielts', name: '雅思', icon: '✈️' },
    { code: 'toefl', name: '托福', icon: '🗽' },
    { code: 'gre', name: 'GRE', icon: '🎩' },
  ])
  
  // 计算属性
  const gridSize = computed(() => puzzle.value?.grid_size || 5)
  const words = computed(() => puzzle.value?.words || [])
  const cells = computed(() => puzzle.value?.cells || [])
  const clueNumbers = computed(() => puzzle.value?.clue_numbers || [])
  
  const progress = computed(() => {
    if (!puzzle.value?.words?.length) return 0
    return Math.round((completedWords.value.length / puzzle.value.words.length) * 100)
  })
  
  const isLevelComplete = computed(() => {
    if (!puzzle.value?.words?.length) return false
    return completedWords.value.length === puzzle.value.words.length
  })
  
  const formattedTimer = computed(() => {
    const minutes = Math.floor(timer.value / 60)
    const seconds = timer.value % 60
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  })
  
  // 按需加载单关数据（直接从单独的JSON文件加载，非常快）
  // 新目录结构: /data/levels/{group}/{level}.json
  async function loadSingleLevel(group, levelNum) {
    const cacheKey = `${group}_${levelNum}`
    
    // 如果已缓存该关卡，直接返回
    if (cachedLevels.value[cacheKey]) {
      return cachedLevels.value[cacheKey]
    }
    
    try {
      console.log(`加载关卡: ${group}/${levelNum}`)
      const levelData = await staticApi.getLevelData(group, levelNum)
      
      if (levelData && levelData.words) {
        // 缓存该关卡
        cachedLevels.value[cacheKey] = levelData
        console.log(`关卡 ${group}/${levelNum} 加载完成`)
        return levelData
      } else {
        console.warn(`关卡 ${group}/${levelNum} 数据格式错误`)
        return null
      }
    } catch (error) {
      console.error(`加载关卡 ${group}/${levelNum} 失败:`, error)
      return null
    }
  }
  
  // 批量预加载（可选，用于预加载当前关卡附近的几关）
  async function preloadNearbyLevels(group, currentLevel, range = 2) {
    const promises = []
    for (let i = currentLevel; i <= currentLevel + range; i++) {
      const cacheKey = `${group}_${i}`
      if (!cachedLevels.value[cacheKey]) {
        promises.push(loadSingleLevel(group, i))
      }
    }
    if (promises.length > 0) {
      await Promise.all(promises)
    }
  }
  
  // 加载关卡汇总数据（从静态JSON文件）
  async function loadLevelsSummary() {
    if (cachedLevelsSummary.value) {
      return cachedLevelsSummary.value
    }
    
    try {
      const data = await staticApi.getLevelsSummary()
      if (data) {
        cachedLevelsSummary.value = data
        return data
      }
      return null
    } catch (error) {
      console.error('加载关卡汇总失败:', error)
      return null
    }
  }
  
  // 获取词库的关卡总数（从静态数据）
  async function getGroupLevelCount(group) {
    try {
      const summary = await loadLevelsSummary()
      if (summary && summary.groups) {
        const groupInfo = summary.groups.find(g => g.group_code === group)
        return groupInfo ? groupInfo.level_count : 0
      }
    } catch (error) {
      console.error('获取关卡数量失败:', error)
    }
    return 0
  }
  
  // 从缓存中获取指定关卡（改为返回缓存的单关数据）
  function getLevelFromCache(group, levelNum) {
    const cacheKey = `${group}_${levelNum}`
    return cachedLevels.value[cacheKey] || null
  }
  
  // 兼容旧接口：保留loadGroupLevels但不再加载全部数据
  async function loadGroupLevels(group) {
    // 只返回关卡数量信息，不再一次性加载所有关卡
    const count = await getGroupLevelCount(group)
    console.log(`词库 ${group} 共 ${count} 关（按需加载模式）`)
    return count
  }
  
  // 动作 - 加载关卡（按需加载单关，避免加载整个词库）
  async function loadPuzzle(mode, level = 1, group = 'primary', duration = 180, difficulty = 'medium') {
    currentMode.value = mode
    currentLevel.value = level
    currentGroup.value = group
    
    // 获取用户选择的难度
    const userDifficulty = difficulty || localStorage.getItem('game_difficulty') || 'medium'
    
    try {
      let data = null
      
      if (mode === 'campaign') {
        // 闯关模式：按需加载单关数据（不再一次性加载整个词库）
        const levelData = await loadSingleLevel(group, level)
        
        if (levelData && levelData.words) {
          // 后端API直接返回游戏需要的格式
          data = {
            grid_size: levelData.grid_size,
            cells: levelData.cells,
            words: levelData.words,
            prefilled: levelData.prefilled || {},
            level: levelData.level || level,
            difficulty: 'campaign',
            group: group
          }
          
          // 后台预加载下一关（不阻塞当前加载）
          preloadNearbyLevels(group, level + 1, 1)
        } else {
          throw new Error(`关卡 ${level} 数据不存在`)
        }
      } else {
        // 其他模式：使用API服务层
        switch (mode) {
          case 'endless':
            data = await gameApi.getEndlessPuzzle(group, userDifficulty)
            break
          case 'timed':
            data = await gameApi.getTimedPuzzle(group, 180, userDifficulty)
            break
          case 'pk':
            data = await gameApi.getEndlessPuzzle(group, userDifficulty)
            break
          default:
            data = await gameApi.getEndlessPuzzle(group, userDifficulty)
        }
      }
      
      // 验证数据格式
      if (data && data.words && data.words.length > 0) {
        puzzle.value = data
        console.log('关卡加载成功:', { 
          level: level, 
          mode: mode,
          words: data.words.map(w => w.word),
          grid_size: data.grid_size
        })
      } else {
        console.error('返回数据格式错误:', data)
        throw new Error('关卡数据格式错误')
      }
      
      // 重置状态
      userAnswers.value = {}
      prefilledCells.value = {}
      completedWords.value = []
      score.value = 0
      
      // 处理预填字母
      initPrefilledCells()
      
      return true
    } catch (error) {
      console.error('加载关卡失败:', error)
      alert('加载关卡失败，请检查网络连接后刷新页面重试')
      return false
    }
  }
  
  
  // 初始化预填字母（从后端返回的cells中获取）
  function initPrefilledCells() {
    if (!puzzle.value?.cells || !puzzle.value?.prefilled) return
    
    const prefilled = puzzle.value.prefilled
    for (const key of Object.keys(prefilled)) {
      const letter = prefilled[key]
      prefilledCells.value[key] = true
      userAnswers.value[key] = letter
    }
  }
  
  // 检查格子是否是预填的
  function isPrefilledCell(row, col) {
    const key = `${row}-${col}`
    return prefilledCells.value[key] === true
  }
  
  function setAnswer(row, col, letter) {
    const key = `${row}-${col}`
    const oldLetter = userAnswers.value[key]
    userAnswers.value[key] = letter.toUpperCase()
    
    // 如果修改了已完成单词的格子，需要取消该单词的完成状态
    if (oldLetter && oldLetter !== letter.toUpperCase()) {
      uncheckWordAtCell(row, col)
    }
  }
  
  // 取消包含该格子的已完成单词
  function uncheckWordAtCell(row, col) {
    const wordsToRemove = []
    
    for (const completedWord of completedWords.value) {
      let inWord = false
      if (completedWord.direction === 'across') {
        inWord = row === completedWord.start_row && 
                 col >= completedWord.start_col && 
                 col < completedWord.start_col + completedWord.length
      } else {
        inWord = col === completedWord.start_col && 
                 row >= completedWord.start_row && 
                 row < completedWord.start_row + completedWord.length
      }
      
      if (inWord) {
        wordsToRemove.push(completedWord.id)
      }
    }
    
    // 移除这些单词
    for (const wordId of wordsToRemove) {
      const idx = completedWords.value.findIndex(w => w.id === wordId)
      if (idx !== -1) {
        const word = completedWords.value[idx]
        // 减去对应分数
        score.value -= word.length * 10
        completedWords.value.splice(idx, 1)
      }
    }
  }
  
  function getAnswer(row, col) {
    const key = `${row}-${col}`
    return userAnswers.value[key] || ''
  }
  
  function checkWord(wordId) {
    const word = words.value.find(w => w.id === wordId)
    if (!word) return false
    
    // 如果已经完成，直接返回true
    if (completedWords.value.find(w => w.id === wordId)) {
      return true
    }
    
    let userWord = ''
    for (let i = 0; i < word.length; i++) {
      let row = word.start_row
      let col = word.start_col
      
      if (word.direction === 'across') {
        col += i
      } else {
        row += i
      }
      
      userWord += getAnswer(row, col)
    }
    
    // 检查是否匹配答案（去掉备选答案逻辑）
    const isCorrect = userWord.toUpperCase() === word.word.toUpperCase()
    
    if (isCorrect) {
      const completedWordInfo = {
        ...word,
        matchedWord: word.word,
        matchedDefinition: word.definition,
        isAlternative: false
      }
      completedWords.value.push(completedWordInfo)
      score.value += word.length * 10
      // 检查设置项：是否自动发音
      try {
        const settings = JSON.parse(localStorage.getItem('game_settings') || '{}')
        if (settings.autoSpeak !== false) {
          speakWord(word.word)
        }
      } catch (e) {
        speakWord(word.word)
      }
    }
    
    return isCorrect
  }
  
  // 检查所有单词的完成状态（用于初始化和每次输入后）
  function checkAllWords() {
    for (const word of words.value) {
      if (!completedWords.value.find(w => w.id === word.id)) {
        checkWord(word.id)
      }
    }
  }
  
  // 当前音频播放器
  let currentAudio = null

  // 使用本地音频文件播放单词发音
  function speakWord(text, voiceType = null) {
    // 获取设置中的发音类型
    let type = voiceType
    if (!type) {
      try {
        const settings = JSON.parse(localStorage.getItem('game_settings') || '{}')
        type = settings.voiceType || 'us'
      } catch (e) {
        type = 'us'
      }
    }

    // 停止当前播放
    if (currentAudio) {
      currentAudio.pause()
      currentAudio = null
    }

    // 单词转小写，处理特殊字符
    const word = text.toLowerCase().trim()
    if (!word) return

    // 构建音频路径 - 后端静态文件服务
    const audioPath = `/data/audio/${type}/${word}.mp3`

    try {
      currentAudio = new Audio(audioPath)
      currentAudio.volume = 1.0
      
      currentAudio.play().catch(err => {
        console.warn('本地音频播放失败，尝试在线API:', err)
        // 回退到有道在线API
        fallbackSpeakOnline(word, type)
      })

      currentAudio.onended = () => {
        currentAudio = null
      }
    } catch (e) {
      console.warn('创建音频失败:', e)
      fallbackSpeakOnline(word, type)
    }
  }

  // 回退到有道在线API
  function fallbackSpeakOnline(word, type = 'us') {
    try {
      // 有道API: type=1 英音, type=2 美音
      const youdaoType = type === 'uk' ? 1 : 2
      const url = `https://dict.youdao.com/dictvoice?audio=${encodeURIComponent(word)}&type=${youdaoType}`
      
      currentAudio = new Audio(url)
      currentAudio.volume = 1.0
      currentAudio.play().catch(err => {
        console.warn('在线发音也失败:', err)
        // 最后回退到 Web Speech API
        fallbackSpeechSynthesis(word)
      })

      currentAudio.onended = () => {
        currentAudio = null
      }
    } catch (e) {
      fallbackSpeechSynthesis(word)
    }
  }

  // 最终回退到浏览器语音合成
  function fallbackSpeechSynthesis(text) {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = 'en-US'
      utterance.rate = 0.8
      window.speechSynthesis.speak(utterance)
    }
  }
  
  function startTimer(seconds = null) {
    if (timerInterval.value) {
      clearInterval(timerInterval.value)
    }
    
    if (seconds !== null) {
      timer.value = seconds
    } else {
      // 如果没有指定秒数，正计时模式从0开始
      if (currentMode.value === 'campaign') {
        timer.value = 0
      }
    }
    
    isPlaying.value = true
    
    timerInterval.value = setInterval(() => {
      if (currentMode.value === 'timed' || currentMode.value === 'pk' || currentMode.value === 'endless') {
        // 倒计时（计时/PK/无限模式）
        timer.value--
        if (timer.value <= 0) {
          timer.value = 0
          stopTimer()
          // 触发时间结束事件（由 Game.vue 监听处理）
        }
      } else {
        // 正计时（闯关模式）
        timer.value++
      }
    }, 1000)
  }
  
  function stopTimer() {
    if (timerInterval.value) {
      clearInterval(timerInterval.value)
      timerInterval.value = null
    }
    isPlaying.value = false
  }
  
  function resetGame() {
    stopTimer()
    puzzle.value = null
    userAnswers.value = {}
    prefilledCells.value = {}
    completedWords.value = []
    score.value = 0
    timer.value = 0
    isPlaying.value = false
  }
  
  async function nextLevel() {
    if (currentMode.value === 'campaign') {
      // 保存当前关卡完成状态
      saveLevelProgress(currentLevel.value)
      
      // 进入下一关
      const nextLevelNum = currentLevel.value + 1
      currentLevel.value = nextLevelNum
      
      // 更新localStorage中保存的当前关卡
      localStorage.setItem(`campaign_level_${currentGroup.value}`, nextLevelNum.toString())
      
      // 加载下一关
      await loadPuzzle('campaign', nextLevelNum, currentGroup.value)
      
      // 检查预填完成的单词
      checkAllWords()
      
      // 重新启动计时器（正计时从0开始）
      startTimer(0)
    } else {
      await loadPuzzle(currentMode.value, 0, currentGroup.value)
      startTimer()
    }
  }
  
  function saveLevelProgress(completedLevel, earnedStars = null) {
    const group = currentGroup.value
    const key = `campaign_progress_${group}`
    
    // 读取当前进度
    let progress = { unlocked: 1, completed: {} }
    const saved = localStorage.getItem(key)
    if (saved) {
      try {
        progress = JSON.parse(saved)
      } catch (e) {}
    }
    
    // 计算星级：2分钟内三星，3分钟内两星，5分钟以上一星
    let stars = earnedStars
    if (stars === null) {
      const seconds = timer.value
      if (seconds <= 120) stars = 3
      else if (seconds <= 180) stars = 2
      else stars = 1
    }
    
    // 只保存更高的星级
    const existingStars = progress.completed[completedLevel]?.stars || 0
    if (stars > existingStars) {
      progress.completed[completedLevel] = {
        stars: stars,
        score: score.value,
        time: timer.value
      }
    } else if (!progress.completed[completedLevel]) {
      progress.completed[completedLevel] = {
        stars: stars,
        score: score.value,
        time: timer.value
      }
    }
    
    // 解锁下一关（动态最大关卡数，默认500）
    const maxLevels = 500
    if (completedLevel >= progress.unlocked && completedLevel < maxLevels) {
      progress.unlocked = completedLevel + 1
    }
    
    // 保存进度
    localStorage.setItem(key, JSON.stringify(progress))
  }
  
  return {
    // 状态
    currentGroup,
    currentMode,
    currentLevel,
    puzzle,
    userAnswers,
    prefilledCells,
    completedWords,
    score,
    timer,
    isPlaying,
    groups,
    cachedLevels,
    
    // 计算属性
    gridSize,
    words,
    cells,
    clueNumbers,
    progress,
    isLevelComplete,
    formattedTimer,
    
    // 动作
    loadPuzzle,
    loadGroupLevels,
    loadSingleLevel,
    preloadNearbyLevels,
    getGroupLevelCount,
    setAnswer,
    getAnswer,
    checkWord,
    checkAllWords,
    speakWord,
    startTimer,
    stopTimer,
    resetGame,
    nextLevel,
    isPrefilledCell,
    saveLevelProgress
  }
})
