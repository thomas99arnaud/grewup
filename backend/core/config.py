from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _clean_secret(value: str) -> str:
    return value.strip().strip("'").strip('"')


def _dotenv_value(*names: str) -> str:
    path = ROOT_DIR / ".env"
    if not path.exists():
        return ""
    found: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, raw = stripped.partition("=")
        found[key.strip()] = _clean_secret(raw)
    for name in names:
        if found.get(name):
            return found[name]
    return ""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

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

    openai_api_key: str = ""
    openrouter_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    candidate_dossier_path: str = ""

    @model_validator(mode="after")
    def _normalize_llm_key(self):
        """Cursor / le système posent souvent OPENAI_API_KEY : ça ne doit pas écraser OpenRouter."""
        file_key = _dotenv_value("OPENAI_API_KEY", "OPENROUTER_API_KEY")
        env_key = _clean_secret(self.openai_api_key) or _clean_secret(self.openrouter_api_key)
        if "openrouter.ai" in (self.openai_base_url or "").lower():
            if file_key.startswith("sk-or-v1-"):
                self.openai_api_key = file_key
                return self
            if env_key.startswith("sk-or-v1-"):
                self.openai_api_key = env_key
                return self
        self.openai_api_key = env_key or file_key
        return self


settings = Settings()
