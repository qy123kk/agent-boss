#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能简历建议生成模块
基于岗位信息生成针对性的简历制作要点，提高投递成功率
"""

import os
from typing import Dict, List, Optional
from rag_core import RAGSystem
from qa_chain import create_llm


class ResumeAdvisor:
    """智能简历建议生成器"""
    
    def __init__(self, rag_system: Optional[RAGSystem] = None):
        """
        初始化简历建议生成器
        
        Args:
            rag_system: 可选的RAG系统实例，如果不提供则创建新的
        """
        self.rag_system = rag_system
        self.llm = create_llm(streaming=False)
        
    def generate_resume_advice(self, job_metadata: Dict, user_background: Optional[Dict] = None) -> Dict:
        """
        生成针对特定岗位的简历建议
        
        Args:
            job_metadata: 岗位元数据信息
            user_background: 用户背景信息（可选）
            
        Returns:
            包含简历建议的字典
        """
        try:
            # 提取岗位关键信息
            job_info = self._extract_job_requirements(job_metadata)
            
            # 生成简历建议
            advice = self._generate_advice_content(job_info, user_background)
            
            return {
                "success": True,
                "job_title": job_metadata.get('job_title', '未知职位'),
                "company_name": job_metadata.get('company_name', '未知公司'),
                "advice": advice,
                "job_requirements": job_info
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"生成简历建议时出错: {str(e)}"
            }
    
    def _extract_job_requirements(self, job_metadata: Dict) -> Dict:
        """提取岗位关键要求信息"""
        structured_fields = job_metadata.get('structured_fields', {})
        
        return {
            "job_title": job_metadata.get('job_title', ''),
            "company_name": job_metadata.get('company_name', ''),
            "salary": job_metadata.get('salary', ''),
            "education": job_metadata.get('education', ''),
            "experience": job_metadata.get('experience', ''),
            "location": job_metadata.get('location', ''),
            "job_description": structured_fields.get('职位信息', ''),
            "job_type": structured_fields.get('职位类型', ''),
            "company_business": structured_fields.get('主营业务', ''),
            "company_scale": structured_fields.get('公司规模', ''),
            "company_benefits": structured_fields.get('公司福利', ''),
            "internship_time": structured_fields.get('实习时间', '')
        }
    
    def _generate_advice_content(self, job_info: Dict, user_background: Optional[Dict] = None) -> Dict:
        """生成具体的简历建议内容"""
        
        # 构建提示词
        prompt = self._build_resume_advice_prompt(job_info, user_background)
        
        # 调用LLM生成建议
        try:
            from langchain.schema import HumanMessage
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            advice_text = response.content
            
            # 解析和结构化建议内容
            structured_advice = self._parse_advice_response(advice_text)
            
            return structured_advice
            
        except Exception as e:
            # 如果LLM调用失败，返回基础建议
            return self._generate_basic_advice(job_info)
    
    def _build_resume_advice_prompt(self, job_info: Dict, user_background: Optional[Dict] = None) -> str:
        """构建简历建议生成的提示词"""
        
        prompt = f"""你是一位专业的简历优化专家和职业规划师，请根据以下岗位信息，为求职者生成一份详细的简历制作要点，帮助提高投递成功率。

【岗位信息】
职位名称：{job_info.get('job_title', '未知')}
公司名称：{job_info.get('company_name', '未知')}
薪资待遇：{job_info.get('salary', '未知')}
学历要求：{job_info.get('education', '未知')}
工作经验：{job_info.get('experience', '未知')}
工作地点：{job_info.get('location', '未知')}
职位类型：{job_info.get('job_type', '未知')}
公司业务：{job_info.get('company_business', '未知')}
公司规模：{job_info.get('company_scale', '未知')}

【详细职位描述】
{job_info.get('job_description', '暂无详细描述')}

【公司福利】
{job_info.get('company_benefits', '暂无福利信息')}

请按照以下格式生成简历制作要点：

## 🎯 简历优化要点

### 1. 个人信息优化
- [针对该岗位的个人信息展示建议]

### 2. 技能关键词匹配
- [根据职位要求提取的关键技能词]
- [建议在简历中突出的技术栈]

### 3. 工作经验描述
- [如何描述相关工作经验]
- [重点突出的项目类型]

### 4. 教育背景强化
- [学历相关的优化建议]
- [相关课程或证书推荐]

### 5. 项目经验包装
- [适合该岗位的项目经验类型]
- [项目描述的重点方向]

### 6. 软技能展示
- [该岗位看重的软技能]
- [如何在简历中体现这些能力]

### 7. 简历格式建议
- [针对该公司/行业的简历格式建议]
- [页面布局和设计要点]

### 8. 投递策略
- [最佳投递时间建议]
- [求职信要点]

