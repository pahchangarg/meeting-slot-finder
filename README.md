# Meeting Slot Finder

A `nanoagent.plugin/v0001` plugin, made from the structure of NanoAgent's
reference plugin, [arxiv-source](https://github.com/zeyuyang8/arxiv-source).
It finds the earliest meeting slot that every person can attend, from their
busy times in one week, and answers meeting requests: it accepts only inside
your preferred hours, always asks you first, and otherwise proposes the
earliest time that works.

## Tools

| Tool | Does | Code |
|---|---|---|
| `free_gaps` | Lists every stretch of the working day, on the given days, when nobody is busy, in week order then by time | `src/plugin/gaps.py` |
| `slot_conflicts` | Lists every busy time that overlaps a proposed slot, in the people's order | `src/plugin/conflicts.py` |
| `draft_reply` | Writes the notification you answer and the reply it sends, from fixed templates | `src/plugin/reply.py` |

### Tasks

| Task | Does | Runner |
|---|---|---|
| `common-free-gaps` | Shows when everyone is free | `tool`, with `free_gaps` |
| `slot-conflicts` | Checks who is busy during a proposed slot | `tool`, with `slot_conflicts` |
| `earliest-common-slot` | Finds the earliest slot of a given length that everyone can attend | `agent`, with `free_gaps` and `slot_conflicts` |
| `reply-to-meeting-request` | Decides how to answer a meeting request and drafts the notification and reply | `agent`, with `slot_conflicts`, `free_gaps` and `draft_reply` |

The rules:

- Times are `HH:MM` on a day of the week (`mon` to `sun`). `24:00` is the end
  of a day and may only end a span.
- Busy times and slots are half-open: a meeting from 09:00 to 10:00 leaves
  10:00 free, so meetings that touch do not conflict.
- A slot must lie inside the working day (`day_start` to `day_end`) of a
  single requested day. The earliest slot is the first one in week order, then
  by time. When no gap is long enough, the task submits all nulls.
- A meeting request is answered `ask_to_accept` only when it lies inside your
  preferred hours and nobody is busy. Nothing is sent without your yes: the
  output is a notification asking you, and the reply it would send. Otherwise
  the reason is `outside_preferred` (checked first) or `conflict`, and it
  proposes the earliest free slot of the same length inside your preferred
  hours on your days, or declines when none is long enough.

## Layout

```text
.
├── nanoagent.yaml   # manifest (a slimconfig ManifestConfig): id, runtime, permissions, tools, tasks
├── contract.py      # each tool's and task's typed input and output: slimconfig Output classes
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env             # environment variable NAMEs this plugin needs (none)
├── src/plugin/      # the MCP server: __main__.py, its IMPLEMENTATIONS, and one module per tool
├── tests/           # the tools' tests and the verifier's
├── ui/              # outputs are drawn from their JSON Schema
├── product/         # the product page a catalog shows: product.yaml and icon.svg
└── verifier/        # deterministic verifier package
```

The tools merge busy intervals. `verifier/` checks them another way: it marks
every busy minute of each day and scans the working day minute by minute, so a
merging mistake in the tools shows up as a mismatch. For
`earliest-common-slot` it checks that the slot has the right length, lies in
the working day of a requested day, shares no minute with anyone's busy time,
and that no earlier slot fits, and that a request with no fitting gap submits
all nulls. For `reply-to-meeting-request` it works out the decision, reason,
busy names and proposal itself, and rebuilds the notification and reply word
for word from its own copy of the templates (`verifier/wording.py`).

## Develop and run

```bash
uv sync --extra dev
uv run pytest
```

The plugin needs no network and no environment variables.
