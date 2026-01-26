#!/usr/bin/env python3
"""
可配置填字游戏生成器

核心功能：
1. 只使用CSP密集布局算法（11-20关算法）
2. 支持参数化配置：
   - 词汇文件（数十个到数千个）
   - 难度（低，中，高）- 决定单词长度
   - 题量（少，中，多）- 决定矩阵大小
3. 密度>=40%，交叉验证
4. 每个参数组合提供多道题，支持刷新
"""
import random
import time
import json
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
from pathlib import Path


# ==================== 配置常量 ====================

# 难度配置 - 决定单词长度
DIFFICULTY_CONFIG = {
    "low": {"name": "低", "min_len": 2, "max_len": 4},
    "medium": {"name": "中", "min_len": 3, "max_len": 6},
    "high": {"name": "高", "min_len": 5, "max_len": 10},
}

# 题量配置 - 决定矩阵大小
QUANTITY_CONFIG = {
    "small": {"name": "少", "grid_sizes": [4, 5]},
    "medium": {"name": "中", "grid_sizes": [6, 7, 8]},
    "large": {"name": "多", "grid_sizes": [9, 10]},
}

# 最低密度要求
MIN_DENSITY = 0.40


# ==================== 数据结构 ====================

@dataclass
class ConfigurablePuzzle:
    """可配置填字游戏谜题"""
    grid_size: int
    grid: List[List[str]] = field(default_factory=list)
    row_words: List[dict] = field(default_factory=list)
    col_words: List[dict] = field(default_factory=list)
    revealed_positions: Set[Tuple[int, int]] = field(default_factory=set)
    difficulty: str = "medium"
    quantity: str = "medium"
    
    def __post_init__(self):
        if not self.grid:
            self.grid = [['' for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        if not isinstance(self.revealed_positions, set):
            self.revealed_positions = set()
    
    def calculate_density(self) -> float:
        """计算网格密度 = 有字母的格子数 / 总格子数"""
        total_cells = self.grid_size * self.grid_size
        filled_cells = sum(1 for row in self.grid for cell in row if cell and cell.strip())
        return filled_cells / total_cells if total_cells > 0 else 0
    
    def compute_revealed_letters(self, min_reveal: int = 2):
        """
        计算每个单词应该展示的字母
        
        规则：
        1. 每个单词至少展示 min_reveal 个字母（默认2个）
        2. 但不能全部展示，至少保留1个字母作为答案
        3. 优先展示交叉点的字母（一石二鸟）
        """
        self.revealed_positions = set()
        
        # 找出所有交叉点
        position_words: Dict[Tuple[int, int], List[dict]] = defaultdict(list)
        
        all_words = []
        for word_info in self.row_words:
            row = word_info.get('row', 0)
            col = word_info.get('col', 0)
            word = word_info.get('word', '')
            for i, letter in enumerate(word):
                pos = (row, col + i)
                position_words[pos].append({'word_info': word_info, 'index': i, 'direction': 'across'})
            all_words.append({'info': word_info, 'direction': 'across', 'row': row, 'col': col})
        
        for word_info in self.col_words:
            row = word_info.get('row', 0)
            col = word_info.get('col', 0)
            word = word_info.get('word', '')
            for i, letter in enumerate(word):
                pos = (row + i, col)
                position_words[pos].append({'word_info': word_info, 'index': i, 'direction': 'down'})
            all_words.append({'info': word_info, 'direction': 'down', 'row': row, 'col': col})
        
        # 找出交叉点
        crossings = {pos for pos, words_at_pos in position_words.items() if len(words_at_pos) >= 2}
        
        # 为每个单词分配展示的字母
        for word_data in all_words:
            word_info = word_data['info']
            direction = word_data['direction']
            word = word_info.get('word', '')
            row = word_data['row']
            col = word_data['col']
            word_len = len(word)
            
            if word_len <= 2:
                num_reveal = 1
            else:
                num_reveal = min(max(2, word_len // 2), word_len - 1)
            
            # 收集该单词的所有位置
            word_positions = []
            for i in range(word_len):
                if direction == 'across':
                    pos = (row, col + i)
                else:
                    pos = (row + i, col)
                word_positions.append(pos)
            
            # 计算已经展示的位置数
            already_revealed = sum(1 for pos in word_positions if pos in self.revealed_positions)
            need_to_reveal = max(0, num_reveal - already_revealed)
            
            if need_to_reveal > 0:
                unrevealed = [pos for pos in word_positions if pos not in self.revealed_positions]
                crossing_unrevealed = [pos for pos in unrevealed if pos in crossings]
                non_crossing_unrevealed = [pos for pos in unrevealed if pos not in crossings]
                
                random.shuffle(crossing_unrevealed)
                random.shuffle(non_crossing_unrevealed)
                
                to_reveal = []
                to_reveal.extend(crossing_unrevealed[:need_to_reveal])
                remaining = need_to_reveal - len(to_reveal)
                
                if remaining > 0:
                    to_reveal.extend(non_crossing_unrevealed[:remaining])
                
                # 确保不会全部展示
                if len(to_reveal) + already_revealed >= word_len:
                    to_reveal = to_reveal[:word_len - already_revealed - 1]
                
                for pos in to_reveal:
                    self.revealed_positions.add(pos)
    
    def to_dict(self) -> dict:
        """转换为API响应格式"""
        words = []
        clue_number = 1
        
        all_word_info = []
        
        for word_info in self.row_words:
            if isinstance(word_info, dict) and 'row' in word_info:
                all_word_info.append({
                    "row": word_info['row'], 
                    "col": word_info['col'], 
                    "direction": "across", 
                    "info": word_info
                })
        
        for word_info in self.col_words:
            if isinstance(word_info, dict) and 'row' in word_info:
                all_word_info.append({
                    "row": word_info['row'], 
                    "col": word_info['col'], 
                    "direction": "down", 
                    "info": word_info
                })
        
        # 按位置排序
        all_word_info.sort(key=lambda x: (x["row"], x["col"], 0 if x["direction"] == "across" else 1))
        
        # 分配线索编号
        position_clue_map = {}
        
        for item in all_word_info:
            pos = (item["row"], item["col"])
            if pos not in position_clue_map:
                position_clue_map[pos] = clue_number
                clue_number += 1
            
            info = item["info"]
            word_text = info.get("word", info.get("text", ""))
            words.append({
                "id": info.get("id", 0),
                "word": word_text,
                "definition": info.get("definition", ""),
                "direction": item["direction"],
                "start_row": item["row"],
                "start_col": item["col"],
                "length": info.get("length", len(word_text)),
                "clue_number": position_clue_map[pos]
            })
        
        # 创建掩码网格和展示字母标记
        masked_grid = []
        revealed_grid = []
        
        for i, row in enumerate(self.grid):
            masked_row = []
            revealed_row = []
            for j, cell in enumerate(row):
                if cell:
                    pos = (i, j)
                    if pos in self.revealed_positions:
                        masked_row.append(cell)
                        revealed_row.append(True)
                    else:
                        masked_row.append("")
                        revealed_row.append(False)
                else:
                    masked_row.append(None)
                    revealed_row.append(False)
            masked_grid.append(masked_row)
            revealed_grid.append(revealed_row)
        
        # 创建线索编号网格
        clue_number_grid = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        for (row, col), num in position_clue_map.items():
            clue_number_grid[row][col] = num
        
        return {
            "grid_size": self.grid_size,
            "cells": masked_grid,
            "revealed": revealed_grid,
            "words": words,
            "prefilled": {},
            "clue_numbers": clue_number_grid,
            "puzzle_type": "configurable",
            "density": self.calculate_density(),
            "cross_validated": True,
            "difficulty": self.difficulty,
            "quantity": self.quantity,
        }


class WordIndex:
    """单词索引 - 用于高效查询"""
    
    def __init__(self, words: List[dict], min_len: int = 2, max_len: int = 10):
        self.words = words
        self.min_len = min_len
        self.max_len = max_len
        self.by_length: Dict[int, List[str]] = defaultdict(list)
        self.word_to_info: Dict[str, dict] = {}
        self.valid_words_set: Set[str] = set()
        
        # 按长度索引，只保留符合长度要求的单词
        for w in words:
            word = w["word"].upper()
            if self.min_len <= len(word) <= self.max_len:
                self.by_length[len(word)].append(word)
                self.word_to_info[word] = w
                self.valid_words_set.add(word)
        
        # 预计算位置-字母索引
        self.position_letter_index: Dict[int, Dict[Tuple[int, str], Set[str]]] = {}
        for length, word_list in self.by_length.items():
            self.position_letter_index[length] = defaultdict(set)
            for word in word_list:
                for pos, letter in enumerate(word):
                    self.position_letter_index[length][(pos, letter)].add(word)
    
    def is_valid_word(self, text: str) -> bool:
        """检查字母序列是否是有效单词"""
        return text.upper() in self.valid_words_set
    
    def get_words_by_length(self, length: int) -> List[str]:
        """获取指定长度的所有单词"""
        return self.by_length.get(length, [])
    
    def get_word_info(self, word: str) -> Optional[dict]:
        """获取单词的详细信息"""
        return self.word_to_info.get(word.upper())
    
    def has_words_for_grid(self, grid_size: int) -> bool:
        """检查是否有适合该网格大小的单词"""
        for length in range(self.min_len, min(grid_size + 1, self.max_len + 1)):
            if self.by_length.get(length):
                return True
        return False


class CrossValidatedGenerator:
    """
    交叉验证填字生成器
    
    核心特性：
    1. 交叉验证 - 确保所有横向纵向形成的字母序列都是有效单词
    2. 密度控制 - 使用密度(>=40%)衡量
    3. 单词长度多样化
    """
    
    def __init__(self, word_index: WordIndex, grid_size: int, difficulty: str, quantity: str):
        self.word_index = word_index
        self.grid_size = grid_size
        self.difficulty = difficulty
        self.quantity = quantity
        self.grid = [['' for _ in range(grid_size)] for _ in range(grid_size)]
        self.placed_words: List[dict] = []
    
    def generate(self, min_density: float = MIN_DENSITY, timeout: float = 10.0, 
                 max_retries: int = 30) -> Optional[ConfigurablePuzzle]:
        """生成交叉验证的填字游戏"""
        start_time = time.time()
        
        for attempt in range(max_retries):
            if time.time() - start_time > timeout:
                break
            
            # 重置状态
            self.grid = [['' for _ in range(self.grid_size)] for _ in range(self.grid_size)]
            self.placed_words = []
            
            # 尝试生成
            if self._try_generate(min_density, timeout - (time.time() - start_time)):
                puzzle = self._build_puzzle()
                if puzzle and puzzle.calculate_density() >= min_density:
                    puzzle.compute_revealed_letters(min_reveal=2)
                    return puzzle
        
        return None
    
    def _try_generate(self, min_density: float, timeout: float) -> bool:
        """尝试生成一个谜题"""
        start_time = time.time()
        
        # 获取各种长度的单词
        words_by_length = {}
        min_len = DIFFICULTY_CONFIG[self.difficulty]["min_len"]
        max_len = DIFFICULTY_CONFIG[self.difficulty]["max_len"]
        
        for length in range(min_len, min(self.grid_size + 1, max_len + 1)):
            words = self.word_index.get_words_by_length(length)
            if words:
                random.shuffle(words)
                words_by_length[length] = words
        
        if not words_by_length:
            return False
        
        # 创建长度多样化的单词列表
        all_words = []
        lengths = list(words_by_length.keys())
        random.shuffle(lengths)
        
        for i in range(max(len(w) for w in words_by_length.values())):
            for length in lengths:
                if i < len(words_by_length.get(length, [])):
                    all_words.append((words_by_length[length][i], length))
        
        if not all_words:
            return False
        
        # 放置第一个单词
        mid_lengths = [l for l in lengths if min_len <= l <= min(max_len, self.grid_size)]
        if not mid_lengths:
            mid_lengths = lengths
        first_length = random.choice(mid_lengths)
        first_word_list = words_by_length.get(first_length, [])
        
        if first_word_list:
            first_word = first_word_list[0]
            start_row = self.grid_size // 2
            start_col = max(0, (self.grid_size - len(first_word)) // 2)
            
            if start_col + len(first_word) <= self.grid_size:
                self._place_word(first_word, start_row, start_col, "across")
        
        # 继续放置单词
        used_words = {first_word.upper() if first_word_list else ''}
        max_attempts = 500
        attempts = 0
        
        while self._calculate_density() < min_density and attempts < max_attempts:
            if time.time() - start_time > timeout:
                break
            
            attempts += 1
            
            word_to_place = None
            for word, length in all_words:
                if word.upper() not in used_words:
                    word_to_place = word
                    break
            
            if not word_to_place:
                break
            
            placed = self._try_place_word_validated(word_to_place)
            if placed:
                used_words.add(word_to_place.upper())
            else:
                used_words.add(word_to_place.upper())
        
        return self._calculate_density() >= min_density
    
    def _calculate_density(self) -> float:
        """计算当前网格密度"""
        total = self.grid_size * self.grid_size
        filled = sum(1 for row in self.grid for cell in row if cell)
        return filled / total
    
    def _try_place_word_validated(self, word: str) -> bool:
        """尝试放置单词，并验证不会形成无效的字母序列"""
        word = word.upper()
        word_len = len(word)
        
        placements = []
        
        # 寻找与已有单词的交叉点
        for placed in self.placed_words:
            placed_word = placed['word']
            placed_row = placed['row']
            placed_col = placed['col']
            placed_dir = placed['direction']
            
            for i, letter1 in enumerate(placed_word):
                for j, letter2 in enumerate(word):
                    if letter1 == letter2:
                        if placed_dir == 'across':
                            new_row = placed_row - j
                            new_col = placed_col + i
                            new_dir = 'down'
                        else:
                            new_row = placed_row + i
                            new_col = placed_col - j
                            new_dir = 'across'
                        
                        if self._can_place_validated(word, new_row, new_col, new_dir):
                            score = self._calculate_placement_score(word, new_row, new_col, new_dir)
                            if score > 0:
                                placements.append((new_row, new_col, new_dir, score))
        
        # 如果是第一个单词
        if not placements and len(self.placed_words) == 0:
            row = self.grid_size // 2
            col = max(0, (self.grid_size - word_len) // 2)
            if self._can_place_validated(word, row, col, 'across'):
                placements.append((row, col, 'across', 100))
        
        if not placements:
            return False
        
        placements.sort(key=lambda x: x[3], reverse=True)
        best = placements[0]
        
        return self._place_word(word, best[0], best[1], best[2])
    
    def _can_place_validated(self, word: str, row: int, col: int, direction: str) -> bool:
        """检查是否可以放置单词，并验证不会形成无效的字母序列"""
        word_len = len(word)
        
        # 边界检查
        if direction == 'across':
            if row < 0 or row >= self.grid_size:
                return False
            if col < 0 or col + word_len > self.grid_size:
                return False
        else:
            if col < 0 or col >= self.grid_size:
                return False
            if row < 0 or row + word_len > self.grid_size:
                return False
        
        # 检查是否与同方向的已有单词重叠（防止形成子串，如 LEG 和 LEGS 同时存在）
        for placed in self.placed_words:
            if placed['direction'] == direction:
                p_row, p_col = placed['row'], placed['col']
                p_len = placed['length']
                
                if direction == 'across' and row == p_row:
                    # 同行，检查列范围是否重叠
                    new_start, new_end = col, col + word_len - 1
                    exist_start, exist_end = p_col, p_col + p_len - 1
                    if not (new_end < exist_start or new_start > exist_end):
                        return False  # 有重叠，拒绝放置
                
                elif direction == 'down' and col == p_col:
                    # 同列，检查行范围是否重叠
                    new_start, new_end = row, row + word_len - 1
                    exist_start, exist_end = p_row, p_row + p_len - 1
                    if not (new_end < exist_start or new_start > exist_end):
                        return False  # 有重叠，拒绝放置
        
        # 检查是否与现有字母冲突
        has_intersection = (len(self.placed_words) == 0)
        
        for i, letter in enumerate(word):
            if direction == 'across':
                r, c = row, col + i
            else:
                r, c = row + i, col
            
            existing = self.grid[r][c]
            if existing:
                if existing != letter:
                    return False
                has_intersection = True
        
        if not has_intersection:
            return False
        
        # 检查单词首尾
        if direction == 'across':
            if col > 0 and self.grid[row][col - 1]:
                return False
            if col + word_len < self.grid_size and self.grid[row][col + word_len]:
                return False
        else:
            if row > 0 and self.grid[row - 1][col]:
                return False
            if row + word_len < self.grid_size and self.grid[row + word_len][col]:
                return False
        
        # 交叉验证
        if not self._validate_cross_sequences(word, row, col, direction):
            return False
        
        return True
    
    def _validate_cross_sequences(self, word: str, row: int, col: int, direction: str) -> bool:
        """验证放置后不会形成无效的字母序列"""
        word_len = len(word)
        
        # 创建临时网格
        temp_grid = [r[:] for r in self.grid]
        for i, letter in enumerate(word):
            if direction == 'across':
                temp_grid[row][col + i] = letter
            else:
                temp_grid[row + i][col] = letter
        
        # 检查垂直于放置方向的序列
        for i in range(word_len):
            if direction == 'across':
                r, c = row, col + i
                seq = self._get_vertical_sequence(temp_grid, r, c)
            else:
                r, c = row + i, col
                seq = self._get_horizontal_sequence(temp_grid, r, c)
            
            if len(seq) >= 2:
                if not self.word_index.is_valid_word(seq):
                    return False
        
        return True
    
    def _get_vertical_sequence(self, grid: List[List[str]], row: int, col: int) -> str:
        """获取垂直连续字母序列"""
        start_row = row
        while start_row > 0 and grid[start_row - 1][col]:
            start_row -= 1
        
        seq = ""
        r = start_row
        while r < self.grid_size and grid[r][col]:
            seq += grid[r][col]
            r += 1
        
        return seq
    
    def _get_horizontal_sequence(self, grid: List[List[str]], row: int, col: int) -> str:
        """获取水平连续字母序列"""
        start_col = col
        while start_col > 0 and grid[row][start_col - 1]:
            start_col -= 1
        
        seq = ""
        c = start_col
        while c < self.grid_size and grid[row][c]:
            seq += grid[row][c]
            c += 1
        
        return seq
    
    def _calculate_placement_score(self, word: str, row: int, col: int, direction: str) -> int:
        """计算放置位置的得分"""
        score = 50
        word_len = len(word)
        
        intersections = 0
        for i in range(word_len):
            if direction == 'across':
                r, c = row, col + i
            else:
                r, c = row + i, col
            
            if self.grid[r][c]:
                intersections += 1
        
        score += intersections * 20
        
        center = self.grid_size // 2
        if direction == 'across':
            dist = abs(row - center) + abs(col + word_len // 2 - center)
        else:
            dist = abs(row + word_len // 2 - center) + abs(col - center)
        score -= dist * 2
        
        existing_lengths = {len(pw['word']) for pw in self.placed_words}
        if word_len not in existing_lengths:
            score += 15
        
        return score
    
    def _place_word(self, word: str, row: int, col: int, direction: str) -> bool:
        """放置单词到网格"""
        word = word.upper()
        word_len = len(word)
        
        for i, letter in enumerate(word):
            if direction == 'across':
                self.grid[row][col + i] = letter
            else:
                self.grid[row + i][col] = letter
        
        word_info = self.word_index.get_word_info(word)
        self.placed_words.append({
            'word': word,
            'row': row,
            'col': col,
            'direction': direction,
            'length': word_len,
            'definition': word_info.get('definition', '') if word_info else '',
            'id': word_info.get('id', 0) if word_info else 0
        })
        
        return True
    
    def _build_puzzle(self) -> Optional[ConfigurablePuzzle]:
        """构建谜题对象"""
        if not self.placed_words:
            return None
        
        puzzle = ConfigurablePuzzle(
            grid_size=self.grid_size,
            difficulty=self.difficulty,
            quantity=self.quantity
        )
        puzzle.grid = [row[:] for row in self.grid]
        
        for pw in self.placed_words:
            word_data = {
                'id': pw['id'],
                'word': pw['word'],
                'definition': pw['definition'],
                'row': pw['row'],
                'col': pw['col'],
                'length': pw['length']
            }
            
            if pw['direction'] == 'across':
                puzzle.row_words.append(word_data)
            else:
                puzzle.col_words.append(word_data)
        
        return puzzle


class ConfigurablePuzzleGenerator:
    """
    可配置填字游戏生成器 - 主入口类
    
    支持参数：
    - 难度：low（2-4字母）, medium（3-6字母）, high（5-10字母）
    - 题量：small（4x4,5x5）, medium（6x6,7x7,8x8）, large（9x9,10x10）
    """
    
    def __init__(self, random_seed: int = None):
        self._answer_cache: Dict[int, str] = {}
        self._word_id_counter = 100000
        
        if random_seed is None:
            random_seed = int(time.time() * 1000000) % (2**31)
        random.seed(random_seed)
        self._random_seed = random_seed
    
    def reseed(self, seed: int = None):
        """重新设置随机种子"""
        if seed is None:
            seed = int(time.time() * 1000000) % (2**31)
        random.seed(seed)
        self._random_seed = seed
        return seed
    
    def generate_puzzle(self, vocab_words: List[dict], difficulty: str = "medium", 
                        quantity: str = "medium", timeout: float = 15.0) -> Optional[dict]:
        """
        生成填字游戏
        
        Args:
            vocab_words: 词库单词列表
            difficulty: 难度 - "low"/"medium"/"high"
            quantity: 题量 - "small"/"medium"/"large"
            timeout: 超时时间
        
        Returns:
            生成的谜题字典，失败返回None
        """
        if difficulty not in DIFFICULTY_CONFIG:
            difficulty = "medium"
        if quantity not in QUANTITY_CONFIG:
            quantity = "medium"
        
        diff_config = DIFFICULTY_CONFIG[difficulty]
        qty_config = QUANTITY_CONFIG[quantity]
        
        # 创建单词索引
        word_index = WordIndex(
            vocab_words,
            min_len=diff_config["min_len"],
            max_len=diff_config["max_len"]
        )
        
        # 随机选择网格大小
        grid_sizes = qty_config["grid_sizes"]
        random.shuffle(grid_sizes)
        
        for grid_size in grid_sizes:
            if not word_index.has_words_for_grid(grid_size):
                continue
            
            generator = CrossValidatedGenerator(word_index, grid_size, difficulty, quantity)
            puzzle = generator.generate(min_density=MIN_DENSITY, timeout=timeout / len(grid_sizes))
            
            if puzzle:
                # 缓存答案
                for word_info in puzzle.row_words + puzzle.col_words:
                    word_id = word_info.get('id', 0)
                    word = word_info.get('word', '')
                    if word_id and word:
                        self._answer_cache[word_id] = word
                
                result = puzzle.to_dict()
                return result
        
        return None
    
    def generate_multiple_puzzles(self, vocab_words: List[dict], difficulty: str = "medium",
                                   quantity: str = "medium", count: int = 3,
                                   timeout: float = 30.0) -> List[dict]:
        """
        生成多个填字游戏（用于预生成题库）
        
        Args:
            vocab_words: 词库单词列表
            difficulty: 难度
            quantity: 题量
            count: 生成数量
            timeout: 总超时时间
        
        Returns:
            生成的谜题列表
        """
        puzzles = []
        start_time = time.time()
        
        for i in range(count * 3):  # 多尝试几次
            if len(puzzles) >= count:
                break
            if time.time() - start_time > timeout:
                break
            
            # 每次重新设置随机种子
            self.reseed()
            
            puzzle = self.generate_puzzle(vocab_words, difficulty, quantity, timeout=5.0)
            if puzzle:
                puzzle["puzzle_index"] = len(puzzles) + 1
                puzzles.append(puzzle)
        
        return puzzles
    
    def verify_answer(self, word_id: int, answer: str) -> dict:
        """验证答案"""
        correct_answer = self._answer_cache.get(word_id, "")
        is_correct = answer.upper() == correct_answer.upper()
        
        return {
            "correct": is_correct,
            "word": correct_answer if is_correct else "",
            "definition": ""
        }


def generate_all_combinations(vocab_words: List[dict]) -> Dict[str, List[dict]]:
    """
    生成所有参数组合的题库
    
    Returns:
        {"difficulty_quantity": [puzzle1, puzzle2, puzzle3, ...], ...}
    """
    generator = ConfigurablePuzzleGenerator()
    all_puzzles = {}
    
    for difficulty in DIFFICULTY_CONFIG.keys():
        for quantity in QUANTITY_CONFIG.keys():
            key = f"{difficulty}_{quantity}"
            print(f"生成组合: {key}")
            
            puzzles = generator.generate_multiple_puzzles(
                vocab_words,
                difficulty=difficulty,
                quantity=quantity,
                count=3,
                timeout=30.0
            )
            
            all_puzzles[key] = puzzles
            print(f"  成功生成 {len(puzzles)} 道题")
    
    return all_puzzles


def load_vocabulary_file(vocab_path: str) -> List[dict]:
    """加载词汇文件"""
    with open(vocab_path, 'r', encoding='utf-8') as f:
        words = json.load(f)
    
    # 确保每个单词有ID
    for i, w in enumerate(words):
        if 'id' not in w:
            w['id'] = i + 1
    
    return words


def display_puzzle_answer(puzzle: dict) -> str:
    """以答案形式展示谜题"""
    output = []
    grid_size = puzzle.get("grid_size", 0)
    words = puzzle.get("words", [])
    cells = puzzle.get("cells", [])
    revealed = puzzle.get("revealed", [])
    
    output.append(f"\n网格大小: {grid_size}x{grid_size}")
    output.append(f"难度: {puzzle.get('difficulty', 'N/A')}")
    output.append(f"题量: {puzzle.get('quantity', 'N/A')}")
    output.append(f"密度: {puzzle.get('density', 0):.1%}")
    output.append(f"单词数: {len(words)}")
    
    # 构建答案网格
    answer_grid = [[cell if cell else '' for cell in row] for row in cells]
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
    
    # 显示网格
    output.append("\n答案网格 ([]表示展示的字母):")
    header = "    " + " ".join(f"{i:2}" for i in range(grid_size))
    output.append(header)
    output.append("    " + "-" * (grid_size * 3))
    
    for i, row in enumerate(answer_grid):
        row_str = f"{i:2} |"
        for j, cell in enumerate(row):
            if cell == '' or cell is None:
                row_str += " . "
            else:
                is_revealed = False
                if revealed and i < len(revealed) and j < len(revealed[i]):
                    is_revealed = revealed[i][j]
                if is_revealed:
                    row_str += f"[{cell}]"
                else:
                    row_str += f" {cell} "
        output.append(row_str)
    
    # 显示单词列表
    across_words = [w for w in words if w["direction"] == "across"]
    down_words = [w for w in words if w["direction"] == "down"]
    
    output.append(f"\n横向单词 ({len(across_words)}个):")
    for w in sorted(across_words, key=lambda x: x.get("clue_number", 0)):
        output.append(f"  {w.get('clue_number', '?')}. {w['word']} - {w.get('definition', '')}")
    
    output.append(f"\n纵向单词 ({len(down_words)}个):")
    for w in sorted(down_words, key=lambda x: x.get("clue_number", 0)):
        output.append(f"  {w.get('clue_number', '?')}. {w['word']} - {w.get('definition', '')}")
    
    return "\n".join(output)


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="可配置填字游戏生成器")
    parser.add_argument("--vocab", required=True, help="词汇文件路径 (JSON格式)")
    parser.add_argument("--difficulty", choices=["low", "medium", "high"], default="medium",
                        help="难度: low(2-4字母), medium(3-6字母), high(5-10字母)")
    parser.add_argument("--quantity", choices=["small", "medium", "large"], default="medium",
                        help="题量: small(4x4,5x5), medium(6x6,7x7,8x8), large(9x9,10x10)")
    parser.add_argument("--count", type=int, default=3, help="生成题目数量")
    parser.add_argument("--output", help="输出文件路径 (JSON)")
    parser.add_argument("--all-combinations", action="store_true", help="生成所有参数组合")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("可配置填字游戏生成器")
    print("=" * 60)
    
    # 加载词库
    print(f"加载词库: {args.vocab}")
    vocab_words = load_vocabulary_file(args.vocab)
    print(f"共 {len(vocab_words)} 个单词")
    
    if args.all_combinations:
        # 生成所有组合
        print("\n生成所有参数组合...")
        all_puzzles = generate_all_combinations(vocab_words)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(all_puzzles, f, ensure_ascii=False, indent=2)
            print(f"\n已保存到: {args.output}")
        else:
            for key, puzzles in all_puzzles.items():
                print(f"\n=== {key} ===")
                for p in puzzles:
                    print(display_puzzle_answer(p))
    else:
        # 生成指定参数的题目
        print(f"\n参数: 难度={args.difficulty}, 题量={args.quantity}, 数量={args.count}")
        
        generator = ConfigurablePuzzleGenerator()
        puzzles = generator.generate_multiple_puzzles(
            vocab_words,
            difficulty=args.difficulty,
            quantity=args.quantity,
            count=args.count
        )
        
        print(f"成功生成 {len(puzzles)} 道题")
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(puzzles, f, ensure_ascii=False, indent=2)
            print(f"已保存到: {args.output}")
        else:
            for p in puzzles:
                print(display_puzzle_answer(p))
