#!/usr/bin/env python3
"""
有道词典离线词库构建脚本
从 kajweb/dict 获取数据，构建本地离线词库
"""

import os
import io
import json
import time
import zipfile
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

# ============ 配置 ============
BASE_DIR = Path(__file__).parent.parent / "data"
WORDS_DIR = BASE_DIR / "words"
AUDIO_DIR = BASE_DIR / "audio"
CACHE_DIR = BASE_DIR / "cache"

# kajweb/dict 原始数据URL (GitHub raw)
KAJWEB_RAW_URL = "https://raw.githubusercontent.com/kajweb/dict/master/book"

# 有道原始数据URL（备用）
YOUDAO_NOS_URL = "http://ydschool-online.nos.netease.com"

# 有道发音API
YOUDAO_AUDIO_US = "https://dict.youdao.com/dictvoice?audio={word}&type=2"  # 美音
YOUDAO_AUDIO_UK = "https://dict.youdao.com/dictvoice?audio={word}&type=1"  # 英音

# 请求配置
REQUEST_TIMEOUT = 60
REQUEST_DELAY = 0.2  # 请求间隔，避免被封
MAX_WORKERS = 5      # 并发下载数

# ============ 词书分类定义 ============
# zip_prefix: GitHub上的文件前缀，格式为 {prefix}_{book_id}.zip
WORDBOOK_CATEGORIES = {
    "01_考试类": {
        "description": "四六级、考研等国内考试词汇",
        "books": [
            {"id": "CET4luan_1", "name": "四级真题核心词（图片记忆）", "count": 1162, "zip_prefix": "1523620217431"},
            {"id": "CET6luan_1", "name": "六级真题核心词（图片记忆）", "count": 1228, "zip_prefix": "1521164660466"},
            {"id": "KaoYanluan_1", "name": "考研必考词汇", "count": 1341, "zip_prefix": "1521164661106"},
            {"id": "CET4luan_2", "name": "四级英语词汇", "count": 3739, "zip_prefix": "1524052539052"},
            {"id": "CET6_2", "name": "六级英语词汇", "count": 2078, "zip_prefix": "1524052554766"},
            {"id": "KaoYan_2", "name": "考研英语词汇", "count": 4533, "zip_prefix": "1521164654696"},
            {"id": "CET4_3", "name": "新东方四级词汇", "count": 2607, "zip_prefix": "1521164643060"},
            {"id": "CET6_3", "name": "新东方六级词汇", "count": 2345, "zip_prefix": "1521164633851"},
        ]
    },
    "02_出国留学": {
        "description": "雅思、托福、GRE等出国考试词汇",
        "books": [
            {"id": "IELTSluan_2", "name": "雅思词汇", "count": 3427, "zip_prefix": "1521164624473"},
            {"id": "TOEFL_2", "name": "TOEFL词汇", "count": 9213, "zip_prefix": "1521164640451"},
            {"id": "GRE_2", "name": "GRE词汇", "count": 7199, "zip_prefix": "1521164637271"},
            {"id": "SAT_2", "name": "SAT词汇", "count": 4423, "zip_prefix": "1521164670910"},
            {"id": "GMATluan_2", "name": "GMAT词汇", "count": 3254, "zip_prefix": "1521164629611"},
        ]
    },
    "03_中高考": {
        "description": "中考、高考必备词汇",
        "books": [
            {"id": "ChuZhongluan_2", "name": "中考必备词汇", "count": 1420, "zip_prefix": "1521164669076"},
            {"id": "GaoZhongluan_2", "name": "高考必备词汇（图片记忆）", "count": 3668, "zip_prefix": "1521164673602"},
            {"id": "ChuZhong_3", "name": "新东方初中词汇", "count": 1803, "zip_prefix": "1521164652700"},
            {"id": "GaoZhong_3", "name": "新东方高中词汇", "count": 2340, "zip_prefix": "1521164679263"},
        ]
    },
    "04_人教版小学": {
        "description": "人教版PEP小学英语教材词汇",
        "books": [
            {"id": "PEPXiaoXue3_1", "name": "三年级上册", "count": 64, "zip_prefix": "1521164661774"},
            {"id": "PEPXiaoXue3_2", "name": "三年级下册", "count": 72, "zip_prefix": "1521164656604"},
            {"id": "PEPXiaoXue4_1", "name": "四年级上册", "count": 84, "zip_prefix": "1521164677447"},
            {"id": "PEPXiaoXue4_2", "name": "四年级下册", "count": 104, "zip_prefix": "1521164663086"},
            {"id": "PEPXiaoXue5_1", "name": "五年级上册", "count": 131, "zip_prefix": "1530101080610"},
            {"id": "PEPXiaoXue5_2", "name": "五年级下册", "count": 156, "zip_prefix": "1530101073491"},
            {"id": "PEPXiaoXue6_1", "name": "六年级上册", "count": 130, "zip_prefix": "1530101075331"},
            {"id": "PEPXiaoXue6_2", "name": "六年级下册", "count": 108, "zip_prefix": "1521164632445"},
        ]
    },
    "05_人教版初中": {
        "description": "人教版初中英语教材词汇",
        "books": [
            {"id": "PEPChuZhong7_1", "name": "七年级上册", "count": 392, "zip_prefix": "1530101067588"},
            {"id": "PEPChuZhong7_2", "name": "七年级下册", "count": 492, "zip_prefix": "1521164677043"},
            {"id": "PEPChuZhong8_1", "name": "八年级上册", "count": 419, "zip_prefix": "1530101070747"},
            {"id": "PEPChuZhong8_2", "name": "八年级下册", "count": 466, "zip_prefix": "1521164666522"},
            {"id": "PEPChuZhong9_1", "name": "九年级全册", "count": 551, "zip_prefix": "1530101078234"},
        ]
    },
    "06_外研社初中": {
        "description": "外研社版初中英语教材词汇",
        "books": [
            {"id": "WaiYanSheChuZhong_1", "name": "七年级上册", "count": 629, "zip_prefix": "reciteWord_1545032533243"},
            {"id": "WaiYanSheChuZhong_2", "name": "七年级下册", "count": 438, "zip_prefix": "reciteWord_1545032493536"},
            {"id": "WaiYanSheChuZhong_3", "name": "八年级上册", "count": 320, "zip_prefix": "reciteWord_1545032532744"},
            {"id": "WaiYanSheChuZhong_4", "name": "八年级下册", "count": 266, "zip_prefix": "reciteWord_1545032533455"},
            {"id": "WaiYanSheChuZhong_5", "name": "九年级上册", "count": 381, "zip_prefix": "reciteWord_1545032533808"},
            {"id": "WaiYanSheChuZhong_6", "name": "九年级下册", "count": 128, "zip_prefix": "reciteWord_1545032534071"},
        ]
    },
    "07_人教版高中": {
        "description": "人教版高中英语教材词汇",
        "books": [
            {"id": "PEPGaoZhong_1", "name": "必修1", "count": 311, "zip_prefix": "1521164674793"},
            {"id": "PEPGaoZhong_2", "name": "必修2", "count": 319, "zip_prefix": "1521164678610"},
            {"id": "PEPGaoZhong_3", "name": "必修3", "count": 366, "zip_prefix": "1521164676690"},
            {"id": "PEPGaoZhong_4", "name": "必修4", "count": 307, "zip_prefix": "1521164657462"},
            {"id": "PEPGaoZhong_5", "name": "必修5", "count": 357, "zip_prefix": "1521164657147"},
            {"id": "PEPGaoZhong_6", "name": "选修6", "count": 391, "zip_prefix": "1521164629184"},
            {"id": "PEPGaoZhong_7", "name": "选修7", "count": 384, "zip_prefix": "1521164648940"},
            {"id": "PEPGaoZhong_8", "name": "选修8", "count": 420, "zip_prefix": "1521164666266"},
            {"id": "PEPGaoZhong_9", "name": "选修9", "count": 352, "zip_prefix": "1521164670293"},
            {"id": "PEPGaoZhong_10", "name": "选修10", "count": 361, "zip_prefix": "1521164634796"},
            {"id": "PEPGaoZhong_11", "name": "选修11", "count": 309, "zip_prefix": "1521164639915"},
        ]
    },
    "08_北师大高中": {
        "description": "北师大版高中英语教材词汇",
        "books": [
            {"id": "BeiShiGaoZhong_1", "name": "必修1", "count": 226, "zip_prefix": "reciteWord"},
            {"id": "BeiShiGaoZhong_2", "name": "必修2", "count": 244, "zip_prefix": "1530101085958"},
            {"id": "BeiShiGaoZhong_3", "name": "必修3", "count": 295, "zip_prefix": "1530101089143"},
            {"id": "BeiShiGaoZhong_4", "name": "必修4", "count": 336, "zip_prefix": "reciteWord"},
            {"id": "BeiShiGaoZhong_5", "name": "必修5", "count": 327, "zip_prefix": "reciteWord"},
            {"id": "BeiShiGaoZhong_6", "name": "选修6", "count": 271, "zip_prefix": "reciteWord"},
            {"id": "BeiShiGaoZhong_7", "name": "选修7", "count": 334, "zip_prefix": "1530101082895"},
            {"id": "BeiShiGaoZhong_8", "name": "选修8", "count": 364, "zip_prefix": "reciteWord"},
            {"id": "BeiShiGaoZhong_9", "name": "选修9", "count": 299, "zip_prefix": "reciteWord"},
            {"id": "BeiShiGaoZhong_10", "name": "选修10", "count": 267, "zip_prefix": "reciteWord"},
            {"id": "BeiShiGaoZhong_11", "name": "选修11", "count": 330, "zip_prefix": "reciteWord"},
        ]
    },
    "09_专业英语": {
        "description": "专四专八专业英语词汇",
        "books": [
            {"id": "Level4luan_2", "name": "专四核心词汇", "count": 4025, "zip_prefix": "1521164625401"},
            {"id": "Level8luan_2", "name": "专八核心词汇", "count": 12197, "zip_prefix": "1521164650006"},
        ]
    },
    "10_商务英语": {
        "description": "商务英语BEC词汇",
        "books": [
            {"id": "BEC_2", "name": "商务英语词汇", "count": 2753, "zip_prefix": "1521164626760"},
        ]
    },
    "11_新东方扩展": {
        "description": "新东方系列扩展词汇",
        "books": [
            {"id": "KaoYan_3", "name": "新东方考研词汇", "count": 3728, "zip_prefix": "1521164658897"},
            {"id": "IELTS_3", "name": "新东方雅思词汇", "count": 3575, "zip_prefix": "1521164666922"},
            {"id": "TOEFL_3", "name": "新东方TOEFL词汇", "count": 4264, "zip_prefix": "1521164667985"},
            {"id": "GRE_3", "name": "新东方GRE词汇", "count": 6515, "zip_prefix": "1521164677706"},
            {"id": "BEC_3", "name": "新东方BEC词汇", "count": 2825, "zip_prefix": "1521164649506"},
        ]
    },
}


