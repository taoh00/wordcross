"""
填字游戏生成器单元测试
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from puzzle_generator import (
    is_pure_alpha, Word, PlacedWord, CrosswordPuzzle, 
    CrosswordGenerator, PROGRESSIVE_LEVEL_CONFIG
)


class TestWord:
    """测试Word数据类"""
    
    def test_word_creation(self):
        """测试创建Word对象"""
        word = Word(id=1, text="CAT", definition="猫", difficulty=1)
        assert word.id == 1
        assert word.text == "CAT"
        assert word.definition == "猫"
        assert word.difficulty == 1
    
    def test_word_default_difficulty(self):
        """测试默认难度"""
        word = Word(id=1, text="DOG", definition="狗")
        assert word.difficulty == 1


class TestPlacedWord:
    """测试PlacedWord数据类"""
    
    def test_placed_word_across(self):
        """测试横向放置的单词"""
        word = Word(id=1, text="CAT", definition="猫")
        placed = PlacedWord(word=word, row=0, col=0, direction="across")
        
        assert placed.row == 0
        assert placed.col == 0
        assert placed.direction == "across"
        assert placed.end_row == 0
        assert placed.end_col == 2  # CAT长度3，从0开始，结束于2
    
    def test_placed_word_down(self):
        """测试纵向放置的单词"""
        word = Word(id=1, text="CAT", definition="猫")
        placed = PlacedWord(word=word, row=0, col=0, direction="down")
        
        assert placed.end_row == 2  # CAT长度3，从0开始，结束于2
        assert placed.end_col == 0


class TestCrosswordPuzzle:
    """测试CrosswordPuzzle类"""
    
    def test_puzzle_initialization(self):
        """测试谜题初始化"""
        puzzle = CrosswordPuzzle(grid_size=5)
        
        assert puzzle.grid_size == 5
        assert len(puzzle.grid) == 5
        assert all(len(row) == 5 for row in puzzle.grid)
        assert all(cell is None for row in puzzle.grid for cell in row)
    
    def test_puzzle_to_dict(self):
        """测试转换为字典格式"""
        puzzle = CrosswordPuzzle(grid_size=5)
        word = Word(id=1, text="CAT", definition="猫")
        placed = PlacedWord(word=word, row=0, col=0, direction="across")
        
        # 放置单词
        puzzle.placed_words.append(placed)
        for i, letter in enumerate("CAT"):
            puzzle.grid[0][i] = letter
        
        result = puzzle.to_dict()
        
        assert "grid_size" in result
        assert "cells" in result
        assert "words" in result
        assert "prefilled" in result
        assert result["grid_size"] == 5
        assert len(result["words"]) == 1
    
    def test_puzzle_clue_numbers(self):
        """测试线索编号系统"""
        puzzle = CrosswordPuzzle(grid_size=5)
        
        # 添加两个单词在不同位置
        word1 = Word(id=1, text="CAT", definition="猫")
        word2 = Word(id=2, text="DOG", definition="狗")
        
        placed1 = PlacedWord(word=word1, row=0, col=0, direction="across")
        placed2 = PlacedWord(word=word2, row=2, col=0, direction="across")
        
        puzzle.placed_words.extend([placed1, placed2])
        
        result = puzzle.to_dict()
        
        # 验证线索编号
        words = result["words"]
        assert len(words) == 2
        assert words[0]["clue_number"] == 1
        assert words[1]["clue_number"] == 2


class TestCrosswordGenerator:
    """测试填字游戏生成器"""
    
    @pytest.fixture
    def generator(self):
        """创建生成器实例"""
        return CrosswordGenerator()
    
    def test_generator_initialization(self, generator):
        """测试生成器初始化"""
        assert generator is not None
        assert hasattr(generator, "_valid_words_set")
    
    def test_level_config_defined(self):
        """测试关卡配置已定义"""
        assert len(CrosswordGenerator.LEVEL_CONFIG) > 0
        
        for level_range, config in CrosswordGenerator.LEVEL_CONFIG.items():
            start, end = level_range
            grid_size, min_words, max_words, max_word_len = config
            
            assert start <= end
            assert grid_size >= 5
            assert min_words > 0
            assert max_words >= min_words
            assert max_word_len >= 2
    
    def test_difficulty_config_defined(self):
        """测试难度配置已定义"""
        assert "easy" in CrosswordGenerator.DIFFICULTY_CONFIG
        assert "medium" in CrosswordGenerator.DIFFICULTY_CONFIG
        assert "hard" in CrosswordGenerator.DIFFICULTY_CONFIG
    
    def test_prefill_ratio_defined(self):
        """测试预填比例已定义"""
        assert "easy" in CrosswordGenerator.PREFILL_RATIO
        assert "medium" in CrosswordGenerator.PREFILL_RATIO
        assert "hard" in CrosswordGenerator.PREFILL_RATIO
        
        for difficulty, (min_ratio, max_ratio) in CrosswordGenerator.PREFILL_RATIO.items():
            assert 0 <= min_ratio <= max_ratio <= 1
    
    def test_progressive_level_config(self):
        """测试渐进式关卡配置"""
        assert len(PROGRESSIVE_LEVEL_CONFIG) == 10
        
        for level in range(1, 11):
            assert level in PROGRESSIVE_LEVEL_CONFIG
            config = PROGRESSIVE_LEVEL_CONFIG[level]
            grid_size, min_words, max_words, max_word_len, difficulty, prefill_boost = config
            
            assert grid_size >= 5
            assert min_words > 0
            assert max_words >= min_words
            assert difficulty in ["easy", "medium", "hard"]
            assert 0 <= prefill_boost <= 1


class TestPuzzleGeneration:
    """测试谜题生成功能"""
    
    @pytest.fixture
    def generator(self):
        return CrosswordGenerator(random_seed=42)  # 固定种子以便重现
    
    def test_generator_has_valid_words_set(self, generator):
        """测试生成器有有效单词集"""
        assert hasattr(generator, "_valid_words_set")
        assert isinstance(generator._valid_words_set, set)
    
    def test_manual_puzzle_creation(self, generator):
        """测试手动创建谜题"""
        puzzle = CrosswordPuzzle(grid_size=5)
        
        # 手动放置单词
        word1 = Word(id=1, text="CAT", definition="猫")
        word2 = Word(id=2, text="TEN", definition="十")
        
        placed1 = PlacedWord(word=word1, row=0, col=0, direction="across")
        placed2 = PlacedWord(word=word2, row=0, col=2, direction="down")
        
        puzzle.placed_words.append(placed1)
        puzzle.placed_words.append(placed2)
        
        # 填充网格
        for i, letter in enumerate("CAT"):
            puzzle.grid[0][i] = letter
        for i, letter in enumerate("TEN"):
            puzzle.grid[i][2] = letter
        
        # 验证
        assert len(puzzle.placed_words) == 2
        assert puzzle.grid[0][2] == "T"  # 交叉点


class TestIsPureAlpha:
    """测试纯字母检查"""
    
    def test_valid_words(self):
        """测试有效单词"""
        assert is_pure_alpha("hello") == True
        assert is_pure_alpha("WORLD") == True
        assert is_pure_alpha("Test") == True
    
    def test_invalid_words(self):
        """测试无效单词"""
        assert is_pure_alpha("hello-world") == False
        assert is_pure_alpha("it's") == False
        assert is_pure_alpha("ice cream") == False
        assert is_pure_alpha("mp3") == False
        assert is_pure_alpha("") == False
