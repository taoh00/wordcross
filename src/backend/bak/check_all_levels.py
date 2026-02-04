#!/usr/bin/env python3
"""
检查所有关卡的生成情况

验证项目：
1. 每个分组是否有10关
2. 每关是否有至少2个单词
3. 网格大小是否合理（5-10）
4. 单词是否有定义
5. 单词位置是否正确
6. 预填字母是否设置

输出检查报告。
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


def check_level(level_data: dict, group_code: str, level_num: int) -> List[dict]:
    """检查单个关卡，返回问题列表"""
    issues = []
    
    # 检查是否有错误标记
    if level_data.get("error"):
        issues.append({
            "type": "error",
            "severity": "critical",
            "message": f"关卡生成失败: {level_data.get('message', '未知错误')}"
        })
        return issues
    
    # 检查网格大小
    grid_size = level_data.get("grid_size", 0)
    if grid_size < 5:
        issues.append({
            "type": "grid_size",
            "severity": "warning",
            "message": f"网格太小: {grid_size}x{grid_size}"
        })
    elif grid_size > 15:
        issues.append({
            "type": "grid_size",
            "severity": "warning",
            "message": f"网格太大: {grid_size}x{grid_size}"
        })
    
    # 检查单词数量
    words = level_data.get("words", [])
    word_count = len(words)
    if word_count < 2:
        issues.append({
            "type": "word_count",
            "severity": "critical",
            "message": f"单词数量不足: 只有{word_count}个"
        })
    elif word_count < 3:
        issues.append({
            "type": "word_count",
            "severity": "warning",
            "message": f"单词数量偏少: 只有{word_count}个"
        })
    
    # 检查每个单词
    for i, word_info in enumerate(words):
        word = word_info.get("word", "")
        definition = word_info.get("definition", "")
        direction = word_info.get("direction", "")
        start_row = word_info.get("start_row", -1)
        start_col = word_info.get("start_col", -1)
        
        # 检查单词是否为空
        if not word:
            issues.append({
                "type": "empty_word",
                "severity": "critical",
                "message": f"第{i+1}个单词为空"
            })
        
        # 检查定义是否为空
        if not definition:
            issues.append({
                "type": "empty_definition",
                "severity": "warning",
                "message": f"单词 '{word}' 没有定义"
            })
        
        # 检查方向是否有效
        if direction not in ["across", "down"]:
            issues.append({
                "type": "invalid_direction",
                "severity": "critical",
                "message": f"单词 '{word}' 方向无效: {direction}"
            })
        
        # 检查位置是否有效
        if start_row < 0 or start_col < 0:
            issues.append({
                "type": "invalid_position",
                "severity": "critical",
                "message": f"单词 '{word}' 位置无效: ({start_row}, {start_col})"
            })
        
        # 检查单词是否超出网格
        word_len = len(word)
        if direction == "across" and start_col + word_len > grid_size:
            issues.append({
                "type": "out_of_bounds",
                "severity": "critical",
                "message": f"单词 '{word}' 横向超出网格"
            })
        if direction == "down" and start_row + word_len > grid_size:
            issues.append({
                "type": "out_of_bounds",
                "severity": "critical",
                "message": f"单词 '{word}' 纵向超出网格"
            })
    
    # 检查cells数组
    cells = level_data.get("cells", [])
    if not cells:
        issues.append({
            "type": "missing_cells",
            "severity": "critical",
            "message": "缺少cells数组"
        })
    elif len(cells) != grid_size:
        issues.append({
            "type": "cells_size_mismatch",
            "severity": "critical",
            "message": f"cells行数({len(cells)})与grid_size({grid_size})不匹配"
        })
    
    # 检查预填字母
    prefilled = level_data.get("prefilled", {})
    if not prefilled:
        issues.append({
            "type": "no_prefilled",
            "severity": "info",
            "message": "没有预填字母"
        })
    
    return issues


def check_all_levels():
    """检查所有关卡"""
    print("=" * 70)
    print("开始检查所有关卡")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 加载关卡数据
    levels_path = Path(__file__).parent.parent / "data" / "primary_campaign_levels.json"
    
    if not levels_path.exists():
        print("错误: 关卡数据文件不存在!")
        return None
    
    with open(levels_path, "r", encoding="utf-8") as f:
        all_levels = json.load(f)
    
    # 检查结果
    report = {
        "check_time": datetime.now().isoformat(),
        "total_groups": 0,
        "total_levels": 0,
        "total_words": 0,
        "issues_by_severity": {
            "critical": 0,
            "warning": 0,
            "info": 0
        },
        "groups": [],
        "all_issues": []
    }
    
    # 遍历所有分组
    for group_code, group_data in all_levels.items():
        group_name = group_data.get("name", group_code)
        levels = group_data.get("levels", [])
        
        print(f"\n检查 [{group_name}] ({group_code})")
        
        group_report = {
            "group_code": group_code,
            "group_name": group_name,
            "level_count": len(levels),
            "word_count": 0,
            "issues": [],
            "status": "ok"
        }
        
        # 检查是否有10关
        if len(levels) != 10:
            issue = {
                "level": 0,
                "type": "missing_levels",
                "severity": "warning",
                "message": f"关卡数量不是10个，实际有{len(levels)}个"
            }
            group_report["issues"].append(issue)
            report["issues_by_severity"]["warning"] += 1
        
        # 检查每一关
        for level_data in levels:
            level_num = level_data.get("level", 0)
            
            # 统计单词数
            words = level_data.get("words", [])
            group_report["word_count"] += len(words)
            
            # 检查关卡
            issues = check_level(level_data, group_code, level_num)
            
            for issue in issues:
                issue["level"] = level_num
                issue["group"] = group_code
                group_report["issues"].append(issue)
                report["issues_by_severity"][issue["severity"]] += 1
                report["all_issues"].append(issue)
        
        # 确定分组状态
        critical_count = sum(1 for i in group_report["issues"] if i["severity"] == "critical")
        warning_count = sum(1 for i in group_report["issues"] if i["severity"] == "warning")
        
        if critical_count > 0:
            group_report["status"] = "error"
        elif warning_count > 0:
            group_report["status"] = "warning"
        else:
            group_report["status"] = "ok"
        
        report["groups"].append(group_report)
        report["total_groups"] += 1
        report["total_levels"] += len(levels)
        report["total_words"] += group_report["word_count"]
        
        # 打印分组结果
        status_icon = {"ok": "✓", "warning": "⚠", "error": "✗"}[group_report["status"]]
        print(f"  {status_icon} {len(levels)}关, {group_report['word_count']}词, {len(group_report['issues'])}个问题")
    
    # 保存检查报告
    report_path = Path(__file__).parent.parent / "data" / "levels_check_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n检查报告已保存到: {report_path}")
    
    # 打印汇总
    print("\n" + "=" * 70)
    print("检查完成 - 汇总报告")
    print("=" * 70)
    print(f"总分组数: {report['total_groups']}")
    print(f"总关卡数: {report['total_levels']}")
    print(f"总单词数: {report['total_words']}")
    print(f"\n问题统计:")
    print(f"  严重问题 (critical): {report['issues_by_severity']['critical']}")
    print(f"  警告 (warning): {report['issues_by_severity']['warning']}")
    print(f"  提示 (info): {report['issues_by_severity']['info']}")
    
    # 列出所有严重问题
    critical_issues = [i for i in report["all_issues"] if i["severity"] == "critical"]
    if critical_issues:
        print(f"\n严重问题列表 ({len(critical_issues)}个):")
        for issue in critical_issues[:20]:  # 最多显示20个
            print(f"  [{issue['group']}] 关卡{issue['level']}: {issue['message']}")
        if len(critical_issues) > 20:
            print(f"  ... 还有 {len(critical_issues) - 20} 个严重问题")
    else:
        print("\n没有发现严重问题 ✓")
    
    # 列出警告
    warning_issues = [i for i in report["all_issues"] if i["severity"] == "warning"]
    if warning_issues:
        print(f"\n警告列表 ({len(warning_issues)}个):")
        for issue in warning_issues[:10]:  # 最多显示10个
            print(f"  [{issue['group']}] 关卡{issue['level']}: {issue['message']}")
        if len(warning_issues) > 10:
            print(f"  ... 还有 {len(warning_issues) - 10} 个警告")
    
    print("\n" + "-" * 70)
    
    # 各分组状态
    print("\n各分组状态:")
    print("-" * 70)
    print(f"{'分组代码':<15} {'名称':<15} {'关卡数':<8} {'单词数':<8} {'问题数':<8} {'状态':<10}")
    print("-" * 70)
    
    for g in report["groups"]:
        status_str = {"ok": "✓ 正常", "warning": "⚠ 警告", "error": "✗ 错误"}[g["status"]]
        print(f"{g['group_code']:<15} {g['group_name']:<15} {g['level_count']:<8} {g['word_count']:<8} {len(g['issues']):<8} {status_str:<10}")
    
    print("-" * 70)
    
    # 最终结论
    if report["issues_by_severity"]["critical"] == 0:
        print("\n" + "=" * 70)
        print("结论: 所有关卡检查通过，没有严重问题 ✓")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print(f"结论: 发现 {report['issues_by_severity']['critical']} 个严重问题需要修复")
        print("=" * 70)
    
    return report


if __name__ == "__main__":
    check_all_levels()
