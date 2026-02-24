from datetime import date


def date_json_encoder(obj):
    if isinstance(obj, date):
        return f"{obj:%Y-%m-%d}"
    raise TypeError(f"Cannot serialize object of {type(obj)}")
