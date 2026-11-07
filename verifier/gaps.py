from .checks import clock, days_problem, expected_gaps, first_problem, people_problem, result, span_problem


def request_problem(value):
    return first_problem(
        people_problem(value.people),
        days_problem(value.days),
        span_problem("the working day", value.day_start, value.day_end),
    )


def verify_input(value):
    problem = request_problem(value)
    return result(False, problem) if problem else result(True, "input is valid")


def verify_output(input_value, output_value, workspace):
    want = [
        (day, clock(start), clock(end), end - start)
        for day, start, end in expected_gaps(input_value.people, input_value.days, input_value.day_start, input_value.day_end)
    ]
    got = [(gap.day, gap.start, gap.end, gap.minutes) for gap in output_value.gaps]
    if got != want:
        return result(
            False,
            "the gaps differ from the free minutes of the working day",
            expected=[f"{day.value} {start}-{end}" for day, start, end, _ in want],
        )
    return result(True, f"{len(want)} free gaps", gaps=len(want))
