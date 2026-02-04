#!/usr/bin/env python3
"""
填单词游戏 - UI截图自动化测试脚本
使用Playwright进行浏览器截图测试

使用方法:
    pip install playwright
    playwright install chromium
    python tests/test_ui_screenshot.py --base-url http://localhost:10010
"""

import asyncio
import argparse
import os
from datetime import datetime
from playwright.async_api import async_playwright
import json

# 测试配置
DEFAULT_BASE_URL = "http://localhost:10010"
SCREENSHOT_DIR = "tests/screenshots"
VIEWPORT_MOBILE = {"width": 375, "height": 812}  # iPhone X
VIEWPORT_TABLET = {"width": 768, "height": 1024}  # iPad
VIEWPORT_DESKTOP = {"width": 1280, "height": 800}

# 测试页面列表
TEST_PAGES = [
    {"name": "首页", "path": "/", "wait_for": ".home-screen, .main-card"},
    {"name": "设置页", "path": "/settings", "wait_for": ".settings-screen, .settings-card"},
    {"name": "排行榜", "path": "/leaderboard", "wait_for": ".leaderboard-screen"},
]

async def take_screenshots(base_url: str, viewport_name: str, viewport: dict, output_dir: str):
    """对所有页面进行截图"""
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport=viewport)
        page = await context.new_page()
        
        for test_page in TEST_PAGES:
            url = f"{base_url}{test_page['path']}"
            filename = f"{viewport_name}_{test_page['name']}.png"
            filepath = os.path.join(output_dir, filename)
            
            try:
                print(f"  📸 截图: {test_page['name']} ({viewport_name})")
                await page.goto(url, timeout=30000)
                
                # 等待页面加载
                if test_page.get("wait_for"):
                    try:
                        await page.wait_for_selector(test_page["wait_for"], timeout=10000)
                    except:
                        print(f"    ⚠️ 等待选择器超时: {test_page['wait_for']}")
                
                # 额外等待确保动画完成
                await page.wait_for_timeout(1000)
                
                # 截图
                await page.screenshot(path=filepath, full_page=True)
                
                results.append({
                    "page": test_page["name"],
                    "viewport": viewport_name,
                    "status": "success",
                    "screenshot": filepath
                })
                print(f"    ✅ 已保存: {filename}")
                
            except Exception as e:
                results.append({
                    "page": test_page["name"],
                    "viewport": viewport_name,
                    "status": "error",
                    "error": str(e)
                })
                print(f"    ❌ 失败: {str(e)}")
        
        await browser.close()
    
    return results

async def run_ui_tests(base_url: str, output_dir: str):
    """运行所有UI测试"""
    print(f"\n{'='*60}")
    print("填单词游戏 UI 截图测试")
    print(f"测试目标: {base_url}")
    print(f"截图目录: {output_dir}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 创建截图目录
    os.makedirs(output_dir, exist_ok=True)
    
    all_results = []
    
    # 移动端测试
    print("📱 移动端截图 (375x812)")
    results = await take_screenshots(base_url, "mobile", VIEWPORT_MOBILE, output_dir)
    all_results.extend(results)
    print()
    
    # 平板测试
    print("📋 平板截图 (768x1024)")
    results = await take_screenshots(base_url, "tablet", VIEWPORT_TABLET, output_dir)
    all_results.extend(results)
    print()
    
    # 桌面测试
    print("🖥️ 桌面截图 (1280x800)")
    results = await take_screenshots(base_url, "desktop", VIEWPORT_DESKTOP, output_dir)
    all_results.extend(results)
    print()
    
    # 统计结果
    success = sum(1 for r in all_results if r["status"] == "success")
    total = len(all_results)
    
    print(f"{'='*60}")
    print(f"截图完成: {success}/{total} 成功")
    print(f"截图保存到: {output_dir}")
    print(f"{'='*60}\n")
    
    # 保存结果报告
    report = {
        "base_url": base_url,
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": total,
            "success": success,
            "failed": total - success
        },
        "results": all_results
    }
    
    report_path = os.path.join(output_dir, "screenshot_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📄 报告已保存到: {report_path}")
    
    return all_results

def main():
    parser = argparse.ArgumentParser(description="填单词游戏 UI 截图测试")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="应用基础URL")
    parser.add_argument("--output-dir", default=SCREENSHOT_DIR, help="截图输出目录")
    args = parser.parse_args()
    
    asyncio.run(run_ui_tests(args.base_url, args.output_dir))

if __name__ == "__main__":
    main()
