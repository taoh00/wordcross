#!/usr/bin/env python3
"""
生成小学生闯关模式题目

使用人教版小学词汇（三年级到六年级）生成闯关模式的所有关卡。
每个年级生成117关，共936关（8个年级）。

关卡难度按12关一组循环递增：
- 第1-2关：4x4网格，2-3个单词
- 第3-4关：5x5网格，3-4个单词
- 第5-6关：6x6网格，4-5个单词
- 第7-8关：7x7网格，5-6个单词
- 第9-12关：8x8网格，6+个单词
"""
import sys
import os
import json
import random
import time
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

# 添加后端目录到路径
script_dir = Path(__file__).parent
backend_dir = script_dir.parent / "src" / "backend"
sys.path.insert(0, str(backend_dir))


# ==================== 关卡配置 ====================

# 每关的配置模板（12关一组循环）
LEVEL_CONFIG_TEMPLATE = [
    {"grid_size": 4, "min_words": 2, "max_words": 3, "min_len": 2, "max_len": 4},  # 1
    {"grid_size": 4, "min_words": 2, "max_words": 3, "min_len": 2, "max_len": 4},  # 2
    {"grid_size": 5, "min_words": 3, "max_words": 4, "min_len": 3, "max_len": 5},  # 3
    {"grid_size": 5, "min_words": 3, "max_words": 4, "min_len": 3, "max_len": 5},  # 4
    {"grid_size": 6, "min_words": 4, "max_words": 5, "min_len": 3, "max_len": 6},  # 5
    {"grid_size": 6, "min_words": 4, "max_words": 5, "min_len": 3, "max_len": 6},  # 6
    {"grid_size": 7, "min_words": 5, "max_words": 6, "min_len": 3, "max_len": 7},  # 7
    {"grid_size": 7, "min_words": 5, "max_words": 6, "min_len": 3, "max_len": 7},  # 8
    {"grid_size": 8, "min_words": 6, "max_words": 8, "min_len": 3, "max_len": 8},  # 9
    {"grid_size": 8, "min_words": 6, "max_words": 8, "min_len": 3, "max_len": 8},  # 10
    {"grid_size": 8, "min_words": 6, "max_words": 8, "min_len": 3, "max_len": 8},  # 11
    {"grid_size": 8, "min_words": 6, "max_words": 8, "min_len": 3, "max_len": 8},  # 12
]

LEVELS_PER_GRADE = 117  # 每个年级的关卡数

def get_level_config(level_num: int) -> dict:
    """获取指定关卡的配置（循环使用模板）"""
    idx = (level_num - 1) % len(LEVEL_CONFIG_TEMPLATE)
    return LEVEL_CONFIG_TEMPLATE[idx].copy()

# 词汇文件映射
VOCAB_FILES = {
    "三年级上册": "PEPXiaoXue3_1.json",
    "三年级下册": "PEPXiaoXue3_2.json",
    "四年级上册": "PEPXiaoXue4_1.json",
    "四年级下册": "PEPXiaoXue4_2.json",
    "五年级上册": "PEPXiaoXue5_1.json",
    "五年级下册": "PEPXiaoXue5_2.json",
    "六年级上册": "PEPXiaoXue6_1.json",
    "六年级下册": "PEPXiaoXue6_2.json",
}

# 年级代码（用于存储）
GRADE_CODES = {
    "三年级上册": "grade3_1",
    "三年级下册": "grade3_2",
    "四年级上册": "grade4_1",
    "四年级下册": "grade4_2",
    "五年级上册": "grade5_1",
    "五年级下册": "grade5_2",
    "六年级上册": "grade6_1",
    "六年级下册": "grade6_2",
}


# ==================== 数据结构 ====================

@dataclass
class WordInfo:
    id: int
    word: str
    definition: str
    length: int


@dataclass
class PuzzlePiece:
    grid_size: int
    grid: List[List[str]] = field(default_factory=list)
    words: List[Dict] = field(default_factory=list)
    prefilled: Dict[str, str] = field(default_factory=dict)
    clue_numbers: List[List[Optional[int]]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.grid:
            self.grid = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        if not self.clue_numbers:
            self.clue_numbers = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]


# ==================== 工具函数 ====================

