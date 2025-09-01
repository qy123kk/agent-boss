#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合检索系统
第一阶段：向量检索（语义匹配职位和地点）
第二阶段：关键词+数值范围过滤（精确薪资匹配）
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from rag_core import load_existing_rag_system
from incremental_vector_store import IncrementalVectorStore


class SalaryFilter:
    """薪资过滤器 - 基于关键词和数值范围"""
    
    def __init__(self, tolerance_ratio: float = 0.2):
        """
        初始化薪资过滤器
        
        Args:
            tolerance_ratio: 薪资容忍比例，例如0.2表示上下浮动20%
        """
        self.tolerance_ratio = tolerance_ratio
    
    def parse_salary_number(self, salary_text: str) -> Optional[Tuple[int, int]]:
        """
        解析薪资文本，返回最小值和最大值（月薪，单位：元）
        
        Args:
            salary_text: 薪资文本，如"10-15K"、"月薪12000"等
            
        Returns:
            (min_salary, max_salary) 或 None
        """
        if not salary_text or salary_text.strip() in ['面议', '薪资面议', '待遇面议']:
            return None
        
        salary_text = salary_text.strip().lower()
        
        # 薪资解析模式（按优先级排序）
        patterns = [
            # 1. 范围格式: 10-15K, 10-15万, 10K-15K
            (r'(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)[kK万]', self._parse_range_k_wan),
            (r'(\d+(?:\.\d+)?)[kK万]-(\d+(?:\.\d+)?)[kK万]', self._parse_range_k_wan),
            
            # 2. 以上格式: 10K以上, 10万以上
            (r'(\d+(?:\.\d+)?)[kK万]以上', self._parse_above_k_wan),
            
            # 3. 左右格式: 10K左右, 10万左右
            (r'(\d+(?:\.\d+)?)[kK万]左右', self._parse_around_k_wan),
            
            # 4. 单一数值: 10K, 10万
            (r'(\d+(?:\.\d+)?)[kK万](?![-以左右])', self._parse_single_k_wan),
            
            # 5. 千元格式: 8千-12千, 10千
            (r'(\d+(?:\.\d+)?)千-(\d+(?:\.\d+)?)千', self._parse_range_thousand),
            (r'(\d+(?:\.\d+)?)千', self._parse_single_thousand),
            
            # 6. 月薪格式: 月薪12000
            (r'月薪(\d+)', self._parse_monthly),
            
            # 7. 年薪格式: 年薪30万, 年薪300000
            (r'年薪(\d+(?:\.\d+)?)万', self._parse_annual_wan),
            (r'年薪(\d+)', self._parse_annual),
            
            # 8. 纯数字范围: 10000-15000
            (r'(\d+)-(\d+)(?![kK万千])', self._parse_range_number),
            
            # 9. 带薪字数: 25-50K·16薪
            (r'(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)[kK万]·\d+薪', self._parse_range_k_wan_with_months),
        ]
        
        for pattern, parser in patterns:
            match = re.search(pattern, salary_text)
            if match:
                try:
                    result = parser(match, salary_text)
                    if result:
                        return result
                except:
                    continue
        
        return None
    
    def _parse_range_k_wan(self, match, salary_text):
        """解析范围格式：10-15K, 10-15万"""
        min_val, max_val = float(match.group(1)), float(match.group(2))
        if '万' in salary_text:
            return (int(min_val * 10000), int(max_val * 10000))
        else:  # K
            return (int(min_val * 1000), int(max_val * 1000))
    
    def _parse_above_k_wan(self, match, salary_text):
        """解析以上格式：10K以上"""
        val = float(match.group(1))
        if '万' in salary_text:
            min_val = int(val * 10000)
            return (min_val, min_val * 3)  # 设置一个合理的上限
        else:  # K
            min_val = int(val * 1000)
            return (min_val, min_val * 3)
    
    def _parse_around_k_wan(self, match, salary_text):
        """解析左右格式：10K左右"""
        val = float(match.group(1))
        if '万' in salary_text:
            center = int(val * 10000)
        else:  # K
            center = int(val * 1000)
        
        tolerance = int(center * self.tolerance_ratio)
        return (center - tolerance, center + tolerance)
    
    def _parse_single_k_wan(self, match, salary_text):
        """解析单一数值：10K, 10万"""
        val = float(match.group(1))
        if '万' in salary_text:
            salary = int(val * 10000)
        else:  # K
            salary = int(val * 1000)
        
        tolerance = int(salary * self.tolerance_ratio)
        return (salary - tolerance, salary + tolerance)
    
    def _parse_range_thousand(self, match, salary_text):
        """解析千元范围：8千-12千"""
        min_val, max_val = float(match.group(1)), float(match.group(2))
        return (int(min_val * 1000), int(max_val * 1000))
    
    def _parse_single_thousand(self, match, salary_text):
        """解析单一千元：10千"""
        val = float(match.group(1))
        salary = int(val * 1000)
        tolerance = int(salary * self.tolerance_ratio)
        return (salary - tolerance, salary + tolerance)
    
    def _parse_monthly(self, match, salary_text):
        """解析月薪：月薪12000"""
        salary = int(match.group(1))
        tolerance = int(salary * self.tolerance_ratio)
        return (salary - tolerance, salary + tolerance)
    
    def _parse_annual_wan(self, match, salary_text):
        """解析年薪万元：年薪30万"""
        annual = float(match.group(1)) * 10000
        monthly = int(annual / 12)
        tolerance = int(monthly * self.tolerance_ratio)
        return (monthly - tolerance, monthly + tolerance)
    
    def _parse_annual(self, match, salary_text):
        """解析年薪：年薪300000"""
        annual = int(match.group(1))
        monthly = int(annual / 12)
        tolerance = int(monthly * self.tolerance_ratio)
        return (monthly - tolerance, monthly + tolerance)
    
    def _parse_range_number(self, match, salary_text):
        """解析纯数字范围：10000-15000"""
        min_val, max_val = int(match.group(1)), int(match.group(2))
        return (min_val, max_val)
    
    def _parse_range_k_wan_with_months(self, match, salary_text):
        """解析带薪字数：25-50K·16薪"""
        min_val, max_val = float(match.group(1)), float(match.group(2))
        if '万' in salary_text:
            return (int(min_val * 10000), int(max_val * 10000))
        else:  # K
            return (int(min_val * 1000), int(max_val * 1000))
    
    def is_salary_match(self, user_salary: str, job_salary: str) -> Tuple[bool, float, str]:
        """
        判断薪资是否匹配
        
        Args:
            user_salary: 用户期望薪资
            job_salary: 职位薪资
            
        Returns:
            (是否匹配, 匹配度分数, 匹配类型)
        """
        user_range = self.parse_salary_number(user_salary)
        job_range = self.parse_salary_number(job_salary)
        
        # 处理面议情况
        if not user_range and not job_range:
            return (True, 0.5, "双方面议")
        elif not user_range:
            return (True, 0.4, "用户面议")
        elif not job_range:
            return (True, 0.3, "职位面议")
        
        user_min, user_max = user_range
        job_min, job_max = job_range
        
        # 计算重叠区间
        overlap_min = max(user_min, job_min)
        overlap_max = min(user_max, job_max)
        
        if overlap_min <= overlap_max:
            # 有重叠
            overlap_size = overlap_max - overlap_min
            user_size = user_max - user_min
            job_size = job_max - job_min
            
            # 计算重叠比例（相对于用户期望范围）
            if user_size > 0:
                overlap_ratio = overlap_size / user_size
            else:
                overlap_ratio = 1.0
            
            # 判断匹配类型
            if overlap_ratio >= 0.8:
                return (True, overlap_ratio, "完全匹配")
            elif overlap_ratio >= 0.5:
                return (True, overlap_ratio, "高度匹配")
            elif overlap_ratio >= 0.3:
                return (True, overlap_ratio, "部分匹配")
            else:
                return (True, overlap_ratio, "轻微匹配")
        else:
            # 无重叠，检查是否在容忍范围内
            if job_max < user_min:
                gap = user_min - job_max
                gap_ratio = gap / user_min if user_min > 0 else 1.0
                if gap_ratio <= self.tolerance_ratio:
                    return (True, 0.2, "略低于期望")
            elif job_min > user_max:
                gap = job_min - user_max
                gap_ratio = gap / user_max if user_max > 0 else 1.0
                if gap_ratio <= self.tolerance_ratio:
                    return (True, 0.2, "略高于期望")
            
            return (False, 0.0, "薪资不匹配")


