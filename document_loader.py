#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档加载模块
负责加载各种格式的文档，包括Excel、PDF、Word、文本文件
"""

import os
import pandas as pd
from typing import List, Iterator
from langchain.schema import Document
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
)
from langchain_community.document_loaders.base import BaseLoader


class ExcelJobDataLoader(BaseLoader):
    """
    自定义Excel文档加载器 - 继承BaseLoader
    专门用于加载招聘数据Excel文件，优化结构化检索
    """

    def __init__(self, file_path: str, sheet_name: str = None):
        """
        初始化Excel加载器

        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称，如果为None则加载所有工作表
        """
        self.file_path = file_path
        self.sheet_name = sheet_name

    def load(self) -> List[Document]:
        """实现BaseLoader的load方法"""
        return list(self.lazy_load())

    def lazy_load(self) -> Iterator[Document]:
        """实现BaseLoader的lazy_load方法 - 支持懒加载"""
        try:
            excel_file = pd.ExcelFile(self.file_path)

            # 确定要处理的工作表
            sheet_names = [self.sheet_name] if self.sheet_name else excel_file.sheet_names

            for sheet_name in sheet_names:
                if sheet_name not in excel_file.sheet_names:
                    continue

                # 读取工作表
                df = pd.read_excel(self.file_path, sheet_name=sheet_name)

                # 跳过空的工作表
                if df.empty:
                    continue

                # 获取列标题
                headers = df.columns.tolist()

                # 为每一行数据创建单独的Document
                for index, row in df.iterrows():
                    # 收集结构化字段
                    structured_fields = {}
                    for col in headers:
                        cell_value = row[col]
                        if pd.isna(cell_value):
                            cell_value = ""
                        else:
                            cell_value = str(cell_value)
                        structured_fields[col] = cell_value

                    # 创建优化的文档内容
                    job_content = self._create_structured_content(structured_fields, index + 1)

                    # 添加搜索关键词
                    job_content += self._create_search_keywords(structured_fields)

                    # 创建Document对象
                    doc = Document(
                        page_content=job_content,
                        metadata={
                            "source": self.file_path,
                            "sheet_name": sheet_name,
                            "file_type": "excel",
                            "row_index": index + 1,
                            "total_rows": len(df),
                            "total_columns": len(df.columns),
                            "structured_fields": structured_fields,
                            "job_title": structured_fields.get('职位名称', ''),
                            "company_name": structured_fields.get('公司名称', ''),
                            "location": structured_fields.get('地区', structured_fields.get('地 区', '')),
                            "salary": structured_fields.get('薪资', ''),
                            "experience": structured_fields.get('工作经验', ''),
                            "education": structured_fields.get('学历', '')
                        }
                    )
                    yield doc

        except Exception as e:
            print(f"加载Excel文件 {self.file_path} 时出错: {e}")
            return

    def _create_structured_content(self, structured_fields: dict, row_num: int) -> str:
        """创建结构化的文档内容"""
        return _create_structured_content(structured_fields, row_num)

    def _create_search_keywords(self, structured_fields: dict) -> str:
        """创建搜索关键词"""
        return _create_search_keywords(structured_fields)


class DocumentLoaderFactory:
    """
    文档加载器工厂类 - 展示架构设计能力
    根据文件类型自动选择合适的加载器
    """

    @staticmethod
    def create_loader(file_path: str) -> BaseLoader:
        """
        根据文件扩展名创建相应的加载器

        Args:
            file_path: 文件路径

        Returns:
            BaseLoader: 相应的文档加载器实例
        """
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension in ['.xlsx', '.xls']:
            return ExcelJobDataLoader(file_path)
        elif file_extension == '.pdf':
            return PyPDFLoader(file_path)
        elif file_extension == '.docx':
            return Docx2txtLoader(file_path)
        elif file_extension == '.txt':
            return TextLoader(file_path, encoding="utf-8")
        else:
            raise ValueError(f"不支持的文件类型: {file_extension}")

    @staticmethod
    def load_document(file_path: str) -> List[Document]:
        """
        便捷方法：直接加载文档

        Args:
            file_path: 文件路径

        Returns:
            List[Document]: 加载的文档列表
        """
        loader = DocumentLoaderFactory.create_loader(file_path)
        return loader.load()


def load_excel_document(file_path: str) -> List[Document]:
    """
    兼容性函数 - 使用新的ExcelJobDataLoader
    保持向后兼容性
    """
    loader = ExcelJobDataLoader(file_path)
    return loader.load()


def _create_structured_content(structured_fields: dict, row_number: int) -> str:
    """创建结构化的文档内容"""
    content = f"【职位信息 #{row_number}】\n\n"

    # 核心信息优先显示
    core_fields = ['职位名称', '公司名称', '公司全称', '地区', '薪资', '工作经验', '学历']

    content += "=== 核心信息 ===\n"
    for field in core_fields:
        value = structured_fields.get(field, '').strip()
        if value:
            content += f"• {field}: {value}\n"

    # 公司详情
    company_fields = ['主营业务', '公司规模', '是否融资', '注册资金', '成立时间', '公司类型', '法定代表人', '经营状态']
    company_info = []
    for field in company_fields:
        value = structured_fields.get(field, '').strip()
        if value:
            company_info.append(f"• {field}: {value}")

    if company_info:
        content += f"\n=== 公司详情 ===\n"
        content += "\n".join(company_info) + "\n"

    # 职位详情
    job_fields = ['职位信息', '职位类型', '实习时间', '公司福利']
    job_info = []
    for field in job_fields:
        value = structured_fields.get(field, '').strip()
        if value and value != '[空]':
            # 限制职位信息长度，避免过长
            if field == '职位信息' and len(value) > 200:
                value = value[:200] + "..."
            job_info.append(f"• {field}: {value}")

    if job_info:
        content += f"\n=== 职位详情 ===\n"
        content += "\n".join(job_info) + "\n"

    # 位置信息
    location_fields = ['经度', '纬度']
    location_info = []
    for field in location_fields:
        value = structured_fields.get(field, '').strip()
        if value:
            location_info.append(f"{field}: {value}")

    if location_info:
        content += f"\n=== 位置信息 ===\n"
        content += "• " + " | ".join(location_info) + "\n"

    return content


def _create_search_keywords(structured_fields: dict) -> str:
    """创建搜索关键词，增强检索效果"""
    keywords = "\n=== 搜索关键词 ===\n"

    # 公司相关关键词
    company_name = structured_fields.get('公司名称', '').strip()
    company_full_name = structured_fields.get('公司全称', '').strip()
    if company_name:
        keywords += f"公司: {company_name}"
        if company_full_name and company_full_name != company_name:
            keywords += f" ({company_full_name})"
        keywords += "\n"

    # 职位相关关键词
    job_title = structured_fields.get('职位名称', '').strip()
    if job_title:
        keywords += f"职位: {job_title} 招聘 岗位\n"

    # 地区关键词
    location = structured_fields.get('地区', '').strip()
    if location:
        keywords += f"地区: {location} 工作地点 办公地址\n"

    # 薪资关键词
    salary = structured_fields.get('薪资', '').strip()
    if salary:
        keywords += f"薪资: {salary} 工资 待遇 薪酬\n"

    # 经验关键词
    experience = structured_fields.get('工作经验', '').strip()
    if experience:
        keywords += f"经验: {experience} 工作经验 经验要求\n"

    # 学历关键词
    education = structured_fields.get('学历', '').strip()
    if education:
        keywords += f"学历: {education} 学历要求 教育背景\n"

    # 行业关键词
    business = structured_fields.get('主营业务', '').strip()
    if business:
        keywords += f"行业: {business} 业务领域\n"

    return keywords


def load_documents(files_dir: str) -> List[Document]:
    """
    从指定目录加载所有支持的文档
    使用工厂模式，更优雅的架构设计
    """
    docs = []
    if not os.path.exists(files_dir):
        return docs

    for filename in os.listdir(files_dir):
        file_path = os.path.join(files_dir, filename)
        if not os.path.isfile(file_path):
            continue

        try:
            # 使用工厂模式创建加载器
            docs.extend(DocumentLoaderFactory.load_document(file_path))
        except ValueError as e:
            # 不支持的文件类型，跳过
            continue
        except Exception as e:
            print(f"加载文件 {filename} 时出错: {e}")

    return docs


def load_documents_legacy(files_dir: str) -> List[Document]:
    """
    传统的文档加载方式 - 保留作为对比
    """
    docs = []
    if not os.path.exists(files_dir):
        return docs

    for filename in os.listdir(files_dir):
        file_path = os.path.join(files_dir, filename)
        if not os.path.isfile(file_path):
            continue

        try:
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                docs.extend(loader.load())
            elif filename.endswith(".docx"):
                loader = Docx2txtLoader(file_path)
                docs.extend(loader.load())
            elif filename.endswith(".txt"):
                loader = TextLoader(file_path, encoding="utf-8")
                docs.extend(loader.load())
            elif filename.endswith((".xls", ".xlsx")):
                excel_docs = load_excel_document(file_path)
                docs.extend(excel_docs)
        except Exception as e:
            print(f"加载文件 {filename} 时出错: {e}")

    return docs


def split_documents(documents) -> List[Document]:
    """将文档分割成较小的文本块"""
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
    )
    return text_splitter.split_documents(documents)
