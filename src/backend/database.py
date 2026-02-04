"""
排行榜系统 - SQLite数据库模块
"""
import sqlite3
import os
import json
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# 数据库文件路径 (支持环境变量配置)
_env_data_dir = os.environ.get("WORDCROSS_DATA_DIR")
if _env_data_dir:
    DB_DIR = _env_data_dir
else:
    DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(DB_DIR, "wordcross.db")

# 确保目录存在
os.makedirs(DB_DIR, exist_ok=True)


@contextmanager
def get_db_connection():
    """获取数据库连接（上下文管理器）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 支持字典式访问
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    """初始化数据库表结构"""
    with get_db_connection() as conn:
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
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
        
        # 功能使用统计表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feature_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            feature_name TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            last_used_at DATETIME,
            UNIQUE(user_id, feature_name)
        )
        """)
        
        # 排行榜缓存表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS leaderboard_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lb_type TEXT NOT NULL,
            vocab_group TEXT NOT NULL,
            rank INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            nickname TEXT,
            avatar TEXT,
            value INTEGER,
            extra_data TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lb_type, vocab_group, user_id)
        )
        """)
        
        # 用户行为事件表（记录关键操作）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_data TEXT,
            platform TEXT DEFAULT 'web',
            device_info TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 用户会话表（记录登录会话）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            platform TEXT DEFAULT 'web',
            device_type TEXT,
            browser TEXT,
            os TEXT,
            screen_width INTEGER,
            screen_height INTEGER,
            ip_address TEXT,
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            end_time DATETIME,
            duration_seconds INTEGER DEFAULT 0,
            UNIQUE(session_id)
        )
        """)
        
        # 体力领取记录表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS energy_claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            claim_type TEXT NOT NULL,
            amount INTEGER NOT NULL,
            platform TEXT DEFAULT 'web',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 道具使用记录表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prop_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            prop_type TEXT NOT NULL,
            game_mode TEXT,
            vocab_group TEXT,
            level INTEGER,
            platform TEXT DEFAULT 'web',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 关卡完成记录表（用于分析留存率）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS level_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            vocab_group TEXT NOT NULL,
            level INTEGER NOT NULL,
            stars INTEGER DEFAULT 0,
            score INTEGER DEFAULT 0,
            duration_seconds INTEGER,
            platform TEXT DEFAULT 'web',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, vocab_group, level)
        )
        """)
        
        # 系统配置表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_records_user ON game_records(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_records_mode ON game_records(game_mode)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_records_group ON game_records(vocab_group)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_records_created ON game_records(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_stats_user ON user_stats(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leaderboard_cache_type ON leaderboard_cache(lb_type, vocab_group)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_events_user ON user_events(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_events_type ON user_events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_events_created ON user_events(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_energy_claims_user ON energy_claims(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prop_usage_user ON prop_usage(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_level_completions_user ON level_completions(user_id)")
        
        conn.commit()
        print(f"数据库初始化完成: {DB_PATH}")


# ============ 用户操作 ============

def create_user(user_id: str, nickname: str, avatar: str = "😊") -> Dict:
    """创建用户"""
    now = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (id, nickname, avatar, created_at, last_active_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, nickname, avatar, now, now))
    return get_user(user_id)


def get_user(user_id: str) -> Optional[Dict]:
    """获取用户信息"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def update_user(user_id: str, nickname: str = None, avatar: str = None) -> Optional[Dict]:
    """更新用户信息"""
    updates = []
    values = []
    if nickname is not None:
        updates.append("nickname = ?")
        values.append(nickname)
    if avatar is not None:
        updates.append("avatar = ?")
        values.append(avatar)
    
    if not updates:
        return get_user(user_id)
    
    values.append(user_id)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", values)
    return get_user(user_id)


def update_user_activity(user_id: str):
    """更新用户最后活跃时间"""
    now = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_active_at = ? WHERE id = ?", (now, user_id))


def get_all_users(limit: int = 100, offset: int = 0) -> List[Dict]:
    """获取所有用户（分页）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM users 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """, (limit, offset))
        return [dict(row) for row in cursor.fetchall()]


