/**
 * 音效管理模块
 * 使用 Web Audio API 生成游戏音效
 */

// 音频上下文（延迟创建以避免自动播放限制）
let audioContext = null

// 背景音乐
let bgmSource = null
let bgmGainNode = null
let bgmLoopTimeout = null
let bgmOscillators = []  // 存储活动的振荡器以便淡出

// 当前播放的模式
let currentBgmMode = null

// 获取或创建音频上下文
function getAudioContext() {
  if (!audioContext) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)()
  }
  // 如果上下文被暂停，恢复它
  if (audioContext.state === 'suspended') {
    audioContext.resume()
  }
  return audioContext
}

// 检查设置
function getSettings() {
  try {
    return JSON.parse(localStorage.getItem('game_settings') || '{}')
  } catch {
    return {}
  }
}

/**
 * 播放输入字母音效 - 清脆的点击声
 */
export function playTypeSound() {
  const settings = getSettings()
  if (settings.soundEffect === false) return

  try {
    const ctx = getAudioContext()
    const oscillator = ctx.createOscillator()
    const gainNode = ctx.createGain()
    
    oscillator.connect(gainNode)
    gainNode.connect(ctx.destination)
    
    oscillator.type = 'sine'
    oscillator.frequency.setValueAtTime(800, ctx.currentTime)
    oscillator.frequency.exponentialRampToValueAtTime(600, ctx.currentTime + 0.05)
    
    gainNode.gain.setValueAtTime(0.15, ctx.currentTime)
    gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.05)
    
    oscillator.start(ctx.currentTime)
    oscillator.stop(ctx.currentTime + 0.05)

    // 震动反馈
    if (settings.vibration !== false && navigator.vibrate) {
      navigator.vibrate(10)
    }
  } catch (e) {
    // 忽略音效播放错误
  }
}

/**
 * 播放删除音效 - 低沉的点击声
 */
export function playDeleteSound() {
  const settings = getSettings()
  if (settings.soundEffect === false) return

  try {
    const ctx = getAudioContext()
    const oscillator = ctx.createOscillator()
    const gainNode = ctx.createGain()
    
    oscillator.connect(gainNode)
    gainNode.connect(ctx.destination)
    
    oscillator.type = 'sine'
    oscillator.frequency.setValueAtTime(400, ctx.currentTime)
    oscillator.frequency.exponentialRampToValueAtTime(200, ctx.currentTime + 0.08)
    
    gainNode.gain.setValueAtTime(0.12, ctx.currentTime)
    gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.08)
    
    oscillator.start(ctx.currentTime)
    oscillator.stop(ctx.currentTime + 0.08)
  } catch (e) {
    // 忽略
  }
}

/**
 * 播放正确音效 - 悦耳的双音符
 */
export function playCorrectSound() {
  const settings = getSettings()
  if (settings.soundEffect === false) return

  try {
    const ctx = getAudioContext()
    
    // 第一个音符 C5
    const osc1 = ctx.createOscillator()
    const gain1 = ctx.createGain()
    osc1.connect(gain1)
    gain1.connect(ctx.destination)
    osc1.type = 'sine'
    osc1.frequency.value = 523.25
    gain1.gain.setValueAtTime(0.2, ctx.currentTime)
    gain1.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.15)
    osc1.start(ctx.currentTime)
    osc1.stop(ctx.currentTime + 0.15)
    
    // 第二个音符 E5（延迟0.1秒）
    const osc2 = ctx.createOscillator()
    const gain2 = ctx.createGain()
    osc2.connect(gain2)
    gain2.connect(ctx.destination)
    osc2.type = 'sine'
    osc2.frequency.value = 659.25
    gain2.gain.setValueAtTime(0.2, ctx.currentTime + 0.1)
    gain2.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.25)
    osc2.start(ctx.currentTime + 0.1)
    osc2.stop(ctx.currentTime + 0.25)

    // 震动反馈
    if (settings.vibration !== false && navigator.vibrate) {
      navigator.vibrate([30, 50, 30])
    }
  } catch (e) {
    // 忽略
  }
}

/**
 * 播放错误音效 - 低沉的嗡嗡声
 */
export function playWrongSound() {
  const settings = getSettings()
  if (settings.soundEffect === false) return

  try {
    const ctx = getAudioContext()
    const oscillator = ctx.createOscillator()
    const gainNode = ctx.createGain()
    
    oscillator.connect(gainNode)
    gainNode.connect(ctx.destination)
    
    oscillator.type = 'sawtooth'
    oscillator.frequency.setValueAtTime(150, ctx.currentTime)
    oscillator.frequency.exponentialRampToValueAtTime(100, ctx.currentTime + 0.2)
    
    gainNode.gain.setValueAtTime(0.1, ctx.currentTime)
    gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2)
    
    oscillator.start(ctx.currentTime)
    oscillator.stop(ctx.currentTime + 0.2)

    // 震动反馈
    if (settings.vibration !== false && navigator.vibrate) {
      navigator.vibrate(100)
    }
  } catch (e) {
    // 忽略
  }
}