def load_vocabulary(vocab_path: str) -> List[WordInfo]:
    """加载词汇文件"""
    with open(vocab_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    words = []
    word_list = data.get("words", data) if isinstance(data, dict) else data
    
    for i, w in enumerate(word_list):
        word_text = w.get("word", "").strip()
        # 跳过包含空格的词组和太长的单词
        if " " in word_text or len(word_text) > 10 or len(word_text) < 2:
            continue
        # 只保留纯字母单词
        if not word_text.isalpha():
            continue
        
        # 获取释义
        trans = w.get("trans", [])
        definition = ""
        if trans and isinstance(trans, list) and len(trans) > 0:
            definition = trans[0].get("tranCn", "")
        if not definition:
            definition = w.get("definition", "")
        
        words.append(WordInfo(
            id=i + 1,
            word=word_text.upper(),
            definition=definition,
            length=len(word_text)
        ))
    
    return words


def filter_words_by_length(words: List[WordInfo], min_len: int, max_len: int) -> List[WordInfo]:
    """按长度过滤单词"""
    return [w for w in words if min_len <= w.length <= max_len]


# ==================== 填字生成器 ====================

class SimplePuzzleGenerator:
    """简化版填字游戏生成器"""
    
    def __init__(self, words: List[WordInfo], config: dict):
        self.words = words
        self.grid_size = config["grid_size"]
        self.min_words = config["min_words"]
        self.max_words = config["max_words"]
        self.min_len = config["min_len"]
        self.max_len = config["max_len"]
        
        # 按长度筛选
        self.available_words = filter_words_by_length(words, self.min_len, min(self.max_len, self.grid_size))
        random.shuffle(self.available_words)
        
        # 初始化网格
        self.grid = [['' for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.placed_words = []
        self.used_word_ids = set()
    
    def generate(self, max_attempts: int = 50) -> Optional[PuzzlePiece]:
        """生成填字游戏"""
        for attempt in range(max_attempts):
            self._reset()
            
            if self._try_generate():
                if len(self.placed_words) >= self.min_words:
                    return self._build_puzzle()
        
        return None
    
    def _reset(self):
        """重置状态"""
        self.grid = [['' for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.placed_words = []
        self.used_word_ids = set()
        random.shuffle(self.available_words)
    
    def _try_generate(self) -> bool:
        """尝试生成谜题"""
        if not self.available_words:
            return False
        
        # 放置第一个单词（横向，居中）
        for word in self.available_words:
            if word.length <= self.grid_size:
                start_col = max(0, (self.grid_size - word.length) // 2)
                start_row = self.grid_size // 2
                if self._place_word(word, start_row, start_col, "across"):
                    break
        
        if not self.placed_words:
            return False
        
        # 继续尝试放置更多单词
        attempts = 0
        max_attempts = len(self.available_words) * 3
        
        while len(self.placed_words) < self.max_words and attempts < max_attempts:
            attempts += 1
            
            for word in self.available_words:
                if word.id in self.used_word_ids:
                    continue
                if word.length > self.grid_size:
                    continue
                
                if self._try_place_word_crossing(word):
                    if len(self.placed_words) >= self.max_words:
                        break
        
        return len(self.placed_words) >= self.min_words
    
    def _try_place_word_crossing(self, word: WordInfo) -> bool:
        """尝试通过交叉放置单词"""
        placements = []
        
        for placed in self.placed_words:
            placed_word = placed["word"]
            placed_row = placed["row"]
            placed_col = placed["col"]
            placed_dir = placed["direction"]
            
            for i, letter1 in enumerate(placed_word):
                for j, letter2 in enumerate(word.word):
                    if letter1 == letter2:
                        if placed_dir == "across":
                            # 新单词纵向
                            new_row = placed_row - j
                            new_col = placed_col + i
                            new_dir = "down"
                        else:
                            # 新单词横向
                            new_row = placed_row + i
                            new_col = placed_col - j
                            new_dir = "across"
                        
                        if self._can_place(word, new_row, new_col, new_dir):
                            score = self._score_placement(word, new_row, new_col, new_dir)
                            placements.append((new_row, new_col, new_dir, score))
        
        if not placements:
            return False
        
        # 选择最佳位置
        placements.sort(key=lambda x: x[3], reverse=True)
        best = placements[0]
        
        return self._place_word(word, best[0], best[1], best[2])
    
    def _can_place(self, word: WordInfo, row: int, col: int, direction: str) -> bool:
        """检查是否可以放置单词"""
        word_len = word.length
        
        # 边界检查
        if direction == "across":
            if row < 0 or row >= self.grid_size:
                return False
            if col < 0 or col + word_len > self.grid_size:
                return False
        else:
            if col < 0 or col >= self.grid_size:
                return False
            if row < 0 or row + word_len > self.grid_size:
                return False
        
        # 检查冲突
        has_intersection = False
        for i, letter in enumerate(word.word):
            if direction == "across":
                r, c = row, col + i
            else:
                r, c = row + i, col
            
            existing = self.grid[r][c]
            if existing:
                if existing != letter:
                    return False
                has_intersection = True
        
        # 必须有交叉（除非是第一个单词）
        if self.placed_words and not has_intersection:
            return False
        
        # 检查首尾不能紧贴其他字母
        if direction == "across":
            if col > 0 and self.grid[row][col - 1]:
                return False
            if col + word_len < self.grid_size and self.grid[row][col + word_len]:
                return False
        else:
            if row > 0 and self.grid[row - 1][col]:
                return False
            if row + word_len < self.grid_size and self.grid[row + word_len][col]:
                return False
        
        # 检查平行方向的相邻格子（避免形成无效单词）
        for i, letter in enumerate(word.word):
            if direction == "across":
                r, c = row, col + i
                # 检查上下
                if self.grid[r][c] != letter:  # 不是交叉点
                    if r > 0 and self.grid[r - 1][c]:
                        return False
                    if r < self.grid_size - 1 and self.grid[r + 1][c]:
                        return False
            else:
                r, c = row + i, col
                # 检查左右
                if self.grid[r][c] != letter:  # 不是交叉点
                    if c > 0 and self.grid[r][c - 1]:
                        return False
                    if c < self.grid_size - 1 and self.grid[r][c + 1]:
                        return False
        
        return True
    
    def _score_placement(self, word: WordInfo, row: int, col: int, direction: str) -> int:
        """评估放置位置的得分"""
        score = 50
        
        # 交叉点越多越好
        intersections = 0
        for i, letter in enumerate(word.word):
            if direction == "across":
                r, c = row, col + i
            else:
                r, c = row + i, col
            if self.grid[r][c]:
                intersections += 1
        score += intersections * 20
        
        # 靠近中心更好
        center = self.grid_size // 2
        if direction == "across":
            dist = abs(row - center) + abs(col + word.length // 2 - center)
        else:
            dist = abs(row + word.length // 2 - center) + abs(col - center)
        score -= dist * 3
        
        return score
    
    def _place_word(self, word: WordInfo, row: int, col: int, direction: str) -> bool:
        """放置单词到网格"""
        # 写入网格
        for i, letter in enumerate(word.word):
            if direction == "across":
                self.grid[row][col + i] = letter
            else:
                self.grid[row + i][col] = letter
        
        # 记录
        self.placed_words.append({
            "id": word.id,
            "word": word.word,
            "definition": word.definition,
            "direction": direction,
            "row": row,
            "col": col,
            "length": word.length
        })
        self.used_word_ids.add(word.id)
        
        return True
    
    def _build_puzzle(self) -> PuzzlePiece:
        """构建谜题对象"""
        puzzle = PuzzlePiece(grid_size=self.grid_size)
        
        # 转换网格（空格为None）
        cells = []
        for row in self.grid:
            cells_row = []
            for cell in row:
                cells_row.append("" if cell else None)
            cells.append(cells_row)
        puzzle.grid = cells
        
        # 计算线索编号
        position_clue_map = {}
        clue_number = 1
        
        # 按位置排序单词
        sorted_words = sorted(self.placed_words, 
                              key=lambda w: (w["row"], w["col"], 0 if w["direction"] == "across" else 1))
        
        for word_info in sorted_words:
            pos = (word_info["row"], word_info["col"])
            if pos not in position_clue_map:
                position_clue_map[pos] = clue_number
                clue_number += 1
            word_info["clue_number"] = position_clue_map[pos]
            word_info["start_row"] = word_info["row"]
            word_info["start_col"] = word_info["col"]
        
        puzzle.words = sorted_words
        
        # 创建线索编号网格
        for (row, col), num in position_clue_map.items():
            puzzle.clue_numbers[row][col] = num
        
        # 计算预填字母（每个单词至少显示1-2个）
        puzzle.prefilled = self._calculate_prefilled()
        
        return puzzle
    
    def _calculate_prefilled(self) -> Dict[str, str]:
        """计算预填字母"""
        prefilled = {}
        
        for word_info in self.placed_words:
            word = word_info["word"]
            row = word_info["row"]
            col = word_info["col"]
            direction = word_info["direction"]
            word_len = len(word)
            
            # 计算要预填的字母数量
            if word_len <= 3:
                num_prefill = 1
            elif word_len <= 5:
                num_prefill = 2
            else:
                num_prefill = min(3, word_len - 2)
            
            # 收集该单词的所有位置
            positions = []
            for i in range(word_len):
                if direction == "across":
                    positions.append((row, col + i, word[i]))
                else:
                    positions.append((row + i, col, word[i]))
            
            # 随机选择预填位置（优先首尾）
            prefill_indices = [0]  # 首字母必填
            if word_len > 2:
                prefill_indices.append(word_len - 1)  # 末尾
            if num_prefill > 2 and word_len > 4:
                mid = word_len // 2
                if mid not in prefill_indices:
                    prefill_indices.append(mid)
            
            for idx in prefill_indices[:num_prefill]:
                r, c, letter = positions[idx]
                key = f"{r}-{c}"
                if key not in prefilled:
                    prefilled[key] = letter
        
        return prefilled


# ==================== 主逻辑 ====================

def generate_levels_for_grade(grade_name: str, words: List[WordInfo]) -> List[Dict]:
    """为一个年级生成所有关卡（117关）"""
    levels = []
    failed_count = 0
    
    for level_num in range(1, LEVELS_PER_GRADE + 1):
        config = get_level_config(level_num)
        
        # 每10关打印一次进度
        if level_num % 10 == 1 or level_num == LEVELS_PER_GRADE:
            print(f"    生成第{level_num}/{LEVELS_PER_GRADE}关...")
        
        generator = SimplePuzzleGenerator(words, config)
        puzzle = generator.generate(max_attempts=100)
        
        if puzzle:
            # 根据关卡位置计算难度
            cycle_pos = (level_num - 1) % 12
            if cycle_pos < 4:
                difficulty = "easy"
            elif cycle_pos < 8:
                difficulty = "medium"
            else:
                difficulty = "hard"
            
            level_data = {
                "level": level_num,
                "grade": grade_name,
                "grid_size": puzzle.grid_size,
                "cells": puzzle.grid,
                "words": puzzle.words,
                "prefilled": puzzle.prefilled,
                "clue_numbers": puzzle.clue_numbers,
                "difficulty": difficulty,
            }
            levels.append(level_data)
        else:
            failed_count += 1
    
    if failed_count > 0:
        print(f"    ⚠ {failed_count}关生成失败")
    
    return levels


def main():
    print("=" * 60)
    print("生成小学生闯关模式题目")
    print(f"每个年级 {LEVELS_PER_GRADE} 关")
    print("=" * 60)
    
    # 词汇目录
    data_dir = Path(__file__).parent.parent / "data" / "words" / "04_人教版小学"
    output_dir = Path(__file__).parent.parent / "src" / "data"
    
    if not data_dir.exists():
        print(f"错误: 词汇目录不存在 {data_dir}")
        return
    
    all_levels = {}
    
    for grade_name, vocab_file in VOCAB_FILES.items():
        vocab_path = data_dir / vocab_file
        
        if not vocab_path.exists():
            print(f"跳过: {grade_name} - 文件不存在")
            continue
        
        print(f"\n处理 {grade_name}...")
        
        # 加载词汇
        words = load_vocabulary(str(vocab_path))
        print(f"  加载 {len(words)} 个单词")
        
        if len(words) < 10:
            print(f"  单词太少，跳过")
            continue
        
        # 生成关卡
        start_time = time.time()
        levels = generate_levels_for_grade(grade_name, words)
        elapsed = time.time() - start_time
        
        if levels:
            grade_code = GRADE_CODES[grade_name]
            all_levels[grade_code] = {
                "name": grade_name,
                "levels": levels
            }
            print(f"  ✓ 完成，共{len(levels)}关 ({elapsed:.1f}秒)")
    
    # 保存结果
    output_file = output_dir / "primary_campaign_levels.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_levels, f, ensure_ascii=False, indent=2)
    
    print(f"\n保存到: {output_file}")
    
    # 统计
    total_levels = sum(len(g["levels"]) for g in all_levels.values())
    total_words = sum(
        sum(len(l["words"]) for l in g["levels"])
        for g in all_levels.values()
    )
    
    print(f"\n统计:")
    print(f"  年级数: {len(all_levels)}")
    print(f"  关卡总数: {total_levels} (目标: {len(all_levels) * LEVELS_PER_GRADE})")
    print(f"  单词总数: {total_words}")
    print("\n完成!")


if __name__ == "__main__":
    main()
