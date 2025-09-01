#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音交互配置
为语音智能体提供完整的配置参数和建议
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class VoiceProvider(Enum):
    """语音服务提供商"""
    AZURE_SPEECH = "azure_speech"
    GOOGLE_CLOUD = "google_cloud"
    AWS_POLLY = "aws_polly"
    BAIDU_SPEECH = "baidu_speech"
    IFLYTEK = "iflytek"
    OPENAI_TTS = "openai_tts"


class ASRProvider(Enum):
    """语音识别服务提供商"""
    AZURE_SPEECH = "azure_speech"
    GOOGLE_CLOUD = "google_cloud"
    AWS_TRANSCRIBE = "aws_transcribe"
    BAIDU_ASR = "baidu_asr"
    IFLYTEK_ASR = "iflytek_asr"
    OPENAI_WHISPER = "openai_whisper"


@dataclass
class VoiceConfig:
    """语音配置"""
    # TTS配置
    tts_provider: VoiceProvider = VoiceProvider.AZURE_SPEECH
    tts_voice_name: str = "zh-CN-XiaoxiaoNeural"  # 推荐女声
    tts_speech_rate: float = 0.9                   # 语速稍慢
    tts_speech_volume: float = 0.8                 # 音量适中
    tts_speech_pitch: float = 0.0                  # 音调自然
    
    # ASR配置
    asr_provider: ASRProvider = ASRProvider.AZURE_SPEECH
    asr_language: str = "zh-CN"
    asr_sample_rate: int = 16000
    asr_timeout: float = 10.0                      # 识别超时
    asr_silence_timeout: float = 2.0               # 静音超时
    
    # 交互配置
    wake_word: str = "小助手"                       # 唤醒词
    confirmation_timeout: float = 5.0              # 确认超时
    max_retry_count: int = 3                       # 最大重试次数
    conversation_timeout: float = 300.0            # 对话超时（5分钟）
    
    # 音频配置
    audio_format: str = "wav"
    audio_channels: int = 1
    audio_sample_rate: int = 16000
    audio_chunk_size: int = 1024


