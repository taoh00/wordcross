"""
CSP (约束满足问题) 填字游戏关卡生成器

实现改进的填字游戏生成：
- 支持稀疏和密集两种布局
- 交叉验证：确保所有横向纵向形成的字母组合都是有效单词
- 密度控制：使用密度(>=35%)而不是数量衡量
- 单词长度多样化：长短不一搭配
- 字母展示：每个单词展示2个以上字母但不能全展示，红色标记

核心算法：
1. 单词级CSP建模 - 变量是行/列的单词槽位
2. AC-3弧一致性约束传播
3. 回溯搜索 + MRV启发式
4. 前向检查优化
5. 交叉验证 - 验证所有连续字母序列是有效单词
"""
import random
import time
from typing import List, Dict, Tuple, Optional, Set, FrozenSet
from dataclasses import dataclass, field
from collections import defaultdict
from copy import deepcopy


def is_pure_alpha(word: str) -> bool:
    """检查单词是否只包含26个英文字母（不含连字符、撇号、空格等）
    
    无效单词示例：
    - X-RAY, T-SHIRT（含连字符）
    - O'CLOCK, WE'LL（含撇号）
    - ICE CREAM（含空格）
    """
    return word.isalpha()


@dataclass
class WordSlot:
    """单词槽位 - CSP中的变量"""
    id: str                          # 唯一标识，如 "row_0" 或 "col_3"
    direction: str                   # "across" 或 "down"
    index: int                       # 行号或列号
    length: int                      # 单词长度（等于网格大小）
    domain: List[str] = field(default_factory=list)  # 可选单词域
    assigned_word: Optional[str] = None  # 已分配的单词


@dataclass
class CSPConstraint:
    """CSP约束 - 两个单词槽位在某位置必须字母相同"""
    slot1_id: str      # 第一个槽位ID
    slot2_id: str      # 第二个槽位ID
    pos1: int          # 槽位1中的字母位置
    pos2: int          # 槽位2中的字母位置


@dataclass
class DensePuzzle:
    """密集填字游戏谜题"""
    grid_size: int
    grid: List[List[str]] = field(default_factory=list)
    row_words: List[dict] = field(default_factory=list)  # 横向单词信息
    col_words: List[dict] = field(default_factory=list)  # 纵向单词信息
    revealed_positions: Set[Tuple[int, int]] = field(default_factory=set)  # 展示的字母位置（红色）
    
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
        4. 返回展示的位置集合
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
        
        # 找出交叉点（被多个单词共用的位置）
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
                # 2字母单词：展示1个
                num_reveal = 1
            else:
                # 展示至少2个，但不超过 word_len - 1
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
                # 优先选择交叉点
                unrevealed = [pos for pos in word_positions if pos not in self.revealed_positions]
                crossing_unrevealed = [pos for pos in unrevealed if pos in crossings]
                non_crossing_unrevealed = [pos for pos in unrevealed if pos not in crossings]
                
                # 随机选择
                to_reveal = []
                random.shuffle(crossing_unrevealed)
                random.shuffle(non_crossing_unrevealed)
                
                # 先选交叉点
                to_reveal.extend(crossing_unrevealed[:need_to_reveal])
                remaining = need_to_reveal - len(to_reveal)
                
                # 再选非交叉点
                if remaining > 0:
                    to_reveal.extend(non_crossing_unrevealed[:remaining])
                
                # 确保不会全部展示
                if len(to_reveal) + already_revealed >= word_len:
                    # 至少保留一个不展示
                    to_reveal = to_reveal[:word_len - already_revealed - 1]
                
                for pos in to_reveal:
                    self.revealed_positions.add(pos)
    
    def to_dict(self) -> dict:
        """转换为API响应格式"""
        words = []
        clue_number = 1
        
        # 添加所有单词（按位置排序）
        all_word_info = []
        
        for word_info in self.row_words:
            # 支持新格式（带row/col）和旧格式（按索引）
            if isinstance(word_info, dict) and 'row' in word_info:
                all_word_info.append({
                    "row": word_info['row'], 
                    "col": word_info['col'], 
                    "direction": "across", 
                    "info": word_info
                })
            else:
                i = self.row_words.index(word_info)
                all_word_info.append({
                    "row": i, "col": 0, "direction": "across", "info": word_info
                })
        
        for word_info in self.col_words:
            if isinstance(word_info, dict) and 'row' in word_info:
                all_word_info.append({
                    "row": word_info['row'], 
                    "col": word_info['col'], 
                    "direction": "down", 
                    "info": word_info
                })
            else:
                j = self.col_words.index(word_info)
                all_word_info.append({
                    "row": 0, "col": j, "direction": "down", "info": word_info
                })
        
        # 按位置排序（行优先，列次之）
        all_word_info.sort(key=lambda x: (x["row"], x["col"], 0 if x["direction"] == "across" else 1))
        
        # 分配线索编号
        position_clue_map = {}  # (row, col) -> clue_number
        
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
        revealed_grid = []  # 标记哪些位置是展示的（红色）
        
        for i, row in enumerate(self.grid):
            masked_row = []
            revealed_row = []
            for j, cell in enumerate(row):
                if cell:
                    pos = (i, j)
                    if pos in self.revealed_positions:
                        # 展示的字母
                        masked_row.append(cell)
                        revealed_row.append(True)
                    else:
                        # 需要填写的字母
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
        
        # 创建 prefilled 字典，格式为 {"row-col": "letter"}
        # 将 revealed_positions 转换为前端期望的格式
        prefilled = {}
        for i, row in enumerate(self.grid):
            for j, cell in enumerate(row):
                if cell and (i, j) in self.revealed_positions:
                    prefilled[f"{i}-{j}"] = cell
        
        return {
            "grid_size": self.grid_size,
            "cells": masked_grid,
            "revealed": revealed_grid,  # 展示的字母位置（用于红色标记）
            "words": words,
            "prefilled": prefilled,  # 预填字母字典
            "clue_numbers": clue_number_grid,
            "puzzle_type": "template",  # 标识为模板填字类型
            "density": self.calculate_density()  # 密度信息
        }