def get_user_count() -> int:
    """获取用户总数"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]


# ============ 游戏记录操作 ============

def add_game_record(user_id: str, game_mode: str, vocab_group: str,
                    score: int = 0, words_count: int = 0, level_reached: int = 0,
                    duration_seconds: int = None, result: str = None,
                    extra_data: dict = None) -> int:
    """添加游戏记录"""
    now = datetime.now().isoformat()
    extra_json = json.dumps(extra_data) if extra_data else None
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO game_records 
            (user_id, game_mode, vocab_group, score, words_count, level_reached, 
             duration_seconds, result, extra_data, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, game_mode, vocab_group, score, words_count, level_reached,
              duration_seconds, result, extra_json, now))
        
        # 更新用户总游玩次数
        cursor.execute("""
            UPDATE users SET total_play_count = total_play_count + 1, last_active_at = ?
            WHERE id = ?
        """, (now, user_id))
        
        return cursor.lastrowid


def get_user_game_records(user_id: str, game_mode: str = None, limit: int = 50) -> List[Dict]:
    """获取用户游戏记录"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if game_mode:
            cursor.execute("""
                SELECT * FROM game_records 
                WHERE user_id = ? AND game_mode = ?
                ORDER BY created_at DESC LIMIT ?
            """, (user_id, game_mode, limit))
        else:
            cursor.execute("""
                SELECT * FROM game_records 
                WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (user_id, limit))
        
        records = []
        for row in cursor.fetchall():
            record = dict(row)
            if record.get("extra_data"):
                record["extra_data"] = json.loads(record["extra_data"])
            records.append(record)
        return records


# ============ 用户统计操作 ============

def update_user_stats(user_id: str, game_mode: str, vocab_group: str,
                      score: int = 0, words_count: int = 0, level_reached: int = 0,
                      duration_seconds: int = None, result: str = None):
    """更新用户统计数据"""
    now = datetime.now().isoformat()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 先检查是否存在记录
        cursor.execute("""
            SELECT * FROM user_stats 
            WHERE user_id = ? AND game_mode = ? AND vocab_group = ?
        """, (user_id, game_mode, vocab_group))
        existing = cursor.fetchone()
        
        if existing:
            existing = dict(existing)
            # 根据游戏模式更新不同字段
            if game_mode == "campaign":
                new_max_level = max(existing.get("campaign_max_level", 0), level_reached)
                new_total_score = existing.get("campaign_total_score", 0) + score
                new_total_words = existing.get("campaign_total_words", 0) + words_count
                cursor.execute("""
                    UPDATE user_stats SET
                        campaign_max_level = ?,
                        campaign_total_score = ?,
                        campaign_total_words = ?,
                        play_count = play_count + 1,
                        last_played_at = ?,
                        updated_at = ?
                    WHERE user_id = ? AND game_mode = ? AND vocab_group = ?
                """, (new_max_level, new_total_score, new_total_words, now, now,
                      user_id, game_mode, vocab_group))
            
            elif game_mode == "endless":
                new_max_level = max(existing.get("endless_max_level", 0), level_reached)
                new_total_score = existing.get("endless_total_score", 0) + score
                cursor.execute("""
                    UPDATE user_stats SET
                        endless_max_level = ?,
                        endless_total_score = ?,
                        play_count = play_count + 1,
                        last_played_at = ?,
                        updated_at = ?
                    WHERE user_id = ? AND game_mode = ? AND vocab_group = ?
                """, (new_max_level, new_total_score, now, now,
                      user_id, game_mode, vocab_group))
            
            elif game_mode == "timed":
                new_max_words = max(existing.get("timed_max_words", 0), words_count)
                new_total_score = existing.get("timed_total_score", 0) + score
                new_best_time = existing.get("timed_best_time", 0)
                if duration_seconds and (new_best_time == 0 or duration_seconds < new_best_time):
                    new_best_time = duration_seconds
                cursor.execute("""
                    UPDATE user_stats SET
                        timed_max_words = ?,
                        timed_total_score = ?,
                        timed_best_time = ?,
                        play_count = play_count + 1,
                        last_played_at = ?,
                        updated_at = ?
                    WHERE user_id = ? AND game_mode = ? AND vocab_group = ?
                """, (new_max_words, new_total_score, new_best_time, now, now,
                      user_id, game_mode, vocab_group))
            
            elif game_mode == "pk":
                wins = existing.get("pk_wins", 0)
                draws = existing.get("pk_draws", 0)
                losses = existing.get("pk_losses", 0)
                pk_score = existing.get("pk_total_score", 0)
                
                if result == "win":
                    wins += 1
                    pk_score += 3
                elif result == "draw":
                    draws += 1
                    pk_score += 1
                elif result == "lose":
                    losses += 1
                
                cursor.execute("""
                    UPDATE user_stats SET
                        pk_wins = ?,
                        pk_draws = ?,
                        pk_losses = ?,
                        pk_total_score = ?,
                        play_count = play_count + 1,
                        last_played_at = ?,
                        updated_at = ?
                    WHERE user_id = ? AND game_mode = ? AND vocab_group = ?
                """, (wins, draws, losses, pk_score, now, now,
                      user_id, game_mode, vocab_group))
        else:
            # 创建新记录
            pk_wins = 1 if game_mode == "pk" and result == "win" else 0
            pk_draws = 1 if game_mode == "pk" and result == "draw" else 0
            pk_losses = 1 if game_mode == "pk" and result == "lose" else 0
            pk_score_init = 3 if result == "win" else (1 if result == "draw" else 0)
            
            cursor.execute("""
                INSERT INTO user_stats 
                (user_id, game_mode, vocab_group,
                 campaign_max_level, campaign_total_score, campaign_total_words,
                 endless_max_level, endless_total_score,
                 timed_max_words, timed_total_score, timed_best_time,
                 pk_wins, pk_draws, pk_losses, pk_total_score,
                 play_count, last_played_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (
                user_id, game_mode, vocab_group,
                level_reached if game_mode == "campaign" else 0,
                score if game_mode == "campaign" else 0,
                words_count if game_mode == "campaign" else 0,
                level_reached if game_mode == "endless" else 0,
                score if game_mode == "endless" else 0,
                words_count if game_mode == "timed" else 0,
                score if game_mode == "timed" else 0,
                duration_seconds if game_mode == "timed" and duration_seconds else 0,
                pk_wins, pk_draws, pk_losses,
                pk_score_init if game_mode == "pk" else 0,
                now, now
            ))


def get_user_stats(user_id: str, game_mode: str = None) -> List[Dict]:
    """获取用户统计数据"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if game_mode:
            cursor.execute("""
                SELECT * FROM user_stats 
                WHERE user_id = ? AND game_mode = ?
            """, (user_id, game_mode))
        else:
            cursor.execute("SELECT * FROM user_stats WHERE user_id = ?", (user_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_user_all_stats_summary(user_id: str) -> Dict:
    """获取用户全部统计汇总"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 闯关统计
        cursor.execute("""
            SELECT 
                MAX(campaign_max_level) as max_level,
                SUM(campaign_total_score) as total_score,
                SUM(campaign_total_words) as total_words,
                SUM(play_count) as play_count
            FROM user_stats 
            WHERE user_id = ? AND game_mode = 'campaign'
        """, (user_id,))
        campaign = dict(cursor.fetchone() or {})
        
        # 无限模式统计
        cursor.execute("""
            SELECT 
                MAX(endless_max_level) as max_level,
                SUM(endless_total_score) as total_score,
                SUM(play_count) as play_count
            FROM user_stats 
            WHERE user_id = ? AND game_mode = 'endless'
        """, (user_id,))
        endless = dict(cursor.fetchone() or {})
        
        # 计时模式统计
        cursor.execute("""
            SELECT 
                MAX(timed_max_words) as max_words,
                SUM(timed_total_score) as total_score,
                MIN(CASE WHEN timed_best_time > 0 THEN timed_best_time END) as best_time,
                SUM(play_count) as play_count
            FROM user_stats 
            WHERE user_id = ? AND game_mode = 'timed'
        """, (user_id,))
        timed = dict(cursor.fetchone() or {})
        
        # PK模式统计
        cursor.execute("""
            SELECT 
                SUM(pk_wins) as wins,
                SUM(pk_draws) as draws,
                SUM(pk_losses) as losses,
                SUM(pk_total_score) as total_score,
                SUM(play_count) as play_count
            FROM user_stats 
            WHERE user_id = ? AND game_mode = 'pk'
        """, (user_id,))
        pk = dict(cursor.fetchone() or {})
        
        return {
            "campaign": {
                "max_level": campaign.get("max_level") or 0,
                "total_score": campaign.get("total_score") or 0,
                "total_words": campaign.get("total_words") or 0,
                "play_count": campaign.get("play_count") or 0
            },
            "endless": {
                "max_level": endless.get("max_level") or 0,
                "total_score": endless.get("total_score") or 0,
                "play_count": endless.get("play_count") or 0
            },
            "timed": {
                "max_words": timed.get("max_words") or 0,
                "total_score": timed.get("total_score") or 0,
                "best_time": timed.get("best_time") or 0,
                "play_count": timed.get("play_count") or 0
            },
            "pk": {
                "wins": pk.get("wins") or 0,
                "draws": pk.get("draws") or 0,
                "losses": pk.get("losses") or 0,
                "total_score": pk.get("total_score") or 0,
                "play_count": pk.get("play_count") or 0
            }
        }


# ============ 功能使用统计 ============

def record_feature_usage(user_id: str, feature_name: str):
    """记录功能使用"""
    now = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO feature_usage (user_id, feature_name, usage_count, last_used_at)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(user_id, feature_name) 
            DO UPDATE SET usage_count = usage_count + 1, last_used_at = ?
        """, (user_id, feature_name, now, now))


def get_user_feature_usage(user_id: str) -> List[Dict]:
    """获取用户功能使用统计"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT feature_name, usage_count, last_used_at 
            FROM feature_usage 
            WHERE user_id = ?
            ORDER BY usage_count DESC
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_all_feature_usage_stats() -> List[Dict]:
    """获取所有功能使用统计（后台）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                feature_name,
                COUNT(DISTINCT user_id) as user_count,
                SUM(usage_count) as total_usage,
                MAX(last_used_at) as last_used
            FROM feature_usage
            GROUP BY feature_name
            ORDER BY total_usage DESC
        """)
        return [dict(row) for row in cursor.fetchall()]


