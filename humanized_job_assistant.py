#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人性化求职助手 - 主系统
集成对话工作流和RAG检索功能，提供完整的求职服务
"""

from typing import Dict, List, Optional, Any
from conversation_workflow import ConversationWorkflowEngine
from rag_core import load_existing_rag_system
from incremental_vector_store import IncrementalVectorStore
from hybrid_retrieval_system import HybridRetrievalSystem
import json
import time


class HumanizedJobAssistant:
    """人性化求职助手主类"""
    
    def __init__(self, vector_store_path: str = "vector_store", documents_dir: str = "documents"):
        self.vector_store_path = vector_store_path
        self.documents_dir = documents_dir
        self.workflow_engine = ConversationWorkflowEngine()
        self.rag_system = None
        self.hybrid_retrieval = None
        self.vector_manager = IncrementalVectorStore(vector_store_path)
        self.is_initialized = False
        
    def initialize(self) -> Dict[str, Any]:
        """初始化系统"""
        try:
            print("🔄 正在初始化人性化求职助手...")
            
            # 1. 智能管理向量存储
            print("📊 检查向量存储状态...")
            success = self.vector_manager.create_or_update_vector_store(self.documents_dir)
            if not success:
                return {
                    "success": False,
                    "error": "向量存储初始化失败",
                    "details": "无法创建或更新向量存储"
                }
            
            # 2. 加载RAG系统
            print("🤖 加载RAG系统...")
            self.rag_system = load_existing_rag_system(
                vector_store_path=self.vector_store_path,
                system_prompt="你是一个专业的求职顾问，专门帮助分析职位信息。",
                use_streaming=False
            )

            # 3. 初始化混合检索系统
            print("💰 初始化混合检索系统...")
            self.hybrid_retrieval = HybridRetrievalSystem(
                vector_store_path=self.vector_store_path,
                documents_dir=self.documents_dir,
                salary_tolerance=0.2  # 20%薪资容忍度
            )
            self.hybrid_retrieval.rag_system = self.rag_system  # 复用已加载的RAG系统

            # 4. 获取系统统计信息
            stats = self._get_system_stats()
            
            self.is_initialized = True
            print("✅ 人性化求职助手初始化成功！")
            
            return {
                "success": True,
                "message": "系统初始化成功",
                "stats": stats
            }
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "details": "系统初始化过程中出现错误"
            }
    
    def start_conversation(self) -> Dict[str, Any]:
        """开始新的对话"""
        if not self.is_initialized:
            return {
                "success": False,
                "error": "系统未初始化",
                "message": "请先调用initialize()方法初始化系统"
            }
        
        greeting = self.workflow_engine.start_conversation()
        
        return {
            "success": True,
            "message": greeting,
            "stage": "greeting",
            "progress": {
                "percentage": 0,
                "completed_fields": 0,
                "total_required_fields": 3
            }
        }
    
    def process_message(self, user_message: str, job_count: int = 3) -> Dict[str, Any]:
        """处理用户消息"""
        if not self.is_initialized:
            return {
                "success": False,
                "error": "系统未初始化"
            }
        
        if not user_message.strip():
            return {
                "success": False,
                "error": "消息不能为空"
            }
        
        try:
            # 处理用户输入
            workflow_result = self.workflow_engine.process_user_input(user_message)
            
            # 检查是否准备好搜索
            if workflow_result.get("ready_for_search", False):
                # 执行搜索
                search_result = self._perform_job_search(job_count)
                
                if search_result["success"]:
                    return {
                        "success": True,
                        "message": workflow_result["response"],
                        "stage": "search_completed",
                        "progress": workflow_result["progress"],
                        "search_results": search_result["results"],
                        "search_summary": search_result["summary"]
                    }
                else:
                    return {
                        "success": True,
                        "message": workflow_result["response"] + "\n\n❌ 搜索过程中出现问题：" + search_result["error"],
                        "stage": workflow_result["stage"],
                        "progress": workflow_result["progress"]
                    }
            
            # 正常的对话流程
            return {
                "success": True,
                "message": workflow_result["response"],
                "stage": workflow_result["stage"],
                "progress": workflow_result["progress"],
                "extracted_info": workflow_result.get("extracted_info", {}),
                "confidence": workflow_result.get("confidence", 0.0)
            }
            
        except Exception as e:
            print(f"处理消息时出错: {e}")
            return {
                "success": False,
                "error": f"处理消息时出错: {str(e)}"
            }
    
    def _perform_job_search(self, job_count: int = 3) -> Dict[str, Any]:
        """执行职位搜索 - 使用混合检索系统"""
        try:
            # 获取用户需求
            req = self.workflow_engine.state_manager.requirements

            print(f"🔍 混合检索: {req.job_type} | {req.location} | {req.salary}")

            # 使用混合检索系统
            hybrid_results = self.hybrid_retrieval.search_jobs(
                job_type=req.job_type or "",
                location=req.location or "",
                salary_requirement=req.salary or "",
                k=job_count,
                vector_k_multiplier=3  # 向量检索job_count*3个候选，然后薪资过滤
            )

            if not hybrid_results:
                return {
                    "success": False,
                    "error": "没有找到匹配的职位",
                    "results": [],
                    "summary": {}
                }

            # 转换为原格式并添加薪资匹配信息
            search_results = []
            for result in hybrid_results:
                doc = result["document"]
                # 添加薪资匹配信息到metadata
                doc.metadata["salary_match_score"] = result["salary_match_score"]
                doc.metadata["salary_match_type"] = result["salary_match_type"]
                search_results.append(doc)

            # 格式化搜索结果
            formatted_results = self._format_search_results(search_results)

            # 生成搜索摘要
            summary = self._generate_search_summary(search_results)

            return {
                "success": True,
                "results": formatted_results,
                "summary": summary,
                "total_found": len(search_results),
                "search_method": "混合检索(向量+薪资过滤)"
            }
            
        except Exception as e:
            print(f"搜索失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "summary": {}
            }
    
    def _format_search_results(self, search_results: List) -> List[Dict[str, Any]]:
        """格式化搜索结果"""
        formatted_results = []
        
        for i, doc in enumerate(search_results, 1):
            metadata = doc.metadata
            structured_fields = metadata.get('structured_fields', {})
            
            # 提取核心信息
            job_info = {
                "rank": i,
                "job_title": metadata.get('job_title', '未知职位'),
                "company_name": metadata.get('company_name', '未知公司'),
                "salary": metadata.get('salary', '面议'),
                "location": metadata.get('location', '未知'),
                "education": metadata.get('education', '未知'),
                "experience": metadata.get('experience', '未知'),
                
                # 详细信息
                "job_description": structured_fields.get('职位信息', ''),
                "company_full_name": structured_fields.get('公司全称', ''),
                "company_size": structured_fields.get('公司规模', ''),
                "company_business": structured_fields.get('主营业务', ''),
                "company_benefits": structured_fields.get('公司福利', ''),
                "internship_time": structured_fields.get('实习时间', ''),
                "job_type": structured_fields.get('职位类型', ''),
                
                # 地理信息
                "longitude": structured_fields.get('经度', ''),
                "latitude": structured_fields.get('纬度', ''),
                
                # 原始文档内容（用于详细展示）
                "full_content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content
            }
            
            formatted_results.append(job_info)
        
        return formatted_results
    
    def _generate_search_summary(self, search_results: List) -> Dict[str, Any]:
        """生成搜索摘要"""
        if not search_results:
            return {}
        
        companies = set()
        locations = set()
        salary_ranges = []
        job_types = set()
        
        for doc in search_results:
            metadata = doc.metadata
            structured_fields = metadata.get('structured_fields', {})
            
            # 统计公司
            company = metadata.get('company_name', '')
            if company:
                companies.add(company)
            
            # 统计地点
            location = metadata.get('location', '')
            if location:
                locations.add(location)
            
            # 统计薪资
            salary = metadata.get('salary', '')
            if salary:
                salary_ranges.append(salary)
            
            # 统计职位类型
            job_type = structured_fields.get('职位类型', '')
            if job_type:
                job_types.add(job_type)
        
        return {
            "total_positions": len(search_results),
            "unique_companies": len(companies),
            "company_list": list(companies),
            "locations": list(locations),
            "salary_ranges": salary_ranges,
            "job_types": list(job_types)
        }
    
    def get_job_details(self, job_rank: int) -> Dict[str, Any]:
        """获取特定职位的详细信息"""
        # 这里可以实现获取特定职位详情的逻辑
        # 目前返回基本结构
        return {
            "success": True,
            "message": f"职位 {job_rank} 的详细信息"
        }
    
    def restart_conversation(self) -> Dict[str, Any]:
        """重新开始对话"""
        self.workflow_engine.reset_conversation()
        return self.start_conversation()
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.workflow_engine.get_conversation_state().get("conversation_history", [])
    
    def get_current_requirements(self) -> Dict[str, Any]:
        """获取当前收集的需求信息"""
        state = self.workflow_engine.get_conversation_state()
        return state.get("requirements", {})
    
    def _get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            # 获取向量存储统计
            metadata = self.vector_manager._load_metadata()
            
            # 获取RAG系统统计
            rag_stats = self.rag_system.get_document_stats() if self.rag_system else {}
            
            return {
                "vector_store": {
                    "total_documents": metadata.get('total_documents', 0) if metadata else 0,
                    "total_chunks": metadata.get('total_chunks', 0) if metadata else 0,
                    "last_update": metadata.get('last_update', '未知') if metadata else '未知'
                },
                "rag_system": rag_stats,
                "workflow_engine": {
                    "initialized": True,
                    "supported_stages": [stage.value for stage in self.workflow_engine.state_manager.stage.__class__]
                }
            }
        except Exception as e:
            print(f"获取系统统计失败: {e}")
            return {}


# 便捷函数
def create_humanized_job_assistant(vector_store_path: str = "vector_store", 
                                 documents_dir: str = "documents") -> HumanizedJobAssistant:
    """创建人性化求职助手实例"""
    assistant = HumanizedJobAssistant(vector_store_path, documents_dir)
    return assistant


# 命令行测试接口
def main():
    """命令行测试接口"""
    print("🤖 人性化求职助手 - 命令行测试")
    print("=" * 50)
    
    # 创建助手
    assistant = create_humanized_job_assistant()
    
    # 初始化
    init_result = assistant.initialize()
    if not init_result["success"]:
        print(f"❌ 初始化失败: {init_result['error']}")
        return
    
    print(f"✅ 初始化成功")
    if "stats" in init_result:
        stats = init_result["stats"]
        print(f"📊 系统统计: 文档 {stats.get('vector_store', {}).get('total_documents', 0)} 个")
    
    # 开始对话
    start_result = assistant.start_conversation()
    if start_result["success"]:
        print(f"\n🤖 助手: {start_result['message']}")
    
    # 交互循环
    while True:
        try:
            user_input = input("\n👤 您: ").strip()
            
            if user_input.lower() in ['退出', 'quit', 'exit']:
                print("👋 感谢使用人性化求职助手！")
                break
            
            if user_input.lower() in ['重新开始', 'restart']:
                restart_result = assistant.restart_conversation()
                if restart_result["success"]:
                    print(f"\n🤖 助手: {restart_result['message']}")
                continue
            
            # 处理用户消息
            result = assistant.process_message(user_input)
            
            if result["success"]:
                print(f"\n🤖 助手: {result['message']}")
                
                # 显示进度
                if "progress" in result:
                    progress = result["progress"]
                    print(f"📊 进度: {progress.get('progress_percentage', 0):.0f}% ({progress.get('completed_fields', 0)}/{progress.get('total_required_fields', 3)})")
                
                # 显示搜索结果
                if "search_results" in result:
                    print(f"\n🎉 为您找到 {len(result['search_results'])} 个匹配的职位：")
                    for job in result["search_results"]:
                        print(f"\n【职位 {job['rank']}】")
                        print(f"  🏢 {job['company_name']}")
                        print(f"  💼 {job['job_title']}")
                        print(f"  💰 {job['salary']}")
                        print(f"  📍 {job['location']}")
            else:
                print(f"❌ 错误: {result.get('error', '未知错误')}")
                
        except KeyboardInterrupt:
            print("\n\n👋 感谢使用人性化求职助手！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")


if __name__ == "__main__":
    main()
