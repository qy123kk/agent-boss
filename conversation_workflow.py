#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能问答工作流引擎
负责根据对话状态智能生成问题，控制整个对话流程
"""

import random
from typing import Dict, List, Optional, Any
from conversation_state import ConversationStateManager, ConversationStage
from qa_chain import create_llm
from intelligent_workflow_processor import IntelligentWorkflowProcessor
from langchain_conversation_processor import LangChainConversationProcessor
from modern_langchain_processor import ModernLangChainProcessor
import json


class ConversationWorkflowEngine:
    """智能对话工作流引擎"""
    
    def __init__(self):
        self.state_manager = ConversationStateManager()
        self.llm = None
        self.intelligent_processor = IntelligentWorkflowProcessor()
        self.langchain_processor = LangChainConversationProcessor()
        self.modern_processor = ModernLangChainProcessor()
        self._initialize_llm()
        
        # 预定义的问题模板
        self.question_templates = {
            ConversationStage.GREETING: [
                "你好！我是您的专属求职助手 🤖\n我将帮助您找到最合适的工作机会。让我们开始吧！\n\n请告诉我，您想找什么类型的工作呢？比如：Python开发工程师、UI设计师、产品经理等。",
                "欢迎使用智能求职助手！✨\n我会通过几个简单的问题了解您的需求，然后为您推荐最匹配的职位。\n\n首先，您希望从事什么职位呢？请尽量具体一些，比如：前端开发、数据分析师、市场运营等。",
                "很高兴为您服务！🎯\n为了给您推荐最合适的工作，我需要了解一些基本信息。\n\n请问您想要应聘什么职位？可以说说您的专业方向或感兴趣的工作类型。"
            ],
            
            ConversationStage.COLLECTING_JOB_TYPE: [
                "请告诉我您想要从事的具体职位，比如：\n• Python开发工程师\n• UI/UX设计师\n• 产品经理\n• 数据分析师\n• 市场运营专员\n\n您的目标职位是？",
                "为了更好地为您匹配职位，请具体说明您想要的工作类型。\n\n比如您可以说：'我想做Java后端开发'或'我对新媒体运营感兴趣'。",
                "请描述一下您理想的工作职位，可以包括：\n• 技术方向（如前端、后端、移动端）\n• 职能类型（如开发、设计、运营、销售）\n• 具体技能（如Python、React、Photoshop）"
            ],
            
            ConversationStage.COLLECTING_LOCATION: [
                "很好！接下来请告诉我您希望在哪个城市工作？\n\n比如：北京、上海、深圳、杭州、成都等。",
                "请问您期望的工作地点是哪里？\n\n可以是具体的城市，比如：广州、南京、武汉、西安等。",
                "关于工作地点，您有什么偏好吗？\n\n请告诉我您希望工作的城市名称。"
            ],
            
            ConversationStage.COLLECTING_SALARY: [
                "最后一个问题，请告诉我您的薪资期望？\n\n可以这样表达：\n• 15-20K\n• 月薪1万以上\n• 年薪30万左右\n• 面议",
                "关于薪资待遇，您的期望是多少呢？\n\n比如：12K-18K、20万年薪、或者其他具体数字。",
                "请分享一下您的薪资期望，这样我能为您筛选更合适的职位。\n\n格式可以是：8K-12K、15万年薪、或者您觉得合理的范围。"
            ]
        }
        
        # 确认和澄清的模板
        self.clarification_templates = {
            "job_type": [
                "我理解您想找{job_type}相关的工作，这个理解对吗？\n\n如果不准确，请再详细描述一下您的目标职位。",
                "您说的是{job_type}类型的工作对吧？\n\n如果需要补充或修正，请告诉我。"
            ],
            "location": [
                "确认一下，您希望在{location}工作，是这样吗？",
                "工作地点是{location}，我理解得对吗？"
            ],
            "salary": [
                "您的薪资期望是{salary}，这样理解对吗？",
                "关于薪资{salary}，这个范围合适吗？"
            ]
        }
        
        # 重新询问的模板
        self.retry_templates = {
            "job_type": [
                "抱歉，我没有完全理解您想要的职位类型。\n\n能否更具体地说明一下？比如：\n• 技术开发类：Java工程师、前端开发\n• 设计创意类：UI设计师、平面设计\n• 运营管理类：产品经理、市场运营",
                "让我重新理解一下，您希望从事什么样的工作呢？\n\n请尽量具体，这样我能为您找到更匹配的职位。"
            ],
            "location": [
                "请告诉我一个具体的城市名称，比如北京、上海、深圳等。",
                "工作地点请说一个城市名称，这样我能为您搜索当地的职位。"
            ],
            "salary": [
                "请告诉我一个具体的薪资数字或范围，比如：\n• 10K-15K\n• 月薪8000以上\n• 年薪20万",
                "关于薪资，请给出一个数字范围，这样我能筛选合适的职位。"
            ]
        }
    
    def _initialize_llm(self):
        """初始化大语言模型"""
        try:
            self.llm = create_llm(streaming=False)
        except Exception as e:
            print(f"初始化LLM失败: {e}")
            self.llm = None
    
    def start_conversation(self) -> str:
        """开始对话"""
        self.state_manager.reset()
        greeting = random.choice(self.question_templates[ConversationStage.GREETING])
        self.state_manager.add_conversation("assistant", greeting)
        # 推进到收集职位类型阶段，准备接收用户的第一个回答
        self.state_manager.advance_to_next_stage()
        return greeting
    
    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """处理用户输入并生成响应"""
        if not user_input.strip():
            return {
                "response": "请告诉我一些信息，这样我能更好地帮助您。",
                "stage": self.state_manager.stage.value,
                "progress": self.state_manager.get_progress_summary()
            }
        
        # 记录用户输入
        self.state_manager.add_conversation("user", user_input)
        
        # 优先使用最新的现代LangChain处理器
        try:
            parse_result = self.modern_processor.process_user_input(
                user_input,
                self.state_manager.stage,
                self.state_manager.conversation_history,
                thread_id="main_conversation"
            )
            print(f"🚀 现代LangChain处理结果: 理解={parse_result.get('understood')}, 置信度={parse_result.get('confidence', 0):.2f}")
        except Exception as e:
            print(f"⚠️ 现代LangChain处理失败，回退到传统LangChain: {e}")
            try:
                parse_result = self.langchain_processor.process_user_input(
                    user_input,
                    self.state_manager.stage,
                    self.state_manager.conversation_history
                )
                print(f"🔗 传统LangChain处理结果: 理解={parse_result.get('understood')}, 置信度={parse_result.get('confidence', 0):.2f}")
            except Exception as e2:
                print(f"⚠️ 传统LangChain也失败，回退到智能处理器: {e2}")
                # 最后回退到原有的智能处理器
                parse_result = self.intelligent_processor.process_user_input(
                    user_input,
                    self.state_manager.stage,
                    self.state_manager.conversation_history
                )
        
        # 根据解析结果生成响应
        response = self._generate_response(user_input, parse_result)
        
        # 记录助手响应
        self.state_manager.add_conversation("assistant", response["message"])
        
        return {
            "response": response["message"],
            "stage": self.state_manager.stage.value,
            "progress": self.state_manager.get_progress_summary(),
            "extracted_info": parse_result.get("extracted_info", {}),
            "confidence": parse_result.get("confidence", 0.0),
            "ready_for_search": self.state_manager.requirements.is_complete()
        }
    
    def _generate_response(self, user_input: str, parse_result: Dict[str, Any]) -> Dict[str, str]:
        """根据解析结果生成响应"""
        current_stage = self.state_manager.stage
        extracted_info = parse_result.get("extracted_info", {})
        confidence = parse_result.get("confidence", 0.0)
        needs_clarification = parse_result.get("needs_clarification", False)
        understood = parse_result.get("understood", False)
        ai_response = parse_result.get("ai_response", "")

        # 如果AI理解了用户输入且置信度较高
        if understood and extracted_info and confidence > 0.5:
            # 更新需求信息
            for field, value in extracted_info.items():
                self.state_manager.update_requirements(field, value)
            
            # 生成确认信息并推进到下一阶段
            confirmation = self._generate_confirmation(extracted_info)
            self.state_manager.advance_to_next_stage()
            
            # 如果所有必需信息已收集完毕
            if self.state_manager.requirements.is_complete():
                return {
                    "message": confirmation + "\n\n✅ 太好了！我已经收集到了所有必要信息：\n" + 
                              self._format_collected_info() + 
                              "\n\n正在为您搜索匹配的职位，请稍候..."
                }
            else:
                # 继续收集下一个信息
                next_question = self._get_next_question()
                return {
                    "message": confirmation + "\n\n" + next_question
                }
        
        # 如果AI理解了但置信度较低，需要确认
        elif understood and extracted_info and confidence > 0.3:
            field_name = list(extracted_info.keys())[0]
            field_value = list(extracted_info.values())[0]

            if field_name in self.clarification_templates:
                clarification = random.choice(self.clarification_templates[field_name])
                return {
                    "message": clarification.format(**{field_name: field_value})
                }

        # 如果AI没有理解或需要澄清，优先使用AI生成的回复
        else:
            if ai_response:
                return {"message": ai_response}

            # 回退到传统处理
            self.state_manager.current_question_attempts += 1

            # 如果尝试次数过多，使用LLM生成个性化响应
            if self.state_manager.current_question_attempts >= 2 and self.llm:
                return {"message": self._generate_llm_response(user_input)}

            # 使用重试模板
            field_map = {
                ConversationStage.COLLECTING_JOB_TYPE: "job_type",
                ConversationStage.COLLECTING_LOCATION: "location",
                ConversationStage.COLLECTING_SALARY: "salary"
            }

            if current_stage in field_map:
                field = field_map[current_stage]
                retry_msg = random.choice(self.retry_templates[field])
                return {"message": retry_msg}

            return {"message": "抱歉，我没有理解您的意思。请再试一次。"}
    
    def _generate_confirmation(self, extracted_info: Dict[str, Any]) -> str:
        """生成确认信息"""
        confirmations = []
        
        if "job_type" in extracted_info:
            confirmations.append(f"✅ 职位类型：{extracted_info['job_type']}")
        if "location" in extracted_info:
            confirmations.append(f"✅ 工作地点：{extracted_info['location']}")
        if "salary" in extracted_info:
            confirmations.append(f"✅ 薪资期望：{extracted_info['salary']}")
        
        if confirmations:
            return "好的，我记录下了：\n" + "\n".join(confirmations)
        return "好的，我明白了。"
    
    def _get_next_question(self) -> str:
        """获取下一个问题"""
        current_stage = self.state_manager.stage
        
        if current_stage in self.question_templates:
            return random.choice(self.question_templates[current_stage])
        
        return "请继续告诉我您的需求。"
    
    def _format_collected_info(self) -> str:
        """格式化已收集的信息"""
        req = self.state_manager.requirements
        info_lines = []
        
        if req.job_type:
            info_lines.append(f"🎯 职位类型：{req.job_type}")
        if req.location:
            info_lines.append(f"📍 工作地点：{req.location}")
        if req.salary:
            info_lines.append(f"💰 薪资期望：{req.salary}")
        
        return "\n".join(info_lines)
    
    def _generate_llm_response(self, user_input: str) -> str:
        """使用LLM生成个性化响应"""
        try:
            current_stage = self.state_manager.stage.value
            missing_fields = self.state_manager.requirements.get_missing_required_fields()
            
            prompt = f"""你是一个友好的求职助手，正在帮助用户收集求职需求。

