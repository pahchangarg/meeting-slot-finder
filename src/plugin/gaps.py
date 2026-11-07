from __future__ import annotations

from pathlib import Path

from contract import Day, Gap, GapsInput, GapsOutput, Person
from plugin.clock import check_days, check_people, clock, minutes, working_day


def merged_busy(people: list[Person], day: Day) -> list[tuple[int, int]]:
    """Everyone's busy times on ``day``, merged where they overlap or touch."""
    spans = sorted(
        (minutes(busy.start), minutes(busy.end, end=True))
        for person in people
        for busy in person.busy
        if busy.day is day
    )
    merged: list[list[int]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(start, end) for start, end in merged]


def free_gaps(request: GapsInput, workspace: Path) -> GapsOutput:
    check_people(request.people)
    open_at, close_at = working_day(request.day_start, request.day_end)
    gaps = []
    for day in check_days(request.days):
        cursor = open_at
        for start, end in [*merged_busy(request.people, day), (close_at, close_at)]:
            start, end = min(max(start, open_at), close_at), min(end, close_at)
            if start > cursor:
                gaps.append(Gap(day=day, start=clock(cursor), end=clock(start), minutes=start - cursor))
            cursor = max(cursor, end)
    return GapsOutput(gaps=gaps)