# ============ 排行榜操作 ============

LEADERBOARD_TYPES = {
    "campaign_level": ("campaign", "campaign_max_level", "max"),
    "campaign_score": ("campaign", "campaign_total_score", "sum"),
    "endless_level": ("endless", "endless_max_level", "max"),
    "endless_score": ("endless", "endless_total_score", "sum"),
    "timed_words": ("timed", "timed_max_words", "max"),
    "timed_score": ("timed", "timed_total_score", "sum"),
    "pk_wins": ("pk", "pk_wins", "sum"),
    "pk_score": ("pk", "pk_total_score", "sum"),
}


def refresh_leaderboard(lb_type: str, vocab_group: str = "all", limit: int = 100):
    """刷新排行榜缓存"""
    if lb_type not in LEADERBOARD_TYPES:
        return
    
    game_mode, field, agg_type = LEADERBOARD_TYPES[lb_type]
    now = datetime.now().isoformat()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 根据分组和聚合类型构建查询
        if vocab_group == "all":
            if agg_type == "max":
                sql = f"""
                    SELECT 
                        us.user_id,
                        u.nickname,
                        u.avatar,
                        MAX(us.{field}) as value,
                        us.vocab_group
                    FROM user_stats us
                    JOIN users u ON us.user_id = u.id
                    WHERE us.game_mode = ?
                    GROUP BY us.user_id
                    ORDER BY value DESC
                    LIMIT ?
                """
            else:  # sum
                sql = f"""
                    SELECT 
                        us.user_id,
                        u.nickname,
                        u.avatar,
                        SUM(us.{field}) as value,
                        'all' as vocab_group
                    FROM user_stats us
                    JOIN users u ON us.user_id = u.id
                    WHERE us.game_mode = ?
                    GROUP BY us.user_id
                    ORDER BY value DESC
                    LIMIT ?
                """
            cursor.execute(sql, (game_mode, limit))
        else:
            sql = f"""
                SELECT 
                    us.user_id,
                    u.nickname,
                    u.avatar,
                    us.{field} as value,
                    us.vocab_group
                FROM user_stats us
                JOIN users u ON us.user_id = u.id
                WHERE us.game_mode = ? AND us.vocab_group = ?
                ORDER BY value DESC
                LIMIT ?
            """
            cursor.execute(sql, (game_mode, vocab_group, limit))
        
        entries = cursor.fetchall()
        
        # 清除旧缓存
        cursor.execute("""
            DELETE FROM leaderboard_cache 
            WHERE lb_type = ? AND vocab_group = ?
        """, (lb_type, vocab_group))
        
        # 插入新缓存
        for rank, entry in enumerate(entries, 1):
            entry = dict(entry)
            extra = {}
            if lb_type.startswith("pk"):
                # 获取PK额外信息
                cursor.execute("""
                    SELECT SUM(pk_wins) as wins, SUM(pk_wins + pk_draws + pk_losses) as games
                    FROM user_stats 
                    WHERE user_id = ? AND game_mode = 'pk'
                """, (entry["user_id"],))
                pk_info = cursor.fetchone()
                if pk_info:
                    extra = {"wins": pk_info[0] or 0, "games": pk_info[1] or 0}
            elif lb_type.startswith("endless"):
                # 获取无限模式总分（累计分数，不清零）
                cursor.execute("""
                    SELECT SUM(endless_total_score) as total_score, MAX(endless_max_level) as max_level
                    FROM user_stats 
                    WHERE user_id = ? AND game_mode = 'endless'
                """, (entry["user_id"],))
                endless_info = cursor.fetchone()
                if endless_info:
                    extra = {
                        "total_score": endless_info[0] or 0,
                        "max_level": endless_info[1] or 0
                    }
            elif lb_type.startswith("timed"):
                # 获取计时模式总分（累计分数，不清零）
                cursor.execute("""
                    SELECT SUM(timed_total_score) as total_score, MAX(timed_max_words) as max_words
                    FROM user_stats 
                    WHERE user_id = ? AND game_mode = 'timed'
                """, (entry["user_id"],))
                timed_info = cursor.fetchone()
                if timed_info:
                    extra = {
                        "total_score": timed_info[0] or 0,
                        "max_words": timed_info[1] or 0
                    }
            
            cursor.execute("""
                INSERT INTO leaderboard_cache 
                (lb_type, vocab_group, rank, user_id, nickname, avatar, value, extra_data, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (lb_type, vocab_group, rank, entry["user_id"], entry["nickname"],
                  entry["avatar"], entry["value"], json.dumps(extra), now))


def get_leaderboard(lb_type: str, vocab_group: str = "all", limit: int = 50) -> List[Dict]:
    """获取排行榜（从缓存）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM leaderboard_cache
            WHERE lb_type = ? AND vocab_group = ?
            ORDER BY rank ASC
            LIMIT ?
        """, (lb_type, vocab_group, limit))
        
        results = []
        for row in cursor.fetchall():
            entry = dict(row)
            if entry.get("extra_data"):
                entry["extra"] = json.loads(entry["extra_data"])
            else:
                entry["extra"] = {}
            del entry["extra_data"]
            results.append(entry)
        return results


def get_user_rank(user_id: str, lb_type: str, vocab_group: str = "all") -> Optional[Dict]:
    """获取用户在排行榜中的排名"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM leaderboard_cache
            WHERE lb_type = ? AND vocab_group = ? AND user_id = ?
        """, (lb_type, vocab_group, user_id))
        row = cursor.fetchone()
        if row:
            entry = dict(row)
            if entry.get("extra_data"):
                entry["extra"] = json.loads(entry["extra_data"])
            else:
                entry["extra"] = {}
            del entry["extra_data"]
            return entry
    return None


def refresh_all_leaderboards():
    """刷新所有排行榜缓存"""
    groups = [
        "all", "grade3_1", "grade3_2", "grade4_1", "grade4_2",
        "grade5_1", "grade5_2", "grade6_1", "grade6_2",
        "junior", "senior", "ket", "pet",
        "cet4", "cet6", "postgrad", "ielts", "toefl", "gre"
    ]
    
    for lb_type in LEADERBOARD_TYPES.keys():
        for group in groups:
            refresh_leaderboard(lb_type, group)
    
    print(f"排行榜刷新完成: {len(LEADERBOARD_TYPES)} 类型 x {len(groups)} 分组")


# ============ 后台统计 ============

def get_daily_stats(days: int = 30) -> List[Dict]:
    """获取每日统计"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as game_count,
                COUNT(DISTINCT user_id) as active_users,
                SUM(score) as total_score,
                SUM(words_count) as total_words
            FROM game_records
            WHERE created_at >= DATE('now', ?)
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, (f'-{days} days',))
        return [dict(row) for row in cursor.fetchall()]