请确保建议具体、实用、针对性强，能够真正帮助求职者提高投递成功率。"""

        # 如果有用户背景信息，添加到提示词中
        if user_background:
            prompt += f"\n\n【求职者背景】\n{self._format_user_background(user_background)}\n\n请结合求职者的背景信息，提供更加个性化的建议。"
        
        return prompt
    
    def _format_user_background(self, user_background: Dict) -> str:
        """格式化用户背景信息"""
        background_text = ""
        if user_background.get('education'):
            background_text += f"学历：{user_background['education']}\n"
        if user_background.get('experience_years'):
            background_text += f"工作年限：{user_background['experience_years']}\n"
        if user_background.get('skills'):
            background_text += f"技能：{', '.join(user_background['skills'])}\n"
        if user_background.get('industry'):
            background_text += f"行业经验：{user_background['industry']}\n"
        
        return background_text

    def _parse_advice_response(self, advice_text: str) -> Dict:
        """解析LLM生成的建议文本，提取结构化信息"""
        try:
            # 简单的解析逻辑，将文本按段落分组
            sections = {}
            current_section = None
            current_content = []

            lines = advice_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 检测是否是新的章节标题
                if line.startswith('###') or line.startswith('##'):
                    # 保存前一个章节
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content)

                    # 开始新章节
                    current_section = line.replace('#', '').strip()
                    current_content = []
                elif current_section:
                    current_content.append(line)

            # 保存最后一个章节
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content)

            return {
                "full_text": advice_text,
                "sections": sections,
                "summary": self._extract_key_points(advice_text)
            }

        except Exception as e:
            return {
                "full_text": advice_text,
                "sections": {},
                "summary": ["解析建议内容时出现问题，请查看完整文本"],
                "error": str(e)
            }

    def _extract_key_points(self, advice_text: str) -> List[str]:
        """从建议文本中提取关键要点"""
        key_points = []
        lines = advice_text.split('\n')

        for line in lines:
            line = line.strip()
            # 提取以 - 或 • 开头的要点
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                point = line[1:].strip()
                if point and len(point) > 10:  # 过滤太短的内容
                    key_points.append(point)

        return key_points[:10]  # 最多返回10个关键要点

    def _generate_basic_advice(self, job_info: Dict) -> Dict:
        """生成基础的简历建议（当LLM调用失败时使用）"""

        job_title = job_info.get('job_title', '').lower()
        company_business = job_info.get('company_business', '')

        # 基于职位类型的基础建议
        basic_advice = {
            "full_text": "## 🎯 基础简历优化建议\n\n",
            "sections": {},
            "summary": []
        }

        # 技能关键词建议
        if 'python' in job_title or 'java' in job_title or '开发' in job_title:
            basic_advice["summary"].extend([
                "突出编程语言技能和项目经验",
                "详细描述技术栈和开发框架",
                "展示代码质量和团队协作能力"
            ])
        elif 'ui' in job_title or '设计' in job_title:
            basic_advice["summary"].extend([
                "展示设计作品集和创意能力",
                "突出用户体验设计思维",
                "强调设计工具的熟练程度"
            ])
        elif '产品' in job_title or '运营' in job_title:
            basic_advice["summary"].extend([
                "突出数据分析和用户洞察能力",
                "展示产品规划和项目管理经验",
                "强调跨部门协作和沟通能力"
            ])

        # 通用建议
        basic_advice["summary"].extend([
            f"针对{job_info.get('education', '本科')}学历要求优化教育背景",
            f"匹配{job_info.get('experience', '1-3年')}工作经验要求",
            "简历格式清晰，重点突出，控制在1-2页内"
        ])

        basic_advice["full_text"] += "### 关键建议\n" + '\n'.join([f"• {point}" for point in basic_advice["summary"]])

        return basic_advice


def create_resume_advisor(rag_system: Optional[RAGSystem] = None) -> ResumeAdvisor:
    """创建简历建议生成器实例"""
    return ResumeAdvisor(rag_system)


# 便捷函数
def generate_quick_resume_advice(job_metadata: Dict, user_background: Optional[Dict] = None) -> Dict:
    """快速生成简历建议的便捷函数"""
    advisor = create_resume_advisor()
    return advisor.generate_resume_advice(job_metadata, user_background)


if __name__ == "__main__":
    # 测试示例
    test_job_metadata = {
        'job_title': 'Python开发工程师',
        'company_name': '深圳科技有限公司',
        'salary': '15-25K',
        'education': '本科',
        'experience': '3-5年',
        'location': '深圳',
        'structured_fields': {
            '职位信息': 'Python后端开发，熟悉Django/Flask框架，有微服务经验',
            '职位类型': '全职',
            '主营业务': '互联网金融',
            '公司规模': '100-500人',
            '公司福利': '五险一金，弹性工作，年终奖'
        }
    }

    test_user_background = {
        'education': '本科',
        'experience_years': '4年',
        'skills': ['Python', 'Django', 'MySQL', 'Redis'],
        'industry': '互联网'
    }

    print("🧪 测试简历建议生成功能...")
    result = generate_quick_resume_advice(test_job_metadata, test_user_background)

    if result['success']:
        print(f"✅ 为 {result['job_title']} 职位生成建议成功")
        print(f"📝 关键要点数量: {len(result['advice']['summary'])}")
        print("\n🔍 关键要点预览:")
        for i, point in enumerate(result['advice']['summary'][:3], 1):
            print(f"  {i}. {point}")
    else:
        print(f"❌ 生成失败: {result['error']}")
