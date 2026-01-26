#!/usr/bin/env python3
"""
音频下载脚本 - 批量下载唯一单词的发音
"""

import os
import json
import time
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

# ============ 配置 ============
BASE_DIR = Path(__file__).parent.parent / "data"
WORDS_DIR = BASE_DIR / "words"
AUDIO_DIR = BASE_DIR / "audio"
CACHE_DIR = BASE_DIR / "cache"

# 有道发音API
YOUDAO_AUDIO_US = "https://dict.youdao.com/dictvoice?audio={word}&type=2"  # 美音
YOUDAO_AUDIO_UK = "https://dict.youdao.com/dictvoice?audio={word}&type=1"  # 英音

# 请求配置
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.05  # 请求间隔
MAX_WORKERS = 10      # 并发下载数


class AudioDownloader:
    """音频下载器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        # 确保目录存在
        self._ensure_dirs()
        
        # 统计
        self.stats = {
            "downloaded": 0,
            "skipped": 0,
            "failed": 0,
        }
        self.failed_words = []
    
    def _ensure_dirs(self):
        """确保音频目录存在"""
        for audio_type in ["us", "uk"]:
            for letter in "abcdefghijklmnopqrstuvwxyz":
                (AUDIO_DIR / audio_type / letter).mkdir(parents=True, exist_ok=True)
    
    def get_unique_words(self):
        """从所有词书中提取唯一单词"""
        all_words = set()
        
        for cat_dir in sorted(WORDS_DIR.iterdir()):
            if cat_dir.is_dir():
                for book_file in cat_dir.glob('*.json'):
                    with open(book_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for w in data.get('words', []):
                            if isinstance(w, dict) and 'word' in w:
                                word = w['word'].lower().strip()
                                # 过滤掉非英文单词
                                if word and word[0].isalpha():
                                    all_words.add(word)
        
        return sorted(all_words)
    
    def download_word_audio(self, word, audio_type="us"):
        """下载单个单词的音频"""
        word_lower = word.lower().strip()
        if not word_lower or not word_lower[0].isalpha():
            return None
        
        first_letter = word_lower[0]
        audio_dir = AUDIO_DIR / audio_type / first_letter
        audio_file = audio_dir / f"{word_lower}.mp3"
        
        # 检查是否已存在
        if audio_file.exists():
            self.stats["skipped"] += 1
            return str(audio_file)
        
        # 下载
        if audio_type == "us":
            url = YOUDAO_AUDIO_US.format(word=quote(word_lower))
        else:
            url = YOUDAO_AUDIO_UK.format(word=quote(word_lower))
        
        try:
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200 and len(resp.content) > 500:  # 有效音频至少0.5KB
                with open(audio_file, 'wb') as f:
                    f.write(resp.content)
                self.stats["downloaded"] += 1
                return str(audio_file)
            else:
                self.stats["failed"] += 1
                self.failed_words.append(word_lower)
                return None
        except Exception as e:
            self.stats["failed"] += 1
            self.failed_words.append(word_lower)
            return None
    
    def download_all(self, audio_type="us", limit=None):
        """下载所有唯一单词的音频"""
        words = self.get_unique_words()
        if limit:
            words = words[:limit]
        
        total = len(words)
        print(f"开始下载 {total} 个单词的{audio_type}音频...")
        print(f"保存目录: {AUDIO_DIR / audio_type}")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(self.download_word_audio, word, audio_type): word
                for word in words
            }
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                if completed % 500 == 0:
                    elapsed = time.time() - start_time
                    rate = completed / elapsed
                    remaining = (total - completed) / rate if rate > 0 else 0
                    print(f"进度: {completed}/{total} ({completed*100/total:.1f}%) "
                          f"- 下载 {self.stats['downloaded']}, 跳过 {self.stats['skipped']}, "
                          f"失败 {self.stats['failed']} - 预计剩余 {remaining/60:.1f} 分钟")
        
        elapsed = time.time() - start_time
        print(f"\n下载完成! 耗时 {elapsed/60:.1f} 分钟")
        print(f"下载: {self.stats['downloaded']}, 跳过: {self.stats['skipped']}, 失败: {self.stats['failed']}")
        
        # 保存失败列表
        if self.failed_words:
            failed_file = CACHE_DIR / f"failed_{audio_type}.json"
            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump(self.failed_words, f, ensure_ascii=False, indent=2)
            print(f"失败列表已保存: {failed_file}")
        
        # 计算音频总大小
        total_size = 0
        for letter_dir in (AUDIO_DIR / audio_type).iterdir():
            if letter_dir.is_dir():
                for audio_file in letter_dir.glob('*.mp3'):
                    total_size += audio_file.stat().st_size
        
        print(f"音频总大小: {total_size / (1024*1024):.1f} MB")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="下载词书音频")
    parser.add_argument("--type", "-t", choices=["us", "uk", "both"], default="us",
                       help="音频类型: us=美音, uk=英音, both=双音")
    parser.add_argument("--limit", "-l", type=int, help="限制下载数量（测试用）")
    parser.add_argument("--stats", "-s", action="store_true", help="只显示统计信息")
    
    args = parser.parse_args()
    
    downloader = AudioDownloader()
    
    if args.stats:
        words = downloader.get_unique_words()
        print(f"唯一单词数: {len(words)}")
        
        # 统计已下载
        for audio_type in ["us", "uk"]:
            count = 0
            size = 0
            for letter_dir in (AUDIO_DIR / audio_type).iterdir():
                if letter_dir.is_dir():
                    for f in letter_dir.glob('*.mp3'):
                        count += 1
                        size += f.stat().st_size
            print(f"{audio_type}音频: {count} 个, {size/(1024*1024):.1f} MB")
        return
    
    if args.type == "both":
        print("=== 下载美音 ===")
        downloader.download_all("us", args.limit)
        
        # 重置统计
        downloader.stats = {"downloaded": 0, "skipped": 0, "failed": 0}
        downloader.failed_words = []
        
        print("\n=== 下载英音 ===")
        downloader.download_all("uk", args.limit)
    else:
        downloader.download_all(args.type, args.limit)


if __name__ == "__main__":
    main()
