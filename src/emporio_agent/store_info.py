"""Store contact data and opening hours (manual sections 1.2 and 2).

The manual lists two phone numbers: (67) 3341-4444 on the cover and in
the company data table, and (67) 3321-4500 as the WhatsApp channel in
section 7. We expose both with their labels instead of picking one.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from .config import STORE_TZ

STORE = {
    "name": "Empório da Música",
    "address": "Rua 14 de Maio, 3200, Centro, Campo Grande, MS, CEP 79202-333",
    "phone": "(67) 3341-4444",
    "whatsapp": "(67) 3321-4500",
    "email": "contato@emporiodamusica.com.br",
    "timezone": "America/Campo_Grande",
}

# weekday() -> (open, close). Monday is 0. None means closed.
WEEKLY_HOURS: dict[int, tuple[time, time] | None] = {
    0: (time(9, 0), time(18, 0)),
    1: (time(9, 0), time(18, 0)),
    2: (time(9, 0), time(18, 0)),
    3: (time(9, 0), time(18, 0)),
    4: (time(9, 0), time(18, 0)),
    5: (time(9, 0), time(13, 0)),
    6: None,
}

# Brazilian national holidays with a fixed date (month, day).
# Movable holidays (Carnival, Good Friday, Corpus Christi) are not covered.
FIXED_HOLIDAYS = {
    (1, 1),
    (4, 21),
    (5, 1),
    (9, 7),
    (10, 12),
    (11, 2),
    (11, 15),
    (12, 25),
}

WEEKDAY_NAMES = [
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
]

HOURS_TEXT = "segunda a sexta das 09:00 às 18:00, sábado das 09:00 às 13:00, domingo e feriados fechado"


def is_holiday(day: date) -> bool:
    return (day.month, day.day) in FIXED_HOLIDAYS


def opening_hours(day: date) -> tuple[time, time] | None:
    if is_holiday(day):
        return None
    return WEEKLY_HOURS[day.weekday()]


def is_open(now: datetime) -> bool:
    hours = opening_hours(now.date())
    if hours is None:
        return False
    open_at, close_at = hours
    return open_at <= now.time() < close_at


def next_opening(now: datetime) -> datetime:
    """First moment the store opens at or after `now`."""
    day = now.date()
    for _ in range(14):  # never more than a few days until a working day
        hours = opening_hours(day)
        if hours is not None:
            open_at, close_at = hours
            candidate = datetime.combine(day, open_at, tzinfo=now.tzinfo)
            if day > now.date() or now.time() < open_at:
                return candidate
        day += timedelta(days=1)
    raise RuntimeError("no opening day found in the next two weeks")


def store_status(now: datetime | None = None) -> dict:
    now = now or datetime.now(tz=STORE_TZ)
    hours = opening_hours(now.date())
    today_text = (
        f"{hours[0]:%H:%M} às {hours[1]:%H:%M}" if hours else "fechado"
    )
    result = {
        **STORE,
        "now": now.strftime("%d/%m/%Y %H:%M"),
        "weekday": WEEKDAY_NAMES[now.weekday()],
        "is_open": is_open(now),
        "today_hours": today_text,
        "weekly_hours": HOURS_TEXT,
    }
    if not result["is_open"]:
        nxt = next_opening(now)
        result["next_opening"] = (
            f"{WEEKDAY_NAMES[nxt.weekday()]} {nxt:%d/%m} às {nxt:%H:%M}"
        )
    return result
