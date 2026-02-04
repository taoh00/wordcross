#!/usr/bin/env python3
"""
关卡生成大规模测试脚本
使用CET-4词库验证关卡生成算法的稳定性
"""

import sys
import json
import time
from collections import defaultdict
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from puzzle_generator import CrosswordGenerator, PROGRESSIVE_LEVEL_CONFIG
from vocabulary import VocabularyManager


class LevelGenerationTester:
    """关卡生成测试器"""
    
    def __init__(self, group: str = "cet4"):
        self.vocab_manager = VocabularyManager()
        self.generator = CrosswordGenerator()
        self.group = group
        
        # 统计数据
        self.stats = {
            "total_tests": 0,
            "successful": 0,
            "failed": 0,
            "failures": [],
            "word_count_distribution": defaultdict(int),
            "level_stats": defaultdict(lambda: {"success": 0, "fail": 0, "word_counts": []})
        }
    
    def get_vocab_info(self):
        """获取词汇信息"""
        words = self.vocab_manager._vocabulary_cache.get(self.group, [])
        print(f"\n{'='*60}")
        print(f"词库信息: {self.group}")
        print(f"{'='*60}")
        print(f"总词汇数: {len(words)}")
        
        # 按长度统计
        length_dist = defaultdict(int)
        for w in words:
            length_dist[len(w["word"])] += 1
        
        print("\n按单词长度分布:")
        for length in sorted(length_dist.keys()):
            print(f"  {length}字母: {length_dist[length]}个")
        
        return len(words)
    
    def test_single_level(self, level: int, verbose: bool = False) -> dict:
        """测试单个关卡生成"""
        try:
            start_time = time.time()
            puzzle = self.generator.generate_campaign_level(level, self.group, self.vocab_manager)
            elapsed = time.time() - start_time
            
            word_count = len(puzzle.get("words", []))
            grid_size = puzzle.get("grid_size", 0)
            
            # 判断成功条件
            if level in PROGRESSIVE_LEVEL_CONFIG:
                _, min_words, max_words, _, _, _ = PROGRESSIVE_LEVEL_CONFIG[level]
            else:
                config = self.generator.get_level_config(level)
                _, min_words, max_words, _ = config
            
            # 至少生成了目标数量一半的单词才算成功
            min_required = max(2, min_words)
            success = word_count >= min_required
            
            result = {
                "level": level,
                "success": success,
                "word_count": word_count,
                "grid_size": grid_size,
                "expected_min": min_words,
                "expected_max": max_words,
                "elapsed_ms": elapsed * 1000
            }
            
            if verbose:
                status = "✓" if success else "✗"
                print(f"  {status} 关卡 {level:3d}: {word_count}/{min_words}-{max_words}词, "
                      f"{grid_size}x{grid_size}网格, {elapsed*1000:.1f}ms")
            
            return result
            
        except Exception as e:
            if verbose:
                print(f"  ✗ 关卡 {level}: 异常 - {str(e)}")
            return {
                "level": level,
                "success": False,
                "error": str(e)
            }
    
    def run_batch_test(self, level_range: tuple = (1, 256), iterations: int = 3, verbose: bool = True):
        """批量测试多个关卡"""
        start_level, end_level = level_range
        total_levels = end_level - start_level + 1
        total_tests = total_levels * iterations
        
        print(f"\n{'='*60}")
        print(f"开始批量测试")
        print(f"{'='*60}")
        print(f"关卡范围: {start_level} - {end_level}")
        print(f"每关卡测试次数: {iterations}")
        print(f"总测试次数: {total_tests}")
        print(f"词库: {self.group}")
        
        start_time = time.time()
        
        for iteration in range(iterations):
            print(f"\n--- 第 {iteration + 1}/{iterations} 轮测试 ---")
            
            for level in range(start_level, end_level + 1):
                result = self.test_single_level(level, verbose=verbose)
                
                self.stats["total_tests"] += 1
                
                if result.get("success"):
                    self.stats["successful"] += 1
                    self.stats["level_stats"][level]["success"] += 1
                else:
                    self.stats["failed"] += 1
                    self.stats["level_stats"][level]["fail"] += 1
                    self.stats["failures"].append(result)
                
                if "word_count" in result:
                    self.stats["word_count_distribution"][result["word_count"]] += 1
                    self.stats["level_stats"][level]["word_counts"].append(result["word_count"])
        
        elapsed = time.time() - start_time
        
        self.print_summary(elapsed)
    
    def run_stress_test(self, level: int = 10, iterations: int = 100, verbose: bool = False):
        """压力测试单个关卡"""
        print(f"\n{'='*60}")
        print(f"关卡 {level} 压力测试 ({iterations} 次)")
        print(f"{'='*60}")
        
        start_time = time.time()
        word_counts = []
        failures = []
        
        for i in range(iterations):
            result = self.test_single_level(level, verbose=verbose)
            
            if result.get("success"):
                word_counts.append(result.get("word_count", 0))
            else:
                failures.append(result)
            
            if (i + 1) % 10 == 0:
                print(f"  进度: {i+1}/{iterations}")
        
        elapsed = time.time() - start_time
        
        print(f"\n结果统计:")
        print(f"  成功率: {len(word_counts)}/{iterations} ({len(word_counts)/iterations*100:.1f}%)")
        print(f"  失败次数: {len(failures)}")
        if word_counts:
            print(f"  平均单词数: {sum(word_counts)/len(word_counts):.2f}")
            print(f"  最少单词数: {min(word_counts)}")
            print(f"  最多单词数: {max(word_counts)}")
        print(f"  总耗时: {elapsed:.2f}秒")
        print(f"  平均每次: {elapsed/iterations*1000:.1f}ms")
        
        if failures:
            print(f"\n失败详情:")
            for f in failures[:5]:
                print(f"  - {f}")
    
    def print_summary(self, elapsed: float):
        """打印测试总结"""
        print(f"\n{'='*60}")
        print(f"测试总结")
        print(f"{'='*60}")
        
        success_rate = self.stats["successful"] / self.stats["total_tests"] * 100 if self.stats["total_tests"] > 0 else 0
        
        print(f"总测试次数: {self.stats['total_tests']}")
        print(f"成功次数: {self.stats['successful']}")
        print(f"失败次数: {self.stats['failed']}")
        print(f"成功率: {success_rate:.2f}%")
        print(f"总耗时: {elapsed:.2f}秒")
        
        print(f"\n单词数量分布:")
        for count in sorted(self.stats["word_count_distribution"].keys()):
            times = self.stats["word_count_distribution"][count]
            print(f"  {count}个词: {times}次")
        
        # 找出失败率最高的关卡
        problem_levels = []
        for level, stats in self.stats["level_stats"].items():
            total = stats["success"] + stats["fail"]
            if total > 0 and stats["fail"] > 0:
                fail_rate = stats["fail"] / total * 100
                problem_levels.append((level, fail_rate, stats["fail"], total))
        
        if problem_levels:
            problem_levels.sort(key=lambda x: x[1], reverse=True)
            print(f"\n问题关卡 (失败率 > 0%):")
            for level, fail_rate, fails, total in problem_levels[:10]:
                avg_words = sum(self.stats["level_stats"][level]["word_counts"]) / len(self.stats["level_stats"][level]["word_counts"]) if self.stats["level_stats"][level]["word_counts"] else 0
                print(f"  关卡 {level:3d}: 失败率 {fail_rate:.1f}% ({fails}/{total}), 平均词数 {avg_words:.1f}")
        
        if self.stats["failures"]:
            print(f"\n部分失败详情 (前5个):")
            for f in self.stats["failures"][:5]:
                print(f"  {f}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="关卡生成测试")
    parser.add_argument("--group", default="cet4", help="词库组别")
    parser.add_argument("--levels", default="1-50", help="关卡范围 (如 1-50)")
    parser.add_argument("--iterations", type=int, default=3, help="每关卡测试次数")
    parser.add_argument("--stress", type=int, help="压力测试指定关卡N次")
    parser.add_argument("--stress-level", type=int, default=10, help="压力测试的关卡号")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    tester = LevelGenerationTester(group=args.group)
    
    # 显示词库信息
    word_count = tester.get_vocab_info()
    
    if word_count == 0:
        print(f"\n错误: 词库 '{args.group}' 没有词汇!")
        sys.exit(1)
    
    if args.stress:
        # 压力测试
        tester.run_stress_test(level=args.stress_level, iterations=args.stress, verbose=args.verbose)
    else:
        # 批量测试
        level_parts = args.levels.split("-")
        start_level = int(level_parts[0])
        end_level = int(level_parts[1]) if len(level_parts) > 1 else start_level
        
        tester.run_batch_test(
            level_range=(start_level, end_level),
            iterations=args.iterations,
            verbose=args.verbose
        )


if __name__ == "__main__":
    main()
