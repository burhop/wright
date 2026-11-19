"""One ordered execution loop for standalone and host-provided step handlers."""

from enum import Enum


class Transition(Enum):
    ADVANCE = "advance"
    HOLD = "hold"


async def execute_steps(steps, cursor, dispatch):
    if not 0 <= cursor <= len(steps):
        raise ValueError("The saved cursor is outside this workflow.")
    while cursor < len(steps):
        transition = await dispatch(cursor, steps[cursor])
        if transition is Transition.HOLD:
            break
        if transition is Transition.ADVANCE:
            cursor += 1
        elif type(transition) is int and 0 <= transition < cursor:
            cursor = transition
        else:
            raise ValueError("The handler returned an invalid step transition.")
    return cursor
