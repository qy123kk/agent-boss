#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话状态管理器
负责跟踪用户信息收集进度，管理多轮对话状态
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import json
import re


class ConversationStage(Enum):
    """对话阶段枚举"""
    GREETING = "greeting"           # 问候阶段
    COLLECTING_JOB_TYPE = "job_type"      # 收集职位类型
    COLLECTING_LOCATION = "location"       # 收集工作地点
    COLLECTING_SALARY = "salary"          # 收集薪资期望
    COLLECTING_ADDITIONAL = "additional"   # 收集额外信息
    SEARCHING = "searching"               # 搜索阶段
    SHOWING_RESULTS = "showing_results"   # 展示结果
    COMPLETED = "completed"               # 完成


@dataclass
class UserRequirements:
    """用户需求数据类"""
    job_type: Optional[str] = None          # 职位类型（必需）
    location: Optional[str] = None          # 工作地点（必需）
    salary: Optional[str] = None            # 薪资期望（必需）
    experience: Optional[str] = None        # 工作经验（可选）
    education: Optional[str] = None         # 学历要求（可选）
    company_size: Optional[str] = None      # 公司规模（可选）
    industry: Optional[str] = None          # 行业偏好（可选）
    
    def get_missing_required_fields(self) -> List[str]:
        """获取缺失的必需字段"""
        missing = []
        if not self.job_type:
            missing.append("job_type")
        if not self.location:
            missing.append("location")
        if not self.salary:
            missing.append("salary")
        return missing
    
    def is_complete(self) -> bool:
        """检查必需信息是否完整"""
        return len(self.get_missing_required_fields()) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "job_type": self.job_type,
            "location": self.location,
            "salary": self.salary,
            "experience": self.experience,
            "education": self.education,
            "company_size": self.company_size,
            "industry": self.industry
        }


