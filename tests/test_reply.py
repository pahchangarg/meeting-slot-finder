from __future__ import annotations

from pathlib import Path

import pytest
from slimconfig import build_output, plain_output
from test_tools import PEOPLE

import verifier
from contract import TASKS, DraftInput, Task
from plugin import draft_reply

# Preferred hours 10:00-16:00; alternatives on Monday and Tuesday. Monday's only free stretch in those
# hours is 12:00-16:00; Tuesday's are 10:00-13:00 and 14:30-16:00.
BASE = {"sender": "Priya", "subject": "Project sync", "people": PEOPLE, "days": ["mon", "tue"],
        "preferred_start": "10:00", "preferred_end": "16:00"}
NO_PROPOSAL = {"proposed_day": None, "proposed_start": None, "proposed_end": None}
MONDAY_NOON = {"proposed_day": "mon", "proposed_start": "12:00", "proposed_end": "13:00"}


def ask(day: str, start: str, end: str) -> dict:
    return {**BASE, "day": day, "start": start, "end": end}


def answer(request: dict, decision: str, reason: str, busy: list[str], proposal: dict, workspace: Path) -> dict:
    """The output a correct agent submits: its choices, and draft_reply's text for them."""
    draft = {key: request[key] for key in ("sender", "subject", "day", "start", "end")}
    draft |= {"decision": decision, "reason": reason, "busy_names": busy, **proposal}
    text = plain_output(draft_reply(build_output(draft, DraftInput), workspace))
    return {"decision": decision, "reason": reason, "busy_names": busy, **proposal, **text}


def verify(request: dict, output: dict, workspace: Path) -> dict:
    given, made = TASKS[Task.REPLY_TO_MEETING_REQUEST]
    return verifier.verify_task(
        "reply-to-meeting-request", build_output(request, given), build_output(output, made), None, str(workspace)
    )


CASES = [
    # Inside preferred hours and nobody busy: ask before accepting.
    (ask("tue", "10:00", "11:00"), "ask_to_accept", "fits", [], NO_PROPOSAL),
    # Before preferred hours, even though everyone is free then.
    (ask("mon", "08:00", "09:00"), "propose_other", "outside_preferred", [], MONDAY_NOON),
    # Bob is busy until 12:00; Alice's meeting ends at 11:00, as the slot starts.
    (ask("mon", "11:00", "12:00"), "propose_other", "conflict", ["Bob"], MONDAY_NOON),
    (ask("mon", "10:30", "11:30"), "propose_other", "conflict", ["Alice", "Bob"], MONDAY_NOON),
    # Runs past 16:00: outside preferred hours comes first, though Bob is busy at 16:00 too.
    (ask("mon", "15:30", "16:30"), "propose_other", "outside_preferred", [], MONDAY_NOON),
    # Five hours: no stretch in preferred hours is that long.
    (ask("tue", "10:00", "15:00"), "decline", "conflict", ["Alice"], NO_PROPOSAL),
]


@pytest.mark.parametrize(("request_", "decision", "reason", "busy", "proposal"), CASES)
def test_approves_the_right_reply(tmp_path: Path, request_: dict, decision: str, reason: str, busy: list, proposal: dict) -> None:
    output = answer(request_, decision, reason, busy, proposal, tmp_path)
    assert verify(request_, output, tmp_path)["valid"] is True


def test_the_wording_is_fixed(tmp_path: Path) -> None:
    accept = answer(ask("tue", "10:00", "11:00"), "ask_to_accept", "fits", [], NO_PROPOSAL, tmp_path)
    assert accept["notification"] == (
        'Accept "Project sync" from Priya on Tue 10:00-11:00? Everyone is free and it is inside your preferred hours.'
    )
    assert accept["reply"] == "Hi Priya, Tue 10:00-11:00 works for me. See you then."
    clash = answer(ask("mon", "11:00", "12:00"), "propose_other", "conflict", ["Bob"], MONDAY_NOON, tmp_path)
    assert clash["notification"] == (
        '"Project sync" from Priya asks for Mon 11:00-12:00, which clashes with Bob. Propose Mon 12:00-13:00 instead?'
    )


