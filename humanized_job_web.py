#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人性化求职助手 - Web界面
基于Streamlit的流畅多轮对话界面
"""

import streamlit as st
import time
from typing import Dict, List, Any
from humanized_job_assistant import create_humanized_job_assistant
import json


def initialize_session_state():
    """初始化会话状态"""
    if 'assistant' not in st.session_state:
        st.session_state.assistant = None
    
    if 'system_initialized' not in st.session_state:
        st.session_state.system_initialized = False
    
    if 'conversation_started' not in st.session_state:
        st.session_state.conversation_started = False
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'current_stage' not in st.session_state:
        st.session_state.current_stage = "greeting"
    
    if 'progress' not in st.session_state:
        st.session_state.progress = {
            "percentage": 0,
            "completed_fields": 0,
            "total_required_fields": 3
        }
    
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    
    if 'search_completed' not in st.session_state:
        st.session_state.search_completed = False

    if 'job_count' not in st.session_state:
        st.session_state.job_count = 3  # 默认3个职位

    if 'ai_processing_info' not in st.session_state:
        st.session_state.ai_processing_info = []  # AI处理信息历史

    if 'show_ai_debug' not in st.session_state:
        st.session_state.show_ai_debug = False  # 是否显示AI调试信息


def initialize_system():
    """初始化求职助手系统"""
    if not st.session_state.system_initialized:
        with st.spinner("🔄 正在初始化人性化求职助手..."):
            assistant = create_humanized_job_assistant()
            init_result = assistant.initialize()
            
            if init_result["success"]:
                st.session_state.assistant = assistant
                st.session_state.system_initialized = True
                
                # 显示系统统计信息
                if "stats" in init_result:
                    stats = init_result["stats"]
                    vector_stats = stats.get("vector_store", {})
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📄 文档数量", vector_stats.get("total_documents", 0))
                    with col2:
                        st.metric("🧩 文本块数量", vector_stats.get("total_chunks", 0))
                    with col3:
                        last_update = vector_stats.get("last_update", "未知")
                        if len(last_update) > 10:
                            last_update = last_update[:10]
                        st.metric("📅 最后更新", last_update)
                
                st.success("✅ 系统初始化成功！")
                return True
            else:
                st.error(f"❌ 系统初始化失败: {init_result.get('error', '未知错误')}")
                return False
    return True


def start_conversation():
    """开始对话"""
    if not st.session_state.conversation_started:
        start_result = st.session_state.assistant.start_conversation()
        
        if start_result["success"]:
            st.session_state.messages.append({
                "role": "assistant",
                "content": start_result["message"],
                "timestamp": time.time()
            })
            st.session_state.current_stage = start_result.get("stage", "greeting")
            st.session_state.progress = start_result.get("progress", st.session_state.progress)
            st.session_state.conversation_started = True


def get_smart_input_placeholder(current_stage: str) -> str:
    """根据当前阶段获取智能输入提示"""
    placeholders = {
        "greeting": "请输入您的回答...",
        "job_type": "例如：Python开发工程师、UI设计师、产品经理...",
        "location": "例如：深圳、北京、上海、远程办公...",
        "salary": "例如：15-20K、月薪1万、年薪30万...",
        "search_completed": "搜索已完成"
    }
    return placeholders.get(current_stage, "请输入您的回答...")


def display_input_suggestions(current_stage: str):
    """显示输入建议"""
    suggestions = {
        "job_type": {
            "title": "💡 职位类型建议",
            "items": ["Python开发工程师", "Java开发工程师", "前端开发工程师", "UI设计师", "产品经理", "数据分析师"]
        },
        "location": {
            "title": "📍 地点建议",
            "items": ["深圳", "北京", "上海", "广州", "杭州", "远程办公"]
        },
        "salary": {
            "title": "💰 薪资格式建议",
            "items": ["15-20K", "月薪15000", "年薪30万", "20K以上", "面议"]
        }
    }

    if current_stage in suggestions:
        suggestion = suggestions[current_stage]
        with st.expander(suggestion["title"], expanded=False):
            cols = st.columns(3)
            for i, item in enumerate(suggestion["items"]):
                with cols[i % 3]:
                    if st.button(item, key=f"suggest_{current_stage}_{i}", use_container_width=True):
                        # 这里可以添加点击建议后的处理逻辑
                        st.info(f"💡 您可以输入：{item}")


def display_chat_interface():
    """显示聊天界面"""
    # 聊天消息容器
    chat_container = st.container()
    
    with chat_container:
        # 显示对话历史
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # 显示AI处理信息（如果启用调试模式）
                if (message["role"] == "assistant" and
                    st.session_state.show_ai_debug and
                    i < len(st.session_state.ai_processing_info)):

                    ai_info = st.session_state.ai_processing_info[i]
                    if ai_info:
                        with st.expander("🔍 AI处理详情", expanded=False):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("理解程度", "✅ 已理解" if ai_info.get('understood') else "❌ 未理解")
                                st.metric("置信度", f"{ai_info.get('confidence', 0):.1%}")
                            with col2:
                                extracted = ai_info.get('extracted_info', {})
                                if extracted:
                                    st.write("**提取信息:**")
                                    for key, value in extracted.items():
                                        st.write(f"- {key}: {value}")
                                else:
                                    st.write("**提取信息:** 无")

                # 如果是搜索结果消息，显示职位卡片
                if message.get("search_results"):
                    display_job_results(message["search_results"])
    
    # 用户输入区域
    if not st.session_state.search_completed:
        # 根据当前阶段提供智能输入提示
        input_placeholder = get_smart_input_placeholder(st.session_state.current_stage)
        user_input = st.chat_input(input_placeholder)

        # 显示输入建议
        if st.session_state.current_stage != "greeting":
            display_input_suggestions(st.session_state.current_stage)

        if user_input:
            # 添加用户消息
            st.session_state.messages.append({
                "role": "user",
                "content": user_input,
                "timestamp": time.time()
            })
            
            # 处理用户输入
            with st.spinner("🤔 正在智能分析您的输入..."):
                result = st.session_state.assistant.process_message(user_input, st.session_state.job_count)

            if result["success"]:
                # 保存AI处理信息（用于调试显示）
                ai_info = {
                    "user_input": user_input,
                    "understood": result.get("extracted_info", {}) != {},
                    "confidence": result.get("confidence", 0.0),
                    "extracted_info": result.get("extracted_info", {}),
                    "stage": result.get("stage", st.session_state.current_stage),
                    "timestamp": time.time()
                }
                st.session_state.ai_processing_info.append(ai_info)

                # 添加助手回复
                assistant_message = {
                    "role": "assistant",
                    "content": result["message"],
                    "timestamp": time.time()
                }

                # 如果有搜索结果，添加到消息中
                if "search_results" in result:
                    assistant_message["search_results"] = result["search_results"]
                    assistant_message["search_summary"] = result.get("search_summary", {})
                    st.session_state.search_results = result["search_results"]
                    st.session_state.search_completed = True

                st.session_state.messages.append(assistant_message)

                # 更新状态
                st.session_state.current_stage = result.get("stage", st.session_state.current_stage)
                st.session_state.progress = result.get("progress", st.session_state.progress)

                # 显示AI处理反馈
                if ai_info["understood"] and ai_info["extracted_info"]:
                    extracted = ai_info["extracted_info"]
                    feedback_parts = []
                    for key, value in extracted.items():
                        if key == "job_type":
                            feedback_parts.append(f"职位类型: {value}")
                        elif key == "location":
                            feedback_parts.append(f"工作地点: {value}")
                        elif key == "salary":
                            feedback_parts.append(f"薪资期望: {value}")

                    if feedback_parts:
                        st.success(f"✅ AI智能识别: {', '.join(feedback_parts)} (置信度: {ai_info['confidence']:.1%})")
                elif not ai_info["understood"]:
                    st.info("💡 AI正在引导您提供更准确的信息")
                
            else:
                st.error(f"❌ 处理消息失败: {result.get('error', '未知错误')}")
            
            # 刷新页面显示新消息
            st.rerun()


def display_progress_bar():
    """显示进度条"""
    progress = st.session_state.progress
    percentage = progress.get("percentage", 0)
    completed = progress.get("completed_fields", 0)
    total = progress.get("total_required_fields", 3)
    
    # 进度条
    st.progress(percentage / 100)
    
    # 进度文字
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(f"信息收集进度: {completed}/{total} 项完成")
    with col2:
        st.caption(f"{percentage:.0f}%")
    
    # 阶段指示器
    stages = ["问候", "职位类型", "工作地点", "薪资期望", "搜索中"]
    stage_map = {
        "greeting": 0,
        "job_type": 1,
        "location": 2,
        "salary": 3,
        "search_completed": 4
    }
    
    current_stage_index = stage_map.get(st.session_state.current_stage, 0)
    
    cols = st.columns(len(stages))
    for i, (col, stage) in enumerate(zip(cols, stages)):
        with col:
            if i < current_stage_index:
                st.success(f"✅ {stage}")
            elif i == current_stage_index:
                st.info(f"🔄 {stage}")
            else:
                st.caption(f"⏳ {stage}")


def display_job_results(search_results: List[Dict[str, Any]]):
    """显示职位搜索结果"""
    if not search_results:
        return

    st.markdown("---")
    st.subheader("🎉 为您找到以下匹配的职位：")

    # 搜索结果摘要
    st.info(f"📊 共找到 **{len(search_results)}** 个匹配职位，按薪资匹配度排序")

    # 显示搜索方法
    st.caption("🔬 使用混合检索技术：向量语义匹配 + 薪资精确过滤")

    # 创建标签页显示职位
    tabs = st.tabs([f"职位 {i+1}" for i in range(len(search_results))])

    for i, (tab, job) in enumerate(zip(tabs, search_results)):
        with tab:
            display_single_job(job, i+1)


def display_single_job(job: Dict[str, Any], rank: int):
    """显示单个职位详情"""
    # 职位标题
    st.markdown(f"### 🏢 {job['company_name']}")
    st.markdown(f"#### 💼 {job['job_title']}")

    # 核心信息卡片
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("💰 薪资", job.get('salary', '面议'))
    with col2:
        st.metric("📍 地点", job.get('location', '未知'))
    with col3:
        st.metric("🎓 学历", job.get('education', '未知'))
    with col4:
        st.metric("⏰经验", job.get('experience', '未知'))

    # 详细信息区域
    col_left, col_right = st.columns([2, 1])

    with col_left:
        # 职位描述
        if job.get('job_description'):
            st.subheader("📝 职位描述")
            with st.expander("点击查看详细描述", expanded=True):
                st.markdown(job['job_description'])

        # 公司信息
        st.subheader("🏢 公司信息")
        company_info_col1, company_info_col2 = st.columns(2)

        with company_info_col1:
            st.write(f"**公司全称**: {job.get('company_full_name', '未知')}")
            st.write(f"**公司规模**: {job.get('company_size', '未知')}")
            st.write(f"**主营业务**: {job.get('company_business', '未知')}")

        with company_info_col2:
            st.write(f"**职位类型**: {job.get('job_type', '未知')}")
            if job.get('internship_time'):
                st.write(f"**实习时间**: {job.get('internship_time', '未知')}")

        # 福利待遇
        if job.get('company_benefits') and job['company_benefits'] != '[空]':
            st.subheader("🎁 福利待遇")
            st.info(job['company_benefits'])

    with col_right:
        # 快速操作
        st.subheader("⚡ 快速操作")

        if st.button(f"💾 收藏职位", key=f"save_{rank}", use_container_width=True):
            st.success("✅ 已收藏到我的职位")

        if st.button(f"📧 投递简历", key=f"apply_{rank}", use_container_width=True):
            st.info("💡 简历投递功能开发中...")

        if st.button(f"🔗 查看详情", key=f"detail_{rank}", use_container_width=True):
            st.info("💡 详情页面开发中...")

        # 薪资匹配度显示
        st.subheader("🎯 薪资匹配度")

        # 从metadata中获取薪资匹配信息
        salary_match_score = job.get('salary_match_score', 0.0)
        salary_match_type = job.get('salary_match_type', '未知')

        if salary_match_score > 0:
            st.progress(salary_match_score)
            st.caption(f"薪资匹配: {salary_match_score:.1%} ({salary_match_type})")

            # 匹配度颜色提示
            if salary_match_score >= 0.8:
                st.success("🎯 薪资完全匹配")
            elif salary_match_score >= 0.5:
                st.info("📊 薪资高度匹配")
            elif salary_match_score >= 0.3:
                st.warning("⚠️ 薪资部分匹配")
            else:
                st.error("❌ 薪资匹配度较低")
        else:
            st.caption("💡 薪资匹配度: 待分析")

        # 地理位置
        if job.get('longitude') and job.get('latitude'):
            st.subheader("📍 地理位置")
            try:
                import pandas as pd
                map_data = pd.DataFrame({
                    'lat': [float(job['latitude'])],
                    'lon': [float(job['longitude'])]
                })
                st.map(map_data, zoom=12)
            except:
                st.write(f"经度: {job['longitude']}")
                st.write(f"纬度: {job['latitude']}")

    # 分隔线
    st.markdown("---")


def display_sidebar():
    """显示侧边栏"""
    with st.sidebar:
        st.header("🎯 求职助手")

        # 系统状态
        if st.session_state.system_initialized:
            st.success("✅ 系统已就绪")
        else:
            st.warning("⏳ 系统初始化中...")

        # 进度显示
        if st.session_state.conversation_started and not st.session_state.search_completed:
            st.subheader("📊 收集进度")
            display_progress_bar()

        # 搜索设置
        st.subheader("⚙️ 搜索设置")

        # 职位数量调整滑块
        new_job_count = st.slider(
            "🔍 职位显示数量",
            min_value=3,
            max_value=15,
            value=st.session_state.job_count,
            step=1,
            help="选择要显示的职位数量，更多职位意味着更全面的选择"
        )

        # 更新职位数量
        if new_job_count != st.session_state.job_count:
            st.session_state.job_count = new_job_count
            # 如果已经有搜索结果，提示重新搜索
            if st.session_state.search_completed:
                st.info("💡 职位数量已更新，点击重新搜索以应用新设置")

        # 显示当前设置
        st.caption(f"当前设置：显示 {st.session_state.job_count} 个职位")

        # AI智能处理统计
        if st.session_state.ai_processing_info:
            st.subheader("🤖 AI处理统计")

            total_inputs = len(st.session_state.ai_processing_info)
            understood_inputs = sum(1 for info in st.session_state.ai_processing_info if info.get('understood', False))
            avg_confidence = sum(info.get('confidence', 0) for info in st.session_state.ai_processing_info) / total_inputs if total_inputs > 0 else 0

            col1, col2 = st.columns(2)
            with col1:
                st.metric("理解率", f"{understood_inputs}/{total_inputs}")
            with col2:
                st.metric("平均置信度", f"{avg_confidence:.1%}")

            # AI调试开关
            st.session_state.show_ai_debug = st.checkbox(
                "🔍 显示AI处理详情",
                value=st.session_state.show_ai_debug,
                help="显示每次AI处理的详细信息，包括理解程度、置信度和提取信息"
            )

        # 操作按钮
        st.subheader("🛠️ 操作")
        
        if st.button("🔄 重新开始", use_container_width=True):
            # 重置对话
            if st.session_state.assistant:
                restart_result = st.session_state.assistant.restart_conversation()
                if restart_result["success"]:
                    st.session_state.messages = [{
                        "role": "assistant",
                        "content": restart_result["message"],
                        "timestamp": time.time()
                    }]
                    st.session_state.current_stage = "greeting"
                    st.session_state.progress = {
                        "percentage": 0,
                        "completed_fields": 0,
                        "total_required_fields": 3
                    }
                    st.session_state.search_results = []
                    st.session_state.search_completed = False
                    # 清理AI处理信息
                    st.session_state.ai_processing_info = []
                    st.rerun()
        
        if st.session_state.search_completed:
            if st.button("🔄 重新搜索", use_container_width=True):
                # 重新执行搜索，使用新的职位数量
                with st.spinner("🔍 正在重新搜索..."):
                    try:
                        search_result = st.session_state.assistant._perform_job_search(st.session_state.job_count)
                        if search_result["success"]:
                            # 更新搜索结果
                            st.session_state.search_results = search_result["results"]
                            st.success(f"✅ 重新搜索完成！找到 {len(search_result['results'])} 个职位")
                            st.rerun()
                        else:
                            st.error(f"❌ 重新搜索失败: {search_result['error']}")
                    except Exception as e:
                        st.error(f"❌ 重新搜索出错: {e}")

            if st.button("🔍 查看更多职位", use_container_width=True):
                st.info("💡 请调整上方的职位数量滑块，然后点击重新搜索")
        
        # 帮助信息
        st.subheader("💡 使用提示")
        st.markdown("""
        **智能对话特点：**
        - 🤖 **AI理解**：系统能智能理解您的自然语言输入
        - 🎯 **精准匹配**：混合检索技术确保薪资精确匹配
        - 💬 **友好引导**：遇到不清楚的输入会耐心引导

        **输入示例：**
        - 职位：python、前端、设计师、产品经理
        - 地点：深圳、北上广、远程办公
        - 薪资：15K、15-20K、月薪1万、年薪30万

        **AI会自动：**
        - ✅ 理解简化输入（如"python"→"Python开发工程师"）
        - ✅ 补全缺失信息（如"15-20"→"15-20K"）
        - ✅ 识别无效输入并友好提示
        """)


def main():
    """主函数"""
    st.set_page_config(
        page_title="人性化求职助手",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 初始化会话状态
    initialize_session_state()
    
    # 页面标题
    st.title("🤖 人性化求职助手")
    st.markdown("**智能对话，精准匹配，让求职更简单**")
    
    # 显示侧边栏
    display_sidebar()
    
    # 初始化系统
    if not initialize_system():
        st.stop()
    
    # 开始对话
    start_conversation()
    
    # 显示聊天界面
    display_chat_interface()
    
    # 页脚
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
            🤖 人性化求职助手 | 基于AI的智能对话求职系统 | 
            <a href="#" style="color: #1f77b4;">使用说明</a> | 
            <a href="#" style="color: #1f77b4;">意见反馈</a>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
