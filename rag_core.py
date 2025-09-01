#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG核心模块 - 简化版
整合文档加载、向量存储和问答链功能，提供简洁的API
"""

import os
from typing import List, Dict, Optional
from document_loader import load_documents, split_documents, load_excel_document
from vector_store import create_vector_store, load_vector_store, search_documents
from qa_chain import setup_qa_chain, setup_streaming_qa_chain, ask_question, ask_question_streaming


class RAGSystem:
    """RAG系统核心类"""
    
    def __init__(self, vector_store_path: str = "vector_store"):
        self.vector_store_path = vector_store_path
        self.vector_store = None
        self.qa_chain = None
        self.streaming_handler = None
        self.documents = []
        
    def load_documents_from_directory(self, documents_dir: str):
        """从目录加载文档"""
        print(f"正在从 {documents_dir} 加载文档...")
        self.documents = load_documents(documents_dir)
        print(f"成功加载 {len(self.documents)} 个文档")
        return self.documents
    
    def load_excel_file(self, excel_path: str):
        """加载单个Excel文件"""
        print(f"正在加载Excel文件: {excel_path}")
        self.documents = load_excel_document(excel_path)
        print(f"成功加载 {len(self.documents)} 个文档")
        return self.documents
    
    def create_vector_store(self, documents: Optional[List] = None):
        """创建向量存储"""
        if documents is None:
            documents = self.documents
            
        if not documents:
            raise ValueError("没有文档可以创建向量存储")
        
        print("正在分割文档...")
        chunks = split_documents(documents)
        print(f"文档分割完成，共 {len(chunks)} 个块")
        
        print("正在创建向量存储...")
        self.vector_store = create_vector_store(chunks, self.vector_store_path)
        print("向量存储创建完成")
        return self.vector_store
    
    def load_existing_vector_store(self):
        """加载现有的向量存储"""
        if not os.path.exists(self.vector_store_path):
            raise FileNotFoundError(f"向量存储路径不存在: {self.vector_store_path}")
        
        print(f"正在加载向量存储: {self.vector_store_path}")
        self.vector_store = load_vector_store(self.vector_store_path)
        print("向量存储加载完成")
        return self.vector_store
    
    def setup_qa_system(self, system_prompt: str = "", use_streaming: bool = True, conversation_history: Optional[List[Dict]] = None):
        """设置问答系统"""
        if self.vector_store is None:
            raise ValueError("请先创建或加载向量存储")
        
        if use_streaming:
            self.qa_chain, self.streaming_handler = setup_streaming_qa_chain(
                self.vector_store, system_prompt, conversation_history
            )
        else:
            self.qa_chain, _ = setup_qa_chain(
                self.vector_store, system_prompt, conversation_history
            )
            self.streaming_handler = None
        
        print("问答系统设置完成")
        return self.qa_chain
    
    def ask(self, question: str, use_streaming: bool = None):
        """提问"""
        if self.qa_chain is None:
            raise ValueError("请先设置问答系统")
        
        # 如果没有指定streaming模式，根据是否有streaming_handler决定
        if use_streaming is None:
            use_streaming = self.streaming_handler is not None
        
        if use_streaming and self.streaming_handler:
            return ask_question_streaming(self.qa_chain, self.streaming_handler, question)
        else:
            return ask_question(self.qa_chain, question)
    
    def search(self, query: str, k: int = 3):
        """搜索相关文档"""
        if self.vector_store is None:
            raise ValueError("请先创建或加载向量存储")
        
        return search_documents(self.vector_store, query, k)
    
    def get_document_stats(self):
        """获取文档统计信息"""
        stats = {
            "total_documents": 0,
            "file_types": {}
        }

        if not self.documents:
            return stats

        stats["total_documents"] = len(self.documents)

        for doc in self.documents:
            file_type = doc.metadata.get('file_type', 'unknown')
            stats["file_types"][file_type] = stats["file_types"].get(file_type, 0) + 1

        return stats


# 便捷函数
def create_rag_system(documents_dir: str, vector_store_path: str = "vector_store", 
                     system_prompt: str = "", use_streaming: bool = True):
    """创建完整的RAG系统"""
    rag = RAGSystem(vector_store_path)
    
    # 加载文档
    rag.load_documents_from_directory(documents_dir)
    
    # 创建向量存储
    rag.create_vector_store()
    
    # 设置问答系统
    rag.setup_qa_system(system_prompt, use_streaming)
    
    return rag


def load_existing_rag_system(vector_store_path: str = "vector_store", 
                           system_prompt: str = "", use_streaming: bool = True):
    """加载现有的RAG系统"""
    rag = RAGSystem(vector_store_path)
    
    # 加载向量存储
    rag.load_existing_vector_store()
    
    # 设置问答系统
    rag.setup_qa_system(system_prompt, use_streaming)
    
    return rag


# 向后兼容的函数
def setup_streaming_qa_chain(vector_store, system_prompt: str = "", conversation_history=None):
    """向后兼容的函数"""
    from qa_chain import setup_streaming_qa_chain as _setup_streaming_qa_chain
    return _setup_streaming_qa_chain(vector_store, system_prompt, conversation_history)


if __name__ == "__main__":
    # 示例用法
    print("RAG系统示例")
    
    # 创建新的RAG系统
    try:
        rag = create_rag_system(
            documents_dir="documents",
            system_prompt="你是一个智能助手，专门帮助分析Excel数据。"
        )
        
        # 提问
        question = "文档中有哪些公司？"
        print(f"问题: {question}")
        
        if rag.streaming_handler:
            print("回答: ", end="")
            for token in rag.ask(question):
                print(token, end="", flush=True)
            print()
        else:
            answer = rag.ask(question)
            print(f"回答: {answer}")
            
    except Exception as e:
        print(f"错误: {e}")
        
        # 尝试加载现有系统
        try:
            rag = load_existing_rag_system(
                system_prompt="你是一个智能助手，专门帮助分析Excel数据。"
            )
            print("成功加载现有RAG系统")
        except Exception as e2:
            print(f"加载现有系统也失败: {e2}")
