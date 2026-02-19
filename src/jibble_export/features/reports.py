from jibble_export.features.holidays import get_holidates, get_calendars
from jibble_export.formatter import export_with_weekdays
from functools import cached_property
import calendar
from dataclasses import dataclass, field
import pandas as pd
from datetime import date, datetime
import http
from jibble_export.client import AuthorizedJibbleClient
from jibble_export.models.responses import (
    TrackedTimeReport,
    MemberValue,
    DateValue,
)


@dataclass(frozen=True)
class Month:
    index: int | calendar.Month = field(default_factory=lambda: date.today().month)
    year: int = field(default_factory=lambda: date.today().year)

    @cached_property
    def first_date(self) -> pd.Timestamp:
        month = int(self.index)
        first_day_of_month = pd.to_datetime(date(year=self.year, month=month, day=1))
        return first_day_of_month

    @cached_property
    def periods(self) -> int:
        month = int(self.index)
        first_day_of_month = pd.to_datetime(date(year=self.year, month=month, day=1))
        return first_day_of_month.days_in_month

    @cached_property
    def name(self):
        return calendar.month_name[self.index]


class Week:
    index: int
    year: int = field(default_factory=lambda: date.today().year)

    @cached_property
    def first_date(self) -> pd.Timestamp:
        date_str = datetime.strptime(f"{self.year}-{self.index}-1", "%Y-%W-%w").date()
        return pd.to_datetime(date_str)

    @cached_property
    def periods(self) -> int:
        # FIX: what happens for first partial week?
        days = 366 if self.first_date.is_leap_year else 365
        this_day = self.first_date.day_of_year
        return min(7, days - this_day)


type Duration = Week | Month


def get_time_attendance_report(
    from_date: date | None = None, to_date: date | None = None
):
    if from_date is None:
        from_date = date.today().replace(day=1)
    if to_date is None:
        last_day = calendar.monthrange(from_date.year, from_date.month)[1]
        to_date = from_date.replace(day=last_day)
    assert to_date >= from_date, "to_date cannot be older than from_date"
    client = AuthorizedJibbleClient()
    resp = client.get(
        subdomain="time-attendance",
        relative_path="/v1/TrackedTimeReport",
        params={
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d"),
            "groupBy": "Date",
            "subGroupBy": "Member",
            "$expand": "Subject,Items($expand=Subject)",
        },
        response_model=TrackedTimeReport,
        status=http.HTTPStatus.OK,
    )
    return resp


def prepare_attendance_report(
    attendance_report: TrackedTimeReport, duration: Duration
) -> pd.DataFrame:
    attendance_by_members: dict[str, dict[str, bool]] = {}
    for value in attendance_report.value:
        match value:
            case DateValue(
                id=dt,
                items=[*_, MemberValue()] as items,
            ):
                attendance_by_members[dt] = {
                    entry.subject.name: entry.trackedTime for entry in items
                }

            case _:
                raise NotImplementedError()
    df = pd.DataFrame.from_records(attendance_by_members)
    columns = pd.DatetimeIndex(df.columns)
    df.set_axis(columns, axis="columns")
    new_columns = pd.date_range(start=duration.first_date, periods=duration.periods)
    all_days_report = df.reindex(columns=new_columns)
    return all_days_report


if __name__ == "__main__":
    resp = get_time_attendance_report()
    month = Month(10)
    df = prepare_attendance_report(resp, duration=month)
    calendars = get_calendars()
    calendar_id = next(str(calendar.id) for calendar in calendars.value)
    holidays = get_holidates(2026, calendar_id)
    holiday_list = [pd.to_datetime(value.date) for value in holidays.value]
    present_mask = df.notnull()
    new_df = df.mask(present_mask, "P").astype(object)
    new_df.loc[:, df.columns.weekday >= 5] = "Off"  # ty: ignore[unresolved-attribute]
    export_with_weekdays(
        new_df,
        f"{month.name}-{month.year}.xlsx",
        holidays=holiday_list,
    )
