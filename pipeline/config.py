"""Runtime settings (env-driven) and competitor-config loading."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from pipeline.schemas import CompetitorsFile

# Repo root = two levels up from this file (pipeline/config.py -> repo root).
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_COMPETITORS_PATH = REPO_ROOT / "config" / "competitors.yaml"


class Settings(BaseSettings):
    """Environment-driven settings. Reads from process env and `.env`."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Paths
    data_dir: Path = Field(default=REPO_ROOT / "data", alias="COMPETE_DATA_DIR")
    duckdb_path: Path = Field(
        default=REPO_ROOT / "data" / "compete.duckdb", alias="COMPETE_DUCKDB_PATH"
    )

    # LLM
    llm_provider: str = Field(default="gemini", alias="COMPETE_LLM_PROVIDER")
    llm_model: str = Field(default="gemini-1.5-flash", alias="COMPETE_LLM_MODEL")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    ollama_base_url: str = Field(default="http://localhost:11434/v1", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.1", alias="OLLAMA_MODEL")
    # Max characters of page text sent to the LLM per extraction (cost control).
    llm_max_input_chars: int = Field(default=6000, alias="COMPETE_LLM_MAX_INPUT_CHARS")

    # Embeddings - provider: hashing (default, zero-dep) | minilm | gemini
    embed_provider: str = Field(default="hashing", alias="COMPETE_EMBED_PROVIDER")
    embed_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", alias="COMPETE_EMBED_MODEL"
    )
    embed_dim: int = Field(default=256, alias="COMPETE_EMBED_DIM")

    # Change detection: cosine similarity at/above this = "minor edit" (skip LLM).
    diff_similarity_threshold: float = Field(default=0.9, alias="COMPETE_DIFF_SIMILARITY_THRESHOLD")

    # Collection
    user_agent: str = Field(
        default="compete-intel-bot/0.1 (+https://github.com/your/repo)",
        alias="COMPETE_USER_AGENT",
    )
    request_timeout: float = Field(default=30.0, alias="COMPETE_REQUEST_TIMEOUT")
    throttle_seconds: float = Field(default=2.0, alias="COMPETE_THROTTLE_SECONDS")
    respect_robots: bool = Field(default=True, alias="COMPETE_RESPECT_ROBOTS")

    # Alerts
    alerts_enabled: bool = Field(default=False, alias="COMPETE_ALERTS_ENABLED")
    alert_min_significance: int = Field(default=4, alias="COMPETE_ALERT_MIN_SIGNIFICANCE")
    slack_webhook_url: str | None = Field(default=None, alias="SLACK_WEBHOOK_URL")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    alert_email_to: str | None = Field(default=None, alias="ALERT_EMAIL_TO")

    # API
    api_host: str = Field(default="127.0.0.1", alias="COMPETE_API_HOST")
    api_port: int = Field(default=8000, alias="COMPETE_API_PORT")
    cors_origins: str = Field(default="http://localhost:3000", alias="COMPETE_CORS_ORIGINS")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def ensure_dirs(self) -> None:
        """Create data directories if missing (idempotent)."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "raw").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "reports").mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()


def load_competitors(path: Path | None = None) -> CompetitorsFile:
    """Load and validate the competitor configuration file."""
    p = path or DEFAULT_COMPETITORS_PATH
    if not p.exists():
        raise FileNotFoundError(f"Competitor config not found: {p}")
    with p.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return CompetitorsFile.model_validate(data)