class WordValidator:
    """
    单词验证器 - 快速验证字母序列是否是有效单词
    
    用于交叉验证：确保横向纵向形成的所有字母组合都是有效单词
    """
    
    def __init__(self, words: List[dict]):
        # 构建有效单词集合（大写）
        self.valid_words: Set[str] = set()
        for w in words:
            word = w["word"].upper()
            if len(word) >= 2:
                self.valid_words.add(word)
    
    def is_valid_word(self, text: str) -> bool:
        """检查是否是有效单词"""
        return text.upper() in self.valid_words
    
    def is_valid_or_partial(self, text: str) -> bool:
        """检查是否是有效单词或可能是有效单词的前缀"""
        text_upper = text.upper()
        if text_upper in self.valid_words:
            return True
        # 检查是否是某个单词的前缀
        for word in self.valid_words:
            if word.startswith(text_upper):
                return True
        return False


class WordIndex:
    """
    单词索引 - 为CSP提供高效的单词查询
    
    支持：
    1. 按长度查询所有单词
    2. 按位置和字母查询兼容单词
    3. 预过滤不可行单词
    4. 验证字母序列是否是有效单词（交叉验证）
    """
    
    def __init__(self, words: List[dict]):
        self.words = words
        self.by_length: Dict[int, List[str]] = defaultdict(list)
        self.word_to_info: Dict[str, dict] = {}
        self.valid_words_set: Set[str] = set()  # 用于快速验证
        
        # 按长度索引（过滤特殊字符）
        for w in words:
            word = w["word"].upper()
            # 只接受纯字母单词，过滤含撇号、连字符等特殊字符的单词
            if 2 <= len(word) <= 15 and is_pure_alpha(word):
                self.by_length[len(word)].append(word)
                self.word_to_info[word] = w
                self.valid_words_set.add(word)
        
        # 预计算：按位置-字母索引
        # position_letter_index[length][(pos, letter)] = set of words
        self.position_letter_index: Dict[int, Dict[Tuple[int, str], Set[str]]] = {}
        for length, word_list in self.by_length.items():
            self.position_letter_index[length] = defaultdict(set)
            for word in word_list:
                for pos, letter in enumerate(word):
                    self.position_letter_index[length][(pos, letter)].add(word)
    
    def is_valid_word(self, text: str) -> bool:
        """检查字母序列是否是有效单词"""
        return text.upper() in self.valid_words_set
    
    def get_feasible_words_for_dense(self, grid_size: int) -> List[str]:
        """
        获取能够参与密集填字的可行单词
        
        预过滤策略：每个单词的每个位置的字母都必须在其他单词的对应位置出现过
        """
        all_words = self.by_length.get(grid_size, [])
        if not all_words:
            return []
        
        # 统计每个位置的字母分布
        position_letters: Dict[int, Set[str]] = defaultdict(set)
        for word in all_words:
            for pos, letter in enumerate(word):
                position_letters[pos].add(letter)
        
        # 过滤单词：每个位置的字母必须在其他位置也有足够的支持
        feasible = []
        for word in all_words:
            is_feasible = True
            for i, letter in enumerate(word):
                # 这个字母需要作为其他单词在位置i的字母出现
                # 即需要有单词w使得w[i] == letter，这样才能在(i,j)位置交叉
                if letter not in position_letters[i]:
                    is_feasible = False
                    break
            if is_feasible:
                feasible.append(word)
        
        return feasible
    
    def get_words_by_length(self, length: int) -> List[str]:
        """获取指定长度的所有单词"""
        return self.by_length.get(length, [])
    
    def get_compatible_words(self, length: int, constraints: List[Tuple[int, str]]) -> List[str]:
        """
        获取满足约束的单词
        constraints: [(position, letter), ...] - 必须在position位置有letter字母
        """
        if length not in self.position_letter_index:
            return []
        
        if not constraints:
            return self.by_length.get(length, [])
        
        # 取交集
        result = None
        for pos, letter in constraints:
            words_with_letter = self.position_letter_index[length].get((pos, letter), set())
            if result is None:
                result = words_with_letter.copy()
            else:
                result &= words_with_letter
            
            if not result:
                return []
        
        return list(result)
    
    def get_word_info(self, word: str) -> Optional[dict]:
        """获取单词的详细信息"""
        return self.word_to_info.get(word.upper())


