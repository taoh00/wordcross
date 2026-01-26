"""
我爱填单词 WordCross - FastAPI Backend
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import random
import os
import uuid
import time

from puzzle_generator import CrosswordGenerator
from csp_puzzle_generator import CSPPuzzleGenerator
from configurable_puzzle_generator import ConfigurablePuzzleGenerator, DIFFICULTY_CONFIG, QUANTITY_CONFIG
from vocabulary import VocabularyManager
import database as db

app = FastAPI(
    title="我爱填单词 WordCross API",
    description="填单词游戏后端API",
    version="1.0.0"
)

# 数据目录（支持环境变量配置）
_env_data_dir = os.environ.get("WORDCROSS_DATA_DIR")
if _env_data_dir:
    DATA_DIR = _env_data_dir
else:
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# 静态文件目录（Docker环境不需要，nginx直接服务）
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

# 音频文件目录
_env_audio_dir = os.environ.get("WORDCROSS_AUDIO_DIR")
if _env_audio_dir:
    AUDIO_DIR = _env_audio_dir
else:
    AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "audio")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化词汇管理器和关卡生成器
vocab_manager = VocabularyManager()
puzzle_generator = CrosswordGenerator()
csp_generator = CSPPuzzleGenerator()  # CSP模式生成器
configurable_generator = ConfigurablePuzzleGenerator()  # 可配置生成器


# ============ 数据模型 ============

class VocabularyGroup(BaseModel):
    code: str
    name: str
    count: int


class PuzzleCell(BaseModel):
    row: int
    col: int
    letter: str
    is_empty: bool = False
    word_ids: List[int] = []


class WordClue(BaseModel):
    id: int
    word: str
    definition: str
    direction: str  # "across" or "down"
    start_row: int
    start_col: int
    length: int


class Puzzle(BaseModel):
    grid_size: int
    cells: List[List[Optional[str]]]
    words: List[WordClue]
    level: int
    difficulty: str
    group: str


class AnswerSubmit(BaseModel):
    word_id: int
    answer: str


class GameResult(BaseModel):
    correct: bool
    word: str
    definition: str


class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    score: int
    mode: str
    group: str


# ============ 用户数据存储（简单内存存储，正式版应使用数据库） ============
users_db: Dict[str, dict] = {}


# ============ 用户相关数据模型 ============

class UserRegister(BaseModel):
    nickname: str
    avatar: str = "😊"


class UserInfo(BaseModel):
    id: str
    nickname: str
    avatar: str
    created_at: str


# ============ API 路由 ============

@app.get("/api")
async def api_root():
    return {"message": "欢迎来到 我爱填单词 WordCross!", "version": "1.0.0"}


# ============ 用户 API ============

@app.post("/api/user/register")
async def register_user(user: UserRegister, response: Response):
    """
    用户注册，后端生成用户ID，设置cookie返回给前端
    """
    # 生成用户ID
    user_id = str(uuid.uuid4())
    
    # 使用数据库存储用户
    user_info = db.create_user(user_id, user.nickname.strip(), user.avatar)
    
    # 同时保存到内存缓存（兼容旧逻辑）
    users_db[user_id] = user_info
    
    # 设置cookie（7天有效期）
    response.set_cookie(
        key="user_id",
        value=user_id,
        max_age=7 * 24 * 60 * 60,  # 7天
        httponly=False,
        samesite="lax",
        path="/"
    )
    
    return user_info


@app.get("/api/user/info")
async def get_user_info(user_id: Optional[str] = Cookie(default=None)):
    """
    获取当前用户信息（通过cookie中的user_id）
    """
    if not user_id:
        return {"registered": False}
    
    # 先从数据库查询
    user_info = db.get_user(user_id)
    if user_info:
        # 更新内存缓存
        users_db[user_id] = user_info
        return {
            "registered": True,
            **user_info
        }
    
    # 兼容：检查内存缓存
    if user_id in users_db:
        return {
            "registered": True,
            **users_db[user_id]
        }
    
    # 用户ID存在但数据库中没有（可能是旧cookie），返回未注册
    return {"registered": False}


@app.put("/api/user/update")
async def update_user(user: UserRegister, user_id: Optional[str] = Cookie(default=None)):
    """
    更新用户信息
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="用户未登录")
    
    # 更新数据库
    user_info = db.update_user(user_id, user.nickname.strip(), user.avatar)
    if not user_info:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    # 同步更新内存缓存
    users_db[user_id] = user_info
    
    return user_info


@app.delete("/api/user/logout")
async def logout_user(response: Response):
    """
    用户登出，清除cookie
    """
    response.delete_cookie(key="user_id", path="/")
    return {"success": True, "message": "已退出登录"}


# ============ 体力和道具 API ============

# 用户体力数据存储（简单内存存储，正式版应使用数据库）
user_energy_db: Dict[str, dict] = {}
user_props_db: Dict[str, dict] = {}

# 各模式体力消耗配置（闯关10点，其他模式30点）
ENERGY_COST = {
    "campaign": 10,   # 闯关模式
    "timed": 30,      # 计时模式
    "pk": 30,         # PK模式
    "endless": 30,    # 无限模式
}


class EnergyUpdate(BaseModel):
    energy: int
    mode: Optional[str] = None


class PropsUpdate(BaseModel):
    hintLetterCount: int
    showTranslationCount: int


@app.get("/api/user/energy")
async def get_user_energy(user_id: Optional[str] = Cookie(default=None)):
    """
    获取用户体力值
    """
    if not user_id:
        return {"energy": 200, "max_energy": 200}
    
    if user_id in user_energy_db:
        return user_energy_db[user_id]
    
    # 默认200点体力
    return {"energy": 200, "max_energy": 200}


@app.post("/api/user/energy/consume")
async def consume_energy(mode: str, user_id: Optional[str] = Cookie(default=None)):
    """
    记录体力消耗（仅用于日志记录，不实际扣除体力）
    
    注意：体力扣除由前端完成并通过 PUT /api/user/energy 同步
    此接口仅用于记录游戏模式消耗历史，不再重复扣除体力
    
    Args:
        mode: 游戏模式 - campaign/timed/pk/endless
    """
    if mode not in ENERGY_COST:
        raise HTTPException(status_code=400, detail=f"未知游戏模式: {mode}")
    
    cost = ENERGY_COST[mode]
    
    # 获取当前体力（仅用于返回，不扣除）
    current_energy = 100
    if user_id and user_id in user_energy_db:
        current_energy = user_energy_db[user_id].get("energy", 100)
    
    # 注意：不再在此处扣除体力，前端已经扣除并会通过 PUT /api/user/energy 同步
    # 此接口仅用于记录消耗日志
    
    return {
        "success": True,
        "message": f"记录消耗{cost}点体力",
        "energy": current_energy,  # 返回当前体力，不扣除
        "cost": cost
    }


@app.put("/api/user/energy")
async def update_user_energy(data: EnergyUpdate, user_id: Optional[str] = Cookie(default=None)):
    """
    更新用户体力值（用于同步前端状态）
    """
    if not user_id:
        user_id = "anonymous"
    
    if user_id not in user_energy_db:
        user_energy_db[user_id] = {"energy": 200, "max_energy": 200}
    
    user_energy_db[user_id]["energy"] = max(0, min(data.energy, 200))
    
    return user_energy_db[user_id]


class FreeEnergyRequest(BaseModel):
    amount: int = 10


@app.post("/api/user/energy/claim-free")
async def claim_free_energy(data: FreeEnergyRequest, user_id: Optional[str] = Cookie(default=None)):
    """
    领取免费体力（看广告、每日奖励等场景）
    
    Args:
        data: 包含要领取的体力数量
        user_id: 用户ID
    
    Returns:
        更新后的体力值
    """
    if not user_id:
        user_id = "anonymous"
    
    if user_id not in user_energy_db:
        user_energy_db[user_id] = {"energy": 200, "max_energy": 200}
    
    # 增加体力，上限为200
    current_energy = user_energy_db[user_id]["energy"]
    new_energy = min(current_energy + data.amount, 200)
    user_energy_db[user_id]["energy"] = new_energy
    
    return {
        "energy": new_energy,
        "max_energy": 200,
        "added": new_energy - current_energy
    }


@app.get("/api/user/props")
async def get_user_props(user_id: Optional[str] = Cookie(default=None)):
    """
    获取用户道具数量
    """
    if not user_id:
        return {"hintLetterCount": 20, "showTranslationCount": 20}
    
    if user_id in user_props_db:
        return user_props_db[user_id]
    
    # 默认20个
    return {"hintLetterCount": 20, "showTranslationCount": 20}


@app.put("/api/user/props")
async def update_user_props(data: PropsUpdate, user_id: Optional[str] = Cookie(default=None)):
    """
    更新用户道具数量
    """
    if not user_id:
        user_id = "anonymous"
    
    user_props_db[user_id] = {
        "hintLetterCount": max(0, data.hintLetterCount),
        "showTranslationCount": max(0, data.showTranslationCount)
    }
    
    return user_props_db[user_id]


