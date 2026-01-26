#!/usr/bin/env python3
"""
关卡验证脚本 - 检查超纲问题和覆盖度

功能：
1. 检查每个关卡中的单词是否都在对应级别的词库中（超纲检查）
2. 统计词库中单词的覆盖度（使用了多少词库中的词）
3. 生成详细报告
"""

import json
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime


# 年级映射到PEP文件（累积方式）
GRADE_TO_PEP = {
    "grade3_1": ["PEPXiaoXue3_1.json"],
    "grade3_2": ["PEPXiaoXue3_1.json", "PEPXiaoXue3_2.json"],
    "grade4_1": ["PEPXiaoXue3_1.json", "PEPXiaoXue3_2.json", "PEPXiaoXue4_1.json"],
    "grade4_2": ["PEPXiaoXue3_1.json", "PEPXiaoXue3_2.json", "PEPXiaoXue4_1.json", "PEPXiaoXue4_2.json"],
    "grade5_1": ["PEPXiaoXue3_1.json", "PEPXiaoXue3_2.json", "PEPXiaoXue4_1.json", "PEPXiaoXue4_2.json", "PEPXiaoXue5_1.json"],
    "grade5_2": ["PEPXiaoXue3_1.json", "PEPXiaoXue3_2.json", "PEPXiaoXue4_1.json", "PEPXiaoXue4_2.json", "PEPXiaoXue5_1.json", "PEPXiaoXue5_2.json"],
    "grade6_1": ["PEPXiaoXue3_1.json", "PEPXiaoXue3_2.json", "PEPXiaoXue4_1.json", "PEPXiaoXue4_2.json", "PEPXiaoXue5_1.json", "PEPXiaoXue5_2.json", "PEPXiaoXue6_1.json"],
    "grade6_2": ["PEPXiaoXue3_1.json", "PEPXiaoXue3_2.json", "PEPXiaoXue4_1.json", "PEPXiaoXue4_2.json", "PEPXiaoXue5_1.json", "PEPXiaoXue5_2.json", "PEPXiaoXue6_1.json", "PEPXiaoXue6_2.json"],
}


def load_pep_vocabulary(grade_code: str) -> Set[str]:
    """加载指定年级的PEP词库（累积方式）"""
    pep_files = GRADE_TO_PEP.get(grade_code, [])
    if not pep_files:
        return set()
    
    pep_dir = Path(__file__).parent.parent.parent / "data" / "words" / "04_人教版小学"
    word_set = set()
    
    for pep_file in pep_files:
        file_path = pep_dir / pep_file
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for w in data.get("words", []):
                        word = w.get("word", "").strip().lower()
                        if word and " " not in word:
                            word_set.add(word)
            except Exception as e:
                print(f"警告: 加载PEP文件失败 {pep_file}: {e}")
    
    return word_set


def load_vocabulary_file(group_code: str) -> Set[str]:
    """加载汇总词库文件"""
    vocab_dir = Path(__file__).parent.parent / "data" / "vocabulary"
    file_path = vocab_dir / f"{group_code}.json"
    
    if not file_path.exists():
        return set()
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            word_set = set()
            for w in data:
                word = w.get("word", "").strip().lower()
                if word and " " not in word:
                    word_set.add(word)
            return word_set
    except Exception as e:
        print(f"警告: 加载词库文件失败 {file_path}: {e}")
        return set()


def get_vocabulary_for_group(group_code: str) -> Set[str]:
    """获取指定分组的词库"""
    if group_code.startswith("grade"):
        return load_pep_vocabulary(group_code)
    else:
        return load_vocabulary_file(group_code)


def load_level_data(group_code: str) -> List[dict]:
    """加载关卡数据"""
    levels_dir = Path(__file__).parent.parent / "data" / "levels"
    file_path = levels_dir / f"{group_code}.json"
    
    if not file_path.exists():
        return []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("levels", [])
    except Exception as e:
        print(f"警告: 加载关卡文件失败 {file_path}: {e}")
        return []


