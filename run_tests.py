#!/usr/bin/env python3
"""
ComfyUI Copilot 测试运行器
简化测试执行流程
"""

import sys
import os
import subprocess
import argparse

def run_mock_tests():
    """运行模拟测试"""
    print("🚀 运行模拟测试...")
    try:
        result = subprocess.run([
            sys.executable, 
            "backend/test_tools_fixed.py"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        return False

def run_full_tests():
    """运行完整测试"""
    print("🔧 运行完整集成测试...")
    try:
        result = subprocess.run([
            sys.executable, 
            "backend/test_tools.py"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        return False

def check_dependencies():
    """检查依赖是否安装"""
    print("📋 检查依赖...")
    try:
        import agents
        import sqlalchemy
        import openai
        print("✅ 依赖检查通过")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("💡 请运行: pip install -r requirements.txt")
        return False

def main():
    parser = argparse.ArgumentParser(description="ComfyUI Copilot 测试运行器")
    parser.add_argument(
        "--type", 
        choices=["mock", "full", "check"], 
        default="mock",
        help="测试类型: mock=模拟测试, full=完整测试, check=检查依赖"
    )
    
    args = parser.parse_args()
    
    print("🧪 ComfyUI Copilot 测试运行器")
    print("=" * 50)
    
    if args.type == "check":
        success = check_dependencies()
    elif args.type == "mock":
        success = run_mock_tests()
    elif args.type == "full":
        if not check_dependencies():
            print("❌ 依赖检查失败，无法运行完整测试")
            return 1
        success = run_full_tests()
    
    if success:
        print("\n🎉 测试完成！")
        return 0
    else:
        print("\n❌ 测试失败！")
        return 1

if __name__ == "__main__":
    exit(main()) 