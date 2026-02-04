#!/usr/bin/env python3
"""
关卡检查报告生成脚本

检查每一关的：
- 单词数量
- 最大单词长度
- 最小单词长度
- 是否包含特殊字符（非A-Z字母）

生成详细的检查报告
"""

import json
import re
from pathlib import Path
from datetime import datetime


def is_pure_alpha(word: str) -> bool:
    """检查单词是否只包含26个英文字母"""
    return word.isalpha()


def check_level(level_data: dict) -> dict:
    """检查单个关卡的数据
    
    返回检查结果字典
    """
    level_num = level_data.get("level", 0)
    words = level_data.get("words", [])
    grid_size = level_data.get("grid_size", 0)
    difficulty = level_data.get("difficulty", "unknown")
    
    # 收集单词信息
    word_list = []
    has_special_char = False
    special_char_words = []
    
    for w in words:
        word = w.get("word", "").upper()
        word_list.append(word)
        
        if not is_pure_alpha(word):
            has_special_char = True
            # 找出非字母字符
            special_chars = [c for c in word if not c.isalpha()]
            special_char_words.append({
                "word": word,
                "special_chars": special_chars
            })
    
    word_count = len(word_list)
    
    if word_count > 0:
        word_lengths = [len(w) for w in word_list]
        max_length = max(word_lengths)
        min_length = min(word_lengths)
        avg_length = sum(word_lengths) / word_count
    else:
        max_length = 0
        min_length = 0
        avg_length = 0
    
    return {
        "level": level_num,
        "grid_size": grid_size,
        "difficulty": difficulty,
        "word_count": word_count,
        "max_length": max_length,
        "min_length": min_length,
        "avg_length": round(avg_length, 1),
        "words": word_list,
        "has_special_char": has_special_char,
        "special_char_words": special_char_words,
        "is_error": level_data.get("error", False),
        "error_message": level_data.get("message", "")
    }


def check_group(group_code: str, levels_dir: Path) -> dict:
    """检查单个词库的所有关卡"""
    group_dir = levels_dir / group_code
    
    if not group_dir.exists():
        return {
            "group_code": group_code,
            "exists": False,
            "level_count": 0,
            "levels": []
        }
    
    # 读取元数据
    meta_path = group_dir / "meta.json"
    meta = {}
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
    
    # 读取所有关卡文件
    level_files = sorted(group_dir.glob("*.json"), key=lambda p: int(p.stem) if p.stem.isdigit() else 0)
    level_files = [f for f in level_files if f.stem.isdigit()]  # 只保留数字命名的文件
    
    levels_result = []
    total_words = 0
    total_special_char_levels = 0
    error_levels = 0
    all_words_set = set()
    all_special_char_words = []
    
    for level_file in level_files:
        try:
            with open(level_file, "r", encoding="utf-8") as f:
                level_data = json.load(f)
            
            result = check_level(level_data)
            levels_result.append(result)
            
            total_words += result["word_count"]
            if result["has_special_char"]:
                total_special_char_levels += 1
                all_special_char_words.extend(result["special_char_words"])
            if result["is_error"]:
                error_levels += 1
            
            for w in result["words"]:
                all_words_set.add(w.upper())
                
        except Exception as e:
            levels_result.append({
                "level": int(level_file.stem) if level_file.stem.isdigit() else 0,
                "error": True,
                "error_message": str(e)
            })
            error_levels += 1
    
    # 统计词长分布
    length_distribution = {}
    for w in all_words_set:
        wlen = len(w)
        if wlen not in length_distribution:
            length_distribution[wlen] = 0
        length_distribution[wlen] += 1
    
    return {
        "group_code": group_code,
        "group_name": meta.get("name", group_code),
        "category": meta.get("category", "unknown"),
        "exists": True,
        "level_count": len(levels_result),
        "total_words_used": total_words,
        "unique_words": len(all_words_set),
        "vocab_size": meta.get("vocab_size", 0),
        "coverage": meta.get("coverage", 0),
        "error_levels": error_levels,
        "special_char_levels": total_special_char_levels,
        "special_char_words": all_special_char_words,
        "length_distribution": dict(sorted(length_distribution.items())),
        "levels": levels_result
    }


