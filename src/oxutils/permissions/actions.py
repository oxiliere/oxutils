# actions.py

READ = "r"
WRITE = "w"
DELETE = "d"
UPDATE = "u"
APPROVE = "a"

ACTIONS = [READ, WRITE, DELETE, UPDATE, APPROVE]


ACTION_HIERARCHY = {
    "r": set(),            # read
    "w": {"r"},            # write ⇒ read
    "u": {"r"},            # update ⇒ read
    "d": {"r", "w"},       # delete ⇒ write ⇒ read
    "a": {"r"},            # approve ⇒ read
}


def collapse_actions(actions: list[str]) -> set[str]:
    """
    ['d','w','r'] -> {'d'}
    ['w','r']     -> {'w'}
    ['r']         -> {'r'}
    """
    actions = set(actions)
    roots = set(actions)

    # Remove all implied actions from roots
    for action in list(roots):
        if action in ACTION_HIERARCHY:
            implied = ACTION_HIERARCHY[action]
            roots -= implied

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
