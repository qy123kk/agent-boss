#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能工作流处理器
使用AI大模型处理每个对话阶段，提供更智能的用户输入理解和响应
"""

from typing import Dict, List, Optional, Any, Tuple
from conversation_state import ConversationStage, ConversationStateManager
from qa_chain import create_llm
import json
import re


class IntelligentWorkflowProcessor:
    """智能工作流处理器"""
    
    def __init__(self):
        self.llm = None
        self._initialize_llm()
        
        # 各阶段的AI提示模板
        self.stage_prompts = {
            ConversationStage.COLLECTING_JOB_TYPE: {
                "system_prompt": """你是一个专业的求职顾问，正在帮助用户收集职位类型信息。

你的任务：
1. 理解用户输入是否包含职位类型信息
2. 如果包含，提取具体的职位类型
3. 如果不包含或不清楚，友好地重新询问

职位类型示例：
- 技术类：Python开发工程师、前端开发、Java工程师、数据分析师、算法工程师
- 设计类：UI设计师、UX设计师、平面设计师、产品设计师
- 管理类：产品经理、项目经理、运营经理、技术总监
- 销售类：销售代表、客户经理、商务拓展
- 其他：人事专员、财务分析师、市场营销等

请分析用户输入并返回JSON格式：
{
    "understood": true/false,
    "job_type": "提取的职位类型" 或 null,
    "confidence": 0.0-1.0,
    "response": "给用户的回复"
}""",
                
                "examples": [
                    {"input": "python", "job_type": "Python开发工程师", "confidence": 0.8},
                    {"input": "前端", "job_type": "前端开发工程师", "confidence": 0.9},
                    {"input": "1", "job_type": None, "confidence": 0.0},
                    {"input": "设计", "job_type": "设计师", "confidence": 0.6},
                ]
            },
            
            ConversationStage.COLLECTING_LOCATION: {
                "system_prompt": """你是一个专业的求职顾问，正在帮助用户收集工作地点信息。

你的任务：
1. 理解用户输入是否包含地点信息
2. 如果包含，提取具体的城市或地区
3. 如果不包含或不清楚，友好地重新询问

地点示例：
- 一线城市：北京、上海、广州、深圳
- 新一线城市：杭州、成都、武汉、南京、西安、苏州
- 其他城市：青岛、大连、厦门、长沙、郑州等
- 特殊情况：远程办公、在家办公、不限地点

请分析用户输入并返回JSON格式：
{
    "understood": true/false,
    "location": "提取的地点" 或 null,
    "confidence": 0.0-1.0,
    "response": "给用户的回复"
}""",
                
                "examples": [
                    {"input": "深圳", "location": "深圳", "confidence": 1.0},
                    {"input": "北上广", "location": "北京、上海、广州", "confidence": 0.9},
                    {"input": "1", "location": None, "confidence": 0.0},
                    {"input": "远程", "location": "远程办公", "confidence": 0.8},
                ]
            },
            
            ConversationStage.COLLECTING_SALARY: {
                "system_prompt": """你是一个专业的求职顾问，正在帮助用户收集薪资期望信息。

你的任务：
1. 理解用户输入是否包含薪资信息
2. 如果包含，提取具体的薪资范围或数字
3. 如果不包含或不清楚，友好地重新询问

薪资表达示例：
- 范围格式：15-20K、10-15万、8千-1万2
- 单一数值：15K、20万、月薪12000
- 模糊表达：20K以上、15万左右、面议
- 年薪表达：年薪30万、年收入50万

