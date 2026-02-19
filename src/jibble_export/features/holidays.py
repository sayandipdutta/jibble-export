from datetime import date
from jibble_export.models.responses import Calendars, HolidayResponse
import http
from jibble_export.client import AuthorizedJibbleClient


def get_calendars():
    client = AuthorizedJibbleClient()
    resp = client.get(
        subdomain="workspace",
        relative_path="/v1/Calendars",
        params={"$select": "id,name"},
        response_model=Calendars,
        status=http.HTTPStatus.OK,
    )
    return resp


def get_holidates(year: int, calendar_id: str):
    query = f"(year(Date) eq {year} and calendarId eq {calendar_id})"
    client = AuthorizedJibbleClient()
    resp = client.get(
        subdomain="workspace",
        relative_path="/v1/CalendarDays",
        params={"$filter": query, "$count": "true"},
        response_model=HolidayResponse,
        status=http.HTTPStatus.OK,
    )
    return resp


if __name__ == "__main__":
    calendars = get_calendars()
    calendar_id = next(str(calendar.id) for calendar in calendars.value)
    print(calendars)
    holidays = get_holidates(date.today().year, calendar_id)
    print(holidays)
