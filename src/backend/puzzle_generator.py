"""
填字游戏关卡生成器 - 核心算法

增强功能：
1. 交叉验证 - 确保所有横向纵向形成的字母序列都是有效单词
2. 避免形成无效的字母组合如 ACDE, KHIS
"""
import random
import time
from typing import List, Dict, Tuple, Optional, Set, FrozenSet
from dataclasses import dataclass, field


def is_pure_alpha(word: str) -> bool:
    """检查单词是否只包含26个英文字母（不含连字符、撇号、空格等）
    
    无效单词示例：
    - X-RAY, T-SHIRT（含连字符）
    - O'CLOCK, WE'LL（含撇号）
    - ICE CREAM（含空格）
    """
    return word.isalpha()


@dataclass
class Word:
    """单词数据结构"""
    id: int
    text: str
    definition: str
    difficulty: int = 1


@dataclass
class PlacedWord:
    """已放置的单词"""
    word: Word
    row: int
    col: int
    direction: str  # "across" or "down"
    
    @property
    def end_row(self) -> int:
        if self.direction == "down":
            return self.row + len(self.word.text) - 1
        return self.row
    
    @property
    def end_col(self) -> int:
        if self.direction == "across":
            return self.col + len(self.word.text) - 1
        return self.col


@dataclass 
class CrosswordPuzzle:
    """填字游戏谜题"""
    grid_size: int
    grid: List[List[Optional[str]]] = field(default_factory=list)
    placed_words: List[PlacedWord] = field(default_factory=list)
    prefilled: Dict[str, str] = field(default_factory=dict)  # "row-col" -> letter
    
    def __post_init__(self):
        if not self.grid:
            self.grid = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
    
    def to_dict(self) -> dict:
        """转换为API响应格式 - 使用正确的填字游戏编号系统"""
        # 1. 首先计算每个位置的线索编号
        # 按照填字游戏规则：从左到右、从上到下扫描，每个单词起始位置分配编号
        # 同一位置的横向和纵向单词共享编号
        
        # 收集所有单词起始位置
        start_positions = set()
        for pw in self.placed_words:
            start_positions.add((pw.row, pw.col))
        
        # 按照行优先、列次之排序
        sorted_positions = sorted(start_positions, key=lambda p: (p[0], p[1]))
        
        # 为每个起始位置分配线索编号
        position_to_clue_number = {}
        clue_number = 1
        for pos in sorted_positions:
            position_to_clue_number[pos] = clue_number
            clue_number += 1
        
        # 2. 构建单词列表，按照线索编号和方向排序
        words_with_clue = []
        for pw in self.placed_words:
            clue_num = position_to_clue_number[(pw.row, pw.col)]
            words_with_clue.append({
                "id": pw.word.id,
                "word": pw.word.text,
                "definition": pw.word.definition,
                "direction": pw.direction,
                "start_row": pw.row,
                "start_col": pw.col,
                "length": len(pw.word.text),
                "clue_number": clue_num  # 添加线索编号
            })
        
        # 按照线索编号排序，同编号的横向优先
        words_with_clue.sort(key=lambda w: (w["clue_number"], 0 if w["direction"] == "across" else 1))
        
        # 3. 创建掩码网格 (隐藏答案)
        masked_grid = []
        for row in self.grid:
            masked_row = []
            for cell in row:
                if cell is None:
                    masked_row.append(None)
                else:
                    masked_row.append("")  # 空字符串表示需要填写
            masked_grid.append(masked_row)
        
        # 4. 创建线索编号网格（用于在网格中显示数字）
        clue_number_grid = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        for pos, num in position_to_clue_number.items():
            clue_number_grid[pos[0]][pos[1]] = num
        
        return {
            "grid_size": self.grid_size,
            "cells": masked_grid,
            "words": words_with_clue,
            "prefilled": self.prefilled,
            "clue_numbers": clue_number_grid  # 新增：线索编号网格
        }


# ==================== 动态关卡配置 ====================
# 1-10关采用循序渐进的难度配置，动态使用选定词库的词汇
# 配置格式：(grid_size, min_words, max_words, max_word_len, difficulty, prefill_boost)
# prefill_boost: 额外的预填比例加成（新手关卡需要更多提示）
PROGRESSIVE_LEVEL_CONFIG = {
    # 第1-2关：入门级 - 5x5网格，2个简单短词
    1: (5, 2, 2, 4, "easy", 0.3),
    2: (5, 2, 2, 4, "easy", 0.25),
    
    # 第3-4关：初级 - 5x5网格，3个词
    3: (5, 2, 3, 5, "easy", 0.2),
    4: (5, 3, 3, 5, "easy", 0.15),
    
    # 第5-6关：中级入门 - 6x6网格，3-4个词
    5: (6, 3, 4, 6, "medium", 0.1),
    6: (6, 3, 4, 6, "medium", 0.1),
    
    # 第7-8关：中级 - 7x7网格，4-5个词
    7: (7, 4, 5, 7, "medium", 0.05),
    8: (8, 4, 5, 8, "medium", 0.0),
    
    # 第9关：高级 - 8x8网格，5-6个词
    9: (8, 5, 6, 8, "hard", 0.0),
    
    # 第10关：终极挑战 - 10x10网格，6-8个词（支持大学词汇等长词）
    10: (10, 6, 8, 10, "hard", 0.0),
}


