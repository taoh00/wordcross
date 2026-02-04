// Kawaii Pastel Theme for iOS App
// Matches WeChat MiniGame & Web Frontend
// 马卡龙配色统一定义

export const COLORS = {
  // Core Pastel Palette - 核心马卡龙色
  mint: {
    main: '#98FB98',    // 薄荷绿
    dark: '#3CB371',    // 深薄荷绿
    light: '#E0FBE0',   // 浅薄荷绿
  },
  pink: {
    main: '#FFB6C1',    // 婴儿粉（主边框色）
    dark: '#FF69B4',    // 深粉色（强调色）
    light: '#FFF0F5',   // 浅粉色
  },
  blue: {
    main: '#87CEEB',    // 天蓝（装饰用）
    dark: '#4682B4',    // 深天蓝
    light: '#F0F8FF',   // 浅天蓝
  },
  yellow: {
    main: '#FFFACD',    // 柠檬黄
    dark: '#DAA520',    // 金色（更深的黄）
    light: '#FFFFF0',   // 浅柠檬黄
  },
  purple: {
    main: '#DDA0DD',    // 香芋紫
    dark: '#BA55D3',    // 深紫
    light: '#F3E6F3',   // 浅紫
  },
  
  // Cream - 奶白色（副色）
  cream: {
    main: '#FFFAF0',    // 奶白色（页面背景）
    light: '#FAF8F5',   // 更浅奶白
    dark: '#F5EFE6',    // 浅米色
  },
  
  // Neutrals - 中性色
  white: '#FFFFFF',           // 纯白（卡片背景）
  textMain: '#5D5D5D',        // 主文字色（替代白色文字）
  textLight: '#888888',       // 次要文字色
  textLighter: '#AAAAAA',     // 更浅文字色
  
  // Semantic - 语义色
  bg: '#FFFAF0',              // 页面背景（奶白色）
  border: '#FFB6C1',          // 边框色（浅粉色，替代蓝色）
  shadow: '#FFB6C1',          // 阴影色
  
  // 兼容旧属性
  background: '#FFFAF0',
  blueLight: '#F0F8FF',
};

// 阴影定义 - 使用粉色系
export const SHADOWS = {
  soft: {
    shadowColor: '#FFB6C1',   // 改为粉色
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
    elevation: 5,
  },
  card: {
    shadowColor: '#FFB6C1',   // 改为粉色
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 0,          // 3D效果
    elevation: 4,
  },
  button3D: (color: string = '#FF69B4') => ({
    shadowColor: color,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 1, // Solid shadow for 3D effect
    shadowRadius: 0,
    elevation: 4,
  }),
};

export const LAYOUT = {
  radiusLg: 24,
  radiusMd: 16,
  radiusSm: 8,
  padding: 16,
};

// 按钮样式预设
export const BUTTON_STYLES = {
  primary: {
    backgroundColor: COLORS.pink.main,
    borderColor: COLORS.pink.dark,
    textColor: COLORS.textMain,  // 深色文字，不是白色
    shadowColor: COLORS.pink.dark,
  },
  secondary: {
    backgroundColor: COLORS.cream.main,
    borderColor: COLORS.pink.main,
    textColor: COLORS.textMain,
    shadowColor: COLORS.yellow.dark,
  },
  success: {
    backgroundColor: COLORS.mint.main,
    borderColor: COLORS.mint.dark,
    textColor: COLORS.textMain,
    shadowColor: COLORS.mint.dark,
  },
};

// 卡片样式预设
export const CARD_STYLES = {
  default: {
    backgroundColor: COLORS.white,
    borderColor: COLORS.pink.main,
    borderRadius: LAYOUT.radiusLg,
    shadowColor: COLORS.pink.main,
  },
};
