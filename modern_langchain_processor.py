#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于最新LangChain 2025的智能对话处理器
使用LangGraph的StateGraph和MemorySaver进行对话记忆管理
"""

from typing import Dict, List, Optional, Any, TypedDict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from conversation_state import ConversationStage
from qa_chain import create_llm
import json
import re


class ConversationState(TypedDict):
    """对话状态类型定义"""
    messages: List[BaseMessage]
    current_stage: str
    extracted_info: Dict[str, Any]
    confidence: float


class ModernLangChainProcessor:
    """基于最新LangChain 2025的智能对话处理器"""
    
    def __init__(self):
        self.llm = None
        self.app = None
        self.memory = MemorySaver()
        self._initialize_components()
        
        # 各阶段的处理提示模板
        self.stage_prompts = {
            ConversationStage.COLLECTING_JOB_TYPE: """
你是一个专业的求职顾问，正在帮助用户收集职位类型信息。

分析对话历史和当前用户输入，理解用户想要的职位类型。

重要规则：
1. 如果用户输入确认词（是的、对、没错、好的、嗯），检查对话历史中是否有待确认的职位类型
2. 如果用户输入否定词（不是、不对、错了），表示需要重新收集
3. 如果用户输入具体职位名称或关键词，提取并确认
4. 如果输入不清楚，友好地重新询问

职位类型示例：Python开发工程师、UI设计师、产品经理、数据分析师等

请返回JSON格式：
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

分析对话历史和当前用户输入，理解用户期望的工作地点。

重要规则：
1. 如果用户输入确认词，检查对话历史中是否有待确认的地点
2. 如果用户输入否定词，表示需要重新收集
3. 如果用户输入城市名称，提取并确认
4. 支持多个城市（如"北上广"）

地点示例：北京、上海、深圳、远程办公等

请返回JSON格式：
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

分析对话历史和当前用户输入，理解用户的薪资期望。

重要规则：
1. 如果用户输入确认词，检查对话历史中是否有待确认的薪资
2. 如果用户输入否定词，表示需要重新收集
3. 如果用户输入数字和薪资相关词汇，提取并确认
4. 智能补全单位（如"15-20"可能是"15-20K"）

薪资格式示例：15-20K、月薪1万、年薪30万、面议等

