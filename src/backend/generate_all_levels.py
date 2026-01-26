#!/usr/bin/env python3
"""
一次性生成全部关卡

三级难度系统：
- 简单(easy): 预填字母多（40%），单词数少
- 中等(medium): 预填字母适中（25%），单词数适中
- 困难(hard): 预填字母少（15%），单词数多

阶梯难度规则：

小学词库（最大8×8）- 从5×5开始，基础81关：
  5×5: 9关 (1-9) - 简单3关 + 中3关 + 难3关
  6×6: 18关 (10-27) - 每个难度6关
  7×7: 27关 (28-54) - 每个难度9关
  8×8: 27关 (55-81) - 每个难度9关
  第82关起：如果覆盖度<85%，继续用8×8困难模式补齐

其他词库（最大10×10）- 从6×6开始，基础108关：
  6×6: 9关 (1-9) - 简单3关 + 中3关 + 难3关
  7×7: 18关 (10-27) - 每个难度6关
  8×8: 27关 (28-54) - 每个难度9关
  9×9: 27关 (55-81) - 每个难度9关
  10×10: 27关 (82-108) - 每个难度9关
  第109关起：如果覆盖度<85%，继续用10×10困难模式补齐

备选答案规则：
- 每关的每个单词都搜索备选答案
- 备选答案从全量词库中进行正则匹配
- 命中备选答案也算答对

生成完成后输出汇总报告。
"""

import sys
import json
import time
import random
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Set

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from puzzle_generator import CrosswordGenerator
from csp_puzzle_generator import CSPPuzzleGenerator
from vocabulary import VocabularyManager


# 最大关卡数限制（不限制，根据覆盖率需要生成）
MAX_LEVELS_LIMIT = 99999  # 实际上由覆盖率决定

# 统一目标覆盖率：85%
TARGET_COVERAGE = 0.85

# 三级难度配置
# 预填字母比例：简单40%、中等25%、困难15%
# 单词长度范围：按设计简报规定
DIFFICULTY_CONFIG = {
    "easy": {"prefill_ratio": 0.40, "word_count_factor": 0.7, "word_len_range": (2, 4)},
    "medium": {"prefill_ratio": 0.25, "word_count_factor": 1.0, "word_len_range": (3, 6)},
    "hard": {"prefill_ratio": 0.15, "word_count_factor": 1.3, "word_len_range": (5, 10)}
}

# 小学基础关卡数（81关）
PRIMARY_BASE_LEVELS = 81
# 其他词库基础关卡数（108关）
OTHER_BASE_LEVELS = 108

# 小学关卡规格（最大8×8）- 动态生成函数
# 从5×5开始，基础81关，之后用8x8困难模式补齐
def get_primary_level_specs(max_levels: int) -> list:
    """根据最大关卡数生成小学关卡规格
    
    从5×5开始，基础81关：
      5×5: 9关 (1-9) - 简单3关 + 中3关 + 难3关
      6×6: 18关 (10-27) - 每个难度6关
      7×7: 27关 (28-54) - 每个难度9关
      8×8: 27关 (55-81) - 每个难度9关
    第82关起用8×8困难模式补齐
    """
    # 基础81关的递进规格（含难度信息）
    specs = [
        # 5×5: 9关，每个难度3关
        {"grid_size": 5, "count": 3, "difficulty": "easy"},      # 1-3
        {"grid_size": 5, "count": 3, "difficulty": "medium"},    # 4-6
        {"grid_size": 5, "count": 3, "difficulty": "hard"},      # 7-9
        # 6×6: 18关，每个难度6关
        {"grid_size": 6, "count": 6, "difficulty": "easy"},      # 10-15
        {"grid_size": 6, "count": 6, "difficulty": "medium"},    # 16-21
        {"grid_size": 6, "count": 6, "difficulty": "hard"},      # 22-27
        # 7×7: 27关，每个难度9关
        {"grid_size": 7, "count": 9, "difficulty": "easy"},      # 28-36
        {"grid_size": 7, "count": 9, "difficulty": "medium"},    # 37-45
        {"grid_size": 7, "count": 9, "difficulty": "hard"},      # 46-54
        # 8×8: 27关，每个难度9关
        {"grid_size": 8, "count": 9, "difficulty": "easy"},      # 55-63
        {"grid_size": 8, "count": 9, "difficulty": "medium"},    # 64-72
        {"grid_size": 8, "count": 9, "difficulty": "hard"},      # 73-81
    ]
    
    # 如果超过81关，剩余全部用8×8困难模式
    if max_levels > PRIMARY_BASE_LEVELS:
        remaining = max_levels - PRIMARY_BASE_LEVELS
        specs.append({"grid_size": 8, "count": remaining, "difficulty": "hard"})
    
    # 计算start和end
    current = 1
    for spec in specs:
        spec["start"] = current
        spec["end"] = current + spec["count"] - 1
        current = spec["end"] + 1
    
    return specs

# 其他词库关卡规格（最大10×10）- 动态生成函数
# 从6×6开始，基础108关，之后用10x10困难模式补齐
def get_other_level_specs(max_levels: int) -> list:
    """根据最大关卡数生成其他词库关卡规格
    
    从6×6开始，基础108关：
      6×6: 9关 (1-9) - 简单3关 + 中3关 + 难3关
      7×7: 18关 (10-27) - 每个难度6关
      8×8: 27关 (28-54) - 每个难度9关
      9×9: 27关 (55-81) - 每个难度9关
      10×10: 27关 (82-108) - 每个难度9关
    第109关起用10×10困难模式补齐
    
    超过10字母的单词会被放弃
    """
    # 基础108关的递进规格（含难度信息）
    specs = [
        # 6×6: 9关，每个难度3关
        {"grid_size": 6, "count": 3, "difficulty": "easy"},      # 1-3
        {"grid_size": 6, "count": 3, "difficulty": "medium"},    # 4-6
        {"grid_size": 6, "count": 3, "difficulty": "hard"},      # 7-9
        # 7×7: 18关，每个难度6关
        {"grid_size": 7, "count": 6, "difficulty": "easy"},      # 10-15
        {"grid_size": 7, "count": 6, "difficulty": "medium"},    # 16-21
        {"grid_size": 7, "count": 6, "difficulty": "hard"},      # 22-27
        # 8×8: 27关，每个难度9关
        {"grid_size": 8, "count": 9, "difficulty": "easy"},      # 28-36
        {"grid_size": 8, "count": 9, "difficulty": "medium"},    # 37-45
        {"grid_size": 8, "count": 9, "difficulty": "hard"},      # 46-54
        # 9×9: 27关，每个难度9关
        {"grid_size": 9, "count": 9, "difficulty": "easy"},      # 55-63
        {"grid_size": 9, "count": 9, "difficulty": "medium"},    # 64-72
        {"grid_size": 9, "count": 9, "difficulty": "hard"},      # 73-81
        # 10×10: 27关，每个难度9关
        {"grid_size": 10, "count": 9, "difficulty": "easy"},     # 82-90
        {"grid_size": 10, "count": 9, "difficulty": "medium"},   # 91-99
        {"grid_size": 10, "count": 9, "difficulty": "hard"},     # 100-108
    ]
    
    # 如果超过108关，剩余全部用10×10困难模式
    if max_levels > OTHER_BASE_LEVELS:
        remaining = max_levels - OTHER_BASE_LEVELS
        specs.append({"grid_size": 10, "count": remaining, "difficulty": "hard"})
    
    # 计算start和end
    current = 1
    for spec in specs:
        spec["start"] = current
        spec["end"] = current + spec["count"] - 1
        current = spec["end"] + 1
    
    return specs

