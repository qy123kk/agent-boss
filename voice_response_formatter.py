#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音交互响应格式化器
专门为语音交互设计的响应格式和数据结构
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, replace
from enum import Enum
import json
import copy


class VoiceResponseType(Enum):
    """语音响应类型"""
    QUESTION = "question"           # 询问问题
    CONFIRMATION = "confirmation"   # 确认信息
    INFORMATION = "information"     # 提供信息
    ERROR = "error"                # 错误提示
    SUCCESS = "success"            # 成功反馈
    SEARCH_RESULT = "search_result" # 搜索结果


class VoiceEmotionTone(Enum):
    """语音情感语调"""
    NEUTRAL = "neutral"      # 中性
    FRIENDLY = "friendly"    # 友好
    ENCOURAGING = "encouraging" # 鼓励
    APOLOGETIC = "apologetic"   # 抱歉
    EXCITED = "excited"         # 兴奋
    PROFESSIONAL = "professional" # 专业


@dataclass
class VoiceResponse:
    """语音响应数据结构"""
    text: str                           # 语音文本内容
    response_type: VoiceResponseType    # 响应类型
    emotion_tone: VoiceEmotionTone      # 情感语调
    confidence: float                   # 置信度
    
    # 语音参数
    speech_rate: float = 1.0           # 语速 (0.5-2.0)
    speech_volume: float = 0.8         # 音量 (0.0-1.0)
    speech_pitch: float = 0.0          # 音调 (-20 to 20)
    pause_after: float = 0.5           # 后续停顿时间
    
    # 交互参数
    expect_response: bool = True        # 是否期待用户回复
    timeout: float = 10.0              # 等待回复超时时间
    retry_count: int = 0               # 重试次数
    
    # 上下文信息
    extracted_data: Dict[str, Any] = None  # 提取的数据
    next_action: str = None                # 下一步动作
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "text": self.text,
            "response_type": self.response_type.value,
            "emotion_tone": self.emotion_tone.value,
            "confidence": self.confidence,
            "speech_params": {
                "rate": self.speech_rate,
                "volume": self.speech_volume,
                "pitch": self.speech_pitch,
                "pause_after": self.pause_after
            },
            "interaction_params": {
                "expect_response": self.expect_response,
                "timeout": self.timeout,
                "retry_count": self.retry_count
            },
            "context": {
                "extracted_data": self.extracted_data or {},
                "next_action": self.next_action
            }
        }
    
    def to_ssml(self) -> str:
        """转换为SSML格式"""
        # 根据情感语调调整语音参数
        emotion_adjustments = {
            VoiceEmotionTone.FRIENDLY: {"rate": 0.9, "pitch": "+2st"},
            VoiceEmotionTone.ENCOURAGING: {"rate": 0.95, "pitch": "+3st"},
            VoiceEmotionTone.APOLOGETIC: {"rate": 0.8, "pitch": "-1st"},
            VoiceEmotionTone.EXCITED: {"rate": 1.1, "pitch": "+5st"},
            VoiceEmotionTone.PROFESSIONAL: {"rate": 0.9, "pitch": "0st"}
        }
        
        adjustments = emotion_adjustments.get(self.emotion_tone, {})
        rate = adjustments.get("rate", self.speech_rate)
        pitch = adjustments.get("pitch", f"{self.speech_pitch:+.0f}st")
        
        ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">
    <prosody rate="{rate}" pitch="{pitch}" volume="{self.speech_volume}">
        {self.text}
    </prosody>
    <break time="{self.pause_after}s"/>