class HybridRetrievalSystem:
    """混合检索系统：向量检索 + 薪资关键词过滤"""
    
    def __init__(self, vector_store_path: str = "vector_store", documents_dir: str = "documents", 
                 salary_tolerance: float = 0.2):
        """
        初始化混合检索系统
        
        Args:
            vector_store_path: 向量存储路径
            documents_dir: 文档目录
            salary_tolerance: 薪资容忍度（例如0.2表示上下浮动20%）
        """
        self.vector_store_path = vector_store_path
        self.documents_dir = documents_dir
        self.rag_system = None
        self.vector_manager = IncrementalVectorStore(vector_store_path)
        self.salary_filter = SalaryFilter(salary_tolerance)
        
    def initialize(self) -> bool:
        """初始化系统"""
        try:
            print("🔄 初始化混合检索系统...")
            
            # 初始化向量存储
            success = self.vector_manager.create_or_update_vector_store(self.documents_dir)
            if not success:
                print("❌ 向量存储初始化失败")
                return False
            
            # 加载RAG系统
            self.rag_system = load_existing_rag_system(
                vector_store_path=self.vector_store_path,
                use_streaming=False
            )
            
            print("✅ 混合检索系统初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            return False
    
    def search_jobs(self, job_type: str, location: str, salary_requirement: str, 
                   k: int = 3, vector_k_multiplier: int = 3) -> List[Dict[str, Any]]:
        """
        混合检索：向量检索 + 薪资过滤
        
        Args:
            job_type: 职位类型
            location: 工作地点  
            salary_requirement: 薪资要求
            k: 最终返回结果数量
            vector_k_multiplier: 向量检索倍数（检索k*multiplier个候选，然后薪资过滤）
            
        Returns:
            匹配的职位列表
        """
        try:
            print(f"🔍 混合检索: {job_type} | {location} | {salary_requirement}")
            
            # 第一阶段：向量检索（不包含薪资，避免数值干扰）
            vector_query = f"{job_type} {location}".strip()
            print(f"📊 第一阶段 - 向量检索: {vector_query}")
            
            # 检索更多候选结果
            vector_k = k * vector_k_multiplier
            vector_results = self.rag_system.search(vector_query, k=vector_k)
            print(f"✅ 向量检索获得 {len(vector_results)} 个候选职位")
            
            if not vector_results:
                return []
            
            # 第二阶段：薪资关键词过滤
            print(f"💰 第二阶段 - 薪资过滤: {salary_requirement}")
            
            filtered_results = []
            for doc in vector_results:
                metadata = doc.metadata
                job_salary = metadata.get('salary', '面议')
                
                # 薪资匹配检查
                is_match, match_score, match_type = self.salary_filter.is_salary_match(
                    salary_requirement, job_salary
                )
                
                if is_match:
                    result_item = {
                        "document": doc,
                        "job_title": metadata.get('job_title', '未知'),
                        "company_name": metadata.get('company_name', '未知'),
                        "salary": job_salary,
                        "location": metadata.get('location', '未知'),
                        "salary_match_score": match_score,
                        "salary_match_type": match_type,
                        "user_salary": salary_requirement,
                        "structured_fields": metadata.get('structured_fields', {})
                    }
                    filtered_results.append(result_item)
            
            # 按薪资匹配度排序
            filtered_results.sort(key=lambda x: x["salary_match_score"], reverse=True)
            
            # 返回前k个结果
            final_results = filtered_results[:k]
            
            print(f"✅ 薪资过滤后返回 {len(final_results)} 个匹配职位")
            
            return final_results
            
        except Exception as e:
            print(f"❌ 混合检索失败: {e}")
            return []


def test_hybrid_retrieval():
    """测试混合检索系统"""
    print("🧪 混合检索系统测试")
    print("=" * 60)
    
    # 初始化系统
    hybrid_system = HybridRetrievalSystem(salary_tolerance=0.2)  # 20%容忍度
    if not hybrid_system.initialize():
        print("❌ 系统初始化失败")
        return
    
    # 测试用例
    test_cases = [
        {
            "name": "精确薪资匹配",
            "job_type": "Python开发工程师",
            "location": "深圳", 
            "salary": "15K",
            "description": "测试15K是否能匹配15-20K等范围"
        },
        {
            "name": "范围薪资匹配",
            "job_type": "Java开发",
            "location": "深圳",
            "salary": "10-12K", 
            "description": "测试10-12K范围匹配"
        },
        {
            "name": "低薪资测试",
            "job_type": "前端开发",
            "location": "深圳",
            "salary": "8K",
            "description": "测试8K是否能找到合适职位"
        },
        {
            "name": "高薪资测试", 
            "job_type": "架构师",
            "location": "深圳",
            "salary": "30K",
            "description": "测试30K高薪职位匹配"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 测试用例 {i}: {test_case['name']}")
        print(f"📝 描述: {test_case['description']}")
        print("-" * 50)
        
        results = hybrid_system.search_jobs(
            test_case['job_type'],
            test_case['location'], 
            test_case['salary'],
            k=3
        )
        
        if results:
            for j, result in enumerate(results, 1):
                print(f"   {j}. {result['company_name']} - {result['job_title']}")
                print(f"      💰 薪资: {result['salary']}")
                print(f"      📊 匹配: {result['salary_match_score']:.2%} ({result['salary_match_type']})")
        else:
            print("   ❌ 未找到匹配的职位")


if __name__ == "__main__":
    test_hybrid_retrieval()
