"""
词汇管理器 - 加载和管理各级别词汇
"""
import json
import os
import random
from typing import List, Dict, Optional
from pathlib import Path


def is_pure_alpha(word: str) -> bool:
    """检查单词是否只包含26个英文字母（不含连字符、撇号、空格等）"""
    return word.isalpha()


class VocabularyManager:
    """词汇管理器"""
    
    # 词汇组别配置
    GROUPS = {
        "primary": {"name": "小学词汇", "file": "primary.json"},
        "ket": {"name": "KET考试", "file": "ket.json"},
        "pet": {"name": "PET考试", "file": "pet.json"},
        "junior": {"name": "初中词汇", "file": "junior.json"},
        "senior": {"name": "高中词汇", "file": "senior.json"},
        "cet4": {"name": "大学四级", "file": "cet4.json"},
        "cet6": {"name": "大学六级", "file": "cet6.json"},
        "postgrad": {"name": "考研词汇", "file": "postgrad.json"},
        "ielts": {"name": "雅思", "file": "ielts.json"},
        "toefl": {"name": "托福", "file": "toefl.json"},
        "gre": {"name": "GRE", "file": "gre.json"},
    }
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # 优先使用环境变量，然后是默认相对路径
            env_data_dir = os.environ.get("WORDCROSS_DATA_DIR")
            if env_data_dir:
                self.data_dir = Path(env_data_dir) / "vocabulary"
            else:
                # 本地开发环境默认路径
                self.data_dir = Path(__file__).parent.parent / "data" / "vocabulary"
        else:
            self.data_dir = Path(data_dir)
        
        self._vocabulary_cache: Dict[str, List[dict]] = {}
        self._grade_vocabulary_cache: Dict[str, List[dict]] = {}  # 年级词库缓存
        self._word_id_counter = 1
        
        # 加载所有词汇
        self._load_all_vocabulary()
        
        # 加载年级词库（从预生成关卡中提取）
        self._load_grade_vocabulary()
    
    def _load_all_vocabulary(self):
        """加载所有词汇文件"""
        for group_code, config in self.GROUPS.items():
            file_path = self.data_dir / config["file"]
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # 为每个单词分配ID
                        for word in data:
                            word["id"] = self._word_id_counter
                            self._word_id_counter += 1
                        self._vocabulary_cache[group_code] = data
                except Exception as e:
                    print(f"加载词汇文件失败 {file_path}: {e}")
                    self._vocabulary_cache[group_code] = []
            else:
                # 文件不存在，使用示例数据
                self._vocabulary_cache[group_code] = self._get_sample_vocabulary(group_code)
    
    def _load_grade_vocabulary(self):
        """从预生成关卡中提取年级词库（支持新的单文件目录结构）"""
        # 使用环境变量或默认路径
        env_data_dir = os.environ.get("WORDCROSS_DATA_DIR")
        if env_data_dir:
            data_base = Path(env_data_dir)
        else:
            data_base = self.data_dir.parent
        
        # 1. 先加载旧版的 primary_campaign_levels.json（如果存在）
        levels_path = data_base / "primary_campaign_levels.json"
        if levels_path.exists():
            try:
                with open(levels_path, "r", encoding="utf-8") as f:
                    levels_data = json.load(f)
                
                for grade_code, grade_info in levels_data.items():
                    self._extract_words_from_grade_info(grade_code, grade_info)
            except Exception as e:
                print(f"加载 primary_campaign_levels.json 失败: {e}")
        
        # 2. 加载新目录结构 levels/{group}/meta.json 和各关卡文件
        levels_dir = data_base / "levels"
        if levels_dir.exists():
            for group_dir in levels_dir.iterdir():
                if group_dir.is_dir():
                    group_code = group_dir.name
                    # 跳过已加载的
                    if group_code in self._grade_vocabulary_cache:
                        continue
                    
                    meta_path = group_dir / "meta.json"
                    if meta_path.exists():
                        try:
                            with open(meta_path, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                            
                            word_set = set()
                            words_list = []
                            level_count = meta.get("level_count", 0)
                            
                            # 加载每关的数据提取词汇
                            for level_num in range(1, min(level_count + 1, 200)):  # 最多加载前200关
                                level_file = group_dir / f"{level_num}.json"
                                if level_file.exists():
                                    try:
                                        with open(level_file, "r", encoding="utf-8") as f:
                                            level_data = json.load(f)
                                        
                                        for word_info in level_data.get("words", []):
                                            word_upper = word_info.get("word", "").upper()
                                            if word_upper and word_upper not in word_set:
                                                word_set.add(word_upper)
                                                words_list.append({
                                                    "word": word_upper.lower(),
                                                    "definition": word_info.get("definition", ""),
                                                    "difficulty": 1,
                                                    "id": self._word_id_counter
                                                })
                                                self._word_id_counter += 1
                                    except Exception as e:
                                        pass  # 跳过无法加载的关卡
                            
                            if words_list:
                                self._grade_vocabulary_cache[group_code] = words_list
                                print(f"加载词库 {group_code}: {len(words_list)} 词")
                        except Exception as e:
                            print(f"加载词库 {group_code} 失败: {e}")
    
    def _extract_words_from_grade_info(self, grade_code: str, grade_info: dict):
        """从年级信息中提取词汇"""
        word_set = set()
        words_list = []
        
        for level in grade_info.get("levels", []):
            for word_info in level.get("words", []):
                word_upper = word_info.get("word", "").upper()
                if word_upper and word_upper not in word_set:
                    word_set.add(word_upper)
                    words_list.append({
                        "word": word_upper.lower(),
                        "definition": word_info.get("definition", ""),
                        "difficulty": 1,
                        "id": self._word_id_counter
                    })
                    self._word_id_counter += 1
        
        if words_list:
            self._grade_vocabulary_cache[grade_code] = words_list
            print(f"加载年级词库 {grade_code}: {len(words_list)} 词")
    
    def _get_sample_vocabulary(self, group_code: str) -> List[dict]:
        """获取示例词汇数据"""
        # 基础示例词汇 - 适合生成填字游戏
        sample_words = {
            "primary": [
                {"word": "dog", "definition": "狗", "difficulty": 1},
                {"word": "cat", "definition": "猫", "difficulty": 1},
                {"word": "sun", "definition": "太阳", "difficulty": 1},
                {"word": "moon", "definition": "月亮", "difficulty": 1},
                {"word": "star", "definition": "星星", "difficulty": 1},
                {"word": "book", "definition": "书", "difficulty": 1},
                {"word": "pen", "definition": "钢笔", "difficulty": 1},
                {"word": "red", "definition": "红色", "difficulty": 1},
                {"word": "blue", "definition": "蓝色", "difficulty": 1},
                {"word": "green", "definition": "绿色", "difficulty": 1},
                {"word": "apple", "definition": "苹果", "difficulty": 1},
                {"word": "ball", "definition": "球", "difficulty": 1},
                {"word": "car", "definition": "汽车", "difficulty": 1},
                {"word": "door", "definition": "门", "difficulty": 1},
                {"word": "egg", "definition": "鸡蛋", "difficulty": 1},
                {"word": "fish", "definition": "鱼", "difficulty": 1},
                {"word": "girl", "definition": "女孩", "difficulty": 1},
                {"word": "hand", "definition": "手", "difficulty": 1},
                {"word": "ice", "definition": "冰", "difficulty": 1},
                {"word": "jump", "definition": "跳", "difficulty": 1},
                {"word": "kite", "definition": "风筝", "difficulty": 1},
                {"word": "lion", "definition": "狮子", "difficulty": 1},
                {"word": "milk", "definition": "牛奶", "difficulty": 1},
                {"word": "nose", "definition": "鼻子", "difficulty": 1},
                {"word": "orange", "definition": "橙子", "difficulty": 1},
                {"word": "pig", "definition": "猪", "difficulty": 1},
                {"word": "queen", "definition": "女王", "difficulty": 1},
                {"word": "rain", "definition": "雨", "difficulty": 1},
                {"word": "snow", "definition": "雪", "difficulty": 1},
                {"word": "tree", "definition": "树", "difficulty": 1},
                {"word": "up", "definition": "向上", "difficulty": 1},
                {"word": "van", "definition": "货车", "difficulty": 1},
                {"word": "water", "definition": "水", "difficulty": 1},
                {"word": "box", "definition": "盒子", "difficulty": 1},
                {"word": "yes", "definition": "是", "difficulty": 1},
                {"word": "zoo", "definition": "动物园", "difficulty": 1},
            ],
            "junior": [
                {"word": "about", "definition": "关于", "difficulty": 2},
                {"word": "above", "definition": "在...上面", "difficulty": 2},
                {"word": "accept", "definition": "接受", "difficulty": 2},
                {"word": "across", "definition": "穿过", "difficulty": 2},
                {"word": "action", "definition": "行动", "difficulty": 2},
                {"word": "active", "definition": "活跃的", "difficulty": 2},
                {"word": "actor", "definition": "演员", "difficulty": 2},
                {"word": "address", "definition": "地址", "difficulty": 2},
                {"word": "advice", "definition": "建议", "difficulty": 2},
                {"word": "afraid", "definition": "害怕的", "difficulty": 2},
                {"word": "after", "definition": "在...之后", "difficulty": 2},
                {"word": "again", "definition": "再次", "difficulty": 2},
                {"word": "age", "definition": "年龄", "difficulty": 2},
                {"word": "agree", "definition": "同意", "difficulty": 2},
                {"word": "air", "definition": "空气", "difficulty": 2},
                {"word": "almost", "definition": "几乎", "difficulty": 2},
                {"word": "alone", "definition": "独自", "difficulty": 2},
                {"word": "along", "definition": "沿着", "difficulty": 2},
                {"word": "always", "definition": "总是", "difficulty": 2},
                {"word": "among", "definition": "在...之中", "difficulty": 2},
            ],
            "cet4": [
                {"word": "abandon", "definition": "放弃", "difficulty": 3},
                {"word": "abstract", "definition": "抽象的", "difficulty": 3},
                {"word": "academic", "definition": "学术的", "difficulty": 3},
                {"word": "accelerate", "definition": "加速", "difficulty": 3},
                {"word": "access", "definition": "接近；入口", "difficulty": 3},
                {"word": "accomplish", "definition": "完成", "difficulty": 3},
                {"word": "accurate", "definition": "准确的", "difficulty": 3},
                {"word": "achieve", "definition": "达成", "difficulty": 3},
                {"word": "acquire", "definition": "获得", "difficulty": 3},
                {"word": "adapt", "definition": "适应", "difficulty": 3},
                {"word": "adequate", "definition": "充足的", "difficulty": 3},
                {"word": "adjust", "definition": "调整", "difficulty": 3},
                {"word": "administration", "definition": "管理", "difficulty": 3},
                {"word": "admire", "definition": "钦佩", "difficulty": 3},
                {"word": "admit", "definition": "承认", "difficulty": 3},
            ],
        }
        
        # 获取对应组别的词汇，如果没有则使用primary
        words = sample_words.get(group_code, sample_words["primary"])
        
        # 分配ID
        for word in words:
            word["id"] = self._word_id_counter
            self._word_id_counter += 1
        
        return words
    
    def get_groups(self) -> List[dict]:
        """获取所有词汇组别"""
        result = []
        for code, config in self.GROUPS.items():
            count = len(self._vocabulary_cache.get(code, []))
            result.append({
                "code": code,
                "name": config["name"],
                "count": count
            })
        return result
    
    def get_words(self, group: str, limit: int = 100) -> List[dict]:
        """获取指定组别的词汇"""
        # 优先检查年级词库
        words = self._grade_vocabulary_cache.get(group, [])
        if not words:
            words = self._vocabulary_cache.get(group, [])
        return words[:limit]
    
    def get_words_for_puzzle(self, group: str, count: int, max_word_len: int = None) -> List[dict]:
        """获取用于生成谜题的词汇（随机选择，优先选择适合长度的词）"""
        # 优先检查年级词库
        words = self._grade_vocabulary_cache.get(group, [])
        if not words:
            # 再检查主分类词库
            words = self._vocabulary_cache.get(group, [])
        if not words:
            # 如果指定组别没有词汇，使用primary
            words = self._vocabulary_cache.get("primary", [])
        
        result = []
        
        # 按词汇长度过滤，同时过滤掉含非字母字符的词
        if max_word_len:
            # 优先选择长度在2到max_word_len之间的纯字母词（单字母词不太适合填字游戏）
            suitable_words = [w for w in words if 2 <= len(w["word"]) <= max_word_len and is_pure_alpha(w["word"])]
            
            # 如果适合的词足够，直接使用
            if len(suitable_words) >= count:
                if len(suitable_words) <= count:
                    result = suitable_words.copy()
                else:
                    result = random.sample(suitable_words, count)
            else:
                # 如果适合的词不够，先加入所有适合的词，再补充稍长的词
                result = suitable_words.copy()
                # 获取稍长的词（max_word_len+1 到 max_word_len+3）
                longer_words = [w for w in words if max_word_len < len(w["word"]) <= max_word_len + 3 and is_pure_alpha(w["word"])]
                if longer_words:
                    need_more = count - len(result)
                    if len(longer_words) <= need_more:
                        result.extend(longer_words)
                    else:
                        result.extend(random.sample(longer_words, need_more))
        else:
            # 无长度限制时，过滤掉单字母词和非纯字母词
            suitable_words = [w for w in words if len(w["word"]) >= 2 and is_pure_alpha(w["word"])]
            if len(suitable_words) <= count:
                result = suitable_words.copy()
            else:
                result = random.sample(suitable_words, count)
        
        return result
    
    def get_word_by_id(self, word_id: int) -> Optional[dict]:
        """通过ID获取单词"""
        for words in self._vocabulary_cache.values():
            for word in words:
                if word.get("id") == word_id:
                    return word
        return None
    
    def search_words(self, query: str, group: str = None, limit: int = 20) -> List[dict]:
        """搜索单词"""
        results = []
        
        groups_to_search = [group] if group else self.GROUPS.keys()
        
        for g in groups_to_search:
            words = self._vocabulary_cache.get(g, [])
            for word in words:
                if query.lower() in word["word"].lower():
                    results.append(word)
                    if len(results) >= limit:
                        return results
        
        return results
    
    def get_all_words_for_csp(self, primary_group: str = None) -> List[dict]:
        """
        获取用于CSP生成的完整词库
        
        如果指定了主词库，只使用该词库的单词，不混入其他词库
        这样确保小学生只看到小学词汇，不会出现超纲词
        
        支持子分类：grade3_1, grade3_2, junior7_1 等
        """
        all_words = []
        word_set = set()
        
        # 检查是否是年级子分类（如 grade3_1, grade4_2, junior7_1 等）
        if primary_group and (primary_group.startswith("grade") or 
                              primary_group.startswith("junior") and "_" in primary_group or
                              primary_group.startswith("senior") and primary_group[-1].isdigit()):
            # 尝试从年级词库缓存获取
            if primary_group in self._grade_vocabulary_cache:
                words = self._grade_vocabulary_cache[primary_group]
                for w in words:
                    word_upper = w["word"].upper()
                    if word_upper not in word_set and len(word_upper) >= 2 and is_pure_alpha(word_upper):
                        word_set.add(word_upper)
                        all_words.append(w.copy())
                return all_words
        
        # 处理 primary_all 等全量词库
        if primary_group and "_all" in primary_group:
            # 获取主分类
            main_group = primary_group.replace("_all", "")
            if main_group in self.GROUPS:
                words = self._vocabulary_cache.get(main_group, [])
                for w in words:
                    word_upper = w["word"].upper()
                    if word_upper not in word_set and len(word_upper) >= 2 and is_pure_alpha(word_upper):
                        word_set.add(word_upper)
                        all_words.append(w.copy())
                return all_words
        
        # 只使用指定的词库，不再混合其他词库
        if primary_group and primary_group in self.GROUPS:
            groups_to_use = [primary_group]
        else:
            # 如果没有指定或指定的不存在，使用primary作为默认
            groups_to_use = ["primary"]
        
        # 只加载指定词库 - 优先从年级词库获取，其次从主词库
        for group in groups_to_use:
            # 优先检查年级词库缓存（从levels目录加载的，词汇更完整）
            words = self._grade_vocabulary_cache.get(group, [])
            if not words:
                # 如果年级词库没有，再从主词库获取
                words = self._vocabulary_cache.get(group, [])
            for w in words:
                word_upper = w["word"].upper()
                if word_upper not in word_set and len(word_upper) >= 2 and is_pure_alpha(word_upper):
                    word_set.add(word_upper)
                    all_words.append(w.copy())
        
        return all_words
