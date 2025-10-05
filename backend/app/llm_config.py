import os
import logging
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

logger = logging.getLogger(__name__)

class UniversalLLMConfig:
    """
    Universal LLM configuration supporting multiple providers.
    
    Supported Providers:
    - Google Gemini (google/gemini)
    - OpenAI ChatGPT (openai/chatgpt)
    - Anthropic Claude (anthropic/claude)
    - DeepSeek (deepseek)
    - XAI Grok (grok/xai)
    - Groq (groq)
    - Meta Llama (llama - via Groq, Together, or local)
    - Local models via Ollama/LM Studio (local/ollama/lmstudio)
    - Any OpenAI-compatible API (custom)
    """
    
    # Provider and model configuration
    PROVIDER = os.getenv("LLM_PROVIDER", "google").lower()
    MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")
    TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.2"))
    MAX_RETRIES = int(os.getenv("MODEL_MAX_RETRIES", "3"))
    TIMEOUT = int(os.getenv("MODEL_TIMEOUT", "120"))
    
    # API Keys
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    XAI_API_KEY = os.getenv("XAI_API_KEY")  # For Grok
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
    CUSTOM_API_KEY = os.getenv("CUSTOM_API_KEY")
    CUSTOM_BASE_URL = os.getenv("CUSTOM_BASE_URL")
    
    # Provider-specific base URLs
    PROVIDER_URLS = {
        "deepseek": "https://api.deepseek.com",
        "xai": "https://api.x.ai/v1",
        "grok": "https://api.x.ai/v1",
        "groq": "https://api.groq.com/openai/v1",
        "together": "https://api.together.xyz/v1",
        "ollama": "http://localhost:11434/v1",
        "lmstudio": "http://localhost:1234/v1",
    }
    
    @classmethod
    def get_llm(cls):
        """Get configured LLM instance based on provider."""
        
        provider = cls.PROVIDER.lower()
        
        # Google Gemini
        if provider in ["google", "gemini"]:
            if not cls.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY not found in environment")
            
            logger.info(f"Using Google Gemini: {cls.MODEL_NAME}")
            return ChatGoogleGenerativeAI(
                model=cls.MODEL_NAME,
                temperature=cls.TEMPERATURE,
                timeout=cls.TIMEOUT,
                max_retries=cls.MAX_RETRIES,
                google_api_key=cls.GOOGLE_API_KEY
            )
        
        # OpenAI ChatGPT
        elif provider in ["openai", "chatgpt"]:
            if not cls.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not found in environment")
            
            logger.info(f"Using OpenAI: {cls.MODEL_NAME}")
            return ChatOpenAI(
                model=cls.MODEL_NAME,
                temperature=cls.TEMPERATURE,
                timeout=cls.TIMEOUT,
                max_retries=cls.MAX_RETRIES,
                openai_api_key=cls.OPENAI_API_KEY
            )
        
        # Anthropic Claude
        elif provider in ["anthropic", "claude"]:
            if not cls.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            
            logger.info(f"Using Anthropic Claude: {cls.MODEL_NAME}")
            return ChatAnthropic(
                model=cls.MODEL_NAME,
                temperature=cls.TEMPERATURE,
                timeout=cls.TIMEOUT,
                max_retries=cls.MAX_RETRIES,
                anthropic_api_key=cls.ANTHROPIC_API_KEY
            )
        
        # DeepSeek
        elif provider == "deepseek":
            if not cls.DEEPSEEK_API_KEY:
                raise ValueError("DEEPSEEK_API_KEY not found in environment")
            
            logger.info(f"Using DeepSeek: {cls.MODEL_NAME}")
            return ChatOpenAI(
                model=cls.MODEL_NAME,
                temperature=cls.TEMPERATURE,
                timeout=cls.TIMEOUT,
                max_retries=cls.MAX_RETRIES,
                openai_api_key=cls.DEEPSEEK_API_KEY,
                base_url=cls.PROVIDER_URLS["deepseek"]
            )
        
        # XAI Grok
        elif provider in ["grok", "xai"]:
            if not cls.XAI_API_KEY:
                raise ValueError("XAI_API_KEY not found in environment")
            
            logger.info(f"Using XAI Grok: {cls.MODEL_NAME}")
            return ChatOpenAI(
                model=cls.MODEL_NAME,
                temperature=cls.TEMPERATURE,
                timeout=cls.TIMEOUT,
                max_retries=cls.MAX_RETRIES,
                openai_api_key=cls.XAI_API_KEY,
                base_url=cls.PROVIDER_URLS["grok"]
            )
        
        # Groq (fast inference)
        elif provider == "groq":
            if not cls.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY not found in environment")
            
            logger.info(f"Using Groq: {cls.MODEL_NAME}")
            return ChatOpenAI(
                model=cls.MODEL_NAME,
                temperature=cls.TEMPERATURE,
                timeout=cls.TIMEOUT,
                max_retries=cls.MAX_RETRIES,
                openai_api_key=cls.GROQ_API_KEY,
                base_url=cls.PROVIDER_URLS["groq"]
            )
        
        # Together AI (Llama and others)
        elif provider in ["together", "llama-together"]:
            if not cls.TOGETHER_API_KEY:
                raise ValueError("TOGETHER_API_KEY not found in environment")
            
            logger.info(f"Using Together AI: {cls.MODEL_NAME}")
            return ChatOpenAI(
                model=cls.MODEL_NAME,
                temperature=cls.TEMPERATURE,
                timeout=cls.TIMEOUT,
                max_retries=cls.MAX_RETRIES,
                openai_api_key=cls.TOGETHER_API_KEY,
                base_url=cls.PROVIDER_URLS["together"]
            )
        
        # Ollama (local models)
        elif provider in ["ollama", "local-ollama"]:
            logger.info(f"Using Ollama (local): {cls.MODEL_NAME}")
            return ChatOpenAI(
                model=cls.MODEL_NAME,
                temperature=cls.TEMPERATURE,
                timeout=cls.TIMEOUT,
                max_retries=cls.MAX_RETRIES,
                openai_api_key="ollama",  # Dummy key for local
                base_url=cls.CUSTOM_BASE_URL or cls.PROVIDER_URLS["ollama"]
            )
        
        # LM Studio (local models)
        elif provider in ["lmstudio", "local-lmstudio"]:
            logger.info(f"Using LM Studio (local): {cls.MODEL_NAME}")
            return ChatOpenAI(
                model=cls.MODEL_NAME,
                temperature=cls.TEMPERATURE,
                timeout=cls.TIMEOUT,
                max_retries=cls.MAX_RETRIES,
                openai_api_key="lmstudio",  # Dummy key for local
                base_url=cls.CUSTOM_BASE_URL or cls.PROVIDER_URLS["lmstudio"]
            )
        
        # Local models (generic)
        elif provider == "local":
            logger.info(f"Using Local Model: {cls.MODEL_NAME}")
            if not cls.CUSTOM_BASE_URL:
                raise ValueError("CUSTOM_BASE_URL required for local models")
            
            return ChatOpenAI(
                model=cls.MODEL_NAME,
                temperature=cls.TEMPERATURE,
                timeout=cls.TIMEOUT,
                max_retries=cls.MAX_RETRIES,
                openai_api_key="local",  # Dummy key for local
                base_url=cls.CUSTOM_BASE_URL
            )
        
        # Custom OpenAI-compatible API
        elif provider == "custom":
            if not cls.CUSTOM_API_KEY:
                raise ValueError("CUSTOM_API_KEY not found in environment")
            if not cls.CUSTOM_BASE_URL:
                raise ValueError("CUSTOM_BASE_URL not found in environment")
            
            logger.info(f"Using Custom OpenAI-compatible API: {cls.MODEL_NAME} at {cls.CUSTOM_BASE_URL}")
            return ChatOpenAI(
                model=cls.MODEL_NAME,
                temperature=cls.TEMPERATURE,
                timeout=cls.TIMEOUT,
                max_retries=cls.MAX_RETRIES,
                openai_api_key=cls.CUSTOM_API_KEY,
                base_url=cls.CUSTOM_BASE_URL
            )
        
        else:
            raise ValueError(
                f"Unsupported LLM provider: {cls.PROVIDER}. "
                f"Supported: google, openai, anthropic, deepseek, grok, groq, together, ollama, lmstudio, local, custom"
            )
    
    @classmethod
    def get_provider_info(cls) -> dict:
        """Get information about the current provider configuration."""
        return {
            "provider": cls.PROVIDER,
            "model": cls.MODEL_NAME,
            "temperature": cls.TEMPERATURE,
            "max_retries": cls.MAX_RETRIES,
            "timeout": cls.TIMEOUT
        }
