"""
Configuration for the Student Management Text-to-SQL API
"""
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""

    # API Settings
    api_title: str = "Student Management Text-to-SQL API"
    api_description: str = "MVP for converting natural language to SQL queries"
    api_version: str = "1.0.0"

    # Database
    database_url: str = "student_management.db"

    # LLM Settings
    llm_provider: str = "openai"  # "local", "openai", "anthropic", or "modal"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    modal_endpoint_url: Optional[str] = None
    modal_api_key: Optional[str] = None
    modal_timeout_seconds: int = 120
    llm_model: str = "spider1_qlora_latest"  # Local model path or external model name
    llm_device: str = "auto"  # "auto", "cpu", or "cuda"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 500

    # Security
    allowed_sql_keywords: list = [
        "SELECT", "FROM", "WHERE", "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN",
        "GROUP BY", "ORDER BY", "LIMIT", "OFFSET", "COUNT", "SUM", "AVG", "MIN", "MAX",
        "AS", "AND", "OR", "NOT", "IN", "BETWEEN", "LIKE", "IS NULL", "IS NOT NULL",
        "INSERT INTO", "VALUES", "UPDATE", "SET", "DELETE FROM"
    ]

    # Query Safety
    max_query_rows: int = 1000
    allow_write_operations: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()