# 兼容旧代码
PRIMARY_LEVEL_SPECS = get_primary_level_specs(PRIMARY_BASE_LEVELS)
OTHER_LEVEL_SPECS = get_other_level_specs(OTHER_BASE_LEVELS)

def get_level_config(level: int, is_primary: bool, max_levels: int = None) -> dict:
    """根据关卡号和词库类型获取配置
    
    返回包含网格大小、单词数量、难度等级、预填比例和单词长度范围的配置
    """
    if max_levels is None:
        max_levels = PRIMARY_BASE_LEVELS if is_primary else OTHER_BASE_LEVELS
    
    # 动态生成规格
    specs = get_primary_level_specs(max_levels) if is_primary else get_other_level_specs(max_levels)
    
    for spec in specs:
        if spec["start"] <= level <= spec["end"]:
            grid_size = spec["grid_size"]
            difficulty = spec.get("difficulty", "medium")
            
            # 根据难度配置调整单词数量
            base_word_count = max(3, min(grid_size - 1, 8))
            difficulty_factor = DIFFICULTY_CONFIG[difficulty]["word_count_factor"]
            word_count = max(3, int(base_word_count * difficulty_factor))
            
            # 获取预填比例
            prefill_ratio = DIFFICULTY_CONFIG[difficulty]["prefill_ratio"]
            
            # 获取单词长度范围（按设计简报规定）
            word_len_range = DIFFICULTY_CONFIG[difficulty]["word_len_range"]
            
            return {
                "grid_size": grid_size,
                "word_count": word_count,
                "difficulty": difficulty,
                "prefill_ratio": prefill_ratio,
                "word_len_range": word_len_range
            }
    
    # 默认配置（困难模式）
    max_grid = 8 if is_primary else 10
    return {
        "grid_size": max_grid, 
        "word_count": max(3, max_grid - 1), 
        "difficulty": "hard",
        "prefill_ratio": DIFFICULTY_CONFIG["hard"]["prefill_ratio"],
        "word_len_range": DIFFICULTY_CONFIG["hard"]["word_len_range"]
    }


def calculate_max_levels(vocab_size: int, target_coverage: float = None, is_primary: bool = False) -> int:
    """根据词库大小计算需要的关卡数以达到目标覆盖度
    
    假设每关平均使用4个独立单词（大网格可以放更多）
    统一目标覆盖率：85%
    
    阶梯难度规则：
    - 小学词库：最少81关（完成5×5→8×8阶梯）
    - 其他词库：最少108关（完成6×6→10×10阶梯）
    """
    # 统一使用85%目标覆盖率
    if target_coverage is None:
        target_coverage = TARGET_COVERAGE  # 85%
    
    target_words = int(vocab_size * target_coverage)
    words_per_level = 4.0
    # 增加30%冗余，因为有些词可能无法放入网格
    needed_levels = int(target_words / words_per_level * 1.3) + 50
    
    # 小学最少81关，其他最少108关（按新的阶梯难度规则）
    min_levels = PRIMARY_BASE_LEVELS if is_primary else OTHER_BASE_LEVELS
    
    return max(min_levels, needed_levels)

# 词库大小映射（用于计算需要的关卡数）
# 这些值从vocabulary文件统计得来
VOCAB_SIZES = {
    "grade3_1": 63,     # 三年级上册（累积）
    "grade3_2": 133,    # 三年级下册（累积）
    "grade4_1": 207,    # 四年级上册（累积）
    "grade4_2": 285,    # 四年级下册（累积）
    "grade5_1": 393,    # 五年级上册（累积）
    "grade5_2": 478,    # 五年级下册（累积）
    "grade6_1": 576,    # 六年级上册（累积）
    "grade6_2": 709,    # 六年级下册（累积）
    # 初中分年级（人教版）- 累积方式
    "junior7_1": 392,   # 七年级上册
    "junior7_2": 700,   # 七年级下册（累积）
    "junior8_1": 1000,  # 八年级上册（累积）
    "junior8_2": 1300,  # 八年级下册（累积）
    "junior9": 1600,    # 九年级（累积）
    # 高中分年级（人教版）- 按必修册
    "senior1": 311,     # 必修1
    "senior2": 600,     # 必修1-2（累积）
    "senior3": 900,     # 必修1-3（累积）
    "senior4": 1200,    # 必修1-4（累积）
    "senior5": 1500,    # 必修1-5（累积）
    "junior": 3119,
    "senior": 6555,
    "ket": 531,
    "pet": 514,
    "cet4": 4543,
    "cet6": 3991,
    "postgrad": 5047,
    "ielts": 5275,
    "toefl": 10367,
    "gre": 9984,
}

