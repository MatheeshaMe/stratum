"""§27 — mandatory correctness checks. Any violation FAILS the simulation.

These four assertions would have caught C9, C10, C11 and C12. They are imported
by every simulation in this phase and are not optional.
"""
class InvariantViolation(AssertionError): pass

def check_trade(side, entry, stop, target=None):
    if side > 0:
        if not stop < entry:  raise InvariantViolation(f"LONG stop {stop} not < entry {entry}")
        if target is not None and not target > entry:
            raise InvariantViolation(f"LONG target {target} not > entry {entry}")
    elif side < 0:
        if not stop > entry:  raise InvariantViolation(f"SHORT stop {stop} not > entry {entry}")
        if target is not None and not target < entry:
            raise InvariantViolation(f"SHORT target {target} not < entry {entry}")
    else:
        raise InvariantViolation("side must be +1 or -1")
    if abs(entry - stop) <= 0: raise InvariantViolation("risk must be > 0")

def check_trail(side, old_stop, new_stop, bar_low, bar_high):
    """A trailing stop may only move toward profit, and may never be placed at a
    level the current bar has already traded through (C12)."""
    if side > 0:
        if new_stop < old_stop: raise InvariantViolation("LONG trail moved away from profit")
        if new_stop >= bar_low: raise InvariantViolation("LONG trail placed at a level already traded")
    else:
        if new_stop > old_stop: raise InvariantViolation("SHORT trail moved away from profit")
        if new_stop <= bar_high: raise InvariantViolation("SHORT trail placed at a level already traded")

def check_causal(feature_bar, data_bar):
    if data_bar > feature_bar:
        raise InvariantViolation(f"feature at {feature_bar} read data from {data_bar}")