class ConversationStateManager:
    """对话状态管理器"""
    
    def __init__(self):
        self.stage = ConversationStage.GREETING
        self.requirements = UserRequirements()
        self.conversation_history: List[Dict[str, str]] = []
        self.search_results: List[Any] = []
        self.current_question_attempts = 0  # 当前问题尝试次数
        self.max_attempts = 3  # 最大尝试次数
        
    def add_conversation(self, role: str, content: str):
        """添加对话记录"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "stage": self.stage.value
        })
    
    def get_current_stage(self) -> ConversationStage:
        """获取当前对话阶段"""
        return self.stage
    
    def advance_to_next_stage(self):
        """推进到下一个阶段"""
        if self.stage == ConversationStage.GREETING:
            # 检查哪个必需信息缺失，优先收集
            missing = self.requirements.get_missing_required_fields()
            if "job_type" in missing:
                self.stage = ConversationStage.COLLECTING_JOB_TYPE
            elif "location" in missing:
                self.stage = ConversationStage.COLLECTING_LOCATION
            elif "salary" in missing:
                self.stage = ConversationStage.COLLECTING_SALARY
            else:
                self.stage = ConversationStage.SEARCHING
                
        elif self.stage == ConversationStage.COLLECTING_JOB_TYPE:
            missing = self.requirements.get_missing_required_fields()
            if "location" in missing:
                self.stage = ConversationStage.COLLECTING_LOCATION
            elif "salary" in missing:
                self.stage = ConversationStage.COLLECTING_SALARY
            else:
                self.stage = ConversationStage.SEARCHING
                
        elif self.stage == ConversationStage.COLLECTING_LOCATION:
            missing = self.requirements.get_missing_required_fields()
            if "salary" in missing:
                self.stage = ConversationStage.COLLECTING_SALARY
            else:
                self.stage = ConversationStage.SEARCHING
                
        elif self.stage == ConversationStage.COLLECTING_SALARY:
            self.stage = ConversationStage.SEARCHING
            
        elif self.stage == ConversationStage.SEARCHING:
            self.stage = ConversationStage.SHOWING_RESULTS
            
        elif self.stage == ConversationStage.SHOWING_RESULTS:
            self.stage = ConversationStage.COMPLETED
        
        # 重置尝试次数
        self.current_question_attempts = 0
    
    def update_requirements(self, field: str, value: str) -> bool:
        """更新用户需求信息"""
        if hasattr(self.requirements, field):
            setattr(self.requirements, field, value)
            return True
        return False
    
    def parse_user_input(self, user_input: str) -> Dict[str, Any]:
        """解析用户输入，提取相关信息"""
        result = {
            "extracted_info": {},
            "confidence": 0.0,
            "needs_clarification": False
        }
        
        user_input_lower = user_input.lower().strip()
        
        # 根据当前阶段解析不同类型的信息
        if self.stage == ConversationStage.COLLECTING_JOB_TYPE:
            result = self._parse_job_type(user_input)
        elif self.stage == ConversationStage.COLLECTING_LOCATION:
            result = self._parse_location(user_input)
        elif self.stage == ConversationStage.COLLECTING_SALARY:
            result = self._parse_salary(user_input)
        
        return result
    
    def _parse_job_type(self, user_input: str) -> Dict[str, Any]:
        """解析职位类型"""
        # 常见职位关键词
        job_keywords = [
            "开发", "工程师", "程序员", "设计师", "产品经理", "运营", "销售", 
            "市场", "人事", "财务", "客服", "测试", "数据", "算法", "前端", 
            "后端", "全栈", "移动", "安卓", "iOS", "UI", "UX", "Java", 
            "Python", "JavaScript", "React", "Vue", "Node"
        ]
        
        user_input_lower = user_input.lower()
        found_keywords = [kw for kw in job_keywords if kw.lower() in user_input_lower]
        
        if found_keywords or any(char.isalpha() for char in user_input):
            return {
                "extracted_info": {"job_type": user_input.strip()},
                "confidence": 0.8 if found_keywords else 0.6,
                "needs_clarification": False
            }
        
        return {
            "extracted_info": {},
            "confidence": 0.0,
            "needs_clarification": True
        }
    
    def _parse_location(self, user_input: str) -> Dict[str, Any]:
        """解析工作地点"""
        # 常见城市名称
        cities = [
            "北京", "上海", "广州", "深圳", "杭州", "南京", "苏州", "成都", 
            "武汉", "西安", "重庆", "天津", "青岛", "大连", "厦门", "长沙",
            "郑州", "济南", "合肥", "福州", "昆明", "南昌", "贵阳", "海口"
        ]
        
        user_input_clean = user_input.strip()
        found_cities = [city for city in cities if city in user_input_clean]
        
        if found_cities:
            return {
                "extracted_info": {"location": found_cities[0]},
                "confidence": 0.9,
                "needs_clarification": False
            }
        elif any(char.isalpha() for char in user_input_clean):
            return {
                "extracted_info": {"location": user_input_clean},
                "confidence": 0.6,
                "needs_clarification": False
            }
        
        return {
            "extracted_info": {},
            "confidence": 0.0,
            "needs_clarification": True
        }
    
    def _parse_salary(self, user_input: str) -> Dict[str, Any]:
        """解析薪资期望"""
        # 薪资模式匹配
        salary_patterns = [
            r'(\d+)-(\d+)[kK万]',  # 15-20K, 15-20万
            r'(\d+)[kK万]以上',     # 20K以上, 20万以上
            r'(\d+)[kK万]左右',     # 15K左右
            r'(\d+)[kK万]',        # 15K, 15万
            r'(\d+)千-(\d+)千',     # 8千-12千
            r'(\d+)千以上',        # 10千以上
            r'(\d+)千',           # 8千
        ]
        
        user_input_clean = user_input.strip()
        
        for pattern in salary_patterns:
            match = re.search(pattern, user_input_clean)
            if match:
                return {
                    "extracted_info": {"salary": user_input_clean},
                    "confidence": 0.8,
                    "needs_clarification": False
                }
        
        # 如果包含数字，可能是薪资
        if re.search(r'\d+', user_input_clean):
            return {
                "extracted_info": {"salary": user_input_clean},
                "confidence": 0.5,
                "needs_clarification": False
            }
        
        return {
            "extracted_info": {},
            "confidence": 0.0,
            "needs_clarification": True
        }
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """获取进度摘要"""
        missing_fields = self.requirements.get_missing_required_fields()
        total_required = 3  # job_type, location, salary
        completed_required = total_required - len(missing_fields)
        
        return {
            "stage": self.stage.value,
            "progress_percentage": (completed_required / total_required) * 100,
            "completed_fields": completed_required,
            "total_required_fields": total_required,
            "missing_fields": missing_fields,
            "requirements": self.requirements.to_dict(),
            "is_ready_for_search": self.requirements.is_complete()
        }
    
    def reset(self):
        """重置对话状态"""
        self.stage = ConversationStage.GREETING
        self.requirements = UserRequirements()
        self.conversation_history = []
        self.search_results = []
        self.current_question_attempts = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "stage": self.stage.value,
            "requirements": self.requirements.to_dict(),
            "conversation_history": self.conversation_history,
            "current_question_attempts": self.current_question_attempts,
            "progress": self.get_progress_summary()
        }