# 所有词库分组 - 关卡数根据词库大小动态计算
ALL_GROUPS = {
    # 小学分年级 - 根据累积词库大小计算关卡数
    "grade3_1": {"name": "三年级上册", "category": "小学", "is_primary": True, "max_levels": calculate_max_levels(63, is_primary=True)},
    "grade3_2": {"name": "三年级下册", "category": "小学", "is_primary": True, "max_levels": calculate_max_levels(133, is_primary=True)},
    "grade4_1": {"name": "四年级上册", "category": "小学", "is_primary": True, "max_levels": calculate_max_levels(207, is_primary=True)},
    "grade4_2": {"name": "四年级下册", "category": "小学", "is_primary": True, "max_levels": calculate_max_levels(285, is_primary=True)},
    "grade5_1": {"name": "五年级上册", "category": "小学", "is_primary": True, "max_levels": calculate_max_levels(393, is_primary=True)},
    "grade5_2": {"name": "五年级下册", "category": "小学", "is_primary": True, "max_levels": calculate_max_levels(478, is_primary=True)},
    "grade6_1": {"name": "六年级上册", "category": "小学", "is_primary": True, "max_levels": calculate_max_levels(576, is_primary=True)},
    "grade6_2": {"name": "六年级下册", "category": "小学", "is_primary": True, "max_levels": calculate_max_levels(709, is_primary=True)},
    # 小学总词库（覆盖所有年级）
    "primary_all": {"name": "小学全部", "category": "小学", "is_primary": True, "max_levels": calculate_max_levels(709, is_primary=True)},
    # 初中分年级（人教版）
    "junior7_1": {"name": "七年级上册", "category": "初中", "is_primary": False, "max_levels": calculate_max_levels(392)},
    "junior7_2": {"name": "七年级下册", "category": "初中", "is_primary": False, "max_levels": calculate_max_levels(700)},
    "junior8_1": {"name": "八年级上册", "category": "初中", "is_primary": False, "max_levels": calculate_max_levels(1000)},
    "junior8_2": {"name": "八年级下册", "category": "初中", "is_primary": False, "max_levels": calculate_max_levels(1300)},
    "junior9": {"name": "九年级全册", "category": "初中", "is_primary": False, "max_levels": calculate_max_levels(1600)},
    # 初中总词库
    "junior": {"name": "初中词汇", "category": "初中", "is_primary": False, "max_levels": calculate_max_levels(3119)},
    "junior_all": {"name": "初中全部", "category": "初中", "is_primary": False, "max_levels": calculate_max_levels(3119)},
    # 高中分年级（人教版必修）
    "senior1": {"name": "必修1", "category": "高中", "is_primary": False, "max_levels": calculate_max_levels(311)},
    "senior2": {"name": "必修2", "category": "高中", "is_primary": False, "max_levels": calculate_max_levels(600)},
    "senior3": {"name": "必修3", "category": "高中", "is_primary": False, "max_levels": calculate_max_levels(900)},
    "senior4": {"name": "必修4", "category": "高中", "is_primary": False, "max_levels": calculate_max_levels(1200)},
    "senior5": {"name": "必修5", "category": "高中", "is_primary": False, "max_levels": calculate_max_levels(1500)},
    # 高中总词库
    "senior": {"name": "高中词汇", "category": "高中", "is_primary": False, "max_levels": calculate_max_levels(6555)},
    "senior_all": {"name": "高中全部", "category": "高中", "is_primary": False, "max_levels": calculate_max_levels(6555)},
    "ket": {"name": "KET考试", "category": "考试", "is_primary": False, "max_levels": calculate_max_levels(531)},
    "pet": {"name": "PET考试", "category": "考试", "is_primary": False, "max_levels": calculate_max_levels(514)},
    "cet4": {"name": "大学四级", "category": "考试", "is_primary": False, "max_levels": calculate_max_levels(4543)},
    "cet6": {"name": "大学六级", "category": "考试", "is_primary": False, "max_levels": calculate_max_levels(3991)},
    "postgrad": {"name": "考研词汇", "category": "考试", "is_primary": False, "max_levels": calculate_max_levels(5047)},
    "ielts": {"name": "雅思", "category": "考试", "is_primary": False, "max_levels": calculate_max_levels(5275)},
    "toefl": {"name": "托福", "category": "考试", "is_primary": False, "max_levels": calculate_max_levels(10367)},
    "gre": {"name": "GRE", "category": "考试", "is_primary": False, "max_levels": calculate_max_levels(9984)},
}


def load_pep_grade_vocabulary(grade_code: str) -> List[dict]:
    """从原始PEP文件加载指定年级的词汇（累积方式：高年级可使用低年级词）"""
    # 年级映射到PEP文件
    grade_to_pep = {
        "grade3_1": ["PEPXiaoXue3_1.json"],
        "grade3_2": ["PEPXiaoXue3_1.json", "PEPXiaoXue3_2.json"],
        "grade4_1": ["PEPXiaoXue3_1.json", "PEPXiaoXue3_2.json", "PEPXiaoXue4_1.json"],
        "grade4_2": ["PEPXiaoXue3_1.json", "PEPXiaoXue3_2.json", "PEPXiaoXue4_1.json", "PEPXiaoXue4_2.json"],
        "grade5_1": ["PEPXiaoXue3_1.json", "PEPXiaoXue3_2.json", "PEPXiaoXue4_1.json", "PEPXiaoXue4_2.json", "PEPXiaoXue5_1.json"],
        "grade5_2": ["PEPXiaoXue3_1.json", "PEPXiaoXue3_2.json", "PEPXiaoXue4_1.json", "PEPXiaoXue4_2.json", "PEPXiaoXue5_1.json", "PEPXiaoXue5_2.json"],
        "grade6_1": ["PEPXiaoXue3_1.json", "PEPXiaoXue3_2.json", "PEPXiaoXue4_1.json", "PEPXiaoXue4_2.json", "PEPXiaoXue5_1.json", "PEPXiaoXue5_2.json", "PEPXiaoXue6_1.json"],
        "grade6_2": ["PEPXiaoXue3_1.json", "PEPXiaoXue3_2.json", "PEPXiaoXue4_1.json", "PEPXiaoXue4_2.json", "PEPXiaoXue5_1.json", "PEPXiaoXue5_2.json", "PEPXiaoXue6_1.json", "PEPXiaoXue6_2.json"],
    }
    
    pep_files = grade_to_pep.get(grade_code, [])
    if not pep_files:
        return []
    
    # PEP文件目录
    pep_dir = Path(__file__).parent.parent.parent / "data" / "words" / "04_人教版小学"
    
    all_words = []
    word_set = set()
    word_id = 1
    
    for pep_file in pep_files:
        file_path = pep_dir / pep_file
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    words_list = data.get("words", [])
                    for w in words_list:
                        word = w.get("word", "").strip()
                        # 过滤掉多词短语、太短的词、超过10个字母的词
                        if word and " " not in word and 2 <= len(word) <= 10:
                            word_lower = word.lower()
                            if word_lower not in word_set:
                                word_set.add(word_lower)
                                # 提取中文释义
                                trans = w.get("trans", [])
                                definition = trans[0].get("tranCn", "") if trans else ""
                                all_words.append({
                                    "id": word_id,
                                    "word": word_lower,
                                    "definition": definition,
                                    "difficulty": 1
                                })
                                word_id += 1
            except Exception as e:
                print(f"  警告: 加载PEP文件失败 {pep_file}: {e}")
    
    return all_words


