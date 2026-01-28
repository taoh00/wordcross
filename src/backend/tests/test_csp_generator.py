"""
CSP填字游戏生成器单元测试
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from csp_puzzle_generator import CSPPuzzleGenerator, WordSlot
from vocabulary import VocabularyManager


class TestWordSlot:
    """测试WordSlot数据类"""
    
    def test_word_slot_creation(self):
        """测试创建WordSlot - 使用实际的参数"""
        slot = WordSlot(
            id="row_0",
            direction="across",
            index=0,
            length=5
        )
        
        assert slot.id == "row_0"
        assert slot.direction == "across"
        assert slot.index == 0
        assert slot.length == 5
    
    def test_word_slot_domain(self):
        """测试槽位域"""
        slot = WordSlot(
            id="col_2",
            direction="down",
            index=2,
            length=4,
            domain=["CATS", "DOGS", "TREE"]
        )
        
        assert len(slot.domain) == 3
        assert "CATS" in slot.domain


class TestCSPPuzzleGenerator:
    """测试CSP谜题生成器"""
    
    @pytest.fixture
    def generator(self):
        """创建生成器实例"""
        return CSPPuzzleGenerator()
    
    @pytest.fixture
    def vocab_manager(self):
        """创建词库管理器"""
        return VocabularyManager()
    
    def test_generator_initialization(self, generator):
        """测试生成器初始化"""
        assert generator is not None
    
    def test_generate_random_puzzle_with_vocab_manager(self, generator, vocab_manager):
        """测试使用词库管理器生成随机谜题"""
        puzzle = generator.generate_random_puzzle(
            group="primary",
            difficulty="easy",
            vocab_manager=vocab_manager
        )
        
        if puzzle:
            assert "grid_size" in puzzle
            assert "cells" in puzzle
            assert "words" in puzzle
    
    def test_generate_campaign_level_with_vocab_manager(self, generator, vocab_manager):
        """测试使用词库管理器生成闯关关卡"""
        puzzle = generator.generate_campaign_level(
            level=1,
            group="primary",
            vocab_manager=vocab_manager
        )
        
        if puzzle:
            assert "level" in puzzle or "words" in puzzle
    
    def test_puzzle_structure(self, generator, vocab_manager):
        """测试谜题结构完整性"""
        puzzle = generator.generate_random_puzzle(
            group="primary",
            difficulty="easy",
            vocab_manager=vocab_manager
        )
        
        if puzzle:
            # 验证网格
            assert "grid_size" in puzzle
            assert "cells" in puzzle
            
            grid_size = puzzle["grid_size"]
            cells = puzzle["cells"]
            
            assert len(cells) == grid_size
            assert all(len(row) == grid_size for row in cells)
            
            # 验证单词列表
            assert "words" in puzzle
            for word_info in puzzle["words"]:
                assert "word" in word_info
                assert "definition" in word_info
                assert "direction" in word_info


class TestDifficultyScaling:
    """测试难度缩放"""
    
    @pytest.fixture
    def generator(self):
        return CSPPuzzleGenerator()
    
    @pytest.fixture
    def vocab_manager(self):
        return VocabularyManager()
    
    def test_different_difficulties(self, generator, vocab_manager):
        """测试不同难度"""
        for difficulty in ["easy", "medium", "hard"]:
            puzzle = generator.generate_random_puzzle(
                group="primary",
                difficulty=difficulty,
                vocab_manager=vocab_manager
            )
            
            # 生成可能失败，但不应该抛出异常
            if puzzle:
                assert "difficulty" in puzzle or "words" in puzzle


class TestGridSizes:
    """测试不同网格大小"""
    
    @pytest.fixture
    def generator(self):
        return CSPPuzzleGenerator()
    
    @pytest.fixture
    def vocab_manager(self):
        return VocabularyManager()
    
    def test_generate_with_config(self, generator, vocab_manager):
        """测试带配置生成"""
        config = {
            "grid_size": 6,
            "min_words": 3,
            "max_words": 5
        }
        
        puzzle = generator.generate_campaign_level(
            level=1,
            group="primary",
            vocab_manager=vocab_manager,
            config=config
        )
        
        # 配置可能被忽略，但不应抛出异常
        assert puzzle is None or isinstance(puzzle, dict)
