#!/usr/bin/env python3
"""
反向检查脚本：检查每道题是否有超纲单词

对比每个关卡中使用的单词是否都在对应级别的词库中
"""

import json
from pathlib import Path
from typing import Dict, List, Set

# 数据目录
DATA_DIR = Path(__file__).parent.parent / "data"
LEVELS_DIR = DATA_DIR / "levels"
VOCAB_DIR = DATA_DIR / "vocabulary"

# 分组到词库的映射（可以是列表，表示允许使用多个词库）
GROUP_TO_VOCAB = {
    # 小学分组都使用 primary 词库
    "grade3_1": ["primary"],
    "grade3_2": ["primary"], 
    "grade4_1": ["primary"],
    "grade4_2": ["primary"],
    "grade5_1": ["primary"],
    "grade5_2": ["primary"],
    "grade6_1": ["primary"],
    "grade6_2": ["primary"],
    # 其他分组使用对应词库
    "junior": ["junior"],
    "senior": ["senior"],
    "ket": ["ket"],
    "pet": ["pet"],
    "cet4": ["cet4"],
    # 高级词库可以借用cet4的基础词汇
    "cet6": ["cet6", "cet4"],
    "postgrad": ["postgrad", "cet4"],
    "ielts": ["ielts", "cet4"],
    "toefl": ["toefl", "cet4"],
    "gre": ["gre", "cet4"],
}

def load_vocabulary(vocab_name: str) -> Set[str]:
    """加载词库，返回单词集合（全部小写）"""
    vocab_path = VOCAB_DIR / f"{vocab_name}.json"
    if not vocab_path.exists():
        print(f"警告: 词库文件不存在: {vocab_path}")
        return set()
    
    with open(vocab_path, "r", encoding="utf-8") as f:
        words = json.load(f)
    
    return {w["word"].lower() for w in words}

def load_level_data(group_code: str) -> dict:
    """加载关卡数据"""
    level_path = LEVELS_DIR / f"{group_code}.json"
    if not level_path.exists():
        print(f"警告: 关卡文件不存在: {level_path}")
        return {}
    
    with open(level_path, "r", encoding="utf-8") as f:
        return json.load(f)

def check_group_outofscope(group_code: str, vocab_set: Set[str], vocab_names: List[str]) -> dict:
    """检查一个分组的所有关卡是否有超纲单词"""
    level_data = load_level_data(group_code)
    if not level_data:
        return {"error": "无法加载关卡数据"}
    
    levels = level_data.get("levels", [])
    outofscope_levels = []
    total_words = 0
    outofscope_words = 0
    
    for level in levels:
        if level.get("error"):
            continue
        
        words = level.get("words", [])
        level_num = level.get("level", 0)
        level_outofscope = []
        
        for word_data in words:
            word = word_data.get("word", "").lower()
            total_words += 1
            
            if word and word not in vocab_set:
                outofscope_words += 1
                level_outofscope.append({
                    "word": word.upper(),
                    "definition": word_data.get("definition", "")
                })
        
        if level_outofscope:
            outofscope_levels.append({
                "level": level_num,
                "grid_size": level.get("grid_size", 0),
                "outofscope_words": level_outofscope
            })
    
    return {
        "group_code": group_code,
        "group_name": level_data.get("name", ""),
        "vocab_names": vocab_names,
        "vocab_size": len(vocab_set),
        "total_levels": len([l for l in levels if not l.get("error")]),
        "total_words": total_words,
        "outofscope_words_count": outofscope_words,
        "outofscope_levels_count": len(outofscope_levels),
        "outofscope_levels": outofscope_levels
    }

def main():
    """主函数：检查所有分组"""
    print("=" * 70)
    print("开始反向检查：查找超纲单词")
    print("=" * 70)
    
    # 加载所有词库
    vocab_cache = {}
    all_vocab_names = set()
    for vocab_list in GROUP_TO_VOCAB.values():
        for vn in vocab_list:
            all_vocab_names.add(vn)
    
    for vocab_name in all_vocab_names:
        vocab_cache[vocab_name] = load_vocabulary(vocab_name)
        print(f"已加载词库 {vocab_name}: {len(vocab_cache[vocab_name])} 个单词")
    
    print()
    
    # 检查每个分组
    all_results = []
    total_outofscope = 0
    
    for group_code, vocab_names in GROUP_TO_VOCAB.items():
        # 合并多个词库
        vocab_set = set()
        for vn in vocab_names:
            vocab_set.update(vocab_cache.get(vn, set()))
        result = check_group_outofscope(group_code, vocab_set, vocab_names)
        all_results.append(result)
        
        outofscope_count = result.get("outofscope_words_count", 0)
        total_outofscope += outofscope_count
        
        # 打印结果
        status = "✗ 有超纲" if outofscope_count > 0 else "✓ 正常"
        print(f"[{status}] {group_code} ({result.get('group_name', '')})")
        vocab_names_str = "+".join(vocab_names)
        print(f"    词库: {vocab_names_str} ({result.get('vocab_size', 0)}词)")
        print(f"    关卡: {result.get('total_levels', 0)}关, 单词: {result.get('total_words', 0)}个")
        
        if outofscope_count > 0:
            print(f"    超纲: {outofscope_count}个单词 (涉及{result.get('outofscope_levels_count', 0)}关)")
            # 显示前5个超纲单词
            for level_info in result.get("outofscope_levels", [])[:3]:
                words = [w["word"] for w in level_info["outofscope_words"]]
                print(f"      第{level_info['level']}关: {', '.join(words)}")
        print()
    
    # 保存详细报告
    report = {
        "total_groups": len(all_results),
        "total_outofscope_words": total_outofscope,
        "groups_with_issues": len([r for r in all_results if r.get("outofscope_words_count", 0) > 0]),
        "results": all_results
    }
    
    report_path = DATA_DIR / "outofscope_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("=" * 70)
    print(f"检查完成！共发现 {total_outofscope} 个超纲单词")
    print(f"详细报告已保存到: {report_path}")
    print("=" * 70)
    
    return report

if __name__ == "__main__":
    main()