def load_pep_junior_vocabulary(grade_code: str) -> List[dict]:
    """从原始PEP文件加载初中指定年级的词汇（累积方式）"""
    # 年级映射到PEP文件
    grade_to_pep = {
        "junior7_1": ["PEPChuZhong7_1.json"],
        "junior7_2": ["PEPChuZhong7_1.json", "PEPChuZhong7_2.json"],
        "junior8_1": ["PEPChuZhong7_1.json", "PEPChuZhong7_2.json", "PEPChuZhong8_1.json"],
        "junior8_2": ["PEPChuZhong7_1.json", "PEPChuZhong7_2.json", "PEPChuZhong8_1.json", "PEPChuZhong8_2.json"],
        "junior9": ["PEPChuZhong7_1.json", "PEPChuZhong7_2.json", "PEPChuZhong8_1.json", "PEPChuZhong8_2.json", "PEPChuZhong9_1.json"],
    }
    
    pep_files = grade_to_pep.get(grade_code, [])
    if not pep_files:
        return []
    
    # PEP文件目录
    pep_dir = Path(__file__).parent.parent.parent / "data" / "words" / "05_人教版初中"
    
    all_words = []
    word_set = set()
    word_id = 1
    
    for pep_file in pep_files:
        file_path = pep_dir / pep_file
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    words_list = data.get("words", [])
                    for w in words_list:
                        word = w.get("word", "").strip()
                        # 过滤掉多词短语、太短的词、超过10个字母的词
                        if word and " " not in word and 2 <= len(word) <= 10:
                            word_lower = word.lower()
                            if word_lower not in word_set:
                                word_set.add(word_lower)
                                # 提取中文释义
                                trans = w.get("trans", [])
                                definition = trans[0].get("tranCn", "") if trans else ""
                                all_words.append({
                                    "id": word_id,
                                    "word": word_lower,
                                    "definition": definition,
                                    "difficulty": 2
                                })
                                word_id += 1
            except Exception as e:
                print(f"  警告: 加载PEP初中文件失败 {pep_file}: {e}")
    
    return all_words


def load_pep_senior_vocabulary(grade_code: str) -> List[dict]:
    """从原始PEP文件加载高中指定年级的词汇（累积方式）"""
    # 年级映射到PEP文件（必修1-5）
    grade_to_pep = {
        "senior1": ["PEPGaoZhong_1.json"],
        "senior2": ["PEPGaoZhong_1.json", "PEPGaoZhong_2.json"],
        "senior3": ["PEPGaoZhong_1.json", "PEPGaoZhong_2.json", "PEPGaoZhong_3.json"],
        "senior4": ["PEPGaoZhong_1.json", "PEPGaoZhong_2.json", "PEPGaoZhong_3.json", "PEPGaoZhong_4.json"],
        "senior5": ["PEPGaoZhong_1.json", "PEPGaoZhong_2.json", "PEPGaoZhong_3.json", "PEPGaoZhong_4.json", "PEPGaoZhong_5.json"],
    }
    
    pep_files = grade_to_pep.get(grade_code, [])
    if not pep_files:
        return []
    
    # PEP文件目录
    pep_dir = Path(__file__).parent.parent.parent / "data" / "words" / "07_人教版高中"
    
    all_words = []
    word_set = set()
    word_id = 1
    
    for pep_file in pep_files:
        file_path = pep_dir / pep_file
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    words_list = data.get("words", [])
                    for w in words_list:
                        word = w.get("word", "").strip()
                        # 过滤掉多词短语、太短的词、超过10个字母的词
                        if word and " " not in word and 2 <= len(word) <= 10:
                            word_lower = word.lower()
                            if word_lower not in word_set:
                                word_set.add(word_lower)
                                # 提取中文释义
                                trans = w.get("trans", [])
                                definition = trans[0].get("tranCn", "") if trans else ""
                                all_words.append({
                                    "id": word_id,
                                    "word": word_lower,
                                    "definition": definition,
                                    "difficulty": 3
                                })
                                word_id += 1
            except Exception as e:
                print(f"  警告: 加载PEP高中文件失败 {pep_file}: {e}")
    
    return all_words


def get_vocabulary_for_grade(vocab_manager: VocabularyManager, group_code: str) -> List[dict]:
    """获取指定分组的词汇 - 使用完整词库"""
    
    # 处理初中分年级
    if group_code.startswith("junior") and group_code != "junior_all":
        if group_code in ["junior7_1", "junior7_2", "junior8_1", "junior8_2", "junior9"]:
            words = load_pep_junior_vocabulary(group_code)
            if words:
                print(f"  从PEP初中文件加载词汇: {len(words)} 个")
                return words
    
    # 处理高中分年级
    if group_code.startswith("senior") and group_code != "senior_all":
        if group_code in ["senior1", "senior2", "senior3", "senior4", "senior5"]:
            words = load_pep_senior_vocabulary(group_code)
            if words:
                print(f"  从PEP高中文件加载词汇: {len(words)} 个")
                return words
    
    # 处理 _all 类型的词库（小学全部、初中全部、高中全部）
    if group_code == "primary_all":
        # 加载所有小学年级的词汇
        all_words = []
        word_set = set()
        word_id = 1
        for grade in ["grade3_1", "grade3_2", "grade4_1", "grade4_2", "grade5_1", "grade5_2", "grade6_1", "grade6_2"]:
            grade_words = load_pep_grade_vocabulary(grade)
            for w in grade_words:
                word_lower = w["word"].lower()
                if word_lower not in word_set:
                    word_set.add(word_lower)
                    w["id"] = word_id
                    all_words.append(w)
                    word_id += 1
        if all_words:
            print(f"  从所有PEP文件加载小学全部词汇: {len(all_words)} 个")
            return all_words
        # 回退到primary词库
        words = vocab_manager._vocabulary_cache.get("primary", [])
        return [w for w in words if 2 <= len(w["word"]) <= 8 and " " not in w["word"]]
    
    if group_code == "junior_all":
        # 初中全部 = junior 词库
        words = vocab_manager._vocabulary_cache.get("junior", [])
        filtered = [w for w in words if " " not in w.get("word", "") and 2 <= len(w.get("word", "")) <= 10]
        print(f"  加载初中全部词汇: {len(filtered)} 个")
        return filtered
    
    if group_code == "senior_all":
        # 高中全部 = senior 词库
        words = vocab_manager._vocabulary_cache.get("senior", [])
        filtered = [w for w in words if " " not in w.get("word", "") and 2 <= len(w.get("word", "")) <= 10]
        print(f"  加载高中全部词汇: {len(filtered)} 个")
        return filtered
    
    # 如果是小学年级分组，从原始PEP文件加载（累积方式）
    if group_code.startswith("grade"):
        words = load_pep_grade_vocabulary(group_code)
        if words:
            print(f"  从PEP文件加载词汇: {len(words)} 个")
            return words
        # 如果加载失败，回退到primary词库
        print(f"  警告: PEP文件加载失败，使用primary词库")
        words = vocab_manager._vocabulary_cache.get("primary", [])
        return [w for w in words if 2 <= len(w["word"]) <= 8 and " " not in w["word"]]
    
    # 其他词库直接获取完整词汇
    words = vocab_manager._vocabulary_cache.get(group_code, [])
    
    # 过滤掉多词短语和超过10个字母的词
    filtered = [w for w in words if " " not in w.get("word", "") and 2 <= len(w.get("word", "")) <= 10]
    
    print(f"  从词库加载词汇: {len(filtered)} 个")
    return filtered


