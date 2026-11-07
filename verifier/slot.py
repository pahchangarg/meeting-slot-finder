"""The earliest-common-slot task: the first gap long enough for the meeting, in week order."""

from .checks import busy_minutes, clock, expected_gaps, result, to_minutes
from .gaps import request_problem


def verify_task(arguments, output, reference, workspace):
    problem = request_problem(arguments)
    if not problem and not 1 <= arguments.duration_minutes <= 1440:
        problem = "duration_minutes must be 1 to 1440"
    if problem:
        return result(False, f"the request is not valid: {problem}")
    length = arguments.duration_minutes
    gaps = expected_gaps(arguments.people, arguments.days, arguments.day_start, arguments.day_end)
    fits = [(day, start) for day, start, end in gaps if end - start >= length]
    fields = (output.day, output.start, output.end)
    if not fits:
        if fields != (None, None, None):
            return result(False, "no gap is long enough, so every field must be null")
        return result(True, "no gap is long enough, and the output says so")
    if None in fields:
        return result(False, "a gap is long enough, so no field may be null")
    start, end = to_minutes(output.start), to_minutes(output.end, end=True)
    if start is None or end is None or end - start != length:
        return result(False, f"the slot {output.start}-{output.end} is not {length} minutes long")
    if output.day not in arguments.days:
        return result(False, f"{output.day.value} is not one of the requested days")
    open_at, close_at = to_minutes(arguments.day_start), to_minutes(arguments.day_end, end=True)
    if start < open_at or end > close_at:
        return result(False, "the slot is outside the working day")
    if any(busy_minutes(arguments.people, output.day)[start:end]):
        return result(False, f"someone is busy during {output.day.value} {output.start}-{output.end}")
    day, first = fits[0]
    if (output.day, start) != (day, first):
        return result(False, f"{day.value} {clock(first)} is earlier and free", expected=f"{day.value} {clock(first)}")
    return result(True, f"{day.value} {clock(first)}-{clock(first + length)} is the earliest common slot")