class WordbookBuilder:
    """词库构建器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        # 确保目录存在
        self._ensure_dirs()
        
        # 加载缓存
        self.downloaded = self._load_cache("downloaded.json")
        self.failed = self._load_cache("failed.json")
        
        # 统计
        self.stats = {
            "words_downloaded": 0,
            "words_skipped": 0,
            "words_failed": 0,
            "audio_downloaded": 0,
            "audio_skipped": 0,
            "audio_failed": 0,
        }
    
    def _ensure_dirs(self):
        """确保目录结构存在"""
        dirs = [
            WORDS_DIR, AUDIO_DIR, CACHE_DIR,
            AUDIO_DIR / "us", AUDIO_DIR / "uk"
        ]
        # 按首字母创建音频子目录
        for letter in "abcdefghijklmnopqrstuvwxyz":
            dirs.append(AUDIO_DIR / "us" / letter)
            dirs.append(AUDIO_DIR / "uk" / letter)
        
        # 创建分类目录
        for cat_id in WORDBOOK_CATEGORIES.keys():
            dirs.append(WORDS_DIR / cat_id)
        
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def _load_cache(self, filename):
        """加载缓存文件"""
        cache_file = CACHE_DIR / filename
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self, filename, data):
        """保存缓存文件"""
        cache_file = CACHE_DIR / filename
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def fetch_wordbook_from_kajweb(self, book_id, zip_prefix):
        """从kajweb/dict获取词书数据（zip格式）"""
        # 构造zip文件名
        zip_filename = f"{zip_prefix}_{book_id}.zip"
        
        # 尝试从GitHub raw下载
        url = f"{KAJWEB_RAW_URL}/{zip_filename}"
        
        try:
            print(f"  尝试下载: {zip_filename}")
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            
            if resp.status_code == 200:
                return self._parse_zip_data(resp.content, book_id)
            else:
                print(f"  [!] GitHub下载失败 HTTP {resp.status_code}")
                
                # 尝试从有道原始服务器下载
                url2 = f"{YOUDAO_NOS_URL}/{zip_filename}"
                print(f"  尝试备用源: {url2}")
                resp2 = self.session.get(url2, timeout=REQUEST_TIMEOUT)
                
                if resp2.status_code == 200:
                    return self._parse_zip_data(resp2.content, book_id)
                else:
                    print(f"  [!] 备用源也失败 HTTP {resp2.status_code}")
                    return None
                    
        except Exception as e:
            print(f"  [!] 请求失败: {e}")
            return None
    
    def _parse_zip_data(self, zip_content, book_id):
        """解析zip文件中的JSON数据（支持JSONL格式，每行一个JSON对象）"""
        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                # 列出zip内的文件
                file_list = zf.namelist()
                
                # 查找JSON文件
                json_files = [f for f in file_list if f.endswith('.json')]
                
                if not json_files:
                    print(f"  [!] zip中没有找到JSON文件: {file_list}")
                    return None
                
                # 读取第一个JSON文件（通常是 {book_id}.json）
                target_file = None
                for jf in json_files:
                    if book_id in jf:
                        target_file = jf
                        break
                
                if not target_file:
                    target_file = json_files[0]
                
                with zf.open(target_file) as f:
                    content = f.read().decode('utf-8')
                    print(f"  解析文件: {target_file}")
                    
                    # 尝试作为标准JSON解析
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        pass
                    
                    # 尝试作为JSONL解析（每行一个JSON对象）
                    words = []
                    for line in content.strip().split('\n'):
                        line = line.strip()
                        if line:
                            try:
                                obj = json.loads(line)
                                words.append(obj)
                            except json.JSONDecodeError:
                                continue
                    
                    if words:
                        print(f"  JSONL格式，共 {len(words)} 条")
                        return words
                    
                    print(f"  [!] 无法解析文件内容")
                    return None
                    
        except zipfile.BadZipFile:
            print(f"  [!] 无效的zip文件")
            return None
        except Exception as e:
            print(f"  [!] 解析失败: {e}")
            return None
    
    def download_audio(self, word, audio_type="us"):
        """下载单词音频"""
        word_lower = word.lower().strip()
        if not word_lower or not word_lower[0].isalpha():
            return None
        
        first_letter = word_lower[0]
        audio_dir = AUDIO_DIR / audio_type / first_letter
        audio_file = audio_dir / f"{word_lower}.mp3"
        
        # 检查是否已存在
        if audio_file.exists():
            self.stats["audio_skipped"] += 1
            return str(audio_file)
        
        # 检查缓存
        cache_key = f"{audio_type}:{word_lower}"
        if cache_key in self.downloaded:
            self.stats["audio_skipped"] += 1
            return self.downloaded[cache_key]
        
        # 下载
        if audio_type == "us":
            url = YOUDAO_AUDIO_US.format(word=quote(word_lower))
        else:
            url = YOUDAO_AUDIO_UK.format(word=quote(word_lower))
        
        try:
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200 and len(resp.content) > 1000:  # 有效音频至少1KB
                with open(audio_file, 'wb') as f:
                    f.write(resp.content)
                
                self.downloaded[cache_key] = str(audio_file)
                self.stats["audio_downloaded"] += 1
                return str(audio_file)
            else:
                self.failed[cache_key] = f"Invalid response: {resp.status_code}"
                self.stats["audio_failed"] += 1
                return None
        except Exception as e:
            self.failed[cache_key] = str(e)
            self.stats["audio_failed"] += 1
            return None
    
    def build_category(self, category_id, download_audio=True):
        """构建单个分类的所有词书"""
        if category_id not in WORDBOOK_CATEGORIES:
            print(f"[!] 未知分类: {category_id}")
            return
        
        category = WORDBOOK_CATEGORIES[category_id]
        category_dir = WORDS_DIR / category_id
        
        print(f"\n{'='*60}")
        print(f"构建分类: {category_id}")
        print(f"描述: {category['description']}")
        print(f"词书数量: {len(category['books'])}")
        print(f"{'='*60}")
        
        all_words = set()  # 收集该分类下的所有唯一单词
        
        for book in category["books"]:
            book_id = book["id"]
            book_name = book["name"]
            expected_count = book["count"]
            zip_prefix = book.get("zip_prefix", "")
            
            print(f"\n[{book_id}] {book_name} (预期{expected_count}词)")
            
            # 检查是否已构建
            book_file = category_dir / f"{book_id}.json"
            if book_file.exists():
                print(f"  [跳过] 已存在")
                # 读取已有数据，收集单词
                with open(book_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                    for w in existing.get("words", []):
                        if isinstance(w, dict) and "word" in w:
                            all_words.add(w["word"].lower())
                        elif isinstance(w, str):
                            all_words.add(w.lower())
                continue
            
            # 从kajweb获取数据
            print(f"  正在获取数据...")
            data = self.fetch_wordbook_from_kajweb(book_id, zip_prefix)
            
            if data is None:
                print(f"  [失败] 无法获取数据")
                continue
            
            # 处理数据格式
            words_data = self._normalize_wordbook_data(data, book_id)
            
            # 保存
            book_data = {
                "id": book_id,
                "name": book_name,
                "category": category_id,
                "count": len(words_data),
                "words": words_data
            }
            
            with open(book_file, 'w', encoding='utf-8') as f:
                json.dump(book_data, f, ensure_ascii=False, indent=2)
            
            print(f"  [完成] 获取 {len(words_data)} 词")
            self.stats["words_downloaded"] += len(words_data)
            
            # 收集单词
            for w in words_data:
                if isinstance(w, dict) and "word" in w:
                    all_words.add(w["word"].lower())
                elif isinstance(w, str):
                    all_words.add(w.lower())
            
            time.sleep(REQUEST_DELAY)
        
        # 下载该分类的音频
        if download_audio and all_words:
            print(f"\n下载音频 ({len(all_words)} 个唯一单词)...")
            self._download_audio_batch(list(all_words))
        
        # 保存缓存
        self._save_cache("downloaded.json", self.downloaded)
        self._save_cache("failed.json", self.failed)
        
        print(f"\n分类 {category_id} 构建完成!")
        self._print_stats()
    
    def _normalize_wordbook_data(self, data, book_id):
        """统一词书数据格式 - 处理有道词典复杂的嵌套结构"""
        words = []
        
        # kajweb/dict 的数据可能有多种格式
        if isinstance(data, list):
            raw_words = data
        elif isinstance(data, dict):
            raw_words = data.get("words", data.get("data", []))
        else:
            return words
        
        for item in raw_words:
            if isinstance(item, str):
                words.append({
                    "word": item,
                    "usphone": "",
                    "ukphone": "",
                    "trans": "",
                    "sentences": []
                })
            elif isinstance(item, dict):
                # 有道的数据结构较复杂，需要深层解析
                word_data = self._extract_word_data(item)
                if word_data and word_data.get("word"):
                    words.append(word_data)
        
        return words
    
    def _extract_word_data(self, item):
        """从有道的复杂数据结构中提取单词信息"""
        result = {
            "word": "",
            "usphone": "",
            "ukphone": "",
            "trans": [],
            "sentences": [],
            "phrases": [],
            "synos": []
        }
        
        # 直接获取headWord
        result["word"] = item.get("headWord", item.get("word", ""))
        
        # 尝试从content.word.content获取详细信息
        content = item.get("content", {})
        if isinstance(content, dict):
            word_content = content.get("word", {})
            if isinstance(word_content, dict):
                inner_content = word_content.get("content", {})
                if isinstance(inner_content, dict):
                    # 音标
                    result["usphone"] = inner_content.get("usphone", "")
                    result["ukphone"] = inner_content.get("ukphone", "")
                    
                    # 翻译
                    trans = inner_content.get("trans", [])
                    if isinstance(trans, list):
                        result["trans"] = [
                            {
                                "pos": t.get("pos", ""),
                                "tranCn": t.get("tranCn", "")
                            }
                            for t in trans if isinstance(t, dict)
                        ]
                    
                    # 例句
                    sentence = inner_content.get("sentence", {})
                    if isinstance(sentence, dict):
                        sentences = sentence.get("sentences", [])
                        if isinstance(sentences, list):
                            result["sentences"] = [
                                {
                                    "en": s.get("sContent", ""),
                                    "cn": s.get("sCn", "")
                                }
                                for s in sentences[:3] if isinstance(s, dict)
                            ]
                    
                    # 短语
                    phrase = inner_content.get("phrase", {})
                    if isinstance(phrase, dict):
                        phrases = phrase.get("phrases", [])
                        if isinstance(phrases, list):
                            result["phrases"] = [
                                {
                                    "en": p.get("pContent", ""),
                                    "cn": p.get("pCn", "")
                                }
                                for p in phrases[:3] if isinstance(p, dict)
                            ]
        
        # 如果没有从嵌套结构获取到，尝试直接获取
        if not result["usphone"]:
            result["usphone"] = item.get("usphone", "")
        if not result["ukphone"]:
            result["ukphone"] = item.get("ukphone", "")
        if not result["trans"]:
            trans = item.get("trans", item.get("translation", ""))
            if isinstance(trans, str) and trans:
                result["trans"] = [{"pos": "", "tranCn": trans}]
        
        return result
    
    def _download_audio_batch(self, words):
        """批量下载音频"""
        total = len(words)
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}
            for word in words:
                # 同时下载美音和英音
                futures[executor.submit(self.download_audio, word, "us")] = (word, "us")
                futures[executor.submit(self.download_audio, word, "uk")] = (word, "uk")
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                if completed % 100 == 0:
                    print(f"  音频下载进度: {completed}/{total*2}")
    
    def _print_stats(self):
        """打印统计信息"""
        print(f"\n统计:")
        print(f"  文本: 下载 {self.stats['words_downloaded']}, "
              f"跳过 {self.stats['words_skipped']}, "
              f"失败 {self.stats['words_failed']}")
        print(f"  音频: 下载 {self.stats['audio_downloaded']}, "
              f"跳过 {self.stats['audio_skipped']}, "
              f"失败 {self.stats['audio_failed']}")
    
    def build_all(self, download_audio=True):
        """构建所有分类"""
        print("=" * 60)
        print("开始构建全部词库")
        print("=" * 60)
        
        for category_id in WORDBOOK_CATEGORIES.keys():
            self.build_category(category_id, download_audio)
        
        # 生成索引
        self._generate_index()
        
        print("\n" + "=" * 60)
        print("全部构建完成!")
        print("=" * 60)
        self._print_stats()
    
    def _generate_index(self):
        """生成词书索引"""
        index = {
            "version": "1.0",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "categories": {}
        }
        
        for cat_id, cat_data in WORDBOOK_CATEGORIES.items():
            index["categories"][cat_id] = {
                "name": cat_id.split("_", 1)[1] if "_" in cat_id else cat_id,
                "description": cat_data["description"],
                "books": []
            }
            
            for book in cat_data["books"]:
                book_file = WORDS_DIR / cat_id / f"{book['id']}.json"
                if book_file.exists():
                    with open(book_file, 'r', encoding='utf-8') as f:
                        book_data = json.load(f)
                        index["categories"][cat_id]["books"].append({
                            "id": book["id"],
                            "name": book["name"],
                            "count": book_data.get("count", book["count"])
                        })
        
        # 保存索引
        with open(WORDS_DIR / "index.json", 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        
        print(f"\n索引文件已生成: {WORDS_DIR / 'index.json'}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="有道词典离线词库构建工具")
    parser.add_argument("--category", "-c", help="指定构建的分类ID，如 01_考试类")
    parser.add_argument("--all", "-a", action="store_true", help="构建所有分类")
    parser.add_argument("--no-audio", action="store_true", help="不下载音频")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有分类")
    
    args = parser.parse_args()
    
    if args.list:
        print("\n可用的分类:")
        for cat_id, cat_data in WORDBOOK_CATEGORIES.items():
            total_words = sum(b["count"] for b in cat_data["books"])
            print(f"  {cat_id}: {cat_data['description']} ({len(cat_data['books'])}本, {total_words}词)")
        return
    
    builder = WordbookBuilder()
    download_audio = not args.no_audio
    
    if args.all:
        builder.build_all(download_audio)
    elif args.category:
        builder.build_category(args.category, download_audio)
    else:
        # 默认显示帮助
        parser.print_help()
        print("\n示例:")
        print("  python build_wordbooks.py --list                    # 列出所有分类")
        print("  python build_wordbooks.py -c 01_考试类               # 构建考试类")
        print("  python build_wordbooks.py -c 01_考试类 --no-audio    # 只下载文本")
        print("  python build_wordbooks.py --all                     # 构建全部")


if __name__ == "__main__":
    main()
