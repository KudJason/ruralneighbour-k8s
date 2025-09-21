#!/usr/bin/env python3
"""
消息队列测试运行脚本

用法:
    python run_message_queue_tests.py [选项]

选项:
    --core          运行核心功能测试
    --business      运行业务场景测试
    --performance   运行性能测试
    --all           运行所有测试
    --verbose       详细输出
    --coverage      生成覆盖率报告
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type, verbose=False, coverage=False):
    """运行指定类型的测试"""
    
    # 获取测试文件路径
    test_dir = Path(__file__).parent
    test_files = {
        "core": test_dir / "test_message_queue_core.py",
        "business": test_dir / "test_business_scenarios.py", 
        "performance": test_dir / "test_message_queue_performance.py"
    }
    
    if test_type not in test_files:
        print(f"未知的测试类型: {test_type}")
        return False
    
    test_file = test_files[test_type]
    
    # 构建pytest命令
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    cmd.append(str(test_file))
    
    print(f"运行 {test_type} 测试...")
    print(f"命令: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, cwd=test_dir.parent, check=True)
        print(f"\n✅ {test_type} 测试通过!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {test_type} 测试失败!")
        print(f"退出码: {e.returncode}")
        return False


def run_all_tests(verbose=False, coverage=False):
    """运行所有测试"""
    test_types = ["core", "business", "performance"]
    results = []
    
    print("🚀 开始运行所有消息队列测试...")
    print("=" * 60)
    
    for test_type in test_types:
        success = run_tests(test_type, verbose, coverage)
        results.append((test_type, success))
        print()
    
    # 汇总结果
    print("=" * 60)
    print("📊 测试结果汇总:")
    
    passed = 0
    failed = 0
    
    for test_type, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_type:12} {status}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("🎉 所有测试都通过了!")
        return True
    else:
        print("⚠️  有测试失败，请检查输出")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="消息队列测试运行器")
    parser.add_argument("--core", action="store_true", help="运行核心功能测试")
    parser.add_argument("--business", action="store_true", help="运行业务场景测试")
    parser.add_argument("--performance", action="store_true", help="运行性能测试")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--coverage", action="store_true", help="生成覆盖率报告")
    
    args = parser.parse_args()
    
    # 检查参数
    if not any([args.core, args.business, args.performance, args.all]):
        parser.print_help()
        return 1
    
    # 运行测试
    success = True
    
    if args.all:
        success = run_all_tests(args.verbose, args.coverage)
    else:
        if args.core:
            success &= run_tests("core", args.verbose, args.coverage)
        if args.business:
            success &= run_tests("business", args.verbose, args.coverage)
        if args.performance:
            success &= run_tests("performance", args.verbose, args.coverage)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())




