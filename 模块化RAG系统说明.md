# 模块化RAG系统说明

## 概述

原来的 `rag.py` 文件过于庞大（509行），包含了太多功能。现在已经重构为模块化架构，将不同功能分离到独立的模块中，提高了代码的可维护性和可扩展性。

## 新的模块结构

### 1. `document_loader.py` - 文档加载模块
**功能**: 负责加载各种格式的文档
- `load_excel_document()` - 加载Excel文件并转换为Document对象
- `load_documents()` - 从目录加载多种格式文档（PDF、Word、文本、Excel）
- `split_documents()` - 将文档分割成较小的文本块

**特点**:
- 专门优化Excel文件的结构化处理
- 支持多种文档格式
- 为每行Excel数据创建独立的Document，便于精确检索

### 2. `vector_store.py` - 向量存储模块
**功能**: 负责创建、保存和加载向量存储
- `create_vector_store()` - 创建向量存储并保存到本地
- `load_vector_store()` - 从本地加载向量存储
- `search_documents()` - 在向量存储中搜索相关文档
- `create_embeddings()` - 创建嵌入模型

**特点**:
- 统一的API密钥管理
- 使用阿里云DashScope嵌入模型
- 支持相似度搜索

### 3. `qa_chain.py` - 问答链模块
**功能**: 负责创建和管理问答链
- `StreamingCallbackHandler` - 流式输出回调处理器
- `setup_qa_chain()` - 设置基础问答链
- `setup_streaming_qa_chain()` - 设置流式问答链
- `ask_question()` - 提问并获取答案
- `create_memory()` - 创建对话记忆

**特点**:
- 支持流式和非流式输出
- 对话历史管理
- 使用DeepSeek-R1模型

### 4. `rag_core.py` - 核心RAG模块
**功能**: 整合所有功能，提供简洁的API
- `RAGSystem` 类 - 核心RAG系统类
- `create_rag_system()` - 创建完整的RAG系统
- `load_existing_rag_system()` - 加载现有的RAG系统

**特点**:
- 面向对象的设计
- 简化的API接口
- 向后兼容性

## 新的应用程序

### 1. `simple_rag_cli.py` - 命令行应用
**功能**: 简化版的命令行RAG应用
- 自动检测和加载现有向量存储
- 支持流式对话
- 文档统计显示

**使用方法**:
```bash
python simple_rag_cli.py        # 启动对话模式
python simple_rag_cli.py test   # 测试搜索功能
```

### 2. `simple_rag_streamlit.py` - Web应用
**功能**: 简化版的Streamlit Web应用
- 现代化的Web界面
- 侧边栏搜索功能
- 对话历史管理
- 系统信息显示

**使用方法**:
```bash
streamlit run simple_rag_streamlit.py
```

## 与原系统的对比

### 原系统 (`rag.py`)
- ❌ 单文件509行，难以维护
- ❌ 功能耦合严重
- ❌ 包含大量复杂的角色扮演逻辑
- ❌ 代码重复较多

### 新系统 (模块化)
- ✅ 模块化设计，职责清晰
- ✅ 代码复用性高
- ✅ 易于测试和维护
- ✅ 保留核心RAG功能
- ✅ 简化的API接口

## 保留的核心功能

1. **文档加载**: 支持Excel、PDF、Word、文本文件
2. **向量存储**: 使用FAISS和DashScope嵌入
3. **问答功能**: 基于DeepSeek-R1模型
4. **流式输出**: 支持实时响应
5. **对话记忆**: 保持对话上下文

## 移除的功能

1. **复杂的角色扮演**: 移除了过度复杂的角色设定逻辑
2. **对话历史优化**: 简化了对话历史管理
3. **多种记忆策略**: 统一使用ConversationBufferMemory
4. **复杂的提示词工程**: 简化了提示词模板

## 使用示例

### 基本使用
```python
from rag_core import create_rag_system

# 创建RAG系统
rag = create_rag_system(
    documents_dir="documents",
    system_prompt="你是一个智能助手。"
)

# 提问
answer = rag.ask("文档中有哪些公司？")
print(answer)
```

### 流式输出
```python
# 流式输出
for token in rag.ask("文档中有哪些公司？", use_streaming=True):
    print(token, end="", flush=True)
```

### 搜索功能
```python
# 搜索相关文档
results = rag.search("Python工程师", k=3)
for doc in results:
    print(doc.page_content[:100])
```

## 测试

更新后的测试脚本 `test_rag_system.py` 已适配新的模块结构：

```bash
python test_rag_system.py
```

## 向后兼容性

为了保持向后兼容，`rag_core.py` 提供了与原系统相同的函数接口：

```python
# 这些函数仍然可用
from rag_core import setup_streaming_qa_chain
```

## 总结

新的模块化架构具有以下优势：

1. **更清晰的代码结构**: 每个模块职责单一
2. **更好的可维护性**: 修改某个功能不会影响其他模块
3. **更高的代码复用性**: 模块可以独立使用
4. **更简单的API**: 提供了更直观的使用接口
5. **保持核心功能**: 所有重要的RAG功能都得到保留

这个重构大大提高了代码质量，同时保持了系统的核心功能和性能。