def generate_report(output_format: str = "both"):
    """生成完整的检查报告
    
    Args:
        output_format: "text", "json", or "both"
    """
    levels_dir = Path(__file__).parent.parent / "data" / "levels"
    report_dir = Path(__file__).parent.parent / "data" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取所有词库目录
    group_dirs = [d for d in levels_dir.iterdir() if d.is_dir()]
    group_codes = sorted([d.name for d in group_dirs])
    
    print(f"发现 {len(group_codes)} 个词库目录")
    print("=" * 80)
    
    all_results = []
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_groups": 0,
        "total_levels": 0,
        "total_words": 0,
        "total_unique_words": 0,
        "groups_with_special_chars": 0,
        "levels_with_special_chars": 0,
        "error_levels": 0,
        "all_special_char_words": []
    }
    
    for group_code in group_codes:
        print(f"\n检查词库: {group_code}")
        result = check_group(group_code, levels_dir)
        all_results.append(result)
        
        if result["exists"]:
            summary["total_groups"] += 1
            summary["total_levels"] += result["level_count"]
            summary["total_words"] += result["total_words_used"]
            summary["total_unique_words"] += result["unique_words"]
            summary["error_levels"] += result["error_levels"]
            summary["levels_with_special_chars"] += result["special_char_levels"]
            
            if result["special_char_levels"] > 0:
                summary["groups_with_special_chars"] += 1
                summary["all_special_char_words"].extend(result["special_char_words"])
            
            # 打印词库摘要
            print(f"  关卡数: {result['level_count']}")
            print(f"  唯一词数: {result['unique_words']}")
            print(f"  覆盖率: {result['coverage']}%")
            if result["special_char_levels"] > 0:
                print(f"  ⚠️ 含特殊字符关卡: {result['special_char_levels']}")
            if result["error_levels"] > 0:
                print(f"  ❌ 错误关卡: {result['error_levels']}")
    
    summary["groups"] = all_results
    
    # 生成文本报告
    if output_format in ["text", "both"]:
        text_report = generate_text_report(summary)
        text_path = report_dir / "levels_check_report.txt"
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text_report)
        print(f"\n文本报告已保存: {text_path}")
    
    # 生成JSON报告
    if output_format in ["json", "both"]:
        json_path = report_dir / "levels_check_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"JSON报告已保存: {json_path}")
    
    # 打印总结
    print("\n" + "=" * 80)
    print("检查报告总结")
    print("=" * 80)
    print(f"词库总数: {summary['total_groups']}")
    print(f"关卡总数: {summary['total_levels']}")
    print(f"词汇使用总次数: {summary['total_words']}")
    print(f"错误关卡数: {summary['error_levels']}")
    print(f"含特殊字符的词库: {summary['groups_with_special_chars']}")
    print(f"含特殊字符的关卡: {summary['levels_with_special_chars']}")
    
    if summary["all_special_char_words"]:
        print("\n⚠️ 发现的特殊字符单词:")
        unique_special = {}
        for item in summary["all_special_char_words"]:
            word = item["word"]
            if word not in unique_special:
                unique_special[word] = item["special_chars"]
        
        for word, chars in sorted(unique_special.items()):
            print(f"  {word} (特殊字符: {chars})")
    else:
        print("\n✅ 所有单词均为纯字母，无特殊字符！")
    
    return summary


