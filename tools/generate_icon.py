#!/usr/bin/env python3
"""
我爱填单词 - 游戏图标生成器
生成萌萌风格的填字游戏图标
"""

import os
import sys

# SVG 图标模板 - 萌萌风格填字游戏
ICON_SVG = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <!-- 背景渐变 -->
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#a78bfa;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#7c3aed;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="cellGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#ffffff;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#f1f5f9;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#fef3c7;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#fde68a;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="greenGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#6ee7b7;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#34d399;stop-opacity:1" />
    </linearGradient>
    <!-- 阴影效果 -->
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#000" flood-opacity="0.25"/>
    </filter>
  </defs>
  
  <!-- 背景圆角矩形 -->
  <rect x="0" y="0" width="512" height="512" rx="100" ry="100" fill="url(#bgGrad)"/>
  
  <!-- 装饰性圆点 -->
  <circle cx="80" cy="80" r="25" fill="#c4b5fd" opacity="0.5"/>
  <circle cx="432" cy="80" r="18" fill="#c4b5fd" opacity="0.5"/>
  <circle cx="432" cy="432" r="30" fill="#c4b5fd" opacity="0.5"/>
  <circle cx="70" cy="440" r="15" fill="#c4b5fd" opacity="0.5"/>
  
  <!-- 主要游戏格子区域 -->
  <g filter="url(#shadow)" transform="translate(86, 86)">
    <!-- 3x3 网格 -->
    <!-- 第一行 -->
    <rect x="0" y="0" width="100" height="100" rx="16" fill="url(#cellGrad)" stroke="#c7d2fe" stroke-width="4"/>
    <text x="50" y="68" font-family="Arial, sans-serif" font-size="50" font-weight="bold" fill="#5b21b6" text-anchor="middle">L</text>
    
    <rect x="120" y="0" width="100" height="100" rx="16" fill="url(#greenGrad)" stroke="#10b981" stroke-width="4"/>
    <text x="170" y="68" font-family="Arial, sans-serif" font-size="50" font-weight="bold" fill="white" text-anchor="middle">O</text>
    
    <rect x="240" y="0" width="100" height="100" rx="16" fill="url(#cellGrad)" stroke="#c7d2fe" stroke-width="4"/>
    <text x="290" y="68" font-family="Arial, sans-serif" font-size="50" font-weight="bold" fill="#5b21b6" text-anchor="middle">V</text>
    
    <!-- 第二行 -->
    <rect x="0" y="120" width="100" height="100" rx="16" fill="url(#goldGrad)" stroke="#fbbf24" stroke-width="4"/>
    <text x="50" y="188" font-family="Arial, sans-serif" font-size="50" font-weight="bold" fill="#92400e" text-anchor="middle">O</text>
    
    <rect x="120" y="120" width="100" height="100" rx="16" fill="url(#greenGrad)" stroke="#10b981" stroke-width="4"/>
    <text x="170" y="188" font-family="Arial, sans-serif" font-size="50" font-weight="bold" fill="white" text-anchor="middle">R</text>
    
    <rect x="240" y="120" width="100" height="100" rx="16" fill="url(#cellGrad)" stroke="#c7d2fe" stroke-width="4"/>
    <text x="290" y="188" font-family="Arial, sans-serif" font-size="50" font-weight="bold" fill="#5b21b6" text-anchor="middle">E</text>
    
    <!-- 第三行 -->
    <rect x="0" y="240" width="100" height="100" rx="16" fill="url(#cellGrad)" stroke="#c7d2fe" stroke-width="4"/>
    <text x="50" y="308" font-family="Arial, sans-serif" font-size="50" font-weight="bold" fill="#5b21b6" text-anchor="middle">V</text>
    
    <rect x="120" y="240" width="100" height="100" rx="16" fill="url(#greenGrad)" stroke="#10b981" stroke-width="4"/>
    <text x="170" y="308" font-family="Arial, sans-serif" font-size="50" font-weight="bold" fill="white" text-anchor="middle">D</text>
    
    <rect x="240" y="240" width="100" height="100" rx="16" fill="url(#goldGrad)" stroke="#fbbf24" stroke-width="4"/>
    <text x="290" y="308" font-family="Arial, sans-serif" font-size="50" font-weight="bold" fill="#92400e" text-anchor="middle">S</text>
  </g>
  
  <!-- 星星装饰 -->
  <g transform="translate(410, 50)">
    <polygon points="20,0 26,15 42,15 29,24 35,40 20,30 5,40 11,24 -2,15 14,15" fill="#fde68a" stroke="#fbbf24" stroke-width="2"/>
  </g>
  <g transform="translate(50, 390) scale(0.8)">
    <polygon points="20,0 26,15 42,15 29,24 35,40 20,30 5,40 11,24 -2,15 14,15" fill="#fde68a" stroke="#fbbf24" stroke-width="2"/>
  </g>
  
  <!-- 可爱铅笔装饰 -->
  <g transform="translate(380, 380) rotate(-45)">
    <rect x="0" y="0" width="20" height="70" rx="3" fill="#fde68a" stroke="#fbbf24" stroke-width="2"/>
    <rect x="0" y="0" width="20" height="15" rx="3" fill="#fecaca" stroke="#f87171" stroke-width="2"/>
    <polygon points="10,70 0,90 20,90" fill="#374151"/>
    <polygon points="10,85 5,95 15,95" fill="#fef3c7"/>
  </g>
</svg>
'''

def main():
    output_dir = os.path.dirname(os.path.abspath(__file__))
    svg_path = os.path.join(output_dir, 'icon.svg')
    png_path = os.path.join(output_dir, 'icon_512.png')
    
    # 生成 SVG 文件
    print("生成 SVG 图标...")
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(ICON_SVG)
    print(f"SVG 已保存: {svg_path}")
    
    # 尝试转换为 PNG
    try:
        import cairosvg
        print("转换为 PNG...")
        cairosvg.svg2png(
            bytestring=ICON_SVG.encode('utf-8'),
            write_to=png_path,
            output_width=512,
            output_height=512
        )
        print(f"PNG 已保存: {png_path}")
        
        # 生成不同尺寸
        for size in [192, 180, 152, 144, 120, 96, 72, 48]:
            size_path = os.path.join(output_dir, f'icon_{size}.png')
            cairosvg.svg2png(
                bytestring=ICON_SVG.encode('utf-8'),
                write_to=size_path,
                output_width=size,
                output_height=size
            )
            print(f"PNG {size}x{size} 已保存: {size_path}")
            
    except ImportError:
        print("\n提示: 安装 cairosvg 库可自动转换为 PNG:")
        print("pip install cairosvg -i https://pypi.tuna.tsinghua.edu.cn/simple")
        print("\n或者使用在线工具转换 SVG 为 PNG:")
        print("https://svgtopng.com/")
        print("https://cloudconvert.com/svg-to-png")
    
    print("\n完成！")

if __name__ == '__main__':
    main()
