def nor(*args):
    """NOR gate w/ arbitrary number of inputs"""
    y = False
    for m in args:
        assert(isinstance(m, bool))
        y = y or m
    return not y