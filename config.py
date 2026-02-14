import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()


class AppConfig(BaseModel):
    """Application configuration"""

    # Paths
    BASE_DIR: Path = Path(__file__).parent
    DATA_DIR: Path = BASE_DIR / "data"

    # API Keys
    openai_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )
    google_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("GOOGLE_API_KEY")
    )
    anthropic_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY")
    )
    notion_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("NOTION_API_KEY")
    )

    # Notion Settings
    notion_parent_page_id: Optional[str] = Field(
        default_factory=lambda: os.getenv("NOTION_PARENT_PAGE_ID")
    )

    # LLM Settings
    default_llm_provider: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_LLM_PROVIDER", "openai")
    )
    default_model: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_MODEL", "gpt-5-nano")
    )
    temperature: float = 0.7
    max_tokens: int = 2000

    # Application Settings
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    max_conversation_history: int = 50

    model_config = {"arbitrary_types_allowed": True}

    def model_post_init(self, __context):
        """Ensure data directory exists after init"""
        self.DATA_DIR.mkdir(exist_ok=True)

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for specified provider"""
        key_map = {
            "openai": self.openai_api_key,
            "google": self.google_api_key,
            "gemini": self.google_api_key,
            "anthropic": self.anthropic_api_key,
            "claude": self.anthropic_api_key,
            "notion": self.notion_api_key,
        }
        return key_map.get(provider.lower())


# Global config instance
config = AppConfig()
