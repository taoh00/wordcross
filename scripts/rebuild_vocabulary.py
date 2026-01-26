#!/usr/bin/env python3
"""
重新汇总源词库到分类词库
从 data/words/ 目录读取源词库，汇总到 src/data/vocabulary/ 目录

分类映射：
- primary.json ← 04_人教版小学/PEPXiaoXue*.json
- junior.json ← 03_中高考/ChuZhong*.json + 05_人教版初中/*.json + 06_外研社初中/*.json
- senior.json ← 03_中高考/GaoZhong*.json + 07_人教版高中/*.json + 08_北师大高中/*.json
- cet4.json ← 01_考试类/CET4*.json
- cet6.json ← 01_考试类/CET6*.json
- postgrad.json ← 01_考试类/KaoYan*.json + 11_新东方扩展/KaoYan_3.json
- gre.json ← 02_出国留学/GRE_2.json + 11_新东方扩展/GRE_3.json
- toefl.json ← 02_出国留学/TOEFL_2.json + 11_新东方扩展/TOEFL_3.json
- ielts.json ← 02_出国留学/IELTSluan_2.json + 11_新东方扩展/IELTS_3.json
"""

import os
import json
from pathlib import Path
from collections import OrderedDict

# 路径配置
BASE_DIR = Path(__file__).parent.parent
SOURCE_DIR = BASE_DIR / "data" / "words"
OUTPUT_DIR = BASE_DIR / "src" / "data" / "vocabulary"

# 分类映射配置
CATEGORY_MAPPING = {
    "primary": {
        "name": "小学词汇",
        "difficulty": 1,
        "sources": [
            ("04_人教版小学", "*"),  # 所有PEP小学文件
        ]
    },
    "junior": {
        "name": "初中词汇",
        "difficulty": 2,
        "sources": [
            ("03_中高考", "ChuZhong*"),
            ("05_人教版初中", "*"),
            ("06_外研社初中", "*"),
        ]
    },
    "senior": {
        "name": "高中词汇",
        "difficulty": 3,
        "sources": [
            ("03_中高考", "GaoZhong*"),
            ("07_人教版高中", "*"),
            ("08_北师大高中", "*"),
        ]
    },
    "cet4": {
        "name": "四级词汇",
        "difficulty": 3,
        "sources": [
            ("01_考试类", "CET4*"),
        ]
    },
    "cet6": {
        "name": "六级词汇",
        "difficulty": 4,
        "sources": [
            ("01_考试类", "CET6*"),
        ]
    },
    "postgrad": {
        "name": "考研词汇",
        "difficulty": 4,
        "sources": [
            ("01_考试类", "KaoYan*"),
            ("11_新东方扩展", "KaoYan_3"),
        ]
    },
    "gre": {
        "name": "GRE词汇",
        "difficulty": 5,
        "sources": [
            ("02_出国留学", "GRE_2"),
            ("11_新东方扩展", "GRE_3"),
        ]
    },
    "toefl": {
        "name": "托福词汇",
        "difficulty": 4,
        "sources": [
            ("02_出国留学", "TOEFL_2"),
            ("11_新东方扩展", "TOEFL_3"),
        ]
    },
    "ielts": {
        "name": "雅思词汇",
        "difficulty": 4,
        "sources": [
            ("02_出国留学", "IELTSluan_2"),
            ("11_新东方扩展", "IELTS_3"),
        ]
    },
    "ket": {
        "name": "KET词汇",
        "difficulty": 2,
        "sources": []  # 需要额外处理，可能需要保留现有数据
    },
    "pet": {
        "name": "PET词汇",
        "difficulty": 3,
        "sources": []  # 需要额外处理，可能需要保留现有数据
    },
}


