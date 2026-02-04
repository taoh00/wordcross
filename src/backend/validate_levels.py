#!/usr/bin/env python3
"""
关卡验证脚本

模拟前端加载关卡并解答，生成验证报告。

功能：
1. 加载每个关卡的JSON文件（模拟前端fetch）
2. 验证关卡数据格式是否正确
3. 模拟解答关卡（验证关卡是否可解）
4. 生成详细的验证报告

使用方法：
    python validate_levels.py --all          # 验证所有词库
    python validate_levels.py -g grade3_1    # 验证指定词库
    python validate_levels.py -g gre --limit 10  # 只验证前10关
    python validate_levels.py --report       # 生成HTML报告
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ValidationStatus(Enum):
    """验证状态"""
    SUCCESS = "success"      # 验证通过
    LOAD_FAILED = "load_failed"  # 加载失败
    FORMAT_ERROR = "format_error"  # 格式错误
    SOLVE_FAILED = "solve_failed"  # 无法解答
    PARTIAL = "partial"      # 部分通过


@dataclass
class LevelValidation:
    """单个关卡的验证结果"""
    group: str
    level: int
    status: ValidationStatus
    load_time_ms: float = 0
    solve_time_ms: float = 0
    grid_size: int = 0
    word_count: int = 0
    words: List[str] = field(default_factory=list)
    prefilled_count: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    solved_words: List[str] = field(default_factory=list)
    unsolved_words: List[str] = field(default_factory=list)


@dataclass  
class GroupValidation:
    """词库验证结果"""
    group_code: str
    group_name: str
    total_levels: int
    validated_levels: int
    success_count: int
    failed_count: int
    error_details: List[LevelValidation] = field(default_factory=list)
    all_results: List[LevelValidation] = field(default_factory=list)
    total_load_time_ms: float = 0
    total_solve_time_ms: float = 0


class LevelValidator:
    """关卡验证器"""
    
    def __init__(self, levels_dir: Path = None):
        """初始化验证器
        
        Args:
            levels_dir: 关卡数据目录，默认为 src/data/levels
        """
        if levels_dir is None:
            levels_dir = Path(__file__).parent.parent / "data" / "levels"
        self.levels_dir = levels_dir
        self.reports_dir = Path(__file__).parent.parent / "data" / "validation_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def load_level(self, group: str, level: int) -> Tuple[Optional[dict], float, Optional[str]]:
        """加载关卡数据（模拟前端fetch）
        
        Returns:
            (data, load_time_ms, error_message)
        """
        level_path = self.levels_dir / group / f"{level}.json"
        
        start = time.time()
        try:
            if not level_path.exists():
                return None, 0, f"文件不存在: {level_path}"
            
            with open(level_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            load_time = (time.time() - start) * 1000
            return data, load_time, None
            
        except json.JSONDecodeError as e:
            return None, 0, f"JSON解析错误: {e}"
        except Exception as e:
            return None, 0, f"加载错误: {e}"
    
    def validate_format(self, data: dict) -> List[str]:
        """验证关卡数据格式
        
        Returns:
            错误列表
        """
        errors = []
        
        # 必需字段
        required_fields = ["grid_size", "cells", "words"]
        for field in required_fields:
            if field not in data:
                errors.append(f"缺少必需字段: {field}")
        
        if errors:
            return errors
        
        # 验证grid_size
        grid_size = data.get("grid_size", 0)
        if not isinstance(grid_size, int) or grid_size < 4 or grid_size > 15:
            errors.append(f"grid_size无效: {grid_size}")
        
        # 验证cells
        cells = data.get("cells", [])
        if not isinstance(cells, list) or len(cells) != grid_size:
            errors.append(f"cells行数错误: 期望{grid_size}, 实际{len(cells) if isinstance(cells, list) else 'N/A'}")
        else:
            for row_idx, row in enumerate(cells):
                if not isinstance(row, list) or len(row) != grid_size:
                    errors.append(f"cells第{row_idx}行列数错误")
        
        # 验证words
        words = data.get("words", [])
        if not isinstance(words, list) or len(words) < 2:
            errors.append(f"words数量不足: {len(words) if isinstance(words, list) else 'N/A'}")
        else:
            for idx, word in enumerate(words):
                if not isinstance(word, dict):
                    errors.append(f"第{idx}个单词格式错误")
                    continue
                
                # 验证单词必需字段
                word_required = ["word", "direction", "start_row", "start_col"]
                for field in word_required:
                    if field not in word:
                        errors.append(f"单词{idx}缺少字段: {field}")
                
                # 验证单词只包含字母
                word_text = word.get("word", "")
                if word_text and not word_text.isalpha():
                    errors.append(f"单词包含非字母字符: {word_text}")
                
                # 验证方向
                direction = word.get("direction", "")
                if direction not in ["across", "down"]:
                    errors.append(f"单词{idx}方向无效: {direction}")
        
        return errors
    
    def solve_level(self, data: dict) -> Tuple[List[str], List[str], float]:
        """模拟解答关卡
        
        检查每个单词是否可以正确填入网格（不产生冲突）
        
        Returns:
            (solved_words, unsolved_words, solve_time_ms)
        """
        start = time.time()
        
        grid_size = data.get("grid_size", 0)
        cells = data.get("cells", [])
        words = data.get("words", [])
        prefilled = data.get("prefilled", {})
        
        # 创建模拟网格
        grid = [[None for _ in range(grid_size)] for _ in range(grid_size)]
        
        # 填入预填字母
        for key, letter in prefilled.items():
            try:
                row, col = map(int, key.split("-"))
                grid[row][col] = letter.upper()
            except:
                pass
        
        solved = []
        unsolved = []
        
        for word_info in words:
            word = word_info.get("word", "").upper()
            direction = word_info.get("direction", "across")
            start_row = word_info.get("start_row", 0)
            start_col = word_info.get("start_col", 0)
            length = len(word)
            
            can_solve = True
            conflicts = []
            
            # 检查每个位置
            for i in range(length):
                if direction == "across":
                    r, c = start_row, start_col + i
                else:
                    r, c = start_row + i, start_col
                
                # 边界检查
                if r < 0 or r >= grid_size or c < 0 or c >= grid_size:
                    can_solve = False
                    conflicts.append(f"位置({r},{c})超出边界")
                    break
                
                # 检查单元格是否可用
                cell_value = cells[r][c] if r < len(cells) and c < len(cells[r]) else None
                if cell_value is None:
                    can_solve = False
                    conflicts.append(f"位置({r},{c})不可用")
                    break
                
                # 检查是否与现有字母冲突
                expected_letter = word[i]
                existing = grid[r][c]
                if existing is not None and existing != expected_letter:
                    can_solve = False
                    conflicts.append(f"位置({r},{c})冲突: 期望{expected_letter}, 现有{existing}")
            
            if can_solve:
                # 填入单词
                for i in range(length):
                    if direction == "across":
                        r, c = start_row, start_col + i
                    else:
                        r, c = start_row + i, start_col
                    grid[r][c] = word[i]
                solved.append(word)
            else:
                unsolved.append(f"{word}: {', '.join(conflicts)}")
        
        solve_time = (time.time() - start) * 1000
        return solved, unsolved, solve_time
    
    def validate_level(self, group: str, level: int) -> LevelValidation:
        """验证单个关卡"""
        result = LevelValidation(group=group, level=level, status=ValidationStatus.SUCCESS)
        
        # 1. 加载关卡
        data, load_time, error = self.load_level(group, level)
        result.load_time_ms = load_time
        
        if error:
            result.status = ValidationStatus.LOAD_FAILED
            result.errors.append(error)
            return result
        
        # 2. 验证格式
        format_errors = self.validate_format(data)
        if format_errors:
            result.status = ValidationStatus.FORMAT_ERROR
            result.errors.extend(format_errors)
            return result
        
        # 3. 提取基本信息
        result.grid_size = data.get("grid_size", 0)
        result.word_count = len(data.get("words", []))
        result.words = [w.get("word", "") for w in data.get("words", [])]
        result.prefilled_count = len(data.get("prefilled", {}))
        
        # 4. 模拟解答
        solved, unsolved, solve_time = self.solve_level(data)
        result.solve_time_ms = solve_time
        result.solved_words = solved
        result.unsolved_words = unsolved
        
        if unsolved:
            result.status = ValidationStatus.SOLVE_FAILED
            result.errors.extend([f"无法解答: {u}" for u in unsolved])
        
        return result
    
    def validate_group(self, group_code: str, limit: int = None, verbose: bool = True) -> GroupValidation:
        """验证整个词库"""
        # 读取meta信息
        meta_path = self.levels_dir / group_code / "meta.json"
        if not meta_path.exists():
            print(f"错误: 词库 {group_code} 不存在")
            return GroupValidation(
                group_code=group_code,
                group_name="未知",
                total_levels=0,
                validated_levels=0,
                success_count=0,
                failed_count=0
            )
        
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        
        group_name = meta.get("name", group_code)
        total_levels = meta.get("level_count", 0)
        
        if verbose:
            print(f"\n验证词库: {group_name} ({group_code})")
            print(f"总关卡数: {total_levels}")
            print("-" * 50)
        
        result = GroupValidation(
            group_code=group_code,
            group_name=group_name,
            total_levels=total_levels,
            validated_levels=0,
            success_count=0,
            failed_count=0
        )
        
        # 确定验证范围
        max_level = min(total_levels, limit) if limit else total_levels
        
        for level in range(1, max_level + 1):
            level_result = self.validate_level(group_code, level)
            result.validated_levels += 1
            result.total_load_time_ms += level_result.load_time_ms
            result.total_solve_time_ms += level_result.solve_time_ms
            result.all_results.append(level_result)
            
            if level_result.status == ValidationStatus.SUCCESS:
                result.success_count += 1
                if verbose and level % 100 == 0:
                    print(f"  已验证 {level}/{max_level} 关...")
            else:
                result.failed_count += 1
                result.error_details.append(level_result)
                if verbose:
                    print(f"  ✗ 关卡 {level}: {level_result.status.value} - {', '.join(level_result.errors[:2])}")
        
        if verbose:
            print(f"\n验证完成: {result.success_count}/{result.validated_levels} 通过")
            if result.failed_count > 0:
                print(f"失败关卡: {result.failed_count}")
            print(f"总加载时间: {result.total_load_time_ms:.1f}ms")
            print(f"总解答时间: {result.total_solve_time_ms:.1f}ms")
            print(f"平均每关: {(result.total_load_time_ms + result.total_solve_time_ms) / max(result.validated_levels, 1):.2f}ms")
        
        return result
    
    def validate_all(self, limit: int = None, verbose: bool = True) -> Dict[str, GroupValidation]:
        """验证所有词库"""
        results = {}
        
        # 获取所有词库目录
        group_dirs = [d for d in self.levels_dir.iterdir() if d.is_dir() and (d / "meta.json").exists()]
        
        if verbose:
            print("=" * 60)
            print("开始验证所有词库")
            print(f"共 {len(group_dirs)} 个词库")
            print("=" * 60)
        
        for group_dir in sorted(group_dirs):
            group_code = group_dir.name
            result = self.validate_group(group_code, limit=limit, verbose=verbose)
            results[group_code] = result
        
        return results
    
    def generate_report(self, results: Dict[str, GroupValidation], output_format: str = "json") -> Path:
        """生成验证报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_format == "json":
            report_path = self.reports_dir / f"validation_report_{timestamp}.json"
            
            report_data = {
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_groups": len(results),
                    "total_levels": sum(r.total_levels for r in results.values()),
                    "validated_levels": sum(r.validated_levels for r in results.values()),
                    "success_count": sum(r.success_count for r in results.values()),
                    "failed_count": sum(r.failed_count for r in results.values()),
                    "total_load_time_ms": sum(r.total_load_time_ms for r in results.values()),
                    "total_solve_time_ms": sum(r.total_solve_time_ms for r in results.values()),
                },
                "groups": []
            }
            
            for group_code, result in results.items():
                group_data = {
                    "group_code": group_code,
                    "group_name": result.group_name,
                    "total_levels": result.total_levels,
                    "validated_levels": result.validated_levels,
                    "success_count": result.success_count,
                    "failed_count": result.failed_count,
                    "success_rate": f"{result.success_count / max(result.validated_levels, 1) * 100:.1f}%",
                    "avg_load_time_ms": result.total_load_time_ms / max(result.validated_levels, 1),
                    "avg_solve_time_ms": result.total_solve_time_ms / max(result.validated_levels, 1),
                    "error_levels": [
                        {
                            "level": e.level,
                            "status": e.status.value,
                            "errors": e.errors,
                            "words": e.words
                        }
                        for e in result.error_details
                    ]
                }
                report_data["groups"].append(group_data)
            
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        elif output_format == "html":
            report_path = self.reports_dir / f"validation_report_{timestamp}.html"
            html_content = self._generate_html_report(results)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(html_content)
        
        elif output_format == "csv":
            report_path = self.reports_dir / f"validation_report_{timestamp}.csv"
            csv_content = self._generate_csv_report(results)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(csv_content)
        
        else:
            # 纯文本格式
            report_path = self.reports_dir / f"validation_report_{timestamp}.txt"
            text_content = self._generate_text_report(results)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(text_content)
        
        print(f"\n报告已保存: {report_path}")
        return report_path
    
    def _generate_html_report(self, results: Dict[str, GroupValidation]) -> str:
        """生成HTML格式报告"""
        total_levels = sum(r.validated_levels for r in results.values())
        total_success = sum(r.success_count for r in results.values())
        total_failed = sum(r.failed_count for r in results.values())
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>关卡验证报告</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #333; }}
        .summary {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .summary h2 {{ margin-top: 0; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }}
        .stat-card {{ background: #e3f2fd; padding: 15px; border-radius: 6px; text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #1976d2; }}
        .stat-label {{ color: #666; font-size: 14px; }}
        .group-table {{ width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .group-table th, .group-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        .group-table th {{ background: #1976d2; color: white; }}
        .group-table tr:hover {{ background: #f5f5f5; }}
        .success {{ color: #4caf50; }}
        .failed {{ color: #f44336; }}
        .error-details {{ background: #fff3e0; padding: 10px; border-radius: 4px; margin-top: 10px; font-size: 12px; }}
        .progress-bar {{ background: #e0e0e0; border-radius: 10px; height: 20px; overflow: hidden; }}
        .progress-fill {{ background: #4caf50; height: 100%; transition: width 0.3s; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 关卡验证报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <h2>📊 总体统计</h2>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{len(results)}</div>
                    <div class="stat-label">词库数量</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_levels}</div>
                    <div class="stat-label">验证关卡</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value success">{total_success}</div>
                    <div class="stat-label">通过</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value failed">{total_failed}</div>
                    <div class="stat-label">失败</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_success / max(total_levels, 1) * 100:.1f}%</div>
                    <div class="stat-label">通过率</div>
                </div>
            </div>
        </div>
        
        <h2>📚 词库详情</h2>
        <table class="group-table">
            <thead>
                <tr>
                    <th>词库</th>
                    <th>关卡数</th>
                    <th>通过</th>
                    <th>失败</th>
                    <th>通过率</th>
                    <th>平均加载(ms)</th>
                </tr>
            </thead>
            <tbody>"""
        
        for group_code, result in sorted(results.items(), key=lambda x: x[1].failed_count, reverse=True):
            success_rate = result.success_count / max(result.validated_levels, 1) * 100
            avg_load = result.total_load_time_ms / max(result.validated_levels, 1)
            
            html += f"""
                <tr>
                    <td><strong>{result.group_name}</strong> ({group_code})</td>
                    <td>{result.validated_levels}</td>
                    <td class="success">{result.success_count}</td>
                    <td class="failed">{result.failed_count}</td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {success_rate}%"></div>
                        </div>
                        {success_rate:.1f}%
                    </td>
                    <td>{avg_load:.2f}</td>
                </tr>"""
            
            if result.error_details:
                html += f"""
                <tr>
                    <td colspan="6">
                        <div class="error-details">
                            <strong>错误关卡:</strong>
                            {', '.join([f'第{e.level}关({e.status.value})' for e in result.error_details[:10]])}
                            {f'... 共{len(result.error_details)}个' if len(result.error_details) > 10 else ''}
                        </div>
                    </td>
                </tr>"""
        
        html += """
            </tbody>
        </table>
    </div>
</body>
</html>"""
        return html
    
    def _generate_text_report(self, results: Dict[str, GroupValidation]) -> str:
        """生成纯文本报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("关卡验证报告")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        
        total_levels = sum(r.validated_levels for r in results.values())
        total_success = sum(r.success_count for r in results.values())
        total_failed = sum(r.failed_count for r in results.values())
        
        lines.append(f"\n总体统计:")
        lines.append(f"  词库数量: {len(results)}")
        lines.append(f"  验证关卡: {total_levels}")
        lines.append(f"  通过: {total_success}")
        lines.append(f"  失败: {total_failed}")
        lines.append(f"  通过率: {total_success / max(total_levels, 1) * 100:.1f}%")
        
        lines.append("\n" + "-" * 60)
        lines.append("各词库详情:")
        lines.append("-" * 60)
        
        for group_code, result in sorted(results.items()):
            success_rate = result.success_count / max(result.validated_levels, 1) * 100
            status = "✓" if result.failed_count == 0 else "✗"
            lines.append(f"\n{status} {result.group_name} ({group_code})")
            lines.append(f"  关卡: {result.validated_levels}, 通过: {result.success_count}, 失败: {result.failed_count} ({success_rate:.1f}%)")
            
            if result.error_details:
                lines.append(f"  错误关卡:")
                for e in result.error_details[:5]:
                    lines.append(f"    - 第{e.level}关: {e.status.value} - {', '.join(e.errors[:2])}")
                if len(result.error_details) > 5:
                    lines.append(f"    ... 共{len(result.error_details)}个错误关卡")
        
        return "\n".join(lines)
    
    def _generate_csv_report(self, results: Dict[str, GroupValidation]) -> str:
        """生成CSV格式报告"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入标题行
        writer.writerow([
            '词库代码', '词库名称', 'meta关卡数', '实际文件数', '一致性', 
            '验证关卡', '通过数', '失败数', '通过率', 
            '平均加载(ms)', '平均解答(ms)', '错误关卡'
        ])
        
        for group_code, result in sorted(results.items()):
            success_rate = result.success_count / max(result.validated_levels, 1) * 100
            avg_load = result.total_load_time_ms / max(result.validated_levels, 1)
            avg_solve = result.total_solve_time_ms / max(result.validated_levels, 1)
            
            # 统计实际文件数
            actual_file_count = result.validated_levels
            consistency = "✓" if result.total_levels == actual_file_count else f"✗ (差异:{result.total_levels - actual_file_count})"
            
            # 错误关卡列表
            error_levels = ', '.join([str(e.level) for e in result.error_details[:10]])
            if len(result.error_details) > 10:
                error_levels += f'...共{len(result.error_details)}个'
            
            writer.writerow([
                group_code,
                result.group_name,
                result.total_levels,
                actual_file_count,
                consistency,
                result.validated_levels,
                result.success_count,
                result.failed_count,
                f"{success_rate:.1f}%",
                f"{avg_load:.2f}",
                f"{avg_solve:.2f}",
                error_levels or '-'
            ])
        
        # 添加汇总行
        total_levels = sum(r.validated_levels for r in results.values())
        total_success = sum(r.success_count for r in results.values())
        total_failed = sum(r.failed_count for r in results.values())
        total_meta = sum(r.total_levels for r in results.values())
        total_load = sum(r.total_load_time_ms for r in results.values())
        total_solve = sum(r.total_solve_time_ms for r in results.values())
        
        writer.writerow([])
        writer.writerow([
            '汇总', '-', total_meta, total_levels, 
            "✓" if total_meta == total_levels else "✗",
            total_levels, total_success, total_failed,
            f"{total_success / max(total_levels, 1) * 100:.1f}%",
            f"{total_load / max(total_levels, 1):.2f}",
            f"{total_solve / max(total_levels, 1):.2f}",
            '-'
        ])
        
        return output.getvalue()
    
    def check_file_consistency(self, group_code: str) -> Tuple[int, int, bool]:
        """检查关卡文件数量与meta.json的一致性
        
        Returns:
            (meta_count, actual_count, is_consistent)
        """
        meta_path = self.levels_dir / group_code / "meta.json"
        if not meta_path.exists():
            return 0, 0, False
        
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        
        meta_count = meta.get("level_count", 0)
        
        # 统计实际关卡文件数量
        group_dir = self.levels_dir / group_code
        actual_count = len([f for f in group_dir.iterdir() if f.suffix == '.json' and f.name != 'meta.json'])
        
        return meta_count, actual_count, meta_count == actual_count


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='关卡验证工具')
    parser.add_argument('--group', '-g', type=str, action='append', help='指定验证的词库（可多次使用）')
    parser.add_argument('--all', '-a', action='store_true', help='验证所有词库')
    parser.add_argument('--limit', '-l', type=int, help='每个词库只验证前N关')
    parser.add_argument('--report', '-r', choices=['json', 'html', 'text', 'csv'], default='json', help='报告格式')
    parser.add_argument('--quiet', '-q', action='store_true', help='安静模式，只输出结果')
    
    args = parser.parse_args()
    
    validator = LevelValidator()
    
    if args.all:
        results = validator.validate_all(limit=args.limit, verbose=not args.quiet)
    elif args.group:
        results = {}
        for group in args.group:
            result = validator.validate_group(group, limit=args.limit, verbose=not args.quiet)
            results[group] = result
    else:
        # 默认验证所有
        results = validator.validate_all(limit=args.limit, verbose=not args.quiet)
    
    # 生成报告
    if results:
        report_path = validator.generate_report(results, output_format=args.report)
        
        # 打印简要统计
        print("\n" + "=" * 60)
        print("验证完成统计")
        print("=" * 60)
        
        total_levels = sum(r.validated_levels for r in results.values())
        total_success = sum(r.success_count for r in results.values())
        total_failed = sum(r.failed_count for r in results.values())
        
        print(f"总词库: {len(results)}")
        print(f"总关卡: {total_levels}")
        print(f"通过: {total_success}")
        print(f"失败: {total_failed}")
        print(f"通过率: {total_success / max(total_levels, 1) * 100:.1f}%")
        
        if total_failed > 0:
            print(f"\n失败关卡详情请查看报告: {report_path}")


if __name__ == "__main__":
    main()
