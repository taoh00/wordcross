#!/usr/bin/env python3
"""
生成静态关卡数据文件 - 随前端分发

根据设计简报生成各分类的闯关关卡数据：
- 4×4: 9关
- 5×5: 18关  
- 6×6: 18关
- 7×7: 18关
- 8×8: 小学54关，其他18关
- 9×9: 18关（小学无）
- 10×10: 81关（小学无）

小学总共117关，其他词库180关
"""
import os
import sys
import json
import random
import time
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from csp_puzzle_generator import CSPPuzzleGenerator


# 关卡配置
LEVEL_CONFIG = {
    "primary": {  # 小学 - 117关
        "4x4": 9,
        "5x5": 18,
        "6x6": 18,
        "7x7": 18,
        "8x8": 54,  # 小学8x8有54关作为终极挑战
        # 小学没有9x9和10x10
    },
    "other": {  # 其他词库 - 180关
        "4x4": 9,
        "5x5": 18,
        "6x6": 18,
        "7x7": 18,
        "8x8": 18,
        "9x9": 18,
        "10x10": 81,
    }
}


# 词库分类映射
VOCABULARY_MAPPING = {
    # 小学（人教版PEP）
    "primary": {
        "grade3_1": {"book_id": "PEPXiaoXue3_1", "name": "三年级上册", "category": "04_人教版小学"},
        "grade3_2": {"book_id": "PEPXiaoXue3_2", "name": "三年级下册", "category": "04_人教版小学"},
        "grade4_1": {"book_id": "PEPXiaoXue4_1", "name": "四年级上册", "category": "04_人教版小学"},
        "grade4_2": {"book_id": "PEPXiaoXue4_2", "name": "四年级下册", "category": "04_人教版小学"},
        "grade5_1": {"book_id": "PEPXiaoXue5_1", "name": "五年级上册", "category": "04_人教版小学"},
        "grade5_2": {"book_id": "PEPXiaoXue5_2", "name": "五年级下册", "category": "04_人教版小学"},
        "grade6_1": {"book_id": "PEPXiaoXue6_1", "name": "六年级上册", "category": "04_人教版小学"},
        "grade6_2": {"book_id": "PEPXiaoXue6_2", "name": "六年级下册", "category": "04_人教版小学"},
    },
    # 初中（人教版）
    "junior": {
        "junior7_1": {"book_id": "PEPChuZhong7_1", "name": "七年级上册", "category": "05_人教版初中"},
        "junior7_2": {"book_id": "PEPChuZhong7_2", "name": "七年级下册", "category": "05_人教版初中"},
        "junior8_1": {"book_id": "PEPChuZhong8_1", "name": "八年级上册", "category": "05_人教版初中"},
        "junior8_2": {"book_id": "PEPChuZhong8_2", "name": "八年级下册", "category": "05_人教版初中"},
        "junior9": {"book_id": "PEPChuZhong9_1", "name": "九年级全册", "category": "05_人教版初中"},
    },
    # 高中（人教版）
    "senior": {
        "senior1": {"book_id": "PEPGaoZhong_1", "name": "高一必修1", "category": "07_人教版高中"},
        "senior2": {"book_id": "PEPGaoZhong_3", "name": "高二必修3", "category": "07_人教版高中"},
        "senior3": {"book_id": "PEPGaoZhong_5", "name": "高三必修5", "category": "07_人教版高中"},
    },
    # 考试类
    "cet4": {"book_id": "CET4_3", "name": "大学四级", "category": "01_考试类"},
    "cet6": {"book_id": "CET6_3", "name": "大学六级", "category": "01_考试类"},
    "postgrad": {"book_id": "KaoYan_3", "name": "考研词汇", "category": "11_新东方扩展"},
    # 出国留学
    "ielts": {"book_id": "IELTS_3", "name": "雅思词汇", "category": "11_新东方扩展"},
    "toefl": {"book_id": "TOEFL_3", "name": "托福词汇", "category": "11_新东方扩展"},
    "gre": {"book_id": "GRE_3", "name": "GRE词汇", "category": "11_新东方扩展"},
    # 中高考
    "zhongkao": {"book_id": "ChuZhong_3", "name": "中考词汇", "category": "03_中高考"},
    "gaokao": {"book_id": "GaoZhong_3", "name": "高考词汇", "category": "03_中高考"},
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
        # 过滤无效单词
        if not word or len(word) < 2 or len(word) > 10:
            continue
        if not word.isalpha():
            continue
        
        # 获取释义
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


def generate_level(generator: CSPPuzzleGenerator, words: List[Dict], grid_size: int, 
                   level_num: int, max_attempts: int = 5) -> Optional[Dict]:
    """生成单个关卡"""
    for attempt in range(max_attempts):
        try:
            # 根据网格大小过滤单词
            min_len = max(2, grid_size - 3)
            max_len = grid_size
            
            filtered_words = [w for w in words if min_len <= len(w["word"]) <= max_len]
            if len(filtered_words) < 6:
                # 放宽限制
                filtered_words = [w for w in words if 2 <= len(w["word"]) <= grid_size]
            
            if len(filtered_words) < 4:
                print(f"  警告: 关卡{level_num} 可用单词不足")
                return None
            
            # 随机打乱
            random.shuffle(filtered_words)
            
            # 生成谜题
            puzzle = generator.generate_dense_puzzle(
                grid_size=grid_size,
                vocabulary=filtered_words[:100],  # 限制词库大小提高速度
                min_density=0.35,
                timeout=10.0
            )
            
            if puzzle and puzzle.calculate_density() >= 0.35:
                # 计算预填字母
                puzzle.compute_revealed_letters(min_reveal=2)
                
                # 转换为关卡数据格式
                level_data = convert_puzzle_to_level(puzzle, level_num, grid_size)
                return level_data
                
        except Exception as e:
            print(f"  尝试{attempt+1}失败: {e}")
            continue
    
    return None


def convert_puzzle_to_level(puzzle, level_num: int, grid_size: int) -> Dict:
    """将谜题转换为关卡数据格式"""
    # 构建cells矩阵
    cells = [[None for _ in range(grid_size)] for _ in range(grid_size)]
    for r in range(grid_size):
        for c in range(grid_size):
            if puzzle.grid[r][c]:
                cells[r][c] = puzzle.grid[r][c]
    
    # 合并所有单词
    all_words = []
    word_id = 1
    
    # 计算线索编号（填字游戏标准编号）
    clue_numbers = [[0] * grid_size for _ in range(grid_size)]
    clue_counter = 1
    
    # 找出所有单词起始位置
    word_starts = set()
    for word_info in puzzle.row_words:
        word_starts.add((word_info['row'], word_info['col']))
    for word_info in puzzle.col_words:
        word_starts.add((word_info['row'], word_info['col']))
    
    # 按位置排序分配编号
    sorted_starts = sorted(word_starts, key=lambda x: (x[0], x[1]))
    for row, col in sorted_starts:
        clue_numbers[row][col] = clue_counter
        clue_counter += 1
    
    # 处理横向单词
    for word_info in puzzle.row_words:
        row = word_info['row']
        col = word_info['col']
        word = word_info['word']
        definition = word_info.get('definition', '')
        
        all_words.append({
            "id": word_id,
            "word": word.upper(),
            "definition": definition,
            "direction": "across",
            "start_row": row,
            "start_col": col,
            "length": len(word),
            "clue_number": clue_numbers[row][col],
            "alternatives": []  # 备选答案，可后续扩展
        })
        word_id += 1
    
    # 处理纵向单词
    for word_info in puzzle.col_words:
        row = word_info['row']
        col = word_info['col']
        word = word_info['word']
        definition = word_info.get('definition', '')
        
        all_words.append({
            "id": word_id,
            "word": word.upper(),
            "definition": definition,
            "direction": "down",
            "start_row": row,
            "start_col": col,
            "length": len(word),
            "clue_number": clue_numbers[row][col],
            "alternatives": []
        })
        word_id += 1
    
    # 构建预填字母（prefilled）
    prefilled = {}
    for (r, c) in puzzle.revealed_positions:
        if 0 <= r < grid_size and 0 <= c < grid_size and puzzle.grid[r][c]:
            prefilled[f"{r}-{c}"] = puzzle.grid[r][c]
    
    return {
        "level": level_num,
        "grid_size": grid_size,
        "cells": cells,
        "words": all_words,
        "prefilled": prefilled,
        "clue_numbers": clue_numbers,
        "density": puzzle.calculate_density(),
        "word_count": len(all_words),
        "layout_type": "dense"
    }


def generate_levels_for_group(group_code: str, vocab_info: Dict, data_dir: Path, 
                              generator: CSPPuzzleGenerator, is_primary: bool = False) -> Dict:
    """为单个分组生成所有关卡"""
    print(f"\n正在生成 {group_code} ({vocab_info.get('name', '')}) 的关卡...")
    
    # 加载词库
    if isinstance(vocab_info, dict) and "book_id" in vocab_info:
        words = load_vocabulary(vocab_info["book_id"], vocab_info["category"], data_dir)
    else:
        words = []
    
    if not words:
        print(f"  无可用单词，跳过")
        return {"levels": [], "name": vocab_info.get("name", group_code)}
    
    print(f"  加载了 {len(words)} 个单词")
    
    # 确定关卡配置
    config = LEVEL_CONFIG["primary"] if is_primary else LEVEL_CONFIG["other"]
    
    levels = []
    level_num = 1
    
    for grid_key, count in config.items():
        grid_size = int(grid_key.replace("x", "").split("x")[0])
        print(f"  生成 {grid_key} 网格 {count} 关...")
        
        for i in range(count):
            level = generate_level(generator, words, grid_size, level_num)
            if level:
                levels.append(level)
                if level_num % 10 == 0:
                    print(f"    已完成 {level_num} 关")
            else:
                print(f"    关卡 {level_num} 生成失败")
            level_num += 1
    
    print(f"  共生成 {len(levels)} 关")
    
    return {
        "name": vocab_info.get("name", group_code),
        "group_code": group_code,
        "level_count": len(levels),
        "word_count": len(words),
        "levels": levels
    }


def main():
    """主函数"""
    print("=" * 60)
    print("静态关卡数据生成器")
    print("=" * 60)
    
    # 路径配置
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    output_dir = project_root / "src" / "frontend" / "public" / "data" / "levels"
    test_output_dir = project_root / "data" / "test_levels"
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    test_output_dir.mkdir(parents=True, exist_ok=True)
    
    # 初始化生成器
    generator = CSPPuzzleGenerator()
    
    # 存储所有生成的数据
    all_campaign_data = {}
    
    # 1. 生成小学各年级关卡
    print("\n" + "=" * 40)
    print("生成小学关卡")
    print("=" * 40)
    
    for grade_code, vocab_info in VOCABULARY_MAPPING["primary"].items():
        result = generate_levels_for_group(
            grade_code, vocab_info, data_dir, generator, is_primary=True
        )
        all_campaign_data[grade_code] = result
        
        # 保存单个年级文件
        output_file = output_dir / f"{grade_code}.json"
        # 正式版不含答案
        public_result = create_public_version(result)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(public_result, f, ensure_ascii=False, indent=2)
        print(f"  已保存到 {output_file}")
        
        # 测试版含答案
        test_file = test_output_dir / f"{grade_code}_with_answers.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  测试版保存到 {test_file}")
    
    # 2. 生成其他词库关卡
    print("\n" + "=" * 40)
    print("生成其他词库关卡")
    print("=" * 40)
    
    other_vocabs = {k: v for k, v in VOCABULARY_MAPPING.items() 
                    if k not in ["primary", "junior", "senior"]}
    
    for group_code, vocab_info in other_vocabs.items():
        if isinstance(vocab_info, dict) and "book_id" in vocab_info:
            result = generate_levels_for_group(
                group_code, vocab_info, data_dir, generator, is_primary=False
            )
            all_campaign_data[group_code] = result
            
            # 保存
            output_file = output_dir / f"{group_code}.json"
            public_result = create_public_version(result)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(public_result, f, ensure_ascii=False, indent=2)
            
            test_file = test_output_dir / f"{group_code}_with_answers.json"
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 3. 生成索引文件
    print("\n" + "=" * 40)
    print("生成索引文件")
    print("=" * 40)
    
    index_data = {
        "version": "1.0",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "categories": {
            "primary": {
                "name": "小学词汇",
                "icon": "📚",
                "has_sub_groups": True,
                "sub_groups": [
                    {"code": code, "name": data["name"], "level_count": data["level_count"]}
                    for code, data in all_campaign_data.items()
                    if code.startswith("grade")
                ]
            },
            "exam": {
                "name": "考试类",
                "icon": "🎓",
                "has_sub_groups": True,
                "sub_groups": [
                    {"code": "cet4", "name": "大学四级", "level_count": all_campaign_data.get("cet4", {}).get("level_count", 0)},
                    {"code": "cet6", "name": "大学六级", "level_count": all_campaign_data.get("cet6", {}).get("level_count", 0)},
                    {"code": "postgrad", "name": "考研词汇", "level_count": all_campaign_data.get("postgrad", {}).get("level_count", 0)},
                ]
            },
            "abroad": {
                "name": "出国留学",
                "icon": "✈️",
                "has_sub_groups": True,
                "sub_groups": [
                    {"code": "ielts", "name": "雅思", "level_count": all_campaign_data.get("ielts", {}).get("level_count", 0)},
                    {"code": "toefl", "name": "托福", "level_count": all_campaign_data.get("toefl", {}).get("level_count", 0)},
                    {"code": "gre", "name": "GRE", "level_count": all_campaign_data.get("gre", {}).get("level_count", 0)},
                ]
            }
        },
        "total_levels": sum(d.get("level_count", 0) for d in all_campaign_data.values())
    }
    
    index_file = output_dir / "index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    print(f"索引文件已保存到 {index_file}")
    
    # 4. 保存完整数据到后端
    backend_file = project_root / "src" / "data" / "primary_campaign_levels.json"
    backend_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 只保存小学年级数据到后端
    primary_data = {k: v for k, v in all_campaign_data.items() if k.startswith("grade")}
    with open(backend_file, 'w', encoding='utf-8') as f:
        json.dump(primary_data, f, ensure_ascii=False, indent=2)
    print(f"后端数据已保存到 {backend_file}")
    
    print("\n" + "=" * 60)
    print("生成完成!")
    print(f"总关卡数: {index_data['total_levels']}")
    print("=" * 60)


def create_public_version(data: Dict) -> Dict:
    """创建不含答案的公开版本"""
    public_data = {
        "name": data.get("name"),
        "group_code": data.get("group_code"),
        "level_count": data.get("level_count"),
        "word_count": data.get("word_count"),
        "levels": []
    }
    
    for level in data.get("levels", []):
        public_level = {
            "level": level.get("level"),
            "grid_size": level.get("grid_size"),
            "cells": level.get("cells"),  # 保留cells用于显示网格结构
            "words": [],
            "prefilled": level.get("prefilled"),
            "clue_numbers": level.get("clue_numbers"),
            "word_count": level.get("word_count"),
        }
        
        # 单词信息不含完整答案，只保留必要信息
        for word in level.get("words", []):
            public_word = {
                "id": word.get("id"),
                "word": word.get("word"),  # 保留单词用于验证
                "definition": word.get("definition"),
                "direction": word.get("direction"),
                "start_row": word.get("start_row"),
                "start_col": word.get("start_col"),
                "length": word.get("length"),
                "clue_number": word.get("clue_number"),
                "alternatives": word.get("alternatives", [])
            }
            public_level["words"].append(public_word)
        
        public_data["levels"].append(public_level)
    
    return public_data


if __name__ == "__main__":
    main()
