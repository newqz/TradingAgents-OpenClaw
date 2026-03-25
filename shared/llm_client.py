"""统一的 LLM 客户端创建工具"""
import os
from typing import Optional

def get_llm_client(provider: str = "openai", api_key: Optional[str] = None) -> "OpenAI":
    """获取 LLM 客户端，自动使用正确的 base_url"""
    from openai import OpenAI
    
    # API Key 映射
    KEY_MAP = {
        "openai": os.getenv("OPENAI_API_KEY"),
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "google": os.getenv("GOOGLE_API_KEY"),
        "xai": os.getenv("XAI_API_KEY"),
        "minimax": os.getenv("MINIMAX_API_KEY"),
        "ollama": os.getenv("OLLAMA_API_KEY", "local"),
    }
    
    # Base URL 映射
    BASE_URLS = {
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com",
        "google": "https://generativelanguage.googleapis.com/v1beta",
        "xai": "https://api.x.ai/v1",
        "minimax": "https://api.minimaxi.com/v1",
        "ollama": "http://localhost:11434/v1",
    }
    
    key = api_key or KEY_MAP.get(provider)
    base_url = BASE_URLS.get(provider, "https://api.openai.com/v1")
    
    if not key:
        raise ValueError(f"No API key found for provider: {provider}")
    
    return OpenAI(api_key=key, base_url=base_url)


def get_model_for_provider(provider: str, task_type: str = "default") -> str:
    """获取 provider 对应的默认模型"""
    MODELS = {
        "openai": {
            "default": "gpt-4o",
            "fast": "gpt-4o-mini",
            "reasoning": "gpt-4o",
        },
        "anthropic": {
            "default": "claude-opus-4.6",
            "fast": "claude-sonnet-4.6",
            "reasoning": "claude-opus-4.6",
        },
        "minimax": {
            "default": "MiniMax-M2.7-highspeed",
            "fast": "MiniMax-M2.5-highspeed",
            "reasoning": "MiniMax-M2.7-highspeed",
        },
        "google": {
            "default": "gemini-3",
            "fast": "gemini-3.1-flash",
            "reasoning": "gemini-3",
        },
        "xai": {
            "default": "grok-4",
            "fast": "grok-4",
            "reasoning": "grok-4",
        },
    }
    
    return MODELS.get(provider, {}).get(task_type, MODELS.get("openai", {}).get("default", "gpt-4o"))