/**
 * 播放通关音效 - 欢快的旋律（增强版，确保能播放）
 */
export function playLevelCompleteSound() {
  const settings = getSettings()
  // 默认开启音效
  if (settings.soundEffect === false) return

  try {
    const ctx = getAudioContext()
    
    // 确保音频上下文处于运行状态
    if (ctx.state === 'suspended') {
      ctx.resume().then(() => {
        playLevelCompleteMelody(ctx)
      })
    } else {
      playLevelCompleteMelody(ctx)
    }

    // 震动反馈
    if (settings.vibration !== false && navigator.vibrate) {
      navigator.vibrate([50, 50, 50, 50, 100])
    }
  } catch (e) {
    console.warn('通关音效播放失败:', e)
  }
}

// 播放通关旋律的具体实现
function playLevelCompleteMelody(ctx) {
  // 播放一段欢快的旋律 C-E-G-C(高)，音量更大
  const notes = [
    { freq: 523.25, time: 0 },      // C5
    { freq: 659.25, time: 0.15 },   // E5
    { freq: 783.99, time: 0.30 },   // G5
    { freq: 1046.50, time: 0.45 }   // C6
  ]
  
  notes.forEach(note => {
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain)
    gain.connect(ctx.destination)
    
    osc.type = 'sine'
    osc.frequency.value = note.freq
    
    // 增大音量，延长时间
    gain.gain.setValueAtTime(0.35, ctx.currentTime + note.time)
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + note.time + 0.3)
    
    osc.start(ctx.currentTime + note.time)
    osc.stop(ctx.currentTime + note.time + 0.3)
  })
}

/**
 * 播放按钮点击音效
 */
export function playClickSound() {
  const settings = getSettings()
  if (settings.soundEffect === false) return

  try {
    const ctx = getAudioContext()
    const oscillator = ctx.createOscillator()
    const gainNode = ctx.createGain()
    
    oscillator.connect(gainNode)
    gainNode.connect(ctx.destination)
    
    oscillator.type = 'sine'
    oscillator.frequency.value = 600
    
    gainNode.gain.setValueAtTime(0.1, ctx.currentTime)
    gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.03)
    
    oscillator.start(ctx.currentTime)
    oscillator.stop(ctx.currentTime + 0.03)
  } catch (e) {
    // 忽略
  }
}

/**
 * 开始播放背景音乐
 * 根据游戏模式播放不同风格的音乐
 * @param {string} mode - 游戏模式: 'campaign', 'endless', 'timed', 'pk'
 */
