"""Configuration settings for the Zoho Projects Bot"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    
    # Zoho Projects Configuration
    zoho_client_id: str = Field(..., env="ZOHO_CLIENT_ID")
    zoho_client_secret: str = Field(..., env="ZOHO_CLIENT_SECRET")
    zoho_refresh_token: str = Field(..., env="ZOHO_REFRESH_TOKEN")
    zoho_portal_id: str = Field(..., env="ZOHO_PORTAL_ID")
    
    # Zoho API URLs
    zoho_api_base_url: str = Field(
        default="https://projectsapi.zoho.com", 
        env="ZOHO_API_BASE_URL"
    )
    zoho_auth_base_url: str = Field(
        default="https://accounts.zoho.com", 
        env="ZOHO_AUTH_BASE_URL"
    )
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Agent Configuration
    max_iterations: int = Field(default=10, env="MAX_ITERATIONS")
    temperature: float = Field(default=0.1, env="TEMPERATURE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