class CSPSolver:
    """
    CSP求解器 - 使用回溯搜索 + 约束传播生成密集填字游戏
    
    建模方式：
    - 变量：n行 + n列 = 2n个单词槽位
    - 域：每个槽位的可选单词（长度为n的词）
    - 约束：行i与列j在位置(i,j)的字母必须相同
    """
    
    def __init__(self, word_index: WordIndex, grid_size: int):
        self.word_index = word_index
        self.grid_size = grid_size
        self.slots: Dict[str, WordSlot] = {}
        self.constraints: List[CSPConstraint] = []
        self.constraint_graph: Dict[str, List[CSPConstraint]] = defaultdict(list)
        
        self._init_slots()
        self._init_constraints()
        
        # 统计
        self.backtracks = 0
        self.nodes_explored = 0
    
    def _init_slots(self):
        """初始化单词槽位"""
        # 使用预过滤的可行单词
        words = self.word_index.get_feasible_words_for_dense(self.grid_size)
        if not words:
            words = self.word_index.get_words_by_length(self.grid_size)
        
        # 随机打乱以增加多样性
        words = words.copy()
        random.shuffle(words)
        
        # 行槽位
        for i in range(self.grid_size):
            slot_id = f"row_{i}"
            self.slots[slot_id] = WordSlot(
                id=slot_id,
                direction="across",
                index=i,
                length=self.grid_size,
                domain=words.copy()
            )
        
        # 列槽位
        for j in range(self.grid_size):
            slot_id = f"col_{j}"
            self.slots[slot_id] = WordSlot(
                id=slot_id,
                direction="down",
                index=j,
                length=self.grid_size,
                domain=words.copy()
            )
    
    def _init_constraints(self):
        """初始化约束 - 每个(row_i, col_j)在位置(j, i)必须字母相同"""
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                row_slot = f"row_{i}"
                col_slot = f"col_{j}"
                
                constraint = CSPConstraint(
                    slot1_id=row_slot,
                    slot2_id=col_slot,
                    pos1=j,    # 行单词在位置j的字母
                    pos2=i     # 列单词在位置i的字母
                )
                
                self.constraints.append(constraint)
                self.constraint_graph[row_slot].append(constraint)
                self.constraint_graph[col_slot].append(constraint)
    
    def solve(self, timeout_seconds: float = 5.0, use_ac3: bool = False) -> Optional[Dict[str, str]]:
        """
        求解CSP问题
        
        Args:
            timeout_seconds: 超时时间
            use_ac3: 是否使用AC-3预处理（对于小词库可能过于激进）
        
        Returns:
            成功时返回 {slot_id: word} 的分配字典
            失败时返回 None
        """
        start_time = time.time()
        self.backtracks = 0
        self.nodes_explored = 0
        
        # 初始化域（随机打乱以增加多样性）
        domains = {}
        for slot_id, slot in self.slots.items():
            domain = slot.domain.copy()
            random.shuffle(domain)
            domains[slot_id] = domain
        
        # AC-3初始化（可选 - 对于小词库可能过于激进）
        if use_ac3:
            if not self._ac3(domains):
                return None
        
        # 回溯搜索
        assignment = {}
        result = self._backtrack(assignment, domains, start_time, timeout_seconds)
        
        return result
    
    def _backtrack(self, assignment: Dict[str, str], domains: Dict[str, List[str]], 
                   start_time: float, timeout: float) -> Optional[Dict[str, str]]:
        """回溯搜索"""
        # 超时检查
        if time.time() - start_time > timeout:
            return None
        
        self.nodes_explored += 1
        
        # 检查是否完成
        if len(assignment) == len(self.slots):
            return assignment
        
        # 选择变量（MRV启发式 - 最少剩余值）
        var = self._select_unassigned_variable(assignment, domains)
        if var is None:
            return None
        
        # 尝试域中的每个值（可以用LCV启发式排序）
        values = self._order_domain_values(var, domains)
        
        for value in values:
            # 检查一致性
            if self._is_consistent(var, value, assignment):
                # 分配
                assignment[var] = value
                
                # 保存域状态用于回溯
                saved_domains = {k: v.copy() for k, v in domains.items()}
                domains[var] = [value]
                
                # 前向检查 + MAC (Maintaining Arc Consistency)
                if self._forward_check(var, value, domains):
                    result = self._backtrack(assignment, domains, start_time, timeout)
                    if result is not None:
                        return result
                
                # 回溯
                del assignment[var]
                domains.clear()
                domains.update(saved_domains)
                self.backtracks += 1
        
        return None
    
    def _select_unassigned_variable(self, assignment: Dict[str, str], 
                                    domains: Dict[str, List[str]]) -> Optional[str]:
        """MRV启发式选择变量 - 选择域最小的未分配变量"""
        unassigned = [v for v in self.slots if v not in assignment]
        
        if not unassigned:
            return None
        
        # MRV: 选择域最小的
        return min(unassigned, key=lambda v: len(domains.get(v, [])))
    
    def _order_domain_values(self, var: str, domains: Dict[str, List[str]]) -> List[str]:
        """
        LCV启发式排序值 - 选择最少约束其他变量的值
        简化版本：随机打乱以增加多样性
        """
        values = domains.get(var, []).copy()
        random.shuffle(values)
        return values
    
    def _is_consistent(self, var: str, value: str, assignment: Dict[str, str]) -> bool:
        """检查赋值是否与现有分配一致"""
        for constraint in self.constraint_graph[var]:
            if constraint.slot1_id == var:
                other_var = constraint.slot2_id
                pos_self = constraint.pos1
                pos_other = constraint.pos2
            else:
                other_var = constraint.slot1_id
                pos_self = constraint.pos2
                pos_other = constraint.pos1
            
            if other_var in assignment:
                other_value = assignment[other_var]
                if value[pos_self] != other_value[pos_other]:
                    return False
        
        return True
    
    def _forward_check(self, var: str, value: str, domains: Dict[str, List[str]]) -> bool:
        """前向检查 - 削减相邻变量的域"""
        for constraint in self.constraint_graph[var]:
            if constraint.slot1_id == var:
                other_var = constraint.slot2_id
                pos_self = constraint.pos1
                pos_other = constraint.pos2
            else:
                other_var = constraint.slot1_id
                pos_self = constraint.pos2
                pos_other = constraint.pos1
            
            if other_var in domains and len(domains[other_var]) > 1:
                required_letter = value[pos_self]
                
                # 过滤域
                new_domain = [w for w in domains[other_var] 
                             if w[pos_other] == required_letter]
                
                if not new_domain:
                    return False
                
                domains[other_var] = new_domain
        
        return True
    
    def _ac3(self, domains: Dict[str, List[str]]) -> bool:
        """AC-3弧一致性算法"""
        queue = list(self.constraints)
        
        while queue:
            constraint = queue.pop(0)
            
            if self._revise(domains, constraint):
                slot1_id = constraint.slot1_id
                
                if not domains[slot1_id]:
                    return False
                
                # 将相关约束加入队列
                for c in self.constraint_graph[slot1_id]:
                    if c != constraint:
                        queue.append(c)
        
        return True
    
    def _revise(self, domains: Dict[str, List[str]], constraint: CSPConstraint) -> bool:
        """修订域 - 移除不一致的值"""
        revised = False
        slot1_domain = domains[constraint.slot1_id]
        slot2_domain = domains[constraint.slot2_id]
        
        new_domain = []
        for word1 in slot1_domain:
            # 检查是否存在slot2中的word使得约束满足
            letter1 = word1[constraint.pos1]
            
            has_support = any(
                word2[constraint.pos2] == letter1 
                for word2 in slot2_domain
            )
            
            if has_support:
                new_domain.append(word1)
            else:
                revised = True
        
        if revised:
            domains[constraint.slot1_id] = new_domain
        
        return revised


