from datetime import date
import http
from jibble_export.models.responses import Timeoffs
from jibble_export.client import AuthorizedJibbleClient


def get_timeoffs(
    from_date: date, to_date: date, person_id: str | None = None
) -> Timeoffs:
    assert from_date <= to_date
    client = AuthorizedJibbleClient()
    conditions = (
        f"(startDate ge {from_date:%Y-%m-%d} and startDate le {to_date:%Y-%m-%d})"
        f"or (endDate ge {from_date:%Y-%m-%d} and endDate le {to_date:%Y-%m-%d})"
    )
    if person_id is not None:
        conditions = f"(({conditions}) and (personId eq {person_id}))"
    else:
        conditions = f"(({conditions}))"
    resp = client.get(
        subdomain="time-tracking",
        relative_path="/v1/TimeOffOverview",
        params={
            "$count": "true",
            "$expand": "person($select=fullName,id),policy($select=name,compensation,kind,id)",
            "$filter": conditions,
            "$orderby": "startDate",
        },
        response_model=Timeoffs,
        status=http.HTTPStatus.OK,
    )
    return resp


if __name__ == "__main__":
    timeoffs = get_timeoffs(
        date(2026, 2, 1),
        date(2026, 2, 28),
        person_id="aaa9e07e-a006-404a-a911-07729ddb1d28",
    )
    print(timeoffs.model_dump_json(indent=2))