当前阶段：{current_stage}
还需要收集的信息：{', '.join(missing_fields)}

用户刚才说："{user_input}"

请生成一个友好、耐心的回复，引导用户提供所需信息。回复要：
1. 简洁明了，不超过100字
2. 语气友好、鼓励性
3. 给出具体的例子
4. 使用emoji增加亲和力

回复："""
            
            response = self.llm.invoke(prompt)
            if hasattr(response, 'content'):
                return response.content.strip()
            else:
                return str(response).strip()
                
        except Exception as e:
            print(f"LLM生成响应失败: {e}")
            # 回退到模板响应
            return self._get_next_question()
    
    def get_search_query(self) -> str:
        """构建搜索查询"""
        req = self.state_manager.requirements
        query_parts = []
        
        if req.job_type:
            query_parts.append(req.job_type)
        if req.location:
            query_parts.append(req.location)
        if req.salary:
            # 简化薪资信息用于搜索
            salary_clean = req.salary.replace("以上", "").replace("左右", "").replace("面议", "")
            if salary_clean.strip():
                query_parts.append(salary_clean.strip())
        
        return " ".join(query_parts)
    
    def get_conversation_state(self) -> Dict[str, Any]:
        """获取完整的对话状态"""
        return self.state_manager.to_dict()
    
    def reset_conversation(self):
        """重置对话"""
        self.state_manager.reset()