请分析用户输入并返回JSON格式：
{
    "understood": true/false,
    "salary": "提取的薪资" 或 null,
    "confidence": 0.0-1.0,
    "response": "给用户的回复"
}""",
                
                "examples": [
                    {"input": "15K", "salary": "15K", "confidence": 1.0},
                    {"input": "15-20", "salary": "15-20K", "confidence": 0.8},
                    {"input": "1", "salary": None, "confidence": 0.0},
                    {"input": "面议", "salary": "面议", "confidence": 1.0},
                ]
            }
        }
    
    def _initialize_llm(self):
        """初始化大语言模型"""
        try:
            self.llm = create_llm(streaming=False)
        except Exception as e:
            print(f"初始化LLM失败: {e}")
            self.llm = None
    
    def process_user_input(self, user_input: str, current_stage: ConversationStage, 
                          conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        使用AI处理用户输入
        
        Args:
            user_input: 用户输入
            current_stage: 当前对话阶段
            conversation_history: 对话历史
            
        Returns:
            处理结果字典
        """
        if not self.llm:
            return self._fallback_processing(user_input, current_stage)
        
        if current_stage not in self.stage_prompts:
            return self._fallback_processing(user_input, current_stage)
        
        try:
            # 构建AI提示
            prompt = self._build_ai_prompt(user_input, current_stage, conversation_history)
            
            # 调用AI模型
            response = self.llm.invoke(prompt)
            
            # 解析AI响应
            if hasattr(response, 'content'):
                ai_response = response.content.strip()
            else:
                ai_response = str(response).strip()
            
            # 尝试解析JSON
            try:
                result = json.loads(ai_response)
                return self._validate_ai_result(result, current_stage)
            except json.JSONDecodeError:
                # 如果不是JSON格式，尝试从文本中提取信息
                return self._extract_from_text_response(ai_response, user_input, current_stage)
                
        except Exception as e:
            print(f"AI处理失败: {e}")
            return self._fallback_processing(user_input, current_stage)
    
    def _build_ai_prompt(self, user_input: str, current_stage: ConversationStage,
                        conversation_history: List[Dict] = None) -> str:
        """构建AI提示"""
        stage_config = self.stage_prompts[current_stage]

        prompt = f"""{stage_config['system_prompt']}

对话上下文："""

        # 添加对话历史上下文
        if conversation_history:
            recent_history = conversation_history[-4:]  # 最近4轮对话
            for msg in recent_history:
                role = "助手" if msg.get("role") == "assistant" else "用户"
                content = msg.get("content", "")
                prompt += f"\n{role}: {content[:100]}..."  # 限制长度

        prompt += f"""

当前用户输入："{user_input}"

重要提示：
1. 如果用户输入是确认性回复（如"是的"、"对"、"没错"、"好的"等），请检查对话历史中是否有待确认的信息
2. 如果用户输入是否定性回复（如"不是"、"不对"、"错了"等），表示需要重新收集信息
3. 考虑对话上下文来理解用户的真实意图

请分析这个输入并返回JSON格式的结果。

示例：
"""

        # 添加示例
        for example in stage_config['examples']:
            prompt += f"输入：\"{example['input']}\" -> "
            if current_stage == ConversationStage.COLLECTING_JOB_TYPE:
                prompt += f"职位类型：{example.get('job_type', 'null')}\n"
            elif current_stage == ConversationStage.COLLECTING_LOCATION:
                prompt += f"地点：{example.get('location', 'null')}\n"
            elif current_stage == ConversationStage.COLLECTING_SALARY:
                prompt += f"薪资：{example.get('salary', 'null')}\n"

        # 添加确认回复的示例
        prompt += f"""
特殊情况示例：
输入："是的" (在询问Python开发工程师确认后) -> 职位类型：Python开发工程师
输入："对的" (在询问深圳确认后) -> 地点：深圳
输入："不是" (在询问确认后) -> 需要重新收集

现在请分析用户输入："{user_input}"
"""

        return prompt
    
    def _validate_ai_result(self, result: Dict, current_stage: ConversationStage) -> Dict[str, Any]:
        """验证AI返回结果"""
        # 确保必需字段存在
        if not isinstance(result, dict):
            return self._fallback_processing("", current_stage)
        
        understood = result.get('understood', False)
        confidence = result.get('confidence', 0.0)
        response = result.get('response', '')
        
        # 根据阶段提取相应字段
        extracted_info = {}
        if current_stage == ConversationStage.COLLECTING_JOB_TYPE:
            job_type = result.get('job_type')
            if job_type:
                extracted_info['job_type'] = job_type
        elif current_stage == ConversationStage.COLLECTING_LOCATION:
            location = result.get('location')
            if location:
                extracted_info['location'] = location
        elif current_stage == ConversationStage.COLLECTING_SALARY:
            salary = result.get('salary')
            if salary:
                extracted_info['salary'] = salary
        
        return {
            "understood": understood,
            "extracted_info": extracted_info,
            "confidence": confidence,
            "ai_response": response,
            "needs_clarification": not understood or confidence < 0.5
        }
    
    def _extract_from_text_response(self, ai_response: str, user_input: str, 
                                   current_stage: ConversationStage) -> Dict[str, Any]:
        """从文本响应中提取信息"""
        # 简单的文本解析逻辑
        understood = "不理解" not in ai_response and "不清楚" not in ai_response
        
        return {
            "understood": understood,
            "extracted_info": {},
            "confidence": 0.3 if understood else 0.0,
            "ai_response": ai_response,
            "needs_clarification": True
        }
    
    def _fallback_processing(self, user_input: str, current_stage: ConversationStage) -> Dict[str, Any]:
        """回退处理逻辑（当AI不可用时）"""
        # 使用规则基础的处理
        if current_stage == ConversationStage.COLLECTING_JOB_TYPE:
            return self._fallback_job_type(user_input)
        elif current_stage == ConversationStage.COLLECTING_LOCATION:
            return self._fallback_location(user_input)
        elif current_stage == ConversationStage.COLLECTING_SALARY:
            return self._fallback_salary(user_input)
        
        return {
            "understood": False,
            "extracted_info": {},
            "confidence": 0.0,
            "ai_response": "抱歉，我没有理解您的意思，请再试一次。",
            "needs_clarification": True
        }
    
    def _fallback_job_type(self, user_input: str) -> Dict[str, Any]:
        """职位类型回退处理"""
        job_keywords = [
            "开发", "工程师", "程序员", "设计师", "产品经理", "运营", "销售",
            "python", "java", "前端", "后端", "ui", "ux", "数据", "算法"
        ]
        
        user_lower = user_input.lower()
        found_keywords = [kw for kw in job_keywords if kw in user_lower]
        
        if found_keywords:
            return {
                "understood": True,
                "extracted_info": {"job_type": user_input.strip()},
                "confidence": 0.7,
                "ai_response": f"好的，我理解您想找{user_input}相关的工作。",
                "needs_clarification": False
            }
        
        return {
            "understood": False,
            "extracted_info": {},
            "confidence": 0.0,
            "ai_response": "抱歉，我没有理解您想要的职位类型。请告诉我具体的职位，比如：Python开发工程师、UI设计师、产品经理等。",
            "needs_clarification": True
        }
    
    def _fallback_location(self, user_input: str) -> Dict[str, Any]:
        """地点回退处理"""
        cities = [
            "北京", "上海", "广州", "深圳", "杭州", "南京", "苏州", "成都",
            "武汉", "西安", "重庆", "天津", "青岛", "大连", "厦门", "长沙"
        ]
        
        found_cities = [city for city in cities if city in user_input]
        
        if found_cities:
            return {
                "understood": True,
                "extracted_info": {"location": found_cities[0]},
                "confidence": 0.9,
                "ai_response": f"好的，工作地点是{found_cities[0]}。",
                "needs_clarification": False
            }
        
        return {
            "understood": False,
            "extracted_info": {},
            "confidence": 0.0,
            "ai_response": "请告诉我一个具体的城市名称，比如：北京、上海、深圳、杭州等。",
            "needs_clarification": True
        }
    
    def _fallback_salary(self, user_input: str) -> Dict[str, Any]:
        """薪资回退处理"""
        salary_patterns = [
            r'\d+[kK万]', r'\d+-\d+[kK万]', r'\d+千', r'面议', r'年薪\d+万'
        ]
        
        for pattern in salary_patterns:
            if re.search(pattern, user_input):
                return {
                    "understood": True,
                    "extracted_info": {"salary": user_input.strip()},
                    "confidence": 0.8,
                    "ai_response": f"好的，薪资期望是{user_input}。",
                    "needs_clarification": False
                }
        
        return {
            "understood": False,
            "extracted_info": {},
            "confidence": 0.0,
            "ai_response": "请告诉我您的薪资期望，比如：15-20K、月薪1万、年薪30万等。",
            "needs_clarification": True
        }


