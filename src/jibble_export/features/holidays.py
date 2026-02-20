from datetime import date
import logging
from jibble_export.models.responses import Calendars, Holidays
import http
from jibble_export.client import client


def get_calendars() -> Calendars:
    resp = client.get(
        subdomain="workspace",
        relative_path="/v1/Calendars",
        params={"$select": "id,name"},
        response_model=Calendars,
        status=http.HTTPStatus.OK,
    )
    return resp


def get_holidays(calendar_id: str, year: int | None = None) -> Holidays:
    year = year if year is not None else date.today().year
    query = f"(year(Date) eq {year} and calendarId eq {calendar_id})"
    resp = client.get(
        subdomain="workspace",
        relative_path="/v1/CalendarDays",
        params={"$filter": query, "$count": "true"},
        response_model=Holidays,
        status=http.HTTPStatus.OK,
    )
    return resp


def get_holidays_by_name(calendar_name: str, year: int | None = None) -> Holidays:
    year = year if year is not None else date.today().year
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
    return get_holidays(calendar_id, year)


if __name__ == "__main__":
    holidays = get_holidays_by_name("Droplet")
    print(holidays)
