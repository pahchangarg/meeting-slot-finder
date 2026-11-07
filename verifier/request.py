"""The reply-to-meeting-request task: accept only inside your preferred hours with nobody busy, and only after
asking you; otherwise propose the earliest free slot of the same length in your preferred hours, or decline."""

from contract import Decision, Reason

from .checks import (
    clock,
    days_problem,
    expected_gaps,
    first_problem,
    people_problem,
    result,
    span_problem,
    to_minutes,
)
from .wording import render


def request_problem(arguments):
    if not arguments.sender.strip() or not arguments.subject.strip():
        return "sender and subject must not be blank"
    return first_problem(
        people_problem(arguments.people),
        days_problem(arguments.days),
        span_problem("the requested slot", arguments.start, arguments.end),
        span_problem("your preferred hours", arguments.preferred_start, arguments.preferred_end),
    )


def expected(arguments):
    """(decision, reason, busy names, proposed (day, start, end) or None)."""
    start, end = to_minutes(arguments.start), to_minutes(arguments.end, end=True)
    asked = set(range(start, end))
    busy = [
        person.name
        for person in arguments.people
        if any(
            busy.day is arguments.day and asked & set(range(to_minutes(busy.start), to_minutes(busy.end, end=True)))
            for busy in person.busy
        )
    ]
    inside = to_minutes(arguments.preferred_start) <= start and end <= to_minutes(arguments.preferred_end, end=True)
    if inside and not busy:
        return Decision.ASK_TO_ACCEPT, Reason.FITS, [], None
    reason, names = (Reason.CONFLICT, busy) if inside else (Reason.OUTSIDE_PREFERRED, [])
    gaps = expected_gaps(arguments.people, arguments.days, arguments.preferred_start, arguments.preferred_end)
    for day, first, last in gaps:
        if last - first >= end - start:
            return Decision.PROPOSE_OTHER, reason, names, (day, clock(first), clock(first + end - start))
    return Decision.DECLINE, reason, names, None


def verify_task(arguments, output, reference, workspace):
    problem = request_problem(arguments)
    if problem:
        return result(False, f"the request is not valid: {problem}")
    decision, reason, names, proposed = expected(arguments)
    if output.decision is not decision:
        return result(False, f"the decision should be {decision.value}, not {output.decision.value}", expected=decision)
    if output.reason is not reason:
        return result(False, f"the reason should be {reason.value}, not {output.reason.value}", expected=reason)
    if output.busy_names != names:
        return result(False, f"busy_names should be {names}", expected=names)
    got = (output.proposed_day, output.proposed_start, output.proposed_end)
    if got != (proposed or (None, None, None)):
        shown = f"{proposed[0].value} {proposed[1]}-{proposed[2]}" if proposed else "nothing"
        return result(False, f"the proposal should be {shown}", expected=shown)
    notification, reply = render(
        arguments.sender, arguments.subject, (arguments.day, arguments.start, arguments.end), decision, reason, names, proposed
    )
    if output.notification != notification:
        return result(False, "the notification differs from the template", expected=notification)
    if output.reply != reply:
        return result(False, "the reply differs from the template", expected=reply)
    return result(True, f"{decision.value} ({reason.value}), held until you say yes", decision=decision)
