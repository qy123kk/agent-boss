#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版求职助手 - 固定工作流模式
收集需求 → 搜索 → 输出完整结果 → 任务完成
"""

import re
from typing import List, Dict, Optional
from rag_core import load_existing_rag_system
from incremental_vector_store import IncrementalVectorStore


class SimpleJobFinder:
    """简化版求职助手"""
    
    def __init__(self):
        self.rag_system = None
        self.user_requirements = {}
        self.vector_manager = IncrementalVectorStore("vector_store")
        
    def initialize(self):
        """初始化系统"""
        try:
            print("🔄 正在初始化求职助手...")

            # 智能管理向量存储
            print("📊 检查向量存储状态...")
            success = self.vector_manager.create_or_update_vector_store('documents')
            if not success:
                print("❌ 向量存储初始化失败")
                return False

            # 加载RAG系统
            self.rag_system = load_existing_rag_system(use_streaming=False)
            print("✅ 求职助手初始化成功")
            return True
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            return False
    
    def start_job_search(self):
        """开始求职搜索流程"""
        print("🎯 欢迎使用智能求职助手！")
        print("我将帮您找到合适的工作机会，并提供完整的公司信息。")
        print("=" * 60)
        
        # 步骤1：收集需求
        self._collect_requirements()
        
        # 步骤2：执行搜索
        results = self._search_jobs()
        
        # 步骤3：输出完整结果
        if results:
            self._output_complete_results(results)
        else:
            print("😔 抱歉，没有找到符合您要求的职位。")
            print("💡 建议：可以适当放宽条件重新搜索。")
        
        print("\n🎉 求职搜索完成！感谢使用智能求职助手！")
    
    def _collect_requirements(self):
        """收集用户需求"""
        print("📝 请提供您的求职需求：")
        
        # 职位类型
        job_type = input("🔹 职位类型（如：Python开发、UI设计师、产品经理）: ").strip()
        if job_type:
            self.user_requirements['job_type'] = job_type
        
        # 期望薪资
        salary = input("💰 期望薪资（如：15-20K、20K以上）: ").strip()
        if salary:
            self.user_requirements['salary'] = salary
        
        # 学历要求
        education = input("🎓 学历背景（如：本科、大专、硕士）: ").strip()
        if education:
            self.user_requirements['education'] = education
        
        # 工作地点
        location = input("📍 工作地点（如：深圳、北京、上海）: ").strip()
        if location:
            self.user_requirements['location'] = location
        
        # 工作经验
        experience = input("⏰ 工作经验（如：1-3年、应届生、5年以上）: ").strip()
        if experience:
            self.user_requirements['experience'] = experience
        
        print(f"\n✅ 需求收集完成！正在为您搜索匹配的职位...")
        print("=" * 60)
    
    def _search_jobs(self) -> List:
        """执行职位搜索"""
        # 构建搜索查询
        search_query = self._build_search_query()
        print(f"🔍 搜索关键词: {search_query}")
        
        try:
            # 执行搜索，获取更多结果
            results = self.rag_system.search(search_query, k=8)
            print(f"✅ 找到 {len(results)} 个相关职位")
            return results
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return []
    
    def _build_search_query(self) -> str:
        """构建搜索查询"""
        query_parts = []
        
        if 'job_type' in self.user_requirements:
            query_parts.append(self.user_requirements['job_type'])
        
        if 'location' in self.user_requirements:
            query_parts.append(self.user_requirements['location'])
        
        if 'education' in self.user_requirements:
            query_parts.append(self.user_requirements['education'])
        
        return " ".join(query_parts) if query_parts else "职位"
    
    def _output_complete_results(self, results: List):
        """输出完整的搜索结果"""
        print("🎉 为您找到以下匹配的工作机会：")
        print("=" * 60)
        
        for i, doc in enumerate(results, 1):
            print(f"\n【职位 {i}】")
            print("=" * 40)
            
            metadata = doc.metadata
            structured_fields = metadata.get('structured_fields', {})
            
            # 核心职位信息
            print("🔹 核心信息:")
            print(f"  职位名称: {metadata.get('job_title', '未知')}")
            print(f"  公司名称: {metadata.get('company_name', '未知')}")
            print(f"  薪资待遇: {metadata.get('salary', '面议')}")
            print(f"  学历要求: {metadata.get('education', '未知')}")
            print(f"  工作经验: {metadata.get('experience', '未知')}")
            print(f"  工作地点: {metadata.get('location', '未知')}")
            print(f"  实习机会: {structured_fields.get('实习时间', '未知')}")
            print(f"  职位类型: {structured_fields.get('职位类型', '未知')}")
            
            # 详细职位描述
            job_info = structured_fields.get('职位信息', '')
            if job_info and job_info.strip():
                print(f"\n📝 职位详情:")
                # 格式化职位信息
                formatted_info = self._format_job_description(job_info)
                print(f"  {formatted_info}")
            
            # 完整公司信息
            print(f"\n🏢 公司详情:")
            print(f"  公司全称: {structured_fields.get('公司全称', '未知')}")
            print(f"  公司规模: {structured_fields.get('公司规模', '未知')}")
            print(f"  主营业务: {structured_fields.get('主营业务', '未知')}")
            print(f"  融资情况: {structured_fields.get('是否融资', '未知')}")
            print(f"  注册资金: {structured_fields.get('注册资金', '未知')}")
            print(f"  成立时间: {structured_fields.get('成立时间', '未知')}")
            print(f"  公司类型: {structured_fields.get('公司类型', '未知')}")
            print(f"  法定代表人: {structured_fields.get('法定代表人', '未知')}")
            print(f"  经营状态: {structured_fields.get('经营状态', '未知')}")
            
            # 福利待遇
            benefits = structured_fields.get('公司福利', '')
            if benefits and benefits.strip() and benefits != '[空]':
                print(f"\n🎁 福利待遇:")
                print(f"  {benefits}")
            
            # 地理位置
            longitude = structured_fields.get('经度', '')
            latitude = structured_fields.get('纬度', '')
            if longitude and latitude:
                print(f"\n📍 地理位置:")
                print(f"  经度: {longitude}")
                print(f"  纬度: {latitude}")
            
            print("\n" + "-" * 60)
        
        # 输出搜索总结
        self._output_search_summary(results)
    
    def _format_job_description(self, job_info: str) -> str:
        """格式化职位描述"""
        # 简单的格式化：按句号和分号分行
        formatted = job_info.replace('；', '\n    • ').replace('。', '\n    • ')
        # 移除空行和多余的符号
        lines = [line.strip() for line in formatted.split('\n') if line.strip()]
        return '\n  '.join(lines)
    
    def _output_search_summary(self, results: List):
        """输出搜索总结"""
        print(f"\n📊 搜索总结:")
        print(f"  共找到 {len(results)} 个职位")
        
        # 统计公司数量
        companies = set()
        locations = set()
        salary_ranges = []
        
        for doc in results:
            metadata = doc.metadata
            company = metadata.get('company_name', '')
            location = metadata.get('location', '')
            salary = metadata.get('salary', '')
            
            if company:
                companies.add(company)
            if location:
                locations.add(location)
            if salary:
                salary_ranges.append(salary)
        
        print(f"  涉及公司: {len(companies)} 家")
        print(f"  工作地点: {', '.join(list(locations)[:5])}")
        if len(locations) > 5:
            print(f"    等 {len(locations)} 个地区")
        
        print(f"\n💡 建议:")
        print(f"  • 仔细阅读职位详情和公司信息")
        print(f"  • 重点关注福利待遇和公司发展前景")
        print(f"  • 可以根据地理位置选择合适的工作地点")


def main():
    """主函数"""
    finder = SimpleJobFinder()
    
    if not finder.initialize():
        print("❌ 系统初始化失败")
        return
    
    try:
        finder.start_job_search()
    except KeyboardInterrupt:
        print("\n\n👋 搜索被用户中断，感谢使用！")
    except Exception as e:
        print(f"\n❌ 搜索过程中出现错误: {e}")


if __name__ == "__main__":
    main()