export function startBgMusic(mode = 'campaign') {
  const settings = getSettings()
  if (settings.bgMusic === false) return
  
  try {
    const ctx = getAudioContext()
    
    // 如果已经在播放相同模式的音乐，不重复启动
    if (currentBgmMode === mode && bgmGainNode) return
    
    // 停止之前的背景音乐（带淡出）
    stopBgMusic()
    
    currentBgmMode = mode
    bgmOscillators = []
    
    // 创建主音量控制
    bgmGainNode = ctx.createGain()
    bgmGainNode.gain.value = 0  // 从0开始淡入
    bgmGainNode.connect(ctx.destination)
    
    // 淡入到目标音量
    const targetVolume = 0.08
    bgmGainNode.gain.linearRampToValueAtTime(targetVolume, ctx.currentTime + 0.5)
    
    // 根据模式选择不同的旋律和节奏
    let melodyNotes, noteFreq, baseTempo
    
    if (mode === 'timed' || mode === 'pk') {
      // 计时/PK模式：快节奏、紧张感
      baseTempo = 0.35  // 更快的节奏
      melodyNotes = [
        { note: 'E4', duration: baseTempo },
        { note: 'G4', duration: baseTempo },
        { note: 'A4', duration: baseTempo },
        { note: 'G4', duration: baseTempo },
        { note: 'E4', duration: baseTempo },
        { note: 'D4', duration: baseTempo },
        { note: 'E4', duration: baseTempo * 2 },
        { note: 'G4', duration: baseTempo },
        { note: 'A4', duration: baseTempo },
        { note: 'B4', duration: baseTempo },
        { note: 'A4', duration: baseTempo },
        { note: 'G4', duration: baseTempo },
        { note: 'E4', duration: baseTempo },
        { note: 'D4', duration: baseTempo * 2 },
      ]
      noteFreq = {
        'D4': 293.66,
        'E4': 329.63,
        'G4': 392.00,
        'A4': 440.00,
        'B4': 493.88,
      }
    } else {
      // 闯关/无限模式：舒缓卡通风格
      baseTempo = 0.8
      melodyNotes = [
        { note: 'C4', duration: baseTempo },
        { note: 'E4', duration: baseTempo },
        { note: 'G4', duration: baseTempo },
        { note: 'E4', duration: baseTempo },
        { note: 'F4', duration: baseTempo },
        { note: 'A4', duration: baseTempo },
        { note: 'G4', duration: baseTempo * 1.5 },
        { note: 'E4', duration: baseTempo * 0.5 },
        { note: 'D4', duration: baseTempo },
        { note: 'F4', duration: baseTempo },
        { note: 'E4', duration: baseTempo },
        { note: 'C4', duration: baseTempo },
        { note: 'D4', duration: baseTempo },
        { note: 'G3', duration: baseTempo },
        { note: 'C4', duration: baseTempo * 2 },
      ]
      noteFreq = {
        'G3': 196.00,
        'C4': 261.63,
        'D4': 293.66,
        'E4': 329.63,
        'F4': 349.23,
        'G4': 392.00,
        'A4': 440.00,
      }
    }
    
    // 计算旋律总时长
    const melodyDuration = melodyNotes.reduce((sum, n) => sum + n.duration, 0)
    
    // 播放旋律函数
    function playMelody(startTime) {
      let time = startTime
      
      melodyNotes.forEach(({ note, duration }) => {
        const freq = noteFreq[note]
        if (!freq || !bgmGainNode) return
        
        // 使用正弦波 + 三角波混合，更柔和
        const osc1 = ctx.createOscillator()
        const osc2 = ctx.createOscillator()
        const noteGain = ctx.createGain()
        
        osc1.type = 'sine'
        osc1.frequency.value = freq
        osc2.type = 'triangle'
        osc2.frequency.value = freq * 2  // 高八度泛音
        
        const noteGain2 = ctx.createGain()
        noteGain2.gain.value = mode === 'timed' || mode === 'pk' ? 0.2 : 0.15
        
        osc1.connect(noteGain)
        osc2.connect(noteGain2)
        noteGain2.connect(noteGain)
        noteGain.connect(bgmGainNode)
        
        // 柔和的包络，避免爆音
        noteGain.gain.setValueAtTime(0, time)
        noteGain.gain.linearRampToValueAtTime(0.5, time + 0.05)
        noteGain.gain.linearRampToValueAtTime(0.3, time + duration * 0.5)
        noteGain.gain.linearRampToValueAtTime(0, time + duration - 0.02)
        
        osc1.start(time)
        osc1.stop(time + duration)
        osc2.start(time)
        osc2.stop(time + duration)
        
        // 跟踪振荡器
        bgmOscillators.push({ osc: osc1, stopTime: time + duration })
        bgmOscillators.push({ osc: osc2, stopTime: time + duration })
        
        time += duration
      })
      
      return time
    }
    
    // 循环播放旋律
    function scheduleLoop() {
      if (!bgmGainNode) return  // 已停止
      
      // 清理已停止的振荡器，避免内存累积
      const currentTime = ctx.currentTime
      bgmOscillators = bgmOscillators.filter(item => item.stopTime > currentTime)
      
      const startTime = ctx.currentTime + 0.1
      playMelody(startTime)
      
      // 设置下一次循环
      bgmLoopTimeout = setTimeout(scheduleLoop, (melodyDuration - 0.3) * 1000)
    }
    
    scheduleLoop()
    
  } catch (e) {
    console.warn('背景音乐启动失败:', e)
  }
}

/**
 * 停止背景音乐（带淡出，避免爆音）
 */
export function stopBgMusic() {
  // 清理循环定时器
  if (bgmLoopTimeout) {
    clearTimeout(bgmLoopTimeout)
    bgmLoopTimeout = null
  }
  
  // 重置当前模式
  currentBgmMode = null
  
  // 淡出音量后断开，避免爆音
  if (bgmGainNode) {
    try {
      const ctx = getAudioContext()
      const currentTime = ctx.currentTime
      
      // 快速淡出到0
      bgmGainNode.gain.cancelScheduledValues(currentTime)
      bgmGainNode.gain.setValueAtTime(bgmGainNode.gain.value, currentTime)
      bgmGainNode.gain.linearRampToValueAtTime(0, currentTime + 0.1)
      
      // 延迟后断开连接
      const gainNodeToDisconnect = bgmGainNode
      setTimeout(() => {
        try {
          gainNodeToDisconnect.disconnect()
        } catch (e) {
          // 忽略
        }
      }, 150)
    } catch (e) {
      // 忽略
      try {
        bgmGainNode.disconnect()
      } catch (e2) {
        // 忽略
      }
    }
    bgmGainNode = null
  }
  
  if (bgmSource) {
    try {
      bgmSource.stop()
    } catch (e) {
      // 忽略
    }
    bgmSource = null
  }
  
  // 清理振荡器列表
  bgmOscillators = []
}

/**
 * 设置背景音乐音量
 * @param {number} volume - 0到1之间的值
 */
export function setBgMusicVolume(volume) {
  if (bgmGainNode) {
    bgmGainNode.gain.value = volume * 0.1 // 保持较低音量
  }
}

// 导出所有函数
export default {
  playTypeSound,
  playDeleteSound,
  playCorrectSound,
  playWrongSound,
  playLevelCompleteSound,
  playClickSound,
  startBgMusic,
  stopBgMusic,
  setBgMusicVolume
}
