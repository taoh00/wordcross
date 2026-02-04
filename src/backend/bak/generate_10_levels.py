#!/usr/bin/env python3
"""
生成10关测试关卡
- 关卡1-5：稀疏布局（传统交叉填字）
- 关卡6-10：密集布局（CSP模板填字）
"""

import sys
import json
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from puzzle_generator import CrosswordGenerator
from csp_puzzle_generator import CSPPuzzleGenerator
from vocabulary import VocabularyManager


def display_grid(cells, grid_size):
    """显示网格"""
    print(f"\n  网格 ({grid_size}x{grid_size}):")
    for row in cells:
        row_str = "  "
        for cell in row:
            if cell is None:
                row_str += "█ "  # 黑格
            elif cell == "":
                row_str += "□ "  # 空白待填
            else:
                row_str += f"{cell} "  # 预填字母
        print(row_str)


def display_words(words):
    """显示单词列表"""
    across = [w for w in words if w["direction"] == "across"]
    down = [w for w in words if w["direction"] == "down"]
    
    print(f"\n  横向 ({len(across)}个):")
    for w in sorted(across, key=lambda x: x.get("clue_number", 0)):
        clue_num = w.get("clue_number", "?")
        print(f"    {clue_num}. {w['word']} - {w['definition']}")
    
    print(f"\n  纵向 ({len(down)}个):")
    for w in sorted(down, key=lambda x: x.get("clue_number", 0)):
        clue_num = w.get("clue_number", "?")
        print(f"    {clue_num}. {w['word']} - {w['definition']}")


def generate_10_levels(group: str = "primary"):
    """生成10关"""
    print("=" * 60)
    print("生成10关测试关卡")
    print("=" * 60)
    print(f"词库: {group}")
    print("关卡1-5: 稀疏布局（传统交叉填字）")
    print("关卡6-10: 密集布局（CSP模板填字）")
    print("=" * 60)
    
    # 初始化
    vocab_manager = VocabularyManager()
    sparse_generator = CrosswordGenerator()  # 稀疏布局
    dense_generator = CSPPuzzleGenerator()   # 密集布局
    
    # 检查词库
    words = vocab_manager.get_words(group, limit=100)
    if not words:
        print(f"错误: 词库 '{group}' 没有词汇!")
        return None
    print(f"词库加载成功: {len(vocab_manager._vocabulary_cache.get(group, []))} 个单词")
    
    all_levels = []
    
    # 生成关卡1-5：稀疏布局
    print("\n" + "=" * 60)
    print("生成稀疏布局关卡 (1-5)")
    print("=" * 60)
    
    for level in range(1, 6):
        print(f"\n{'='*40}")
        print(f"关卡 {level} - 稀疏布局")
        print(f"{'='*40}")
        
        puzzle = sparse_generator.generate_campaign_level(level, group, vocab_manager)
        
        if puzzle and len(puzzle.get("words", [])) > 0:
            puzzle["layout_type"] = "sparse"
            all_levels.append(puzzle)
            
            print(f"  生成成功!")
            print(f"  网格大小: {puzzle['grid_size']}x{puzzle['grid_size']}")
            print(f"  单词数量: {len(puzzle['words'])}")
            print(f"  难度: {puzzle.get('difficulty', 'unknown')}")
            
            display_grid(puzzle["cells"], puzzle["grid_size"])
            display_words(puzzle["words"])
            
            # 显示预填字母
            prefilled = puzzle.get("prefilled", {})
            if prefilled:
                print(f"\n  预填字母: {len(prefilled)}个")
        else:
            print(f"  生成失败!")
            all_levels.append({"level": level, "error": True, "layout_type": "sparse"})
    
    # 生成关卡6-10：密集布局
    print("\n" + "=" * 60)
    print("生成密集布局关卡 (6-10)")
    print("=" * 60)
    
    for level in range(6, 11):
        print(f"\n{'='*40}")
        print(f"关卡 {level} - 密集布局")
        print(f"{'='*40}")
        
        # 密集布局使用CSP生成器
        # 调整关卡号来获取适当的难度
        puzzle = dense_generator.generate_campaign_level(level, group, vocab_manager)
        
        if puzzle and not puzzle.get("error"):
            puzzle["layout_type"] = "dense"
            puzzle["level"] = level  # 确保关卡号正确
            all_levels.append(puzzle)
            
            print(f"  生成成功!")
            print(f"  网格大小: {puzzle['grid_size']}x{puzzle['grid_size']}")
            print(f"  单词数量: {len(puzzle['words'])}")
            print(f"  难度: {puzzle.get('difficulty', 'unknown')}")
            
            display_grid(puzzle["cells"], puzzle["grid_size"])
            display_words(puzzle["words"])
        else:
            print(f"  生成失败! {puzzle.get('message', '')}")
            all_levels.append({"level": level, "error": True, "layout_type": "dense"})
    
    # 保存到JSON文件
    output_path = Path(__file__).parent.parent / "data" / "generated_levels.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_levels, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("生成完成!")
    print("=" * 60)
    print(f"成功生成: {len([l for l in all_levels if not l.get('error')])} 关")
    print(f"失败: {len([l for l in all_levels if l.get('error')])} 关")
    print(f"关卡数据已保存到: {output_path}")
    
    return all_levels


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="生成10关测试关卡")
    parser.add_argument("--group", default="primary", help="词库组别 (默认: primary)")
    
    args = parser.parse_args()
    
    generate_10_levels(args.group)
