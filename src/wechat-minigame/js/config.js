/**
 * 小游戏配置常量
 */

// API配置
// 注意：开发环境使用 http，生产环境需要配置 https
var API_BASE = 'http://superhe.art:10010'

// 颜色配置 - 马卡龙风格 (与网页版完全一致)
var COLORS = {
  // 主色调 - 粉色系
  primary: '#FF69B4',        // 深粉色（强调色）
  primaryDark: '#DB3580',    // 更深的粉色（阴影色）
  primaryLight: '#FFB6C1',   // 婴儿粉（主边框色）
  primaryBg: '#FFF0F5',      // 浅粉色背景
  
  // 薄荷绿系
  mint: '#98FB98',           // 薄荷绿
  mintDark: '#3CB371',       // 深薄荷绿
  mintLight: '#E0FBE0',      // 浅薄荷绿
  
  // 天蓝系
  skyBlue: '#87CEEB',        // 天蓝
  skyBlueDark: '#4682B4',    // 深天蓝
  skyBlueLight: '#F0F8FF',   // 浅天蓝
  
  // 柠檬黄系
  lemon: '#FFFACD',          // 柠檬黄
  lemonDark: '#DAA520',      // 金色
  lemonLight: '#FFFFF0',     // 浅柠檬
  
  // 香芋紫系
  purple: '#DDA0DD',         // 香芋紫
  purpleDark: '#BA55D3',     // 深紫
  purpleLight: '#F3E6F3',    // 浅紫
  
  // 功能色
  success: '#10b981',        // 成功绿
  successLight: '#a7f3d0',   // 浅绿
  warning: '#fbbf24',        // 警告黄
  warningDark: '#d97706',    // 深黄
  error: '#ef4444',          // 错误红
  errorLight: '#fecaca',     // 浅红
  
  // 中性色
  white: '#FFFFFF',
  background: '#FFFAF0',     // 奶白色页面背景
  cream: '#FFFAF0',          // 奶白色
  creamLight: '#FAF8F5',     // 浅奶白
  creamDark: '#F5EFE6',      // 米色
  text: '#5D5D5D',           // 主文字色（避免纯黑）
  textLight: '#888888',      // 次要文字色
  textLighter: '#AAAAAA',    // 更浅文字色
  border: '#FFB6C1',         // 边框色（浅粉色）
  borderDark: '#FF69B4',     // 深边框色
  borderNeutral: '#e5e7eb',  // 中性边框色（灰色）
  borderNeutralDark: '#d1d5db' // 深中性边框色
}

// 词库配置
var VOCAB_GROUPS = [
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
      { code: 'grade6_2', name: '六年级下册', icon: '🎋' }
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
      { code: 'junior9', name: '九年级全册', icon: '🌴' }
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
      { code: 'senior5', name: '必修5', icon: '📓' }
    ]
  },
  { code: 'ket', name: 'KET考试', icon: '🎯' },
  { code: 'pet', name: 'PET考试', icon: '🎓' },
  { code: 'cet4', name: '大学四级', icon: '🏛️' },
  { code: 'cet6', name: '大学六级', icon: '🎖️' },
  { code: 'postgrad', name: '考研词汇', icon: '🔬' },
  { code: 'ielts', name: '雅思', icon: '✈️' },
  { code: 'toefl', name: '托福', icon: '🗽' },
  { code: 'gre', name: 'GRE', icon: '🎩' }
]

// 难度配置
var DIFFICULTY_OPTIONS = [
  { code: 'low', name: '简单', desc: '2-4字母短词', icon: '🌱' },
  { code: 'medium', name: '中等', desc: '3-6字母词汇', icon: '🌿' },
  { code: 'high', name: '困难', desc: '5-10字母长词', icon: '🌲' }
]

// 时间配置（计时模式）
var DURATION_OPTIONS = [
  { value: 60, label: '1分钟', icon: '⏱️' },
  { value: 180, label: '3分钟', icon: '⏳' },
  { value: 300, label: '5分钟', icon: '🕐' }
]

