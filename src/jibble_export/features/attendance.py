from jibble_export.models.duration import Duration
import http
from jibble_export.client import client
from jibble_export.models.responses import (
    TrackedTimeReport,
)


def get_time_attendance(duration: Duration) -> TrackedTimeReport:
    from_date, to_date = duration.start_date, duration.end_date
    assert to_date >= from_date, "to_date cannot be older than from_date"
    resp = client.get(
        subdomain="time-attendance",
        relative_path="/v1/TrackedTimeReport",
        params={
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d"),
            "groupBy": "Member",
            "subGroupBy": "Date",
            "$expand": "Subject,Items($expand=Subject)",
        },
        response_model=TrackedTimeReport,
        status=http.HTTPStatus.OK,
    )
    return resp


if __name__ == "__main__":
    month = Duration.current_month()
    timetrack = get_time_attendance(month)
    print(timetrack)
