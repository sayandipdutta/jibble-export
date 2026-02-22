import calendar
import http
import logging
from datetime import date

from jibble_export.client import client
from jibble_export.models.duration import Duration
from jibble_export.models.responses import Calendars, Holidays


def get_calendars() -> Calendars:
    resp = client.get(
        subdomain="workspace",
        relative_path="/v1/Calendars",
        params={"$select": "id,name"},
        response_model=Calendars,
        status=http.HTTPStatus.OK,
    )
    return resp


def get_holidays_for_year(
    calendar_id: str,
    year: int,
) -> Holidays:
    query = f"(year(Date) eq {year} and calendarId eq {calendar_id})"
    resp = client.get(
        subdomain="workspace",
        relative_path="/v1/CalendarDays",
        params={"$filter": query, "$count": "true"},
        response_model=Holidays,
        status=http.HTTPStatus.OK,
    )
    return resp


def get_holidays(
    calendar_id: str,
    duration: calendar.Month | Duration,
) -> Holidays:
    query = f"(calendarId eq {calendar_id})"
    if isinstance(duration, Duration):
        query = f"({query} and (Date ge {duration.start_date:%Y-%m-%d} and Date le {duration.end_date:%Y-%m-%d}))"
    else:
        query = f"({query} and month(Date) eq {duration.value} and year(Date) eq {date.today().year})"
    resp = client.get(
        subdomain="workspace",
        relative_path="/v1/CalendarDays",
        params={"$filter": query, "$count": "true"},
        response_model=Holidays,
        status=http.HTTPStatus.OK,
    )
    return resp


def get_holidays_by_name(
    calendar_name: str,
    duration: Duration,
) -> Holidays:
    calendars = get_calendars()
    try:
        calendar_id = next(
            str(calendar.id)
            for calendar in calendars.value
            if calendar.name == calendar_name
        )
    except StopIteration:
        logging.error("Could not find calendar name: %s" % calendar_name)
        raise NameError(f"Calendar name {calendar_name} not found")
    return get_holidays(calendar_id, duration)


if __name__ == "__main__":
    holidays = get_holidays_by_name(
        "Droplet",
        duration=Duration.month(calendar.OCTOBER),
    )
    print(holidays)
