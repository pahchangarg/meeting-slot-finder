"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    FREE_GAPS = "free_gaps"
    SLOT_CONFLICTS = "slot_conflicts"
    DRAFT_REPLY = "draft_reply"


class Task(Enum):
    COMMON_FREE_GAPS = "common-free-gaps"
    SLOT_CONFLICTS = "slot-conflicts"
    EARLIEST_COMMON_SLOT = "earliest-common-slot"
    REPLY_TO_MEETING_REQUEST = "reply-to-meeting-request"


class Day(Enum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"


class Decision(Enum):
    ASK_TO_ACCEPT = "ask_to_accept"
    PROPOSE_OTHER = "propose_other"
    DECLINE = "decline"


class Reason(Enum):
    FITS = "fits"
    OUTSIDE_PREFERRED = "outside_preferred"
    CONFLICT = "conflict"


PEOPLE = "Everyone who must attend, each with their busy times; names are unique"
DAYS = "The days to search, each once"
DAY_START = "When the working day starts, HH:MM"
DAY_END = "When the working day ends, HH:MM, after day_start"


@dataclass
class Busy(Output):
    day: Annotated[Day, "The day"]
    start: Annotated[str, "When it starts, HH:MM, 00:00 to 24:00; 24:00 is the end of the day and may only end a span"]
    end: Annotated[str, "When it ends, after start; the minute it ends is free again"]


@dataclass
class Person(Output):
    name: Annotated[str, "The person's name"]
    busy: Annotated[list[Busy], "Their busy times; they may overlap or touch"]


@dataclass
class Gap(Output):
    day: Annotated[Day, "The day"]
    start: Annotated[str, "When everyone becomes free, HH:MM"]
    end: Annotated[str, "When someone is busy again or the working day ends, HH:MM"]
    minutes: Annotated[int, "The gap's length in minutes"]


@dataclass
class GapsInput(Output):
    people: Annotated[list[Person], PEOPLE]
    days: Annotated[list[Day], DAYS]
    day_start: Annotated[str, DAY_START]
    day_end: Annotated[str, DAY_END]


@dataclass
class GapsOutput(Output):
    gaps: Annotated[list[Gap], "Every stretch inside the working day when nobody is busy, in week order, then by time"]


@dataclass
class Conflict(Output):
    name: Annotated[str, "Who is busy"]
    busy: Annotated[Busy, "The busy time that overlaps the slot"]


@dataclass
class ConflictsInput(Output):
    people: Annotated[list[Person], PEOPLE]
    day: Annotated[Day, "The slot's day"]
    start: Annotated[str, "The slot's start, HH:MM"]
    end: Annotated[str, "The slot's end, HH:MM, after its start"]


@dataclass
class ConflictsOutput(Output):
    conflicts: Annotated[list[Conflict], "Every busy time that overlaps the slot, in the people's order, then theirs"]


@dataclass
class SlotInput(Output):
    people: Annotated[list[Person], PEOPLE]
    days: Annotated[list[Day], DAYS]
    day_start: Annotated[str, DAY_START]
    day_end: Annotated[str, DAY_END]
    duration_minutes: Annotated[int, "How long the meeting is, 1 to 1440 minutes"]


@dataclass
class SlotOutput(Output):
    day: Annotated[Day | None, "The earliest slot's day, or null when no gap is long enough"]
    start: Annotated[str | None, "Its start, HH:MM, or null"]
    end: Annotated[str | None, "Its end, start plus the duration, HH:MM, or null"]


@dataclass
class MeetingRequestInput(Output):
    sender: Annotated[str, "Who asked for the meeting"]
    subject: Annotated[str, "The meeting's subject"]
    day: Annotated[Day, "The requested day"]
    start: Annotated[str, "The requested start, HH:MM"]
    end: Annotated[str, "The requested end, HH:MM, after its start"]
    people: Annotated[list[Person], "Everyone who must attend, you included, each with their busy times; names are unique"]
    days: Annotated[list[Day], "The days you would meet on instead, each once"]
    preferred_start: Annotated[str, "The start of your preferred hours, HH:MM: no meeting is accepted before it"]
    preferred_end: Annotated[str, "The end of your preferred hours, HH:MM: no meeting is accepted after it"]


@dataclass
class DraftInput(Output):
    sender: Annotated[str, "Who asked for the meeting"]
    subject: Annotated[str, "The meeting's subject"]
    day: Annotated[Day, "The requested day"]
    start: Annotated[str, "The requested start, HH:MM"]
    end: Annotated[str, "The requested end, HH:MM"]
    decision: Annotated[Decision, "What to do with the request"]
    reason: Annotated[Reason, "Why: it fits, it is outside your preferred hours, or someone has a conflict"]
    busy_names: Annotated[list[str], "For a conflict, who is busy, in the people's order, each once; else empty"]
    proposed_day: Annotated[Day | None, "For propose_other, the proposed day; else null"]
    proposed_start: Annotated[str | None, "For propose_other, the proposed start, HH:MM; else null"]
    proposed_end: Annotated[str | None, "For propose_other, the proposed end, HH:MM; else null"]


@dataclass
class DraftOutput(Output):
    notification: Annotated[str, "What you are asked before anything is sent: yes sends the reply"]
    reply: Annotated[str, "The reply to send once you say yes"]


@dataclass
class ReplyOutput(Output):
    decision: Annotated[
        Decision,
        "ask_to_accept when the requested slot is inside your preferred hours and nobody is busy; propose_other"
        " with the earliest free slot of the same length in your preferred hours on your days; else decline",
    ]
    reason: Annotated[Reason, "fits; else outside_preferred when outside your preferred hours; else conflict"]
    busy_names: Annotated[list[str], "For a conflict, who is busy during the requested slot, in the people's order; else empty"]
    proposed_day: Annotated[Day | None, "For propose_other, the proposed day; else null"]
    proposed_start: Annotated[str | None, "For propose_other, the proposed start; else null"]
    proposed_end: Annotated[str | None, "For propose_other, the proposed end; else null"]
    notification: Annotated[str, "draft_reply's notification, exactly"]
    reply: Annotated[str, "draft_reply's reply, exactly"]


TOOLS = {
    Tool.FREE_GAPS: (GapsInput, GapsOutput),
    Tool.SLOT_CONFLICTS: (ConflictsInput, ConflictsOutput),
    Tool.DRAFT_REPLY: (DraftInput, DraftOutput),
}
TASKS = {
    Task.COMMON_FREE_GAPS: (GapsInput, GapsOutput),
    Task.SLOT_CONFLICTS: (ConflictsInput, ConflictsOutput),
    Task.EARLIEST_COMMON_SLOT: (SlotInput, SlotOutput),
    Task.REPLY_TO_MEETING_REQUEST: (MeetingRequestInput, ReplyOutput),
}
