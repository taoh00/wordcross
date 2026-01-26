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
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_records_user ON game_records(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_records_mode ON game_records(game_mode)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_records_group ON game_records(vocab_group)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_records_created ON game_records(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_stats_user ON user_stats(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leaderboard_cache_type ON leaderboard_cache(lb_type, vocab_group)")
        
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


# 初始化数据库
init_database()
