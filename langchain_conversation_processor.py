#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于LangChain的智能对话处理器
使用ConversationBufferMemory管理对话历史，提供上下文感知的智能处理
"""

from typing import Dict, List, Optional, Any
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from conversation_state import ConversationStage
from qa_chain import create_llm
import json
import re


class LangChainConversationProcessor:
    """基于LangChain的智能对话处理器"""
    
    def __init__(self):
        self.llm = None
        self.memory = None
        self.conversation_chain = None
        self._initialize_components()
        
        # 各阶段的处理提示模板
        self.stage_prompts = {
            ConversationStage.COLLECTING_JOB_TYPE: """
你是一个专业的求职顾问，正在帮助用户收集职位类型信息。

当前任务：理解用户想要的职位类型

职位类型示例：
- 技术类：Python开发工程师、前端开发、Java工程师、数据分析师
- 设计类：UI设计师、UX设计师、平面设计师
- 管理类：产品经理、项目经理、运营经理
- 其他：销售代表、人事专员、财务分析师

重要规则：
1. 如果用户输入确认词（是的、对、没错、好的、嗯），检查对话历史中是否有待确认的职位类型
2. 如果用户输入否定词（不是、不对、错了），表示需要重新收集
3. 如果用户输入具体职位名称或关键词，提取并确认
4. 如果输入不清楚，友好地重新询问

请根据对话历史和当前输入，返回JSON格式：
{{
    "understood": true/false,
    "job_type": "提取的职位类型" 或 null,
    "confidence": 0.0-1.0,
    "response": "给用户的回复",
    "action": "confirm/extract/retry"
}}
""",
            
            ConversationStage.COLLECTING_LOCATION: """
你是一个专业的求职顾问，正在帮助用户收集工作地点信息。

当前任务：理解用户期望的工作地点

地点示例：
- 一线城市：北京、上海、广州、深圳
- 新一线城市：杭州、成都、武汉、南京、西安
- 特殊情况：远程办公、在家办公、不限地点

重要规则：
1. 如果用户输入确认词，检查对话历史中是否有待确认的地点
2. 如果用户输入否定词，表示需要重新收集
3. 如果用户输入城市名称，提取并确认
4. 支持多个城市（如"北上广"）

请根据对话历史和当前输入，返回JSON格式：
{{
    "understood": true/false,
    "location": "提取的地点" 或 null,
    "confidence": 0.0-1.0,
    "response": "给用户的回复",
    "action": "confirm/extract/retry"
}}
""",
            
            ConversationStage.COLLECTING_SALARY: """
你是一个专业的求职顾问，正在帮助用户收集薪资期望信息。

当前任务：理解用户的薪资期望

薪资格式示例：
- 范围：15-20K、10-15万、8千-1万2
- 单一：15K、20万、月薪12000
- 模糊：20K以上、15万左右、面议

重要规则：
1. 如果用户输入确认词，检查对话历史中是否有待确认的薪资
2. 如果用户输入否定词，表示需要重新收集
3. 如果用户输入数字和薪资相关词汇，提取并确认
4. 智能补全单位（如"15-20"可能是"15-20K"）

