from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Grew"
    debug: bool = False
    database_url: str = f"sqlite+aiosqlite:///{DATA_DIR / 'grew.db'}"
    redis_url: str = "redis://localhost:6379"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Rate limits (requests per second, approximate)
    wttj_concurrency: int = 5
    indeed_concurrency: int = 1
    ats_concurrency: int = 10
    indeed_delay_seconds: float = 3.0

    use_arq_worker: bool = True


settings = Settings()
