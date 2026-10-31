"""Settings from environment variables. In development, reads the root `.env` without overriding the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path = ROOT / ".env") -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = field(default="", repr=False)
    gemini_model: str = ""
    data_dir: Path = ROOT / "data" / "build"
    timezone: str = "America/Campo_Grande"
    chat_timeout_s: float = 25.0
    max_rounds: int = 3
    max_tool_calls: int = 6
    max_model_calls: int = 4
    history_turns: int = 10
    session_ttl_s: int = 30 * 60
    max_sessions: int = 500
    turns_per_minute: int = 10
    max_turns_per_day: int = 400  # whole process; protects the Gemini budget on the public demo
    thinking_level: str = ""
    expose_trace: bool = True
    admin_token: str = field(default="", repr=False)  # empty: /admin/api/stats always answers 404
    pricing_path: Path = ROOT / "evals" / "pricing.json"
    extra: dict = field(default_factory=dict)

    @property
    def catalog_db(self) -> Path:
        return self.data_dir / "catalog.db"

    @property
    def orders_db(self) -> Path:
        return self.data_dir / "orders-demo.db"

    @property
    def policy_index(self) -> Path:
        return self.data_dir / "policy_sections.json"


def get_settings() -> Settings:
    load_dotenv()
    env = os.environ
    return Settings(
        gemini_api_key=env.get("GEMINI_API_KEY", ""),
        gemini_model=env.get("GEMINI_MODEL", ""),
        data_dir=Path(env.get("DATA_DIR", ROOT / "data" / "build")),
        timezone=env.get("APP_TIMEZONE", "America/Campo_Grande"),
        chat_timeout_s=float(env.get("CHAT_TIMEOUT_S", "25")),
        max_turns_per_day=int(env.get("MAX_TURNS_PER_DAY", "400")),
        thinking_level=env.get("GEMINI_THINKING_LEVEL", ""),
        expose_trace=env.get("EXPOSE_TRACE", "1") == "1",
        admin_token=env.get("ADMIN_TOKEN", ""),
    )
