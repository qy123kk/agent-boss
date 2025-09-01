#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
薪资匹配测试文件
测试不同薪资要求对职位检索结果的影响
"""

import sys
import time
from typing import List, Dict, Any
from humanized_job_assistant import create_humanized_job_assistant
import re


class SalaryMatchingTester:
    """薪资匹配测试器"""
    
    def __init__(self):
        self.assistant = None
        self.test_cases = [
            # 低薪资范围测试
            {
                "name": "低薪资范围",
                "job_type": "Python开发工程师",
                "location": "深圳",
                "salary": "5-8K",
                "expected_range": (5000, 8000)
            },
            {
                "name": "入门级薪资",
                "job_type": "Java开发",
                "location": "深圳",
                "salary": "8-12K",
                "expected_range": (8000, 12000)
            },
            # 中等薪资范围测试
            {
                "name": "中等薪资范围",
                "job_type": "前端开发",
                "location": "深圳",
                "salary": "12-18K",
                "expected_range": (12000, 18000)
            },
            {
                "name": "中高级薪资",
                "job_type": "Python开发工程师",
                "location": "深圳",
                "salary": "15-20K",
                "expected_range": (15000, 20000)
            },
            # 高薪资范围测试
            {
                "name": "高薪资范围",
                "job_type": "高级开发工程师",
                "location": "深圳",
                "salary": "25-35K",
                "expected_range": (25000, 35000)
            },
            {
                "name": "资深级薪资",
                "job_type": "架构师",
                "location": "深圳",
                "salary": "30-50K",
                "expected_range": (30000, 50000)
            },
            # 特殊表达方式测试
            {
                "name": "月薪表达",
                "job_type": "产品经理",
                "location": "深圳",
                "salary": "月薪15000",
                "expected_range": (15000, 15000)
            },
            {
                "name": "以上表达",
                "job_type": "技术总监",
                "location": "深圳",
                "salary": "20K以上",
                "expected_range": (20000, 999999)
            },
            {
                "name": "年薪表达",
                "job_type": "数据分析师",
                "location": "深圳",
                "salary": "年薪30万",
                "expected_range": (25000, 25000)  # 30万/12个月
            },
            {
                "name": "面议薪资",
                "job_type": "UI设计师",
                "location": "深圳",
                "salary": "面议",
                "expected_range": (0, 999999)  # 面议应该返回各种薪资范围
            }
        ]
    
    def initialize_system(self) -> bool:
        """初始化测试系统"""
        print("🔄 初始化薪资匹配测试系统...")
        
        try:
            self.assistant = create_humanized_job_assistant()
            init_result = self.assistant.initialize()
            
            if init_result["success"]:
                print("✅ 系统初始化成功")
                if "stats" in init_result:
                    stats = init_result["stats"]
                    vector_stats = stats.get("vector_store", {})
                    print(f"📊 知识库统计: {vector_stats.get('total_documents', 0)} 个文档, {vector_stats.get('total_chunks', 0)} 个文本块")
                return True
            else:
                print(f"❌ 系统初始化失败: {init_result.get('error', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"❌ 初始化异常: {e}")
            return False
    
    def parse_salary_from_text(self, salary_text: str) -> tuple:
        """从薪资文本中解析数值范围"""
        if not salary_text or salary_text == "面议":
            return (0, 999999)
        
        # 匹配各种薪资格式
        patterns = [
            r'(\d+)-(\d+)[kK万]',      # 15-20K, 15-20万
            r'(\d+)[kK万]-(\d+)[kK万]', # 15K-20K
            r'(\d+)[kK万]以上',         # 20K以上
            r'(\d+)[kK万]',            # 15K
            r'月薪(\d+)',              # 月薪15000
            r'年薪(\d+)万',            # 年薪30万
            r'(\d+)千-(\d+)千',        # 8千-12千
            r'(\d+)千',               # 10千
        ]
        
        salary_lower = salary_text.lower()
        
        for pattern in patterns:
            match = re.search(pattern, salary_lower)
            if match:
                if '以上' in salary_lower:
                    min_val = int(match.group(1))
                    if 'k' in salary_lower:
                        min_val *= 1000
                    elif '万' in salary_lower:
                        min_val *= 10000
                    return (min_val, 999999)
                elif '年薪' in salary_lower and '万' in salary_lower:
                    annual = int(match.group(1)) * 10000
                    monthly = annual // 12
                    return (monthly, monthly)
                elif '千' in salary_lower:
                    if len(match.groups()) == 2:
                        return (int(match.group(1)) * 1000, int(match.group(2)) * 1000)
                    else:
                        val = int(match.group(1)) * 1000
                        return (val, val)
                elif len(match.groups()) == 2:
                    min_val, max_val = int(match.group(1)), int(match.group(2))
                    if 'k' in salary_lower:
                        min_val *= 1000
                        max_val *= 1000
                    elif '万' in salary_lower:
                        min_val *= 10000
                        max_val *= 10000
                    return (min_val, max_val)
                else:
                    val = int(match.group(1))
                    if 'k' in salary_lower:
                        val *= 1000
                    elif '万' in salary_lower:
                        val *= 10000
                    return (val, val)
        
        return (0, 999999)
    
    def analyze_salary_match(self, expected_range: tuple, actual_salary: str) -> Dict[str, Any]:
        """分析薪资匹配度"""
        actual_range = self.parse_salary_from_text(actual_salary)
        expected_min, expected_max = expected_range
        actual_min, actual_max = actual_range
        
        # 计算重叠度
        overlap_min = max(expected_min, actual_min)
        overlap_max = min(expected_max, actual_max)
        
        if overlap_min <= overlap_max:
            # 有重叠
            overlap_size = overlap_max - overlap_min
            expected_size = expected_max - expected_min
            actual_size = actual_max - actual_min
            
            if expected_size > 0:
                overlap_ratio = overlap_size / expected_size
            else:
                overlap_ratio = 1.0 if actual_min == expected_min else 0.0
        else:
            # 无重叠
            overlap_ratio = 0.0
        
        # 判断匹配类型
        if overlap_ratio >= 0.8:
            match_type = "完全匹配"
        elif overlap_ratio >= 0.5:
            match_type = "部分匹配"
        elif overlap_ratio > 0:
            match_type = "轻微匹配"
        else:
            match_type = "不匹配"
        
        return {
            "expected_range": expected_range,
            "actual_range": actual_range,
            "overlap_ratio": overlap_ratio,
            "match_type": match_type,
            "is_good_match": overlap_ratio >= 0.3  # 30%以上重叠认为是好匹配
        }
    
    def run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个测试用例"""
        print(f"\n🧪 测试用例: {test_case['name']}")
        print(f"   职位: {test_case['job_type']}")
        print(f"   地点: {test_case['location']}")
        print(f"   薪资: {test_case['salary']}")
        print(f"   期望范围: {test_case['expected_range'][0]}-{test_case['expected_range'][1]}")
        
        try:
            # 模拟用户对话流程
            self.assistant.restart_conversation()
            
            # 输入职位类型
            result1 = self.assistant.process_message(test_case['job_type'])
            if not result1["success"]:
                return {"success": False, "error": "职位类型输入失败"}
            
            # 输入地点
            result2 = self.assistant.process_message(test_case['location'])
            if not result2["success"]:
                return {"success": False, "error": "地点输入失败"}
            
            # 输入薪资
            result3 = self.assistant.process_message(test_case['salary'])
            if not result3["success"]:
                return {"success": False, "error": "薪资输入失败"}
            
            # 检查是否有搜索结果
            if "search_results" not in result3:
                return {"success": False, "error": "未获得搜索结果"}
            
            search_results = result3["search_results"]
            print(f"   ✅ 找到 {len(search_results)} 个职位")
            
            # 分析每个结果的薪资匹配度
            matches = []
            for i, job in enumerate(search_results, 1):
                job_salary = job.get('salary', '面议')
                match_analysis = self.analyze_salary_match(test_case['expected_range'], job_salary)
                
                matches.append({
                    "rank": i,
                    "company": job.get('company_name', '未知'),
                    "title": job.get('job_title', '未知'),
                    "salary": job_salary,
                    "analysis": match_analysis
                })
                
                print(f"   {i}. {job['company_name']} - {job['job_title']}")
                print(f"      💰 薪资: {job_salary}")
                print(f"      📊 匹配度: {match_analysis['overlap_ratio']:.2%} ({match_analysis['match_type']})")
            
            # 计算整体匹配统计
            good_matches = sum(1 for m in matches if m['analysis']['is_good_match'])
            avg_overlap = sum(m['analysis']['overlap_ratio'] for m in matches) / len(matches)
            
            return {
                "success": True,
                "test_case": test_case,
                "matches": matches,
                "statistics": {
                    "total_results": len(matches),
                    "good_matches": good_matches,
                    "good_match_ratio": good_matches / len(matches),
                    "average_overlap": avg_overlap
                }
            }
            
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            return {"success": False, "error": str(e)}
    
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """运行所有测试用例"""
        print("🚀 开始薪资匹配测试")
        print("=" * 80)
        
        results = []
        
        for test_case in self.test_cases:
            result = self.run_single_test(test_case)
            results.append(result)
            time.sleep(1)  # 避免API调用过于频繁
        
        return results
    
    def generate_report(self, results: List[Dict[str, Any]]):
        """生成测试报告"""
        print("\n" + "=" * 80)
        print("📊 薪资匹配测试报告")
        print("=" * 80)
        
        successful_tests = [r for r in results if r["success"]]
        failed_tests = [r for r in results if not r["success"]]
        
        print(f"📈 测试概览:")
        print(f"   总测试数: {len(results)}")
        print(f"   成功测试: {len(successful_tests)}")
        print(f"   失败测试: {len(failed_tests)}")
        
        if successful_tests:
            print(f"\n📊 匹配度统计:")
            
            # 按薪资范围分组统计
            salary_groups = {
                "低薪资(≤12K)": [],
                "中薪资(12-25K)": [],
                "高薪资(≥25K)": [],
                "特殊表达": []
            }
            
            for result in successful_tests:
                test_case = result["test_case"]
                stats = result["statistics"]
                expected_max = test_case["expected_range"][1]
                
                if expected_max <= 12000:
                    salary_groups["低薪资(≤12K)"].append(stats)
                elif expected_max <= 25000:
                    salary_groups["中薪资(12-25K)"].append(stats)
                elif expected_max < 999999:
                    salary_groups["高薪资(≥25K)"].append(stats)
                else:
                    salary_groups["特殊表达"].append(stats)
            
            for group_name, group_stats in salary_groups.items():
                if group_stats:
                    avg_good_match_ratio = sum(s["good_match_ratio"] for s in group_stats) / len(group_stats)
                    avg_overlap = sum(s["average_overlap"] for s in group_stats) / len(group_stats)
                    print(f"   {group_name}: 好匹配率 {avg_good_match_ratio:.1%}, 平均重叠度 {avg_overlap:.1%}")
        
        if failed_tests:
            print(f"\n❌ 失败的测试:")
            for result in failed_tests:
                print(f"   - {result.get('test_case', {}).get('name', '未知')}: {result.get('error', '未知错误')}")
        
        print(f"\n💡 建议:")
        if successful_tests:
            overall_good_match_ratio = sum(r["statistics"]["good_match_ratio"] for r in successful_tests) / len(successful_tests)
            if overall_good_match_ratio >= 0.7:
                print("   ✅ 薪资匹配效果良好，系统能够较好地理解和匹配薪资要求")
            elif overall_good_match_ratio >= 0.5:
                print("   ⚠️ 薪资匹配效果一般，建议优化检索算法或增加薪资过滤逻辑")
            else:
                print("   ❌ 薪资匹配效果较差，建议重新设计薪资匹配策略")


def main():
    """主函数"""
    tester = SalaryMatchingTester()
    
    # 初始化系统
    if not tester.initialize_system():
        print("❌ 系统初始化失败，无法进行测试")
        return
    
    # 运行测试
    results = tester.run_all_tests()
    
    # 生成报告
    tester.generate_report(results)


if __name__ == "__main__":
    main()