def generate_text_report(summary: dict) -> str:
    """生成文本格式的详细报告"""
    lines = []
    lines.append("=" * 100)
    lines.append("关卡检查报告")
    lines.append(f"生成时间: {summary['generated_at']}")
    lines.append("=" * 100)
    lines.append("")
    
    # 总结部分
    lines.append("【总体统计】")
    lines.append("-" * 50)
    lines.append(f"词库总数: {summary['total_groups']}")
    lines.append(f"关卡总数: {summary['total_levels']}")
    lines.append(f"词汇使用总次数: {summary['total_words']}")
    lines.append(f"错误关卡数: {summary['error_levels']}")
    lines.append(f"含特殊字符的词库: {summary['groups_with_special_chars']}")
    lines.append(f"含特殊字符的关卡: {summary['levels_with_special_chars']}")
    lines.append("")
    
    # 特殊字符单词列表
    if summary["all_special_char_words"]:
        lines.append("【特殊字符单词列表】")
        lines.append("-" * 50)
        unique_special = {}
        for item in summary["all_special_char_words"]:
            word = item["word"]
            if word not in unique_special:
                unique_special[word] = item["special_chars"]
        
        for word, chars in sorted(unique_special.items()):
            lines.append(f"  {word} (特殊字符: {''.join(chars)})")
        lines.append("")
    
    # 各词库详情
    lines.append("【各词库详情】")
    lines.append("-" * 50)
    
    for group in summary.get("groups", []):
        if not group.get("exists"):
            continue
        
        lines.append("")
        lines.append(f"■ {group['group_name']} ({group['group_code']})")
        lines.append(f"  分类: {group['category']}")
        lines.append(f"  关卡数: {group['level_count']}")
        lines.append(f"  唯一词数: {group['unique_words']}")
        lines.append(f"  词库大小: {group['vocab_size']}")
        lines.append(f"  覆盖率: {group['coverage']}%")
        
        if group.get("length_distribution"):
            dist_str = ", ".join([f"{k}字母:{v}个" for k, v in group["length_distribution"].items()])
            lines.append(f"  词长分布: {dist_str}")
        
        if group.get("error_levels", 0) > 0:
            lines.append(f"  ❌ 错误关卡: {group['error_levels']}")
        
        if group.get("special_char_levels", 0) > 0:
            lines.append(f"  ⚠️ 含特殊字符关卡: {group['special_char_levels']}")
            for item in group.get("special_char_words", []):
                lines.append(f"     - {item['word']} (字符: {''.join(item['special_chars'])})")
        
        # 每关详情（可选，默认不包含以减少文件大小）
        # 如果需要每关详情，取消下面注释
        # lines.append("  各关详情:")
        # for level in group.get("levels", []):
        #     if level.get("is_error"):
        #         lines.append(f"    关卡{level['level']}: 错误 - {level.get('error_message', '')}")
        #     else:
        #         words_str = ", ".join(level.get("words", [])[:5])
        #         if len(level.get("words", [])) > 5:
        #             words_str += "..."
        #         lines.append(f"    关卡{level['level']}: {level['word_count']}词, 长度{level['min_length']}-{level['max_length']}, {level['grid_size']}×{level['grid_size']}")
    
    lines.append("")
    lines.append("=" * 100)
    lines.append("报告结束")
    lines.append("=" * 100)
    
    return "\n".join(lines)


def generate_detailed_csv(summary: dict, output_path: Path):
    """生成CSV格式的每关详细报告"""
    import csv
    
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "词库", "词库名", "分类", "关卡", "网格大小", "难度",
            "单词数", "最小长度", "最大长度", "平均长度",
            "单词列表", "有特殊字符", "错误"
        ])
        
        for group in summary.get("groups", []):
            if not group.get("exists"):
                continue
            
            for level in group.get("levels", []):
                writer.writerow([
                    group["group_code"],
                    group["group_name"],
                    group["category"],
                    level.get("level", 0),
                    level.get("grid_size", 0),
                    level.get("difficulty", ""),
                    level.get("word_count", 0),
                    level.get("min_length", 0),
                    level.get("max_length", 0),
                    level.get("avg_length", 0),
                    "|".join(level.get("words", [])),
                    "是" if level.get("has_special_char") else "否",
                    "是" if level.get("is_error") else "否"
                ])
    
    print(f"CSV详细报告已保存: {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='生成关卡检查报告')
    parser.add_argument('--format', '-f', choices=['text', 'json', 'both'], default='both',
                        help='输出格式: text, json, 或 both（默认）')
    parser.add_argument('--csv', '-c', action='store_true',
                        help='额外生成CSV格式的详细报告')
    
    args = parser.parse_args()
    
    summary = generate_report(args.format)
    
    if args.csv:
        csv_path = Path(__file__).parent.parent / "data" / "reports" / "levels_check_details.csv"
        generate_detailed_csv(summary, csv_path)
