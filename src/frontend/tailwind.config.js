/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Hormone Color Palette (荷尔蒙色 - 新主题)
        hormone: {
          // 主色 - 活力珊瑚粉
          primary: {
            DEFAULT: '#FF4081',
            dark: '#E91E63',
            light: '#FF80AB'
          },
          // 次要色 - 电光蓝
          secondary: {
            DEFAULT: '#00E5FF',
            dark: '#00BCD4',
            light: '#80D8FF'
          },
          // 强调色 - 霓虹紫
          accent: {
            DEFAULT: '#9C27B0',
            dark: '#7B1FA2',
            light: '#CE93D8'
          },
          // 装饰色 - 活力橙
          orange: {
            DEFAULT: '#FF6D00',
            dark: '#E65100',
            light: '#FFB74D'
          },
          // 装饰色 - 霓虹绿
          green: {
            DEFAULT: '#00E676',
            dark: '#00C853',
            light: '#69F0AE'
          },
          // 装饰色 - 电光黄
          yellow: {
            DEFAULT: '#FFD600',
            dark: '#FFC400',
            light: '#FFEE58'
          },
          // 背景色
          bg: {
            DEFAULT: '#1A1A2E',
            secondary: '#16213E',
            light: '#0F3460'
          },
          // 文字色
          text: {
            main: '#FFFFFF',
            light: '#E0E0E0',
            lighter: '#B0B0B0'
          },
          // 边框色
          border: {
            DEFAULT: '#FF4081',
            secondary: '#37474F',
            light: '#546E7A'
          },
          // 语义色
          success: {
            DEFAULT: '#00E676',
            dark: '#00C853',
            light: '#69F0AE'
          },
          warning: {
            DEFAULT: '#FFD600',
            dark: '#FFC400',
            light: '#FFEE58'
          },
          error: {
            DEFAULT: '#FF1744',
            dark: '#D50000',
            light: '#FF5252'
          },
          info: {
            DEFAULT: '#00E5FF',
            dark: '#00BCD4',
            light: '#80D8FF'
          }
        },
        // Kawaii Pastel Palette (马卡龙配色 - 保留以向后兼容)
        kawaii: {
          mint: {
            DEFAULT: '#98FB98',
            dark: '#3CB371',
            light: '#E0FBE0'
          },
          pink: {
            DEFAULT: '#FFB6C1',   // 主边框色
            dark: '#FF69B4',      // 强调色
            light: '#FFF0F5'
          },
          blue: {
            DEFAULT: '#87CEEB',   // 装饰用
            dark: '#4682B4',
            light: '#F0F8FF'
          },
          yellow: {
            DEFAULT: '#FFFACD',
            dark: '#DAA520',      // 金色
            light: '#FFFFF0'
          },
          purple: {
            DEFAULT: '#DDA0DD',   // 香芋紫
            dark: '#BA55D3',
            light: '#F3E6F3'
          },
          // 奶白色（副色）
          cream: {
            DEFAULT: '#FFFAF0',
            dark: '#F5EFE6',
            light: '#FAF8F5'
          },
          // 文字色
          text: {
            main: '#5D5D5D',      // 主文字（替代白色）
            light: '#888888',
            lighter: '#AAAAAA'
          },
          // 页面背景
          bg: '#FFFAF0',          // 奶白色
          // 边框色
          border: '#FFB6C1'       // 浅粉色
        }
      },
      fontFamily: {
        cute: ['Nunito', 'PingFang SC', 'Microsoft YaHei', 'cursive'],
      },
      boxShadow: {
        // 荷尔蒙色3D阴影
        'soft': '0 6px 0 rgba(255, 64, 129, 0.8)',
        '3d': '0 4px 0 rgba(233, 30, 99, 0.9)',
        'card': '0 8px 16px rgba(0, 0, 0, 0.4)',
        'hover': '0 12px 24px rgba(255, 64, 129, 0.5)',
        'inset': 'inset 0 2px 4px rgba(0, 0, 0, 0.3)',
        'glow': '0 0 20px rgba(255, 64, 129, 0.6)',
        // 各颜色的3D阴影
        '3d-primary': '0 4px 0 rgba(233, 30, 99, 0.9)',
        '3d-secondary': '0 4px 0 rgba(0, 188, 212, 0.9)',
        '3d-accent': '0 4px 0 rgba(123, 31, 162, 0.9)',
        '3d-success': '0 4px 0 rgba(0, 200, 83, 0.9)',
        '3d-warning': '0 4px 0 rgba(255, 196, 0, 0.9)',
        '3d-error': '0 4px 0 rgba(213, 0, 0, 0.9)',
        '3d-info': '0 4px 0 rgba(0, 188, 212, 0.9)',
        // 保留马卡龙色阴影
        '3d-pink': '0 4px 0 #FF69B4',
        '3d-mint': '0 4px 0 #3CB371',
        '3d-blue': '0 4px 0 #4682B4',
        '3d-yellow': '0 4px 0 #DAA520',
        '3d-purple': '0 4px 0 #BA55D3',
        '3d-cream': '0 4px 0 #F5EFE6',
        'card-kawaii': '0 6px 0 #FFB6C1',
      },
      borderRadius: {
        'xl': '16px',
        '2xl': '20px',
        '3xl': '28px',
      },
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'bounce-soft': 'bounce-soft 2s ease-in-out infinite',
        'pulse-soft': 'pulse-soft 2s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        'bounce-soft': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        }
      }
    },
  },
  plugins: [],
}