def find_alternatives(word: str, prefilled: dict, all_vocab: List[dict], max_alternatives: int = 5) -> List[dict]:
    """
    为单词找备选答案（通过正则匹配）
    
    Args:
        word: 原始单词
        prefilled: 预填字母的位置，格式如 {"2-1": "E", "3-2": "B"}
        all_vocab: 全部词库（用于正则匹配）
        max_alternatives: 最大备选答案数量
    
    Returns:
        备选答案列表，每个包含 word 和 definition
    """
    word_upper = word.upper()
    word_len = len(word)
    
    # 构建正则模式：已填字母固定，其他位置用 [A-Z]
    pattern_chars = ['[A-Z]'] * word_len
    
    # 从 prefilled 中提取属于这个单词的固定字母
    # prefilled 格式是 "row-col": "letter"，需要根据单词位置匹配
    # 但这里我们简化处理：用单词本身的字母作为模式
    # 如果有预填位置，把对应位置的字母固定
    
    # 构建基于单词本身的模式（假设所有字母都需要填）
    # 这样可以找到相同长度、任意字母组合的词
    # 实际上我们需要考虑预填位置
    
    # 简化方案：对于长度相同的词，全部作为备选
    alternatives = []
    
    for vocab_entry in all_vocab:
        candidate = vocab_entry.get("word", "").upper()
        if len(candidate) == word_len and candidate != word_upper:
            # 检查是否可以作为备选（所有预填位置字母必须匹配）
            # 由于我们没有单词在网格中的具体位置信息，
            # 简化为：只匹配长度相同的词
            alternatives.append({
                "word": candidate,
                "definition": vocab_entry.get("definition", "")
            })
            if len(alternatives) >= max_alternatives:
                break
    
    return alternatives


def calculate_word_overlap(words1: Set[str], words2: Set[str]) -> float:
    """计算两组单词的重叠率"""
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    return len(intersection) / max(len(words1), len(words2))


def add_alternatives_to_puzzle(puzzle: dict, all_vocab: List[dict]) -> None:
    """
    为关卡中的每个单词添加备选答案
    
    根据单词长度和预填字母位置，在全词库中进行正则匹配
    """
    prefilled = puzzle.get("prefilled", {})
    words = puzzle.get("words", [])
    
    # 按长度分组的词库索引（加速查找）
    vocab_by_length = {}
    for v in all_vocab:
        word = v.get("word", "")
        if word and " " not in word and 2 <= len(word) <= 10:
            wlen = len(word)
            if wlen not in vocab_by_length:
                vocab_by_length[wlen] = []
            vocab_by_length[wlen].append(v)
    
    for word_info in words:
        word = word_info.get("word", "").upper()
        word_len = len(word)
        direction = word_info.get("direction", "")
        start_row = word_info.get("start_row", 0)
        start_col = word_info.get("start_col", 0)
        
        # 收集这个单词的预填字母位置
        filled_positions = {}  # 位置 -> 字母
        for i in range(word_len):
            if direction == "across":
                r, c = start_row, start_col + i
            else:
                r, c = start_row + i, start_col
            
            key = f"{r}-{c}"
            if key in prefilled:
                filled_positions[i] = prefilled[key].upper()
        
        # 构建正则模式
        pattern_chars = []
        for i in range(word_len):
            if i in filled_positions:
                pattern_chars.append(filled_positions[i])
            else:
                pattern_chars.append('[A-Z]')
        
        pattern = '^' + ''.join(pattern_chars) + '$'
        
        # 在同长度词中匹配
        alternatives = []
        candidates = vocab_by_length.get(word_len, [])
        
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            for v in candidates:
                candidate = v.get("word", "").upper()
                if candidate != word and regex.match(candidate):
                    alternatives.append({
                        "word": candidate,
                        "definition": v.get("definition", "")
                    })
                    if len(alternatives) >= 5:  # 最多5个备选
                        break
        except:
            pass
        
        word_info["alternatives"] = alternatives


