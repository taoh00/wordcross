#!/usr/bin/env python3
"""
生成样例关卡数据 - 用于快速测试和审核

每个分类只生成少量关卡作为示例
"""
import os
import sys
import json
import random
import time
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from puzzle_generator import CrosswordGenerator, CrosswordPuzzle, Word, PlacedWord


# 简化的关卡配置 - 每个网格大小只生成2关
SAMPLE_LEVEL_CONFIG = {
    "primary": {  # 小学样例
        "4x4": 2,
        "5x5": 2,
        "6x6": 2,
        "7x7": 2,
        "8x8": 2,
    },
    "other": {  # 其他词库样例
        "4x4": 2,
        "5x5": 2,
        "6x6": 2,
        "7x7": 2,
        "8x8": 2,
        "9x9": 2,
        "10x10": 2,
    }
}


# 词库映射 - 只生成部分分类
SAMPLE_VOCABULARY = {
    # 小学 - 只生成2个年级
    "grade3_1": {"book_id": "PEPXiaoXue3_1", "name": "三年级上册", "category": "04_人教版小学"},
    "grade4_1": {"book_id": "PEPXiaoXue4_1", "name": "四年级上册", "category": "04_人教版小学"},
    # 考试类
    "cet4": {"book_id": "CET4_3", "name": "大学四级", "category": "01_考试类"},
    # 出国
    "ielts": {"book_id": "IELTS_3", "name": "雅思词汇", "category": "11_新东方扩展"},
}


