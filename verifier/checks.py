"""Checks shared by the tool verifiers. Pure functions of their arguments."""

import re

from contract import Day

TIME = re.compile(r"^([01]\d|2[0-4]):([0-5]\d)$")
WEEK = list(Day)
DAY = 1440


def result(valid, message, *, score=None, **details):
    return {
        "valid": valid,
        "score": float(valid) if score is None else score,
        "message": message,
        "details": details,
    }


def to_minutes(text, *, end=False):
    """``HH:MM`` as minutes after midnight, or None when it is no time (24:00 only ends a span)."""
    match = TIME.fullmatch(text)
    if not match:
        return None
    value = int(match[1]) * 60 + int(match[2])
    return value if value < DAY or (value == DAY and end) else None


def span_problem(what, start, end):
    first, last = to_minutes(start), to_minutes(end, end=True)
    if first is None or last is None:
        return f"{what} {start}-{end} is not two HH:MM times"
    if first >= last:
        return f"{what} {start}-{end} must end after it starts"
    return None


def people_problem(people):
    names = [person.name for person in people]
    if not people:
        return "people must name at least one person"
    if any(not name.strip() for name in names) or len(set(names)) != len(names):
        return "people's names must be unique and not blank"
    for person in people:
        for busy in person.busy:
            problem = span_problem(f"{person.name}'s busy time", busy.start, busy.end)
            if problem:
                return problem
    return None


def days_problem(days):
    if not days or len(set(days)) != len(days):
        return "days must name at least one day, each once"
    return None


def first_problem(*problems):
    return next((problem for problem in problems if problem), None)


def busy_minutes(people, day):
    """One flag per minute of ``day``: whether anyone is busy then."""
    taken = [False] * DAY
    for person in people:
        for busy in person.busy:
            if busy.day is day:
                for minute in range(to_minutes(busy.start), to_minutes(busy.end, end=True)):
                    taken[minute] = True
    return taken


def expected_gaps(people, days, day_start, day_end):
    """[(day, start, end)] in minutes: every free stretch of the working day, minute by minute."""
    gaps = []
    open_at, close_at = to_minutes(day_start), to_minutes(day_end, end=True)
    for day in sorted(days, key=WEEK.index):
        taken = busy_minutes(people, day)
        start = None
        for minute in range(open_at, close_at + 1):
            free = minute < close_at and not taken[minute]
            if free and start is None:
                start = minute
            elif not free and start is not None:
                gaps.append((day, start, minute))
                start = None
    return gaps


def clock(value):
    return f"{value // 60:02d}:{value % 60:02d}"
