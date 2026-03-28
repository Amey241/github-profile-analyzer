"""Helpers for safely coercing mixed API/cache values into numeric types."""

def safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_sum(values, default: int = 0) -> int:
    total = default
    for value in values:
        total += safe_int(value, 0)
    return total
