#!/usr/bin/env python3
"""
清理包含非纯字母单词的关卡，并重新编号使关卡连续

功能：
1. 扫描所有词库的关卡文件
2. 找出包含非纯字母单词（如连字符、撇号、空格等）的关卡
3. 删除这些关卡
4. 重新编号剩余关卡，确保编号连续（不跳号）
5. 更新 meta.json 中的关卡数量
"""

import json
import os
import shutil
from pathlib import Path
from typing import List, Dict, Set


def is_pure_alpha(word: str) -> bool:
    """检查单词是否只包含26个英文字母"""
    return word.isalpha()


def check_level_validity(level_path: Path) -> tuple[bool, List[str]]:
    """检查关卡是否有效（所有单词都是纯字母）
    
    返回: (是否有效, 无效单词列表)
    """
    try:
        with open(level_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        invalid_words = []
        for word_info in data.get('words', []):
            word = word_info.get('word', '')
            if not is_pure_alpha(word):
                invalid_words.append(word)
        
        return len(invalid_words) == 0, invalid_words
    except Exception as e:
        print(f"  读取关卡文件出错 {level_path}: {e}")
        return False, ["ERROR"]


def get_all_level_files(group_dir: Path) -> List[Path]:
    """获取词库目录下所有关卡文件（按编号排序）"""
    level_files = []
    for f in group_dir.iterdir():
        if f.suffix == '.json' and f.stem.isdigit():
            level_files.append(f)
    level_files.sort(key=lambda x: int(x.stem))
    return level_files


def cleanup_group(group_dir: Path, dry_run: bool = False) -> Dict:
    """清理单个词库的无效关卡
    
    返回统计信息
    """
    group_name = group_dir.name
    level_files = get_all_level_files(group_dir)
    
    if not level_files:
        return {"group": group_name, "total": 0, "invalid": 0, "deleted": []}
    
    # 检查每个关卡
    valid_levels = []
    invalid_levels = []
    
    for level_path in level_files:
        is_valid, invalid_words = check_level_validity(level_path)
        if is_valid:
            valid_levels.append(level_path)
        else:
            invalid_levels.append({
                "path": level_path,
                "level": int(level_path.stem),
                "invalid_words": invalid_words
            })
    
    if not invalid_levels:
        return {
            "group": group_name,
            "total": len(level_files),
            "invalid": 0,
            "deleted": [],
            "final_count": len(level_files)
        }
    
    # 打印无效关卡信息
    print(f"\n📂 {group_name}: 发现 {len(invalid_levels)} 个无效关卡")
    for inv in invalid_levels:
        print(f"   第 {inv['level']} 关: {', '.join(inv['invalid_words'])}")
    
    if dry_run:
        return {
            "group": group_name,
            "total": len(level_files),
            "invalid": len(invalid_levels),
            "deleted": [inv["level"] for inv in invalid_levels],
            "final_count": len(valid_levels)
        }
    
    # 删除无效关卡并重新编号
    print(f"   正在删除并重新编号...")
    
    # 先删除所有无效关卡
    for inv in invalid_levels:
        os.remove(inv["path"])
    
    # 获取剩余的有效关卡（按原编号排序）
    remaining_files = get_all_level_files(group_dir)
    
    # 重新编号
    for new_num, level_path in enumerate(remaining_files, start=1):
        old_num = int(level_path.stem)
        if old_num != new_num:
            # 需要重命名
            new_path = level_path.parent / f"{new_num}.json"
            # 同时更新文件内容中的 level 字段
            with open(level_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data['level'] = new_num
            with open(level_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            # 重命名文件
            shutil.move(level_path, new_path)
    
    # 更新 meta.json
    meta_path = group_dir / 'meta.json'
    if meta_path.exists():
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        old_count = meta.get('level_count', len(level_files))
        meta['level_count'] = len(valid_levels)
        meta['success_count'] = len(valid_levels)
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"   更新 meta.json: {old_count} -> {len(valid_levels)} 关")
    
    print(f"   ✅ 完成: 删除 {len(invalid_levels)} 关，剩余 {len(valid_levels)} 关")
    
    return {
        "group": group_name,
        "total": len(level_files),
        "invalid": len(invalid_levels),
        "deleted": [inv["level"] for inv in invalid_levels],
        "final_count": len(valid_levels)
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="清理无效关卡并重新编号")
    parser.add_argument('--dry-run', action='store_true', help='只扫描不执行删除')
    parser.add_argument('-g', '--groups', nargs='+', help='指定词库（默认全部）')
    args = parser.parse_args()
    
    levels_dir = Path(__file__).parent.parent / 'data' / 'levels'
    
    if not levels_dir.exists():
        print(f"❌ 关卡目录不存在: {levels_dir}")
        return
    
    # 获取所有词库目录
    if args.groups:
        group_dirs = [levels_dir / g for g in args.groups if (levels_dir / g).is_dir()]
    else:
        group_dirs = [d for d in levels_dir.iterdir() if d.is_dir()]
    
    group_dirs.sort(key=lambda x: x.name)
    
    print(f"{'=' * 60}")
    print(f"清理无效关卡（包含非纯字母单词）")
    print(f"{'=' * 60}")
    print(f"模式: {'扫描模式（不删除）' if args.dry_run else '执行模式（会删除并重编号）'}")
    print(f"词库数量: {len(group_dirs)}")
    
    # 处理每个词库
    results = []
    total_invalid = 0
    total_deleted = 0
    
    for group_dir in group_dirs:
        result = cleanup_group(group_dir, args.dry_run)
        results.append(result)
        total_invalid += result["invalid"]
        if not args.dry_run:
            total_deleted += result["invalid"]
    
    # 汇总报告
    print(f"\n{'=' * 60}")
    print(f"汇总报告")
    print(f"{'=' * 60}")
    
    affected_groups = [r for r in results if r["invalid"] > 0]
    if affected_groups:
        print(f"\n受影响的词库 ({len(affected_groups)} 个):")
        for r in affected_groups:
            deleted_str = ', '.join(map(str, r["deleted"][:10]))
            if len(r["deleted"]) > 10:
                deleted_str += f" ... 等 {len(r['deleted'])} 关"
            print(f"  {r['group']}: 删除 {r['invalid']} 关 ({r['total']} -> {r['final_count']})")
            print(f"    删除的关卡: {deleted_str}")
    else:
        print("\n✅ 所有关卡都是有效的，无需清理")
    
    print(f"\n总计:")
    print(f"  扫描词库: {len(results)} 个")
    print(f"  无效关卡: {total_invalid} 个")
    if not args.dry_run:
        print(f"  已删除并重编号: {total_deleted} 个")
    
    # 更新 levels_summary.json
    if not args.dry_run and total_deleted > 0:
        summary_path = levels_dir / 'levels_summary.json'
        if summary_path.exists():
            print("\n正在更新 levels_summary.json...")
            with open(summary_path, 'r', encoding='utf-8') as f:
                summary = json.load(f)
            
            for r in results:
                if r["invalid"] > 0 and r["group"] in summary.get("groups", {}):
                    summary["groups"][r["group"]]["level_count"] = r["final_count"]
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            print("✅ levels_summary.json 已更新")


if __name__ == "__main__":
    main()