def get_mode_stats() -> List[Dict]:
    """获取各模式统计"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                game_mode,
                COUNT(*) as game_count,
                COUNT(DISTINCT user_id) as user_count,
                SUM(score) as total_score,
                SUM(words_count) as total_words,
                AVG(duration_seconds) as avg_duration
            FROM game_records
            GROUP BY game_mode
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_group_stats() -> List[Dict]:
    """获取各分组统计"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                vocab_group,
                COUNT(*) as game_count,
                COUNT(DISTINCT user_id) as user_count,
                SUM(score) as total_score,
                SUM(words_count) as total_words
            FROM game_records
            GROUP BY vocab_group
            ORDER BY game_count DESC
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_overview_stats() -> Dict:
    """获取整体统计概览"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 用户统计
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # 今日活跃用户
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM game_records
            WHERE DATE(created_at) = DATE('now')
        """)
        today_active = cursor.fetchone()[0]
        
        # 总游戏次数
        cursor.execute("SELECT COUNT(*) FROM game_records")
        total_games = cursor.fetchone()[0]
        
        # 今日游戏次数
        cursor.execute("""
            SELECT COUNT(*) FROM game_records
            WHERE DATE(created_at) = DATE('now')
        """)
        today_games = cursor.fetchone()[0]
        
        # 总积分
        cursor.execute("SELECT SUM(score) FROM game_records")
        total_score = cursor.fetchone()[0] or 0
        
        # 总单词数
        cursor.execute("SELECT SUM(words_count) FROM game_records")
        total_words = cursor.fetchone()[0] or 0
        
        return {
            "total_users": total_users,
            "today_active_users": today_active,
            "total_games": total_games,
            "today_games": today_games,
            "total_score": total_score,
            "total_words": total_words
        }