请根据对话历史和当前输入，返回JSON格式：
{{
    "understood": true/false,
    "salary": "提取的薪资" 或 null,
    "confidence": 0.0-1.0,
    "response": "给用户的回复",
    "action": "confirm/extract/retry"
}}
"""
        }
    
    def _initialize_components(self):
        """初始化LangChain组件"""
        try:
            # 创建LLM
            self.llm = create_llm(streaming=False)
            
            # 创建对话记忆
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                human_prefix="用户",
                ai_prefix="助手"
            )
            
            print("✅ LangChain对话处理器初始化成功")
            
        except Exception as e:
            print(f"❌ LangChain对话处理器初始化失败: {e}")
            self.llm = None
            self.memory = None
    
    def process_user_input(self, user_input: str, current_stage: ConversationStage,
                          conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        使用LangChain处理用户输入
        
        Args:
            user_input: 用户输入
            current_stage: 当前对话阶段
            conversation_history: 对话历史（用于恢复记忆）
            
        Returns:
            处理结果字典
        """
        if not self.llm or not self.memory:
            return self._fallback_processing(user_input, current_stage)
        
        try:
            # 恢复对话历史到记忆中
            if conversation_history:
                self._restore_memory(conversation_history)
            
            # 添加当前用户输入到记忆
            self.memory.chat_memory.add_user_message(user_input)
            
            # 获取对话历史
            chat_history = self.memory.chat_memory.messages
            
            # 构建提示
            prompt = self._build_langchain_prompt(user_input, current_stage, chat_history)
            
            # 创建LLM链
            chain = LLMChain(
                llm=self.llm,
                prompt=PromptTemplate(
                    input_variables=["user_input", "chat_history"],
                    template=prompt
                ),
                memory=self.memory,
                verbose=False
            )
            
            # 执行链
            response = chain.run(
                user_input=user_input,
                chat_history=self._format_chat_history(chat_history)
            )
            
            # 解析AI响应
            result = self._parse_ai_response(response, user_input, current_stage)
            
            # 添加AI响应到记忆
            self.memory.chat_memory.add_ai_message(result.get("ai_response", ""))
            
            return result
            
        except Exception as e:
            print(f"LangChain处理失败: {e}")
            return self._fallback_processing(user_input, current_stage)
    
    def _restore_memory(self, conversation_history: List[Dict]):
        """恢复对话历史到记忆中"""
        # 清空当前记忆
        self.memory.chat_memory.clear()
        
        # 恢复历史对话
        for message in conversation_history:
            if message.get('role') == 'user':
                self.memory.chat_memory.add_user_message(message.get('content', ''))
            elif message.get('role') == 'assistant':
                self.memory.chat_memory.add_ai_message(message.get('content', ''))
    
    def _format_chat_history(self, chat_history: List[BaseMessage]) -> str:
        """格式化对话历史"""
        if not chat_history:
            return "无对话历史"
        
        formatted = []
        for message in chat_history[-6:]:  # 最近6条消息
            if isinstance(message, HumanMessage):
                formatted.append(f"用户: {message.content}")
            elif isinstance(message, AIMessage):
                formatted.append(f"助手: {message.content}")
        
        return "\n".join(formatted)
    
    def _build_langchain_prompt(self, user_input: str, current_stage: ConversationStage,
                               chat_history: List[BaseMessage]) -> str:
        """构建LangChain提示"""
        if current_stage not in self.stage_prompts:
            return f"请分析用户输入：{user_input}"
        
        stage_prompt = self.stage_prompts[current_stage]
        
        prompt = f"""{stage_prompt}

对话历史：
{{chat_history}}

当前用户输入：{{user_input}}

请仔细分析对话上下文和用户输入，返回准确的JSON格式结果。
"""
        
        return prompt
    
    def _parse_ai_response(self, response: str, user_input: str, 
                          current_stage: ConversationStage) -> Dict[str, Any]:
        """解析AI响应"""
        try:
            # 尝试解析JSON
            if '{' in response and '}' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                
                return {
                    "understood": result.get("understood", False),
                    "extracted_info": self._extract_info_from_result(result, current_stage),
                    "confidence": result.get("confidence", 0.0),
                    "ai_response": result.get("response", response),
                    "needs_clarification": not result.get("understood", False),
                    "action": result.get("action", "retry")
                }
            else:
                # 如果不是JSON格式，尝试从文本中提取信息
                return self._extract_from_text(response, user_input, current_stage)
                
        except json.JSONDecodeError:
            return self._extract_from_text(response, user_input, current_stage)
    
    def _extract_info_from_result(self, result: Dict, current_stage: ConversationStage) -> Dict[str, Any]:
        """从AI结果中提取信息"""
        extracted = {}
        
        if current_stage == ConversationStage.COLLECTING_JOB_TYPE:
            job_type = result.get("job_type")
            if job_type:
                extracted["job_type"] = job_type
        elif current_stage == ConversationStage.COLLECTING_LOCATION:
            location = result.get("location")
            if location:
                extracted["location"] = location
        elif current_stage == ConversationStage.COLLECTING_SALARY:
            salary = result.get("salary")
            if salary:
                extracted["salary"] = salary
        
        return extracted
    
    def _extract_from_text(self, response: str, user_input: str, 
                          current_stage: ConversationStage) -> Dict[str, Any]:
        """从文本响应中提取信息"""
        # 简单的文本解析逻辑
        understood = "理解" in response and "不理解" not in response
        
        return {
            "understood": understood,
            "extracted_info": {},
            "confidence": 0.3 if understood else 0.0,
            "ai_response": response,
            "needs_clarification": True,
            "action": "retry"
        }
    
    def _fallback_processing(self, user_input: str, current_stage: ConversationStage) -> Dict[str, Any]:
        """回退处理逻辑"""
        # 简单的确认词检测
        confirmation_words = ["是的", "对", "没错", "好的", "嗯", "是", "对的", "正确"]
        negation_words = ["不是", "不对", "错了", "不", "错误"]

        user_lower = user_input.lower().strip()

        if any(word in user_input for word in confirmation_words):
            # 尝试从对话历史中提取待确认的信息
            extracted_info = self._extract_from_context(current_stage)

            return {
                "understood": True,
                "extracted_info": extracted_info,
                "confidence": 0.8,
                "ai_response": "好的，我明白了。",
                "needs_clarification": False,
                "action": "confirm"
            }
        elif any(word in user_input for word in negation_words):
            return {
                "understood": True,
                "extracted_info": {},
                "confidence": 0.8,
                "ai_response": "好的，让我们重新开始。",
                "needs_clarification": True,
                "action": "retry"
            }

        return {
            "understood": False,
            "extracted_info": {},
            "confidence": 0.0,
            "ai_response": "抱歉，我没有理解您的意思，请再试一次。",
            "needs_clarification": True,
            "action": "retry"
        }

    def _extract_from_context(self, current_stage: ConversationStage) -> Dict[str, Any]:
        """从对话上下文中提取待确认的信息"""
        if not self.memory or not self.memory.chat_memory.messages:
            return {}

        # 获取最近的AI消息，查找待确认的信息
        recent_messages = self.memory.chat_memory.messages[-3:]  # 最近3条消息

        for message in reversed(recent_messages):
            if isinstance(message, AIMessage):
                content = message.content

                # 根据当前阶段提取相应信息
                if current_stage == ConversationStage.COLLECTING_JOB_TYPE:
                    # 查找职位类型相关的确认问题
                    patterns = [
                        r'您是想找(.+?)的职位吗',
                        r'您指的是(.+?)吗',
                        r'职位类型是(.+?)对吗',
                        r'(.+?)开发工程师',
                        r'(.+?)工程师',
                        r'(.+?)设计师',
                        r'(.+?)经理'
                    ]

                    for pattern in patterns:
                        import re
                        match = re.search(pattern, content)
                        if match:
                            job_type = match.group(1).strip()
                            if job_type:
                                return {"job_type": job_type}

                elif current_stage == ConversationStage.COLLECTING_LOCATION:
                    # 查找地点相关的确认问题
                    patterns = [
                        r'工作地点是(.+?)对吗',
                        r'您希望在(.+?)工作',
                        r'地点是(.+?)吗'
                    ]

                    for pattern in patterns:
                        import re
                        match = re.search(pattern, content)
                        if match:
                            location = match.group(1).strip()
                            if location:
                                return {"location": location}

                elif current_stage == ConversationStage.COLLECTING_SALARY:
                    # 查找薪资相关的确认问题
                    patterns = [
                        r'薪资期望是(.+?)对吗',
                        r'薪资(.+?)吗',
                        r'期望(.+?)对吗'
                    ]

                    for pattern in patterns:
                        import re
                        match = re.search(pattern, content)
                        if match:
                            salary = match.group(1).strip()
                            if salary:
                                return {"salary": salary}

        return {}
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """获取记忆摘要"""
        if not self.memory:
            return {}
        
        messages = self.memory.chat_memory.messages
        return {
            "total_messages": len(messages),
            "recent_messages": [
                {
                    "type": type(msg).__name__,
                    "content": msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                }
                for msg in messages[-4:]
            ]
        }
    
    def clear_memory(self):
        """清空记忆"""
        if self.memory:
            self.memory.chat_memory.clear()


def test_langchain_processor():
    """测试LangChain对话处理器"""
    processor = LangChainConversationProcessor()
    
    # 模拟对话流程
    conversation_history = [
        {"role": "assistant", "content": "请告诉我您想要的职位类型？"},
        {"role": "user", "content": "python"},
        {"role": "assistant", "content": "您是想找Python开发工程师的职位吗？"}
    ]
    
    # 测试确认回复
    result = processor.process_user_input(
        "是的", 
        ConversationStage.COLLECTING_JOB_TYPE,
        conversation_history
    )
    
    print("🧪 测试确认回复:")
    print(f"   理解: {result['understood']}")
    print(f"   置信度: {result['confidence']:.2f}")
    print(f"   提取信息: {result['extracted_info']}")
    print(f"   AI回复: {result['ai_response']}")
    
    # 获取记忆摘要
    memory_summary = processor.get_memory_summary()
    print(f"\n📝 记忆摘要: {memory_summary}")


if __name__ == "__main__":
    test_langchain_processor()
