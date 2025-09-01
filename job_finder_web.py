#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能求职助手 - Web界面
简洁的求职搜索工具
"""

import streamlit as st
import time
from simple_job_finder import SimpleJobFinder
from incremental_vector_store import IncrementalVectorStore
from resume_advisor import create_resume_advisor


def initialize_session_state():
    """初始化会话状态"""
    if 'job_finder' not in st.session_state:
        st.session_state.job_finder = None
    
    if 'system_initialized' not in st.session_state:
        st.session_state.system_initialized = False
    
    if 'search_completed' not in st.session_state:
        st.session_state.search_completed = False
    
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []

    if 'resume_advisor' not in st.session_state:
        st.session_state.resume_advisor = None

    if 'resume_advice_cache' not in st.session_state:
        st.session_state.resume_advice_cache = {}

    if 'selected_job_for_advice' not in st.session_state:
        st.session_state.selected_job_for_advice = None


def initialize_system():
    """初始化求职系统"""
    if not st.session_state.system_initialized:
        with st.spinner("🔄 正在初始化智能求职助手..."):
            # 显示向量存储状态
            vector_manager = IncrementalVectorStore("vector_store")

            # 检查更新需求
            update_info = vector_manager.check_updates_needed('documents')
            if update_info['needs_update']:
                if update_info['new_files']:
                    st.info(f"📄 发现 {len(update_info['new_files'])} 个新文件，正在更新向量存储...")
                if update_info['modified_files']:
                    st.info(f"📝 发现 {len(update_info['modified_files'])} 个修改文件，正在重建向量存储...")

            finder = SimpleJobFinder()
            if finder.initialize():
                st.session_state.job_finder = finder
                # 初始化简历建议器
                st.session_state.resume_advisor = create_resume_advisor(finder.rag_system)
                st.session_state.system_initialized = True
                st.success("✅ 系统初始化成功！")

                # 显示向量存储统计
                metadata = vector_manager._load_metadata()
                if metadata:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📄 文档数量", metadata.get('total_documents', 0))
                    with col2:
                        st.metric("🧩 文本块数量", metadata.get('total_chunks', 0))
                    with col3:
                        st.metric("📅 最后更新", metadata.get('last_update', '未知')[:10])

                return True
            else:
                st.error("❌ 系统初始化失败，请检查配置")
                return False
    return True


def display_job_search_form():
    """显示求职搜索表单"""
    st.header("🎯 智能求职搜索")
    st.markdown("请填写您的求职需求，我们将为您找到最合适的工作机会：")
    
    with st.form("job_search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            job_type = st.text_input(
                "🔹 职位类型",
                placeholder="如：Python开发、UI设计师、产品经理",
                help="请输入您想要的职位类型"
            )
            
            salary = st.text_input(
                "💰 期望薪资",
                placeholder="如：15-20K、20K以上",
                help="请输入您的期望薪资范围"
            )
            
            education = st.selectbox(
                "🎓 学历背景",
                ["", "大专", "本科", "硕士", "博士", "学历不限"],
                help="选择您的学历背景"
            )
        
        with col2:
            location = st.selectbox(
                "📍 工作地点",
                ["", "深圳", "北京", "上海", "广州", "杭州", "其他"],
                help="选择您期望的工作城市"
            )
            
            experience = st.text_input(
                "⏰ 工作经验",
                placeholder="如：1-3年、应届生、5年以上",
                help="请输入您的工作经验"
            )
            
            search_count = st.slider(
                "🔍 搜索结果数量",
                min_value=3,
                max_value=10,
                value=6,
                help="选择要显示的职位数量"
            )
        
        submitted = st.form_submit_button("🚀 开始搜索", use_container_width=True)
        
        if submitted:
            if not job_type.strip():
                st.error("❌ 请至少填写职位类型")
                return
            
            # 构建搜索需求
            requirements = {}
            if job_type.strip():
                requirements['job_type'] = job_type.strip()
            if salary.strip():
                requirements['salary'] = salary.strip()
            if education:
                requirements['education'] = education
            if location:
                requirements['location'] = location
            if experience.strip():
                requirements['experience'] = experience.strip()
            
            # 执行搜索
            perform_search(requirements, search_count)


def perform_search(requirements, search_count):
    """执行搜索"""
    st.session_state.job_finder.user_requirements = requirements
    
    with st.spinner("🔍 正在搜索匹配的职位..."):
        # 构建搜索查询
        search_query = st.session_state.job_finder._build_search_query()
        
        try:
            # 执行搜索
            results = st.session_state.job_finder.rag_system.search(search_query, k=search_count)
            
            if results:
                st.session_state.search_results = results
                st.session_state.search_completed = True
                st.success(f"✅ 找到 {len(results)} 个匹配的职位！")
                st.rerun()
            else:
                st.warning("😔 没有找到符合要求的职位，请尝试调整搜索条件")
                
        except Exception as e:
            st.error(f"❌ 搜索失败: {e}")


def display_search_results():
    """显示搜索结果"""
    if not st.session_state.search_results:
        return
    
    st.header("🎉 搜索结果")
    st.markdown(f"为您找到 **{len(st.session_state.search_results)}** 个匹配的职位：")
    
    # 创建标签页
    tabs = st.tabs([f"职位 {i+1}" for i in range(len(st.session_state.search_results))])
    
    for i, (tab, doc) in enumerate(zip(tabs, st.session_state.search_results)):
        with tab:
            display_job_detail(doc, i+1)
    
    # 搜索总结
    display_search_summary()


def display_job_detail(doc, job_number):
    """显示单个职位详情"""
    metadata = doc.metadata
    structured_fields = metadata.get('structured_fields', {})
    
    # 职位标题
    st.subheader(f"🔹 {metadata.get('job_title', '未知职位')}")
    st.markdown(f"**🏢 {metadata.get('company_name', '未知公司')}**")
    
    # 核心信息卡片
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💰 薪资待遇", metadata.get('salary', '面议'))
        st.metric("🎓 学历要求", metadata.get('education', '未知'))
    
    with col2:
        st.metric("⏰ 工作经验", metadata.get('experience', '未知'))
        st.metric("📍 工作地点", metadata.get('location', '未知'))
    
    with col3:
        st.metric("🔄 实习机会", structured_fields.get('实习时间', '未知'))
        st.metric("💼 职位类型", structured_fields.get('职位类型', '未知'))
    
    # 职位详情
    job_info = structured_fields.get('职位信息', '')
    if job_info and job_info.strip():
        st.subheader("📝 职位详情")
        formatted_info = format_job_description(job_info)
        st.markdown(formatted_info)
    
    # 公司信息
    st.subheader("🏢 公司信息")
    
    company_col1, company_col2 = st.columns(2)
    
    with company_col1:
        st.write(f"**公司全称**: {structured_fields.get('公司全称', '未知')}")
        st.write(f"**公司规模**: {structured_fields.get('公司规模', '未知')}")
        st.write(f"**主营业务**: {structured_fields.get('主营业务', '未知')}")
        st.write(f"**融资情况**: {structured_fields.get('是否融资', '未知')}")
    
    with company_col2:
        st.write(f"**注册资金**: {structured_fields.get('注册资金', '未知')}")
        st.write(f"**成立时间**: {structured_fields.get('成立时间', '未知')}")
        st.write(f"**公司类型**: {structured_fields.get('公司类型', '未知')}")
        st.write(f"**经营状态**: {structured_fields.get('经营状态', '未知')}")
    
    # 福利待遇
    benefits = structured_fields.get('公司福利', '')
    if benefits and benefits.strip() and benefits != '[空]':
        st.subheader("🎁 福利待遇")
        st.info(benefits)
    
    # 地理位置
    longitude = structured_fields.get('经度', '')
    latitude = structured_fields.get('纬度', '')
    if longitude and latitude:
        st.subheader("📍 地理位置")
        try:
            # 创建地图数据
            import pandas as pd
            map_data = pd.DataFrame({
                'lat': [float(latitude)],
                'lon': [float(longitude)]
            })
            st.map(map_data, zoom=12)
        except:
            st.write(f"经度: {longitude}, 纬度: {latitude}")

    # 智能简历建议功能
    st.markdown("---")
    display_resume_advice_button(doc, job_number)


def format_job_description(job_info):
    """格式化职位描述"""
    # 简单的格式化
    formatted = job_info.replace('；', '\n\n• ').replace('。', '\n\n• ')
    lines = [line.strip() for line in formatted.split('\n') if line.strip()]
    return '\n'.join(lines)


def display_resume_advice_button(doc, job_number):
    """显示智能简历建议按钮"""
    st.subheader("🎯 智能简历制作要点")
    st.markdown("基于该岗位要求，为您生成针对性的简历优化建议")

    # 创建缓存键
    cache_key = f"{doc.metadata.get('job_title', '')}_{doc.metadata.get('company_name', '')}"

    # 使用唯一的key避免ID冲突
    button_key = f"resume_advice_btn_{job_number}_{cache_key}"

    col1, col2, col3 = st.columns([2, 1, 2])

    with col2:
        # 生成建议按钮
        if st.button(
            "🚀 生成简历建议",
            key=button_key,
            use_container_width=True,
            help="点击生成针对该岗位的简历制作要点"
        ):
            # 设置当前选中的职位
            st.session_state.selected_job_for_advice = {
                'doc': doc,
                'job_number': job_number,
                'cache_key': cache_key
            }
            st.rerun()

    # 如果已选中当前职位，显示建议生成界面
    if (hasattr(st.session_state, 'selected_job_for_advice') and
        st.session_state.selected_job_for_advice and
        st.session_state.selected_job_for_advice['cache_key'] == cache_key):

        display_resume_advice_interface(
            st.session_state.selected_job_for_advice['doc'],
            st.session_state.selected_job_for_advice['job_number'],
            st.session_state.selected_job_for_advice['cache_key']
        )


def display_resume_advice_interface(doc, job_number, cache_key):
    """显示简历建议生成界面"""
    st.markdown("---")
    st.subheader("📝 个性化简历建议生成")

    # 用户背景信息输入
    with st.expander("📋 个人背景信息（可选，提供更精准建议）", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            user_education = st.selectbox(
                "学历背景",
                ["", "大专", "本科", "硕士", "博士"],
                key=f"education_{job_number}",
                help="选择您的学历背景"
            )

            user_experience = st.text_input(
                "工作年限",
                placeholder="如：3年、应届生、5年以上",
                key=f"experience_{job_number}",
                help="请输入您的工作年限"
            )

        with col2:
            user_skills = st.text_input(
                "核心技能",
                placeholder="如：Python, Django, MySQL（用逗号分隔）",
                key=f"skills_{job_number}",
                help="请输入您的核心技能"
            )

            user_industry = st.text_input(
                "行业经验",
                placeholder="如：互联网、金融、教育",
                key=f"industry_{job_number}",
                help="请输入您的行业经验"
            )

    # 操作按钮
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        # 生成建议按钮
        if st.button(
            "🤖 开始生成建议",
            key=f"generate_{job_number}",
            use_container_width=True
        ):
            if st.session_state.resume_advisor is None:
                st.error("❌ 简历建议系统未初始化，请刷新页面重试")
                return

            # 构建用户背景信息
            user_background = None
            if any([user_education, user_experience, user_skills, user_industry]):
                user_background = {}
                if user_education:
                    user_background['education'] = user_education
                if user_experience:
                    user_background['experience_years'] = user_experience
                if user_skills:
                    user_background['skills'] = [skill.strip() for skill in user_skills.split(',') if skill.strip()]
                if user_industry:
                    user_background['industry'] = user_industry

            # 生成建议
            with st.spinner("🤖 正在分析岗位要求，生成简历建议..."):
                try:
                    advice_result = st.session_state.resume_advisor.generate_resume_advice(
                        doc.metadata, user_background
                    )

                    if advice_result['success']:
                        # 缓存结果
                        st.session_state.resume_advice_cache[cache_key] = advice_result
                        st.success("✅ 简历建议生成成功！")
                        st.rerun()
                    else:
                        st.error(f"❌ 生成简历建议失败: {advice_result.get('error', '未知错误')}")

                except Exception as e:
                    st.error(f"❌ 生成简历建议时出错: {str(e)}")

    with col3:
        # 关闭按钮
        if st.button(
            "❌ 关闭",
            key=f"close_{job_number}",
            use_container_width=True
        ):
            st.session_state.selected_job_for_advice = None
            st.rerun()

    # 显示缓存的建议结果
    if cache_key in st.session_state.resume_advice_cache:
        st.markdown("---")
        display_resume_advice_content(st.session_state.resume_advice_cache[cache_key])


def display_resume_advice_content(advice_result):
    """显示简历建议内容"""
    if not advice_result['success']:
        st.error(f"❌ {advice_result.get('error', '未知错误')}")
        return

    advice = advice_result['advice']

    # 显示关键要点摘要
    if advice.get('summary'):
        st.subheader("📋 关键要点摘要")
        for i, point in enumerate(advice['summary'], 1):
            st.write(f"**{i}.** {point}")

    # 显示详细建议内容
    if advice.get('full_text'):
        st.subheader("📖 详细建议内容")

        # 使用可展开的区域显示完整内容
        with st.expander("点击查看完整的简历制作要点", expanded=True):
            st.markdown(advice['full_text'])

    # 显示分段建议（如果有的话）
    if advice.get('sections'):
        st.subheader("📚 分类建议")

        # 为每个章节创建标签页
        section_names = list(advice['sections'].keys())
        if section_names:
            tabs = st.tabs(section_names[:6])  # 最多显示6个标签页

            for tab, section_name in zip(tabs, section_names[:6]):
                with tab:
                    st.markdown(advice['sections'][section_name])

    # 操作按钮
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📋 复制建议内容", use_container_width=True):
            # 这里可以添加复制到剪贴板的功能
            st.success("✅ 建议内容已准备复制（请手动选择文本复制）")

    with col2:
        if st.button("📧 发送到邮箱", use_container_width=True):
            st.info("💡 邮箱发送功能开发中...")

    with col3:
        if st.button("💾 保存为文档", use_container_width=True):
            st.info("💡 文档保存功能开发中...")


def display_search_summary():
    """显示搜索总结"""
    st.header("📊 搜索总结")
    
    results = st.session_state.search_results
    
    # 统计信息
    companies = set()
    locations = set()
    salary_ranges = []
    
    for doc in results:
        metadata = doc.metadata
        company = metadata.get('company_name', '')
        location = metadata.get('location', '')
        salary = metadata.get('salary', '')
        
        if company:
            companies.add(company)
        if location:
            locations.add(location)
        if salary:
            salary_ranges.append(salary)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📋 职位总数", len(results))
    
    with col2:
        st.metric("🏢 公司数量", len(companies))
    
    with col3:
        st.metric("📍 地区数量", len(locations))
    
    # 建议
    st.subheader("💡 求职建议")
    st.info("""
    • 仔细阅读职位详情和任职要求
    • 重点关注公司的发展前景和福利待遇
    • 考虑工作地点的交通便利性
    • 可以根据公司规模选择适合的工作环境
    """)


def main():
    """主函数"""
    st.set_page_config(
        page_title="智能求职助手",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # 初始化会话状态
    initialize_session_state()
    
    # 页面标题
    st.title("🎯 智能求职助手")
    st.markdown("**为您找到最合适的工作机会**")
    
    # 初始化系统
    if not initialize_system():
        st.stop()
    
    # 显示搜索表单
    if not st.session_state.search_completed:
        display_job_search_form()
    else:
        # 显示搜索结果
        display_search_results()
        
        # 重新搜索按钮
        if st.button("🔄 重新搜索", use_container_width=True):
            st.session_state.search_completed = False
            st.session_state.search_results = []
            # 清除简历建议相关状态
            st.session_state.resume_advice_cache = {}
            st.session_state.selected_job_for_advice = None
            st.rerun()
    
    # 页脚
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
            🤖 智能求职助手 | 基于AI的职位匹配系统
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
