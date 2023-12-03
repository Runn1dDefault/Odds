def round_two_after_point(value: float = None):
    if isinstance(value, float):
        return round(value, 2)
    return value
