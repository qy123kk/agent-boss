#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量存储模块
负责创建、保存和加载向量存储
"""

import os
from typing import List
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain.schema import Document

# 加载环境变量
load_dotenv()


def get_api_key():
    """获取API密钥"""
    api_key = os.getenv("DASHSCOPE_API_KEY", "sk-ea76fba3b52045579e38a398598ff512")
    if not api_key:
        raise ValueError("请设置DASHSCOPE_API_KEY环境变量")
    return api_key


def create_embeddings():
    """创建嵌入模型"""
    api_key = get_api_key()
    return DashScopeEmbeddings(
        model="text-embedding-v1",
        dashscope_api_key=api_key
    )


def create_vector_store(chunks: List[Document], save_path: str):
    """使用文本块创建向量存储并保存到本地"""
    embeddings = create_embeddings()
    vector_store = FAISS.from_documents(chunks, embeddings)
    # 将向量存储保存到磁盘
    vector_store.save_local(save_path)
    return vector_store


def load_vector_store(load_path: str):
    """从本地加载向量存储"""
    embeddings = create_embeddings()
    return FAISS.load_local(load_path, embeddings, allow_dangerous_deserialization=True)


def search_documents(vector_store, query: str, k: int = 3):
    """在向量存储中搜索相关文档"""
    return vector_store.similarity_search(query, k=k)


def search_documents_with_score(vector_store, query: str, k: int = 3):
    """在向量存储中搜索相关文档，返回相似度分数"""
    return vector_store.similarity_search_with_score(query, k=k)


def create_optimized_retriever(vector_store, search_type: str = "similarity", k: int = 4):
    """创建优化的检索器"""
    return vector_store.as_retriever(
        search_type=search_type,
        search_kwargs={"k": k}
    )
