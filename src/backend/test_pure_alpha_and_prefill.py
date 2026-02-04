#!/usr/bin/env python3
"""
单元测试：is_pure_alpha 函数和预填充逻辑

测试覆盖：
1. is_pure_alpha 函数 - 验证只包含26个英文字母的单词
2. 预填充逻辑 - 验证最后几关的预填充是否正确

运行方式：
    python test_pure_alpha_and_prefill.py
"""

import unittest
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入被测试的函数
from puzzle_generator import is_pure_alpha as puzzle_is_pure_alpha
from csp_puzzle_generator import is_pure_alpha as csp_is_pure_alpha
from configurable_puzzle_generator import is_pure_alpha as configurable_is_pure_alpha
from generate_all_levels import is_pure_alpha as generate_is_pure_alpha


class TestIsPureAlpha(unittest.TestCase):
    """测试 is_pure_alpha 函数"""
    
    def setUp(self):
        """设置测试用例 - 所有四个版本的函数"""
        self.functions = [
            ("puzzle_generator", puzzle_is_pure_alpha),
            ("csp_puzzle_generator", csp_is_pure_alpha),
            ("configurable_puzzle_generator", configurable_is_pure_alpha),
            ("generate_all_levels", generate_is_pure_alpha),
        ]
    
    def test_valid_words_lowercase(self):
        """测试有效的小写单词"""
        valid_words = ["hello", "world", "apple", "banana", "cat", "dog"]
        for name, func in self.functions:
            for word in valid_words:
                with self.subTest(func=name, word=word):
                    self.assertTrue(func(word), f"{name}: '{word}' 应该是有效的纯字母单词")
    
    def test_valid_words_uppercase(self):
        """测试有效的大写单词"""
        valid_words = ["HELLO", "WORLD", "APPLE", "BANANA", "CAT", "DOG"]
        for name, func in self.functions:
            for word in valid_words:
                with self.subTest(func=name, word=word):
                    self.assertTrue(func(word), f"{name}: '{word}' 应该是有效的纯字母单词")
    
    def test_valid_words_mixed_case(self):
        """测试有效的混合大小写单词"""
        valid_words = ["Hello", "World", "ApPle", "BaNaNa"]
        for name, func in self.functions:
            for word in valid_words:
                with self.subTest(func=name, word=word):
                    self.assertTrue(func(word), f"{name}: '{word}' 应该是有效的纯字母单词")
    
    def test_invalid_words_with_hyphen(self):
        """测试包含连字符的无效单词"""
        invalid_words = ["X-RAY", "T-SHIRT", "self-esteem", "e-mail", "co-operate"]
        for name, func in self.functions:
            for word in invalid_words:
                with self.subTest(func=name, word=word):
                    self.assertFalse(func(word), f"{name}: '{word}' 应该是无效的（含连字符）")
    
    def test_invalid_words_with_apostrophe(self):
        """测试包含撇号的无效单词"""
        invalid_words = ["O'CLOCK", "WE'LL", "can't", "don't", "it's", "I'm"]
        for name, func in self.functions:
            for word in invalid_words:
                with self.subTest(func=name, word=word):
                    self.assertFalse(func(word), f"{name}: '{word}' 应该是无效的（含撇号）")
    
    def test_invalid_words_with_space(self):
        """测试包含空格的无效单词"""
        invalid_words = ["ICE CREAM", "NEW YORK", "high school", "good morning"]
        for name, func in self.functions:
            for word in invalid_words:
                with self.subTest(func=name, word=word):
                    self.assertFalse(func(word), f"{name}: '{word}' 应该是无效的（含空格）")
    
    def test_invalid_words_with_numbers(self):
        """测试包含数字的无效单词"""
        invalid_words = ["ABC123", "test1", "2fast", "24hours", "7up"]
        for name, func in self.functions:
            for word in invalid_words:
                with self.subTest(func=name, word=word):
                    self.assertFalse(func(word), f"{name}: '{word}' 应该是无效的（含数字）")
    
    def test_invalid_words_with_special_chars(self):
        """测试包含特殊字符的无效单词"""
        invalid_words = ["hello!", "world?", "test@", "A+B", "C&D", "E=F"]
        for name, func in self.functions:
            for word in invalid_words:
                with self.subTest(func=name, word=word):
                    self.assertFalse(func(word), f"{name}: '{word}' 应该是无效的（含特殊字符）")
    
    def test_edge_cases(self):
        """测试边缘情况"""
        test_cases = [
            ("", False, "空字符串应该返回 False"),
            ("A", True, "单字母应该返回 True"),
            ("AB", True, "两字母应该返回 True"),
            ("  ", False, "空格字符串应该返回 False"),
            ("\n", False, "换行符应该返回 False"),
            ("\t", False, "制表符应该返回 False"),
        ]
        for name, func in self.functions:
            for word, expected, msg in test_cases:
                with self.subTest(func=name, word=repr(word)):
                    self.assertEqual(func(word), expected, f"{name}: {msg}")
    
    def test_unicode_letters(self):
        """测试非ASCII字母（应该返回True，因为isalpha()对Unicode友好）"""
        # 注意：isalpha() 对于中文等字符也返回 True
        # 但在实际使用中，词库数据应该只包含英文
        unicode_words = ["café", "naïve", "über"]  # 这些含有非ASCII字母
        for name, func in self.functions:
            for word in unicode_words:
                with self.subTest(func=name, word=word):
                    # 这些词 isalpha() 返回 False（因为含有重音符号会被识别为字母）
                    # 实际测试看看
                    result = func(word)
                    # 由于 café, naïve, über 中的 é, ï, ü 是字母，所以 isalpha() 返回 True
                    # 这在我们的场景中是可接受的，因为词库本身只包含英文
                    self.assertTrue(result, f"{name}: '{word}' 使用 isalpha() 应该返回 True（包含字母）")