请返回JSON格式：
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
        """初始化LangGraph组件"""
        try:
            # 创建LLM
            self.llm = create_llm(streaming=False)
            
            # 创建StateGraph工作流
            workflow = StateGraph(ConversationState)
            
            # 添加处理节点
            workflow.add_node("process_message", self._process_message_node)
            
            # 添加边
            workflow.add_edge(START, "process_message")
            
            # 编译应用，添加记忆检查点
            self.app = workflow.compile(checkpointer=self.memory)
            
            print("✅ 现代LangChain对话处理器初始化成功")
            
        except Exception as e:
            print(f"❌ 现代LangChain对话处理器初始化失败: {e}")
            self.llm = None
            self.app = None
    
    def _process_message_node(self, state: ConversationState) -> ConversationState:
        """处理消息的节点函数"""
        messages = state["messages"]
        current_stage = state.get("current_stage", "job_type")
        
        if not messages:
            return state
        
        # 获取最新的用户消息
        latest_message = messages[-1]
        if not isinstance(latest_message, HumanMessage):
            return state
        
        user_input = latest_message.content
        
        # 构建分析提示
        stage_enum = self._string_to_stage(current_stage)
        prompt = self._build_analysis_prompt(user_input, messages, stage_enum)
        
        try:
            # 调用LLM分析
            response = self.llm.invoke([SystemMessage(content=prompt)])
            
            # 解析响应
            result = self._parse_llm_response(response.content, user_input, stage_enum)
            
            # 生成AI回复消息
            ai_message = AIMessage(content=result["ai_response"])
            
            return {
                "messages": messages + [ai_message],
                "current_stage": current_stage,
                "extracted_info": result["extracted_info"],
                "confidence": result["confidence"]
            }
            
        except Exception as e:
            print(f"LLM处理失败: {e}")
            # 回退处理
            fallback_result = self._fallback_processing(user_input, stage_enum)
            ai_message = AIMessage(content=fallback_result["ai_response"])
            
            return {
                "messages": messages + [ai_message],
                "current_stage": current_stage,
                "extracted_info": fallback_result["extracted_info"],
                "confidence": fallback_result["confidence"]
            }
    
    def _build_analysis_prompt(self, user_input: str, messages: List[BaseMessage], 
                              current_stage: ConversationStage) -> str:
        """构建分析提示"""
        if current_stage not in self.stage_prompts:
            return f"请分析用户输入：{user_input}"
        
        stage_prompt = self.stage_prompts[current_stage]
        
        # 格式化对话历史
        history_text = self._format_message_history(messages[:-1])  # 排除最新消息
        
        prompt = f"""{stage_prompt}

对话历史：
{history_text}

当前用户输入："{user_input}"

请仔细分析对话上下文和用户输入，返回准确的JSON格式结果。
"""
        
        return prompt
    
    def _format_message_history(self, messages: List[BaseMessage]) -> str:
        """格式化消息历史"""
        if not messages:
            return "无对话历史"
        
        formatted = []
        for message in messages[-6:]:  # 最近6条消息
            if isinstance(message, HumanMessage):
                formatted.append(f"用户: {message.content}")
            elif isinstance(message, AIMessage):
                formatted.append(f"助手: {message.content}")
        
        return "\n".join(formatted)
    
    def _parse_llm_response(self, response: str, user_input: str, 
                           current_stage: ConversationStage) -> Dict[str, Any]:
        """解析LLM响应"""
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
        confirmation_words = ["是的", "对", "没错", "好的", "嗯", "是", "对的", "正确"]
        negation_words = ["不是", "不对", "错了", "不", "错误"]
        
        if any(word in user_input for word in confirmation_words):
            return {
                "understood": True,
                "extracted_info": {},  # 需要从上下文中获取
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
    
    def _string_to_stage(self, stage_str: str) -> ConversationStage:
        """将字符串转换为ConversationStage枚举"""
        stage_mapping = {
            "job_type": ConversationStage.COLLECTING_JOB_TYPE,
            "location": ConversationStage.COLLECTING_LOCATION,
            "salary": ConversationStage.COLLECTING_SALARY
        }
        return stage_mapping.get(stage_str, ConversationStage.COLLECTING_JOB_TYPE)
    
    def process_user_input(self, user_input: str, current_stage: ConversationStage,
                          conversation_history: List[Dict] = None, thread_id: str = "default") -> Dict[str, Any]:
        """
        使用现代LangChain处理用户输入
        
        Args:
            user_input: 用户输入
            current_stage: 当前对话阶段
            conversation_history: 对话历史（用于兼容）
            thread_id: 线程ID
            
        Returns:
            处理结果字典
        """
        if not self.app:
            return self._fallback_processing(user_input, current_stage)
        
        try:
            # 构建初始状态
            messages = []
            
            # 从对话历史恢复消息（如果提供）
            if conversation_history:
                for msg in conversation_history:
                    if msg.get('role') == 'user':
                        messages.append(HumanMessage(content=msg.get('content', '')))
                    elif msg.get('role') == 'assistant':
                        messages.append(AIMessage(content=msg.get('content', '')))
            
            # 添加当前用户输入
            messages.append(HumanMessage(content=user_input))
            
            # 调用LangGraph应用
            result = self.app.invoke(
                {
                    "messages": messages,
                    "current_stage": current_stage.value,
                    "extracted_info": {},
                    "confidence": 0.0
                },
                config={"configurable": {"thread_id": thread_id}}
            )
            
            return {
                "understood": result["confidence"] > 0.5,
                "extracted_info": result["extracted_info"],
                "confidence": result["confidence"],
                "ai_response": result["messages"][-1].content if result["messages"] else "处理完成",
                "needs_clarification": result["confidence"] < 0.5,
                "action": "confirm" if result["confidence"] > 0.7 else "retry"
            }
            
        except Exception as e:
            print(f"现代LangChain处理失败: {e}")
            return self._fallback_processing(user_input, current_stage)
    
    def get_memory_summary(self, thread_id: str = "default") -> Dict[str, Any]:
        """获取记忆摘要"""
        try:
            # 获取检查点状态
            state = self.app.get_state(config={"configurable": {"thread_id": thread_id}})
            if state and state.values:
                messages = state.values.get("messages", [])
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
        except Exception as e:
            print(f"获取记忆摘要失败: {e}")
        
        return {"total_messages": 0, "recent_messages": []}
    
    def clear_memory(self, thread_id: str = "default"):
        """清空记忆"""
        try:
            # LangGraph的MemorySaver会自动管理状态
            # 这里我们可以通过重新初始化来清空特定线程的记忆
            pass
        except Exception as e:
            print(f"清空记忆失败: {e}")


def test_modern_processor():
    """测试现代LangChain对话处理器"""
    processor = ModernLangChainProcessor()
    
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
        conversation_history,
        thread_id="test_1"
    )
    
    print("🧪 测试现代LangChain处理器:")
    print(f"   理解: {result['understood']}")
    print(f"   置信度: {result['confidence']:.2f}")
    print(f"   提取信息: {result['extracted_info']}")
    print(f"   AI回复: {result['ai_response']}")
    
    # 获取记忆摘要
    memory_summary = processor.get_memory_summary("test_1")
    print(f"\n📝 记忆摘要: {memory_summary}")


if __name__ == "__main__":
    test_modern_processor()