def test_intelligent_processor():
    """测试智能处理器"""
    processor = IntelligentWorkflowProcessor()
    
    test_cases = [
        # 职位类型测试
        {"input": "python", "stage": ConversationStage.COLLECTING_JOB_TYPE},
        {"input": "1", "stage": ConversationStage.COLLECTING_JOB_TYPE},
        {"input": "前端开发", "stage": ConversationStage.COLLECTING_JOB_TYPE},
        
        # 地点测试
        {"input": "深圳", "stage": ConversationStage.COLLECTING_LOCATION},
        {"input": "1", "stage": ConversationStage.COLLECTING_LOCATION},
        {"input": "北上广", "stage": ConversationStage.COLLECTING_LOCATION},
        
        # 薪资测试
        {"input": "15K", "stage": ConversationStage.COLLECTING_SALARY},
        {"input": "1", "stage": ConversationStage.COLLECTING_SALARY},
        {"input": "15-20", "stage": ConversationStage.COLLECTING_SALARY},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 测试 {i}: {test_case['input']} ({test_case['stage'].value})")
        result = processor.process_user_input(test_case['input'], test_case['stage'])
        print(f"   理解: {result['understood']}")
        print(f"   置信度: {result['confidence']:.2f}")
        print(f"   提取信息: {result['extracted_info']}")
        print(f"   AI回复: {result['ai_response']}")


if __name__ == "__main__":
    test_intelligent_processor()
