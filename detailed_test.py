#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细的FastAPI测试脚本
"""

import requests
import json
import time


def test_health():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 健康检查失败: {response.text}")
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")


def test_conversation():
    """测试对话功能"""
    print("\n💬 测试对话功能...")
    
    # 1. 开始对话
    print("1️⃣ 开始对话...")
    try:
        start_payload = {
            "user_id": "test_user",
            "preferences": {}
        }
        response = requests.post(
            "http://localhost:8000/api/v1/conversation/start",
            json=start_payload
        )
        print(f"开始对话状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get('session_id')
            print(f"✅ 对话开始成功，会话ID: {session_id}")
            
            # 2. 发送消息
            print("\n2️⃣ 发送消息...")
            message_payload = {
                "session_id": session_id,
                "message": "我想找Python开发工程师的工作",
                "job_count": 3
            }
            
            response = requests.post(
                "http://localhost:8000/api/v1/conversation/message",
                json=message_payload
            )
            print(f"发送消息状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 消息发送成功")
                print(f"助手回复: {data.get('message', '')[:200]}...")
            else:
                print(f"❌ 消息发送失败")
                
        else:
            print(f"❌ 对话开始失败")
            
    except Exception as e:
        print(f"❌ 对话测试异常: {e}")


def test_rag():
    """测试RAG功能"""
    print("\n📚 测试RAG功能...")
    
    # 1. 测试RAG状态
    print("1️⃣ 测试RAG状态...")
    try:
        response = requests.get("http://localhost:8000/api/v1/rag/status")
        print(f"RAG状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ RAG状态正常")
            print(f"初始化状态: {data.get('is_initialized')}")
            print(f"文档统计: {data.get('document_stats', {})}")
        else:
            print(f"❌ RAG状态异常: {response.text}")
    except Exception as e:
        print(f"❌ RAG状态测试异常: {e}")
    
    # 2. 测试RAG查询
    print("\n2️⃣ 测试RAG查询...")
    try:
        query_payload = {
            "question": "有哪些Python开发工程师的职位？",
            "k": 3,
            "use_streaming": False
        }
        response = requests.post(
            "http://localhost:8000/api/v1/rag/query",
            json=query_payload
        )
        print(f"RAG查询状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ RAG查询成功")
            print(f"回答: {data.get('answer', '')[:200]}...")
            print(f"相关文档数: {len(data.get('relevant_documents', []))}")
        else:
            print(f"❌ RAG查询失败: {response.text}")
    except Exception as e:
        print(f"❌ RAG查询异常: {e}")
    
    # 3. 测试职位搜索
    print("\n3️⃣ 测试职位搜索...")
    try:
        search_payload = {
            "job_type": "Python开发工程师",
            "location": "北京",
            "salary": "15-25K",
            "limit": 5
        }
        response = requests.post(
            "http://localhost:8000/api/v1/rag/search/jobs",
            json=search_payload
        )
        print(f"职位搜索状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 职位搜索成功")
            print(f"找到职位数: {data.get('total_count', 0)}")
            results = data.get('results', [])
            for i, job in enumerate(results[:3], 1):
                print(f"  {i}. {job.get('job_title')} - {job.get('company_name')} - {job.get('salary')}")
        else:
            print(f"❌ 职位搜索失败: {response.text}")
    except Exception as e:
        print(f"❌ 职位搜索异常: {e}")


def test_api_docs():
    """测试API文档"""
    print("\n📖 测试API文档...")
    try:
        # 测试OpenAPI文档
        response = requests.get("http://localhost:8000/api/v1/openapi.json")
        print(f"OpenAPI文档状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ OpenAPI文档可访问")
        
        # 测试Swagger UI
        response = requests.get("http://localhost:8000/docs")
        print(f"Swagger UI状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ Swagger UI可访问")
            
        # 测试ReDoc
        response = requests.get("http://localhost:8000/redoc")
        print(f"ReDoc状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ ReDoc可访问")
            
    except Exception as e:
        print(f"❌ API文档测试异常: {e}")


def main():
    """主函数"""
    print("🚀 开始详细的FastAPI测试")
    print("=" * 50)
    
    test_health()
    test_conversation()
    test_rag()
    test_api_docs()
    
    print("\n" + "=" * 50)
    print("🎯 测试完成！")
    print("💡 提示: 你可以访问以下地址查看更多信息:")
    print("   - 主页: http://localhost:8000")
    print("   - API文档: http://localhost:8000/docs")
    print("   - ReDoc: http://localhost:8000/redoc")
    print("   - 健康检查: http://localhost:8000/health")


if __name__ == "__main__":
    main()