def verify_group(group_code: str) -> dict:
    """验证单个分组的关卡"""
    print(f"\n验证分组: {group_code}")
    
    # 加载词库
    vocabulary = get_vocabulary_for_group(group_code)
    vocab_count = len(vocabulary)
    print(f"  词库大小: {vocab_count}")
    
    if vocab_count == 0:
        return {
            "group_code": group_code,
            "status": "error",
            "error": "词库为空"
        }
    
    # 加载关卡数据
    levels = load_level_data(group_code)
    level_count = len(levels)
    print(f"  关卡数量: {level_count}")
    
    if level_count == 0:
        return {
            "group_code": group_code,
            "status": "no_levels",
            "vocab_count": vocab_count,
            "level_count": 0
        }
    
    # 统计变量
    used_words = set()  # 关卡中使用的词
    out_of_scope_words = set()  # 超纲词
    out_of_scope_levels = []  # 含超纲词的关卡
    
    # 遍历每个关卡
    for level in levels:
        level_num = level.get("level", 0)
        words_in_level = level.get("words", [])
        
        level_out_of_scope = []
        
        for word_info in words_in_level:
            word = word_info.get("word", "").strip().lower()
            if not word:
                continue
            
            used_words.add(word)
            
            # 检查是否超纲
            if word not in vocabulary:
                out_of_scope_words.add(word)
                level_out_of_scope.append(word)
        
        if level_out_of_scope:
            out_of_scope_levels.append({
                "level": level_num,
                "words": level_out_of_scope
            })
    
    # 计算覆盖度
    in_scope_words = used_words - out_of_scope_words
    coverage = len(in_scope_words) / vocab_count * 100 if vocab_count > 0 else 0
    
    result = {
        "group_code": group_code,
        "status": "verified",
        "vocab_count": vocab_count,
        "level_count": level_count,
        "used_word_count": len(used_words),
        "in_scope_count": len(in_scope_words),
        "out_of_scope_count": len(out_of_scope_words),
        "out_of_scope_words": sorted(list(out_of_scope_words)),
        "out_of_scope_levels": out_of_scope_levels[:10],  # 只记录前10个
        "coverage_percent": round(coverage, 2),
        "is_valid": len(out_of_scope_words) == 0,
        "coverage_ok": coverage >= 70
    }
    
    # 打印摘要
    if out_of_scope_words:
        print(f"  ❌ 超纲词: {len(out_of_scope_words)} 个")
        print(f"     示例: {sorted(list(out_of_scope_words))[:5]}")
    else:
        print(f"  ✓ 无超纲词")
    
    print(f"  覆盖度: {coverage:.1f}% ({'✓' if coverage >= 70 else '❌ 不足70%'})")
    
    return result


def verify_all_groups() -> dict:
    """验证所有分组"""
    # 所有分组
    all_groups = [
        "grade3_1", "grade3_2", "grade4_1", "grade4_2",
        "grade5_1", "grade5_2", "grade6_1", "grade6_2",
        "junior", "senior", "ket", "pet",
        "cet4", "cet6", "postgrad", "ielts", "toefl", "gre"
    ]
    
    print("=" * 60)
    print("关卡验证 - 超纲检查与覆盖度统计")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {}
    valid_count = 0
    coverage_ok_count = 0
    
    for group_code in all_groups:
        result = verify_group(group_code)
        results[group_code] = result
        
        if result.get("is_valid"):
            valid_count += 1
        if result.get("coverage_ok"):
            coverage_ok_count += 1
    
    # 汇总
    summary = {
        "verified_at": datetime.now().isoformat(),
        "total_groups": len(all_groups),
        "valid_groups": valid_count,
        "coverage_ok_groups": coverage_ok_count,
        "groups": results
    }
    
    # 保存报告
    report_path = Path(__file__).parent.parent / "data" / "verification_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("验证完成")
    print("=" * 60)
    print(f"总分组数: {len(all_groups)}")
    print(f"无超纲词: {valid_count}/{len(all_groups)}")
    print(f"覆盖度≥70%: {coverage_ok_count}/{len(all_groups)}")
    print(f"报告已保存: {report_path}")
    
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='验证关卡数据')
    parser.add_argument('--group', '-g', type=str, help='指定验证的分组代码')
    parser.add_argument('--all', '-a', action='store_true', help='验证所有分组')
    
    args = parser.parse_args()
    
    if args.group:
        result = verify_group(args.group)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        verify_all_groups()