def load_source_file(filepath):
    """加载源词库文件，提取单词列表"""
    words = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 获取单词列表
        if isinstance(data, dict):
            word_list = data.get("words", [])
        elif isinstance(data, list):
            word_list = data
        else:
            return words
        
        # 提取单词信息
        for item in word_list:
            if isinstance(item, dict):
                word = item.get("word", "").strip()
                if not word:
                    continue
                
                # 提取翻译
                trans = item.get("trans", [])
                definition = ""
                if isinstance(trans, list) and trans:
                    # 合并所有翻译
                    trans_parts = []
                    for t in trans:
                        if isinstance(t, dict):
                            pos = t.get("pos", "")
                            tranCn = t.get("tranCn", "")
                            if pos and tranCn:
                                trans_parts.append(f"{pos}.{tranCn}")
                            elif tranCn:
                                trans_parts.append(tranCn)
                    definition = "; ".join(trans_parts)
                elif isinstance(trans, str):
                    definition = trans
                
                if not definition:
                    definition = item.get("translation", item.get("definition", ""))
                
                words.append({
                    "word": word,
                    "definition": definition,
                })
            elif isinstance(item, str):
                words.append({
                    "word": item.strip(),
                    "definition": "",
                })
    except Exception as e:
        print(f"  [!] 加载失败: {filepath} - {e}")
    
    return words


def match_files(category_dir, pattern):
    """根据模式匹配文件"""
    import fnmatch
    
    if not category_dir.exists():
        return []
    
    matched = []
    for f in category_dir.iterdir():
        if f.suffix == '.json':
            name = f.stem
            if pattern == "*" or fnmatch.fnmatch(name, pattern):
                matched.append(f)
    
    return sorted(matched)


def build_vocabulary(category_id, config):
    """构建单个分类词库"""
    print(f"\n{'='*60}")
    print(f"构建: {category_id} ({config['name']})")
    print(f"{'='*60}")
    
    all_words = OrderedDict()  # 使用有序字典去重
    source_stats = []
    
    for source_dir, pattern in config["sources"]:
        category_path = SOURCE_DIR / source_dir
        matched_files = match_files(category_path, pattern)
        
        for filepath in matched_files:
            words = load_source_file(filepath)
            before_count = len(all_words)
            
            for w in words:
                word_lower = w["word"].lower()
                if word_lower not in all_words:
                    all_words[word_lower] = w
                elif not all_words[word_lower]["definition"] and w["definition"]:
                    # 如果已有记录没有定义，但新记录有，则更新
                    all_words[word_lower]["definition"] = w["definition"]
            
            new_count = len(all_words) - before_count
            print(f"  {filepath.name}: {len(words)}词, 新增{new_count}")
            source_stats.append({
                "file": filepath.name,
                "total": len(words),
                "new": new_count
            })
    
    # 转换为列表格式并添加difficulty
    result = []
    for word_data in all_words.values():
        result.append({
            "word": word_data["word"],
            "definition": word_data["definition"],
            "difficulty": config["difficulty"]
        })
    
    print(f"\n总计: {len(result)} 个唯一单词")
    
    return result, source_stats


def main():
    print("=" * 60)
    print("重新汇总源词库到分类词库")
    print(f"源目录: {SOURCE_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)
    
    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    summary = {}
    
    for category_id, config in CATEGORY_MAPPING.items():
        if not config["sources"]:
            # 没有源配置的分类，保留现有数据
            existing_file = OUTPUT_DIR / f"{category_id}.json"
            if existing_file.exists():
                with open(existing_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                summary[category_id] = {
                    "name": config["name"],
                    "count": len(existing),
                    "status": "保留现有"
                }
                print(f"\n[{category_id}] 保留现有数据: {len(existing)}词")
            continue
        
        # 构建词库
        words, stats = build_vocabulary(category_id, config)
        
        if words:
            # 保存
            output_file = OUTPUT_DIR / f"{category_id}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(words, f, ensure_ascii=False, indent=2)
            
            summary[category_id] = {
                "name": config["name"],
                "count": len(words),
                "status": "已更新",
                "sources": stats
            }
            print(f"  已保存: {output_file}")
        else:
            summary[category_id] = {
                "name": config["name"],
                "count": 0,
                "status": "无数据"
            }
    
    # 打印汇总
    print("\n" + "=" * 60)
    print("汇总报告")
    print("=" * 60)
    print(f"{'分类':<15} {'名称':<15} {'数量':>8} {'状态':<10}")
    print("-" * 60)
    
    total_words = 0
    for category_id, info in summary.items():
        print(f"{category_id:<15} {info['name']:<15} {info['count']:>8} {info['status']:<10}")
        total_words += info["count"]
    
    print("-" * 60)
    print(f"{'总计':<15} {'':<15} {total_words:>8}")
    
    # 保存汇总报告
    report_file = OUTPUT_DIR / "rebuild_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n报告已保存: {report_file}")


if __name__ == "__main__":
    main()
