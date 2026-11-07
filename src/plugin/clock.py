"""Times of day as minutes, and the request checks the tools share."""

from __future__ import annotations

import re

from contract import Day, Person

TIME = re.compile(r"^([01]\d|2[0-4]):([0-5]\d)$")
WEEK = list(Day)


def minutes(text: str, *, end: bool = False) -> int:
    """``HH:MM`` as minutes after midnight; 24:00 only when ``end``."""
    match = TIME.fullmatch(text)
    if not match:
        raise ValueError(f"time must be HH:MM, not {text!r}")
    value = int(match[1]) * 60 + int(match[2])
    if value > 1440:
        raise ValueError(f"{text} is not a time of day")
    if value == 1440 and not end:
        raise ValueError("24:00 may only end a span")
    return value


def clock(value: int) -> str:
    return f"{value // 60:02d}:{value % 60:02d}"


def check_people(people: list[Person]) -> None:
    names = [person.name for person in people]
    if not people or any(not name.strip() for name in names) or len(set(names)) != len(names):
        raise ValueError("people must be at least one, with unique, non-blank names")
    for person in people:
        for busy in person.busy:
            if minutes(busy.start) >= minutes(busy.end, end=True):
                raise ValueError(f"{person.name}'s busy time {busy.start}-{busy.end} must end after it starts")


def working_day(day_start: str, day_end: str) -> tuple[int, int]:
    start, end = minutes(day_start), minutes(day_end, end=True)
    if start >= end:
        raise ValueError("day_end must be after day_start")
    return start, end


def check_days(days: list[Day]) -> list[Day]:
    if not days or len(set(days)) != len(days):
        raise ValueError("days must name at least one day, each once")
    return sorted(days, key=WEEK.index)
