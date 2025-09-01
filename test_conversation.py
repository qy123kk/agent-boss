#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试对话API
"""

import requests
import json


def test_conversation():
    """测试完整的对话流程"""
    print("💬 测试对话API...")
    
    # 1. 开始对话
    print("1️⃣ 开始对话...")
    start_payload = {
        "user_id": "test_user",
        "preferences": {}
    }
    
    response = requests.post(
        "http://localhost:8000/api/v1/conversation/start",
        json=start_payload,
        timeout=10
    )
    
    print(f"开始对话状态码: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ 开始对话失败: {response.text}")
        return
    
    data = response.json()
    session_id = data.get('session_id')
    print(f"✅ 对话开始成功，会话ID: {session_id}")
    print(f"欢迎消息: {data.get('message')}")
    print(f"进度: {data.get('progress')}")
    
    # 2. 发送消息
    print("\n2️⃣ 发送消息...")
    message_payload = {
        "session_id": session_id,
        "message": "我想找Python开发工程师的工作",
        "job_count": 3
    }
    
    response = requests.post(
        "http://localhost:8000/api/v1/conversation/message",
        json=message_payload,
        timeout=15
    )
    
    print(f"发送消息状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("✅ 消息发送成功")
        print(f"助手回复: {data.get('message', '')[:200]}...")
        print(f"当前阶段: {data.get('stage')}")
        print(f"进度: {data.get('progress')}")
        print(f"理解置信度: {data.get('confidence')}")
    else:
        print(f"❌ 消息发送失败: {response.text}")
        return
    
    # 3. 继续对话 - 地点
    print("\n3️⃣ 继续对话 - 地点...")
    message_payload = {
        "session_id": session_id,
        "message": "我希望在北京工作",
        "job_count": 3
    }
    
    response = requests.post(
        "http://localhost:8000/api/v1/conversation/message",
        json=message_payload,
        timeout=15
    )
    
    print(f"发送消息状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("✅ 消息发送成功")
        print(f"助手回复: {data.get('message', '')[:200]}...")
        print(f"当前阶段: {data.get('stage')}")
        print(f"进度: {data.get('progress')}")
    else:
        print(f"❌ 消息发送失败: {response.text}")
        return
    
    # 4. 继续对话 - 薪资
    print("\n4️⃣ 继续对话 - 薪资...")
    message_payload = {
        "session_id": session_id,
        "message": "薪资期望15-25K",
        "job_count": 3
    }
    
    response = requests.post(
        "http://localhost:8000/api/v1/conversation/message",
        json=message_payload,
        timeout=20
    )
    
    print(f"发送消息状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("✅ 消息发送成功")
        print(f"助手回复: {data.get('message', '')[:200]}...")
        print(f"当前阶段: {data.get('stage')}")
        print(f"进度: {data.get('progress')}")
        
        # 检查是否有搜索结果
        search_results = data.get('search_results')
        if search_results:
            print(f"\n🎉 找到 {len(search_results)} 个匹配职位:")
            for i, job in enumerate(search_results, 1):
                print(f"  {i}. {job.get('job_title')} - {job.get('company_name')} - {job.get('salary')}")
    else:
        print(f"❌ 消息发送失败: {response.text}")


if __name__ == "__main__":
    test_conversation()