class CrosswordGenerator:
    """
    交叉填字游戏生成器
    
    增强功能：
    - 交叉验证：确保所有横向纵向形成的字母序列都是有效单词
    - 避免形成无效的字母组合如 ACDE, KHIS
    """
    
    # 关卡难度配置 - 最大支持10x10
    LEVEL_CONFIG = {
        # level_range: (grid_size, min_words, max_words, max_word_len)
        (1, 32): (5, 2, 3, 5),
        (33, 64): (6, 3, 4, 6),
        (65, 128): (7, 4, 5, 7),
        (129, 192): (8, 5, 6, 8),
        (193, 256): (10, 6, 8, 10),  # 支持10x10
    }
    
    DIFFICULTY_CONFIG = {
        # difficulty: (grid_size, min_words, max_words, max_word_len)
        "easy": (5, 2, 3, 5),
        "medium": (7, 4, 5, 7),
        "hard": (10, 6, 8, 10),  # 支持10x10
    }
    
    # 预填字母比例配置（根据难度）
    # 新规则：简单40%、中等25%、困难15%
    PREFILL_RATIO = {
        "easy": (0.35, 0.45),   # 简单：预填35%-45%（约40%）
        "medium": (0.20, 0.30), # 中等：预填20%-30%（约25%）
        "hard": (0.10, 0.20),   # 困难：预填10%-20%（约15%）
    }
    
    def __init__(self, random_seed: int = None):
        self._answer_cache: Dict[int, str] = {}  # word_id -> correct answer
        self._word_id_counter = 10000  # 用于预设关卡的单词ID
        self._valid_words_set: Set[str] = set()  # 有效单词集合，用于交叉验证
        # 使用时间戳作为默认随机种子，确保每次生成不同
        if random_seed is None:
            random_seed = int(time.time() * 1000000) % (2**31)
        random.seed(random_seed)
        self._random_seed = random_seed
    
    def _build_valid_words_set(self, word_list: List[dict]):
        """构建有效单词集合，用于交叉验证（只接受纯字母单词）"""
        self._valid_words_set = set()
        for w in word_list:
            word = w.get("word", "").upper()
            if len(word) >= 2 and is_pure_alpha(word):
                self._valid_words_set.add(word)
    
    def _is_valid_word(self, text: str) -> bool:
        """检查字母序列是否是有效单词"""
        return text.upper() in self._valid_words_set
    
    def get_level_config(self, level: int) -> Tuple[int, int, int, int]:
        """根据关卡获取配置 (grid_size, min_words, max_words, max_word_len)"""
        for (start, end), config in self.LEVEL_CONFIG.items():
            if start <= level <= end:
                return config
        return (7, 4, 5, 7)  # 默认中等难度
    
    def generate_campaign_level(self, level: int, group: str, vocab_manager, config: dict = None) -> dict:
        """生成闯关模式关卡 - 使用动态生成，根据词库选择词汇
        
        Args:
            level: 关卡号
            group: 词库分组
            vocab_manager: 词汇管理器
            config: 可选的外部配置，包含 grid_size, word_count, difficulty, prefill_ratio
        """
        
        # 优先使用外部配置
        if config:
            grid_size = config.get("grid_size", 7)
            num_words = config.get("word_count", 4)
            max_word_len = grid_size - 1
            difficulty = config.get("difficulty", "medium")
            prefill_boost = 0.0
        # 1-10关使用渐进式配置
        elif level in PROGRESSIVE_LEVEL_CONFIG:
            grid_size, min_words, max_words, max_word_len, difficulty, prefill_boost = PROGRESSIVE_LEVEL_CONFIG[level]
            num_words = random.randint(min_words, max_words)
        else:
            # 11关及以后使用通用配置
            grid_size, min_words, max_words, max_word_len = self.get_level_config(level)
            num_words = random.randint(min_words, max_words)
            difficulty = self._get_difficulty_name(level)
            prefill_boost = 0.0
        
        # 获取词汇（优先获取适合网格大小的词汇），使用用户选择的词库
        words = vocab_manager.get_words_for_puzzle(group, num_words * 5, max_word_len)
        
        # 获取完整词库用于交叉验证
        if hasattr(vocab_manager, 'get_all_words_for_csp'):
            all_words = vocab_manager.get_all_words_for_csp(group)
        else:
            all_words = vocab_manager.get_words(group, limit=10000)
        self._build_valid_words_set(all_words)
        
        # 使用改进的算法生成谜题（确保单词有共同字母，并进行交叉验证）
        puzzle = self._generate_puzzle_with_crossable_words(grid_size, words, num_words)
        
        # 添加预填字母，新手关卡有额外加成
        self._add_prefilled_letters(puzzle, difficulty, prefill_boost)
        
        result = puzzle.to_dict()
        result["level"] = level
        result["difficulty"] = difficulty
        result["group"] = group
        
        return result
    
    def _find_crossable_words(self, words: List[dict], placed_words: List[Word]) -> List[dict]:
        """找出能与已放置单词交叉的候选词"""
        if not placed_words:
            return words
        
        # 收集已放置单词的所有字母
        placed_letters = set()
        for pw in placed_words:
            placed_letters.update(pw.text.upper())
        
        # 筛选出有共同字母的单词
        crossable = []
        for w in words:
            word_text = w["word"].upper()
            if any(c in placed_letters for c in word_text):
                crossable.append(w)
        
        return crossable
    
    def _generate_puzzle_with_crossable_words(self, grid_size: int, word_list: List[dict], target_words: int) -> CrosswordPuzzle:
        """使用改进的算法生成谜题，确保单词能交叉"""
        puzzle = CrosswordPuzzle(grid_size=grid_size)
        
        # 转换词汇格式（过滤含非字母字符的单词）
        words = [
            Word(id=w["id"], text=w["word"].upper(), definition=w["definition"], difficulty=w.get("difficulty", 1))
            for w in word_list
            if 2 <= len(w["word"]) <= grid_size and is_pure_alpha(w["word"])
        ]
        
        if not words:
            return puzzle
        
        # 按长度排序，优先放置中等长度的词（3-5字母最适合交叉）
        def word_priority(w):
            word_len = len(w.text)
            if 3 <= word_len <= 5:
                return (0, -word_len)
            elif word_len <= 2:
                return (2, word_len)
            else:
                return (1, -word_len)
        
        words.sort(key=word_priority)
        
        # 放置第一个单词
        first_word = words[0]
        start_row = grid_size // 2
        start_col = max(0, (grid_size - len(first_word.text)) // 2)
        
        if self._place_word(puzzle, first_word, start_row, start_col, "across"):
            self._answer_cache[first_word.id] = first_word.text
        
        placed_word_ids = {first_word.id}
        placed_word_objs = [first_word]
        
        # 多轮尝试放置更多单词
        max_attempts = 200
        attempt = 0
        
        while len(puzzle.placed_words) < target_words and attempt < max_attempts:
            attempt += 1
            
            # 筛选能与已放置单词交叉的词
            remaining_words = [w for w in words if w.id not in placed_word_ids]
            crossable = []
            for w in remaining_words:
                if self._can_cross_with_any(w, placed_word_objs):
                    crossable.append(w)
            
            # 如果没有可交叉的词，尝试使用所有剩余单词（放宽条件）
            if not crossable and len(puzzle.placed_words) < target_words:
                crossable = remaining_words[:20]  # 取前20个尝试
            
            if not crossable:
                break
            
            # 随机选一个尝试放置
            random.shuffle(crossable)
            placed_this_round = False
            for word in crossable:
                if self._try_place_word(puzzle, word):
                    self._answer_cache[word.id] = word.text
                    placed_word_ids.add(word.id)
                    placed_word_objs.append(word)
                    placed_this_round = True
                    break
            
            # 如果连续多次都无法放置新单词，退出
            if not placed_this_round and attempt > 50:
                break
        
        # 如果生成的单词太少，尝试用备用算法重新生成
        if len(puzzle.placed_words) < max(2, target_words // 2):
            return self._generate_puzzle_fallback(grid_size, word_list, target_words)
        
        return puzzle
    
    def _generate_puzzle_fallback(self, grid_size: int, word_list: List[dict], target_words: int) -> CrosswordPuzzle:
        """备用生成算法：使用更简单的放置策略"""
        puzzle = CrosswordPuzzle(grid_size=grid_size)
        
        # 转换词汇格式，优先选择3-5字母的纯字母词
        words = []
        for w in word_list:
            word_len = len(w["word"])
            if 3 <= word_len <= min(5, grid_size) and is_pure_alpha(w["word"]):
                words.append(Word(id=w["id"], text=w["word"].upper(), definition=w["definition"], difficulty=w.get("difficulty", 1)))
        
        if len(words) < 2:
            # 如果没有足够的3-5字母词，放宽条件
            for w in word_list:
                word_len = len(w["word"])
                if 2 <= word_len <= grid_size and is_pure_alpha(w["word"]):
                    words.append(Word(id=w["id"], text=w["word"].upper(), definition=w["definition"], difficulty=w.get("difficulty", 1)))
        
        if not words:
            return puzzle
        
        random.shuffle(words)
        
        # 放置第一个单词在中央
        first_word = words[0]
        row = grid_size // 2
        col = max(0, (grid_size - len(first_word.text)) // 2)
        
        if self._place_word(puzzle, first_word, row, col, "across"):
            self._answer_cache[first_word.id] = first_word.text
        
        placed_ids = {first_word.id}
        
        # 尝试放置其他单词
        for word in words[1:]:
            if len(puzzle.placed_words) >= target_words:
                break
            if word.id in placed_ids:
                continue
            
            # 尝试在已有单词上找交叉点
            for placed in puzzle.placed_words:
                if word.id in placed_ids:
                    break
                for i, letter1 in enumerate(placed.word.text):
                    for j, letter2 in enumerate(word.text):
                        if letter1 == letter2:
                            if placed.direction == "across":
                                new_row = placed.row - j
                                new_col = placed.col + i
                                new_dir = "down"
                            else:
                                new_row = placed.row + i
                                new_col = placed.col - j
                                new_dir = "across"
                            
                            if self._can_place(puzzle, word.text, new_row, new_col, new_dir):
                                if self._place_word(puzzle, word, new_row, new_col, new_dir):
                                    self._answer_cache[word.id] = word.text
                                    placed_ids.add(word.id)
                                    break
                    if word.id in placed_ids:
                        break
        
        return puzzle
    
    def _can_cross_with_any(self, word: Word, placed_words: List[Word]) -> bool:
        """检查单词是否能与任何已放置的单词交叉"""
        word_letters = set(word.text.upper())
        for pw in placed_words:
            placed_letters = set(pw.text.upper())
            if word_letters & placed_letters:  # 有共同字母
                return True
        return False
    
    def generate_random_puzzle(self, group: str, difficulty: str, vocab_manager) -> dict:
        """生成随机关卡"""
        config = self.DIFFICULTY_CONFIG.get(difficulty, self.DIFFICULTY_CONFIG["medium"])
        grid_size, min_words, max_words, max_word_len = config
        num_words = random.randint(min_words, max_words)
        
        # 获取完整词库用于交叉验证
        if hasattr(vocab_manager, 'get_all_words_for_csp'):
            all_words = vocab_manager.get_all_words_for_csp(group)
        else:
            all_words = vocab_manager.get_words(group, limit=10000)
        self._build_valid_words_set(all_words)
        
        # 增加重试机制，确保生成至少 min_words 个单词
        max_retries = 5
        best_puzzle = None
        best_word_count = 0
        
        for retry in range(max_retries):
            # 获取词汇（优先获取适合网格大小的词汇），每次重试打乱顺序
            words = vocab_manager.get_words_for_puzzle(group, num_words * 5, max_word_len)
            random.shuffle(words)
            
            # 使用改进的算法生成谜题（带交叉验证）
            puzzle = self._generate_puzzle_with_crossable_words(grid_size, words, num_words)
            
            word_count = len(puzzle.placed_words)
            
            # 如果达到目标数量，直接使用
            if word_count >= min_words:
                best_puzzle = puzzle
                break
            
            # 记录最好的结果
            if word_count > best_word_count:
                best_word_count = word_count
                best_puzzle = puzzle
        
        # 使用最好的结果
        puzzle = best_puzzle
        
        # 添加预填字母（无额外加成）
        self._add_prefilled_letters(puzzle, difficulty, 0.0)
        
        result = puzzle.to_dict()
        result["level"] = 0  # 随机关卡
        result["difficulty"] = difficulty
        result["group"] = group
        
        return result
    
    def _add_prefilled_letters(self, puzzle: CrosswordPuzzle, difficulty: str, prefill_boost: float = 0.0):
        """为每个单词添加预填字母（增强版：智能处理交叉点）
        
        Args:
            puzzle: 谜题对象
            difficulty: 难度级别
            prefill_boost: 额外的预填比例加成（用于新手关卡）
        """
        min_ratio, max_ratio = self.PREFILL_RATIO.get(difficulty, (0.3, 0.5))
        # 应用额外加成
        min_ratio = min(0.9, min_ratio + prefill_boost)
        max_ratio = min(0.95, max_ratio + prefill_boost)
        
        # 首先找出所有交叉点
        intersection_cells: Dict[str, Set[int]] = {}  # key -> set of word_ids
        for pw in puzzle.placed_words:
            for i in range(len(pw.word.text)):
                if pw.direction == 'across':
                    r, c = pw.row, pw.col + i
                else:
                    r, c = pw.row + i, pw.col
                key = f"{r}-{c}"
                if key not in intersection_cells:
                    intersection_cells[key] = set()
                intersection_cells[key].add(pw.word.id)
        
        # 找出真正的交叉点（被多个单词共享的格子）
        true_intersections = {k for k, v in intersection_cells.items() if len(v) >= 2}
        
        for pw in puzzle.placed_words:
            word_len = len(pw.word.text)
            
            # 根据单词长度调整预填比例（短词预填更多）
            length_factor = min(1.0, 3 / word_len)
            adjusted_min = min_ratio + (max_ratio - min_ratio) * length_factor * 0.5
            adjusted_max = max_ratio + (1.0 - max_ratio) * length_factor * 0.3
            
            adjusted_min = max(0.2, min(0.8, adjusted_min))
            adjusted_max = max(adjusted_min, min(0.8, adjusted_max))
            
            prefill_ratio = random.uniform(adjusted_min, adjusted_max)
            num_prefill = max(1, int(word_len * prefill_ratio))
            
            # 确保至少预填2个字母（2字母单词至少预填1个）
            if word_len == 2:
                num_prefill = max(1, num_prefill)
            else:
                num_prefill = max(2, num_prefill)
            
            # 确保至少保留1个字母让用户填
            num_prefill = min(num_prefill, word_len - 1)
            
            # 收集这个单词的所有位置及其属性
            positions_info = []
            for i in range(word_len):
                if pw.direction == 'across':
                    r, c = pw.row, pw.col + i
                else:
                    r, c = pw.row + i, pw.col
                key = f"{r}-{c}"
                is_intersection = key in true_intersections
                already_prefilled = key in puzzle.prefilled
                positions_info.append({
                    'index': i,
                    'key': key,
                    'letter': pw.word.text[i],
                    'is_intersection': is_intersection,
                    'already_prefilled': already_prefilled
                })
            
            # 优先选择策略：
            # 1. 已经被预填的交叉点（不用重复处理）
            # 2. 未预填的交叉点（这些字母在两个单词中都需要）
            # 3. 普通位置
            
            # 统计已经被预填的位置数
            already_filled_count = sum(1 for p in positions_info if p['already_prefilled'])
            remaining_to_fill = max(0, num_prefill - already_filled_count)
            
            if remaining_to_fill > 0:
                # 未预填的位置
                unfilled_positions = [p for p in positions_info if not p['already_prefilled']]
                
                # 先选交叉点，再选普通位置
                intersect_unfilled = [p for p in unfilled_positions if p['is_intersection']]
                normal_unfilled = [p for p in unfilled_positions if not p['is_intersection']]
                
                random.shuffle(intersect_unfilled)
                random.shuffle(normal_unfilled)
                
                # 交叉点优先预填（因为一次预填可以帮助两个单词）
                to_fill = intersect_unfilled[:remaining_to_fill]
                if len(to_fill) < remaining_to_fill:
                    to_fill.extend(normal_unfilled[:remaining_to_fill - len(to_fill)])
                
                for p in to_fill:
                    puzzle.prefilled[p['key']] = p['letter']
    
    def _generate_puzzle(self, grid_size: int, word_list: List[dict], target_words: int) -> CrosswordPuzzle:
        """核心谜题生成算法（带重试机制）"""
        # 最多尝试3次，每次扩大网格尺寸
        for attempt in range(3):
            current_grid_size = grid_size + attempt * 2
            puzzle = self._try_generate_puzzle(current_grid_size, word_list, target_words)
            
            # 如果生成了足够的单词（至少达到目标的一半或最小2个），就返回
            min_required = max(2, target_words // 2)
            if len(puzzle.placed_words) >= min_required:
                return puzzle
        
        # 返回最后一次尝试的结果
        return puzzle
    
    def _try_generate_puzzle(self, grid_size: int, word_list: List[dict], target_words: int) -> CrosswordPuzzle:
        """尝试生成谜题（增强版：支持10x10高阶表格）"""
        puzzle = CrosswordPuzzle(grid_size=grid_size)
        
        # 转换词汇格式（过滤含非字母字符的单词）
        words = [
            Word(id=w["id"], text=w["word"].upper(), definition=w["definition"], difficulty=w.get("difficulty", 1))
            for w in word_list
            if 2 <= len(w["word"]) <= grid_size and is_pure_alpha(w["word"])
        ]
        
        if not words:
            return puzzle
        
        # 智能排序：中等长度优先（3-5字母），因为更容易找到交叉点
        # 太长的词难以放置，太短的词交叉点少
        def word_priority(w):
            word_len = len(w.text)
            # 优先选择3-6字母的单词
            if 3 <= word_len <= 6:
                return (0, -word_len)  # 优先级最高，长的优先
            elif word_len <= 2:
                return (2, word_len)  # 最低优先级
            else:
                return (1, -word_len)  # 中等优先级
        
        words.sort(key=word_priority)
        
        # 对于大网格（8x8及以上），重新排序策略
        if grid_size >= 8:
            # 先按长度降序，但不要选太长的
            max_preferred_len = min(grid_size - 2, 7)
            words.sort(key=lambda w: (
                0 if len(w.text) <= max_preferred_len else 1,
                -len(w.text)
            ))
        
        # 放置第一个单词（居中放置）
        first_word = words[0]
        start_row = grid_size // 2
        start_col = max(0, (grid_size - len(first_word.text)) // 2)
        
        if self._place_word(puzzle, first_word, start_row, start_col, "across"):
            self._answer_cache[first_word.id] = first_word.text
        
        # 尝试放置更多单词
        max_attempts = 300 if grid_size >= 8 else 200
        placed_word_ids = {first_word.id}
        
        # 多轮尝试，每轮打乱顺序
        for round_num in range(3):
            if len(puzzle.placed_words) >= target_words:
                break
            
            remaining_words = [w for w in words if w.id not in placed_word_ids]
            if round_num > 0:
                random.shuffle(remaining_words)
            
            for word in remaining_words:
                if len(puzzle.placed_words) >= target_words:
                    break
                
                # 尝试找到交叉点
                placed = self._try_place_word(puzzle, word)
                if placed:
                    self._answer_cache[word.id] = word.text
                    placed_word_ids.add(word.id)
        
        return puzzle
    
    def _place_word(self, puzzle: CrosswordPuzzle, word: Word, row: int, col: int, direction: str) -> bool:
        """放置单词到网格"""
        # 检查是否可以放置
        if not self._can_place(puzzle, word.text, row, col, direction):
            return False
        
        # 放置单词
        for i, letter in enumerate(word.text):
            if direction == "across":
                puzzle.grid[row][col + i] = letter
            else:  # down
                puzzle.grid[row + i][col] = letter
        
        puzzle.placed_words.append(PlacedWord(word, row, col, direction))
        return True
    
    def _can_place(self, puzzle: CrosswordPuzzle, text: str, row: int, col: int, direction: str) -> bool:
        """检查是否可以在指定位置放置单词（增强版：支持多交叉点 + 交叉验证）"""
        word_len = len(text)
        
        # 首先检查整体边界
        if direction == "across":
            if row < 0 or row >= puzzle.grid_size:
                return False
            if col < 0 or col + word_len > puzzle.grid_size:
                return False
        else:
            if col < 0 or col >= puzzle.grid_size:
                return False
            if row < 0 or row + word_len > puzzle.grid_size:
                return False
        
        has_intersection = False  # 必须至少有一个交叉点（除了第一个单词）
        
        for i, letter in enumerate(text):
            if direction == "across":
                r, c = row, col + i
            else:
                r, c = row + i, col
            
            existing = puzzle.grid[r][c]
            
            # 如果格子已有字母
            if existing is not None:
                if existing != letter:
                    return False  # 字母冲突
                else:
                    has_intersection = True  # 有效交叉点
            else:
                # 格子为空，需要检查相邻格子是否有平行的单词冲突
                if not self._check_adjacent_conflict(puzzle, r, c, direction):
                    return False
        
        # 检查单词首尾是否与其他单词相连（不允许尾部直接连接）
        if direction == "across":
            # 检查左侧
            if col > 0 and puzzle.grid[row][col - 1] is not None:
                return False
            # 检查右侧
            end_col = col + word_len
            if end_col < puzzle.grid_size and puzzle.grid[row][end_col] is not None:
                return False
        else:
            # 检查上方
            if row > 0 and puzzle.grid[row - 1][col] is not None:
                return False
            # 检查下方
            end_row = row + word_len
            if end_row < puzzle.grid_size and puzzle.grid[end_row][col] is not None:
                return False
        
        # 第一个单词不需要交叉点
        if len(puzzle.placed_words) == 0:
            return True
        
        if not has_intersection:
            return False
        
        # 交叉验证：检查放置后是否会形成无效的字母序列
        if self._valid_words_set:  # 只有在有有效单词集合时才验证
            if not self._validate_cross_sequences(puzzle, text, row, col, direction):
                return False
        
        return True
    
    def _validate_cross_sequences(self, puzzle: CrosswordPuzzle, text: str, 
                                   row: int, col: int, direction: str) -> bool:
        """
        交叉验证：检查放置单词后是否会形成无效的字母序列
        
        只检查垂直于放置方向的序列
        """
        word_len = len(text)
        
        # 创建临时网格
        temp_grid = [r[:] if r else [None] * puzzle.grid_size for r in puzzle.grid]
        for i, letter in enumerate(text):
            if direction == "across":
                temp_grid[row][col + i] = letter
            else:
                temp_grid[row + i][col] = letter
        
        # 检查垂直于放置方向的序列
        for i in range(word_len):
            if direction == "across":
                r, c = row, col + i
                # 检查垂直序列
                seq = self._get_vertical_sequence(temp_grid, r, c, puzzle.grid_size)
            else:
                r, c = row + i, col
                # 检查水平序列
                seq = self._get_horizontal_sequence(temp_grid, r, c, puzzle.grid_size)
            
            # 如果形成了2个及以上字母的序列，必须是有效单词
            if len(seq) >= 2:
                if not self._is_valid_word(seq):
                    return False
        
        return True
    
    def _get_vertical_sequence(self, grid: List[List], row: int, col: int, grid_size: int) -> str:
        """获取包含指定位置的垂直连续字母序列"""
        # 向上找起点
        start_row = row
        while start_row > 0 and grid[start_row - 1][col]:
            start_row -= 1
        
        # 向下收集序列
        seq = ""
        r = start_row
        while r < grid_size and grid[r][col]:
            seq += grid[r][col]
            r += 1
        
        return seq
    
    def _get_horizontal_sequence(self, grid: List[List], row: int, col: int, grid_size: int) -> str:
        """获取包含指定位置的水平连续字母序列"""
        # 向左找起点
        start_col = col
        while start_col > 0 and grid[row][start_col - 1]:
            start_col -= 1
        
        # 向右收集序列
        seq = ""
        c = start_col
        while c < grid_size and grid[row][c]:
            seq += grid[row][c]
            c += 1
        
        return seq
    
    def _check_adjacent_conflict(self, puzzle: CrosswordPuzzle, row: int, col: int, direction: str) -> bool:
        """检查相邻格子是否有平行方向的冲突"""
        if direction == "across":
            # 横向放置时，检查上下是否有字母（会造成不期望的并行单词）
            has_above = row > 0 and puzzle.grid[row - 1][col] is not None
            has_below = row < puzzle.grid_size - 1 and puzzle.grid[row + 1][col] is not None
            # 如果上下都有字母，说明这个位置可能是另一个纵向单词的一部分
            # 这种情况我们允许，因为可能是真正的交叉点
            # 但如果只有一边有字母，可能会造成意外的单词组合
            if has_above and not has_below:
                # 检查上方是否是纵向单词的延续
                return self._is_part_of_vertical_word(puzzle, row - 1, col)
            if has_below and not has_above:
                return self._is_part_of_vertical_word(puzzle, row + 1, col)
        else:
            # 纵向放置时，检查左右
            has_left = col > 0 and puzzle.grid[row][col - 1] is not None
            has_right = col < puzzle.grid_size - 1 and puzzle.grid[row][col + 1] is not None
            if has_left and not has_right:
                return self._is_part_of_horizontal_word(puzzle, row, col - 1)
            if has_right and not has_left:
                return self._is_part_of_horizontal_word(puzzle, row, col + 1)
        
        return True
    
    def _is_part_of_vertical_word(self, puzzle: CrosswordPuzzle, row: int, col: int) -> bool:
        """检查指定位置是否是纵向单词的一部分"""
        for pw in puzzle.placed_words:
            if pw.direction == "down" and pw.col == col:
                if pw.row <= row <= pw.end_row:
                    return True
        return False
    
    def _is_part_of_horizontal_word(self, puzzle: CrosswordPuzzle, row: int, col: int) -> bool:
        """检查指定位置是否是横向单词的一部分"""
        for pw in puzzle.placed_words:
            if pw.direction == "across" and pw.row == row:
                if pw.col <= col <= pw.end_col:
                    return True
        return False
    
    def _try_place_word(self, puzzle: CrosswordPuzzle, word: Word) -> bool:
        """尝试在谜题中放置单词（增强版：支持多交叉点）"""
        # 收集所有可能的放置位置
        possible_placements = []
        
        # 方法1：遍历已放置的单词，寻找共同字母
        for placed in puzzle.placed_words:
            for i, letter1 in enumerate(placed.word.text):
                for j, letter2 in enumerate(word.text):
                    if letter1 == letter2:
                        # 找到共同字母，尝试交叉放置
                        if placed.direction == "across":
                            # 已放置的是横向，新单词尝试纵向
                            new_row = placed.row - j
                            new_col = placed.col + i
                            new_dir = "down"
                        else:
                            # 已放置的是纵向，新单词尝试横向
                            new_row = placed.row + i
                            new_col = placed.col - j
                            new_dir = "across"
                        
                        # 检查是否可以放置
                        if self._can_place(puzzle, word.text, new_row, new_col, new_dir):
                            # 计算这个放置的质量分数（交叉点越多越好）
                            score = self._calculate_placement_score(puzzle, word.text, new_row, new_col, new_dir)
                            if score >= 0:
                                possible_placements.append((new_row, new_col, new_dir, score))
        
        # 方法2：尝试在网格中寻找能形成多个交叉点的位置
        if len(puzzle.placed_words) >= 2:
            for r in range(puzzle.grid_size):
                for c in range(puzzle.grid_size):
                    for direction in ["across", "down"]:
                        if self._can_place(puzzle, word.text, r, c, direction):
                            score = self._calculate_placement_score(puzzle, word.text, r, c, direction)
                            if score >= 10:  # 至少要有一个交叉点
                                possible_placements.append((r, c, direction, score))
        
        # 去重并按分数排序
        seen = set()
        unique_placements = []
        for p in possible_placements:
            key = (p[0], p[1], p[2])
            if key not in seen:
                seen.add(key)
                unique_placements.append(p)
        
        if unique_placements:
            unique_placements.sort(key=lambda x: x[3], reverse=True)
            best = unique_placements[0]
            return self._place_word(puzzle, word, best[0], best[1], best[2])
        
        return False
    
    def _calculate_placement_score(self, puzzle: CrosswordPuzzle, text: str, row: int, col: int, direction: str) -> int:
        """计算放置位置的质量分数（增强版：多交叉点奖励）"""
        score = 0
        intersection_count = 0
        word_len = len(text)
        
        for i, letter in enumerate(text):
            if direction == "across":
                r, c = row, col + i
            else:
                r, c = row + i, col
            
            # 边界检查
            if r < 0 or r >= puzzle.grid_size or c < 0 or c >= puzzle.grid_size:
                return -1
            
            # 如果格子已有相同字母，增加分数（交叉点）
            existing = puzzle.grid[r][c]
            if existing is not None:
                if existing == letter:
                    intersection_count += 1
                    # 交叉点越多，奖励越高（指数增长）
                    score += 15 * intersection_count
                else:
                    return -1  # 字母冲突
        
        # 第一个单词后必须有交叉点
        if len(puzzle.placed_words) > 0 and intersection_count == 0:
            return -1
        
        # 多交叉点额外奖励（对于10x10大网格尤为重要）
        if intersection_count >= 2:
            score += 30 * intersection_count
        if intersection_count >= 3:
            score += 50  # 三个及以上交叉点的超级奖励
        
        # 靠近中心的位置加分
        center = puzzle.grid_size // 2
        if direction == "across":
            word_center_row = row
            word_center_col = col + word_len // 2
        else:
            word_center_row = row + word_len // 2
            word_center_col = col
        
        distance_from_center = abs(word_center_row - center) + abs(word_center_col - center)
        score -= distance_from_center * 2
        
        # 较长的单词有轻微加分（更容易形成交叉）
        score += word_len
        
        # 平衡横纵方向（避免都是一个方向）
        across_count = sum(1 for pw in puzzle.placed_words if pw.direction == "across")
        down_count = len(puzzle.placed_words) - across_count
        if direction == "across" and down_count > across_count:
            score += 5
        elif direction == "down" and across_count > down_count:
            score += 5
        
        return score
    
    def _get_difficulty_name(self, level: int) -> str:
        """根据关卡获取难度名称"""
        if level <= 32:
            return "easy"
        elif level <= 128:
            return "medium"
        else:
            return "hard"
    
    def verify_answer(self, word_id: int, answer: str) -> dict:
        """验证答案"""
        correct_answer = self._answer_cache.get(word_id, "")
        is_correct = answer.upper() == correct_answer.upper()
        
        return {
            "correct": is_correct,
            "word": correct_answer if is_correct else "",
            "definition": ""  # 可以从缓存获取
        }
    
    def validate_puzzle(self, puzzle_dict: dict) -> Tuple[bool, List[str]]:
        """
        验证生成的谜题是否正确
        
        检查项：
        1. 每个单词的长度与实际格子数匹配
        2. 单词内容与格子中的字母匹配
        3. 单词不超出网格边界
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        grid_size = puzzle_dict.get("grid_size", 0)
        cells = puzzle_dict.get("cells", [])
        words = puzzle_dict.get("words", [])
        
        for word_info in words:
            word = word_info.get("word", "")
            direction = word_info.get("direction", "")
            start_row = word_info.get("start_row", 0)
            start_col = word_info.get("start_col", 0)
            length = word_info.get("length", 0)
            clue_num = word_info.get("clue_number", "?")
            
            # 检查声明的长度与实际单词长度是否匹配
            if length != len(word):
                errors.append(f"单词{clue_num}({word}): 声明长度{length}与实际长度{len(word)}不匹配")
            
            # 检查边界
            if direction == "across":
                if start_col + len(word) > grid_size:
                    errors.append(f"单词{clue_num}({word}): 横向超出右边界")
                if start_row < 0 or start_row >= grid_size:
                    errors.append(f"单词{clue_num}({word}): 行号{start_row}超出边界")
            else:  # down
                if start_row + len(word) > grid_size:
                    errors.append(f"单词{clue_num}({word}): 纵向超出下边界")
                if start_col < 0 or start_col >= grid_size:
                    errors.append(f"单词{clue_num}({word}): 列号{start_col}超出边界")
            
            # 统计实际格子数
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
    
    def reseed(self, seed: int = None):
        """重新设置随机种子以确保随机性"""
        if seed is None:
            seed = int(time.time() * 1000000) % (2**31)
        random.seed(seed)
        self._random_seed = seed
        return seed
