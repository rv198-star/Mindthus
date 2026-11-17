def normalize_record(value):
    if not isinstance(value, dict):
        raise ValueError("expected a dict")
    fields = ("id", "label", "enabled", "weight")
    if any(not value.get(key) for key in fields):
        raise ValueError("missing field")
    return {key: value[key] for key in fields}
