from jibble_export.models.duration import Month
from datetime import date
import http
from jibble_export.client import client
from jibble_export.models.responses import (
    TrackedTimeReport,
)


def get_time_attendance(from_date: date, to_date: date) -> TrackedTimeReport:
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


def get_time_attendance_for_month(month: Month) -> TrackedTimeReport:
    return get_time_attendance(month.start_date, month.end_date)


if __name__ == "__main__":
    month = Month()
    timetrack = get_time_attendance_for_month(month)
    print(timetrack)
