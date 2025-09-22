def normalize_occupancy(value):
    try:
        v = float(value)
        if v > 1.0:
            v = v / 100.0
        if v < 0:
            v = 0.0
        if v > 1:
            v = 1.0
        return v
    except Exception:
        return None
