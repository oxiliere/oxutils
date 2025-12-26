# actions.py

ACTION_HIERARCHY = {
    "r": set(),            # read
    "w": {"r"},            # write ⇒ read
    "u": {"r"},            # update ⇒ read
    "d": {"r", "w"},       # delete ⇒ write ⇒ read
    "a": {"r"},            # approve ⇒ read
}


VALID_ACTIONS = list(ACTION_HIERARCHY.keys())


def collapse_actions(actions: list[str]) -> set[str]:
    """
    ['d','w','r'] -> {'d'}
    ['w','r']     -> {'w'}
    ['r']         -> {'r'}
    """
    actions = set(actions)
    roots = set(actions)

    for action, implied in ACTION_HIERARCHY.items():
        if action in roots and implied & actions:
            roots.discard(next(iter(implied & actions)))

    return roots


def expand_actions(actions: list[str]) -> list[str]:
    """
    ['w']        -> ['w', 'r']
    ['d']        -> ['d', 'w', 'r']
    ['a', 'w']   -> ['a', 'w', 'r']
    """
    expanded = set(actions)

    stack = list(actions)
    while stack:
        action = stack.pop()
        implied = ACTION_HIERARCHY.get(action, set())

        for a in implied:
            if a not in expanded:
                expanded.add(a)
                stack.append(a)

    return sorted(expanded)
