#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量向量存储管理器
支持向量存储的增量更新、复用和版本管理
"""

import os
import json
import hashlib
import shutil
from datetime import datetime
from typing import List, Dict, Optional
from document_loader import load_documents, split_documents
from vector_store import create_vector_store, load_vector_store, create_embeddings
from langchain_community.vectorstores import FAISS


class IncrementalVectorStore:
    """增量向量存储管理器"""
    
    def __init__(self, vector_store_path: str = "vector_store"):
        self.vector_store_path = vector_store_path
        self.metadata_file = os.path.join(vector_store_path, "metadata.json")
        self.vector_store = None
        self.metadata = {}
        
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件的MD5哈希值"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"计算文件哈希失败 {file_path}: {e}")
            return ""
    
    def _get_documents_info(self, documents_dir: str) -> Dict:
        """获取文档目录的信息"""
        docs_info = {}
        
        if not os.path.exists(documents_dir):
            return docs_info
        
        for filename in os.listdir(documents_dir):
            file_path = os.path.join(documents_dir, filename)
            if os.path.isfile(file_path) and filename.endswith(('.xlsx', '.xls', '.pdf', '.docx', '.txt')):
                file_hash = self._calculate_file_hash(file_path)
                file_stat = os.stat(file_path)
                
                docs_info[filename] = {
                    'hash': file_hash,
                    'size': file_stat.st_size,
                    'modified_time': file_stat.st_mtime,
                    'path': file_path
                }
        
        return docs_info
    
    def _load_metadata(self) -> Dict:
        """加载元数据"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载元数据失败: {e}")
        
        return {
            'created_time': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'documents': {},
            'total_documents': 0,
            'total_chunks': 0,
            'version': '1.0'
        }
    
    def _save_metadata(self):
        """保存元数据"""
        os.makedirs(os.path.dirname(self.metadata_file), exist_ok=True)
        
        self.metadata['last_updated'] = datetime.now().isoformat()
        
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存元数据失败: {e}")
    
    def check_updates_needed(self, documents_dir: str) -> Dict:
        """检查是否需要更新"""
        current_docs = self._get_documents_info(documents_dir)
        self.metadata = self._load_metadata()
        stored_docs = self.metadata.get('documents', {})
        
        result = {
            'needs_update': False,
            'new_files': [],
            'modified_files': [],
            'deleted_files': [],
            'unchanged_files': []
        }
        
        # 检查新增和修改的文件
        for filename, info in current_docs.items():
            if filename not in stored_docs:
                result['new_files'].append(filename)
                result['needs_update'] = True
            elif stored_docs[filename]['hash'] != info['hash']:
                result['modified_files'].append(filename)
                result['needs_update'] = True
            else:
                result['unchanged_files'].append(filename)
        
        # 检查删除的文件
        for filename in stored_docs:
            if filename not in current_docs:
                result['deleted_files'].append(filename)
                result['needs_update'] = True
        
        return result
    
    def create_or_update_vector_store(self, documents_dir: str, force_rebuild: bool = False) -> bool:
        """创建或更新向量存储"""
        print("🔍 检查向量存储更新需求...")
        
        # 检查更新需求
        update_info = self.check_updates_needed(documents_dir)
        
        if not update_info['needs_update'] and not force_rebuild and os.path.exists(self.vector_store_path):
            print("✅ 向量存储已是最新，无需更新")
            self.vector_store = load_vector_store(self.vector_store_path)
            return True
        
        # 显示更新信息
        if update_info['new_files']:
            print(f"📄 新增文件: {len(update_info['new_files'])} 个")
            for file in update_info['new_files'][:3]:
                print(f"  + {file}")
            if len(update_info['new_files']) > 3:
                print(f"  ... 还有 {len(update_info['new_files']) - 3} 个")
        
        if update_info['modified_files']:
            print(f"📝 修改文件: {len(update_info['modified_files'])} 个")
            for file in update_info['modified_files'][:3]:
                print(f"  ~ {file}")
            if len(update_info['modified_files']) > 3:
                print(f"  ... 还有 {len(update_info['modified_files']) - 3} 个")
        
        if update_info['deleted_files']:
            print(f"🗑️ 删除文件: {len(update_info['deleted_files'])} 个")
            for file in update_info['deleted_files'][:3]:
                print(f"  - {file}")
        
        if update_info['unchanged_files']:
            print(f"✅ 未变更文件: {len(update_info['unchanged_files'])} 个")
        
        # 决定更新策略
        if force_rebuild or len(update_info['deleted_files']) > 0 or len(update_info['modified_files']) > 0:
            # 完全重建
            return self._full_rebuild(documents_dir)
        else:
            # 增量更新
            return self._incremental_update(documents_dir, update_info['new_files'])
    
    def _full_rebuild(self, documents_dir: str) -> bool:
        """完全重建向量存储"""
        print("🔄 执行完全重建...")
        
        try:
            # 删除旧的向量存储
            if os.path.exists(self.vector_store_path):
                shutil.rmtree(self.vector_store_path)
            
            # 加载所有文档
            print("📚 加载所有文档...")
            documents = load_documents(documents_dir)
            
            if not documents:
                print("❌ 没有找到文档")
                return False
            
            print(f"✅ 成功加载 {len(documents)} 个文档")
            
            # 分割文档
            print("✂️ 分割文档...")
            chunks = split_documents(documents)
            print(f"✅ 文档分割完成，共 {len(chunks)} 个块")
            
            # 创建向量存储
            print("🧮 创建向量存储...")
            self.vector_store = create_vector_store(chunks, self.vector_store_path)
            
            # 更新元数据
            current_docs = self._get_documents_info(documents_dir)
            self.metadata = self._load_metadata()
            self.metadata['documents'] = current_docs
            self.metadata['total_documents'] = len(documents)
            self.metadata['total_chunks'] = len(chunks)
            self._save_metadata()
            
            print("✅ 向量存储重建完成")
            return True
            
        except Exception as e:
            print(f"❌ 重建失败: {e}")
            return False
    
    def _incremental_update(self, documents_dir: str, new_files: List[str]) -> bool:
        """增量更新向量存储"""
        print("📈 执行增量更新...")
        
        try:
            # 加载现有向量存储
            if os.path.exists(self.vector_store_path):
                print("📂 加载现有向量存储...")
                self.vector_store = load_vector_store(self.vector_store_path)
            else:
                print("🆕 创建新的向量存储...")
                return self._full_rebuild(documents_dir)
            
            # 处理新文件
            new_documents = []
            for filename in new_files:
                file_path = os.path.join(documents_dir, filename)
                print(f"📄 处理新文件: {filename}")
                
                # 加载单个文件
                if filename.endswith(('.xlsx', '.xls')):
                    from document_loader import load_excel_document
                    docs = load_excel_document(file_path)
                    new_documents.extend(docs)
                # 可以添加其他文件类型的处理
            
            if not new_documents:
                print("⚠️ 没有新文档需要添加")
                return True
            
            print(f"✅ 新增 {len(new_documents)} 个文档")
            
            # 分割新文档
            new_chunks = split_documents(new_documents)
            print(f"✅ 新文档分割完成，共 {len(new_chunks)} 个块")
            
            # 添加到现有向量存储
            print("🔗 添加到现有向量存储...")
            embeddings = create_embeddings()
            
            # 创建新文档的向量存储
            new_vector_store = FAISS.from_documents(new_chunks, embeddings)
            
            # 合并向量存储
            self.vector_store.merge_from(new_vector_store)
            
            # 保存更新后的向量存储
            self.vector_store.save_local(self.vector_store_path)
            
            # 更新元数据
            current_docs = self._get_documents_info(documents_dir)
            self.metadata['documents'].update({
                filename: current_docs[filename] for filename in new_files
            })
            self.metadata['total_documents'] += len(new_documents)
            self.metadata['total_chunks'] += len(new_chunks)
            self._save_metadata()
            
            print("✅ 增量更新完成")
            return True
            
        except Exception as e:
            print(f"❌ 增量更新失败: {e}")
            print("🔄 回退到完全重建...")
            return self._full_rebuild(documents_dir)
    
    def get_vector_store(self):
        """获取向量存储"""
        if self.vector_store is None:
            if os.path.exists(self.vector_store_path):
                self.vector_store = load_vector_store(self.vector_store_path)
            else:
                raise ValueError("向量存储不存在，请先创建")
        return self.vector_store
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        self.metadata = self._load_metadata()
        return {
            'total_documents': self.metadata.get('total_documents', 0),
            'total_chunks': self.metadata.get('total_chunks', 0),
            'total_files': len(self.metadata.get('documents', {})),
            'created_time': self.metadata.get('created_time', '未知'),
            'last_updated': self.metadata.get('last_updated', '未知'),
            'version': self.metadata.get('version', '1.0')
        }


def main():
    """测试增量向量存储"""
    print("🧪 测试增量向量存储管理器")
    print("=" * 50)
    
    manager = IncrementalVectorStore()
    
    # 检查更新需求
    update_info = manager.check_updates_needed('documents')
    print("📊 更新检查结果:")
    print(f"  需要更新: {update_info['needs_update']}")
    print(f"  新增文件: {len(update_info['new_files'])}")
    print(f"  修改文件: {len(update_info['modified_files'])}")
    print(f"  删除文件: {len(update_info['deleted_files'])}")
    print(f"  未变更文件: {len(update_info['unchanged_files'])}")
    
    # 创建或更新向量存储
    success = manager.create_or_update_vector_store('documents')
    
    if success:
        # 显示统计信息
        stats = manager.get_statistics()
        print(f"\n📈 向量存储统计:")
        print(f"  文档总数: {stats['total_documents']}")
        print(f"  文本块总数: {stats['total_chunks']}")
        print(f"  文件总数: {stats['total_files']}")
        print(f"  创建时间: {stats['created_time']}")
        print(f"  最后更新: {stats['last_updated']}")
    
    print("\n🎉 测试完成!")


if __name__ == "__main__":
    main()
