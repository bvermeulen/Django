def get_min(value, _min):
    if value:
        if _min is None:
            _min = float(value)
        elif float(value) < _min:
            _min = float(value)

    return _min

def get_max(value, _max):
    if value:
        if _max is None:
            _max = float(value)
        elif float(value) >= _max:
            _max = float(value)

    return _max
