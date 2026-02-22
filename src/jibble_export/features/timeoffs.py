from jibble_export.models.duration import Duration
from typing import Literal
from uuid import UUID
import http
from jibble_export.models.responses import Timeoffs
from jibble_export.client import client


def get_timeoffs(
    duration: Duration,
    person_id: UUID | None = None,
    status: Literal["Approved", "Rejected", "Pending", "Cancelled"] | None = None,
) -> Timeoffs:
    from_date, to_date = duration.start_date, duration.end_date
    conditions = (
        f"((startDate ge {from_date:%Y-%m-%d} and startDate le {to_date:%Y-%m-%d})"
        f"or (endDate ge {from_date:%Y-%m-%d} and endDate le {to_date:%Y-%m-%d}))"
    )
    if person_id is not None:
        conditions += f" and (personId eq {person_id})"
    if status is not None:
        conditions += f" and (status eq '{status}')"
    resp = client.get(
        subdomain="time-tracking",
        relative_path="/v1/TimeOffOverview",
        params={
            "$count": "true",
            "$expand": "person($select=fullName,id),policy($select=name,compensation,kind,id)",
            "$filter": f"({conditions})",
            "$orderby": "startDate",
            "$select": "id,personId,kind,startDate,endDate,status,note,duration,person,policy",
        },
        response_model=Timeoffs,
        status=http.HTTPStatus.OK,
    )
    return resp


if __name__ == "__main__":
    timeoffs = get_timeoffs(
        Duration.current_month(),
        person_id=UUID("aaa9e07e-a006-404a-a911-07729ddb1d28"),
        status="Approved",
    )
    print(timeoffs.model_dump_json(indent=2))
