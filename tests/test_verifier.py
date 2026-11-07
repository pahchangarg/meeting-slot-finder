from __future__ import annotations

from pathlib import Path

import pytest
from slimconfig import build_output, plain_output
from test_tools import PEOPLE, WEEK

import verifier
from contract import TASKS, TOOLS, ConflictsInput, GapsInput, Task, Tool
from plugin import free_gaps, slot_conflicts


# The verifier gets contract instances, as NanoAgent's sandbox builds them from JSON.
def verify_input(tool: str, value: dict) -> dict:
    return verifier.verify_input(tool, build_output(value, TOOLS[Tool(tool)][0]))


def verify_task(task: str, arguments: dict, output: dict, workspace: Path) -> dict:
    given, made = TASKS[Task(task)]
    return verifier.verify_task(task, build_output(arguments, given), build_output(output, made), None, str(workspace))


def slot_request(minutes: int, days: list[str] | None = None) -> dict:
    return {**WEEK, "days": days or WEEK["days"], "duration_minutes": minutes}


def test_approves_the_tools_own_outputs(tmp_path: Path) -> None:
    for request in (WEEK, {**WEEK, "days": ["wed", "sun"], "day_start": "00:00", "day_end": "24:00"}):
        made = plain_output(free_gaps(build_output(request, GapsInput), tmp_path))
        assert verify_task("common-free-gaps", request, made, tmp_path)["valid"] is True
    slot = {"people": PEOPLE, "day": "mon", "start": "10:59", "end": "16:01"}
    made = plain_output(slot_conflicts(build_output(slot, ConflictsInput), tmp_path))
    assert len(made["conflicts"]) == 3
    assert verify_task("slot-conflicts", slot, made, tmp_path)["valid"] is True


def test_refuses_gaps_that_merge_back_to_back_meetings_wrongly(tmp_path: Path) -> None:
    made = plain_output(free_gaps(build_output(WEEK, GapsInput), tmp_path))
    # A gap at Monday 10:00, between Alice's back-to-back meetings, is no gap.
    extra = {"day": "mon", "start": "10:00", "end": "10:00", "minutes": 0}
    assert verify_task("common-free-gaps", WEEK, {"gaps": [extra, *made["gaps"]]}, tmp_path)["valid"] is False
    # Ignoring Bob's meeting past 17:00 would stretch Monday's gap to the end of the day.
    stretched = [{**made["gaps"][0], "end": "17:00", "minutes": 300}, *made["gaps"][1:]]
    assert verify_task("common-free-gaps", WEEK, {"gaps": stretched}, tmp_path)["valid"] is False
    assert verify_task("common-free-gaps", WEEK, {"gaps": made["gaps"][::-1]}, tmp_path)["valid"] is False


def test_refuses_missing_or_extra_conflicts(tmp_path: Path) -> None:
    slot = {"people": PEOPLE, "day": "mon", "start": "11:00", "end": "12:00"}
    bob = {"name": "Bob", "busy": PEOPLE[1]["busy"][0]}
    alice = {"name": "Alice", "busy": PEOPLE[0]["busy"][1]}
    assert verify_task("slot-conflicts", slot, {"conflicts": [bob]}, tmp_path)["valid"] is True
    assert verify_task("slot-conflicts", slot, {"conflicts": []}, tmp_path)["valid"] is False
    assert verify_task("slot-conflicts", slot, {"conflicts": [alice, bob]}, tmp_path)["valid"] is False


@pytest.mark.parametrize(
    ("minutes", "days", "slot"),
    [
        (60, None, ("mon", "12:00", "13:00")),
        (240, None, ("mon", "12:00", "16:00")),  # exactly fills Monday's gap
        (180, ["tue"], ("tue", "09:30", "12:30")),
        (211, ["tue"], (None, None, None)),  # one minute longer than Tuesday's longest gap
        (241, None, (None, None, None)),
    ],
)
def test_approves_the_earliest_common_slot(tmp_path: Path, minutes: int, days: list | None, slot: tuple) -> None:
    output = dict(zip(("day", "start", "end"), slot))
    assert verify_task("earliest-common-slot", slot_request(minutes, days), output, tmp_path)["valid"] is True


@pytest.mark.parametrize(
    ("slot", "message"),
    [
        (("tue", "09:30", "10:30"), "earlier and free"),
        (("mon", "11:00", "12:00"), "busy"),
        (("mon", "16:00", "17:00"), "busy"),
        (("mon", "12:00", "12:59"), "not 60 minutes"),
        (("mon", "08:00", "09:00"), "outside the working day"),
        (("wed", "09:00", "10:00"), "not one of the requested days"),
        (("mon", "noon", "13:00"), "not 60 minutes"),
        ((None, None, None), "no field may be null"),
        (("mon", "12:00", None), "no field may be null"),
    ],
)
def test_refuses_a_wrong_slot(tmp_path: Path, slot: tuple, message: str) -> None:
    output = dict(zip(("day", "start", "end"), slot))
    verdict = verify_task("earliest-common-slot", slot_request(60), output, tmp_path)
    assert verdict["valid"] is False and message in verdict["message"]


def test_no_slot_must_be_all_null(tmp_path: Path) -> None:
    verdict = verify_task("earliest-common-slot", slot_request(241), {"day": "mon", "start": "12:00", "end": "16:01"}, tmp_path)
    assert verdict["valid"] is False and "null" in verdict["message"]
    bad = {**slot_request(30), "duration_minutes": 0}
    assert verify_task("earliest-common-slot", bad, {"day": None, "start": None, "end": None}, tmp_path)["valid"] is False


def test_checks_what_the_types_cannot_say() -> None:
    assert verify_input("free_gaps", WEEK)["valid"] is True
    assert verify_input("free_gaps", {**WEEK, "people": []})["valid"] is False
    assert verify_input("free_gaps", {**WEEK, "days": []})["valid"] is False
    assert verify_input("free_gaps", {**WEEK, "day_end": "25:00"})["valid"] is False
    assert verify_input("free_gaps", {**WEEK, "day_start": "24:00", "day_end": "24:00"})["valid"] is False
    blank = [{"name": " ", "busy": []}]
    assert verify_input("free_gaps", {**WEEK, "people": blank})["valid"] is False
    slot = {"people": PEOPLE, "day": "mon", "start": "12:00", "end": "12:00"}
    assert verify_input("slot_conflicts", slot)["valid"] is False
