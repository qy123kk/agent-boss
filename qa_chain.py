#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问答链模块
负责创建和管理问答链，包括流式输出和对话记忆
"""

import os
import queue
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.base import BaseCallbackHandler

# 加载环境变量
load_dotenv()


class StreamingCallbackHandler(BaseCallbackHandler):
    """用于流式输出的回调处理器"""
    
    def __init__(self):
        self.queue = queue.Queue()
        self.streaming_active = True
        self.last_token = ""
        
    def on_llm_new_token(self, token: str, **kwargs):
        """当LLM生成新token时调用"""
        if self.streaming_active:
            self.last_token = token
            self.queue.put(token)
        return token
        
    def on_llm_end(self, response, **kwargs):
        """当LLM生成结束时调用"""
        self.streaming_active = False
        self.queue.put(None)  # 发送结束信号
        
    def on_llm_error(self, error, **kwargs):
        """当LLM发生错误时调用"""
        self.streaming_active = False
        self.queue.put(None)  # 发送结束信号
        
    def get_tokens(self):
        """获取生成的token流"""
        while self.streaming_active or not self.queue.empty():
            try:
                token = self.queue.get(timeout=0.1)
                if token is None:  # 结束信号
                    break
                yield token
            except queue.Empty:
                continue


def get_api_key():
    """获取API密钥"""
    api_key = os.getenv("DASHSCOPE_API_KEY", "sk-ea76fba3b52045579e38a398598ff512")
    if not api_key:
        raise ValueError("请设置DASHSCOPE_API_KEY环境变量")
    return api_key


def create_llm(streaming: bool = True):
    """创建LLM实例"""
    api_key = get_api_key()
    return ChatOpenAI(
        model="deepseek-v3",  # 使用DeepSeek模型
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0.1,
        streaming=streaming
    )


def create_memory(conversation_history: Optional[List[Dict]] = None):
    """创建对话记忆"""
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        human_prefix="用户",
        ai_prefix="助手"
    )
    
    # 如果有对话历史，恢复到内存中
    if conversation_history:
        restore_conversation_history(memory, conversation_history)
    
    return memory


def restore_conversation_history(memory, conversation_history):
    """将对话历史恢复到内存中"""
    if not conversation_history:
        return

    for message in conversation_history:
        if message['role'] == 'user':
            memory.chat_memory.add_user_message(message['content'])
        elif message['role'] == 'assistant':
            memory.chat_memory.add_ai_message(message['content'])


def create_prompt_template(system_prompt: str = ""):
    """创建优化的提示模板"""
    if not system_prompt:
        system_prompt = "你是一个智能助手，专门帮助分析Excel表格数据，请根据提供的结构化文档内容准确回答用户的问题。"

    return PromptTemplate(
        input_variables=["context", "question", "chat_history"],
        template=f"""你是一个专业的数据分析助手，请根据以下设定回答问题：

【角色设定】{system_prompt}

【重要提示】
- 请仔细阅读参考资料中的结构化信息
- 优先使用"核心信息"部分的数据
- 回答要准确、简洁、有条理
- 如果涉及多个结果，请分条列出

【对话历史】
{{chat_history}}

【参考资料】
{{context}}

【用户问题】
{{question}}

【回答】："""
    )


def setup_qa_chain(vector_store, system_prompt: str = "", conversation_history: Optional[List[Dict]] = None):
    """设置基础问答链"""
    print(f"正在设置问答链，系统提示: {system_prompt[:20]}...")

    # 创建LLM
    llm = create_llm(streaming=False)
    
    # 创建记忆
    memory = create_memory(conversation_history)
    
    # 创建提示模板
    prompt = create_prompt_template(system_prompt)

    # 创建优化的检索器
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}  # 增加检索结果数量
    )

    # 创建QA链
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt}
    )

    return qa_chain, memory


def setup_streaming_qa_chain(vector_store, system_prompt: str = "", conversation_history: Optional[List[Dict]] = None):
    """设置流式问答链"""
    print(f"正在设置流式问答链，系统提示: {system_prompt[:20]}...")

    # 创建流式回调处理器
    streaming_handler = StreamingCallbackHandler()

    # 创建LLM
    llm = create_llm(streaming=True)
    
    # 创建记忆
    memory = create_memory(conversation_history)
    
    # 创建提示模板
    prompt = create_prompt_template(system_prompt)

    # 创建优化的检索器
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}  # 增加检索结果数量
    )

    # 创建QA链
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        callbacks=[streaming_handler],
        combine_docs_chain_kwargs={"prompt": prompt}
    )

    return qa_chain, streaming_handler


def ask_question(qa_chain, question: str):
    """提问并获取答案"""
    try:
        result = qa_chain.invoke({"question": question})
        return result.get("answer", "抱歉，我无法回答这个问题。")
    except Exception as e:
        return f"处理问题时出错: {str(e)}"


def ask_question_streaming(qa_chain, streaming_handler, question: str):
    """流式提问并获取答案"""
    try:
        # 启动问答
        qa_chain.invoke({"question": question})
        
        # 收集流式输出
        answer = ""
        for token in streaming_handler.get_tokens():
            answer += token
            yield token
        
        return answer
    except Exception as e:
        error_msg = f"处理问题时出错: {str(e)}"
        yield error_msg
        return error_msg