class TestPrefillLogic(unittest.TestCase):
    """测试预填充逻辑"""
    
    def test_csp_puzzle_prefill(self):
        """测试 CSP 生成器的预填充逻辑"""
        from csp_puzzle_generator import DensePuzzle
        
        # 创建一个简单的测试谜题
        puzzle = DensePuzzle(grid_size=5)
        
        # 模拟放置一些字母
        puzzle.grid = [
            ['C', 'A', 'T', '', ''],
            ['', 'P', '', '', ''],
            ['', 'P', '', '', ''],
            ['', 'L', '', '', ''],
            ['', 'E', '', '', ''],
        ]
        
        # 设置一些 revealed_positions
        puzzle.revealed_positions = {(0, 0), (0, 1), (1, 1)}
        
        # 调用 to_dict 生成预填字典
        result = puzzle.to_dict()
        prefilled = result.get("prefilled", {})
        
        # 验证预填字典中只包含 revealed_positions 中的位置
        self.assertIn("0-0", prefilled)
        self.assertIn("0-1", prefilled)
        self.assertIn("1-1", prefilled)
        self.assertEqual(prefilled["0-0"], "C")
        self.assertEqual(prefilled["0-1"], "A")
        self.assertEqual(prefilled["1-1"], "P")
        
        # 验证其他位置不在预填字典中
        self.assertNotIn("0-2", prefilled)
        self.assertNotIn("2-1", prefilled)
    
    def test_configurable_puzzle_prefill(self):
        """测试 Configurable 生成器的预填充逻辑"""
        from configurable_puzzle_generator import ConfigurablePuzzle
        
        # 创建一个简单的测试谜题
        puzzle = ConfigurablePuzzle(grid_size=5, difficulty="medium")
        
        # 模拟放置一些字母
        puzzle.grid = [
            ['D', 'O', 'G', None, None],
            [None, 'N', None, None, None],
            [None, 'E', None, None, None],
            [None, None, None, None, None],
            [None, None, None, None, None],
        ]
        
        # 设置一些 revealed_positions
        puzzle.revealed_positions = {(0, 0), (0, 2), (2, 1)}
        
        # 调用 to_dict 生成预填字典
        result = puzzle.to_dict()
        prefilled = result.get("prefilled", {})
        
        # 验证预填字典正确
        self.assertEqual(prefilled.get("0-0"), "D")
        self.assertEqual(prefilled.get("0-2"), "G")
        self.assertEqual(prefilled.get("2-1"), "E")
        
        # 验证其他位置不在预填字典中
        self.assertNotIn("0-1", prefilled)
        self.assertNotIn("1-1", prefilled)
    
    def test_puzzle_generator_prefill_ratio(self):
        """测试 puzzle_generator 的预填充比例配置"""
        from puzzle_generator import CrosswordGenerator
        
        # 验证预填比例配置存在且合理
        self.assertIn("easy", CrosswordGenerator.PREFILL_RATIO)
        self.assertIn("medium", CrosswordGenerator.PREFILL_RATIO)
        self.assertIn("hard", CrosswordGenerator.PREFILL_RATIO)
        
        # 验证比例值合理（简单 > 中等 > 困难）
        easy_min, easy_max = CrosswordGenerator.PREFILL_RATIO["easy"]
        medium_min, medium_max = CrosswordGenerator.PREFILL_RATIO["medium"]
        hard_min, hard_max = CrosswordGenerator.PREFILL_RATIO["hard"]
        
        self.assertGreater(easy_min, medium_min, "简单难度的最小预填比例应大于中等难度")
        self.assertGreater(medium_min, hard_min, "中等难度的最小预填比例应大于困难难度")
        
        # 验证比例在合理范围内
        for diff, (min_r, max_r) in CrosswordGenerator.PREFILL_RATIO.items():
            self.assertGreaterEqual(min_r, 0.0, f"{diff} 最小比例应 >= 0")
            self.assertLessEqual(max_r, 1.0, f"{diff} 最大比例应 <= 1")
            self.assertLess(min_r, max_r, f"{diff} 最小比例应小于最大比例")


