#!/usr/bin/env python3
"""
填单词游戏图标生成器
生成iOS App图标和微信小程序图标
"""

from PIL import Image, ImageDraw, ImageFont
import os
import math

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 颜色配置（与app.json中的splash背景色一致）
COLORS = {
    'primary': '#4F46E5',       # 主色调-靛蓝色
    'primary_dark': '#3730A3',  # 深色
    'primary_light': '#818CF8', # 浅色
    'accent': '#F59E0B',        # 强调色-琥珀色
    'white': '#FFFFFF',
    'grid_bg': '#EEF2FF',       # 网格背景
    'grid_filled': '#4F46E5',   # 填充格子
    'grid_empty': '#FFFFFF',    # 空格子
    'text_dark': '#1E1B4B',     # 深色文字
}

def hex_to_rgb(hex_color):
    """将十六进制颜色转换为RGB元组"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_rounded_rectangle(size, radius, color):
    """创建圆角矩形"""
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制圆角矩形
    x0, y0 = 0, 0
    x1, y1 = size[0], size[1]
    
    draw.rounded_rectangle(
        [(x0, y0), (x1, y1)],
        radius=radius,
        fill=hex_to_rgb(color)
    )
    
    return img

def draw_crossword_grid(draw, x, y, cell_size, grid_data, colors):
    """
    绘制填字游戏网格
    grid_data: 2D列表, None表示空位, 字母表示填充
    """
    rows = len(grid_data)
    cols = len(grid_data[0]) if rows > 0 else 0
    
    corner_radius = cell_size // 6
    
    for row in range(rows):
        for col in range(cols):
            cell_x = x + col * cell_size
            cell_y = y + row * cell_size
            cell_value = grid_data[row][col]
            
            if cell_value is None:
                # 空位 - 不绘制或绘制浅色背景
                continue
            
            # 绘制格子背景
            if cell_value == '':
                # 空白格子（待填）
                fill_color = hex_to_rgb(colors['grid_empty'])
                draw.rounded_rectangle(
                    [(cell_x + 2, cell_y + 2), (cell_x + cell_size - 2, cell_y + cell_size - 2)],
                    radius=corner_radius,
                    fill=fill_color,
                    outline=hex_to_rgb(colors['primary_light']),
                    width=2
                )
            else:
                # 已填充格子
                fill_color = hex_to_rgb(colors['grid_filled'])
                draw.rounded_rectangle(
                    [(cell_x + 2, cell_y + 2), (cell_x + cell_size - 2, cell_y + cell_size - 2)],
                    radius=corner_radius,
                    fill=fill_color
                )
                
                # 绘制字母
                try:
                    font_size = int(cell_size * 0.6)
                    font = ImageFont.truetype("/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                
                # 获取文字边界框
                bbox = draw.textbbox((0, 0), cell_value, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                text_x = cell_x + (cell_size - text_width) // 2
                text_y = cell_y + (cell_size - text_height) // 2 - bbox[1]
                
                draw.text((text_x, text_y), cell_value, fill=hex_to_rgb(colors['white']), font=font)

def create_app_icon(size=1024):
    """
    创建应用图标
    展示填字游戏的核心玩法：字母交叉填充
    """
    # 创建画布
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制圆角背景（iOS图标标准）
    corner_radius = size // 5  # iOS图标圆角
    draw.rounded_rectangle(
        [(0, 0), (size, size)],
        radius=corner_radius,
        fill=hex_to_rgb(COLORS['primary'])
    )
    
    # 添加渐变效果 - 使用叠加层
    for i in range(size // 3):
        alpha = int(30 * (1 - i / (size // 3)))
        overlay_color = (*hex_to_rgb(COLORS['primary_light']), alpha)
        draw.ellipse(
            [(-size // 2, -size // 2 - i * 2), (size // 2, size // 2 - i * 2)],
            fill=None,
            outline=overlay_color,
            width=3
        )
    
    # 重新创建draw对象
    draw = ImageDraw.Draw(img)
    
    # 定义填字网格数据 - 展示 "WORD" 和 "FUN" 交叉
    # None = 透明, '' = 空白格, 字母 = 已填充
    grid_data = [
        [None, 'W', None, None],
        ['F', 'O', 'R', 'D'],
        [None, 'R', None, None],
        [None, 'D', None, None],
    ]
    
    # 计算网格位置和大小
    grid_rows = len(grid_data)
    grid_cols = len(grid_data[0])
    
    # 格子大小
    cell_size = size // 6
    
    # 网格整体居中
    grid_width = grid_cols * cell_size
    grid_height = grid_rows * cell_size
    grid_x = (size - grid_width) // 2
    grid_y = (size - grid_height) // 2
    
    # 绘制网格
    draw_crossword_grid(draw, grid_x, grid_y, cell_size, grid_data, COLORS)
    
    # 添加装饰星星/光点
    star_positions = [
        (size * 0.15, size * 0.15, 15),
        (size * 0.85, size * 0.2, 12),
        (size * 0.1, size * 0.8, 10),
        (size * 0.9, size * 0.85, 14),
    ]
    
    for sx, sy, sr in star_positions:
        sr = int(sr * size / 512)  # 根据尺寸缩放
        draw.ellipse(
            [(sx - sr, sy - sr), (sx + sr, sy + sr)],
            fill=hex_to_rgb(COLORS['accent'])
        )
    
    return img

def create_splash_screen(width=1242, height=2688):
    """创建启动画面"""
    img = Image.new('RGBA', (width, height), hex_to_rgb(COLORS['primary']))
    draw = ImageDraw.Draw(img)
    
    # 添加渐变背景效果
    for y in range(height):
        progress = y / height
        # 从primary渐变到primary_dark
        r1, g1, b1 = hex_to_rgb(COLORS['primary'])
        r2, g2, b2 = hex_to_rgb(COLORS['primary_dark'])
        r = int(r1 + (r2 - r1) * progress)
        g = int(g1 + (g2 - g1) * progress)
        b = int(b1 + (b2 - b1) * progress)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # 重新创建draw
    draw = ImageDraw.Draw(img)
    
    # 在中央放置一个较大的图标样式网格
    grid_data = [
        [None, 'W', None, None, None],
        ['F', 'O', 'R', 'D', None],
        [None, 'R', None, None, None],
        [None, 'D', None, None, None],
    ]
    
    cell_size = width // 8
    grid_rows = len(grid_data)
    grid_cols = len(grid_data[0])
    grid_width = grid_cols * cell_size
    grid_height = grid_rows * cell_size
    grid_x = (width - grid_width) // 2
    grid_y = (height - grid_height) // 2 - height // 6
    
    draw_crossword_grid(draw, grid_x, grid_y, cell_size, grid_data, COLORS)
    
    # 添加应用名称
    try:
        font_size = width // 8
        font = ImageFont.truetype("/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    title = "填单词"
    bbox = draw.textbbox((0, 0), title, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    text_y = grid_y + grid_height + height // 10
    
    draw.text((text_x, text_y), title, fill=hex_to_rgb(COLORS['white']), font=font)
    
    # 副标题
    try:
        sub_font_size = width // 20
        sub_font = ImageFont.truetype("/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf", sub_font_size)
    except:
        sub_font = ImageFont.load_default()
    
    subtitle = "边玩边学 · 单词记忆神器"
    bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    text_y = text_y + font_size + height // 30
    
    draw.text((text_x, text_y), subtitle, fill=hex_to_rgb(COLORS['primary_light']), font=sub_font)
    
    return img

def generate_ios_icons():
    """生成iOS所需的所有图标尺寸"""
    ios_sizes = [
        (1024, 'icon.png'),           # App Store
        (180, 'icon-60@3x.png'),      # iPhone @3x
        (120, 'icon-60@2x.png'),      # iPhone @2x
        (167, 'icon-83.5@2x.png'),    # iPad Pro
        (152, 'icon-76@2x.png'),      # iPad @2x
        (76, 'icon-76.png'),          # iPad
    ]
    
    output_dir = os.path.join(PROJECT_ROOT, 'src/ios-app/assets/images')
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成主图标
    icon = create_app_icon(1024)
    
    for size, filename in ios_sizes:
        resized = icon.resize((size, size), Image.Resampling.LANCZOS)
        filepath = os.path.join(output_dir, filename)
        resized.save(filepath, 'PNG')
        print(f"✓ 生成 iOS 图标: {filename} ({size}x{size})")
    
    # 生成adaptive icon（Android）
    adaptive = create_app_icon(1024)
    adaptive.save(os.path.join(output_dir, 'adaptive-icon.png'), 'PNG')
    print("✓ 生成 Android adaptive-icon.png")
    
    # 生成启动画面
    splash = create_splash_screen()
    splash.save(os.path.join(output_dir, 'splash.png'), 'PNG')
    print("✓ 生成启动画面: splash.png")
    
    return output_dir

def generate_wechat_icons():
    """生成微信小程序所需的图标"""
    # 微信小程序图标尺寸
    wechat_sizes = [
        (1024, 'icon-1024.png'),    # 提审用
        (512, 'icon-512.png'),
        (256, 'icon-256.png'),
        (144, 'icon-144.png'),
        (128, 'icon-128.png'),
        (64, 'icon-64.png'),
    ]
    
    output_dir = os.path.join(PROJECT_ROOT, 'src/wechat-minigame/images')
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成图标（微信小程序图标通常需要正方形无圆角）
    icon = create_app_icon(1024)
    
    for size, filename in wechat_sizes:
        resized = icon.resize((size, size), Image.Resampling.LANCZOS)
        filepath = os.path.join(output_dir, filename)
        resized.save(filepath, 'PNG')
        print(f"✓ 生成微信小程序图标: {filename} ({size}x{size})")
    
    # 生成tabbar图标（如果需要）
    tabbar_icons = [
        ('tabbar-home.png', 'H'),
        ('tabbar-game.png', 'G'),
        ('tabbar-settings.png', 'S'),
    ]
    
    for filename, letter in tabbar_icons:
        tab_icon = create_tabbar_icon(64, letter)
        tab_icon.save(os.path.join(output_dir, filename), 'PNG')
        print(f"✓ 生成 tabbar 图标: {filename}")
    
    return output_dir

def create_tabbar_icon(size, letter):
    """创建tabbar图标"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制圆形背景
    padding = size // 8
    draw.ellipse(
        [(padding, padding), (size - padding, size - padding)],
        fill=hex_to_rgb(COLORS['primary'])
    )
    
    # 绘制字母
    try:
        font_size = size // 2
        font = ImageFont.truetype("/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), letter, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2 - bbox[1]
    
    draw.text((text_x, text_y), letter, fill=hex_to_rgb(COLORS['white']), font=font)
    
    return img

def main():
    print("=" * 50)
    print("填单词游戏图标生成器")
    print("=" * 50)
    print()
    
    print("[1/2] 生成 iOS/Android 图标...")
    ios_dir = generate_ios_icons()
    print(f"    → 输出目录: {ios_dir}")
    print()
    
    print("[2/2] 生成微信小程序图标...")
    wechat_dir = generate_wechat_icons()
    print(f"    → 输出目录: {wechat_dir}")
    print()
    
    print("=" * 50)
    print("✅ 所有图标生成完成!")
    print("=" * 50)

if __name__ == '__main__':
    main()
