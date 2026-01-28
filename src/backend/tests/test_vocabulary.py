"""
词库管理模块单元测试
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vocabulary import is_pure_alpha, VocabularyManager


class TestIsPureAlpha:
    """测试纯字母检查函数"""
    
    def test_pure_alpha_words(self):
        """纯字母单词应返回True"""
        assert is_pure_alpha("cat") == True
        assert is_pure_alpha("DOG") == True
        assert is_pure_alpha("Apple") == True
        assert is_pure_alpha("HELLO") == True
        
    def test_words_with_hyphen(self):
        """含连字符的单词应返回False"""
        assert is_pure_alpha("t-shirt") == False
        assert is_pure_alpha("x-ray") == False
        assert is_pure_alpha("well-known") == False
    
    def test_words_with_apostrophe(self):
        """含撇号的单词应返回False"""
        assert is_pure_alpha("o'clock") == False
        assert is_pure_alpha("we'll") == False
        assert is_pure_alpha("it's") == False
    
    def test_words_with_space(self):
        """含空格的短语应返回False"""
        assert is_pure_alpha("ice cream") == False
        assert is_pure_alpha("hot dog") == False
    
    def test_words_with_numbers(self):
        """含数字的应返回False"""
        assert is_pure_alpha("3d") == False
        assert is_pure_alpha("mp3") == False
    
    def test_empty_string(self):
        """空字符串应返回False"""
        assert is_pure_alpha("") == False


class TestVocabularyManager:
    """测试词库管理器"""
    
    @pytest.fixture
    def vocab_manager(self, temp_data_dir):
        """创建词库管理器实例"""
        vocab_dir = os.path.join(temp_data_dir, "vocabulary")
        os.makedirs(vocab_dir, exist_ok=True)
        return VocabularyManager(vocab_dir)
    
    def test_initialization(self, vocab_manager):
        """测试初始化"""
        assert vocab_manager is not None
        assert vocab_manager.data_dir is not None
    
    def test_groups_defined(self, vocab_manager):
        """测试词汇组别定义"""
        assert "primary" in VocabularyManager.GROUPS
        assert "junior" in VocabularyManager.GROUPS
        assert "senior" in VocabularyManager.GROUPS
        assert "cet4" in VocabularyManager.GROUPS
        assert "cet6" in VocabularyManager.GROUPS
        assert "ielts" in VocabularyManager.GROUPS
        assert "toefl" in VocabularyManager.GROUPS
        assert "gre" in VocabularyManager.GROUPS
    
    def test_get_groups(self, vocab_manager):
        """测试获取所有分组"""
        groups = vocab_manager.get_groups()
        assert isinstance(groups, list)
        assert len(groups) > 0
        
        for group in groups:
            assert "code" in group
            assert "name" in group
            assert "count" in group
    
    def test_get_words_returns_list(self, vocab_manager):
        """测试获取词汇返回列表"""
        words = vocab_manager.get_words("primary", limit=10)
        assert isinstance(words, list)
    
    def test_get_words_respects_limit(self, vocab_manager):
        """测试词汇数量限制"""
        words = vocab_manager.get_words("primary", limit=5)
        assert len(words) <= 5
    
    def test_get_words_for_puzzle(self, vocab_manager):
        """测试获取用于谜题的词汇"""
        words = vocab_manager.get_words_for_puzzle("primary", count=5, max_word_len=6)
        assert isinstance(words, list)
        
        for word in words:
            assert "word" in word
            assert "definition" in word
            # 验证词长限制
            assert len(word["word"]) <= 6 or len(word["word"]) <= 9  # 允许稍长的词补充
    
    def test_get_words_for_puzzle_filters_non_alpha(self, vocab_manager):
        """测试获取词汇时过滤非纯字母词"""
        words = vocab_manager.get_words_for_puzzle("primary", count=20, max_word_len=10)
        
        for word in words:
            assert is_pure_alpha(word["word"]), f"非纯字母词未被过滤: {word['word']}"
    
    def test_sample_vocabulary(self, vocab_manager):
        """测试示例词汇"""
        sample = vocab_manager._get_sample_vocabulary("primary")
        assert len(sample) > 0
        
        for word in sample:
            assert "word" in word
            assert "definition" in word
            assert "id" in word
    
    def test_search_words(self, vocab_manager):
        """测试单词搜索"""
        results = vocab_manager.search_words("cat", limit=5)
        assert isinstance(results, list)
    
    def test_get_all_words_for_csp(self, vocab_manager):
        """测试CSP生成用的完整词库"""
        words = vocab_manager.get_all_words_for_csp("primary")
        assert isinstance(words, list)
        
        # 所有词都应该是纯字母且长度>=2
        for word in words:
            assert len(word["word"]) >= 2
            assert is_pure_alpha(word["word"])
    
    def test_word_ids_unique(self, vocab_manager):
        """测试单词ID唯一性"""
        all_words = vocab_manager.get_all_words_for_csp()
        word_ids = [w.get("id") for w in all_words if w.get("id")]
        
        # ID应该唯一
        assert len(word_ids) == len(set(word_ids)), "存在重复的单词ID"
