from __future__ import annotations

from pathlib import Path

from contract import Conflict, ConflictsInput, ConflictsOutput
from plugin.clock import check_people, minutes


def slot_conflicts(request: ConflictsInput, workspace: Path) -> ConflictsOutput:
    check_people(request.people)
    start, end = minutes(request.start), minutes(request.end, end=True)
    if start >= end:
        raise ValueError("the slot must end after it starts")
    conflicts = [
        Conflict(name=person.name, busy=busy)
        for person in request.people
        for busy in person.busy
        if busy.day is request.day and minutes(busy.start) < end and start < minutes(busy.end, end=True)
    ]
    return ConflictsOutput(conflicts=conflicts)