def load_vocabulary(book_id: str, category: str, data_dir: Path) -> List[Dict]:
    """加载词库文件"""
    vocab_file = data_dir / "words" / category / f"{book_id}.json"
    if not vocab_file.exists():
        print(f"警告: 词库文件不存在 {vocab_file}")
        return []
    
    with open(vocab_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    words = []
    for w in data.get("words", []):
        word = w.get("word", "").strip().upper()
        if not word or len(word) < 2 or len(word) > 10:
            continue
        if not word.isalpha():
            continue
        
        trans_list = w.get("trans", [])
        definition = ""
        if trans_list:
            t = trans_list[0]
            pos = t.get("pos", "")
            tranCn = t.get("tranCn", "")
            definition = f"{pos} {tranCn}".strip() if pos else tranCn
        
        words.append({
            "word": word,
            "definition": definition or "无释义",
            "phonetic": w.get("usphone", "") or w.get("ukphone", ""),
        })
    
    return words


def generate_level(generator: CrosswordGenerator, words: List[Dict], grid_size: int, 
                   level_num: int, max_attempts: int = 5) -> Optional[Dict]:
    """生成单个关卡"""
    for attempt in range(max_attempts):
        try:
            # 根据网格大小过滤词汇
            min_len = max(2, grid_size - 2)
            max_len = min(grid_size, 8)
            
            filtered_words = [w for w in words if min_len <= len(w["word"]) <= max_len]
            if len(filtered_words) < 8:
                filtered_words = [w for w in words if 2 <= len(w["word"]) <= grid_size]
            
            if len(filtered_words) < 4:
                print(f"      词汇不足: {len(filtered_words)}")
                return None
            
            # 随机打乱
            random.shuffle(filtered_words)
            
            # 准备词汇数据（dict格式，方法内部会转换为Word对象）
            word_dicts = []
            for i, w in enumerate(filtered_words[:50]):
                word_dicts.append({
                    "id": i + 1,
                    "word": w["word"],
                    "definition": w["definition"],
                    "difficulty": 1
                })
            
            # 目标单词数
            target_words = min(grid_size, 6) + random.randint(1, 3)
            
            # 生成谜题
            puzzle = generator._generate_puzzle_with_crossable_words(grid_size, word_dicts, target_words)
            
            if puzzle and len(puzzle.placed_words) >= 3:
                # 添加预填字母
                generator._add_prefilled_letters(puzzle, "medium", 0.0)
                
                # 转换为关卡数据格式
                level_data = convert_puzzle_to_level(puzzle, level_num, grid_size, words)
                if level_data and level_data.get("word_count", 0) >= 3:
                    return level_data
                
        except Exception as e:
            import traceback
            print(f"      尝试{attempt+1}异常: {e}")
            traceback.print_exc()
            continue
    
    return None


def convert_puzzle_to_level(puzzle: CrosswordPuzzle, level_num: int, grid_size: int, 
                           vocab_lookup: List[Dict]) -> Dict:
    """将谜题转换为关卡数据格式"""
    # 构建cells矩阵
    cells = [[None for _ in range(grid_size)] for _ in range(grid_size)]
    for r in range(grid_size):
        for c in range(grid_size):
            if puzzle.grid[r][c]:
                cells[r][c] = puzzle.grid[r][c]
    
    # 计算线索编号
    clue_numbers = [[0] * grid_size for _ in range(grid_size)]
    word_starts = set()
    for pw in puzzle.placed_words:
        word_starts.add((pw.row, pw.col))
    
    sorted_starts = sorted(word_starts, key=lambda x: (x[0], x[1]))
    clue_counter = 1
    position_to_clue = {}
    for row, col in sorted_starts:
        clue_numbers[row][col] = clue_counter
        position_to_clue[(row, col)] = clue_counter
        clue_counter += 1
    
    # 构建单词列表
    all_words = []
    word_id = 1
    for pw in puzzle.placed_words:
        # 查找释义
        definition = pw.word.definition
        if not definition:
            # 从词库查找
            for v in vocab_lookup:
                if v["word"] == pw.word.text.upper():
                    definition = v["definition"]
                    break
        
        all_words.append({
            "id": word_id,
            "word": pw.word.text.upper(),
            "definition": definition or "无释义",
            "direction": pw.direction,
            "start_row": pw.row,
            "start_col": pw.col,
            "length": len(pw.word.text),
            "clue_number": position_to_clue.get((pw.row, pw.col), word_id),
            "alternatives": []
        })
        word_id += 1
    
    # 预填字母
    prefilled = dict(puzzle.prefilled) if puzzle.prefilled else {}
    
    # 计算密度
    filled = sum(1 for r in range(grid_size) for c in range(grid_size) if puzzle.grid[r][c])
    total = grid_size * grid_size
    density = filled / total if total > 0 else 0
    
    return {
        "level": level_num,
        "grid_size": grid_size,
        "cells": cells,
        "words": all_words,
        "prefilled": prefilled,
        "clue_numbers": clue_numbers,
        "density": density,
        "word_count": len(all_words),
        "layout_type": "sparse"
    }


def main():
    print("=" * 60)
    print("样例关卡数据生成器")
    print("=" * 60)
    
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    output_dir = project_root / "src" / "frontend" / "public" / "data" / "levels"
    test_output_dir = project_root / "data" / "test_levels"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    test_output_dir.mkdir(parents=True, exist_ok=True)
    
    generator = CrosswordGenerator()
    
    all_data = {}
    
    for group_code, vocab_info in SAMPLE_VOCABULARY.items():
        print(f"\n生成 {group_code} ({vocab_info['name']})...")
        
        words = load_vocabulary(vocab_info["book_id"], vocab_info["category"], data_dir)
        if not words:
            print(f"  无可用单词，跳过")
            continue
        
        print(f"  加载了 {len(words)} 个单词")
        
        is_primary = group_code.startswith("grade")
        config = SAMPLE_LEVEL_CONFIG["primary"] if is_primary else SAMPLE_LEVEL_CONFIG["other"]
        
        levels = []
        level_num = 1
        
        for grid_key, count in config.items():
            # 解析网格大小，如 "4x4" -> 4
            grid_size = int(grid_key.split("x")[0])
            print(f"  生成 {grid_key} 网格 {count} 关...")
            
            for i in range(count):
                level = generate_level(generator, words, grid_size, level_num)
                if level:
                    levels.append(level)
                    print(f"    关卡 {level_num} 完成")
                else:
                    print(f"    关卡 {level_num} 失败")
                level_num += 1
        
        result = {
            "name": vocab_info["name"],
            "group_code": group_code,
            "level_count": len(levels),
            "word_count": len(words),
            "levels": levels
        }
        
        all_data[group_code] = result
        
        # 保存测试版（含答案）
        test_file = test_output_dir / f"{group_code}_with_answers.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  测试版保存到 {test_file}")
    
    # 保存后端数据
    backend_file = project_root / "src" / "data" / "primary_campaign_levels.json"
    backend_file.parent.mkdir(parents=True, exist_ok=True)
    
    primary_data = {k: v for k, v in all_data.items() if k.startswith("grade")}
    with open(backend_file, 'w', encoding='utf-8') as f:
        json.dump(primary_data, f, ensure_ascii=False, indent=2)
    print(f"\n后端数据保存到 {backend_file}")
    
    # 生成索引
    index_data = {
        "version": "1.0",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "note": "样例数据，仅供测试",
        "categories": {}
    }
    
    for code, data in all_data.items():
        index_data["categories"][code] = {
            "name": data["name"],
            "level_count": data["level_count"],
            "word_count": data["word_count"]
        }
    
    index_file = test_output_dir / "index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("样例生成完成!")
    print(f"总分类: {len(all_data)}")
    print(f"总关卡: {sum(d['level_count'] for d in all_data.values())}")
    print("=" * 60)
    print(f"\n测试版数据位置: {test_output_dir}")


if __name__ == "__main__":
    main()
