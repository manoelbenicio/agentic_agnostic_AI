"""Runtime settings for the FastAPI control plane."""

from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_DATABASE_URL = "postgresql://aop_dev:aop_dev_postgres_20260626@127.0.0.1:5432/aop"
DEFAULT_REDIS_URL = "redis://127.0.0.1:6379/0"


@dataclass(frozen=True, slots=True)
class Settings:
    """Environment-backed app settings."""

    database_url: str = DEFAULT_DATABASE_URL
    redis_url: str = DEFAULT_REDIS_URL
    host: str = "127.0.0.1"
    port: int = 8090

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
            redis_url=os.environ.get("REDIS_URL", DEFAULT_REDIS_URL),
            host=os.environ.get("AOP_HOST", "127.0.0.1"),
            port=int(os.environ.get("AOP_PORT", "8090")),
        )
