#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动Web应用的脚本
"""

import os
import sys
import subprocess


def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")

    # 检查文档目录
    if not os.path.exists("documents"):
        print("❌ 未找到文档目录")
        print("💡 请确保 documents 目录存在并包含Excel文件")
        return False

    # 检查核心文件
    required_files = [
        "simple_job_finder.py",
        "job_finder_web.py",
        "rag_core.py",
        "document_loader.py",
        "vector_store.py",
        "qa_chain.py",
        "incremental_vector_store.py"
    ]

    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少核心文件: {file}")
            return False

    # 智能检查向量存储状态
    from incremental_vector_store import IncrementalVectorStore
    vector_manager = IncrementalVectorStore("vector_store")

    update_info = vector_manager.check_updates_needed('documents')
    if update_info['needs_update']:
        print("📊 检测到数据更新，启动时将自动更新向量存储")
        if update_info['new_files']:
            print(f"  📄 新增文件: {len(update_info['new_files'])} 个")
        if update_info['modified_files']:
            print(f"  📝 修改文件: {len(update_info['modified_files'])} 个")
    else:
        print("✅ 向量存储已是最新状态")

    print("✅ 环境检查通过")
    return True


def start_web_app():
    """启动Web应用"""
    print("🚀 启动智能求职助手Web应用...")
    print("=" * 50)
    print("📱 应用将在浏览器中自动打开")
    print("🌐 如果没有自动打开，请访问: http://localhost:8501")
    print("⏹️  按 Ctrl+C 停止应用")
    print("=" * 50)
    
    try:
        # 启动Streamlit应用
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "job_finder_web.py",
            "--server.address", "localhost",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")


def main():
    """主函数"""
    print("🎯 智能求职助手 - Web应用启动器")
    print("=" * 50)
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，请先解决上述问题")
        return
    
    # 启动应用
    start_web_app()


if __name__ == "__main__":
    main()
