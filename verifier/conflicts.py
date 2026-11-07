from .checks import first_problem, people_problem, result, span_problem, to_minutes


def verify_input(value):
    problem = first_problem(people_problem(value.people), span_problem("the slot", value.start, value.end))
    return result(False, problem) if problem else result(True, "input is valid")


def verify_output(input_value, output_value, workspace):
    slot = set(range(to_minutes(input_value.start), to_minutes(input_value.end, end=True)))
    want = [
        (person.name, busy.day, busy.start, busy.end)
        for person in input_value.people
        for busy in person.busy
        if busy.day is input_value.day and slot & set(range(to_minutes(busy.start), to_minutes(busy.end, end=True)))
    ]
    got = [(c.name, c.busy.day, c.busy.start, c.busy.end) for c in output_value.conflicts]
    if got != want:
        return result(False, "the conflicts differ from the busy times sharing a minute with the slot", expected=want)
    return result(True, f"{len(want)} conflicts", conflicts=len(want))
