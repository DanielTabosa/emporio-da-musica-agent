from datetime import datetime

from emporio_agent.config import STORE_TZ, parse_now
from emporio_agent.store_info import is_open, next_opening, store_status


def at(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=STORE_TZ)


def test_parse_now():
    assert parse_now("2026-03-16 10:00") == at("2026-03-16 10:00")
    assert parse_now("2026-03-16").hour == 0
    assert parse_now("").tzinfo is not None
    # a UTC-3 instant is converted to the store's UTC-4
    assert parse_now("2026-03-16 10:00-03:00").hour == 9


def test_open_on_monday_morning():
    assert is_open(at("2026-03-16 10:00"))


def test_closed_at_closing_time_exactly():
    assert is_open(at("2026-03-20 17:59"))
    assert not is_open(at("2026-03-20 18:00"))


def test_saturday_hours():
    assert is_open(at("2026-03-21 12:30"))
    assert not is_open(at("2026-03-21 14:00"))


def test_sunday_and_holiday_closed():
    assert not is_open(at("2026-03-22 10:00"))  # Sunday
    assert not is_open(at("2026-11-02 10:00"))  # Finados, a Monday


def test_next_opening():
    # Saturday afternoon -> Monday 09:00
    assert next_opening(at("2026-03-21 14:00")) == at("2026-03-23 09:00")
    # Saturday early morning -> same day 09:00
    assert next_opening(at("2026-03-21 08:30")) == at("2026-03-21 09:00")
    # Sunday Nov 1 2026 -> Nov 2 is a holiday, so Tuesday Nov 3
    assert next_opening(at("2026-11-01 15:00")) == at("2026-11-03 09:00")


def test_store_status_dict():
    s = store_status(at("2026-03-16 10:00"))
    assert s["is_open"] is True
    assert s["weekday"] == "segunda-feira"
    assert s["today_hours"] == "09:00 às 18:00"
    assert "next_opening" not in s
    assert s["phone"] == "(67) 3341-4444"
    assert s["whatsapp"] == "(67) 3321-4500"
    assert "Rua 14 de Maio, 3200" in s["address"]

    s = store_status(at("2026-03-22 10:00"))
    assert s["is_open"] is False
    assert s["today_hours"] == "fechado"
    assert s["next_opening"] == "segunda-feira 23/03 às 09:00"