# 用户积分存储
user_score_db: Dict[str, dict] = {}


class ScoreSync(BaseModel):
    score: int
    vocab_group: str = "primary"
    level: int = 1


@app.post("/api/game/score")
async def sync_game_score(data: ScoreSync, user_id: Optional[str] = Cookie(default=None)):
    """
    同步游戏积分到用户账户
    """
    if not user_id:
        user_id = "anonymous"
    
    if user_id not in user_score_db:
        user_score_db[user_id] = {"total_score": 0, "games": []}
    
    # 累加总积分
    user_score_db[user_id]["total_score"] += data.score
    
    # 记录游戏信息
    user_score_db[user_id]["games"].append({
        "score": data.score,
        "vocab_group": data.vocab_group,
        "level": data.level,
        "timestamp": time.time()
    })
    
    # 只保留最近100局记录
    if len(user_score_db[user_id]["games"]) > 100:
        user_score_db[user_id]["games"] = user_score_db[user_id]["games"][-100:]
    
    return {
        "success": True,
        "total_score": user_score_db[user_id]["total_score"]
    }


@app.get("/api/game/score")
async def get_game_score(user_id: Optional[str] = Cookie(default=None)):
    """
    获取用户总积分
    """
    if not user_id:
        return {"total_score": 0}
    
    if user_id in user_score_db:
        return {"total_score": user_score_db[user_id]["total_score"]}
    
    return {"total_score": 0}


# ============ 关卡奖励 API ============

class RewardClaimRequest(BaseModel):
    level: int
    vocab_group: str
    stars: int = 1  # 星级 1-3
    time_seconds: int = 0  # 通关时间


@app.post("/api/game/generate-reward")
async def generate_level_reward(user_id: Optional[str] = Cookie(default=None)):
    """
    生成关卡通关奖励（后端随机生成，防止前端篡改）
    
    奖励规则：
    - 三个品类随机选两个
    - 品类一（体力）：80% 10点，19% 20点，1% 50点
    - 品类二（提示）：80% 1点，19% 2点，1% 5点
    - 品类三（发音）：80% 1点，19% 2点，1% 3点
    """
    # 品类一：体力（翻倍后：10点/20点/50点）
    energy_rand = random.random()
    if energy_rand < 0.80:
        energy_reward = {"type": "energy", "name": "体力", "icon": "⚡", "value": 10}
    elif energy_rand < 0.99:
        energy_reward = {"type": "energy", "name": "体力", "icon": "⚡", "value": 20}
    else:
        energy_reward = {"type": "energy", "name": "体力", "icon": "⚡", "value": 50}
    
    # 品类二：提示
    hint_rand = random.random()
    if hint_rand < 0.80:
        hint_reward = {"type": "hint", "name": "提示", "icon": "💡", "value": 1}
    elif hint_rand < 0.99:
        hint_reward = {"type": "hint", "name": "提示", "icon": "💡", "value": 2}
    else:
        hint_reward = {"type": "hint", "name": "提示", "icon": "💡", "value": 5}
    
    # 品类三：发音
    speak_rand = random.random()
    if speak_rand < 0.80:
        speak_reward = {"type": "speak", "name": "发音", "icon": "🔊", "value": 1}
    elif speak_rand < 0.99:
        speak_reward = {"type": "speak", "name": "发音", "icon": "🔊", "value": 2}
    else:
        speak_reward = {"type": "speak", "name": "发音", "icon": "🔊", "value": 3}
    
    # 三个品类随机选两个
    all_rewards = [energy_reward, hint_reward, speak_reward]
    random.shuffle(all_rewards)
    selected_rewards = all_rewards[:2]
    
    return {
        "success": True,
        "rewards": selected_rewards
    }


@app.post("/api/game/claim-reward")
async def claim_level_reward(data: RewardClaimRequest, user_id: Optional[str] = Cookie(default=None)):
    """
    领取关卡奖励并更新用户数据
    
    Args:
        data: 关卡信息（用于验证和记录）
    """
    if not user_id:
        user_id = "anonymous"
    
    # 生成奖励（每次领取都重新生成，确保公平）
    reward_response = await generate_level_reward(user_id)
    rewards = reward_response["rewards"]
    
    # 更新用户数据
    energy_added = 0
    hint_added = 0
    speak_added = 0
    
    for reward in rewards:
        if reward["type"] == "energy":
            energy_added = reward["value"]
            # 更新体力
            if user_id not in user_energy_db:
                user_energy_db[user_id] = {"energy": 100, "max_energy": 100}
            current_energy = user_energy_db[user_id].get("energy", 100)
            user_energy_db[user_id]["energy"] = min(current_energy + energy_added, 200)
        
        elif reward["type"] == "hint":
            hint_added = reward["value"]
            # 更新提示道具
            if user_id not in user_props_db:
                user_props_db[user_id] = {"hintLetterCount": 20, "showTranslationCount": 20}
            user_props_db[user_id]["hintLetterCount"] = user_props_db[user_id].get("hintLetterCount", 20) + hint_added
        
        elif reward["type"] == "speak":
            speak_added = reward["value"]
            # 更新发音道具
            if user_id not in user_props_db:
                user_props_db[user_id] = {"hintLetterCount": 20, "showTranslationCount": 20}
            user_props_db[user_id]["showTranslationCount"] = user_props_db[user_id].get("showTranslationCount", 20) + speak_added
    
    # 返回领取结果和更新后的数据
    return {
        "success": True,
        "rewards": rewards,
        "updated_data": {
            "energy": user_energy_db.get(user_id, {}).get("energy", 100),
            "props": user_props_db.get(user_id, {"hintLetterCount": 20, "showTranslationCount": 20})
        }
    }


@app.get("/api/vocabulary/groups", response_model=List[VocabularyGroup])
async def get_vocabulary_groups():
    """获取所有词汇组别"""
    return vocab_manager.get_groups()


@app.get("/api/vocabulary/{group}/words")
async def get_group_words(group: str, limit: int = 100):
    """获取指定组别的词汇"""
    words = vocab_manager.get_words(group, limit)
    if not words:
        raise HTTPException(status_code=404, detail=f"词汇组别 '{group}' 不存在")
    return {"group": group, "words": words}


# ============ 闯关模式 ============

@app.get("/api/campaign/level/{level}")
async def get_campaign_level(level: int, group: str = "primary", mode: str = "auto"):
    """
    获取闯关模式指定关卡
    
    Args:
        level: 关卡号 (1-2000，支持大词库)
        group: 词库组别（支持 primary, grade3_1, grade3_2 等）
        mode: 生成模式
              - "auto" (自动：1-5关稀疏布局，6-10关密集布局，11+关稀疏布局)
              - "classic" (传统稀疏布局)
              - "csp" (CSP密集布局)
    """
    if level < 1 or level > 2000:
        raise HTTPException(status_code=400, detail="关卡范围: 1-2000")
    
    # 检查是否有预生成的关卡数据
    # 支持 grade3_1, grade3_2, junior7_1, senior1 等子分类代码
    if group in primary_campaign_levels:
        grade_data = primary_campaign_levels[group]
        levels_list = grade_data.get("levels", [])
        # 查找对应关卡
        for lvl in levels_list:
            if lvl.get("level") == level:
                return lvl
        # 如果关卡号超出范围，返回循环的关卡
        if levels_list:
            idx = (level - 1) % len(levels_list)
            return levels_list[idx]
    
    # 如果是 primary_all，从预生成的关卡数据中获取
    if group == "primary_all":
        # 先尝试从 primary_all.json 获取
        if "primary_all" in primary_campaign_levels:
            levels_list = primary_campaign_levels["primary_all"].get("levels", [])
            if levels_list:
                for lvl in levels_list:
                    if lvl.get("level") == level:
                        return lvl
                # 关卡号超出范围，循环使用
                idx = (level - 1) % len(levels_list)
                return levels_list[idx]
        # 回退：从所有年级的关卡中选择
        all_primary_levels = []
        for grade_code, grade_data in primary_campaign_levels.items():
            if grade_code.startswith("grade"):
                all_primary_levels.extend(grade_data.get("levels", []))
        if all_primary_levels:
            # 根据关卡号选择
            idx = (level - 1) % len(all_primary_levels)
            return all_primary_levels[idx]
    
    # 如果是 junior 或 junior_all，从预生成的关卡数据中获取
    if group in ("junior", "junior_all"):
        # 优先使用 junior 词库
        if "junior" in primary_campaign_levels:
            levels_list = primary_campaign_levels["junior"].get("levels", [])
            if levels_list:
                for lvl in levels_list:
                    if lvl.get("level") == level:
                        return lvl
                idx = (level - 1) % len(levels_list)
                return levels_list[idx]
        # 回退到 junior_all
        if "junior_all" in primary_campaign_levels:
            levels_list = primary_campaign_levels["junior_all"].get("levels", [])
            if levels_list:
                for lvl in levels_list:
                    if lvl.get("level") == level:
                        return lvl
                idx = (level - 1) % len(levels_list)
                return levels_list[idx]
    
    # 如果是 senior 或 senior_all，从预生成的关卡数据中获取
    if group in ("senior", "senior_all"):
        # 优先使用 senior 词库
        if "senior" in primary_campaign_levels:
            levels_list = primary_campaign_levels["senior"].get("levels", [])
            if levels_list:
                for lvl in levels_list:
                    if lvl.get("level") == level:
                        return lvl
                idx = (level - 1) % len(levels_list)
                return levels_list[idx]
        # 回退到 senior_all
        if "senior_all" in primary_campaign_levels:
            levels_list = primary_campaign_levels["senior_all"].get("levels", [])
            if levels_list:
                for lvl in levels_list:
                    if lvl.get("level") == level:
                        return lvl
                idx = (level - 1) % len(levels_list)
                return levels_list[idx]
    
    # 自动模式：根据关卡号选择布局类型
    if mode == "auto":
        if 6 <= level <= 10:
            # 关卡6-10使用密集布局
            puzzle = csp_generator.generate_campaign_level(level, group, vocab_manager)
            puzzle["layout_type"] = "dense"
        else:
            # 关卡1-5和11+使用稀疏布局
            puzzle = puzzle_generator.generate_campaign_level(level, group, vocab_manager)
            puzzle["layout_type"] = "sparse"
    elif mode == "csp":
        puzzle = csp_generator.generate_campaign_level(level, group, vocab_manager)
        puzzle["layout_type"] = "dense"
    else:
        puzzle = puzzle_generator.generate_campaign_level(level, group, vocab_manager)
        puzzle["layout_type"] = "sparse"
    
    return puzzle