class TemplateCSPSolver:
    """
    基于模板的CSP求解器 - 使用预定义的单词槽位模板
    
    策略：
    1. 使用预定义的高质量填字模板（槽位布局）
    2. 用CSP填充单词到槽位
    3. 确保所有交叉点字母一致
    """
    
    # 6x6 模板 - 简化版：减少槽位和约束，提高成功率
    # 核心策略：只保留3-4个交叉点，避免过度约束
    TEMPLATES_6X6 = [
        # 模板1：简单十字交叉（4个词，2个交叉点）
        [
            (0, 0, "across", 5),   # 横向词1
            (3, 0, "across", 5),   # 横向词2  
            (0, 0, "down", 5),     # 与横1在(0,0)交叉
            (0, 4, "down", 5),     # 与横1在(0,4)交叉，与横2在(3,4)交叉
        ],
        # 模板2：两横两纵基础版
        [
            (1, 0, "across", 5),
            (4, 0, "across", 5),
            (0, 1, "down", 6),
            (0, 3, "down", 6),
        ],
        # 模板3：紧凑型（3词）
        [
            (0, 0, "across", 6),
            (0, 0, "down", 6),
            (0, 3, "down", 6),
        ],
    ]
    
    # 7x7 模板 - 简化版
    TEMPLATES_7X7 = [
        # 模板1：简单交叉（4词）
        [
            (0, 0, "across", 7),
            (4, 0, "across", 7),
            (0, 0, "down", 7),
            (0, 4, "down", 7),
        ],
        # 模板2：紧凑型（3词）
        [
            (0, 0, "across", 7),
            (0, 0, "down", 7),
            (0, 5, "down", 7),
        ],
    ]
    
    # 8x8 模板 - 简化版
    TEMPLATES_8X8 = [
        # 模板1：简单交叉（4词）
        [
            (0, 0, "across", 8),
            (5, 0, "across", 8),
            (0, 0, "down", 8),
            (0, 5, "down", 8),
        ],
        # 模板2：紧凑型（3词）
        [
            (0, 0, "across", 8),
            (0, 0, "down", 8),
            (0, 6, "down", 8),
        ],
    ]
    
    def __init__(self, word_index: WordIndex, grid_size: int):
        self.word_index = word_index
        self.grid_size = grid_size
        self.template = self._select_template()
    
    def _select_template(self):
        """选择合适的模板"""
        if self.grid_size == 6:
            templates = self.TEMPLATES_6X6
        elif self.grid_size == 7:
            templates = self.TEMPLATES_7X7
        elif self.grid_size >= 8:
            templates = self.TEMPLATES_8X8
        else:
            templates = self.TEMPLATES_6X6
        
        return random.choice(templates)
    
    def solve(self, timeout_seconds: float = 5.0) -> Optional[Dict]:
        """
        求解模板填充问题
        
        Returns:
            成功时返回 {slot_index: word} 和网格
        """
        start_time = time.time()
        
        # 构建槽位和约束
        slots = []
        for i, (row, col, direction, length) in enumerate(self.template):
            words = self.word_index.get_words_by_length(length)
            if not words:
                return None
            random.shuffle(words)
            slots.append({
                'id': i,
                'row': row,
                'col': col,
                'direction': direction,
                'length': length,
                'domain': words[:200],  # 限制域大小
                'assigned': None
            })
        
        # 计算交叉约束
        constraints = []
        for i, slot1 in enumerate(slots):
            for j, slot2 in enumerate(slots):
                if i >= j:
                    continue
                intersection = self._find_intersection(slot1, slot2)
                if intersection:
                    constraints.append((i, j, intersection[0], intersection[1]))
        
        # 回溯搜索
        assignment = {}
        result = self._backtrack_template(slots, constraints, assignment, start_time, timeout_seconds)
        
        if result:
            # 构建网格
            grid = [['' for _ in range(self.grid_size)] for _ in range(self.grid_size)]
            for slot in slots:
                word = result[slot['id']]
                for k, letter in enumerate(word):
                    if slot['direction'] == 'across':
                        grid[slot['row']][slot['col'] + k] = letter
                    else:
                        grid[slot['row'] + k][slot['col']] = letter
            
            return {'assignment': result, 'grid': grid, 'slots': slots}
        
        return None
    
    def _find_intersection(self, slot1, slot2) -> Optional[Tuple[int, int]]:
        """找出两个槽位的交叉点"""
        if slot1['direction'] == slot2['direction']:
            return None
        
        # 确定哪个是横向，哪个是纵向
        if slot1['direction'] == 'across':
            h_slot, v_slot = slot1, slot2
        else:
            h_slot, v_slot = slot2, slot1
        
        # 检查是否相交
        h_row = h_slot['row']
        v_col = v_slot['col']
        
        # 横向槽位覆盖的列范围
        h_col_start = h_slot['col']
        h_col_end = h_slot['col'] + h_slot['length'] - 1
        
        # 纵向槽位覆盖的行范围
        v_row_start = v_slot['row']
        v_row_end = v_slot['row'] + v_slot['length'] - 1
        
        # 检查交叉
        if h_col_start <= v_col <= h_col_end and v_row_start <= h_row <= v_row_end:
            h_pos = v_col - h_col_start  # 横向单词中的位置
            v_pos = h_row - v_row_start  # 纵向单词中的位置
            
            if slot1['direction'] == 'across':
                return (h_pos, v_pos)
            else:
                return (v_pos, h_pos)
        
        return None
    
    def _backtrack_template(self, slots, constraints, assignment, start_time, timeout) -> Optional[Dict]:
        """回溯搜索填充模板"""
        if time.time() - start_time > timeout:
            return None
        
        if len(assignment) == len(slots):
            return assignment
        
        # 选择MRV变量
        var = self._select_variable(slots, assignment, constraints)
        if var is None:
            return None
        
        slot = slots[var]
        
        for word in slot['domain']:
            if self._is_consistent_template(var, word, slots, constraints, assignment):
                assignment[var] = word
                result = self._backtrack_template(slots, constraints, assignment, start_time, timeout)
                if result:
                    return result
                del assignment[var]
        
        return None
    
    def _select_variable(self, slots, assignment, constraints) -> Optional[int]:
        """MRV启发式选择变量"""
        unassigned = [i for i in range(len(slots)) if i not in assignment]
        if not unassigned:
            return None
        
        # 计算每个变量的有效域大小（考虑已有约束）
        def effective_domain_size(var_idx):
            slot = slots[var_idx]
            count = 0
            for word in slot['domain']:
                if self._is_consistent_template(var_idx, word, slots, constraints, assignment):
                    count += 1
                    if count > 10:  # 快速估算
                        break
            return count
        
        return min(unassigned, key=effective_domain_size)
    
    def _is_consistent_template(self, var, word, slots, constraints, assignment) -> bool:
        """检查赋值一致性"""
        for (i, j, pos_i, pos_j) in constraints:
            if i == var and j in assignment:
                if word[pos_i] != assignment[j][pos_j]:
                    return False
            elif j == var and i in assignment:
                if word[pos_j] != assignment[i][pos_i]:
                    return False
        return True


