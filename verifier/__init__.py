"""The deterministic verifier: each tool's checks live in its own module, on contract instances."""

from contract import Task, Tool

from . import conflicts, draft, gaps, request, slot

TOOLS = {Tool.FREE_GAPS: gaps, Tool.SLOT_CONFLICTS: conflicts, Tool.DRAFT_REPLY: draft}


def _tool_output(module):
    """A tool task's check: its output judged as its one tool's verify_output judges it."""
    return lambda arguments, output, reference, workspace: module.verify_output(arguments, output, workspace)


# task -> its output's check, verify_task(arguments, output, reference, workspace)
TASKS = {
    Task.COMMON_FREE_GAPS: _tool_output(gaps),
    Task.SLOT_CONFLICTS: _tool_output(conflicts),
    Task.EARLIEST_COMMON_SLOT: slot.verify_task,
    Task.REPLY_TO_MEETING_REQUEST: request.verify_task,
}


def verify_input(tool, value):
    return TOOLS[Tool(tool)].verify_input(value)


def verify_output(tool, input_value, output_value, workspace):
    return TOOLS[Tool(tool)].verify_output(input_value, output_value, workspace)


def verify_task(task, arguments, output, reference, workspace):
    return TASKS[Task(task)](arguments, output, reference, workspace)