# ============ 无限模式 ============

# 加载预生成的10关测试数据
def load_generated_levels():
    """加载预生成的10关测试关卡"""
    levels_path = os.path.join(DATA_DIR, "generated_levels.json")
    if os.path.exists(levels_path):
        with open(levels_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

generated_levels = load_generated_levels()


# 加载预生成的小学闯关关卡数据
def load_primary_campaign_levels():
    """加载预生成的闯关关卡数据（小学、初中、高中、考试等）"""
    result = {}
    
    # 1. 加载 primary_campaign_levels.json（小学年级数据）
    levels_path = os.path.join(DATA_DIR, "primary_campaign_levels.json")
    if os.path.exists(levels_path):
        with open(levels_path, "r", encoding="utf-8") as f:
            result = json.load(f)
    
    # 2. 加载 levels/ 目录下的所有独立 JSON 文件
    levels_dir = os.path.join(DATA_DIR, "levels")
    if os.path.exists(levels_dir):
        for filename in os.listdir(levels_dir):
            if filename.endswith(".json"):
                group_code = filename[:-5]  # 去掉 .json 后缀
                # 跳过已经在 primary_campaign_levels.json 中加载的
                if group_code not in result:
                    file_path = os.path.join(levels_dir, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            result[group_code] = data
                    except Exception as e:
                        print(f"加载 {filename} 失败: {e}")
    
    return result

primary_campaign_levels = load_primary_campaign_levels()


# 加载测试模式20关数据
def load_test_mode_levels():
    """加载测试模式20关验证关卡"""
    levels_path = os.path.join(DATA_DIR, "test_mode_levels.json")
    if os.path.exists(levels_path):
        with open(levels_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

test_mode_levels = load_test_mode_levels()


@app.get("/api/endless/levels")
async def get_endless_levels(group: str = "primary"):
    """
    获取无限模式预生成的关卡列表（用于测试验证）
    
    Args:
        group: 词库组别 (目前只有primary有预生成数据)
    """
    if group == "primary" and generated_levels:
        return {
            "available": True,
            "count": len(generated_levels),
            "levels": [
                {
                    "level": l.get("level", i+1),
                    "difficulty": l.get("difficulty", "medium"),
                    "layout_type": l.get("layout_type", "sparse"),
                    "word_count": len(l.get("words", [])),
                    "grid_size": l.get("grid_size", 5)
                }
                for i, l in enumerate(generated_levels)
            ]
        }
    return {"available": False, "count": 0, "levels": []}


@app.get("/api/endless/level/{level_num}")
async def get_endless_level(level_num: int, group: str = "primary"):
    """
    获取无限模式指定的预生成关卡
    
    Args:
        level_num: 关卡号 (1-10)
        group: 词库组别
    """
    if group == "primary" and generated_levels:
        if 1 <= level_num <= len(generated_levels):
            return generated_levels[level_num - 1]
    
    raise HTTPException(status_code=404, detail=f"关卡 {level_num} 不存在")


@app.get("/api/endless/puzzle")
async def get_endless_puzzle(group: str = "primary", difficulty: str = "medium", mode: str = "classic"):
    """
    获取无限模式随机关卡
    
    Args:
        group: 词库组别
        difficulty: 难度 - low/medium/high 或 easy/medium/hard
        mode: 生成模式 - "classic" 或 "csp"
    """
    # 映射前端难度到后端难度
    difficulty_map = {
        'low': 'easy',
        'medium': 'medium', 
        'high': 'hard'
    }
    final_difficulty = difficulty_map.get(difficulty, difficulty)
    
    if mode == "csp":
        puzzle = csp_generator.generate_random_puzzle(group, final_difficulty, vocab_manager)
    else:
        puzzle = puzzle_generator.generate_random_puzzle(group, final_difficulty, vocab_manager)
    
    return puzzle


# ============ 测试模式 (可配置版) ============

# 预生成的参数组合题库缓存
configurable_puzzles_cache: Dict[str, List[dict]] = {}


def load_configurable_puzzles():
    """加载可配置题库"""
    puzzles_path = os.path.join(DATA_DIR, "configurable_puzzles.json")
    if os.path.exists(puzzles_path):
        with open(puzzles_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# 初始化加载
configurable_puzzles_cache = load_configurable_puzzles()


@app.get("/api/test-mode/config")
async def get_test_mode_config():
    """
    获取测试模式的配置选项
    
    返回可用的难度和题量选项
    """
    return {
        "difficulties": [
            {"code": k, "name": v["name"], "min_len": v["min_len"], "max_len": v["max_len"]}
            for k, v in DIFFICULTY_CONFIG.items()
        ],
        "quantities": [
            {"code": k, "name": v["name"], "grid_sizes": v["grid_sizes"]}
            for k, v in QUANTITY_CONFIG.items()
        ],
        "min_density": 0.40
    }


@app.get("/api/test-mode/levels")
async def get_test_mode_levels(difficulty: str = None, quantity: str = None):
    """
    获取测试模式关卡列表
    
    Args:
        difficulty: 难度 - low/medium/high
        quantity: 题量 - small/medium/large
    
    如果不指定参数，返回所有可用的参数组合及其关卡数量
    """
    if not difficulty and not quantity:
        # 返回所有组合的概览
        combinations = []
        for diff in DIFFICULTY_CONFIG.keys():
            for qty in QUANTITY_CONFIG.keys():
                key = f"{diff}_{qty}"
                puzzles = configurable_puzzles_cache.get(key, [])
                combinations.append({
                    "difficulty": diff,
                    "difficulty_name": DIFFICULTY_CONFIG[diff]["name"],
                    "quantity": qty,
                    "quantity_name": QUANTITY_CONFIG[qty]["name"],
                    "count": len(puzzles),
                    "available": len(puzzles) > 0
                })
        
        return {
            "available": True,
            "combinations": combinations,
            "total_puzzles": sum(c["count"] for c in combinations)
        }
    
    # 返回指定组合的关卡列表
    if not difficulty:
        difficulty = "medium"
    if not quantity:
        quantity = "medium"
    
    key = f"{difficulty}_{quantity}"
    puzzles = configurable_puzzles_cache.get(key, [])
    
    if not puzzles:
        return {
            "available": False,
            "difficulty": difficulty,
            "quantity": quantity,
            "count": 0,
            "levels": []
        }
    
    return {
        "available": True,
        "difficulty": difficulty,
        "difficulty_name": DIFFICULTY_CONFIG.get(difficulty, {}).get("name", difficulty),
        "quantity": quantity,
        "quantity_name": QUANTITY_CONFIG.get(quantity, {}).get("name", quantity),
        "count": len(puzzles),
        "levels": [
            {
                "index": i + 1,
                "grid_size": p.get("grid_size", 5),
                "word_count": len(p.get("words", [])),
                "density": p.get("density", 0)
            }
            for i, p in enumerate(puzzles)
        ]
    }


@app.get("/api/test-mode/level/{level_num}")
async def get_test_mode_level(level_num: int, difficulty: str = "medium", quantity: str = "medium"):
    """
    获取测试模式指定关卡（包含完整答案）
    
    Args:
        level_num: 关卡号 (从1开始)
        difficulty: 难度
        quantity: 题量
    """
    key = f"{difficulty}_{quantity}"
    puzzles = configurable_puzzles_cache.get(key, [])
    
    if not puzzles:
        raise HTTPException(status_code=404, detail=f"组合 {difficulty}_{quantity} 暂无题目，请先刷新生成")
    
    if level_num < 1 or level_num > len(puzzles):
        raise HTTPException(status_code=404, detail=f"关卡 {level_num} 不存在，有效范围: 1-{len(puzzles)}")
    
    level_data = puzzles[level_num - 1]
    
    # 构建答案网格
    grid_size = level_data.get("grid_size", 5)
    cells = level_data.get("cells", [])
    words = level_data.get("words", [])
    
    answer_grid = [[cell if cell else '' for cell in row] for row in cells]
    for word_info in words:
        word = word_info.get("word", "")
        direction = word_info.get("direction", "")
        start_row = word_info.get("start_row", 0)
        start_col = word_info.get("start_col", 0)
        
        for i, letter in enumerate(word):
            if direction == "across":
                r, c = start_row, start_col + i
            else:
                r, c = start_row + i, start_col
            
            if 0 <= r < grid_size and 0 <= c < grid_size:
                answer_grid[r][c] = letter
    
    return {
        **level_data,
        "answer_grid": answer_grid,
        "mode": "test",
        "level_num": level_num
    }


@app.post("/api/test-mode/refresh")
async def refresh_test_mode_puzzles(difficulty: str = "medium", quantity: str = "medium", 
                                     group: str = "primary", count: int = 3):
    """
    刷新指定参数组合的题目（重新生成）
    
    Args:
        difficulty: 难度 - low/medium/high
        quantity: 题量 - small/medium/large
        group: 词库组别
        count: 生成数量
    """
    global configurable_puzzles_cache
    
    if difficulty not in DIFFICULTY_CONFIG:
        raise HTTPException(status_code=400, detail=f"无效难度: {difficulty}")
    if quantity not in QUANTITY_CONFIG:
        raise HTTPException(status_code=400, detail=f"无效题量: {quantity}")
    
    try:
        # 获取词库
        if hasattr(vocab_manager, 'get_all_words_for_csp'):
            vocab_words = vocab_manager.get_all_words_for_csp(group)
        else:
            vocab_words = vocab_manager.get_words(group, limit=10000)
        
        if not vocab_words:
            raise HTTPException(status_code=404, detail=f"词库 {group} 无可用单词")
        
        # 重新设置随机种子
        configurable_generator.reseed()
        
        # 生成新题目
        puzzles = configurable_generator.generate_multiple_puzzles(
            vocab_words,
            difficulty=difficulty,
            quantity=quantity,
            count=count,
            timeout=30.0
        )
        
        # 更新缓存
        key = f"{difficulty}_{quantity}"
        configurable_puzzles_cache[key] = puzzles
        
        # 保存到文件
        puzzles_path = os.path.join(DATA_DIR, "configurable_puzzles.json")
        with open(puzzles_path, "w", encoding="utf-8") as f:
            json.dump(configurable_puzzles_cache, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "difficulty": difficulty,
            "quantity": quantity,
            "count": len(puzzles),
            "message": f"成功生成 {len(puzzles)} 道题"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@app.post("/api/test-mode/refresh-all")
async def refresh_all_test_mode_puzzles(group: str = "primary", count: int = 3):
    """
    刷新所有参数组合的题目
    
    Args:
        group: 词库组别
        count: 每个组合生成的题目数量
    """
    global configurable_puzzles_cache
    
    try:
        # 获取词库
        if hasattr(vocab_manager, 'get_all_words_for_csp'):
            vocab_words = vocab_manager.get_all_words_for_csp(group)
        else:
            vocab_words = vocab_manager.get_words(group, limit=10000)
        
        if not vocab_words:
            raise HTTPException(status_code=404, detail=f"词库 {group} 无可用单词")
        
        results = []
        new_cache = {}
        
        for difficulty in DIFFICULTY_CONFIG.keys():
            for quantity in QUANTITY_CONFIG.keys():
                key = f"{difficulty}_{quantity}"
                
                # 重新设置随机种子
                configurable_generator.reseed()
                
                puzzles = configurable_generator.generate_multiple_puzzles(
                    vocab_words,
                    difficulty=difficulty,
                    quantity=quantity,
                    count=count,
                    timeout=30.0
                )
                
                new_cache[key] = puzzles
                results.append({
                    "key": key,
                    "difficulty": difficulty,
                    "quantity": quantity,
                    "count": len(puzzles)
                })
        
        # 更新缓存
        configurable_puzzles_cache = new_cache
        
        # 保存到文件
        puzzles_path = os.path.join(DATA_DIR, "configurable_puzzles.json")
        with open(puzzles_path, "w", encoding="utf-8") as f:
            json.dump(configurable_puzzles_cache, f, ensure_ascii=False, indent=2)
        
        total = sum(r["count"] for r in results)
        
        return {
            "success": True,
            "total_puzzles": total,
            "combinations": results,
            "message": f"成功生成 {total} 道题，覆盖 {len(results)} 个参数组合"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


# 加载测试版关卡数据（含答案，用于审核）
def load_test_levels():
    """加载测试版关卡数据"""
    test_levels = {}
    # 测试关卡目录 (在data目录外层)
    _env_test_dir = os.environ.get("WORDCROSS_TEST_LEVELS_DIR")
    if _env_test_dir:
        test_dir = _env_test_dir
    else:
        test_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "test_levels")
    if os.path.exists(test_dir):
        for filename in os.listdir(test_dir):
            if filename.endswith("_with_answers.json"):
                filepath = os.path.join(test_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        group_code = data.get("group_code", filename.replace("_with_answers.json", ""))
                        test_levels[group_code] = data
                except Exception as e:
                    print(f"加载测试数据失败 {filename}: {e}")
    return test_levels

test_levels_data = load_test_levels()


@app.get("/api/test-mode/all-test-data")
async def get_all_test_data():
    """
    获取所有测试版关卡数据（含完整答案，用于审核）
    """
    result = []
    
    for group_code, data in test_levels_data.items():
        levels_with_answers = []
        for level in data.get("levels", []):
            # 构建答案网格
            grid_size = level.get("grid_size", 5)
            cells = level.get("cells", [])
            
            answer_grid = [['' for _ in range(grid_size)] for _ in range(grid_size)]
            for r in range(grid_size):
                for c in range(grid_size):
                    # 安全访问cells，避免越界
                    if r < len(cells) and c < len(cells[r]) and cells[r][c]:
                        answer_grid[r][c] = cells[r][c]
            
            across_words = [w for w in level.get("words", []) if w["direction"] == "across"]
            down_words = [w for w in level.get("words", []) if w["direction"] == "down"]
            
            levels_with_answers.append({
                "level": level.get("level"),
                "grid_size": grid_size,
                "word_count": level.get("word_count"),
                "answer_grid": answer_grid,
                "across_words": sorted(across_words, key=lambda x: x.get("clue_number", 0)),
                "down_words": sorted(down_words, key=lambda x: x.get("clue_number", 0)),
                "prefilled": level.get("prefilled", {}),
                "density": level.get("density", 0)
            })
        
        result.append({
            "group_code": group_code,
            "group_name": data.get("name", group_code),
            "level_count": data.get("level_count", 0),
            "word_count": data.get("word_count", 0),
            "levels": levels_with_answers
        })
    
    return {
        "available": True,
        "groups": result,
        "total_groups": len(result),
        "total_levels": sum(g["level_count"] for g in result)
    }


@app.get("/api/test-mode/levels-summary")
async def get_levels_summary():
    """
    获取所有关卡的生成汇总报告
    """
    summary_path = os.path.join(DATA_DIR, "levels_summary.json")
    
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                summary = json.load(f)
            return {
                "available": True,
                **summary
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }
    
    # 如果没有汇总文件，从关卡数据生成
    summary = {
        "available": True,
        "generated_at": None,
        "total_groups": len(primary_campaign_levels),
        "total_levels": 0,
        "success_count": 0,
        "fail_count": 0,
        "groups": []
    }
    
    for group_code, group_data in primary_campaign_levels.items():
        levels = group_data.get("levels", [])
        success = len([l for l in levels if not l.get("error")])
        fail = len([l for l in levels if l.get("error")])
        
        summary["total_levels"] += len(levels)
        summary["success_count"] += success
        summary["fail_count"] += fail
        
        summary["groups"].append({
            "group_code": group_code,
            "group_name": group_data.get("name", group_code),
            "category": group_data.get("category", "未分类"),
            "status": "completed" if levels else "empty",
            "word_count": group_data.get("word_count", 0),
            "level_count": len(levels),
            "success_count": success,
            "fail_count": fail
        })
    
    return summary


@app.post("/api/test-mode/generate-all")
async def generate_all_levels_api():
    """
    一次性生成全部关卡（后台任务）
    """
    import subprocess
    import os
    
    script_path = os.path.join(os.path.dirname(__file__), "generate_all_levels.py")
    
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail="生成脚本不存在")
    
    try:
        # 运行生成脚本
        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=600,  # 10分钟超时
            cwd=os.path.dirname(script_path)
        )
        
        if result.returncode == 0:
            # 重新加载关卡数据
            global primary_campaign_levels
            primary_campaign_levels = load_primary_campaign_levels()
            
            return {
                "success": True,
                "message": "全部关卡生成完成",
                "output": result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout
            }
        else:
            return {
                "success": False,
                "message": "生成失败",
                "error": result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr
            }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="生成超时（超过10分钟）")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@app.get("/api/test-mode/campaign-grades")
async def get_campaign_grades():
    """
    获取所有年级的闯关模式关卡和词汇表（用于测试验证）
    """
    result = []
    
    for grade_code, grade_data in primary_campaign_levels.items():
        levels_list = grade_data.get("levels", [])
        grade_name = grade_data.get("name", grade_code)
        
        # 收集该年级使用的所有单词
        all_words_set = set()
        all_words_list = []
        
        # 处理每个关卡
        levels_summary = []
        for lvl in levels_list:
            level_words = lvl.get("words", [])
            
            # 构建答案网格
            grid_size = lvl.get("grid_size", 5)
            cells = lvl.get("cells", [])
            
            answer_grid = [['' for _ in range(grid_size)] for _ in range(grid_size)]
            for word_info in level_words:
                word = word_info.get("word", "")
                direction = word_info.get("direction", "")
                start_row = word_info.get("start_row", 0)
                start_col = word_info.get("start_col", 0)
                
                for i, letter in enumerate(word):
                    if direction == "across":
                        r, c = start_row, start_col + i
                    else:
                        r, c = start_row + i, start_col
                    
                    if 0 <= r < grid_size and 0 <= c < grid_size:
                        answer_grid[r][c] = letter
            
            # 标记空格
            for r in range(grid_size):
                for c in range(grid_size):
                    if cells[r][c] is None:
                        answer_grid[r][c] = None
            
            across_words = [w for w in level_words if w["direction"] == "across"]
            down_words = [w for w in level_words if w["direction"] == "down"]
            
            levels_summary.append({
                "level": lvl.get("level", 0),
                "grid_size": grid_size,
                "word_count": len(level_words),
                "answer_grid": answer_grid,
                "across_words": sorted(across_words, key=lambda x: x.get("clue_number", 0)),
                "down_words": sorted(down_words, key=lambda x: x.get("clue_number", 0)),
                "prefilled": lvl.get("prefilled", {})
            })
            
            # 收集单词
            for w in level_words:
                word_upper = w.get("word", "").upper()
                if word_upper and word_upper not in all_words_set:
                    all_words_set.add(word_upper)
                    all_words_list.append({
                        "word": word_upper,
                        "definition": w.get("definition", "")
                    })
                # 备选答案功能已移除
        
        result.append({
            "grade_code": grade_code,
            "grade_name": grade_name,
            "level_count": len(levels_list),
            "word_count": len(all_words_list),
            "levels": levels_summary,
            "vocabulary": sorted(all_words_list, key=lambda x: x["word"])
        })
    
    # 按分类排序：小学 -> 初中 -> 高中 -> 考试
    group_order = [
        # 小学
        "grade3_1", "grade3_2", "grade4_1", "grade4_2", "grade5_1", "grade5_2", "grade6_1", "grade6_2",
        # 初中/高中
        "junior", "senior",
        # 考试
        "ket", "pet", "cet4", "cet6", "postgrad", "ielts", "toefl", "gre"
    ]
    result.sort(key=lambda x: group_order.index(x["grade_code"]) if x["grade_code"] in group_order else 999)
    
    return {
        "available": True,
        "grades": result
    }


@app.get("/api/test-mode/group-levels/{group_code}")
async def get_group_levels(group_code: str):
    """
    按需加载单个词库的关卡数据（用于测试模式查看）
    """
    if group_code not in primary_campaign_levels:
        return {
            "available": False,
            "error": f"词库 {group_code} 不存在"
        }
    
    grade_data = primary_campaign_levels[group_code]
    levels_list = grade_data.get("levels", [])
    grade_name = grade_data.get("name", group_code)
    
    # 处理每个关卡
    levels_summary = []
    for lvl in levels_list:
        level_words = lvl.get("words", [])
        
        # 构建答案网格
        grid_size = lvl.get("grid_size", 5)
        cells = lvl.get("cells", [])
        
        answer_grid = [['' for _ in range(grid_size)] for _ in range(grid_size)]
        for word_info in level_words:
            word = word_info.get("word", "")
            direction = word_info.get("direction", "")
            start_row = word_info.get("start_row", 0)
            start_col = word_info.get("start_col", 0)
            
            for i, letter in enumerate(word):
                if direction == "across":
                    r, c = start_row, start_col + i
                else:
                    r, c = start_row + i, start_col
                
                if 0 <= r < grid_size and 0 <= c < grid_size:
                    answer_grid[r][c] = letter
        
        # 标记空格
        if cells:
            for r in range(grid_size):
                for c in range(grid_size):
                    if r < len(cells) and c < len(cells[r]) and cells[r][c] is None:
                        answer_grid[r][c] = None
        
        across_words = [w for w in level_words if w["direction"] == "across"]
        down_words = [w for w in level_words if w["direction"] == "down"]
        
        levels_summary.append({
            "level": lvl.get("level", 0),
            "grid_size": grid_size,
            "word_count": len(level_words),
            "answer_grid": answer_grid,
            "across_words": sorted(across_words, key=lambda x: x.get("clue_number", 0)),
            "down_words": sorted(down_words, key=lambda x: x.get("clue_number", 0)),
            "prefilled": lvl.get("prefilled", {})
        })
    
    return {
        "available": True,
        "group_code": group_code,
        "group_name": grade_name,
        "level_count": len(levels_list),
        "levels": levels_summary
    }


@app.get("/api/test-mode/all-answers")
async def get_all_test_mode_answers(difficulty: str = None, quantity: str = None):
    """
    获取测试模式指定组合的完整答案展示
    
    Args:
        difficulty: 难度
        quantity: 题量
    """
    if not difficulty:
        difficulty = "medium"
    if not quantity:
        quantity = "medium"
    
    key = f"{difficulty}_{quantity}"
    puzzles = configurable_puzzles_cache.get(key, [])
    
    if not puzzles:
        return {"available": False, "levels": []}
    
    all_answers = []
    for i, level_data in enumerate(puzzles):
        grid_size = level_data.get("grid_size", 5)
        cells = level_data.get("cells", [])
        words = level_data.get("words", [])
        
        # 构建答案网格
        answer_grid = [[cell if cell else '' for cell in row] for row in cells]
        for word_info in words:
            word = word_info.get("word", "")
            direction = word_info.get("direction", "")
            start_row = word_info.get("start_row", 0)
            start_col = word_info.get("start_col", 0)
            
            for j, letter in enumerate(word):
                if direction == "across":
                    r, c = start_row, start_col + j
                else:
                    r, c = start_row + j, start_col
                
                if 0 <= r < grid_size and 0 <= c < grid_size:
                    answer_grid[r][c] = letter
        
        across_words = [w for w in words if w["direction"] == "across"]
        down_words = [w for w in words if w["direction"] == "down"]
        
        revealed_grid = level_data.get("revealed", [[False] * grid_size for _ in range(grid_size)])
        
        all_answers.append({
            "level": i + 1,
            "grid_size": grid_size,
            "word_count": len(words),
            "answer_grid": answer_grid,
            "revealed_grid": revealed_grid,
            "density": level_data.get("density", 0),
            "cross_validated": level_data.get("cross_validated", True),
            "across_words": sorted(across_words, key=lambda x: x.get("clue_number", 0)),
            "down_words": sorted(down_words, key=lambda x: x.get("clue_number", 0))
        })
    
    return {
        "available": True,
        "difficulty": difficulty,
        "quantity": quantity,
        "total_levels": len(all_answers),
        "levels": all_answers
    }


# 保留旧的API兼容性
@app.post("/api/test-mode/regenerate")
async def regenerate_test_mode_levels():
    """
    重新生成测试模式关卡（兼容旧API，生成所有组合）
    """
    return await refresh_all_test_mode_puzzles(group="primary", count=3)


# ============ 计时模式 ============

@app.get("/api/timed/puzzle")
async def get_timed_puzzle(group: str = "primary", duration: int = 180, difficulty: str = None):
    """
    获取计时模式关卡 (duration: 秒，统一3分钟)
    
    Args:
        group: 词库组别
        duration: 时长秒数（默认180秒=3分钟）
        difficulty: 难度 - low/medium/high（可选，若不指定则根据时长计算）
    """
    # 映射前端难度到后端难度
    difficulty_map = {
        'low': 'easy',
        'medium': 'medium', 
        'high': 'hard'
    }
    
    if difficulty:
        # 使用用户选择的难度
        final_difficulty = difficulty_map.get(difficulty, difficulty)
    else:
        # 根据时长调整难度（兼容旧逻辑）
        if duration <= 180:
            final_difficulty = "easy"
        elif duration <= 300:
            final_difficulty = "medium"
        else:
            final_difficulty = "hard"
    
    puzzle = puzzle_generator.generate_random_puzzle(group, final_difficulty, vocab_manager)
    return puzzle


# ============ 答题验证 ============

@app.post("/api/check-answer", response_model=GameResult)
async def check_answer(submit: AnswerSubmit):
    """验证答案"""
    # 这里实际应该从数据库或缓存获取正确答案
    # 简化处理：前端传来的word_id对应的正确答案
    result = puzzle_generator.verify_answer(submit.word_id, submit.answer)
    return result


# ============ 游戏数据提交 API ============

class GameSubmit(BaseModel):
    game_mode: str  # campaign/endless/timed/pk
    vocab_group: str
    score: int = 0
    words_count: int = 0
    level_reached: int = 0
    duration_seconds: Optional[int] = None
    result: Optional[str] = None  # win/lose/draw (PK模式)
    extra_data: Optional[dict] = None


class PKResultSubmitNew(BaseModel):
    vocab_group: str
    result: str  # win/lose/draw
    words_count: int = 0
    duration_seconds: Optional[int] = None


@app.post("/api/game/submit")
async def submit_game_data(data: GameSubmit, user_id: Optional[str] = Cookie(default=None)):
    """
    提交一局游戏数据
    
    Args:
        data: 游戏数据
        - game_mode: 游戏模式 (campaign/endless/timed/pk)
        - vocab_group: 词库分组
        - score: 本局积分
        - words_count: 完成单词数
        - level_reached: 达到的关卡
        - duration_seconds: 游戏时长(秒)
        - result: 对战结果 (PK模式: win/lose/draw)
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="用户未登录")
    
    # 检查用户是否存在
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    # 添加游戏记录
    record_id = db.add_game_record(
        user_id=user_id,
        game_mode=data.game_mode,
        vocab_group=data.vocab_group,
        score=data.score,
        words_count=data.words_count,
        level_reached=data.level_reached,
        duration_seconds=data.duration_seconds,
        result=data.result,
        extra_data=data.extra_data
    )
    
    # 更新用户统计
    db.update_user_stats(
        user_id=user_id,
        game_mode=data.game_mode,
        vocab_group=data.vocab_group,
        score=data.score,
        words_count=data.words_count,
        level_reached=data.level_reached,
        duration_seconds=data.duration_seconds,
        result=data.result
    )
    
    # 记录功能使用
    db.record_feature_usage(user_id, f"game_{data.game_mode}")
    
    # 刷新相关排行榜（异步优化：可以改为定时刷新）
    # 这里简单实现，每次提交后刷新该模式的排行榜
    try:
        for lb_type in db.LEADERBOARD_TYPES.keys():
            if lb_type.startswith(data.game_mode):
                db.refresh_leaderboard(lb_type, data.vocab_group)
                db.refresh_leaderboard(lb_type, "all")
    except Exception as e:
        print(f"刷新排行榜失败: {e}")
    
    return {
        "success": True,
        "record_id": record_id,
        "message": "游戏数据已提交"
    }


@app.post("/api/game/pk-result")
async def submit_pk_result_new(data: PKResultSubmitNew, user_id: Optional[str] = Cookie(default=None)):
    """
    提交PK对战结果（简化版）
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="用户未登录")
    
    # 计算积分
    score = 0
    if data.result == "win":
        score = SCORE_PER_WORD * data.words_count + PK_WIN_SCORE
    elif data.result == "draw":
        score = SCORE_PER_WORD * data.words_count + PK_DRAW_SCORE
    else:
        score = SCORE_PER_WORD * data.words_count
    
    # 添加游戏记录
    record_id = db.add_game_record(
        user_id=user_id,
        game_mode="pk",
        vocab_group=data.vocab_group,
        score=score,
        words_count=data.words_count,
        level_reached=0,
        duration_seconds=data.duration_seconds,
        result=data.result
    )
    
    # 更新用户统计
    db.update_user_stats(
        user_id=user_id,
        game_mode="pk",
        vocab_group=data.vocab_group,
        score=score,
        words_count=data.words_count,
        result=data.result
    )
    
    # 刷新PK排行榜
    try:
        db.refresh_leaderboard("pk_wins", data.vocab_group)
        db.refresh_leaderboard("pk_wins", "all")
        db.refresh_leaderboard("pk_score", data.vocab_group)
        db.refresh_leaderboard("pk_score", "all")
    except Exception as e:
        print(f"刷新排行榜失败: {e}")
    
    return {
        "success": True,
        "record_id": record_id,
        "result": data.result,
        "score": score,
        "message": "PK结果已提交"
    }


# ============ 用户统计 API ============

@app.get("/api/user/stats")
async def get_user_stats_api(user_id: Optional[str] = Cookie(default=None)):
    """
    获取当前用户的游戏统计
    """
    if not user_id:
        return {"registered": False}
    
    user = db.get_user(user_id)
    if not user:
        return {"registered": False}
    
    stats = db.get_user_all_stats_summary(user_id)
    
    return {
        "registered": True,
        "user": user,
        "stats": stats
    }


@app.get("/api/user/stats/{game_mode}")
async def get_user_mode_stats(game_mode: str, user_id: Optional[str] = Cookie(default=None)):
    """
    获取用户特定模式的统计
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="用户未登录")
    
    stats = db.get_user_stats(user_id, game_mode)
    return {
        "game_mode": game_mode,
        "stats": stats
    }


@app.get("/api/user/feature-usage")
async def get_user_feature_usage_api(user_id: Optional[str] = Cookie(default=None)):
    """
    获取用户功能使用统计
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="用户未登录")
    
    usage = db.get_user_feature_usage(user_id)
    return {
        "features": usage
    }


@app.get("/api/user/game-records")
async def get_user_game_records_api(
    game_mode: Optional[str] = None,
    limit: int = 50,
    user_id: Optional[str] = Cookie(default=None)
):
    """
    获取用户游戏记录
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="用户未登录")
    
    records = db.get_user_game_records(user_id, game_mode, limit)
    return {
        "records": records,
        "count": len(records)
    }


# ============ 排行榜系统（增强版） ============

# 排行榜数据存储路径
LEADERBOARD_FILE = os.path.join(DATA_DIR, "leaderboards.json")

# 所有分组代码
ALL_GROUPS = [
    "grade3_1", "grade3_2", "grade4_1", "grade4_2", 
    "grade5_1", "grade5_2", "grade6_1", "grade6_2",
    "junior", "senior", "ket", "pet", 
    "cet4", "cet6", "postgrad", "ielts", "toefl", "gre"
]

# 分组名称映射
GROUP_NAMES = {
    "grade3_1": "三年级上册", "grade3_2": "三年级下册",
    "grade4_1": "四年级上册", "grade4_2": "四年级下册",
    "grade5_1": "五年级上册", "grade5_2": "五年级下册",
    "grade6_1": "六年级上册", "grade6_2": "六年级下册",
    "junior": "初中词汇", "senior": "高中词汇",
    "ket": "KET考试", "pet": "PET考试",
    "cet4": "大学四级", "cet6": "大学六级",
    "postgrad": "考研词汇", "ielts": "雅思",
    "toefl": "托福", "gre": "GRE"
}

# 榜单类型
LEADERBOARD_TYPES = {
    "campaign_level": "闯关关卡榜",     # 最高通关关卡
    "campaign_score": "闯关积分榜",     # 积分（每个单词10分）
    "endless_level": "无限关卡榜",      # 无限模式通关关卡数
    "endless_score": "无限积分榜",      # 无限模式积分
    "timed_words": "计时单词榜",        # 计时模式完成单词数
    "timed_score": "计时积分榜",        # 计时模式积分
    "pk_wins": "PK获胜榜",              # PK获胜局数
    "pk_score": "PK积分榜"              # PK积分（赢3分，平1分）
}

# 分数计算常量
SCORE_PER_WORD = 10      # 每个单词10分
PK_WIN_SCORE = 3         # PK胜利3分
PK_DRAW_SCORE = 1        # PK平局1分


def load_leaderboards():
    """加载排行榜数据"""
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载排行榜失败: {e}")
    
    # 初始化空排行榜结构
    return init_empty_leaderboards()


def init_empty_leaderboards():
    """初始化空排行榜结构"""
    data = {}
    for lb_type in LEADERBOARD_TYPES.keys():
        data[lb_type] = {}
        for group in ALL_GROUPS:
            data[lb_type][group] = []
        data[lb_type]["all"] = []  # 总榜
    return data


def save_leaderboards():
    """保存排行榜数据"""
    try:
        os.makedirs(os.path.dirname(LEADERBOARD_FILE), exist_ok=True)
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(leaderboards_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存排行榜失败: {e}")


# 加载排行榜数据
leaderboards_data = load_leaderboards()


# 排行榜数据模型
class LeaderboardSubmit(BaseModel):
    user_id: str
    nickname: str
    avatar: str = "😊"
    group: str
    value: int  # 关卡数、单词数、积分等
    extra: Optional[dict] = None  # 额外信息（如用时等）


class PKResultSubmit(BaseModel):
    user_id: str
    nickname: str
    avatar: str = "😊"
    group: str
    result: str  # "win", "lose", "draw"
    opponent_id: Optional[str] = None
    opponent_name: Optional[str] = None


@app.get("/api/leaderboard/types")
async def get_leaderboard_types():
    """获取所有排行榜类型"""
    return {
        "types": [
            {"code": k, "name": v} for k, v in LEADERBOARD_TYPES.items()
        ],
        "groups": [
            {"code": k, "name": v} for k, v in GROUP_NAMES.items()
        ]
    }


@app.get("/api/leaderboard/{lb_type}")
async def get_leaderboard(lb_type: str, group: str = "all", limit: int = 50):
    """
    获取排行榜（优先从数据库获取）
    
    Args:
        lb_type: 排行榜类型 (campaign_level, campaign_score, endless_level, 
                            endless_score, timed_words, timed_score, pk_wins, pk_score)
        group: 分组代码 (grade3_1, junior, cet4 等) 或 "all" 表示总榜
        limit: 返回条数限制
    """
    if lb_type not in LEADERBOARD_TYPES:
        raise HTTPException(status_code=400, detail=f"未知的排行榜类型: {lb_type}")
    
    # 优先从数据库获取
    db_entries = db.get_leaderboard(lb_type, group, limit)
    
    if db_entries:
        # 从数据库返回
        result = []
        for entry in db_entries:
            result.append({
                "rank": entry.get("rank", 0),
                "user_id": entry.get("user_id", ""),
                "nickname": entry.get("nickname", "未知用户"),
                "avatar": entry.get("avatar", "😊"),
                "group": group,
                "group_name": GROUP_NAMES.get(group, "全部") if group != "all" else "全部",
                "value": entry.get("value", 0),
                "extra": entry.get("extra", {}),
                "timestamp": entry.get("updated_at", "")
            })
        
        return {
            "lb_type": lb_type,
            "lb_name": LEADERBOARD_TYPES.get(lb_type, lb_type),
            "group": group,
            "group_name": GROUP_NAMES.get(group, "全部") if group != "all" else "全部",
            "count": len(result),
            "entries": result,
            "source": "database"
        }
    
    # 回退：从内存/JSON获取（兼容旧数据）
    if lb_type not in leaderboards_data:
        leaderboards_data[lb_type] = init_empty_leaderboards()[lb_type]
    
    group_data = leaderboards_data[lb_type].get(group, [])
    sorted_data = sorted(group_data, key=lambda x: x.get("value", 0), reverse=True)[:limit]
    
    result = []
    for i, entry in enumerate(sorted_data):
        result.append({
            "rank": i + 1,
            "user_id": entry.get("user_id", ""),
            "nickname": entry.get("nickname", "未知用户"),
            "avatar": entry.get("avatar", "😊"),
            "group": entry.get("group", group),
            "group_name": GROUP_NAMES.get(entry.get("group", ""), entry.get("group", "")),
            "value": entry.get("value", 0),
            "extra": entry.get("extra", {}),
            "timestamp": entry.get("timestamp", "")
        })
    
    return {
        "lb_type": lb_type,
        "lb_name": LEADERBOARD_TYPES.get(lb_type, lb_type),
        "group": group,
        "group_name": GROUP_NAMES.get(group, "全部") if group != "all" else "全部",
        "count": len(result),
        "entries": result,
        "source": "memory"
    }


@app.post("/api/leaderboard/{lb_type}/submit")
async def submit_leaderboard_score(lb_type: str, data: LeaderboardSubmit):
    """
    提交排行榜分数
    
    Args:
        lb_type: 排行榜类型
        data: 提交数据
    """
    if lb_type not in LEADERBOARD_TYPES:
        raise HTTPException(status_code=400, detail=f"未知的排行榜类型: {lb_type}")
    
    if data.group not in ALL_GROUPS and data.group != "all":
        raise HTTPException(status_code=400, detail=f"未知的分组: {data.group}")
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    entry = {
        "user_id": data.user_id,
        "nickname": data.nickname,
        "avatar": data.avatar,
        "group": data.group,
        "value": data.value,
        "extra": data.extra or {},
        "timestamp": timestamp
    }
    
    # 确保数据结构存在
    if lb_type not in leaderboards_data:
        leaderboards_data[lb_type] = init_empty_leaderboards()[lb_type]
    if data.group not in leaderboards_data[lb_type]:
        leaderboards_data[lb_type][data.group] = []
    if "all" not in leaderboards_data[lb_type]:
        leaderboards_data[lb_type]["all"] = []
    
    # 查找用户是否已存在，更新最高分
    def update_or_add(entries_list, entry):
        existing = None
        for i, e in enumerate(entries_list):
            if e.get("user_id") == entry["user_id"]:
                existing = i
                break
        
        if existing is not None:
            # 只更新更高的分数
            if entry["value"] > entries_list[existing].get("value", 0):
                entries_list[existing] = entry
                return "updated"
            return "kept"
        else:
            entries_list.append(entry)
            return "added"
    
    # 更新分组榜和总榜
    result1 = update_or_add(leaderboards_data[lb_type][data.group], entry)
    result2 = update_or_add(leaderboards_data[lb_type]["all"], entry)
    
    # 保存
    save_leaderboards()
    
    # 计算用户当前排名
    group_entries = sorted(leaderboards_data[lb_type][data.group], 
                          key=lambda x: x.get("value", 0), reverse=True)
    rank = next((i+1 for i, e in enumerate(group_entries) 
                 if e.get("user_id") == data.user_id), -1)
    
    return {
        "success": True,
        "message": "分数已提交",
        "lb_type": lb_type,
        "group": data.group,
        "value": data.value,
        "rank": rank,
        "status": result1
    }


@app.post("/api/leaderboard/pk/submit")
async def submit_pk_result(data: PKResultSubmit):
    """
    提交PK对战结果
    
    Args:
        data: PK结果数据 (result: "win"/"lose"/"draw")
    """
    if data.group not in ALL_GROUPS and data.group != "all":
        raise HTTPException(status_code=400, detail=f"未知的分组: {data.group}")
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 计算积分增量
    score_delta = 0
    wins_delta = 0
    if data.result == "win":
        score_delta = PK_WIN_SCORE
        wins_delta = 1
    elif data.result == "draw":
        score_delta = PK_DRAW_SCORE
    # lose不加分
    
    # 更新PK积分榜
    for lb_type in ["pk_score", "pk_wins"]:
        if lb_type not in leaderboards_data:
            leaderboards_data[lb_type] = init_empty_leaderboards()[lb_type]
        if data.group not in leaderboards_data[lb_type]:
            leaderboards_data[lb_type][data.group] = []
        if "all" not in leaderboards_data[lb_type]:
            leaderboards_data[lb_type]["all"] = []
    
    # 查找或创建用户记录
    def update_pk_entry(entries_list, user_id, nickname, avatar, group, score_add, wins_add):
        existing = None
        for i, e in enumerate(entries_list):
            if e.get("user_id") == user_id:
                existing = i
                break
        
        if existing is not None:
            entries_list[existing]["value"] = entries_list[existing].get("value", 0) + score_add
            entries_list[existing]["extra"] = entries_list[existing].get("extra", {})
            entries_list[existing]["extra"]["wins"] = entries_list[existing]["extra"].get("wins", 0) + wins_add
            entries_list[existing]["extra"]["games"] = entries_list[existing]["extra"].get("games", 0) + 1
            entries_list[existing]["timestamp"] = timestamp
        else:
            entries_list.append({
                "user_id": user_id,
                "nickname": nickname,
                "avatar": avatar,
                "group": group,
                "value": score_add,
                "extra": {"wins": wins_add, "games": 1},
                "timestamp": timestamp
            })
    
    # 更新PK积分榜
    update_pk_entry(leaderboards_data["pk_score"][data.group], 
                   data.user_id, data.nickname, data.avatar, data.group, score_delta, wins_delta)
    update_pk_entry(leaderboards_data["pk_score"]["all"], 
                   data.user_id, data.nickname, data.avatar, data.group, score_delta, wins_delta)
    
    # 更新PK胜局榜 (value = 胜局数)
    for group_key in [data.group, "all"]:
        for entry in leaderboards_data["pk_wins"][group_key]:
            if entry.get("user_id") == data.user_id:
                entry["value"] = entry.get("extra", {}).get("wins", 0) + wins_delta
                entry["extra"]["wins"] = entry["value"]
                entry["extra"]["games"] = entry["extra"].get("games", 0) + 1
                entry["timestamp"] = timestamp
                break
        else:
            leaderboards_data["pk_wins"][group_key].append({
                "user_id": data.user_id,
                "nickname": data.nickname,
                "avatar": data.avatar,
                "group": data.group,
                "value": wins_delta,
                "extra": {"wins": wins_delta, "games": 1},
                "timestamp": timestamp
            })
    
    # 保存
    save_leaderboards()
    
    # 获取当前排名
    score_entries = sorted(leaderboards_data["pk_score"][data.group], 
                          key=lambda x: x.get("value", 0), reverse=True)
    rank = next((i+1 for i, e in enumerate(score_entries) 
                 if e.get("user_id") == data.user_id), -1)
    
    # 获取用户当前数据
    user_data = next((e for e in leaderboards_data["pk_score"][data.group] 
                     if e.get("user_id") == data.user_id), {})
    
    return {
        "success": True,
        "message": "PK结果已提交",
        "result": data.result,
        "score_added": score_delta,
        "total_score": user_data.get("value", 0),
        "total_wins": user_data.get("extra", {}).get("wins", 0),
        "total_games": user_data.get("extra", {}).get("games", 0),
        "rank": rank
    }


@app.get("/api/leaderboard/user/{user_id}")
async def get_user_rankings(user_id: str):
    """
    获取用户在各个排行榜的排名
    
    Args:
        user_id: 用户ID
    """
    rankings = {}
    
    for lb_type in LEADERBOARD_TYPES.keys():
        rankings[lb_type] = {
            "name": LEADERBOARD_TYPES[lb_type],
            "groups": {}
        }
        
        # 优先从数据库获取
        for group_code in list(ALL_GROUPS) + ["all"]:
            rank_info = db.get_user_rank(user_id, lb_type, group_code)
            if rank_info:
                rankings[lb_type]["groups"][group_code] = {
                    "rank": rank_info.get("rank", 0),
                    "value": rank_info.get("value", 0),
                    "extra": rank_info.get("extra", {})
                }
        
        # 如果数据库没有数据，回退到内存
        if not rankings[lb_type]["groups"] and lb_type in leaderboards_data:
            for group_code in list(ALL_GROUPS) + ["all"]:
                if group_code not in leaderboards_data[lb_type]:
                    continue
                
                entries = sorted(leaderboards_data[lb_type][group_code], 
                               key=lambda x: x.get("value", 0), reverse=True)
                
                for i, entry in enumerate(entries):
                    if entry.get("user_id") == user_id:
                        rankings[lb_type]["groups"][group_code] = {
                            "rank": i + 1,
                            "total": len(entries),
                            "value": entry.get("value", 0),
                            "extra": entry.get("extra", {})
                        }
                        break
    
    return {
        "user_id": user_id,
        "rankings": rankings
    }


@app.get("/api/leaderboard/stats")
async def get_leaderboard_stats():
    """获取排行榜统计信息"""
    stats = {}
    
    for lb_type, lb_name in LEADERBOARD_TYPES.items():
        if lb_type not in leaderboards_data:
            continue
        
        total_entries = 0
        group_counts = {}
        
        for group_code, entries in leaderboards_data[lb_type].items():
            if group_code == "all":
                continue
            count = len(entries)
            group_counts[group_code] = count
            total_entries += count
        
        stats[lb_type] = {
            "name": lb_name,
            "total_entries": len(leaderboards_data[lb_type].get("all", [])),
            "groups": group_counts
        }
    
    return stats


@app.post("/api/leaderboard/refresh")
async def refresh_leaderboards_api():
    """刷新所有排行榜缓存"""
    try:
        db.refresh_all_leaderboards()
        return {"success": True, "message": "排行榜刷新完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新失败: {str(e)}")


# ============ 后台管理 API ============

# 简单的管理员验证 (生产环境应使用更安全的认证方式)
ADMIN_TOKEN = "wordcross_admin_2026"


def verify_admin(token: str = None):
    """验证管理员权限"""
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="无管理员权限")


@app.get("/api/admin/users")
async def admin_get_users(
    limit: int = 50, 
    offset: int = 0,
    token: Optional[str] = None
):
    """
    获取用户列表（后台管理）
    """
    verify_admin(token)
    
    users = db.get_all_users(limit, offset)
    total = db.get_user_count()
    
    return {
        "users": users,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/api/admin/stats/overview")
async def admin_get_overview_stats(token: Optional[str] = None):
    """
    获取整体统计概览（后台管理）
    """
    verify_admin(token)
    
    overview = db.get_overview_stats()
    mode_stats = db.get_mode_stats()
    group_stats = db.get_group_stats()
    
    return {
        "overview": overview,
        "mode_stats": mode_stats,
        "group_stats": group_stats
    }


@app.get("/api/admin/stats/daily")
async def admin_get_daily_stats(days: int = 30, token: Optional[str] = None):
    """
    获取每日统计（后台管理）
    """
    verify_admin(token)
    
    daily_stats = db.get_daily_stats(days)
    
    return {
        "days": days,
        "stats": daily_stats
    }


@app.get("/api/admin/stats/feature-usage")
async def admin_get_feature_usage_stats(token: Optional[str] = None):
    """
    获取功能使用统计（后台管理）
    """
    verify_admin(token)
    
    feature_stats = db.get_all_feature_usage_stats()
    
    return {
        "features": feature_stats
    }


@app.get("/api/admin/user/{user_id}")
async def admin_get_user_detail(user_id: str, token: Optional[str] = None):
    """
    获取用户详情（后台管理）
    """
    verify_admin(token)
    
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    stats = db.get_user_all_stats_summary(user_id)
    feature_usage = db.get_user_feature_usage(user_id)
    recent_records = db.get_user_game_records(user_id, limit=20)
    
    return {
        "user": user,
        "stats": stats,
        "feature_usage": feature_usage,
        "recent_records": recent_records
    }


# ============ PK模式 WebSocket ============

class PKRoom:
    def __init__(self, room_id: str, group: str):
        self.room_id = room_id
        self.group = group
        self.players: Dict[str, WebSocket] = {}
        self.scores: Dict[str, int] = {}
        self.puzzle = None
        self.started = False


pk_rooms: Dict[str, PKRoom] = {}
waiting_players: Dict[str, List[WebSocket]] = {}  # group -> waiting players


@app.websocket("/ws/pk/{group}")
async def pk_websocket(websocket: WebSocket, group: str):
    """PK模式 WebSocket 连接"""
    await websocket.accept()
    
    try:
        # 等待玩家加入
        if group not in waiting_players:
            waiting_players[group] = []
        
        waiting_players[group].append(websocket)
        
        # 如果有2个玩家，创建房间
        if len(waiting_players[group]) >= 2:
            player1 = waiting_players[group].pop(0)
            player2 = waiting_players[group].pop(0)
            
            room_id = f"{group}_{random.randint(1000, 9999)}"
            room = PKRoom(room_id, group)
            room.players = {"player1": player1, "player2": player2}
            room.scores = {"player1": 0, "player2": 0}
            room.puzzle = puzzle_generator.generate_random_puzzle(group, "medium", vocab_manager)
            pk_rooms[room_id] = room
            
            # 通知两个玩家开始
            start_msg = {
                "type": "start",
                "room_id": room_id,
                "puzzle": room.puzzle
            }
            await player1.send_json(start_msg)
            await player2.send_json(start_msg)
        else:
            await websocket.send_json({"type": "waiting", "message": "等待对手..."})
        
        # 保持连接并处理消息
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "answer":
                room_id = data.get("room_id")
                if room_id in pk_rooms:
                    room = pk_rooms[room_id]
                    player_id = "player1" if websocket == room.players.get("player1") else "player2"
                    
                    # 验证答案
                    if data.get("correct"):
                        room.scores[player_id] += 1
                    
                    # 广播分数更新
                    score_update = {
                        "type": "score_update",
                        "scores": room.scores
                    }
                    for ws in room.players.values():
                        await ws.send_json(score_update)
    
    except WebSocketDisconnect:
        # 清理断开的连接
        if group in waiting_players and websocket in waiting_players[group]:
            waiting_players[group].remove(websocket)


# ============ 静态文件服务 (SPA回退) ============

# 挂载静态资源目录
if os.path.exists(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="static")

# 挂载音频文件目录
if os.path.exists(AUDIO_DIR):
    app.mount("/data/audio", StaticFiles(directory=AUDIO_DIR), name="audio")


# SPA 回退：所有非 API 路由返回 index.html
@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    """
    SPA 回退路由
    - 如果请求的是静态文件且存在，直接返回
    - 否则返回 index.html
    """
    # 跳过 API 路由
    if full_path.startswith("api/") or full_path.startswith("ws/"):
        raise HTTPException(status_code=404, detail="Not found")
    
    # 检查是否存在静态文件
    file_path = os.path.join(STATIC_DIR, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # 返回 index.html (SPA 回退)
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    raise HTTPException(status_code=404, detail="Not found")


# ============ 启动服务 ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10012)
