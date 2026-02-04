#!/usr/bin/env python3
"""
架构可行性验证算法
===================

验证《我爱填单词》游戏架构的核心机制可行性：
1. 双引擎策略验证 - 稀疏布局 vs 密集布局
2. 词库覆盖度验证 - 各难度词库能否生成足够的谜题
3. 性能基准测试 - 响应时间是否满足预算
4. CSP算法收敛性 - 约束满足问题是否可解

作者: Cloud Dragonborn (Game Architect)
日期: 2026-01-24
"""

import sys
import json
import time
import statistics
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from puzzle_generator import CrosswordGenerator, PROGRESSIVE_LEVEL_CONFIG
from csp_puzzle_generator import CSPPuzzleGenerator, WordIndex
from vocabulary import VocabularyManager


# ==================== 数据结构定义 ====================

@dataclass
class ValidationResult:
    """验证结果"""
    test_name: str
    passed: bool
    score: float  # 0-100
    details: Dict = field(default_factory=dict)
    message: str = ""


@dataclass
class PerformanceMetrics:
    """性能指标"""
    mean_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    

# ==================== 验证器类 ====================

class ArchitectureValidator:
    """架构验证器 - 验证核心机制的可行性"""
    
    # 性能预算 (毫秒)
    PERFORMANCE_BUDGET = {
        "puzzle_generation": {"mean": 500, "p95": 1000, "p99": 2000},
        "answer_verification": {"mean": 10, "p95": 50, "p99": 100},
    }
    
    # 成功率阈值
    SUCCESS_RATE_THRESHOLD = {
        "sparse": 0.85,    # 稀疏布局至少85%成功率
        "dense": 0.70,     # 密集布局至少70%成功率
    }
    
    def __init__(self):
        self.vocab_manager = VocabularyManager()
        self.sparse_generator = CrosswordGenerator()
        self.dense_generator = CSPPuzzleGenerator()
        
        self.results: List[ValidationResult] = []
        
    def run_all_validations(self) -> Dict:
        """运行所有验证测试"""
        print("=" * 70)
        print("🏛️  架构可行性验证 - Cloud Dragonborn")
        print("=" * 70)
        print()
        
        # 1. 词库验证
        self._validate_vocabulary_coverage()
        
        # 2. 稀疏布局引擎验证
        self._validate_sparse_engine()
        
        # 3. 密集布局引擎验证
        self._validate_dense_engine()
        
        # 4. 双引擎协同验证
        self._validate_dual_engine_strategy()
        
        # 5. 性能基准测试
        self._validate_performance()
        
        # 6. CSP算法收敛性验证
        self._validate_csp_convergence()
        
        # 汇总报告
        return self._generate_report()
    
    def _validate_vocabulary_coverage(self):
        """验证词库覆盖度"""
        print("\n📚 词库覆盖度验证")
        print("-" * 50)
        
        groups = ["primary", "cet4", "cet6", "ielts", "gre"]
        grid_sizes = [5, 6, 7, 8, 10]
        
        coverage_matrix = {}
        
        for group in groups:
            coverage_matrix[group] = {}
            words = self.vocab_manager.get_words(group, limit=10000)
            
            if not words:
                print(f"  ⚠️  {group}: 词库为空或不存在")
                continue
            
            total = len(words)
            print(f"\n  📖 {group}: 总词汇 {total}")
            
            # 按长度统计
            length_dist = defaultdict(int)
            for w in words:
                length_dist[len(w["word"])] += 1
            
            for size in grid_sizes:
                count = length_dist.get(size, 0)
                coverage_matrix[group][size] = count
                status = "✓" if count >= 20 else "⚠️" if count >= 10 else "✗"
                print(f"      {size}字母: {count:4d}个 {status}")
        
        # 计算得分
        score = 0
        checks = 0
        for group in groups:
            if group in coverage_matrix:
                for size in grid_sizes:
                    checks += 1
                    count = coverage_matrix.get(group, {}).get(size, 0)
                    if count >= 20:
                        score += 1
                    elif count >= 10:
                        score += 0.5
        
        final_score = (score / checks * 100) if checks > 0 else 0
        passed = final_score >= 60
        
        self.results.append(ValidationResult(
            test_name="词库覆盖度",
            passed=passed,
            score=final_score,
            details={"coverage_matrix": coverage_matrix},
            message=f"各词库在目标长度上的覆盖情况"
        ))
        
        print(f"\n  得分: {final_score:.1f}/100 {'✓ PASS' if passed else '✗ FAIL'}")
    
    def _validate_sparse_engine(self):
        """验证稀疏布局引擎"""
        print("\n\n🔧 稀疏布局引擎验证 (CrosswordGenerator)")
        print("-" * 50)
        
        test_cases = [
            {"level": 1, "group": "primary", "expected_words": 2},
            {"level": 5, "group": "cet4", "expected_words": 3},
            {"level": 10, "group": "cet4", "expected_words": 4},
            {"level": 50, "group": "cet6", "expected_words": 4},
        ]
        
        successes = 0
        total = 0
        
        for case in test_cases:
            level = case["level"]
            group = case["group"]
            expected = case["expected_words"]
            
            # 多次尝试
            case_success = 0
            attempts = 5
            
            for _ in range(attempts):
                total += 1
                try:
                    puzzle = self.sparse_generator.generate_campaign_level(
                        level, group, self.vocab_manager
                    )
                    word_count = len(puzzle.get("words", []))
                    if word_count >= expected:
                        successes += 1
                        case_success += 1
                except Exception as e:
                    pass
            
            rate = case_success / attempts * 100
            status = "✓" if rate >= 80 else "⚠️" if rate >= 50 else "✗"
            print(f"  {status} Level {level:3d}, {group:8s}: {rate:.0f}% 成功率")
        
        success_rate = successes / total if total > 0 else 0
        passed = success_rate >= self.SUCCESS_RATE_THRESHOLD["sparse"]
        score = success_rate * 100
        
        self.results.append(ValidationResult(
            test_name="稀疏布局引擎",
            passed=passed,
            score=score,
            details={"success_rate": success_rate, "total_tests": total},
            message=f"成功率 {success_rate*100:.1f}%, 阈值 {self.SUCCESS_RATE_THRESHOLD['sparse']*100}%"
        ))
        
        print(f"\n  总成功率: {success_rate*100:.1f}% {'✓ PASS' if passed else '✗ FAIL'}")
    
    def _validate_dense_engine(self):
        """验证密集布局引擎 (CSP)"""
        print("\n\n🔧 密集布局引擎验证 (CSPPuzzleGenerator)")
        print("-" * 50)
        
        test_configs = [
            {"grid_size": 6, "group": "cet4", "name": "6x6 Easy"},
            {"grid_size": 7, "group": "cet4", "name": "7x7 Medium"},
            {"grid_size": 8, "group": "cet6", "name": "8x8 Hard"},
        ]
        
        successes = 0
        total = 0
        
        for config in test_configs:
            grid_size = config["grid_size"]
            group = config["group"]
            name = config["name"]
            
            # 获取词库
            words = self.vocab_manager.get_words(group, limit=5000)
            
            case_success = 0
            attempts = 5
            
            for _ in range(attempts):
                total += 1
                try:
                    puzzle = self.dense_generator.generate_template_puzzle(
                        grid_size, words, timeout=3.0, max_retries=5
                    )
                    # 成功条件：生成了谜题且至少有2个词（简化模板可能只有3个词）
                    if puzzle and len(puzzle.row_words) + len(puzzle.col_words) >= 2:
                        successes += 1
                        case_success += 1
                except Exception as e:
                    pass
            
            rate = case_success / attempts * 100
            status = "✓" if rate >= 60 else "⚠️" if rate >= 40 else "✗"
            print(f"  {status} {name:12s}: {rate:.0f}% 成功率")
        
        success_rate = successes / total if total > 0 else 0
        passed = success_rate >= self.SUCCESS_RATE_THRESHOLD["dense"]
        score = success_rate * 100
        
        self.results.append(ValidationResult(
            test_name="密集布局引擎",
            passed=passed,
            score=score,
            details={"success_rate": success_rate},
            message=f"成功率 {success_rate*100:.1f}%, 阈值 {self.SUCCESS_RATE_THRESHOLD['dense']*100}%"
        ))
        
        print(f"\n  总成功率: {success_rate*100:.1f}% {'✓ PASS' if passed else '✗ FAIL'}")
    
    def _validate_dual_engine_strategy(self):
        """验证双引擎协同策略"""
        print("\n\n🔧 双引擎协同策略验证")
        print("-" * 50)
        
        # 模拟关卡1-50的生成
        level_results = []
        
        for level in range(1, 51, 5):  # 采样测试
            group = "cet4"
            
            # 根据关卡选择引擎
            if level <= 30:
                engine = "sparse"
                try:
                    puzzle = self.sparse_generator.generate_campaign_level(
                        level, group, self.vocab_manager
                    )
                    success = len(puzzle.get("words", [])) >= 2
                except:
                    success = False
            else:
                engine = "dense"
                words = self.vocab_manager.get_words(group, limit=5000)
                grid_size = 6 if level <= 40 else 7
                try:
                    puzzle = self.dense_generator.generate_template_puzzle(
                        grid_size, words, timeout=2.0, max_retries=3
                    )
                    success = puzzle is not None
                except:
                    success = False
            
            level_results.append({
                "level": level,
                "engine": engine,
                "success": success
            })
            
            status = "✓" if success else "✗"
            print(f"  {status} Level {level:3d} → {engine:6s} engine")
        
        success_count = sum(1 for r in level_results if r["success"])
        success_rate = success_count / len(level_results)
        passed = success_rate >= 0.8
        score = success_rate * 100
        
        self.results.append(ValidationResult(
            test_name="双引擎协同",
            passed=passed,
            score=score,
            details={"level_results": level_results},
            message=f"关卡覆盖率 {success_rate*100:.1f}%"
        ))
        
        print(f"\n  覆盖率: {success_rate*100:.1f}% {'✓ PASS' if passed else '✗ FAIL'}")
    
    def _validate_performance(self):
        """验证性能是否满足预算"""
        print("\n\n⏱️  性能基准测试")
        print("-" * 50)
        
        # 测试谜题生成性能
        print("\n  🧩 谜题生成性能:")
        gen_times = []
        
        for _ in range(20):
            start = time.time()
            try:
                puzzle = self.sparse_generator.generate_campaign_level(
                    5, "cet4", self.vocab_manager
                )
                elapsed = (time.time() - start) * 1000
                gen_times.append(elapsed)
            except:
                pass
        
        if gen_times:
            metrics = self._calculate_metrics(gen_times)
            budget = self.PERFORMANCE_BUDGET["puzzle_generation"]
            
            print(f"      Mean:  {metrics.mean_ms:6.1f}ms (预算: {budget['mean']}ms)")
            print(f"      P50:   {metrics.p50_ms:6.1f}ms")
            print(f"      P95:   {metrics.p95_ms:6.1f}ms (预算: {budget['p95']}ms)")
            print(f"      P99:   {metrics.p99_ms:6.1f}ms (预算: {budget['p99']}ms)")
            
            gen_passed = metrics.p95_ms <= budget["p95"]
        else:
            gen_passed = False
            metrics = None
        
        # 测试答案验证性能
        print("\n  ✓ 答案验证性能:")
        verify_times = []
        
        # 先生成一个谜题获取word_id
        puzzle = self.sparse_generator.generate_campaign_level(1, "cet4", self.vocab_manager)
        if puzzle and puzzle.get("words"):
            word = puzzle["words"][0]
            word_id = word["id"]
            correct_answer = word["word"]
            
            for _ in range(100):
                start = time.time()
                result = self.sparse_generator.verify_answer(word_id, correct_answer)
                elapsed = (time.time() - start) * 1000
                verify_times.append(elapsed)
        
        if verify_times:
            v_metrics = self._calculate_metrics(verify_times)
            v_budget = self.PERFORMANCE_BUDGET["answer_verification"]
            
            print(f"      Mean:  {v_metrics.mean_ms:6.3f}ms (预算: {v_budget['mean']}ms)")
            print(f"      P95:   {v_metrics.p95_ms:6.3f}ms (预算: {v_budget['p95']}ms)")
            
            verify_passed = v_metrics.p95_ms <= v_budget["p95"]
        else:
            verify_passed = False
            v_metrics = None
        
        overall_passed = gen_passed and verify_passed
        score = (50 if gen_passed else 0) + (50 if verify_passed else 0)
        
        self.results.append(ValidationResult(
            test_name="性能基准",
            passed=overall_passed,
            score=score,
            details={
                "generation": metrics.__dict__ if metrics else {},
                "verification": v_metrics.__dict__ if v_metrics else {}
            },
            message=f"生成P95: {metrics.p95_ms:.1f}ms" if metrics else "测试失败"
        ))
        
        print(f"\n  结果: {'✓ PASS' if overall_passed else '✗ FAIL'}")
    
    def _validate_csp_convergence(self):
        """验证CSP算法收敛性"""
        print("\n\n🧮 CSP算法收敛性验证")
        print("-" * 50)
        
        # 测试不同规模的CSP问题
        test_sizes = [6, 7, 8]
        convergence_results = []
        
        words = self.vocab_manager.get_words("cet4", limit=5000)
        
        for size in test_sizes:
            successes = 0
            total_time = 0
            attempts = 10
            backtracks_sum = 0
            
            for _ in range(attempts):
                start = time.time()
                try:
                    puzzle = self.dense_generator.generate_template_puzzle(
                        size, words, timeout=3.0, max_retries=3
                    )
                    if puzzle:
                        successes += 1
                except:
                    pass
                total_time += time.time() - start
            
            avg_time = total_time / attempts * 1000
            rate = successes / attempts * 100
            
            convergence_results.append({
                "size": size,
                "success_rate": rate,
                "avg_time_ms": avg_time
            })
            
            status = "✓" if rate >= 60 else "⚠️" if rate >= 40 else "✗"
            print(f"  {status} {size}x{size}: 成功率 {rate:.0f}%, 平均耗时 {avg_time:.0f}ms")
        
        # 计算综合得分
        avg_rate = sum(r["success_rate"] for r in convergence_results) / len(convergence_results)
        passed = avg_rate >= 50
        score = avg_rate
        
        self.results.append(ValidationResult(
            test_name="CSP收敛性",
            passed=passed,
            score=score,
            details={"convergence_results": convergence_results},
            message=f"平均收敛率 {avg_rate:.1f}%"
        ))
        
        print(f"\n  平均收敛率: {avg_rate:.1f}% {'✓ PASS' if passed else '✗ FAIL'}")
    
    def _calculate_metrics(self, times: List[float]) -> PerformanceMetrics:
        """计算性能指标"""
        sorted_times = sorted(times)
        n = len(sorted_times)
        
        return PerformanceMetrics(
            mean_ms=statistics.mean(sorted_times),
            p50_ms=sorted_times[int(n * 0.5)],
            p95_ms=sorted_times[int(n * 0.95)] if n >= 20 else sorted_times[-1],
            p99_ms=sorted_times[int(n * 0.99)] if n >= 100 else sorted_times[-1],
            min_ms=sorted_times[0],
            max_ms=sorted_times[-1]
        )
    
    def _generate_report(self) -> Dict:
        """生成验证报告"""
        print("\n")
        print("=" * 70)
        print("📊 架构可行性验证报告")
        print("=" * 70)
        
        total_score = 0
        passed_count = 0
        
        print("\n测试结果汇总:")
        print("-" * 50)
        
        for result in self.results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"  {result.test_name:20s}: {result.score:5.1f}/100  {status}")
            total_score += result.score
            if result.passed:
                passed_count += 1
        
        avg_score = total_score / len(self.results) if self.results else 0
        all_passed = passed_count == len(self.results)
        
        print("-" * 50)
        print(f"  {'总体评分':20s}: {avg_score:5.1f}/100")
        print(f"  {'通过测试':20s}: {passed_count}/{len(self.results)}")
        
        print("\n" + "=" * 70)
        if all_passed:
            print("🎉 结论: 架构设计可行! 所有核心机制验证通过。")
        elif avg_score >= 70:
            print("⚠️  结论: 架构基本可行，部分机制需要优化。")
        else:
            print("❌ 结论: 架构存在风险，需要重新评估关键组件。")
        print("=" * 70)
        
        # 建议
        print("\n💡 优化建议:")
        for result in self.results:
            if not result.passed:
                print(f"  - {result.test_name}: {result.message}")
        
        return {
            "overall_score": avg_score,
            "all_passed": all_passed,
            "passed_count": passed_count,
            "total_tests": len(self.results),
            "results": [
                {
                    "name": r.test_name,
                    "passed": r.passed,
                    "score": r.score,
                    "message": r.message
                }
                for r in self.results
            ]
        }


# ==================== 主函数 ====================

def main():
    """运行架构验证"""
    validator = ArchitectureValidator()
    report = validator.run_all_validations()
    
    # 保存报告
    report_path = Path(__file__).parent.parent.parent / "_bmad-output" / "architecture-validation-report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 报告已保存: {report_path}")
    
    # 返回退出码
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    exit(main())
