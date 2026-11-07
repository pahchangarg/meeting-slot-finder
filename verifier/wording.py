"""The notification and reply text, rebuilt word for word from the decision."""

from contract import Decision, Reason


def when(day, start, end):
    return f"{day.value.capitalize()} {start}-{end}"


def render(sender, subject, asked, decision, reason, busy_names, proposed):
    """(notification, reply); ``asked`` and ``proposed`` are (day, start, end), ``proposed`` None unless proposing."""
    asked_text = when(*asked)
    if decision is Decision.ASK_TO_ACCEPT:
        return (
            f'Accept "{subject}" from {sender} on {asked_text}? Everyone is free and it is inside your preferred hours.',
            f"Hi {sender}, {asked_text} works for me. See you then.",
        )
    why = "is outside your preferred hours" if reason is Reason.OUTSIDE_PREFERRED else "clashes with " + ", ".join(busy_names)
    lead = f'"{subject}" from {sender} asks for {asked_text}, which {why}'
    if decision is Decision.PROPOSE_OTHER:
        other = when(*proposed)
        return (
            f"{lead}. Propose {other} instead?",
            f"Hi {sender}, {asked_text} does not work for me. Could we meet {other} instead?",
        )
    return (
        f"{lead}, and no other slot fits. Send a decline?",
        f"Hi {sender}, {asked_text} does not work for me, and I have no other time free that fits. Sorry.",
    )
