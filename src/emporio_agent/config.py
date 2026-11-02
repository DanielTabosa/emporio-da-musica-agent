"""Settings read from environment variables (and .env).

EMPORIO_NOW is the agent's idea of "now". The dataset has orders up to
March 2026, so by default we freeze time at a Monday morning in March
2026. This makes store hours and order deadlines reproducible in tests
and in the example conversations. Leave it empty to use the real clock.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from .data import DEFAULT_DATA_DIR

STORE_TZ = ZoneInfo("America/Campo_Grande")
DEFAULT_MODEL = "claude-sonnet-5-5"


@dataclass(frozen=True)
class Settings:
    model: str
    data_dir: Path
    now: datetime  # timezone-aware, store timezone
    api_key: str | None


def parse_now(value: str | None) -> datetime:
    """'2026-03-16 10:00' or '2026-03-16' (midnight) in the store timezone.

    Empty value means the real current time, converted to the store timezone.
    """
    value = (value or "").strip()
    if not value:
        return datetime.now(tz=STORE_TZ)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=STORE_TZ)
    return parsed.astimezone(STORE_TZ)


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        model=os.getenv("EMPORIO_MODEL", DEFAULT_MODEL),
        data_dir=Path(os.getenv("EMPORIO_DATA_DIR", DEFAULT_DATA_DIR)),
        now=parse_now(os.getenv("EMPORIO_NOW")),
        api_key=os.getenv("ANTHROPIC_API_KEY") or None,
    )
