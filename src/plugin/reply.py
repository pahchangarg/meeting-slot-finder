"""draft_reply: the notification you answer and the reply it sends, from fixed templates."""

from __future__ import annotations

from pathlib import Path

from contract import Decision, DraftInput, DraftOutput, Reason
from plugin.clock import minutes


def check_draft(request: DraftInput) -> None:
    if not request.sender.strip() or not request.subject.strip():
        raise ValueError("sender and subject must not be blank")
    if minutes(request.start) >= minutes(request.end, end=True):
        raise ValueError("the requested slot must end after it starts")
    if (request.decision is Decision.ASK_TO_ACCEPT) != (request.reason is Reason.FITS):
        raise ValueError("ask_to_accept goes with reason fits, and only with it")
    if bool(request.busy_names) != (request.reason is Reason.CONFLICT):
        raise ValueError("busy_names names who is busy for a conflict, and is empty otherwise")
    proposed = (request.proposed_day, request.proposed_start, request.proposed_end)
    if request.decision is Decision.PROPOSE_OTHER:
        if None in proposed:
            raise ValueError("propose_other needs proposed_day, proposed_start and proposed_end")
        if minutes(request.proposed_start) >= minutes(request.proposed_end, end=True):
            raise ValueError("the proposed slot must end after it starts")
    elif proposed != (None, None, None):
        raise ValueError("only propose_other proposes a slot")


def when(day, start: str, end: str) -> str:
    return f"{day.value.capitalize()} {start}-{end}"


def draft_reply(request: DraftInput, workspace: Path) -> DraftOutput:
    check_draft(request)
    asked = when(request.day, request.start, request.end)
    if request.decision is Decision.ASK_TO_ACCEPT:
        return DraftOutput(
            notification=(
                f'Accept "{request.subject}" from {request.sender} on {asked}?'
                " Everyone is free and it is inside your preferred hours."
            ),
            reply=f"Hi {request.sender}, {asked} works for me. See you then.",
        )
    if request.reason is Reason.OUTSIDE_PREFERRED:
        why = "is outside your preferred hours"
    else:
        why = "clashes with " + ", ".join(request.busy_names)
    lead = f'"{request.subject}" from {request.sender} asks for {asked}, which {why}'
    if request.decision is Decision.PROPOSE_OTHER:
        other = when(request.proposed_day, request.proposed_start, request.proposed_end)
        return DraftOutput(
            notification=f"{lead}. Propose {other} instead?",
            reply=f"Hi {request.sender}, {asked} does not work for me. Could we meet {other} instead?",
        )
    return DraftOutput(
        notification=f"{lead}, and no other slot fits. Send a decline?",
        reply=f"Hi {request.sender}, {asked} does not work for me, and I have no other time free that fits. Sorry.",
    )
