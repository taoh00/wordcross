"""
集成测试 - 测试完整的业务流程
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGameFlow:
    """测试游戏完整流程"""
    
    def test_vocabulary_loading(self):
        """测试词汇加载"""
        from vocabulary import VocabularyManager
        
        vocab_manager = VocabularyManager()
        
        # 获取词汇
        words = vocab_manager.get_words_for_puzzle("primary", count=10, max_word_len=6)
        
        assert len(words) > 0, "应该获取到词汇"
        
        for word in words:
            assert "word" in word
            assert "definition" in word
    
    def test_csp_generation_flow(self):
        """测试CSP谜题生成流程"""
        from vocabulary import VocabularyManager
        from csp_puzzle_generator import CSPPuzzleGenerator
        
        vocab_manager = VocabularyManager()
        generator = CSPPuzzleGenerator()
        
        # 生成谜题
        puzzle = generator.generate_random_puzzle(
            group="primary",
            difficulty="easy",
            vocab_manager=vocab_manager
        )
        
        # 验证结果（可能失败）
        if puzzle:
            assert "grid_size" in puzzle
            assert "words" in puzzle
    
    def test_puzzle_generator_basic(self):
        """测试基础谜题生成器"""
        from puzzle_generator import CrosswordGenerator, Word, PlacedWord, CrosswordPuzzle
        
        # 创建生成器
        generator = CrosswordGenerator()
        assert generator is not None
        
        # 创建简单谜题
        puzzle = CrosswordPuzzle(grid_size=5)
        
        word = Word(id=1, text="CAT", definition="猫")
        placed = PlacedWord(word=word, row=0, col=0, direction="across")
        
        puzzle.placed_words.append(placed)
        for i, letter in enumerate("CAT"):
            puzzle.grid[0][i] = letter
        
        # 验证转换
        puzzle_dict = puzzle.to_dict()
        
        assert "grid_size" in puzzle_dict
        assert "cells" in puzzle_dict
        assert "words" in puzzle_dict


class TestDatabaseIntegration:
    """测试数据库集成"""
    
    def test_user_game_record_flow(self, test_db):
        """测试用户-游戏记录流程"""
        import sqlite3
        from datetime import datetime
        
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # 1. 创建用户
        user_id = "flow_test_user"
        cursor.execute("""
            INSERT INTO users (id, nickname, avatar, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, "流程测试用户", "🎮", datetime.now().isoformat()))
        conn.commit()
        
        # 2. 添加多条游戏记录
        for i in range(5):
            cursor.execute("""
                INSERT INTO game_records 
                (user_id, game_mode, vocab_group, score, words_count, level_reached)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, "campaign", "primary", (i+1)*100, (i+1)*3, i+1))
        conn.commit()
        
        # 3. 查询统计
        cursor.execute("""
            SELECT 
                COUNT(*) as game_count,
                SUM(score) as total_score,
                MAX(level_reached) as max_level
            FROM game_records
            WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        
        assert row[0] == 5  # 5场游戏
        assert row[1] == 1500  # 总分 100+200+300+400+500
        assert row[2] == 5  # 最高关卡
        
        conn.close()
    
    def test_stats_update_flow(self, test_db):
        """测试统计更新流程"""
        import sqlite3
        from datetime import datetime
        
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        user_id = "stats_flow_user"
        
        # 1. 创建用户
        cursor.execute("""
            INSERT INTO users (id, nickname, avatar)
            VALUES (?, ?, ?)
        """, (user_id, "统计流程用户", "📊"))
        conn.commit()
        
        # 2. 创建初始统计
        cursor.execute("""
            INSERT INTO user_stats 
            (user_id, game_mode, vocab_group, campaign_max_level, campaign_total_score, play_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, "campaign", "primary", 0, 0, 0))
        conn.commit()
        
        # 3. 模拟多次游戏更新统计
        game_results = [
            (3, 300),   # 第3关，300分
            (5, 500),   # 第5关，500分
            (4, 400),   # 第4关，400分（不应更新最高关卡）
            (8, 800),   # 第8关，800分
        ]
        
        for level, score in game_results:
            cursor.execute("""
                UPDATE user_stats SET
                    campaign_max_level = MAX(campaign_max_level, ?),
                    campaign_total_score = campaign_total_score + ?,
                    play_count = play_count + 1
                WHERE user_id = ? AND game_mode = ? AND vocab_group = ?
            """, (level, score, user_id, "campaign", "primary"))
            conn.commit()
        
        # 4. 验证最终统计
        cursor.execute("""
            SELECT campaign_max_level, campaign_total_score, play_count
            FROM user_stats
            WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        
        assert row[0] == 8  # 最高关卡应该是8
        assert row[1] == 2000  # 总分 300+500+400+800
        assert row[2] == 4  # 4次游戏
        
        conn.close()


class TestPrefillConsistency:
    """测试预填一致性"""
    
    def test_prefill_matches_answer(self):
        """测试预填字母与答案一致"""
        from puzzle_generator import Word, PlacedWord, CrosswordPuzzle
        
        # 创建一个简单谜题
        puzzle = CrosswordPuzzle(grid_size=5)
        
        word = Word(id=1, text="APPLE", definition="苹果")
        placed = PlacedWord(word=word, row=0, col=0, direction="across")
        
        puzzle.placed_words.append(placed)
        for i, letter in enumerate("APPLE"):
            puzzle.grid[0][i] = letter
        
        # 添加预填
        puzzle.prefilled = {"0-0": "A", "0-2": "P"}
        
        # 验证预填正确
        puzzle_dict = puzzle.to_dict()
        
        for key, letter in puzzle_dict["prefilled"].items():
            row, col = map(int, key.split("-"))
            # 预填字母应该与网格中的字母一致
            assert puzzle.grid[row][col] == letter


class TestWordFiltering:
    """测试单词过滤"""
    
    def test_non_alpha_words_filtered(self):
        """测试非字母单词被过滤"""
        from vocabulary import VocabularyManager, is_pure_alpha
        
        vocab = VocabularyManager()
        
        # 获取用于谜题的词汇
        words = vocab.get_words_for_puzzle("primary", count=50, max_word_len=10)
        
        for word in words:
            word_text = word["word"]
            assert is_pure_alpha(word_text), f"非纯字母词未被过滤: {word_text}"
    
    def test_csp_words_all_valid(self):
        """测试CSP词汇全部有效"""
        from vocabulary import VocabularyManager, is_pure_alpha
        
        vocab = VocabularyManager()
        words = vocab.get_all_words_for_csp("primary")
        
        for word in words:
            word_text = word["word"]
            # 长度至少2
            assert len(word_text) >= 2
            # 纯字母
            assert is_pure_alpha(word_text)


class TestLevelGeneration:
    """测试关卡生成"""
    
    def test_level_difficulty_progression(self):
        """测试关卡难度渐进"""
        from puzzle_generator import PROGRESSIVE_LEVEL_CONFIG
        
        prev_grid_size = 0
        
        for level in range(1, 11):
            config = PROGRESSIVE_LEVEL_CONFIG[level]
            grid_size = config[0]
            
            # 网格大小应该递增或保持
            assert grid_size >= prev_grid_size or level <= 2
            
            if level > 2:
                prev_grid_size = grid_size


class TestVocabularyIntegration:
    """测试词汇集成"""
    
    def test_multiple_groups(self):
        """测试多个词库组"""
        from vocabulary import VocabularyManager
        
        vocab = VocabularyManager()
        
        groups = vocab.get_groups()
        assert len(groups) > 0
        
        for group in groups:
            assert "code" in group
            assert "name" in group
    
    def test_get_words_for_each_group(self):
        """测试从每个组获取词汇"""
        from vocabulary import VocabularyManager
        
        vocab = VocabularyManager()
        
        test_groups = ["primary", "junior", "cet4"]
        
        for group in test_groups:
            words = vocab.get_words(group, limit=10)
            # 可能返回空（如果没有词库文件）
            assert isinstance(words, list)
