#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试RAG状态API
"""

import requests
import json


def test_rag_status():
    """测试RAG状态"""
    print("📚 测试RAG状态API...")
    try:
        response = requests.get("http://localhost:8000/api/v1/rag/status", timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ RAG状态获取成功")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ RAG状态获取失败: {response.text}")
            
    except Exception as e:
        print(f"❌ RAG状态测试异常: {e}")


if __name__ == "__main__":
    test_rag_status()
