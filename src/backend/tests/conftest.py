"""
pytest配置和共享fixtures
"""
import pytest
import os
import sys
import tempfile
import sqlite3

# 添加后端目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置测试环境
os.environ["WORDCROSS_DATA_DIR"] = tempfile.mkdtemp()


@pytest.fixture(scope="session")
def temp_data_dir():
    """创建临时数据目录"""
    temp_dir = tempfile.mkdtemp()
    os.makedirs(os.path.join(temp_dir, "vocabulary"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "levels"), exist_ok=True)
    return temp_dir


@pytest.fixture(scope="function")
def test_db(temp_data_dir):
    """创建测试用数据库"""
    db_path = os.path.join(temp_data_dir, "test_wordcross.db")
    
    # 如果存在旧数据库则删除
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # 创建新数据库
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # 创建表结构
    cursor = conn.cursor()
    
    # 用户表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        nickname TEXT NOT NULL,
        avatar TEXT DEFAULT '😊',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_active_at DATETIME,
        total_play_count INTEGER DEFAULT 0
    )
    """)
    
    # 游戏记录表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS game_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        game_mode TEXT NOT NULL,
        vocab_group TEXT NOT NULL,
        score INTEGER DEFAULT 0,
        words_count INTEGER DEFAULT 0,
        level_reached INTEGER DEFAULT 0,
        duration_seconds INTEGER,
        result TEXT,
        extra_data TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 用户统计表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        game_mode TEXT NOT NULL,
        vocab_group TEXT NOT NULL,
        campaign_max_level INTEGER DEFAULT 0,
        campaign_total_score INTEGER DEFAULT 0,
        campaign_total_words INTEGER DEFAULT 0,
        endless_max_level INTEGER DEFAULT 0,
        endless_total_score INTEGER DEFAULT 0,
        timed_max_words INTEGER DEFAULT 0,
        timed_total_score INTEGER DEFAULT 0,
        timed_best_time INTEGER DEFAULT 0,
        pk_wins INTEGER DEFAULT 0,
        pk_draws INTEGER DEFAULT 0,
        pk_losses INTEGER DEFAULT 0,
        pk_total_score INTEGER DEFAULT 0,
        play_count INTEGER DEFAULT 0,
        last_played_at DATETIME,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, game_mode, vocab_group)
    )
    """)
    
    conn.commit()
    
    yield db_path
    
    # 清理
    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def sample_words():
    """提供测试用的单词列表"""
    return [
        {"word": "cat", "definition": "猫", "difficulty": 1, "id": 1},
        {"word": "dog", "definition": "狗", "difficulty": 1, "id": 2},
        {"word": "sun", "definition": "太阳", "difficulty": 1, "id": 3},
        {"word": "moon", "definition": "月亮", "difficulty": 1, "id": 4},
        {"word": "star", "definition": "星星", "difficulty": 1, "id": 5},
        {"word": "book", "definition": "书", "difficulty": 1, "id": 6},
        {"word": "apple", "definition": "苹果", "difficulty": 1, "id": 7},
        {"word": "tree", "definition": "树", "difficulty": 1, "id": 8},
        {"word": "water", "definition": "水", "difficulty": 1, "id": 9},
        {"word": "fire", "definition": "火", "difficulty": 1, "id": 10},
    ]


@pytest.fixture
def sample_puzzle_data():
    """提供测试用的谜题数据"""
    return {
        "grid_size": 5,
        "cells": [
            ["C", "A", "T", None, None],
            [None, None, "E", None, None],
            [None, None, "S", None, None],
            [None, None, "T", None, None],
            [None, None, None, None, None],
        ],
        "words": [
            {
                "id": 1,
                "word": "CAT",
                "definition": "猫",
                "direction": "across",
                "start_row": 0,
                "start_col": 0,
                "length": 3,
                "clue_number": 1,
            },
            {
                "id": 2,
                "word": "TEST",
                "definition": "测试",
                "direction": "down",
                "start_row": 0,
                "start_col": 2,
                "length": 4,
                "clue_number": 2,
            },
        ],
        "prefilled": {"0-0": "C"},
    }