class VoiceInteractionRecommendations:
    """语音交互建议配置"""
    
    @staticmethod
    def get_chinese_voice_recommendations() -> Dict[str, Any]:
        """获取中文语音推荐配置"""
        return {
            "azure_speech": {
                "recommended_voices": [
                    "zh-CN-XiaoxiaoNeural",  # 女声，自然亲和
                    "zh-CN-YunxiNeural",     # 男声，专业稳重
                    "zh-CN-XiaoyiNeural",    # 女声，温柔甜美
                    "zh-CN-YunjianNeural"    # 男声，年轻活力
                ],
                "optimal_settings": {
                    "rate": 0.9,
                    "volume": 0.8,
                    "pitch": "+2st"
                }
            },
            
            "openai_tts": {
                "recommended_voices": [
                    "alloy",    # 中性，清晰
                    "nova",     # 女声，友好
                    "shimmer"   # 女声，温暖
                ],
                "optimal_settings": {
                    "speed": 0.9,
                    "model": "tts-1-hd"
                }
            },
            
            "baidu_speech": {
                "recommended_voices": [
                    "0",  # 女声
                    "1",  # 男声
                    "3",  # 情感女声
                    "4"   # 情感男声
                ],
                "optimal_settings": {
                    "spd": 5,  # 语速（1-15）
                    "pit": 5,  # 音调（1-15）
                    "vol": 8   # 音量（1-15）
                }
            }
        }
    
    @staticmethod
    def get_asr_recommendations() -> Dict[str, Any]:
        """获取语音识别推荐配置"""
        return {
            "azure_speech": {
                "language": "zh-CN",
                "recognition_mode": "conversation",
                "profanity_option": "masked",
                "enable_dictation": True,
                "phrase_list": [
                    "Python开发工程师",
                    "Java开发工程师", 
                    "前端开发",
                    "UI设计师",
                    "产品经理",
                    "数据分析师",
                    "北京", "上海", "深圳", "广州", "杭州",
                    "薪资", "工资", "月薪", "年薪"
                ]
            },
            
            "openai_whisper": {
                "model": "whisper-1",
                "language": "zh",
                "temperature": 0.0,
                "prompt": "这是一个求职对话，包含职位名称、城市名称和薪资信息。"
            },
            
            "baidu_asr": {
                "dev_pid": 1537,  # 普通话(支持简单的英文识别)
                "rate": 16000,
                "format": "wav",
                "cuid": "voice_job_assistant"
            }
        }
    
    @staticmethod
    def get_conversation_flow_config() -> Dict[str, Any]:
        """获取对话流程配置"""
        return {
            "stages": {
                "greeting": {
                    "max_duration": 30,
                    "expected_keywords": ["你好", "开始", "找工作"],
                    "fallback_prompt": "请说您好开始求职咨询"
                },
                
                "job_type": {
                    "max_duration": 60,
                    "expected_keywords": [
                        "开发", "工程师", "设计师", "经理", "分析师",
                        "python", "java", "前端", "后端", "ui", "产品"
                    ],
                    "fallback_prompt": "请告诉我您想要的职位类型",
                    "confirmation_required": True
                },
                
                "location": {
                    "max_duration": 45,
                    "expected_keywords": [
                        "北京", "上海", "深圳", "广州", "杭州", "成都",
                        "远程", "在家", "不限"
                    ],
                    "fallback_prompt": "请告诉我您希望的工作地点",
                    "confirmation_required": True
                },
                
                "salary": {
                    "max_duration": 45,
                    "expected_keywords": [
                        "千", "万", "K", "薪资", "工资", "月薪", "年薪", "面议"
                    ],
                    "fallback_prompt": "请告诉我您的薪资期望",
                    "confirmation_required": True
                },
                
                "search": {
                    "max_duration": 30,
                    "auto_proceed": True,
                    "show_progress": True
                }
            },
            
            "error_handling": {
                "max_retries_per_stage": 3,
                "global_max_retries": 10,
                "escalation_prompts": [
                    "我没有听清楚，请再说一遍",
                    "能否换个说法？",
                    "让我们重新开始这个问题"
                ]
            },
            
            "interruption_handling": {
                "allow_interruption": True,
                "interruption_keywords": ["等等", "停", "重新开始", "退出"],
                "interruption_actions": {
                    "等等": "pause",
                    "停": "pause", 
                    "重新开始": "restart",
                    "退出": "exit"
                }
            }
        }
    
    @staticmethod
    def get_performance_optimization() -> Dict[str, Any]:
        """获取性能优化建议"""
        return {
            "latency_optimization": {
                "target_response_time": 1.5,  # 目标响应时间（秒）
                "tts_streaming": True,         # 启用TTS流式输出
                "asr_streaming": True,         # 启用ASR流式识别
                "llm_streaming": True,         # 启用LLM流式生成
                "cache_common_responses": True, # 缓存常见回复
                "preload_models": True         # 预加载模型
            },
            
            "quality_optimization": {
                "noise_reduction": True,       # 噪音降噪
                "echo_cancellation": True,     # 回声消除
                "automatic_gain_control": True, # 自动增益控制
                "voice_activity_detection": True, # 语音活动检测
                "confidence_threshold": 0.7    # 置信度阈值
            },
            
            "resource_management": {
                "max_concurrent_sessions": 10, # 最大并发会话
                "session_cleanup_interval": 300, # 会话清理间隔
                "memory_limit_mb": 512,        # 内存限制
                "cpu_usage_limit": 80          # CPU使用限制
            }
        }
    
    @staticmethod
    def get_integration_examples() -> Dict[str, str]:
        """获取集成示例代码"""
        return {
            "azure_speech_integration": '''
# Azure Speech Services集成示例
import azure.cognitiveservices.speech as speechsdk

def create_azure_speech_config():
    speech_config = speechsdk.SpeechConfig(
        subscription="YOUR_SUBSCRIPTION_KEY",
        region="YOUR_REGION"
    )
    speech_config.speech_synthesis_voice_name = "zh-CN-XiaoxiaoNeural"
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
    )
    return speech_config
''',
            
            "openai_integration": '''
# OpenAI TTS/Whisper集成示例
from openai import OpenAI

client = OpenAI()

def text_to_speech(text):
    response = client.audio.speech.create(
        model="tts-1-hd",
        voice="alloy",
        input=text,
        speed=0.9
    )
    return response.content

def speech_to_text(audio_file):
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="zh"
    )
    return transcript.text
''',
            
            "voice_workflow_integration": '''
# 语音工作流集成示例
from voice_optimized_processor import VoiceOptimizedProcessor
from voice_response_formatter import VoiceResponseFormatter

class VoiceJobAssistant:
    def __init__(self):
        self.processor = VoiceOptimizedProcessor()
        self.formatter = VoiceResponseFormatter()
    
    async def process_voice_input(self, audio_data):
        # 1. 语音转文字
        text = await self.speech_to_text(audio_data)
        
        # 2. 处理文本
        result = self.processor.process_user_input(text, current_stage)
        
        # 3. 格式化响应
        voice_response = self.formatter.format_response(result)
        
        # 4. 文字转语音
        audio_response = await self.text_to_speech(voice_response.to_ssml())
        
        return audio_response, voice_response.to_dict()
'''
        }


def generate_voice_config_file():
    """生成语音配置文件"""
    config = VoiceConfig()
    recommendations = VoiceInteractionRecommendations()

    # 转换枚举为字符串
    config_dict = {}
    for key, value in config.__dict__.items():
        if hasattr(value, 'value'):  # 枚举类型
            config_dict[key] = value.value
        else:
            config_dict[key] = value

    full_config = {
        "voice_config": config_dict,
        "voice_recommendations": recommendations.get_chinese_voice_recommendations(),
        "asr_recommendations": recommendations.get_asr_recommendations(),
        "conversation_flow": recommendations.get_conversation_flow_config(),
        "performance_optimization": recommendations.get_performance_optimization(),
        "integration_examples": recommendations.get_integration_examples()
    }

    return full_config


if __name__ == "__main__":
    import json
    
    config = generate_voice_config_file()
    
    # 保存配置到文件
    with open("voice_interaction_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print("✅ 语音交互配置文件已生成: voice_interaction_config.json")
    print("\n🎙️ 主要建议:")
    print("1. 使用Azure Speech Services的zh-CN-XiaoxiaoNeural声音")
    print("2. 语速设置为0.9，音量0.8，音调+2st")
    print("3. 启用流式TTS和ASR以降低延迟")
    print("4. 设置置信度阈值为0.7")
    print("5. 支持对话中断和重新开始")
    print("6. 缓存常见回复以提高响应速度")