def generate_level(
    sparse_generator: CrosswordGenerator,
    dense_generator: CSPPuzzleGenerator,
    vocab_words: List[dict],
    level: int,
    group_code: str,
    group_name: str,
    is_primary: bool = False,
    max_levels: int = None,
    used_words: set = None,
    prev_level_words: set = None,
    all_vocab: List[dict] = None
) -> dict:
    """生成单个关卡
    
    Args:
        used_words: 已使用的单词集合，优先使用未使用过的单词
        prev_level_words: 上一关使用的单词集合，用于避免相邻关卡重复
        all_vocab: 全部词库，用于生成备选答案
    
    注意：超过10个字母的单词会被放弃（不适合10x10网格）
    """
    config = get_level_config(level, is_primary, max_levels)
    
    # 根据难度对应的单词长度范围过滤（按设计简报规定）
    # easy: 2-4字母, medium: 3-6字母, hard: 5-10字母
    word_len_range = config.get("word_len_range", (2, 10))
    min_word_len, max_word_len = word_len_range
    
    # 同时不能超过网格大小限制
    max_word_len = min(max_word_len, config["grid_size"] - 1, 10)
    
    # 优先选择符合难度长度要求的单词
    suitable_words = [w for w in vocab_words if min_word_len <= len(w["word"]) <= max_word_len]
    
    if len(suitable_words) < config["word_count"]:
        # 放宽长度限制，允许稍短或稍长的词
        fallback_min = max(2, min_word_len - 1)
        fallback_max = min(config["grid_size"], max_word_len + 2, 10)
        suitable_words = [w for w in vocab_words if fallback_min <= len(w["word"]) <= fallback_max]
    
    if len(suitable_words) < 3:
        return {"level": level, "error": True, "message": "词汇不足"}
    
    # 如果有上一关的单词，优先排除这些词避免重复
    if prev_level_words and len(prev_level_words) > 0:
        # 将上一关用过的词移到列表末尾，优先使用其他词
        non_prev_words = [w for w in suitable_words if w["word"].upper() not in prev_level_words]
        prev_words = [w for w in suitable_words if w["word"].upper() in prev_level_words]
        
        # 打乱非上一关的词，确保随机性
        random.shuffle(non_prev_words)
        random.shuffle(prev_words)
        
        # 优先使用非上一关的词
        suitable_words = non_prev_words + prev_words
    else:
        # 没有上一关信息，直接打乱
        random.shuffle(suitable_words)
    
    # 强制优先使用未使用过的单词，最大化覆盖度
    if used_words:
        unused_words = [w for w in suitable_words if w["word"].upper() not in used_words]
        used_pool = [w for w in suitable_words if w["word"].upper() in used_words]
        
        # 未使用的词随机打乱
        random.shuffle(unused_words)
        random.shuffle(used_pool)
        
        # 始终保证有足够的词供生成器选择，但未使用的词排在前面
        # 生成器会优先从列表头部选词
        selected_words = unused_words + used_pool
        
        # 确保有足够的备选词
        if len(selected_words) < 20:
            # 词太少，无法生成
            pass
    else:
        # 随机选择单词
        random.shuffle(suitable_words)
        selected_words = suitable_words
    
    # 尝试生成关卡（先用稀疏布局，失败再用密集布局）
    try:
        # 分离未使用的词和已使用的词
        if used_words:
            unused_for_level = [w for w in selected_words if w["word"].upper() not in used_words]
            used_for_level = [w for w in selected_words if w["word"].upper() in used_words]
        else:
            unused_for_level = selected_words
            used_for_level = []
        
        # 策略：优先使用未使用的词，但允许少量已使用词辅助交叉
        # 未使用词多时：80%未使用 + 20%已使用（帮助交叉）
        # 未使用词少时：全部混合
        unused_count = len(unused_for_level)
        used_count = len(used_for_level)
        
        # 根据未使用词数量调整策略
        if unused_count >= 100:
            # 大量未使用词：主要用未使用词，少量已使用词辅助交叉
            assist_count = min(len(used_for_level), unused_count // 4)
            random.shuffle(used_for_level)
            mixed_pool = unused_for_level + used_for_level[:assist_count]
            force_unused_only = True
        elif unused_count >= 20:
            # 中等未使用词：混合使用
            mixed_pool = unused_for_level + used_for_level
            force_unused_only = False
        else:
            # 很少未使用词：全部混合
            mixed_pool = unused_for_level + used_for_level
            force_unused_only = False
        
        # 模拟vocab_manager的接口
        class TempVocabManager:
            def __init__(self, unused_words, used_words_backup, mixed_pool, force_unused):
                self._unused = unused_words
                self._used = used_words_backup
                self._mixed = mixed_pool
                self._force_unused = force_unused
                self._all = mixed_pool
                self._vocabulary_cache = {group_code: self._all}
                self._grade_vocabulary_cache = {}
            
            def get_words(self, group, limit=100):
                # 优先返回未使用的词
                if self._force_unused and len(self._unused) >= limit:
                    return self._unused[:limit]
                return self._all[:limit]
            
            def get_words_for_puzzle(self, group, count, max_word_len=None):
                # 关键：强制只使用未使用的词
                if max_word_len:
                    unused_filtered = [w for w in self._unused if len(w["word"]) <= max_word_len]
                    used_filtered = [w for w in self._used if len(w["word"]) <= max_word_len]
                else:
                    unused_filtered = self._unused
                    used_filtered = self._used
                
                import random
                
                # 按长度分组，确保各种长度的词都有机会
                length_groups = {}
                for w in unused_filtered:
                    wlen = len(w["word"])
                    if wlen not in length_groups:
                        length_groups[wlen] = []
                    length_groups[wlen].append(w)
                
                # 从每个长度组中轮流取词，保证多样性
                mixed = []
                while len(mixed) < len(unused_filtered):
                    added_this_round = False
                    for length in sorted(length_groups.keys(), reverse=True):  # 优先长词
                        if length_groups[length]:
                            w = length_groups[length].pop(random.randint(0, len(length_groups[length]) - 1))
                            mixed.append(w)
                            added_this_round = True
                    if not added_this_round:
                        break
                
                # 再打乱一次，避免太规律
                random.shuffle(mixed)
                
                # 强制只使用未使用的词
                if self._force_unused and len(mixed) >= count:
                    return mixed[:count]
                # 否则补充已使用的词（也打乱）
                random.shuffle(used_filtered)
                return (mixed + used_filtered)[:count]
            
            def get_all_words_for_csp(self, group=None):
                # 使用混合词池，未使用的词已经放在前面了
                import random
                mixed_copy = self._mixed.copy()
                # 轻微打乱但保持未使用词优先的大致顺序
                # 分段打乱：前半部分（未使用词为主）和后半部分分别打乱
                half = len(mixed_copy) // 2
                if half > 0:
                    front = mixed_copy[:half]
                    back = mixed_copy[half:]
                    random.shuffle(front)
                    random.shuffle(back)
                    return front + back
                return mixed_copy
        
        temp_vocab = TempVocabManager(unused_for_level, used_for_level, mixed_pool, force_unused_only)
        
        # 使用稀疏布局，传递配置参数
        puzzle = sparse_generator.generate_campaign_level(level, group_code, temp_vocab, config)
        
        if puzzle and len(puzzle.get("words", [])) >= 2:
            puzzle["layout_type"] = "sparse"
            puzzle["group"] = group_code
            puzzle["group_name"] = group_name
            # 设置正确的难度信息
            puzzle["difficulty"] = config["difficulty"]
            puzzle["prefill_ratio"] = config["prefill_ratio"]
            # 备选答案功能已移除
            return puzzle
        
        # 稀疏失败，尝试密集布局
        puzzle = dense_generator.generate_campaign_level(level, group_code, temp_vocab, config)
        
        if puzzle and not puzzle.get("error") and len(puzzle.get("words", [])) >= 2:
            puzzle["layout_type"] = "dense"
            puzzle["group"] = group_code
            puzzle["group_name"] = group_name
            # 设置正确的难度信息
            puzzle["difficulty"] = config["difficulty"]
            puzzle["prefill_ratio"] = config["prefill_ratio"]
            # 备选答案功能已移除
            return puzzle
        
    except Exception as e:
        print(f"    生成失败: {e}")
    
    return {"level": level, "error": True, "message": "生成失败"}


def generate_single_group(group_code: str, vocab_manager=None, sparse_generator=None, dense_generator=None):
    """生成单个分组的所有关卡"""
    
    if group_code not in ALL_GROUPS:
        print(f"错误: 未知的分组代码 {group_code}")
        return None
    
    group_info = ALL_GROUPS[group_code]
    group_name = group_info["name"]
    category = group_info["category"]
    is_primary = group_info.get("is_primary", False)
    max_levels = group_info.get("max_levels", 180 if not is_primary else 117)
    
    print(f"\n{'='*60}")
    print(f"生成 [{category}] {group_name} ({group_code})")
    print(f"目标关卡数: {max_levels} (小学类型: {is_primary})")
    print(f"{'='*60}")
    
    # 初始化生成器（如果未提供）
    if vocab_manager is None:
        vocab_manager = VocabularyManager()
    if sparse_generator is None:
        sparse_generator = CrosswordGenerator()
    if dense_generator is None:
        dense_generator = CSPPuzzleGenerator()
    
    # 获取词汇
    vocab_words = get_vocabulary_for_grade(vocab_manager, group_code)
    print(f"可用词汇: {len(vocab_words)} 个")
    
    # 构建全局词库用于备选答案匹配（合并所有词库）
    global_vocab = []
    global_word_set = set()
    for vc_group in vocab_manager._vocabulary_cache.values():
        for w in vc_group:
            word = w.get("word", "")
            if word and " " not in word and 2 <= len(word) <= 10:
                word_lower = word.lower()
                if word_lower not in global_word_set:
                    global_word_set.add(word_lower)
                    global_vocab.append(w)
    print(f"全局词库（用于备选答案）: {len(global_vocab)} 个")
    
    if len(vocab_words) < 10:
        print(f"警告: 词汇数量不足，跳过此分组")
        return {
            "group_code": group_code,
            "group_name": group_name,
            "category": category,
            "status": "skipped",
            "reason": "词汇不足",
            "word_count": len(vocab_words),
            "level_count": 0,
            "success_count": 0,
            "fail_count": 0,
            "levels": []
        }
    
    # 生成所有关卡
    group_levels = []
    success_count = 0
    fail_count = 0
    all_words_set = set()  # 用于跟踪所有已使用的单词
    
    # 计算可用词数（排除超过10字母的词）
    usable_vocab = [w for w in vocab_words if len(w["word"]) <= 10]
    usable_vocab_size = len(usable_vocab)
    
    # 统一使用85%目标覆盖率
    target_cov = TARGET_COVERAGE  # 85%
    
    print(f"可用词汇（<=10字母）: {usable_vocab_size} 个（原词库: {len(vocab_words)}）")
    print(f"目标覆盖率: {target_cov*100:.0f}%")
    
    # 动态生成：持续生成直到覆盖度>=85%或达到预估关卡上限
    # 预估最大关卡数（按每关4个新词，加上冗余）
    estimated_max = max(max_levels, int(usable_vocab_size / 3 * 1.5) + 100)
    min_levels = PRIMARY_BASE_LEVELS if is_primary else OTHER_BASE_LEVELS  # 最少生成的阶梯关卡数
    
    level = 0
    consecutive_no_new_words = 0  # 连续多少关没有新词
    retry_with_long_words = 0  # 尝试专门用长词生成的次数
    prev_level_words = set()  # 上一关使用的单词，用于避免相邻关卡重复
    
    while True:
        level += 1
        config = get_level_config(level, is_primary, estimated_max)
        
        # 每100关显示一次进度
        if level % 100 == 1:
            print(f"  关卡 {level} ({config['grid_size']}×{config['grid_size']})...", end=" ", flush=True)
        
        # 计算当前覆盖率
        current_coverage = len(all_words_set) / usable_vocab_size * 100 if usable_vocab_size > 0 else 0
        
        # 停止条件：覆盖率达到目标且已完成阶梯关卡
        if current_coverage >= target_cov * 100 and level > min_levels:
            print(f"\n  ✓ 已达到目标覆盖率 {current_coverage:.1f}% >= {target_cov*100:.0f}%，完成生成")
            break
        
        # 安全保护：如果连续100关没有新词或超过预估上限的3倍，尝试长词专用模式
        # 增加容忍度，给更多机会覆盖难以放入的词
        if consecutive_no_new_words >= 100 or level > estimated_max * 3:
            # 检查是否还有未使用的长词（8-10字母）
            remaining_unused = [w for w in usable_vocab if w["word"].upper() not in all_words_set]
            long_unused = [w for w in remaining_unused if len(w["word"]) >= 7]
            
            if long_unused and current_coverage < target_cov * 100:
                print(f"\n  → 尝试长词专用模式（剩余{len(long_unused)}个长词）...")
                
                # 专门用长词尝试生成更多关卡
                long_word_attempts = 0
                max_long_attempts = 50
                consecutive_long_no_new = 0
                
                while long_word_attempts < max_long_attempts and consecutive_long_no_new < 20:
                    long_word_attempts += 1
                    level += 1
                    words_before_long = len(all_words_set)
                    
                    # 强制只使用长词
                    long_unused_current = [w for w in usable_vocab if w["word"].upper() not in all_words_set and len(w["word"]) >= 6]
                    if len(long_unused_current) < 5:
                        break
                    
                    # 用长词生成关卡
                    puzzle = generate_level(
                        sparse_generator, dense_generator,
                        long_unused_current, level, group_code, group_name, is_primary,
                        max_levels=estimated_max,
                        used_words=all_words_set,
                        prev_level_words=prev_level_words,
                        all_vocab=global_vocab  # 传递全局词库用于备选答案匹配
                    )
                    
                    if puzzle.get("error"):
                        fail_count += 1
                    else:
                        words = puzzle.get("words", [])
                        success_count += 1
                        current_words = set()
                        for w in words:
                            word_upper = w["word"].upper()
                            all_words_set.add(word_upper)
                            current_words.add(word_upper)
                        prev_level_words = current_words
                    
                    group_levels.append(puzzle)
                    
                    if len(all_words_set) == words_before_long:
                        consecutive_long_no_new += 1
                    else:
                        consecutive_long_no_new = 0
                
                current_coverage = len(all_words_set) / usable_vocab_size * 100
                print(f"  长词模式完成: 覆盖度 {current_coverage:.1f}%")
            
            print(f"\n  ⚠ 无法继续增加覆盖率，停止生成（已用{len(all_words_set)}/{usable_vocab_size}词）")
            break
        
        words_before = len(all_words_set)
        
        puzzle = generate_level(
            sparse_generator, dense_generator,
            vocab_words, level, group_code, group_name, is_primary,
            max_levels=estimated_max,
            used_words=all_words_set,  # 传递已使用单词集合
            prev_level_words=prev_level_words,  # 传递上一关单词避免重复
            all_vocab=global_vocab  # 传递全局词库用于备选答案匹配
        )
        
        if puzzle.get("error"):
            fail_count += 1
        else:
            words = puzzle.get("words", [])
            success_count += 1
            
            # 收集单词并更新上一关单词集合
            current_words = set()
            for w in words:
                word_upper = w["word"].upper()
                all_words_set.add(word_upper)
                current_words.add(word_upper)
            
            # 更新上一关单词
            prev_level_words = current_words
        
        group_levels.append(puzzle)
        
        # 检查是否有新词
        words_after = len(all_words_set)
        if words_after == words_before:
            consecutive_no_new_words += 1
        else:
            consecutive_no_new_words = 0
        
        # 每100关输出一次进度
        if level % 100 == 0:
            coverage = len(all_words_set) / usable_vocab_size * 100 if usable_vocab_size > 0 else 0
            print(f"已完成 {level}关, 覆盖度: {coverage:.1f}%")
    
    # 计算覆盖度（基于可用词汇，即<=10字母的词）
    coverage = len(all_words_set) / usable_vocab_size * 100 if usable_vocab_size > 0 else 0
    
    # 实际生成的关卡数
    actual_level_count = len(group_levels)
    
    print(f"\n  完成: {success_count}/{actual_level_count} 成功, {fail_count} 失败")
    print(f"  覆盖度: {len(all_words_set)}/{usable_vocab_size} = {coverage:.1f}%")
    
    return {
        "name": group_name,
        "group_code": group_code,
        "category": category,
        "is_primary": is_primary,
        "level_count": actual_level_count,
        "max_levels": actual_level_count,  # 实际生成的关卡数
        "word_count": len(all_words_set),
        "vocab_size": usable_vocab_size,  # 使用可用词库大小
        "original_vocab_size": len(vocab_words),  # 原词库大小
        "coverage": round(coverage, 1),
        "success_count": success_count,
        "fail_count": fail_count,
        "status": "completed",
        "levels": group_levels
    }


def save_group_data(group_code: str, group_data: dict):
    """保存单个分组的数据 - 每关一个JSON文件
    
    新目录结构：
    - levels/{group_code}/1.json
    - levels/{group_code}/2.json
    - ...
    - levels/{group_code}/meta.json (元数据：关卡数量、词库信息等)
    """
    # 创建词库目录
    output_dir = Path(__file__).parent.parent / "data" / "levels" / group_code
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存每一关到单独文件
    levels = group_data.get("levels", [])
    saved_count = 0
    
    for level_data in levels:
        level_num = level_data.get("level", 0)
        if level_num <= 0:
            continue
        
        level_path = output_dir / f"{level_num}.json"
        with open(level_path, "w", encoding="utf-8") as f:
            json.dump(level_data, f, ensure_ascii=False)
        saved_count += 1
    
    # 保存元数据（不含关卡数据，只有统计信息）
    meta = {
        "name": group_data.get("name", ""),
        "group_code": group_code,
        "category": group_data.get("category", ""),
        "is_primary": group_data.get("is_primary", False),
        "level_count": len(levels),
        "word_count": group_data.get("word_count", 0),
        "vocab_size": group_data.get("vocab_size", 0),
        "coverage": group_data.get("coverage", 0),
        "success_count": group_data.get("success_count", 0),
        "fail_count": group_data.get("fail_count", 0)
    }
    
    meta_path = output_dir / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    print(f"  已保存 {saved_count} 个关卡文件到: {output_dir}/")
    return output_dir


def update_summary(all_groups_data: dict):
    """更新汇总文件
    
    从各词库目录的meta.json读取信息，合并生成levels_summary.json
    """
    levels_dir = Path(__file__).parent.parent / "data" / "levels"
    
    # 尝试从已有的meta.json文件中读取信息
    for group_code in ALL_GROUPS.keys():
        if group_code in all_groups_data:
            continue  # 已有数据，跳过
        
        meta_path = levels_dir / group_code / "meta.json"
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    all_groups_data[group_code] = meta
            except:
                pass
    
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_groups": len(all_groups_data),
        "total_levels": sum(g.get("level_count", 0) for g in all_groups_data.values()),
        "success_count": sum(g.get("success_count", 0) for g in all_groups_data.values()),
        "fail_count": sum(g.get("fail_count", 0) for g in all_groups_data.values()),
        "groups": []
    }
    
    for group_code, data in all_groups_data.items():
        summary["groups"].append({
            "group_code": group_code,
            "group_name": data.get("name", data.get("group_name", "")),
            "category": data.get("category", ""),
            "is_primary": data.get("is_primary", False),
            "status": data.get("status", "completed"),
            "word_count": data.get("word_count", 0),
            "vocab_size": data.get("vocab_size", VOCAB_SIZES.get(group_code, 0)),
            "coverage": data.get("coverage", 0),
            "level_count": data.get("level_count", 0),
            "max_levels": data.get("max_levels", data.get("level_count", 0)),
            "success_count": data.get("success_count", 0),
            "fail_count": data.get("fail_count", 0)
        })
    
    summary_path = Path(__file__).parent.parent / "data" / "levels_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"汇总报告已更新: {summary_path}")
    return summary


