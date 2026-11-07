from contract import Decision, Reason

from .checks import result, span_problem
from .wording import render


def draft_problem(value):
    if not value.sender.strip() or not value.subject.strip():
        return "sender and subject must not be blank"
    problem = span_problem("the requested slot", value.start, value.end)
    if problem:
        return problem
    if (value.decision is Decision.ASK_TO_ACCEPT) != (value.reason is Reason.FITS):
        return "ask_to_accept goes with reason fits, and only with it"
    if bool(value.busy_names) != (value.reason is Reason.CONFLICT):
        return "busy_names must name who is busy for a conflict, and be empty otherwise"
    proposed = (value.proposed_day, value.proposed_start, value.proposed_end)
    if value.decision is Decision.PROPOSE_OTHER:
        if None in proposed:
            return "propose_other needs proposed_day, proposed_start and proposed_end"
        return span_problem("the proposed slot", value.proposed_start, value.proposed_end)
    if proposed != (None, None, None):
        return "only propose_other proposes a slot"
    return None


def verify_input(value):
    problem = draft_problem(value)
    return result(False, problem) if problem else result(True, "input is valid")


def verify_output(input_value, output_value, workspace):
    proposed = None
    if input_value.decision is Decision.PROPOSE_OTHER:
        proposed = (input_value.proposed_day, input_value.proposed_start, input_value.proposed_end)
    want = render(
        input_value.sender,
        input_value.subject,
        (input_value.day, input_value.start, input_value.end),
        input_value.decision,
        input_value.reason,
        input_value.busy_names,
        proposed,
    )
    if (output_value.notification, output_value.reply) != want:
        return result(False, "the draft differs from the template", expected=list(want))
    return result(True, "the draft follows the template")
