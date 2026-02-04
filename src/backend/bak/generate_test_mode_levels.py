#!/usr/bin/env python3
"""
生成20关测试模式关卡
- 验证单词与矩阵匹配
- 确保随机性（每次生成不同）
- 以答案形式展示所有关卡内容
"""

import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from puzzle_generator import CrosswordGenerator
from csp_puzzle_generator import CSPPuzzleGenerator
from vocabulary import VocabularyManager


def extract_word_from_grid(cells: List[List], word_info: dict) -> str:
    """从网格中提取单词"""
    word = ""
    direction = word_info.get("direction", "")
    start_row = word_info.get("start_row", 0)
    start_col = word_info.get("start_col", 0)
    length = word_info.get("length", 0)
    grid_size = len(cells)
    
    for i in range(length):
        if direction == "across":
            r, c = start_row, start_col + i
        else:
            r, c = start_row + i, start_col
        
        if 0 <= r < grid_size and 0 <= c < grid_size:
            cell = cells[r][c]
            if cell is not None and cell != "":
                word += cell
            else:
                word += "?"  # 空格子用?表示
        else:
            word += "X"  # 超出边界用X表示
    
    return word


def validate_puzzle_thoroughly(puzzle: dict, answer_grid: List[List] = None) -> Tuple[bool, List[str]]:
    """
    彻底验证谜题
    
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    grid_size = puzzle.get("grid_size", 0)
    cells = puzzle.get("cells", [])
    words = puzzle.get("words", [])
    
    # 如果提供了答案网格，使用它来验证
    if answer_grid:
        grid_to_check = answer_grid
    else:
        grid_to_check = cells
    
    for word_info in words:
        word = word_info.get("word", "")
        direction = word_info.get("direction", "")
        start_row = word_info.get("start_row", 0)
        start_col = word_info.get("start_col", 0)
        length = word_info.get("length", 0)
        clue_num = word_info.get("clue_number", "?")
        
        # 1. 检查声明的长度与实际单词长度是否匹配
        if length != len(word):
            errors.append(f"单词{clue_num}({word}): 声明长度{length} != 实际长度{len(word)}")
        
        # 2. 检查边界
        if direction == "across":
            end_col = start_col + len(word)
            if end_col > grid_size:
                errors.append(f"单词{clue_num}({word}): 横向起始{start_col}+长度{len(word)}={end_col} > 网格大小{grid_size}")
        else:  # down
            end_row = start_row + len(word)
            if end_row > grid_size:
                errors.append(f"单词{clue_num}({word}): 纵向起始{start_row}+长度{len(word)}={end_row} > 网格大小{grid_size}")
        
        # 3. 统计实际可用格子数
        actual_cells = 0
        for i in range(len(word)):
            if direction == "across":
                r, c = start_row, start_col + i
            else:
                r, c = start_row + i, start_col
            
            if 0 <= r < grid_size and 0 <= c < grid_size:
                if cells[r][c] is not None:  # None表示黑格
                    actual_cells += 1
        
        if actual_cells != len(word):
            errors.append(f"单词{clue_num}({word}): 需要{len(word)}个格子但只有{actual_cells}个可用格子")
    
    return len(errors) == 0, errors


def display_puzzle_with_answer(puzzle: dict, level_num: int) -> str:
    """以答案形式展示关卡"""
    output_lines = []
    output_lines.append(f"\n{'='*60}")
    output_lines.append(f"关卡 {level_num}")
    output_lines.append(f"{'='*60}")
    
    grid_size = puzzle.get("grid_size", 0)
    words = puzzle.get("words", [])
    cells = puzzle.get("cells", [])
    revealed = puzzle.get("revealed", [])
    layout_type = puzzle.get("layout_type", "sparse")
    density = puzzle.get("density", 0)
    cross_validated = puzzle.get("cross_validated", False)
    
    output_lines.append(f"网格大小: {grid_size}x{grid_size}")
    output_lines.append(f"布局类型: {layout_type}")
    output_lines.append(f"单词数量: {len(words)}")
    output_lines.append(f"密度: {density:.1%}" if density else "密度: N/A")
    output_lines.append(f"交叉验证: {'是' if cross_validated else '否'}")
    
    # 构建答案网格（将空格子替换为对应字母）
    answer_grid = [row[:] for row in cells]  # 深拷贝
    for word_info in words:
        word = word_info.get("word", "")
        direction = word_info.get("direction", "")
        start_row = word_info.get("start_row", 0)
        start_col = word_info.get("start_col", 0)
        
        for i, letter in enumerate(word):
            if direction == "across":
                r, c = start_row, start_col + i
            else:
                r, c = start_row + i, start_col
            
            if 0 <= r < grid_size and 0 <= c < grid_size:
                answer_grid[r][c] = letter
    
    # 显示答案网格（展示的字母用[]标记）
    output_lines.append("\n答案网格 ([]表示展示的字母/红色):")
    header = "    " + " ".join(f"{i:2}" for i in range(grid_size))
    output_lines.append(header)
    output_lines.append("    " + "-" * (grid_size * 3))
    for i, row in enumerate(answer_grid):
        row_str = f"{i:2} |"
        for j, cell in enumerate(row):
            if cell is None:
                row_str += " █ "
            elif cell == "":
                row_str += " . "
            else:
                # 检查是否是展示的字母
                is_revealed = False
                if revealed and i < len(revealed) and j < len(revealed[i]):
                    is_revealed = revealed[i][j]
                if is_revealed:
                    row_str += f"[{cell}]"  # 展示的字母
                else:
                    row_str += f" {cell} "
        output_lines.append(row_str)
    
    # 显示单词列表
    across_words = [w for w in words if w["direction"] == "across"]
    down_words = [w for w in words if w["direction"] == "down"]
    
    output_lines.append(f"\n横向单词 ({len(across_words)}个):")
    for w in sorted(across_words, key=lambda x: x.get("clue_number", 0)):
        clue_num = w.get("clue_number", "?")
        output_lines.append(f"  {clue_num}. {w['word']} ({len(w['word'])}字母, 位置:{w['start_row']},{w['start_col']}) - {w.get('definition', '')}")
    
    output_lines.append(f"\n纵向单词 ({len(down_words)}个):")
    for w in sorted(down_words, key=lambda x: x.get("clue_number", 0)):
        clue_num = w.get("clue_number", "?")
        output_lines.append(f"  {clue_num}. {w['word']} ({len(w['word'])}字母, 位置:{w['start_row']},{w['start_col']}) - {w.get('definition', '')}")
    
    # 验证
    is_valid, errors = validate_puzzle_thoroughly(puzzle, answer_grid)
    if is_valid:
        output_lines.append("\n验证结果: ✓ 通过")
    else:
        output_lines.append("\n验证结果: ✗ 失败")
        for err in errors:
            output_lines.append(f"  - {err}")
    
    return "\n".join(output_lines), answer_grid


def generate_20_test_levels(group: str = "primary") -> Tuple[List[dict], str]:
    """
    生成20个测试关卡
    
    Returns:
        (levels_list, display_output)
    """
    print("=" * 60)
    print("生成20关测试模式关卡")
    print("=" * 60)
    print(f"词库: {group}")
    print("=" * 60)
    
    # 初始化
    vocab_manager = VocabularyManager()
    
    # 检查词库
    words = vocab_manager.get_words(group, limit=100)
    if not words:
        print(f"错误: 词库 '{group}' 没有词汇!")
        return [], ""
    print(f"词库加载成功: {len(vocab_manager._vocabulary_cache.get(group, []))} 个单词")
    
    all_levels = []
    all_output = []
    word_sets = []  # 用于检查随机性
    
    # 生成20关
    for level in range(1, 21):
        # 每次生成前重新设置随机种子，确保不同
        seed = int(time.time() * 1000000) % (2**31) + level * 12345
        
        if level <= 10:
            # 前10关使用稀疏布局
            generator = CrosswordGenerator(random_seed=seed)
            puzzle = generator.generate_campaign_level(level, group, vocab_manager)
            puzzle["layout_type"] = "sparse"
        else:
            # 后10关使用密集布局
            generator = CSPPuzzleGenerator(random_seed=seed)
            puzzle = generator.generate_campaign_level(level, group, vocab_manager)
            if not puzzle.get("error"):
                puzzle["layout_type"] = "dense"
        
        puzzle["level"] = level
        
        # 检查是否生成成功
        if puzzle.get("error") or len(puzzle.get("words", [])) == 0:
            puzzle = {
                "level": level,
                "error": True,
                "message": "生成失败",
                "grid_size": 5,
                "cells": [[None]*5 for _ in range(5)],
                "words": []
            }
        
        all_levels.append(puzzle)
        
        # 收集单词集合用于随机性检查
        word_set = frozenset(w["word"] for w in puzzle.get("words", []))
        word_sets.append(word_set)
        
        # 生成展示输出
        output, _ = display_puzzle_with_answer(puzzle, level)
        all_output.append(output)
        print(f"关卡 {level}: {'成功' if not puzzle.get('error') else '失败'}")
    
    # 检查随机性
    print("\n" + "=" * 60)
    print("随机性分析")
    print("=" * 60)
    
    unique_sets = len(set(word_sets))
    print(f"20关中有 {unique_sets} 个不同的单词组合")
    
    if unique_sets < 15:
        print("警告: 随机性不足，可能存在重复关卡")
    else:
        print("随机性检查: ✓ 通过")
    
    # 统计重复
    from collections import Counter
    set_counts = Counter(word_sets)
    duplicates = {s: c for s, c in set_counts.items() if c > 1}
    if duplicates:
        print(f"\n重复的单词组合:")
        for word_set, count in duplicates.items():
            print(f"  {list(word_set)}: 出现 {count} 次")
    
    # 验证总结
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    
    valid_count = 0
    invalid_levels = []
    for i, puzzle in enumerate(all_levels):
        if not puzzle.get("error"):
            is_valid, errors = validate_puzzle_thoroughly(puzzle)
            if is_valid:
                valid_count += 1
            else:
                invalid_levels.append((i+1, errors))
    
    print(f"有效关卡: {valid_count}/20")
    if invalid_levels:
        print("\n无效关卡详情:")
        for lvl, errors in invalid_levels:
            print(f"  关卡 {lvl}:")
            for err in errors:
                print(f"    - {err}")
    
    full_output = "\n".join(all_output)
    
    return all_levels, full_output


def save_test_mode_data(levels: List[dict], output_text: str):
    """保存测试模式数据"""
    # 保存JSON数据
    output_path = Path(__file__).parent.parent / "data" / "test_mode_levels.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(levels, f, ensure_ascii=False, indent=2)
    print(f"\n关卡数据已保存到: {output_path}")
    
    # 保存详细展示文本
    text_path = Path(__file__).parent.parent / "data" / "test_mode_answers.txt"
    with open(text_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("测试模式 - 20关答案展示\n")
        f.write("=" * 60 + "\n")
        f.write(output_text)
    print(f"答案展示已保存到: {text_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="生成20关测试模式关卡")
    parser.add_argument("--group", default="primary", help="词库组别 (默认: primary)")
    
    args = parser.parse_args()
    
    levels, output = generate_20_test_levels(args.group)
    save_test_mode_data(levels, output)
    
    # 打印详细输出
    print(output)
