"""Pure validation for host-normalizer-v1; preserves original field values."""


def normalize_record(value):
    if not isinstance(value, dict):
        raise ValueError("expected a dict")
    fields = ("id", "label", "enabled", "weight")
    if set(value) != set(fields):
        raise ValueError("expected exactly id, label, enabled, weight")

    identifier = value["id"]
    label = value["label"]
    enabled = value["enabled"]
    weight = value["weight"]
    if not isinstance(identifier, str) or not str.strip(identifier):
        raise ValueError("id must be a nonblank string")
    if not isinstance(label, str) or not str.strip(label):
        raise ValueError("label must be a nonblank string")
    if type(enabled) is not bool:
        raise ValueError("enabled must be an exact bool")
    if type(weight) is not int or not 0 <= weight <= 100:
        raise ValueError("weight must be an exact int in [0, 100]")
    return {"id": identifier, "label": label, "enabled": enabled, "weight": weight}
