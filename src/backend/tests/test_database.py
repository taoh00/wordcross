"""
数据库模块单元测试
"""
import pytest
import sys
import os
import sqlite3
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDatabaseConnection:
    """测试数据库连接"""
    
    def test_database_file_created(self, test_db):
        """测试数据库文件创建"""
        assert os.path.exists(test_db)
    
    def test_tables_created(self, test_db):
        """测试表结构创建"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # 查询所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # 验证核心表存在
        assert "users" in tables
        assert "game_records" in tables
        assert "user_stats" in tables
        
        conn.close()


class TestUserOperations:
    """测试用户操作"""
    
    def test_create_user(self, test_db):
        """测试创建用户"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        user_id = "test_user_1"
        nickname = "测试用户"
        avatar = "😊"
        
        cursor.execute("""
            INSERT INTO users (id, nickname, avatar, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, nickname, avatar, datetime.now().isoformat()))
        conn.commit()
        
        # 验证用户创建成功
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] == user_id  # id
        assert row[1] == nickname  # nickname
        
        conn.close()
    
    def test_get_user(self, test_db):
        """测试获取用户"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # 先创建用户
        user_id = "test_user_2"
        cursor.execute("""
            INSERT INTO users (id, nickname, avatar)
            VALUES (?, ?, ?)
        """, (user_id, "用户2", "🎮"))
        conn.commit()
        
        # 获取用户
        cursor.execute("SELECT id, nickname, avatar FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] == user_id
        assert row[1] == "用户2"
        assert row[2] == "🎮"
        
        conn.close()
    
    def test_update_user(self, test_db):
        """测试更新用户"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # 创建用户
        user_id = "test_user_3"
        cursor.execute("""
            INSERT INTO users (id, nickname, avatar)
            VALUES (?, ?, ?)
        """, (user_id, "原昵称", "😊"))
        conn.commit()
        
        # 更新昵称
        new_nickname = "新昵称"
        cursor.execute("""
            UPDATE users SET nickname = ? WHERE id = ?
        """, (new_nickname, user_id))
        conn.commit()
        
        # 验证更新
        cursor.execute("SELECT nickname FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        assert row[0] == new_nickname
        
        conn.close()
    
    def test_user_not_found(self, test_db):
        """测试用户不存在"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", ("nonexistent_user",))
        row = cursor.fetchone()
        
        assert row is None
        
        conn.close()


class TestGameRecords:
    """测试游戏记录"""
    
    def test_add_game_record(self, test_db):
        """测试添加游戏记录"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # 先创建用户
        user_id = "game_record_user"
        cursor.execute("""
            INSERT INTO users (id, nickname, avatar)
            VALUES (?, ?, ?)
        """, (user_id, "游戏用户", "🎮"))
        conn.commit()
        
        # 添加游戏记录
        cursor.execute("""
            INSERT INTO game_records 
            (user_id, game_mode, vocab_group, score, words_count, level_reached)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, "campaign", "primary", 100, 5, 3))
        conn.commit()
        
        # 验证记录
        cursor.execute("SELECT * FROM game_records WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[1] == user_id  # user_id
        assert row[2] == "campaign"  # game_mode
        assert row[3] == "primary"  # vocab_group
        assert row[4] == 100  # score
        
        conn.close()
    
    def test_get_user_game_records(self, test_db):
        """测试获取用户游戏记录"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # 创建用户和多条记录
        user_id = "multi_record_user"
        cursor.execute("""
            INSERT INTO users (id, nickname, avatar)
            VALUES (?, ?, ?)
        """, (user_id, "多记录用户", "🎮"))
        
        # 添加多条记录
        for i in range(5):
            cursor.execute("""
                INSERT INTO game_records 
                (user_id, game_mode, vocab_group, score, words_count)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, "endless", "junior", i * 100, i * 3))
        conn.commit()
        
        # 获取记录
        cursor.execute("""
            SELECT * FROM game_records 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        
        assert len(rows) == 5
        
        conn.close()


class TestUserStats:
    """测试用户统计"""
    
    def test_create_user_stats(self, test_db):
        """测试创建用户统计"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # 创建用户
        user_id = "stats_user"
        cursor.execute("""
            INSERT INTO users (id, nickname, avatar)
            VALUES (?, ?, ?)
        """, (user_id, "统计用户", "📊"))
        
        # 创建统计记录
        cursor.execute("""
            INSERT INTO user_stats 
            (user_id, game_mode, vocab_group, campaign_max_level, campaign_total_score)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, "campaign", "primary", 10, 1000))
        conn.commit()
        
        # 验证
        cursor.execute("""
            SELECT campaign_max_level, campaign_total_score 
            FROM user_stats 
            WHERE user_id = ? AND game_mode = ?
        """, (user_id, "campaign"))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] == 10  # max_level
        assert row[1] == 1000  # total_score
        
        conn.close()
    
    def test_update_campaign_stats(self, test_db):
        """测试更新闯关统计"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        user_id = "campaign_stats_user"
        
        # 创建用户和初始统计
        cursor.execute("""
            INSERT INTO users (id, nickname, avatar)
            VALUES (?, ?, ?)
        """, (user_id, "闯关用户", "🎯"))
        
        cursor.execute("""
            INSERT INTO user_stats 
            (user_id, game_mode, vocab_group, campaign_max_level, campaign_total_score, play_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, "campaign", "primary", 5, 500, 5))
        conn.commit()
        
        # 更新统计（模拟新的游戏记录）
        cursor.execute("""
            UPDATE user_stats SET
                campaign_max_level = MAX(campaign_max_level, ?),
                campaign_total_score = campaign_total_score + ?,
                play_count = play_count + 1
            WHERE user_id = ? AND game_mode = ? AND vocab_group = ?
        """, (8, 200, user_id, "campaign", "primary"))
        conn.commit()
        
        # 验证更新
        cursor.execute("""
            SELECT campaign_max_level, campaign_total_score, play_count 
            FROM user_stats 
            WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        
        assert row[0] == 8  # 新的最高关卡
        assert row[1] == 700  # 累计分数
        assert row[2] == 6  # 游戏次数
        
        conn.close()
    
    def test_unique_constraint(self, test_db):
        """测试唯一约束"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        user_id = "unique_test_user"
        
        cursor.execute("""
            INSERT INTO users (id, nickname, avatar)
            VALUES (?, ?, ?)
        """, (user_id, "唯一约束测试", "🔒"))
        
        # 第一次插入
        cursor.execute("""
            INSERT INTO user_stats 
            (user_id, game_mode, vocab_group)
            VALUES (?, ?, ?)
        """, (user_id, "campaign", "primary"))
        conn.commit()
        
        # 第二次插入相同组合应该失败
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO user_stats 
                (user_id, game_mode, vocab_group)
                VALUES (?, ?, ?)
            """, (user_id, "campaign", "primary"))
            conn.commit()
        
        conn.close()


class TestDataIntegrity:
    """测试数据完整性"""
    
    def test_foreign_key_concept(self, test_db):
        """测试外键概念（SQLite默认不强制，但验证逻辑关系）"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # 添加游戏记录时，user_id应该指向有效用户
        user_id = "integrity_user"
        
        cursor.execute("""
            INSERT INTO users (id, nickname, avatar)
            VALUES (?, ?, ?)
        """, (user_id, "完整性测试", "✅"))
        conn.commit()
        
        # 使用有效user_id添加记录
        cursor.execute("""
            INSERT INTO game_records 
            (user_id, game_mode, vocab_group, score)
            VALUES (?, ?, ?, ?)
        """, (user_id, "campaign", "primary", 100))
        conn.commit()
        
        # 验证关联查询
        cursor.execute("""
            SELECT u.nickname, g.score 
            FROM users u 
            JOIN game_records g ON u.id = g.user_id
            WHERE u.id = ?
        """, (user_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] == "完整性测试"
        assert row[1] == 100
        
        conn.close()