def test_never_accepts_outside_preferred_hours(tmp_path: Path) -> None:
    early = ask("mon", "08:00", "09:00")
    accepted = answer(early, "ask_to_accept", "fits", [], NO_PROPOSAL, tmp_path)
    verdict = verify(early, accepted, tmp_path)
    assert verdict["valid"] is False and "propose_other" in verdict["message"]


@pytest.mark.parametrize(
    ("request_", "decision", "reason", "busy", "proposal", "message"),
    [
        (ask("mon", "11:00", "12:00"), "ask_to_accept", "fits", [], NO_PROPOSAL, "decision"),
        (ask("tue", "10:00", "11:00"), "propose_other", "conflict", ["Alice"], MONDAY_NOON, "decision"),
        (ask("mon", "11:00", "12:00"), "propose_other", "outside_preferred", [], MONDAY_NOON, "reason"),
        (ask("mon", "10:30", "11:30"), "propose_other", "conflict", ["Bob", "Alice"], MONDAY_NOON, "busy_names"),
        (ask("mon", "10:30", "11:30"), "propose_other", "conflict", ["Bob"], MONDAY_NOON, "busy_names"),
        # A later slot than the earliest free one.
        (ask("mon", "11:00", "12:00"), "propose_other", "conflict", ["Bob"],
         {"proposed_day": "tue", "proposed_start": "10:00", "proposed_end": "11:00"}, "proposal"),
        # Earlier, but before preferred hours.
        (ask("mon", "11:00", "12:00"), "propose_other", "conflict", ["Bob"],
         {"proposed_day": "tue", "proposed_start": "09:30", "proposed_end": "10:30"}, "proposal"),
        (ask("mon", "11:00", "12:00"), "decline", "conflict", ["Bob"], NO_PROPOSAL, "decision"),
        (ask("tue", "10:00", "15:00"), "propose_other", "conflict", ["Alice"],
         {"proposed_day": "mon", "proposed_start": "12:00", "proposed_end": "17:00"}, "decision"),
    ],
)
def test_refuses_a_wrong_reply(tmp_path: Path, request_, decision, reason, busy, proposal, message) -> None:
    verdict = verify(request_, answer(request_, decision, reason, busy, proposal, tmp_path), tmp_path)
    assert verdict["valid"] is False and message in verdict["message"]


def test_refuses_edited_text_and_bad_requests(tmp_path: Path) -> None:
    request = ask("tue", "10:00", "11:00")
    output = answer(request, "ask_to_accept", "fits", [], NO_PROPOSAL, tmp_path)
    assert verify(request, {**output, "notification": ""}, tmp_path)["valid"] is False
    assert verify(request, {**output, "reply": output["reply"] + " Thanks!"}, tmp_path)["valid"] is False
    assert verify({**request, "preferred_start": "17:00"}, output, tmp_path)["valid"] is False
    assert verify({**request, "sender": " "}, output, tmp_path)["valid"] is False


def test_draft_reply_refuses_mismatched_choices(tmp_path: Path) -> None:
    draft = {"sender": "Priya", "subject": "Sync", "day": "mon", "start": "11:00", "end": "12:00"}
    for bad in (
        {"decision": "ask_to_accept", "reason": "conflict", "busy_names": ["Bob"], **NO_PROPOSAL},
        {"decision": "propose_other", "reason": "conflict", "busy_names": [], **MONDAY_NOON},
        {"decision": "propose_other", "reason": "conflict", "busy_names": ["Bob"], **NO_PROPOSAL},
        {"decision": "decline", "reason": "outside_preferred", "busy_names": [], **MONDAY_NOON},
    ):
        with pytest.raises(ValueError):
            draft_reply(build_output({**draft, **bad}, DraftInput), tmp_path)
        assert verifier.verify_input("draft_reply", build_output({**draft, **bad}, DraftInput))["valid"] is False
