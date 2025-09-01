#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量存储管理工具
提供向量存储的创建、更新、检查、清理等功能
"""

import os
import sys
import argparse
from incremental_vector_store import IncrementalVectorStore


def check_status(vector_store_path="vector_store", documents_dir="documents"):
    """检查向量存储状态"""
    print("📊 向量存储状态检查")
    print("=" * 50)
    
    manager = IncrementalVectorStore(vector_store_path)
    
    # 检查向量存储是否存在
    if os.path.exists(vector_store_path):
        print("✅ 向量存储存在")
        
        # 加载元数据
        metadata = manager._load_metadata()
        if metadata:
            print(f"📄 文档数量: {metadata.get('total_documents', 0)}")
            print(f"🧩 文本块数量: {metadata.get('total_chunks', 0)}")
            print(f"📅 最后更新: {metadata.get('last_update', '未知')}")
            print(f"🗂️ 文件数量: {len(metadata.get('documents', {}))}")
        else:
            print("⚠️ 元数据文件不存在或损坏")
    else:
        print("❌ 向量存储不存在")
    
    # 检查更新需求
    print(f"\n🔍 检查更新需求...")
    update_info = manager.check_updates_needed(documents_dir)
    
    print(f"需要更新: {'是' if update_info['needs_update'] else '否'}")
    if update_info['new_files']:
        print(f"📄 新增文件: {len(update_info['new_files'])} 个")
        for file in update_info['new_files'][:5]:
            print(f"  + {file}")
        if len(update_info['new_files']) > 5:
            print(f"  ... 还有 {len(update_info['new_files']) - 5} 个")
    
    if update_info['modified_files']:
        print(f"📝 修改文件: {len(update_info['modified_files'])} 个")
        for file in update_info['modified_files'][:5]:
            print(f"  ~ {file}")
        if len(update_info['modified_files']) > 5:
            print(f"  ... 还有 {len(update_info['modified_files']) - 5} 个")
    
    if update_info['deleted_files']:
        print(f"🗑️ 删除文件: {len(update_info['deleted_files'])} 个")
        for file in update_info['deleted_files'][:5]:
            print(f"  - {file}")
    
    if update_info['unchanged_files']:
        print(f"✅ 未变更文件: {len(update_info['unchanged_files'])} 个")


def update_vector_store(vector_store_path="vector_store", documents_dir="documents", force=False):
    """更新向量存储"""
    print("🔄 更新向量存储")
    print("=" * 50)
    
    manager = IncrementalVectorStore(vector_store_path)
    
    if force:
        print("⚠️ 强制重建模式")
    
    success = manager.create_or_update_vector_store(documents_dir, force_rebuild=force)
    
    if success:
        print("✅ 向量存储更新成功")
        
        # 显示更新后的状态
        metadata = manager._load_metadata()
        if metadata:
            print(f"\n📊 更新后状态:")
            print(f"📄 文档数量: {metadata.get('total_documents', 0)}")
            print(f"🧩 文本块数量: {metadata.get('total_chunks', 0)}")
            print(f"📅 更新时间: {metadata.get('last_update', '未知')}")
    else:
        print("❌ 向量存储更新失败")
        return False
    
    return True


def clean_vector_store(vector_store_path="vector_store"):
    """清理向量存储"""
    print("🧹 清理向量存储")
    print("=" * 50)
    
    if os.path.exists(vector_store_path):
        import shutil
        try:
            shutil.rmtree(vector_store_path)
            print("✅ 向量存储已清理")
        except Exception as e:
            print(f"❌ 清理失败: {e}")
            return False
    else:
        print("ℹ️ 向量存储不存在，无需清理")
    
    return True


def backup_vector_store(vector_store_path="vector_store", backup_path=None):
    """备份向量存储"""
    if backup_path is None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{vector_store_path}_backup_{timestamp}"
    
    print(f"💾 备份向量存储到: {backup_path}")
    print("=" * 50)
    
    if not os.path.exists(vector_store_path):
        print("❌ 源向量存储不存在")
        return False
    
    try:
        import shutil
        shutil.copytree(vector_store_path, backup_path)
        print("✅ 备份完成")
        return True
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return False


def restore_vector_store(backup_path, vector_store_path="vector_store"):
    """恢复向量存储"""
    print(f"🔄 从备份恢复向量存储: {backup_path}")
    print("=" * 50)
    
    if not os.path.exists(backup_path):
        print("❌ 备份文件不存在")
        return False
    
    try:
        import shutil
        
        # 删除现有向量存储
        if os.path.exists(vector_store_path):
            shutil.rmtree(vector_store_path)
        
        # 恢复备份
        shutil.copytree(backup_path, vector_store_path)
        print("✅ 恢复完成")
        return True
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="向量存储管理工具")
    parser.add_argument("command", choices=["status", "update", "clean", "backup", "restore"], 
                       help="执行的命令")
    parser.add_argument("--vector-store", default="vector_store", 
                       help="向量存储路径 (默认: vector_store)")
    parser.add_argument("--documents", default="documents", 
                       help="文档目录路径 (默认: documents)")
    parser.add_argument("--force", action="store_true", 
                       help="强制重建向量存储")
    parser.add_argument("--backup-path", 
                       help="备份路径")
    
    args = parser.parse_args()
    
    print("🎯 向量存储管理工具")
    print("=" * 60)
    
    try:
        if args.command == "status":
            check_status(args.vector_store, args.documents)
        
        elif args.command == "update":
            success = update_vector_store(args.vector_store, args.documents, args.force)
            sys.exit(0 if success else 1)
        
        elif args.command == "clean":
            success = clean_vector_store(args.vector_store)
            sys.exit(0 if success else 1)
        
        elif args.command == "backup":
            success = backup_vector_store(args.vector_store, args.backup_path)
            sys.exit(0 if success else 1)
        
        elif args.command == "restore":
            if not args.backup_path:
                print("❌ 恢复命令需要指定 --backup-path")
                sys.exit(1)
            success = restore_vector_store(args.backup_path, args.vector_store)
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\n👋 操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