class CrossValidatedPuzzleGenerator:
    """
    交叉验证填字生成器
    
    关键特性：
    1. 交叉验证 - 确保横向纵向形成的所有连续字母序列都是有效单词
    2. 密度控制 - 使用密度(>=35%)而不是数量衡量
    3. 单词长度多样化 - 混合不同长度的单词
    4. 不会形成无效的字母组合如ACDE, KHIS
    """
    
    MIN_DENSITY = 0.35  # 最低密度要求
    
    def __init__(self, word_index: WordIndex, grid_size: int):
        self.word_index = word_index
        self.grid_size = grid_size
        self.grid = [['' for _ in range(grid_size)] for _ in range(grid_size)]
        self.placed_words: List[dict] = []
    
    def generate(self, min_density: float = 0.35, timeout: float = 10.0, 
                 max_retries: int = 20) -> Optional[DensePuzzle]:
        """
        生成交叉验证的填字游戏
        
        Args:
            min_density: 最低密度要求
            timeout: 超时时间
            max_retries: 最大重试次数
        
        Returns:
            生成的谜题
        """
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
                    # 计算展示字母
                    puzzle.compute_revealed_letters(min_reveal=2)
                    return puzzle
        
        return None
    
    def _try_generate(self, min_density: float, timeout: float) -> bool:
        """尝试生成一个谜题"""
        start_time = time.time()
        
        # 获取各种长度的单词，确保多样性
        words_by_length = {}
        for length in range(3, min(self.grid_size + 1, 11)):
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
        
        # 交替添加不同长度的单词
        for i in range(max(len(w) for w in words_by_length.values())):
            for length in lengths:
                if i < len(words_by_length.get(length, [])):
                    all_words.append((words_by_length[length][i], length))
        
        # 放置第一个单词（中等长度，居中）
        mid_lengths = [l for l in lengths if 4 <= l <= 6]
        if not mid_lengths:
            mid_lengths = lengths
        first_length = random.choice(mid_lengths)
        first_word_list = words_by_length.get(first_length, [])
        
        if first_word_list:
            first_word = first_word_list[0]
            start_row = self.grid_size // 2
            start_col = max(0, (self.grid_size - len(first_word)) // 2)
            self._place_word(first_word, start_row, start_col, "across")
        
        # 继续放置单词直到达到密度要求
        used_words = {first_word.upper() if first_word_list else ''}
        max_attempts = 500
        attempts = 0
        
        while self._calculate_density() < min_density and attempts < max_attempts:
            if time.time() - start_time > timeout:
                break
            
            attempts += 1
            
            # 选择一个未使用的单词
            word_to_place = None
            word_length = 0
            
            for word, length in all_words:
                if word.upper() not in used_words:
                    word_to_place = word
                    word_length = length
                    break
            
            if not word_to_place:
                # 用完了所有单词
                break
            
            # 尝试放置这个单词
            placed = self._try_place_word_validated(word_to_place)
            if placed:
                used_words.add(word_to_place.upper())
            else:
                # 标记为已尝试，避免重复
                used_words.add(word_to_place.upper())
        
        return self._calculate_density() >= min_density
    
    def _calculate_density(self) -> float:
        """计算当前网格密度"""
        total = self.grid_size * self.grid_size
        filled = sum(1 for row in self.grid for cell in row if cell)
        return filled / total
    
    def _try_place_word_validated(self, word: str) -> bool:
        """
        尝试放置单词，并验证不会形成无效的字母序列
        """
        word = word.upper()
        word_len = len(word)
        
        # 收集所有可能的放置位置
        placements = []
        
        # 方法1：寻找与已有单词的交叉点
        for placed in self.placed_words:
            placed_word = placed['word']
            placed_row = placed['row']
            placed_col = placed['col']
            placed_dir = placed['direction']
            
            for i, letter1 in enumerate(placed_word):
                for j, letter2 in enumerate(word):
                    if letter1 == letter2:
                        # 计算新单词的放置位置
                        if placed_dir == 'across':
                            new_row = placed_row - j
                            new_col = placed_col + i
                            new_dir = 'down'
                        else:
                            new_row = placed_row + i
                            new_col = placed_col - j
                            new_dir = 'across'
                        
                        # 验证放置
                        if self._can_place_validated(word, new_row, new_col, new_dir):
                            score = self._calculate_placement_score(word, new_row, new_col, new_dir)
                            if score > 0:
                                placements.append((new_row, new_col, new_dir, score))
        
        # 方法2：如果没有交叉点，尝试随机位置
        if not placements and len(self.placed_words) == 0:
            # 这是第一个单词
            row = self.grid_size // 2
            col = max(0, (self.grid_size - word_len) // 2)
            if self._can_place_validated(word, row, col, 'across'):
                placements.append((row, col, 'across', 100))
        
        if not placements:
            return False
        
        # 选择最佳放置位置
        placements.sort(key=lambda x: x[3], reverse=True)
        best = placements[0]
        
        return self._place_word(word, best[0], best[1], best[2])
    
    def _can_place_validated(self, word: str, row: int, col: int, direction: str) -> bool:
        """
        检查是否可以放置单词，并验证不会形成无效的字母序列
        """
        word_len = len(word)
        
        # 1. 基本边界检查
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
        
        # 2. 检查是否与现有字母冲突
        has_intersection = (len(self.placed_words) == 0)  # 第一个单词不需要交叉
        
        for i, letter in enumerate(word):
            if direction == 'across':
                r, c = row, col + i
            else:
                r, c = row + i, col
            
            existing = self.grid[r][c]
            if existing:
                if existing != letter:
                    return False  # 字母冲突
                has_intersection = True
        
        if not has_intersection:
            return False
        
        # 3. 检查单词首尾不会与其他单词直接相连
        if direction == 'across':
            # 检查左边
            if col > 0 and self.grid[row][col - 1]:
                return False
            # 检查右边
            if col + word_len < self.grid_size and self.grid[row][col + word_len]:
                return False
        else:
            # 检查上边
            if row > 0 and self.grid[row - 1][col]:
                return False
            # 检查下边
            if row + word_len < self.grid_size and self.grid[row + word_len][col]:
                return False
        
        # 4. 交叉验证：检查放置后是否会形成无效的字母序列
        # 创建临时网格
        temp_grid = [r[:] for r in self.grid]
        for i, letter in enumerate(word):
            if direction == 'across':
                temp_grid[row][col + i] = letter
            else:
                temp_grid[row + i][col] = letter
        
        # 检查所有受影响的行和列是否形成有效序列
        if not self._validate_grid_sequences(temp_grid, word, row, col, direction):
            return False
        
        return True
    
    def _validate_grid_sequences(self, temp_grid: List[List[str]], 
                                  new_word: str, start_row: int, start_col: int, 
                                  direction: str) -> bool:
        """
        验证网格中所有连续字母序列都是有效单词或预期单词的一部分
        
        关键：只验证与新放置单词相邻或交叉的序列
        """
        word_len = len(new_word)
        
        # 收集需要检查的位置
        positions_to_check = set()
        for i in range(word_len):
            if direction == 'across':
                positions_to_check.add((start_row, start_col + i))
            else:
                positions_to_check.add((start_row + i, start_col))
        
        # 检查垂直方向（如果新单词是水平的）或水平方向（如果新单词是垂直的）
        for pos in positions_to_check:
            r, c = pos
            
            # 检查垂直序列
            if direction == 'across':
                seq = self._get_vertical_sequence(temp_grid, r, c)
                if len(seq) >= 2:  # 只有2个及以上字母的序列需要验证
                    if not self._is_valid_sequence(seq):
                        return False
            else:
                # 检查水平序列
                seq = self._get_horizontal_sequence(temp_grid, r, c)
                if len(seq) >= 2:
                    if not self._is_valid_sequence(seq):
                        return False
        
        return True
    
    def _get_vertical_sequence(self, grid: List[List[str]], row: int, col: int) -> str:
        """获取包含指定位置的垂直连续字母序列"""
        # 向上找起点
        start_row = row
        while start_row > 0 and grid[start_row - 1][col]:
            start_row -= 1
        
        # 向下收集序列
        seq = ""
        r = start_row
        while r < self.grid_size and grid[r][col]:
            seq += grid[r][col]
            r += 1
        
        return seq
    
    def _get_horizontal_sequence(self, grid: List[List[str]], row: int, col: int) -> str:
        """获取包含指定位置的水平连续字母序列"""
        # 向左找起点
        start_col = col
        while start_col > 0 and grid[row][start_col - 1]:
            start_col -= 1
        
        # 向右收集序列
        seq = ""
        c = start_col
        while c < self.grid_size and grid[row][c]:
            seq += grid[row][c]
            c += 1
        
        return seq
    
    def _is_valid_sequence(self, seq: str) -> bool:
        """
        检查序列是否有效：
        1. 长度为1：始终有效（单个字母）
        2. 长度>=2：必须是有效单词
        """
        if len(seq) < 2:
            return True
        
        # 检查是否是有效单词
        return self.word_index.is_valid_word(seq)
    
    def _calculate_placement_score(self, word: str, row: int, col: int, direction: str) -> int:
        """计算放置位置的得分"""
        score = 50  # 基础分
        word_len = len(word)
        
        # 交叉点奖励
        intersections = 0
        for i in range(word_len):
            if direction == 'across':
                r, c = row, col + i
            else:
                r, c = row + i, col
            
            if self.grid[r][c]:
                intersections += 1
        
        score += intersections * 20
        
        # 中心位置奖励
        center = self.grid_size // 2
        if direction == 'across':
            dist = abs(row - center) + abs(col + word_len // 2 - center)
        else:
            dist = abs(row + word_len // 2 - center) + abs(col - center)
        score -= dist * 2
        
        # 长度多样化奖励
        existing_lengths = {len(pw['word']) for pw in self.placed_words}
        if word_len not in existing_lengths:
            score += 15  # 新长度奖励
        
        return score
    
    def _place_word(self, word: str, row: int, col: int, direction: str) -> bool:
        """放置单词到网格"""
        word = word.upper()
        word_len = len(word)
        
        # 放置字母
        for i, letter in enumerate(word):
            if direction == 'across':
                self.grid[row][col + i] = letter
            else:
                self.grid[row + i][col] = letter
        
        # 记录放置的单词
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
    
    def _build_puzzle(self) -> Optional[DensePuzzle]:
        """构建谜题对象"""
        if not self.placed_words:
            return None
        
        puzzle = DensePuzzle(grid_size=self.grid_size)
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


class CSPPuzzleGenerator:
    """
    CSP填字游戏生成器 - 主入口类
    
    支持生成6x6到10x10的填字游戏
    使用模板+CSP混合策略，确保高成功率
    """
    
    # 网格大小配置
    GRID_SIZE_CONFIG = {
        "easy": 6,
        "medium": 7,
        "hard": 8,
        "expert": 9,
        "master": 10
    }
    
    # 关卡难度映射
    LEVEL_TO_DIFFICULTY = {
        (1, 10): "easy",
        (11, 30): "medium", 
        (31, 60): "hard",
        (61, 100): "expert",
        (101, 256): "master"
    }
    
    def __init__(self, random_seed: int = None):
        self._answer_cache: Dict[int, str] = {}
        self._word_id_counter = 50000  # CSP生成的单词ID从50000开始
        # 使用时间戳作为默认随机种子，确保每次生成不同
        if random_seed is None:
            random_seed = int(time.time() * 1000000) % (2**31)
        random.seed(random_seed)
        self._random_seed = random_seed
    
    def reseed(self, seed: int = None):
        """重新设置随机种子以确保随机性"""
        if seed is None:
            seed = int(time.time() * 1000000) % (2**31)
        random.seed(seed)
        self._random_seed = seed
        return seed
    
    def _get_difficulty_for_level(self, level: int) -> str:
        """根据关卡获取难度"""
        for (start, end), difficulty in self.LEVEL_TO_DIFFICULTY.items():
            if start <= level <= end:
                return difficulty
        return "medium"
    
    def generate_cross_validated_puzzle(self, grid_size: int, vocab_words: List[dict],
                                         min_density: float = 0.35, timeout: float = 10.0,
                                         max_retries: int = 20) -> Optional[DensePuzzle]:
        """
        生成交叉验证的填字游戏（推荐使用）
        
        特性：
        1. 交叉验证 - 确保所有横向纵向形成的字母组合都是有效单词
        2. 密度控制 - 使用密度(>=35%)而不是数量衡量
        3. 单词长度多样化 - 长短不一搭配
        4. 字母展示 - 每个单词展示2个以上字母但不能全展示
        
        Args:
            grid_size: 网格大小 (5-10)
            vocab_words: 词库单词列表
            min_density: 最低密度要求 (默认35%)
            timeout: 超时时间
            max_retries: 最大重试次数
        
        Returns:
            生成的谜题，失败返回None
        """
        if not (5 <= grid_size <= 10):
            grid_size = max(5, min(10, grid_size))
        
        # 创建单词索引
        word_index = WordIndex(vocab_words)
        
        # 使用交叉验证生成器
        generator = CrossValidatedPuzzleGenerator(word_index, grid_size)
        puzzle = generator.generate(min_density=min_density, timeout=timeout, max_retries=max_retries)
        
        if puzzle:
            # 缓存答案用于验证
            for word_info in puzzle.row_words + puzzle.col_words:
                word_id = word_info.get('id', 0)
                word = word_info.get('word', '')
                if word_id and word:
                    self._answer_cache[word_id] = word
        
        return puzzle
    
    def generate_template_puzzle(self, grid_size: int, vocab_words: List[dict], 
                                  timeout: float = 5.0, max_retries: int = 10) -> Optional[DensePuzzle]:
        """
        使用模板生成填字游戏（旧方法，建议使用 generate_cross_validated_puzzle）
        
        Args:
            grid_size: 网格大小 (6-10)
            vocab_words: 词库单词列表
            timeout: 单次求解超时（秒）
            max_retries: 最大重试次数
        
        Returns:
            生成的谜题，失败返回None
        """
        if not (6 <= grid_size <= 10):
            grid_size = max(6, min(10, grid_size))
        
        # 创建单词索引
        word_index = WordIndex(vocab_words)
        
        # 多次尝试
        for attempt in range(max_retries):
            solver = TemplateCSPSolver(word_index, grid_size)
            result = solver.solve(timeout_seconds=timeout)
            
            if result:
                return self._build_template_puzzle(result, word_index, grid_size)
        
        return None
    
    def _build_template_puzzle(self, result: Dict, word_index: WordIndex, 
                               grid_size: int) -> DensePuzzle:
        """从模板解构建谜题"""
        puzzle = DensePuzzle(grid_size=grid_size)
        puzzle.grid = result['grid']
        
        for slot in result['slots']:
            word = result['assignment'][slot['id']]
            word_info = word_index.get_word_info(word)
            
            if word_info:
                word_id = word_info.get("id", self._word_id_counter)
                definition = word_info.get("definition", "")
            else:
                self._word_id_counter += 1
                word_id = self._word_id_counter
                definition = ""
            
            word_data = {
                "id": word_id,
                "word": word,
                "definition": definition,
                "row": slot['row'],
                "col": slot['col'],
                "direction": slot['direction'],
                "length": slot['length']
            }
            
            if slot['direction'] == 'across':
                puzzle.row_words.append(word_data)
            else:
                puzzle.col_words.append(word_data)
            
            self._answer_cache[word_id] = word
        
        return puzzle
    
    def generate_dense_puzzle(self, grid_size: int, vocab_words: List[dict], 
                              timeout: float = 5.0, max_retries: int = 10) -> Optional[DensePuzzle]:
        """
        生成密集填字游戏（现在使用模板方法）
        
        Args:
            grid_size: 网格大小 (6-10)
            vocab_words: 词库单词列表
            timeout: 单次求解超时（秒）
            max_retries: 最大重试次数
        
        Returns:
            生成的谜题，失败返回None
        """
        # 使用模板方法代替纯密集CSP
        return self.generate_template_puzzle(grid_size, vocab_words, timeout, max_retries)
    
    def _build_puzzle(self, solution: Dict[str, str], 
                      word_index: WordIndex, grid_size: int) -> DensePuzzle:
        """从CSP解构建谜题对象"""
        puzzle = DensePuzzle(grid_size=grid_size)
        
        # 填充网格
        for i in range(grid_size):
            row_word = solution[f"row_{i}"]
            for j, letter in enumerate(row_word):
                puzzle.grid[i][j] = letter
        
        # 收集横向单词
        for i in range(grid_size):
            word = solution[f"row_{i}"]
            word_info = word_index.get_word_info(word)
            
            if word_info:
                puzzle.row_words.append({
                    "id": word_info.get("id", self._word_id_counter),
                    "word": word,
                    "definition": word_info.get("definition", "")
                })
                self._answer_cache[word_info.get("id", self._word_id_counter)] = word
            else:
                self._word_id_counter += 1
                puzzle.row_words.append({
                    "id": self._word_id_counter,
                    "word": word,
                    "definition": ""
                })
                self._answer_cache[self._word_id_counter] = word
        
        # 收集纵向单词
        for j in range(grid_size):
            word = solution[f"col_{j}"]
            word_info = word_index.get_word_info(word)
            
            if word_info:
                puzzle.col_words.append({
                    "id": word_info.get("id", self._word_id_counter),
                    "word": word,
                    "definition": word_info.get("definition", "")
                })
                self._answer_cache[word_info.get("id", self._word_id_counter)] = word
            else:
                self._word_id_counter += 1
                puzzle.col_words.append({
                    "id": self._word_id_counter,
                    "word": word,
                    "definition": ""
                })
                self._answer_cache[self._word_id_counter] = word
        
        return puzzle
    
    def generate_campaign_level(self, level: int, group: str, vocab_manager, config: dict = None) -> dict:
        """
        生成闯关模式关卡 - 使用交叉验证生成器
        
        特性：
        1. 交叉验证 - 不会出现无效的字母组合
        2. 密度控制 - 使用密度(>=35%)衡量
        3. 单词长度多样化
        4. 字母展示 - 每个单词展示2个以上字母但不能全展示
        
        Args:
            level: 关卡号
            group: 词库组别
            vocab_manager: 词汇管理器
            config: 可选的外部配置，包含 grid_size, word_count, difficulty, prefill_ratio
        
        Returns:
            谜题字典
        """
        # 优先使用外部配置
        if config:
            difficulty = config.get("difficulty", "medium")
            grid_size = config.get("grid_size", 7)
        else:
            difficulty = self._get_difficulty_for_level(level)
            grid_size = self.GRID_SIZE_CONFIG.get(difficulty, 6)
        
        # 根据难度调整密度要求
        density_config = {
            "easy": 0.30,
            "medium": 0.35,
            "hard": 0.38,
            "expert": 0.40,
            "master": 0.42
        }
        min_density = density_config.get(difficulty, 0.35)
        
        # 获取用于CSP的完整词库
        if hasattr(vocab_manager, 'get_all_words_for_csp'):
            all_words = vocab_manager.get_all_words_for_csp(group)
        else:
            all_words = vocab_manager.get_words(group, limit=10000)
        
        # 优先使用交叉验证生成器
        puzzle = self.generate_cross_validated_puzzle(
            grid_size, all_words, 
            min_density=min_density, 
            timeout=10.0, 
            max_retries=20
        )
        
        if puzzle:
            # 关键：生成展示字母（之前缺失导致 prefilled 为空）
            puzzle.compute_revealed_letters(min_reveal=2)
            result = puzzle.to_dict()
            result["level"] = level
            result["difficulty"] = difficulty
            result["group"] = group
            result["cross_validated"] = True  # 标记为交叉验证生成
            return result
        
        # 如果交叉验证生成失败，尝试使用模板生成器作为后备
        puzzle = self.generate_template_puzzle(grid_size, all_words, timeout=5.0, max_retries=10)
        
        if puzzle:
            puzzle.compute_revealed_letters(min_reveal=2)
            result = puzzle.to_dict()
            result["level"] = level
            result["difficulty"] = difficulty
            result["group"] = group
            result["cross_validated"] = False
            return result
        
        # 生成失败，返回错误信息
        return {
            "error": True,
            "message": f"无法为该词库生成{grid_size}x{grid_size}的填字游戏",
            "level": level,
            "difficulty": difficulty,
            "group": group
        }
    
    def generate_random_puzzle(self, group: str, difficulty: str, vocab_manager) -> dict:
        """
        生成随机关卡 - 使用交叉验证生成器
        """
        grid_size = self.GRID_SIZE_CONFIG.get(difficulty, 6)
        
        # 最小单词数配置
        min_words_config = {
            "easy": 2,
            "medium": 3,
            "hard": 4,
        }
        min_words = min_words_config.get(difficulty, 2)
        
        # 根据难度调整密度要求
        density_config = {
            "easy": 0.30,
            "medium": 0.35,
            "hard": 0.38,
            "expert": 0.40,
            "master": 0.42
        }
        min_density = density_config.get(difficulty, 0.35)
        
        # 获取用于CSP的完整词库
        if hasattr(vocab_manager, 'get_all_words_for_csp'):
            all_words = vocab_manager.get_all_words_for_csp(group)
        else:
            all_words = vocab_manager.get_words(group, limit=10000)
        
        # 增加重试机制，确保生成至少 min_words 个单词
        best_result = None
        best_word_count = 0
        
        for attempt in range(5):
            # 打乱词汇顺序
            random.shuffle(all_words)
            
            # 优先使用交叉验证生成器
            puzzle = self.generate_cross_validated_puzzle(
                grid_size, all_words,
                min_density=min_density,
                timeout=10.0,
                max_retries=20
            )
            
            if puzzle:
                # 关键：生成展示字母（之前缺失导致 prefilled 为空）
                puzzle.compute_revealed_letters(min_reveal=2)
                result = puzzle.to_dict()
                word_count = len(result.get("words", []))
                
                if word_count >= min_words:
                    result["level"] = 0
                    result["difficulty"] = difficulty
                    result["group"] = group
                    result["cross_validated"] = True
                    return result
                
                if word_count > best_word_count:
                    best_word_count = word_count
                    best_result = result
        
        # 使用最好的结果
        if best_result:
            best_result["level"] = 0
            best_result["difficulty"] = difficulty
            best_result["group"] = group
            best_result["cross_validated"] = True
            return best_result
        
        # 后备：使用模板生成器
        puzzle = self.generate_template_puzzle(grid_size, all_words, timeout=5.0, max_retries=10)
        
        if puzzle:
            puzzle.compute_revealed_letters(min_reveal=2)
            result = puzzle.to_dict()
            result["level"] = 0
            result["difficulty"] = difficulty
            result["group"] = group
            result["cross_validated"] = False
            return result
        
        return {
            "error": True,
            "message": f"生成失败",
            "level": 0,
            "difficulty": difficulty,
            "group": group
        }
    
    def verify_answer(self, word_id: int, answer: str) -> dict:
        """验证答案"""
        correct_answer = self._answer_cache.get(word_id, "")
        is_correct = answer.upper() == correct_answer.upper()
        
        return {
            "correct": is_correct,
            "word": correct_answer if is_correct else "",
            "definition": ""
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


# ==================== 测试代码 ====================

if __name__ == "__main__":
    import json
    from pathlib import Path
    
    print("=" * 60)
    print("CSP 模板填字游戏生成器测试")
    print("=" * 60)
    
    # 加载真实词库
    vocab_path = Path(__file__).parent.parent / "data" / "vocabulary" / "common_words.json"
    if vocab_path.exists():
        with open(vocab_path, 'r', encoding='utf-8') as f:
            words = json.load(f)
        for i, w in enumerate(words):
            w['id'] = i + 1
        print(f"加载词库: {len(words)} 个单词")
    else:
        # 使用测试数据
        words = [
            {"word": "action", "definition": "行动", "id": 1},
            {"word": "active", "definition": "活跃的", "id": 2},
            {"word": "cat", "definition": "猫", "id": 3},
            {"word": "dog", "definition": "狗", "id": 4},
            {"word": "run", "definition": "跑", "id": 5},
            {"word": "sun", "definition": "太阳", "id": 6},
        ]
        print("使用测试数据")
    
    generator = CSPPuzzleGenerator()
    
    # 测试6x6
    print("\n尝试生成 6x6 模板填字游戏...")
    puzzle = generator.generate_template_puzzle(6, words, timeout=5.0, max_retries=10)
    
    if puzzle:
        print("生成成功！")
        print("\n网格：")
        for row in puzzle.grid:
            row_str = ""
            for cell in row:
                row_str += cell if cell else "."
            print(f"  {row_str}")
        
        print("\n横向单词：")
        for w in puzzle.row_words:
            print(f"  ({w['row']},{w['col']}) {w['word']}: {w['definition']}")
        
        print("\n纵向单词：")
        for w in puzzle.col_words:
            print(f"  ({w['row']},{w['col']}) {w['word']}: {w['definition']}")
        
        # 测试API输出
        result = puzzle.to_dict()
        print(f"\nAPI输出: grid_size={result['grid_size']}, words={len(result['words'])}")
    else:
        print("生成失败")
