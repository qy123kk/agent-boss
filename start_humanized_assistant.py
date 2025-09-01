#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人性化求职助手启动脚本
提供多种启动方式：Web界面、命令行、测试模式
"""

import sys
import os
import argparse
from typing import Optional


def start_web_interface():
    """启动Web界面"""
    print("🌐 启动人性化求职助手Web界面...")
    print("📝 使用说明：")
    print("   1. 系统会智能引导您提供求职需求")
    print("   2. 需要提供：职位类型、工作地点、薪资期望")
    print("   3. 系统将自动为您匹配3个最相关的职位")
    print("   4. 支持多轮对话，自然语言交互")
    print()
    
    try:
        import streamlit.web.cli as stcli
        sys.argv = ["streamlit", "run", "humanized_job_web.py", "--server.port=8501"]
        stcli.main()
    except ImportError:
        print("❌ 未安装streamlit，请先安装：pip install streamlit")
        return False
    except Exception as e:
        print(f"❌ 启动Web界面失败: {e}")
        return False


def start_cli_interface():
    """启动命令行界面"""
    print("💻 启动人性化求职助手命令行界面...")
    
    try:
        from humanized_job_assistant import main
        main()
    except Exception as e:
        print(f"❌ 启动命令行界面失败: {e}")
        return False


def run_system_test():
    """运行系统测试"""
    print("🧪 运行人性化求职助手系统测试...")
    print("=" * 60)
    
    try:
        from humanized_job_assistant import create_humanized_job_assistant
        
        # 创建助手实例
        print("1️⃣ 创建助手实例...")
        assistant = create_humanized_job_assistant()
        
        # 初始化系统
        print("2️⃣ 初始化系统...")
        init_result = assistant.initialize()
        
        if not init_result["success"]:
            print(f"❌ 初始化失败: {init_result['error']}")
            return False
        
        print("✅ 系统初始化成功")
        
        # 显示系统统计
        if "stats" in init_result:
            stats = init_result["stats"]
            vector_stats = stats.get("vector_store", {})
            print(f"📊 系统统计:")
            print(f"   - 文档数量: {vector_stats.get('total_documents', 0)}")
            print(f"   - 文本块数量: {vector_stats.get('total_chunks', 0)}")
            print(f"   - 最后更新: {vector_stats.get('last_update', '未知')}")
        
        # 开始对话测试
        print("\n3️⃣ 开始对话测试...")
        start_result = assistant.start_conversation()
        
        if not start_result["success"]:
            print(f"❌ 开始对话失败: {start_result.get('error', '未知错误')}")
            return False
        
        print("✅ 对话开始成功")
        print(f"🤖 助手: {start_result['message']}")
        
        # 模拟用户输入测试
        test_inputs = [
            "Python开发工程师",
            "深圳",
            "15-20K"
        ]
        
        print("\n4️⃣ 模拟对话流程...")
        for i, user_input in enumerate(test_inputs, 1):
            print(f"\n👤 用户 ({i}/3): {user_input}")
            
            result = assistant.process_message(user_input)
            
            if not result["success"]:
                print(f"❌ 处理消息失败: {result.get('error', '未知错误')}")
                return False
            
            print(f"🤖 助手: {result['message'][:100]}...")
            
            # 显示进度
            progress = result.get("progress", {})
            print(f"📊 进度: {progress.get('progress_percentage', 0):.0f}%")
            
            # 如果有搜索结果
            if "search_results" in result:
                search_results = result["search_results"]
                print(f"🎉 找到 {len(search_results)} 个匹配职位:")
                for j, job in enumerate(search_results, 1):
                    print(f"   {j}. {job['company_name']} - {job['job_title']}")
                    print(f"      💰 {job['salary']} | 📍 {job['location']}")
                break
        
        print("\n✅ 系统测试完成！所有功能正常工作。")
        return True
        
    except Exception as e:
        print(f"❌ 系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_dependencies():
    """检查依赖项"""
    print("🔍 检查系统依赖...")

    # 包名映射：安装名 -> 导入名
    package_mapping = {
        "streamlit": "streamlit",
        "langchain": "langchain",
        "langchain_openai": "langchain_openai",
        "langchain_community": "langchain_community",
        "faiss-cpu": "faiss",  # faiss-cpu 安装后导入为 faiss
        "pandas": "pandas",
        "python-dotenv": "dotenv"  # python-dotenv 安装后导入为 dotenv
    }

    missing_packages = []

    for install_name, import_name in package_mapping.items():
        try:
            __import__(import_name)
            print(f"✅ {install_name}")
        except ImportError:
            print(f"❌ {install_name} (未安装)")
            missing_packages.append(install_name)

    if missing_packages:
        print(f"\n⚠️  缺少以下依赖包:")
        for package in missing_packages:
            print(f"   - {package}")
        print(f"\n💡 安装命令: pip install {' '.join(missing_packages)}")
        return False

    print("✅ 所有依赖项已安装")
    return True


def show_help():
    """显示帮助信息"""
    print("🤖 人性化求职助手 - 使用说明")
    print("=" * 50)
    print()
    print("📋 功能特点:")
    print("  • 智能多轮对话收集求职需求")
    print("  • 自然语言理解用户意图")
    print("  • RAG技术精准匹配职位")
    print("  • 人性化交互体验")
    print()
    print("🚀 启动方式:")
    print("  python start_humanized_assistant.py web     # Web界面")
    print("  python start_humanized_assistant.py cli     # 命令行界面")
    print("  python start_humanized_assistant.py test    # 系统测试")
    print("  python start_humanized_assistant.py check   # 检查依赖")
    print()
    print("💡 使用流程:")
    print("  1. 系统会友好地询问您的求职需求")
    print("  2. 您只需用自然语言回答问题")
    print("  3. 系统会智能理解并收集关键信息")
    print("  4. 收集完成后自动搜索匹配职位")
    print("  5. 展示3个最相关的工作机会")
    print()
    print("📞 技术支持:")
    print("  如遇问题，请先运行: python start_humanized_assistant.py test")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="人性化求职助手启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["web", "cli", "test", "check", "help"],
        default="web",
        help="启动模式: web(Web界面), cli(命令行), test(测试), check(检查依赖), help(帮助)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "help":
        show_help()
    elif args.mode == "check":
        check_dependencies()
    elif args.mode == "test":
        if check_dependencies():
            run_system_test()
    elif args.mode == "cli":
        if check_dependencies():
            start_cli_interface()
    else:  # web
        if check_dependencies():
            start_web_interface()


if __name__ == "__main__":
    main()
