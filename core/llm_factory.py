from typing import Optional, Dict
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from config import config


class LLMFactory:
    """Factory for creating LLM instances"""

    # Default models per provider
    DEFAULT_MODELS = {
        "openai": "gpt-5-nano",
        "google": "gemini-3.0-flash",
        "anthropic": "claude-sonnet-4-20250514"
    }

    @staticmethod
    def create_llm(
        provider: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> BaseChatModel:
        """
        Create an LLM instance based on provider.

        Args:
            provider: LLM provider name (openai, gemini, claude)
            model: Specific model name
            temperature: Generation temperature
            **kwargs: Additional provider-specific parameters

        Returns:
            Chat model instance
        """
        provider = provider.lower()

        if provider == "openai":
            return LLMFactory._create_openai(model, temperature, **kwargs)
        elif provider in ["gemini", "google"]:
            return LLMFactory._create_gemini(model, temperature, **kwargs)
        elif provider in ["claude", "anthropic"]:
            return LLMFactory._create_claude(model, temperature, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    def _create_openai(
        model: Optional[str], temperature: float, **kwargs
    ) -> ChatOpenAI:
        """Create OpenAI LLM"""
        api_key = config.get_api_key("openai")
        if not api_key:
            raise ValueError("OpenAI API key not found in .env")

        return ChatOpenAI(
            model=model or LLMFactory.DEFAULT_MODELS["openai"],
            temperature=temperature,
            openai_api_key=api_key,
            **kwargs,
        )

    @staticmethod
    def _create_gemini(
        model: Optional[str], temperature: float, **kwargs
    ) -> ChatGoogleGenerativeAI:
        """Create Google Gemini LLM"""
        api_key = config.get_api_key("google")
        if not api_key:
            raise ValueError("Google API key not found in .env")

        return ChatGoogleGenerativeAI(
            model=model or LLMFactory.DEFAULT_MODELS["gemini"],
            temperature=temperature,
            google_api_key=api_key,
            **kwargs,
        )

    @staticmethod
    def _create_claude(
        model: Optional[str], temperature: float, **kwargs
    ) -> ChatAnthropic:
        """Create Anthropic Claude LLM"""
        api_key = config.get_api_key("anthropic")
        if not api_key:
            raise ValueError("Anthropic API key not found in .env")

        return ChatAnthropic(
            model=model or LLMFactory.DEFAULT_MODELS["claude"],
            temperature=temperature,
            anthropic_api_key=api_key,
            **kwargs,
        )

    @staticmethod
    def list_available_providers() -> Dict[str, bool]:
        """Check which providers have valid API keys configured"""
        return {
            "openai": bool(config.get_api_key("openai")),
            "gemini": bool(config.get_api_key("google")),
            "claude": bool(config.get_api_key("anthropic")),
        }