# ============ 用户行为事件 ============

def record_user_event(user_id: str, event_type: str, event_data: dict = None,
                      platform: str = "web", device_info: str = None):
    """记录用户行为事件"""
    now = datetime.now().isoformat()
    event_json = json.dumps(event_data) if event_data else None
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_events (user_id, event_type, event_data, platform, device_info, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, event_type, event_json, platform, device_info, now))
        return cursor.lastrowid


def get_event_stats(event_type: str = None, days: int = 30) -> List[Dict]:
    """获取事件统计"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if event_type:
            cursor.execute("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as count,
                    COUNT(DISTINCT user_id) as user_count
                FROM user_events
                WHERE event_type = ? AND created_at >= DATE('now', ?)
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """, (event_type, f'-{days} days'))
        else:
            cursor.execute("""
                SELECT 
                    event_type,
                    COUNT(*) as total_count,
                    COUNT(DISTINCT user_id) as user_count
                FROM user_events
                WHERE created_at >= DATE('now', ?)
                GROUP BY event_type
                ORDER BY total_count DESC
            """, (f'-{days} days',))
        return [dict(row) for row in cursor.fetchall()]


# ============ 用户会话管理 ============

def create_session(user_id: str, session_id: str, platform: str = "web",
                   device_type: str = None, browser: str = None, os: str = None,
                   screen_width: int = None, screen_height: int = None,
                   ip_address: str = None) -> int:
    """创建用户会话"""
    now = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_sessions 
            (user_id, session_id, platform, device_type, browser, os, 
             screen_width, screen_height, ip_address, start_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, session_id, platform, device_type, browser, os,
              screen_width, screen_height, ip_address, now))
        return cursor.lastrowid


