#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音交互优化的对话处理器
专门为语音交互设计的输出格式和处理逻辑
"""

from typing import Dict, List, Optional, Any
from modern_langchain_processor import ModernLangChainProcessor
from conversation_state import ConversationStage
import re


class VoiceOptimizedProcessor(ModernLangChainProcessor):
    """语音交互优化的对话处理器"""
    
    def __init__(self):
        super().__init__()
        
        # 语音友好的提示模板
        self.voice_stage_prompts = {
            ConversationStage.COLLECTING_JOB_TYPE: """
你是一个语音求职助手，正在通过语音对话收集用户的职位需求。

重要规则：
1. 回复要简短、自然，适合语音播报
2. 避免使用符号、表情符号、复杂格式
3. 使用口语化表达，避免书面语
4. 确认信息时要清晰明确

当前任务：理解用户想要的职位类型

请返回JSON格式：
{{
    "understood": true/false,
    "job_type": "提取的职位类型" 或 null,
    "confidence": 0.0-1.0,
    "voice_response": "简短的语音回复",
    "action": "confirm/extract/retry"
}}

语音回复示例：
- "好的，您想找Python开发工程师的工作对吗？"
- "明白了，是软件开发相关的职位"
- "请再说一遍您想要的职位类型"
""",
            
            ConversationStage.COLLECTING_LOCATION: """
你是一个语音求职助手，正在通过语音对话收集用户的工作地点需求。

重要规则：
1. 回复要简短、自然，适合语音播报
2. 避免使用符号、表情符号、复杂格式
3. 使用口语化表达
4. 地点确认要清晰

当前任务：理解用户期望的工作地点

请返回JSON格式：
{{
    "understood": true/false,
    "location": "提取的地点" 或 null,
    "confidence": 0.0-1.0,
    "voice_response": "简短的语音回复",
    "action": "confirm/extract/retry"
}}

语音回复示例：
- "好的，工作地点是深圳对吗？"
- "明白了，您希望在北京工作"
- "请告诉我您希望在哪个城市工作"
""",
            
            ConversationStage.COLLECTING_SALARY: """
你是一个语音求职助手，正在通过语音对话收集用户的薪资期望。

重要规则：
1. 回复要简短、自然，适合语音播报
2. 避免使用符号、表情符号、复杂格式
3. 薪资数字要清晰表达
4. 使用口语化表达

当前任务：理解用户的薪资期望

请返回JSON格式：
{{
    "understood": true/false,
    "salary": "提取的薪资" 或 null,
    "confidence": 0.0-1.0,
    "voice_response": "简短的语音回复",
    "action": "confirm/extract/retry"
}}

语音回复示例：
- "好的，薪资期望是每月一万五到两万对吗？"
- "明白了，您期望月薪一万五千"
- "请告诉我您的薪资期望"
"""
        }
    
    def _build_analysis_prompt(self, user_input: str, messages: List, 
                              current_stage: ConversationStage) -> str:
        """构建语音优化的分析提示"""
        if current_stage not in self.voice_stage_prompts:
            return super()._build_analysis_prompt(user_input, messages, current_stage)
        
        stage_prompt = self.voice_stage_prompts[current_stage]
        
        # 格式化对话历史（简化版）
        history_text = self._format_voice_history(messages[:-1])
        
        prompt = f"""{stage_prompt}

对话历史：
{history_text}

用户刚才说："{user_input}"