// 体力配置
var ENERGY_CONFIG = {
  max: 200,                    // 最大体力
  initial: 200,                // 初始体力
  recoveryPerMinute: 1,        // 每分钟恢复
  freeClaimAmount: 30,         // 免费领取数量
  cost: {
    campaign: 10,              // 闯关模式消耗
    endless: 30,               // 无限模式消耗
    timed: 30                  // 计时模式消耗
  }
}

// 道具配置（与网页版游戏页一致）
// 💡 提示道具：高亮提示字母
// 🔊 发音道具：朗读单词三遍
var PROPS_CONFIG = {
  initial: {
    hint: 20,                  // 初始提示道具
    speak: 20                  // 初始发音道具
  }
}

// 键盘布局
var KEYBOARD_LAYOUT = [
  ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
  ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
  ['Z', 'X', 'C', 'V', 'B', 'N', 'M', '⌫']
]

// 游戏模式
var GAME_MODES = {
  campaign: { name: '闯关', icon: '🏰', desc: '词库闯关' },
  endless: { name: '无限', icon: '♾️', desc: '随机关卡' },
  timed: { name: '计时', icon: '⏱️', desc: '限时挑战' }
}

// 无限模式时间计算（根据网格大小）
// 公式：30 + (网格大小 - 4) × 10 秒
function getEndlessTimeLimit(gridSize) {
  return 30 + (gridSize - 4) * 10
}

// 排行榜类型配置（与网页版一致：6种类型）
var LEADERBOARD_TYPES = [
  { code: 'campaign_level', name: '闯关关卡榜', icon: '🏰' },
  { code: 'campaign_score', name: '闯关积分榜', icon: '🌟' },
  { code: 'endless_level', name: '无限关卡榜', icon: '♾️' },
  { code: 'endless_score', name: '无限积分榜', icon: '📊' },
  { code: 'timed_words', name: '计时单词榜', icon: '⏱️' },
  { code: 'timed_score', name: '计时积分榜', icon: '🏆' }
]

// 词库分类（用于排行榜筛选，与Web版一致）
var GROUP_CATEGORIES = [
  { code: 'primary', name: '小学' },
  { code: 'secondary', name: '初高中' },  // 初中+高中合并
  { code: 'exam', name: '考试' }
]

// 头像选项
var AVATAR_OPTIONS = ['😊', '😎', '🤓', '😺', '🐶', '🦊', '🐰', '🐼', '🦁', '🐸', '🐵', '🐷']

// 字体大小常量
var FONT_SIZES = {
  title: 32,           // 主标题
  subtitle: 16,        // 副标题
  body: 14,            // 正文
  small: 12,           // 小字
  tiny: 10,            // 极小字
  levelButton: 18,     // 关卡按钮数字
  modeIcon: 32,        // 模式图标
  keyboardKey: 16      // 键盘按键
}

// 开发模式配置
var DEV_CONFIG = {
  clickThreshold: 10,  // 连击次数阈值
  clickTimeout: 2000   // 连击超时时间(ms)
}

module.exports = {
  API_BASE: API_BASE,
  COLORS: COLORS,
  VOCAB_GROUPS: VOCAB_GROUPS,
  DIFFICULTY_OPTIONS: DIFFICULTY_OPTIONS,
  DURATION_OPTIONS: DURATION_OPTIONS,
  ENERGY_CONFIG: ENERGY_CONFIG,
  PROPS_CONFIG: PROPS_CONFIG,
  KEYBOARD_LAYOUT: KEYBOARD_LAYOUT,
  GAME_MODES: GAME_MODES,
  getEndlessTimeLimit: getEndlessTimeLimit,
  LEADERBOARD_TYPES: LEADERBOARD_TYPES,
  GROUP_CATEGORIES: GROUP_CATEGORIES,
  AVATAR_OPTIONS: AVATAR_OPTIONS,
  FONT_SIZES: FONT_SIZES,
  DEV_CONFIG: DEV_CONFIG
}