def end_session(session_id: str):
    """结束会话并计算时长"""
    now = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 先获取开始时间
        cursor.execute("SELECT start_time FROM user_sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if row:
            start_time = datetime.fromisoformat(row[0])
            duration = int((datetime.now() - start_time).total_seconds())
            cursor.execute("""
                UPDATE user_sessions 
                SET end_time = ?, duration_seconds = ?
                WHERE session_id = ?
            """, (now, duration, session_id))


def get_platform_stats(days: int = 30) -> List[Dict]:
    """获取平台分布统计"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                platform,
                COUNT(*) as session_count,
                COUNT(DISTINCT user_id) as user_count,
                AVG(duration_seconds) as avg_duration
            FROM user_sessions
            WHERE start_time >= DATE('now', ?)
            GROUP BY platform
        """, (f'-{days} days',))
        return [dict(row) for row in cursor.fetchall()]


def get_device_stats(days: int = 30) -> List[Dict]:
    """获取设备类型统计"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                device_type,
                COUNT(*) as count,
                COUNT(DISTINCT user_id) as user_count
            FROM user_sessions
            WHERE start_time >= DATE('now', ?) AND device_type IS NOT NULL
            GROUP BY device_type
            ORDER BY count DESC
        """, (f'-{days} days',))
        return [dict(row) for row in cursor.fetchall()]


def get_browser_stats(days: int = 30) -> List[Dict]:
    """获取浏览器统计"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                browser,
                COUNT(*) as count,
                COUNT(DISTINCT user_id) as user_count
            FROM user_sessions
            WHERE start_time >= DATE('now', ?) AND browser IS NOT NULL
            GROUP BY browser
            ORDER BY count DESC
        """, (f'-{days} days',))
        return [dict(row) for row in cursor.fetchall()]


def get_os_stats(days: int = 30) -> List[Dict]:
    """获取操作系统统计"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                os,
                COUNT(*) as count,
                COUNT(DISTINCT user_id) as user_count
            FROM user_sessions
            WHERE start_time >= DATE('now', ?) AND os IS NOT NULL
            GROUP BY os
            ORDER BY count DESC
        """, (f'-{days} days',))
        return [dict(row) for row in cursor.fetchall()]


# ============ 体力领取记录 ============

def record_energy_claim(user_id: str, claim_type: str, amount: int, platform: str = "web"):
    """记录体力领取"""
    now = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO energy_claims (user_id, claim_type, amount, platform, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, claim_type, amount, platform, now))
        return cursor.lastrowid


