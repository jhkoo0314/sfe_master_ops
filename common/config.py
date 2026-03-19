"""
SFE OPS 앱 설정 관리

pydantic-settings 기반으로 .env 파일을 자동으로 읽어옵니다.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """SFE OPS 전체 설정. .env 파일에서 자동으로 로드됩니다."""

    # Supabase
    supabase_url: str = Field(default="", description="Supabase 프로젝트 URL")
    supabase_anon_key: str = Field(default="", description="Supabase anon 키")
    supabase_service_role_key: str = Field(default="", description="Supabase service role 키")

    # Agent LLM
    llm_provider: str = Field(default="", description="Agent LLM provider (openai/claude/gemini)")
    llm_model: str = Field(default="", description="Agent LLM model name")
    llm_api_key: str = Field(default="", description="Agent LLM API key")
    llm_base_url: str = Field(default="", description="Optional custom LLM base URL")
    llm_timeout_sec: int = Field(default=20, description="Agent LLM timeout seconds")
    llm_max_tokens: int = Field(default=1200, description="Agent LLM max output tokens")
    llm_temperature: float = Field(default=0.1, description="Agent LLM temperature")

    # OPS Core API
    ops_api_host: str = Field(default="0.0.0.0")
    ops_api_port: int = Field(default=8000)
    ops_env: str = Field(default="development")

    # 데이터 경로
    data_dir: str = Field(default="./data")
    fixture_dir: str = Field(default="./tests/fixtures")

    # Streamlit
    streamlit_port: int = Field(default=8501)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# 전역 싱글톤 - import해서 바로 사용
settings = Settings()