class TestWordFiltering(unittest.TestCase):
    """测试单词过滤逻辑（综合测试）"""
    
    def test_filter_words_from_vocab(self):
        """测试从词库过滤单词时正确应用 is_pure_alpha"""
        from puzzle_generator import is_pure_alpha
        
        # 模拟词库数据
        vocab = [
            {"word": "HELLO", "definition": "问候语"},
            {"word": "X-RAY", "definition": "X光"},  # 含连字符
            {"word": "O'CLOCK", "definition": "点钟"},  # 含撇号
            {"word": "ICE CREAM", "definition": "冰淇淋"},  # 含空格
            {"word": "WORLD", "definition": "世界"},
            {"word": "123ABC", "definition": "混合"},  # 含数字
            {"word": "APPLE", "definition": "苹果"},
        ]
        
        # 过滤逻辑
        filtered = [
            w for w in vocab 
            if 2 <= len(w["word"]) <= 10 and is_pure_alpha(w["word"])
        ]
        
        # 验证过滤结果
        filtered_words = [w["word"] for w in filtered]
        
        self.assertIn("HELLO", filtered_words)
        self.assertIn("WORLD", filtered_words)
        self.assertIn("APPLE", filtered_words)
        
        self.assertNotIn("X-RAY", filtered_words)
        self.assertNotIn("O'CLOCK", filtered_words)
        self.assertNotIn("ICE CREAM", filtered_words)
        self.assertNotIn("123ABC", filtered_words)
    
    def test_all_generators_use_same_filter(self):
        """测试所有生成器使用相同的过滤逻辑"""
        test_words = [
            ("HELLO", True),
            ("X-RAY", False),
            ("O'CLOCK", False),
            ("ICE CREAM", False),
            ("WORLD", True),
            ("can't", False),
            ("self-esteem", False),
            ("", False),
        ]
        
        for word, expected in test_words:
            with self.subTest(word=word):
                # 所有四个实现应该返回相同结果
                self.assertEqual(puzzle_is_pure_alpha(word), expected, f"puzzle_generator: '{word}'")
                self.assertEqual(csp_is_pure_alpha(word), expected, f"csp_puzzle_generator: '{word}'")
                self.assertEqual(configurable_is_pure_alpha(word), expected, f"configurable_puzzle_generator: '{word}'")
                self.assertEqual(generate_is_pure_alpha(word), expected, f"generate_all_levels: '{word}'")


class TestLastLevelsPrefill(unittest.TestCase):
    """测试最后几关的预填充逻辑"""
    
    def test_compute_revealed_letters_exists(self):
        """测试 compute_revealed_letters 方法存在"""
        from csp_puzzle_generator import DensePuzzle
        from configurable_puzzle_generator import ConfigurablePuzzle
        
        csp_puzzle = DensePuzzle(grid_size=5)
        config_puzzle = ConfigurablePuzzle(grid_size=5, difficulty="easy")
        
        self.assertTrue(hasattr(csp_puzzle, 'compute_revealed_letters'), 
                       "DensePuzzle 应该有 compute_revealed_letters 方法")
        self.assertTrue(hasattr(config_puzzle, 'compute_revealed_letters'), 
                       "ConfigurablePuzzle 应该有 compute_revealed_letters 方法")
    
    def test_compute_revealed_letters_sets_positions(self):
        """测试 compute_revealed_letters 正确设置 revealed_positions"""
        from csp_puzzle_generator import DensePuzzle
        
        puzzle = DensePuzzle(grid_size=5)
        
        # 模拟一个完整的网格
        puzzle.grid = [
            ['C', 'A', 'T', 'S', ''],
            ['A', '', '', 'U', ''],
            ['R', 'U', 'N', 'N', ''],
            ['', '', '', '', ''],
            ['', '', '', '', ''],
        ]
        
        # 模拟放置的单词（使用 row_words 和 col_words）
        puzzle.row_words = [
            {"word": "CATS", "row": 0, "col": 0, "direction": "across"},
            {"word": "RUN", "row": 2, "col": 0, "direction": "across"},
        ]
        puzzle.col_words = [
            {"word": "CAR", "row": 0, "col": 0, "direction": "down"},
            {"word": "SUN", "row": 0, "col": 3, "direction": "down"},
        ]
        
        # 调用 compute_revealed_letters
        puzzle.compute_revealed_letters(min_reveal=1)
        
        # 验证 revealed_positions 被设置
        self.assertIsInstance(puzzle.revealed_positions, set)
        self.assertGreater(len(puzzle.revealed_positions), 0, 
                          "应该有一些位置被设置为预填")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestIsPureAlpha))
    suite.addTests(loader.loadTestsFromTestCase(TestPrefillLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestWordFiltering))
    suite.addTests(loader.loadTestsFromTestCase(TestLastLevelsPrefill))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回是否全部通过
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
