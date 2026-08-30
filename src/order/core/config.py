"""Configuration settings"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API Keys
    tinyfish_api_key: str = ""
    github_token: str = ""
    openai_api_key: str = ""
    openrouter_api_key: str = ""

    # CORS — set to your deployed frontend URL in production
    frontend_url: str = ""
    
    # Model config
    llm_model: str = "openrouter/nova-pro"
    
    # Paths
    data_dir: str = "~/.order"
    
    # Cron
    cron_tick_interval: int = 60
    gather_interval_minutes: int = 5
    reduce_interval_minutes: int = 10
    expire_interval_hours: int = 1
    
    # Anti-accumulation
    commitment_expire_hours: int = 72  # 3 days
    
    class Config:
        env_file = ".env"
        env_prefix = "ORDER_"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()