def get_energy_claim_stats(days: int = 30) -> Dict:
    """获取体力领取统计"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 总体统计
        cursor.execute("""
            SELECT 
                claim_type,
                COUNT(*) as claim_count,
                SUM(amount) as total_amount,
                COUNT(DISTINCT user_id) as user_count
            FROM energy_claims
            WHERE created_at >= DATE('now', ?)
            GROUP BY claim_type
        """, (f'-{days} days',))
        by_type = [dict(row) for row in cursor.fetchall()]
        
        # 每日统计
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as claim_count,
                SUM(amount) as total_amount
            FROM energy_claims
            WHERE created_at >= DATE('now', ?)
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, (f'-{days} days',))
        daily = [dict(row) for row in cursor.fetchall()]
        
        return {"by_type": by_type, "daily": daily}


# ============ 道具使用记录 ============

def record_prop_usage(user_id: str, prop_type: str, game_mode: str = None,
                      vocab_group: str = None, level: int = None, platform: str = "web"):
    """记录道具使用"""
    now = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO prop_usage (user_id, prop_type, game_mode, vocab_group, level, platform, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, prop_type, game_mode, vocab_group, level, platform, now))
        return cursor.lastrowid


def get_prop_usage_stats(days: int = 30) -> Dict:
    """获取道具使用统计"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 按类型统计
        cursor.execute("""
            SELECT 
                prop_type,
                COUNT(*) as usage_count,
                COUNT(DISTINCT user_id) as user_count
            FROM prop_usage
            WHERE created_at >= DATE('now', ?)
            GROUP BY prop_type
        """, (f'-{days} days',))
        by_type = [dict(row) for row in cursor.fetchall()]
        
        # 按游戏模式统计
        cursor.execute("""
            SELECT 
                game_mode,
                prop_type,
                COUNT(*) as usage_count
            FROM prop_usage
            WHERE created_at >= DATE('now', ?) AND game_mode IS NOT NULL
            GROUP BY game_mode, prop_type
        """, (f'-{days} days',))
        by_mode = [dict(row) for row in cursor.fetchall()]
        
        # 每日统计
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                prop_type,
                COUNT(*) as usage_count
            FROM prop_usage
            WHERE created_at >= DATE('now', ?)
            GROUP BY DATE(created_at), prop_type
            ORDER BY date DESC
        """, (f'-{days} days',))
        daily = [dict(row) for row in cursor.fetchall()]
        
        return {"by_type": by_type, "by_mode": by_mode, "daily": daily}


# ============ 关卡完成记录 ============

def record_level_completion(user_id: str, vocab_group: str, level: int,
                            stars: int = 0, score: int = 0, duration_seconds: int = None,
                            platform: str = "web"):
    """记录关卡完成"""
    now = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO level_completions 
            (user_id, vocab_group, level, stars, score, duration_seconds, platform, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, vocab_group, level, stars, score, duration_seconds, platform, now))
        return cursor.lastrowid


def get_level_retention_stats(vocab_group: str = None, max_level: int = 50) -> List[Dict]:
    """获取关卡留存率统计（分析哪些关卡流失最多）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if vocab_group:
            cursor.execute("""
                SELECT 
                    level,
                    COUNT(DISTINCT user_id) as player_count,
                    AVG(stars) as avg_stars,
                    AVG(duration_seconds) as avg_duration
                FROM level_completions
                WHERE vocab_group = ? AND level <= ?
                GROUP BY level
                ORDER BY level
            """, (vocab_group, max_level))
        else:
            cursor.execute("""
                SELECT 
                    level,
                    COUNT(DISTINCT user_id) as player_count,
                    AVG(stars) as avg_stars,
                    AVG(duration_seconds) as avg_duration
                FROM level_completions
                WHERE level <= ?
                GROUP BY level
                ORDER BY level
            """, (max_level,))
        
        return [dict(row) for row in cursor.fetchall()]


def get_level_dropoff_analysis(vocab_group: str = None) -> List[Dict]:
    """分析关卡流失点"""
    retention = get_level_retention_stats(vocab_group)
    if len(retention) < 2:
        return []
    
    dropoff = []
    for i in range(1, len(retention)):
        prev = retention[i-1]
        curr = retention[i]
        if prev['player_count'] > 0:
            retention_rate = curr['player_count'] / prev['player_count']
            dropoff.append({
                "from_level": prev['level'],
                "to_level": curr['level'],
                "from_players": prev['player_count'],
                "to_players": curr['player_count'],
                "retention_rate": round(retention_rate * 100, 1),
                "dropoff_rate": round((1 - retention_rate) * 100, 1)
            })
    
    # 按流失率排序，找出流失最严重的关卡
    dropoff.sort(key=lambda x: x['dropoff_rate'], reverse=True)
    return dropoff


