from __future__ import annotations

from pathlib import Path

import pytest
from slimconfig import build_output

from contract import ConflictsInput, GapsInput
from plugin import free_gaps, slot_conflicts

PEOPLE = [
    # Back-to-back on Monday morning, so no gap at 10:00.
    {"name": "Alice", "busy": [{"day": "mon", "start": "09:00", "end": "10:00"},
                               {"day": "mon", "start": "10:00", "end": "11:00"},
                               {"day": "tue", "start": "13:00", "end": "14:30"}]},
    # Overlaps Alice, and runs past the end of the working day.
    {"name": "Bob", "busy": [{"day": "mon", "start": "10:30", "end": "12:00"},
                             {"day": "mon", "start": "16:00", "end": "18:00"},
                             {"day": "tue", "start": "09:00", "end": "09:30"}]},
    {"name": "Cara", "busy": []},
]
WEEK = {"people": PEOPLE, "days": ["tue", "mon"], "day_start": "09:00", "day_end": "17:00"}


def test_finds_the_common_gaps_in_week_order(tmp_path: Path) -> None:
    gaps = free_gaps(build_output(WEEK, GapsInput), tmp_path).gaps
    assert [(g.day.value, g.start, g.end, g.minutes) for g in gaps] == [
        ("mon", "12:00", "16:00", 240),
        ("tue", "09:30", "13:00", 210),
        ("tue", "14:30", "17:00", 150),
    ]


def test_a_free_day_is_one_gap_and_a_busy_day_none(tmp_path: Path) -> None:
    request = {**WEEK, "days": ["wed"], "day_end": "24:00"}
    gaps = free_gaps(build_output(request, GapsInput), tmp_path).gaps
    assert [(g.start, g.end, g.minutes) for g in gaps] == [("09:00", "24:00", 900)]
    booked = {**WEEK, "people": [{"name": "Dee", "busy": [{"day": "mon", "start": "08:00", "end": "18:00"}]}]}
    assert free_gaps(build_output({**booked, "days": ["mon"]}, GapsInput), tmp_path).gaps == []


def test_conflicts_share_a_minute_with_the_slot(tmp_path: Path) -> None:
    slot = {"people": PEOPLE, "day": "mon", "start": "11:00", "end": "12:00"}
    found = slot_conflicts(build_output(slot, ConflictsInput), tmp_path).conflicts
    # Alice's 10:00-11:00 ends as the slot starts: no conflict.
    assert [(c.name, c.busy.start) for c in found] == [("Bob", "10:30")]
    touching = {**slot, "start": "12:00", "end": "16:00"}
    assert slot_conflicts(build_output(touching, ConflictsInput), tmp_path).conflicts == []


def test_refuses_malformed_requests(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="HH:MM"):
        free_gaps(build_output({**WEEK, "day_start": "9am"}, GapsInput), tmp_path)
    with pytest.raises(ValueError, match="after"):
        free_gaps(build_output({**WEEK, "day_start": "17:00", "day_end": "09:00"}, GapsInput), tmp_path)
    with pytest.raises(ValueError, match="24:00"):
        free_gaps(build_output({**WEEK, "day_start": "24:00"}, GapsInput), tmp_path)
    with pytest.raises(ValueError, match="each once"):
        free_gaps(build_output({**WEEK, "days": ["mon", "mon"]}, GapsInput), tmp_path)
    twins = [PEOPLE[2], PEOPLE[2]]
    with pytest.raises(ValueError, match="unique"):
        free_gaps(build_output({**WEEK, "people": twins}, GapsInput), tmp_path)
    backwards = [{"name": "Eve", "busy": [{"day": "mon", "start": "11:00", "end": "10:00"}]}]
    with pytest.raises(ValueError, match="end after"):
        free_gaps(build_output({**WEEK, "people": backwards}, GapsInput), tmp_path)