def generate_all_levels(target_groups=None):
    """生成所有关卡（或指定分组）"""
    print("=" * 70)
    print("开始生成关卡")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 初始化
    vocab_manager = VocabularyManager()
    sparse_generator = CrosswordGenerator()
    dense_generator = CSPPuzzleGenerator()
    
    # 确定要生成的分组
    groups_to_generate = target_groups if target_groups else list(ALL_GROUPS.keys())
    
    # 加载已有数据
    all_results = {}
    levels_dir = Path(__file__).parent.parent / "data" / "levels"
    if levels_dir.exists():
        for f in levels_dir.glob("*.json"):
            group_code = f.stem
            try:
                with open(f, "r", encoding="utf-8") as file:
                    all_results[group_code] = json.load(file)
            except:
                pass
    
    # 遍历要生成的分组
    for group_code in groups_to_generate:
        if group_code not in ALL_GROUPS:
            print(f"警告: 跳过未知分组 {group_code}")
            continue
        
        result = generate_single_group(
            group_code, 
            vocab_manager, 
            sparse_generator, 
            dense_generator
        )
        
        if result:
            all_results[group_code] = result
            save_group_data(group_code, result)
    
    # 更新汇总
    summary = update_summary(all_results)
    
    # 注意：不再保存到 primary_campaign_levels.json 大文件
    # 后端直接从 levels/ 目录加载各个分组数据
    print(f"数据保存完成，后端将从 levels/ 目录加载")
    
    # 打印汇总报告
    print("\n" + "=" * 70)
    print("生成完成 - 汇总报告")
    print("=" * 70)
    print(f"总分组数: {summary['total_groups']}")
    print(f"总关卡数: {summary['total_levels']}")
    print(f"成功: {summary['success_count']}")
    print(f"失败: {summary['fail_count']}")
    if summary['total_levels'] > 0:
        print(f"成功率: {summary['success_count'] / summary['total_levels'] * 100:.1f}%")
    
    print("\n各分组详情:")
    print("-" * 100)
    print(f"{'分类':<8} {'名称':<12} {'状态':<8} {'关卡数':<8} {'词汇量':<8} {'已覆盖':<8} {'覆盖度':<8}")
    print("-" * 100)
    
    for g in summary["groups"]:
        status_str = "✓" if g["status"] == "completed" else "✗"
        coverage_str = f"{g.get('coverage', 0):.1f}%"
        print(f"{g['category']:<8} {g['group_name']:<12} {status_str:<8} {g['max_levels']:<8} {g.get('vocab_size', 0):<8} {g['word_count']:<8} {coverage_str:<8}")
    
    print("-" * 80)
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='生成填单词游戏关卡')
    parser.add_argument('--group', '-g', type=str, action='append', help='指定生成的分组代码（可多次使用，如: -g grade3_1 -g grade3_2）')
    parser.add_argument('--all', '-a', action='store_true', help='生成所有分组')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有分组')
    
    args = parser.parse_args()
    
    if args.list:
        print("可用分组:")
        for code, info in ALL_GROUPS.items():
            print(f"  {code}: {info['name']} ({info['category']}) - {info['max_levels']}关")
    elif args.group:
        generate_all_levels(target_groups=args.group)
    elif args.all:
        generate_all_levels()
    else:
        # 默认生成全部
        generate_all_levels()
