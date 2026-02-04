#!/usr/bin/env python3
"""
填单词游戏 - API自动化测试脚本
测试HTTP接口功能

使用方法:
    python tests/test_api.py --base-url http://localhost:10010
    python tests/test_api.py --base-url http://superhe.art:10010
"""

import requests
import json
import time
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import uuid

# 测试配置
DEFAULT_BASE_URL = "http://localhost:10010"
TIMEOUT = 10

class TestResult:
    """测试结果"""
    def __init__(self, test_id: str, name: str, passed: bool, message: str = "", duration_ms: float = 0):
        self.test_id = test_id
        self.name = name
        self.passed = passed
        self.message = message
        self.duration_ms = duration_ms

class APITester:
    """API测试器"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.user_id: Optional[str] = None
        self.results: List[TestResult] = []
        
    def _api_url(self, path: str) -> str:
        """构建API URL"""
        return f"{self.base_url}/api{path}"
    
    def _static_url(self, path: str) -> str:
        """构建静态资源URL"""
        return f"{self.base_url}{path}"
    
    def _run_test(self, test_id: str, name: str, test_func) -> TestResult:
        """运行单个测试"""
        start_time = time.time()
        try:
            test_func()
            duration = (time.time() - start_time) * 1000
            result = TestResult(test_id, name, True, "PASS", duration)
        except AssertionError as e:
            duration = (time.time() - start_time) * 1000
            result = TestResult(test_id, name, False, f"FAIL: {str(e)}", duration)
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            result = TestResult(test_id, name, False, f"ERROR: {str(e)}", duration)
        
        self.results.append(result)
        status = "✅" if result.passed else "❌"
        print(f"  {status} [{test_id}] {name} ({result.duration_ms:.0f}ms)")
        if not result.passed:
            print(f"      {result.message}")
        return result
    
    # ==================== 用户模块测试 ====================
    
    def test_user_info_unregistered(self):
        """A005: 测试未注册用户获取信息"""
        def test():
            resp = self.session.get(self._api_url("/user/info"), timeout=TIMEOUT)
            assert resp.status_code == 200, f"状态码错误: {resp.status_code}"
            data = resp.json()
            assert data.get("registered") == False, f"未注册用户应返回registered=false: {data}"
        return self._run_test("A005", "未注册用户获取信息", test)
    
    def test_user_register(self):
        """A001: 测试用户注册"""
        def test():
            payload = {
                "nickname": f"测试用户_{uuid.uuid4().hex[:6]}",
                "avatar": "😊"
            }
            resp = self.session.post(self._api_url("/user/register"), json=payload, timeout=TIMEOUT)
            assert resp.status_code == 200, f"状态码错误: {resp.status_code}"
            data = resp.json()
            assert "id" in data or "user_id" in data, f"响应缺少用户ID: {data}"
            self.user_id = data.get("id") or data.get("user_id")
        return self._run_test("A001", "用户注册", test)
    
    def test_user_info_registered(self):
        """A002: 测试已注册用户获取信息"""
        def test():
            assert self.user_id, "需要先注册用户"
            resp = self.session.get(self._api_url("/user/info"), timeout=TIMEOUT)
            assert resp.status_code == 200, f"状态码错误: {resp.status_code}"
            data = resp.json()
            assert data.get("registered") == True or "nickname" in data, f"已注册用户信息异常: {data}"
        return self._run_test("A002", "已注册用户获取信息", test)
    
    def test_user_update(self):
        """A003: 测试更新用户信息"""
        def test():
            assert self.user_id, "需要先注册用户"
            payload = {
                "nickname": f"新昵称_{uuid.uuid4().hex[:4]}",
                "avatar": "😎"
            }
            resp = self.session.put(self._api_url("/user/update"), json=payload, timeout=TIMEOUT)
            assert resp.status_code == 200, f"状态码错误: {resp.status_code}"
        return self._run_test("A003", "更新用户信息", test)
    
    # ==================== 体力与道具测试 ====================
    
    def test_energy_get(self):
        """A101: 测试获取体力"""
        def test():
            resp = self.session.get(self._api_url("/user/energy"), timeout=TIMEOUT)
            assert resp.status_code == 200, f"状态码错误: {resp.status_code}"
            data = resp.json()
            assert "energy" in data, f"响应缺少energy字段: {data}"
        return self._run_test("A101", "获取体力", test)
    
    def test_props_get(self):
        """A104: 测试获取道具"""
        def test():
            resp = self.session.get(self._api_url("/user/props"), timeout=TIMEOUT)
            assert resp.status_code == 200, f"状态码错误: {resp.status_code}"
            data = resp.json()
            assert "hintLetterCount" in data or "hint_count" in data, f"响应缺少道具字段: {data}"
        return self._run_test("A104", "获取道具", test)
    
    # ==================== 词库与关卡测试 ====================
    
    def test_vocabulary_groups(self):
        """A201: 测试获取词库列表"""
        def test():
            resp = self.session.get(self._api_url("/vocabulary/groups"), timeout=TIMEOUT)
            assert resp.status_code == 200, f"状态码错误: {resp.status_code}"
            data = resp.json()
            assert isinstance(data, list) or "groups" in data, f"响应格式异常: {data}"
        return self._run_test("A201", "获取词库列表", test)
    
    def test_level_data(self):
        """A202: 测试获取关卡数据"""
        def test():
            resp = self.session.get(self._static_url("/data/levels/grade3_1/1.json"), timeout=TIMEOUT)
            assert resp.status_code == 200, f"状态码错误: {resp.status_code}"
            data = resp.json()
            assert "grid_size" in data or "cells" in data, f"关卡数据格式异常: {data}"
        return self._run_test("A202", "获取关卡数据", test)
    
    def test_level_meta(self):
        """A203: 测试获取词库元数据"""
        def test():
            resp = self.session.get(self._static_url("/data/levels/grade3_1/meta.json"), timeout=TIMEOUT)
            assert resp.status_code == 200, f"状态码错误: {resp.status_code}"
            data = resp.json()
            assert "level_count" in data or "word_count" in data, f"元数据格式异常: {data}"
        return self._run_test("A203", "获取词库元数据", test)
    
    def test_levels_summary(self):
        """A204: 测试获取词库汇总"""
        def test():
            resp = self.session.get(self._static_url("/data/levels/levels_summary.json"), timeout=TIMEOUT)
            assert resp.status_code == 200, f"状态码错误: {resp.status_code}"
            data = resp.json()
            assert isinstance(data, dict), f"汇总数据格式异常: {data}"
        return self._run_test("A204", "获取词库汇总", test)
    
    def test_endless_puzzle(self):
        """A206: 测试获取无限模式关卡"""
        def test():
            resp = self.session.get(
                self._api_url("/endless/puzzle"),
                params={"group": "grade3_1", "difficulty": "medium"},
                timeout=TIMEOUT
            )
            assert resp.status_code == 200, f"状态码错误: {resp.status_code}"
            data = resp.json()
            assert "grid_size" in data or "cells" in data or "puzzle" in data, f"关卡数据格式异常: {data}"
        return self._run_test("A206", "获取无限模式关卡", test)
    
    # ==================== 排行榜测试 ====================
    
    def test_leaderboard_types(self):
        """A401: 测试获取排行榜类型"""
        def test():
            resp = self.session.get(self._api_url("/leaderboard/types"), timeout=TIMEOUT)
            assert resp.status_code == 200, f"状态码错误: {resp.status_code}"
            data = resp.json()
            assert isinstance(data, list) or "types" in data, f"排行榜类型格式异常: {data}"
        return self._run_test("A401", "获取排行榜类型", test)
    
    def test_leaderboard_data(self):
        """A402: 测试获取排行榜数据"""
        def test():
            resp = self.session.get(
                self._api_url("/leaderboard/campaign_level"),
                params={"group": "grade3_1"},
                timeout=TIMEOUT
            )
            assert resp.status_code == 200, f"状态码错误: {resp.status_code}"
            data = resp.json()
            assert isinstance(data, list) or "entries" in data, f"排行榜数据格式异常: {data}"
        return self._run_test("A402", "获取排行榜数据", test)
    
    # ==================== 音频测试 ====================
    
    def test_audio_us(self):
        """A701: 测试美音音频"""
        def test():
            resp = self.session.head(self._static_url("/data/audio/us/apple.mp3"), timeout=TIMEOUT)
            assert resp.status_code in [200, 302], f"音频文件不存在或无法访问: {resp.status_code}"
        return self._run_test("A701", "美音音频文件", test)
    
    def test_audio_uk(self):
        """A702: 测试英音音频"""
        def test():
            resp = self.session.head(self._static_url("/data/audio/uk/apple.mp3"), timeout=TIMEOUT)
            assert resp.status_code in [200, 302], f"音频文件不存在或无法访问: {resp.status_code}"
        return self._run_test("A702", "英音音频文件", test)
    
    # ==================== 用户退出测试 ====================
    
    def test_user_logout(self):
        """A004: 测试用户退出"""
        def test():
            resp = self.session.delete(self._api_url("/user/logout"), timeout=TIMEOUT)
            assert resp.status_code in [200, 204], f"状态码错误: {resp.status_code}"
        return self._run_test("A004", "用户退出", test)
    
    # ==================== 运行所有测试 ====================
    
    def run_all_tests(self) -> Tuple[int, int]:
        """运行所有测试"""
        print(f"\n{'='*60}")
        print(f"填单词游戏 API 自动化测试")
        print(f"测试目标: {self.base_url}")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # 用户模块测试
        print("📋 用户模块测试")
        self.test_user_info_unregistered()
        self.test_user_register()
        self.test_user_info_registered()
        self.test_user_update()
        print()
        
        # 体力与道具测试
        print("⚡ 体力与道具测试")
        self.test_energy_get()
        self.test_props_get()
        print()
        
        # 词库与关卡测试
        print("📚 词库与关卡测试")
        self.test_vocabulary_groups()
        self.test_level_data()
        self.test_level_meta()
        self.test_levels_summary()
        self.test_endless_puzzle()
        print()
        
        # 排行榜测试
        print("🏆 排行榜测试")
        self.test_leaderboard_types()
        self.test_leaderboard_data()
        print()
        
        # 音频测试
        print("🔊 音频测试")
        self.test_audio_us()
        self.test_audio_uk()
        print()
        
        # 用户退出
        print("🚪 用户退出测试")
        self.test_user_logout()
        print()
        
        # 统计结果
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        print(f"{'='*60}")
        print(f"测试完成: {passed}/{total} 通过")
        print(f"通过率: {passed/total*100:.1f}%")
        print(f"{'='*60}\n")
        
        return passed, total
    
    def generate_report(self, output_file: str = "test_report.json"):
        """生成测试报告"""
        report = {
            "base_url": self.base_url,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.passed),
                "failed": sum(1 for r in self.results if not r.passed),
                "pass_rate": f"{sum(1 for r in self.results if r.passed)/len(self.results)*100:.1f}%"
            },
            "results": [
                {
                    "test_id": r.test_id,
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "duration_ms": r.duration_ms
                }
                for r in self.results
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 测试报告已保存到: {output_file}")
        return report

def main():
    parser = argparse.ArgumentParser(description="填单词游戏 API 自动化测试")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API基础URL")
    parser.add_argument("--report", default="test_report.json", help="测试报告输出文件")
    args = parser.parse_args()
    
    tester = APITester(args.base_url)
    passed, total = tester.run_all_tests()
    tester.generate_report(args.report)
    
    # 返回非零退出码表示有测试失败
    exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
