#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI应用测试脚本
"""

import requests
import json
import time
from typing import Dict, Any


class FastAPITester:
    """FastAPI应用测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.session = requests.Session()
        
    def test_health_check(self) -> bool:
        """测试健康检查"""
        try:
            print("🔍 测试健康检查...")
            response = self.session.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 健康检查通过: {data['status']}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False
    
    def test_conversation_flow(self) -> bool:
        """测试对话流程"""
        try:
            print("\n🗣️ 测试对话流程...")
            
            # 1. 开始对话
            start_data = {"user_id": "test_user"}
            response = self.session.post(
                f"{self.api_base}/conversation/start",
                json=start_data
            )
            
            if response.status_code != 200:
                print(f"❌ 开始对话失败: {response.status_code}")
                return False
            
            start_result = response.json()
            session_id = start_result["session_id"]
            print(f"✅ 对话已开始: {session_id}")
            print(f"📝 欢迎消息: {start_result['message']}")
            
            # 2. 发送消息
            messages = [
                "我想找Python开发工程师的工作",
                "我希望在深圳工作",
                "薪资期望15K到20K"
            ]
            
            for message in messages:
                print(f"\n👤 用户: {message}")
                
                msg_data = {
                    "session_id": session_id,
                    "message": message,
                    "job_count": 3
                }
                
                response = self.session.post(
                    f"{self.api_base}/conversation/message",
                    json=msg_data
                )
                
                if response.status_code != 200:
                    print(f"❌ 发送消息失败: {response.status_code}")
                    return False
                
                result = response.json()
                print(f"🤖 助手: {result['message']}")
                
                if result.get("search_results"):
                    print(f"🎯 找到 {len(result['search_results'])} 个职位")
                
                time.sleep(1)  # 避免请求过快
            
            print("✅ 对话流程测试完成")
            return True
            
        except Exception as e:
            print(f"❌ 对话流程测试异常: {e}")
            return False
    
    def test_rag_query(self) -> bool:
        """测试RAG查询"""
        try:
            print("\n🔍 测试RAG查询...")
            
            query_data = {
                "question": "有哪些Python开发的职位？",
                "k": 3
            }
            
            response = self.session.post(
                f"{self.api_base}/rag/query",
                json=query_data
            )
            
            if response.status_code != 200:
                print(f"❌ RAG查询失败: {response.status_code}")
                return False
            
            result = response.json()
            print(f"✅ RAG查询成功")
            print(f"❓ 问题: {result['question']}")
            print(f"💬 回答: {result['answer'][:100]}...")
            print(f"📄 相关文档: {len(result['relevant_documents'])} 个")
            
            return True
            
        except Exception as e:
            print(f"❌ RAG查询测试异常: {e}")
            return False
    
    def test_job_search(self) -> bool:
        """测试职位搜索"""
        try:
            print("\n💼 测试职位搜索...")
            
            search_data = {
                "job_type": "Python开发工程师",
                "location": "深圳",
                "salary": "15K-20K",
                "limit": 5
            }
            
            response = self.session.post(
                f"{self.api_base}/rag/search/jobs",
                json=search_data
            )
            
            if response.status_code != 200:
                print(f"❌ 职位搜索失败: {response.status_code}")
                return False
            
            result = response.json()
            print(f"✅ 职位搜索成功")
            print(f"🎯 找到 {result['total_count']} 个职位")
            
            for job in result['results'][:2]:  # 显示前2个
                print(f"  📍 {job['company_name']} - {job['job_title']}")
                print(f"     💰 {job['salary']} | 📍 {job['location']}")
            
            return True
            
        except Exception as e:
            print(f"❌ 职位搜索测试异常: {e}")
            return False
    
    def test_system_status(self) -> bool:
        """测试系统状态"""
        try:
            print("\n📊 测试系统状态...")
            
            # RAG系统状态
            response = self.session.get(f"{self.api_base}/rag/status")
            
            if response.status_code != 200:
                print(f"❌ 获取RAG状态失败: {response.status_code}")
                return False
            
            rag_status = response.json()
            print(f"✅ RAG系统状态: {'已初始化' if rag_status['is_initialized'] else '未初始化'}")
            print(f"📄 文档总数: {rag_status['document_stats']['total_documents']}")
            
            # 详细健康检查
            response = self.session.get(f"{self.api_base}/health/detailed")
            
            if response.status_code == 200:
                health = response.json()
                print(f"💻 CPU使用率: {health['system_info']['cpu_percent']:.1f}%")
                print(f"💾 内存使用率: {health['system_info']['memory_percent']:.1f}%")
            
            return True
            
        except Exception as e:
            print(f"❌ 系统状态测试异常: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """运行所有测试"""
        print("🧪 开始FastAPI应用测试")
        print("=" * 50)
        
        tests = {
            "健康检查": self.test_health_check,
            "对话流程": self.test_conversation_flow,
            "RAG查询": self.test_rag_query,
            "职位搜索": self.test_job_search,
            "系统状态": self.test_system_status
        }
        
        results = {}
        
        for test_name, test_func in tests.items():
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name}测试异常: {e}")
                results[test_name] = False
        
        print("\n" + "=" * 50)
        print("📋 测试结果汇总:")
        
        for test_name, passed in results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"  {test_name}: {status}")
        
        passed_count = sum(results.values())
        total_count = len(results)
        print(f"\n🎯 总体结果: {passed_count}/{total_count} 测试通过")
        
        return results


def main():
    """主函数"""
    tester = FastAPITester()
    results = tester.run_all_tests()
    
    # 返回退出码
    if all(results.values()):
        print("\n🎉 所有测试通过！")
        exit(0)
    else:
        print("\n⚠️ 部分测试失败，请检查日志")
        exit(1)


if __name__ == "__main__":
    main()