# ============ 用户成就统计 ============

def get_user_achievements(user_id: str) -> Dict:
    """获取用户成就统计"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 闯关成就
        cursor.execute("""
            SELECT 
                vocab_group,
                MAX(level) as max_level,
                COUNT(*) as completed_levels,
                SUM(CASE WHEN stars = 3 THEN 1 ELSE 0 END) as three_star_count,
                SUM(score) as total_score
            FROM level_completions
            WHERE user_id = ?
            GROUP BY vocab_group
        """, (user_id,))
        campaign_achievements = [dict(row) for row in cursor.fetchall()]
        
        # 游戏统计
        stats = get_user_all_stats_summary(user_id)
        
        # 功能使用
        features = get_user_feature_usage(user_id)
        
        # 最近游戏
        cursor.execute("""
            SELECT * FROM game_records
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        """, (user_id,))
        recent_games = [dict(row) for row in cursor.fetchall()]
        
        return {
            "campaign_achievements": campaign_achievements,
            "stats": stats,
            "features": features,
            "recent_games": recent_games
        }


# ============ 高级统计查询 ============

def get_hourly_activity(days: int = 7) -> List[Dict]:
    """获取每小时活跃度分布"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                strftime('%H', created_at) as hour,
                COUNT(*) as game_count,
                COUNT(DISTINCT user_id) as user_count
            FROM game_records
            WHERE created_at >= DATE('now', ?)
            GROUP BY strftime('%H', created_at)
            ORDER BY hour
        """, (f'-{days} days',))
        return [dict(row) for row in cursor.fetchall()]


def get_retention_analysis(days: int = 30) -> Dict:
    """获取用户留存分析"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 新用户数（按日）
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as new_users
            FROM users
            WHERE created_at >= DATE('now', ?)
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, (f'-{days} days',))
        new_users = [dict(row) for row in cursor.fetchall()]
        
        # 次日留存
        cursor.execute("""
            SELECT 
                u.date as register_date,
                COUNT(DISTINCT g.user_id) as returned_users
            FROM (
                SELECT DATE(created_at) as date, id
                FROM users
                WHERE created_at >= DATE('now', ?)
            ) u
            LEFT JOIN game_records g ON u.id = g.user_id 
                AND DATE(g.created_at) = DATE(u.date, '+1 day')
            GROUP BY u.date
        """, (f'-{days} days',))
        day1_retention = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 7日留存
        cursor.execute("""
            SELECT 
                u.date as register_date,
                COUNT(DISTINCT g.user_id) as returned_users
            FROM (
                SELECT DATE(created_at) as date, id
                FROM users
                WHERE created_at >= DATE('now', ?)
            ) u
            LEFT JOIN game_records g ON u.id = g.user_id 
                AND DATE(g.created_at) BETWEEN DATE(u.date, '+1 day') AND DATE(u.date, '+7 day')
            GROUP BY u.date
        """, (f'-{days} days',))
        day7_retention = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "new_users": new_users,
            "day1_retention": day1_retention,
            "day7_retention": day7_retention
        }


def get_top_players(limit: int = 20) -> List[Dict]:
    """获取顶级玩家列表"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                u.id,
                u.nickname,
                u.avatar,
                u.total_play_count,
                u.created_at,
                COALESCE(SUM(gr.score), 0) as total_score,
                COALESCE(SUM(gr.words_count), 0) as total_words,
                COUNT(gr.id) as game_count
            FROM users u
            LEFT JOIN game_records gr ON u.id = gr.user_id
            GROUP BY u.id
            ORDER BY total_score DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


def get_vocab_group_analysis() -> List[Dict]:
    """获取词库使用分析"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                vocab_group,
                COUNT(DISTINCT user_id) as unique_players,
                COUNT(*) as total_games,
                SUM(score) as total_score,
                SUM(words_count) as total_words,
                AVG(duration_seconds) as avg_duration,
                MAX(level_reached) as max_level_reached
            FROM game_records
            GROUP BY vocab_group
            ORDER BY total_games DESC
        """)
        return [dict(row) for row in cursor.fetchall()]


# ============ 系统配置 ============

def get_config(key: str, default: str = None) -> Optional[str]:
    """获取系统配置"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_config WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default


def set_config(key: str, value: str):
    """设置系统配置"""
    now = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO system_config (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, value, now))


def get_admin_password_hash() -> Optional[str]:
    """获取管理员密码哈希"""
    return get_config("admin_password_hash")


def set_admin_password_hash(password_hash: str):
    """设置管理员密码哈希"""
    set_config("admin_password_hash", password_hash)


# 初始化数据库
init_database()