</speak>'''
        
        return ssml


class VoiceResponseFormatter:
    """语音响应格式化器"""
    
    def __init__(self):
        # 预定义的响应模板
        self.response_templates = {
            "job_type_question": VoiceResponse(
                text="请告诉我您想要找什么类型的工作",
                response_type=VoiceResponseType.QUESTION,
                emotion_tone=VoiceEmotionTone.FRIENDLY,
                confidence=1.0,
                speech_rate=0.9
            ),
            
            "job_type_confirmation": VoiceResponse(
                text="好的，您想找{job_type}的工作对吗？",
                response_type=VoiceResponseType.CONFIRMATION,
                emotion_tone=VoiceEmotionTone.FRIENDLY,
                confidence=0.8,
                speech_rate=0.85
            ),
            
            "location_question": VoiceResponse(
                text="请告诉我您希望在哪个城市工作",
                response_type=VoiceResponseType.QUESTION,
                emotion_tone=VoiceEmotionTone.FRIENDLY,
                confidence=1.0
            ),
            
            "salary_question": VoiceResponse(
                text="请告诉我您的薪资期望",
                response_type=VoiceResponseType.QUESTION,
                emotion_tone=VoiceEmotionTone.FRIENDLY,
                confidence=1.0
            ),
            
            "search_starting": VoiceResponse(
                text="好的，我现在为您搜索匹配的职位",
                response_type=VoiceResponseType.INFORMATION,
                emotion_tone=VoiceEmotionTone.PROFESSIONAL,
                confidence=1.0,
                expect_response=False,
                pause_after=1.0
            ),
            
            "search_success": VoiceResponse(
                text="为您找到{count}个匹配的职位",
                response_type=VoiceResponseType.SUCCESS,
                emotion_tone=VoiceEmotionTone.EXCITED,
                confidence=1.0,
                speech_rate=1.05
            ),
            
            "not_understood": VoiceResponse(
                text="抱歉，我没有理解您的意思，请再说一遍",
                response_type=VoiceResponseType.ERROR,
                emotion_tone=VoiceEmotionTone.APOLOGETIC,
                confidence=0.0,
                speech_rate=0.8
            )
        }
    
    def format_job_type_response(self, job_type: str = None, confidence: float = 0.0) -> VoiceResponse:
        """格式化职位类型响应"""
        if job_type and confidence > 0.7:
            template = self.response_templates["job_type_confirmation"]
            response = replace(
                template,
                text=template.text.format(job_type=job_type),
                confidence=confidence,
                extracted_data={"job_type": job_type}
            )
            return response
        else:
            return self.response_templates["job_type_question"]
    
    def format_location_response(self, location: str = None, confidence: float = 0.0) -> VoiceResponse:
        """格式化地点响应"""
        if location and confidence > 0.7:
            response = VoiceResponse(
                text=f"好的，工作地点是{location}对吗？",
                response_type=VoiceResponseType.CONFIRMATION,
                emotion_tone=VoiceEmotionTone.FRIENDLY,
                confidence=confidence,
                extracted_data={"location": location}
            )
            return response
        else:
            return self.response_templates["location_question"]
    
    def format_salary_response(self, salary: str = None, confidence: float = 0.0) -> VoiceResponse:
        """格式化薪资响应"""
        if salary and confidence > 0.7:
            # 转换薪资表达为语音友好格式
            voice_salary = self._convert_salary_to_voice(salary)
            response = VoiceResponse(
                text=f"好的，薪资期望是{voice_salary}对吗？",
                response_type=VoiceResponseType.CONFIRMATION,
                emotion_tone=VoiceEmotionTone.FRIENDLY,
                confidence=confidence,
                extracted_data={"salary": salary}
            )
            return response
        else:
            return self.response_templates["salary_question"]
    
    def format_search_result_response(self, job_results: List[Dict]) -> VoiceResponse:
        """格式化搜索结果响应"""
        count = len(job_results)
        
        if count == 0:
            return VoiceResponse(
                text="抱歉，没有找到符合您要求的职位",
                response_type=VoiceResponseType.ERROR,
                emotion_tone=VoiceEmotionTone.APOLOGETIC,
                confidence=1.0,
                expect_response=False
            )
        
        # 生成搜索结果摘要
        summary_text = self._generate_job_summary(job_results)
        
        return VoiceResponse(
            text=summary_text,
            response_type=VoiceResponseType.SEARCH_RESULT,
            emotion_tone=VoiceEmotionTone.EXCITED,
            confidence=1.0,
            speech_rate=0.9,
            pause_after=1.0,
            expect_response=False,
            extracted_data={"job_results": job_results}
        )
    
    def format_error_response(self, error_message: str, retry_count: int = 0) -> VoiceResponse:
        """格式化错误响应"""
        if retry_count == 0:
            text = "抱歉，我没有理解您的意思，请再说一遍"
        elif retry_count == 1:
            text = "我还是没有理解，能否换个说法？"
        else:
            text = "让我们重新开始，请告诉我您想要找什么工作"
        
        return VoiceResponse(
            text=text,
            response_type=VoiceResponseType.ERROR,
            emotion_tone=VoiceEmotionTone.APOLOGETIC,
            confidence=0.0,
            speech_rate=0.8,
            retry_count=retry_count
        )
    
    def _convert_salary_to_voice(self, salary: str) -> str:
        """将薪资转换为语音友好格式"""
        # 保持原始格式，只做最小调整
        return salary
    
    def _number_to_chinese(self, num_str: str) -> str:
        """数字转中文"""
        num_map = {
            '1': '一', '2': '二', '3': '三', '4': '四', '5': '五',
            '6': '六', '7': '七', '8': '八', '9': '九', '0': '零'
        }
        
        num = int(num_str)
        if num < 10:
            return num_map.get(str(num), str(num))
        elif num < 20:
            if num == 10:
                return '十'
            else:
                return '十' + num_map.get(str(num % 10), str(num % 10))
        elif num < 100:
            tens = num // 10
            ones = num % 10
            result = num_map.get(str(tens), str(tens)) + '十'
            if ones > 0:
                result += num_map.get(str(ones), str(ones))
            return result
        else:
            return str(num)  # 复杂数字保持原样
    
    def _generate_job_summary(self, job_results: List[Dict]) -> str:
        """生成职位摘要"""
        count = len(job_results)

        if count == 1:
            job = job_results[0]
            company = job.get('company_name', '某公司')
            title = job.get('job_title', '职位')
            salary = job.get('salary', '面议')
            return f"为您找到一个职位，{company}的{title}，薪资{salary}"

        elif count <= 3:
            summary = f"为您找到{count}个匹配的职位。"
            for i, job in enumerate(job_results, 1):
                company = job.get('company_name', '某公司')
                title = job.get('job_title', '职位')
                salary = job.get('salary', '面议')
                summary += f"第{i}个是{company}的{title}，薪资{salary}。"
            return summary

        else:
            return f"为您找到{count}个匹配的职位，我来介绍前三个最相关的。" + self._generate_job_summary(job_results[:3])


def test_voice_formatter():
    """测试语音格式化器"""
    formatter = VoiceResponseFormatter()
    
    # 测试职位类型响应
    job_response = formatter.format_job_type_response("Python开发工程师", 0.9)
    print("🧪 职位类型响应:")
    print(f"文本: {job_response.text}")
    print(f"SSML: {job_response.to_ssml()}")
    
    # 测试搜索结果响应
    mock_jobs = [
        {"company_name": "腾讯", "job_title": "Python开发工程师", "salary": "15-20K"},
        {"company_name": "阿里巴巴", "job_title": "后端开发", "salary": "18-25K"}
    ]
    
    search_response = formatter.format_search_result_response(mock_jobs)
    print(f"\n🎉 搜索结果响应:")
    print(f"文本: {search_response.text}")
    print(f"响应数据: {search_response.to_dict()}")


if __name__ == "__main__":
    test_voice_formatter()
