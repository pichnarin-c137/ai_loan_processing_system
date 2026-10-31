from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> the repo root, wherever the process starts.
REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Read from environment variables (case-insensitive), then the repo-root .env.

    The defaults match infra/compose.yml for local development only.
    Production sets every value explicitly.
    """

    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    app_name: str = "Loan Desk"

    database_url: str = "postgresql+psycopg://loan_desk:loan_desk@localhost:5433/loan_desk"
    redis_url: str = "redis://localhost:6379/0"

    # Any S3-compatible store: SeaweedFS locally, Cloudflare R2 in production.
    s3_endpoint_url: str = "http://localhost:8333"
    s3_region: str = "auto"
    s3_access_key: str = "loan-desk"
    s3_secret_key: SecretStr = SecretStr("loan-desk-secret")
    s3_bucket: str = "loan-desk-documents"


@lru_cache
def get_settings() -> Settings:
    return Settings()