请分析并返回适合语音播报的JSON回复。
"""
        
        return prompt
    
    def _format_voice_history(self, messages: List) -> str:
        """格式化语音对话历史"""
        if not messages:
            return "这是对话开始"
        
        formatted = []
        for message in messages[-4:]:  # 最近4条消息
            if hasattr(message, 'content'):
                content = message.content
                # 清理格式符号
                content = self._clean_for_voice(content)
                
                if hasattr(message, '__class__'):
                    if 'Human' in message.__class__.__name__:
                        formatted.append(f"用户说：{content}")
                    elif 'AI' in message.__class__.__name__:
                        formatted.append(f"助手说：{content}")
        
        return "\n".join(formatted)
    
    def _clean_for_voice(self, text: str) -> str:
        """清理文本，使其适合语音播报"""
        # 移除表情符号和特殊符号
        text = re.sub(r'[🤖🎯📍💰✅❌🔍📊💡🎉]', '', text)
        
        # 移除markdown格式
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # 粗体
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # 斜体
        
        # 移除列表符号
        text = re.sub(r'[•·▪▫]', '', text)
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        
        # 保持数字格式自然，只做最小调整
        # 不转换K和万的表达，保持原样
        
        # 移除多余空行
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()
    
    def _parse_llm_response(self, response: str, user_input: str, 
                           current_stage: ConversationStage) -> Dict[str, Any]:
        """解析LLM响应，优化语音输出"""
        result = super()._parse_llm_response(response, user_input, current_stage)
        
        # 如果有voice_response，使用它作为ai_response
        if isinstance(result.get('ai_response'), str):
            try:
                import json
                if '{' in response and '}' in response:
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    json_str = response[json_start:json_end]
                    parsed = json.loads(json_str)
                    
                    voice_response = parsed.get('voice_response')
                    if voice_response:
                        # 清理语音回复
                        cleaned_response = self._clean_for_voice(voice_response)
                        result['ai_response'] = cleaned_response
                        result['voice_optimized'] = True
            except:
                pass
        
        # 如果没有voice_response，清理原始回复
        if not result.get('voice_optimized'):
            result['ai_response'] = self._clean_for_voice(result['ai_response'])
        
        return result
    
    def get_voice_friendly_summary(self, job_results: List[Dict]) -> str:
        """生成语音友好的搜索结果摘要"""
        if not job_results:
            return "抱歉，没有找到合适的职位"
        
        count = len(job_results)
        
        if count == 1:
            job = job_results[0]
            return f"为您找到一个职位：{job.get('company_name', '某公司')}的{job.get('job_title', '职位')}，薪资{job.get('salary', '面议')}"
        
        elif count <= 3:
            summary = f"为您找到{count}个匹配的职位。"
            for i, job in enumerate(job_results, 1):
                company = job.get('company_name', '某公司')
                title = job.get('job_title', '职位')
                salary = job.get('salary', '面议')
                summary += f"第{i}个是{company}的{title}，薪资{salary}。"
            return summary
        
        else:
            return f"为您找到{count}个匹配的职位，前三个最相关的是：" + self.get_voice_friendly_summary(job_results[:3])
    
    def get_voice_settings(self) -> Dict[str, Any]:
        """获取语音交互的推荐设置"""
        return {
            "speech_rate": 0.9,          # 语速：稍慢一些便于理解
            "speech_volume": 0.8,        # 音量：适中
            "speech_pitch": 0.0,         # 音调：自然
            "pause_duration": 0.5,       # 停顿时长：半秒
            "confirmation_timeout": 5,    # 确认超时：5秒
            "max_response_length": 100,   # 最大回复长度：100字符
            "use_ssml": True,            # 使用SSML标记
            "voice_gender": "female",    # 推荐女声
            "language": "zh-CN"          # 中文
        }
    
    def format_for_tts(self, text: str) -> str:
        """格式化文本用于TTS（文本转语音）"""
        # 添加适当的停顿
        text = re.sub(r'[，。！？]', lambda m: m.group() + '<break time="0.3s"/>', text)
        text = re.sub(r'[；：]', lambda m: m.group() + '<break time="0.5s"/>', text)

        # 保持数字格式自然，TTS引擎会自动处理
        # 不做特殊的数字转换，让TTS自然读出"15K"、"20万"等

        # 包装SSML
        ssml_text = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">{text}</speak>'

        return ssml_text


def test_voice_optimization():
    """测试语音优化功能"""
    processor = VoiceOptimizedProcessor()
    
    # 测试文本清理
    test_text = "好的，我记录下了：\n✅ 职位类型：Python开发工程师\n\n🎯 很好！接下来请告诉我您希望在哪个城市工作？\n\n比如：北京、上海、深圳、杭州、成都等。"
    
    cleaned = processor._clean_for_voice(test_text)
    print("🧪 文本清理测试:")
    print(f"原文: {test_text}")
    print(f"清理后: {cleaned}")
    
    # 测试TTS格式化
    tts_text = processor.format_for_tts("好的，您的薪资期望是15K到20K对吗？")
    print(f"\n🎙️ TTS格式化: {tts_text}")
    
    # 测试语音设置
    settings = processor.get_voice_settings()
    print(f"\n⚙️ 语音设置: {settings}")


if __name__ == "__main__":
    test_voice_optimization()
