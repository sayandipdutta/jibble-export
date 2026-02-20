from jibble_export.features.holidays import get_holidays_by_name
from jibble_export.formatter import export_with_weekdays
from functools import cached_property
import calendar
from dataclasses import dataclass, field
import pandas as pd
from datetime import date, timedelta
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
    def start_date(self) -> pd.Timestamp:
        month = int(self.index)
        first_day_of_month = pd.to_datetime(date(year=self.year, month=month, day=1))
        return first_day_of_month

    @cached_property
    def periods(self) -> int:
        return self.start_date.days_in_month

    @cached_property
    def end_date(self) -> pd.Timestamp:
        return self.start_date + timedelta(days=self.periods - 1)

    @cached_property
    def name(self):
        return calendar.month_name[self.index]


@dataclass(frozen=True)
class Duration:
    start_date: date
    end_date: date


def get_time_attendance_report(from_date: date, to_date: date) -> TrackedTimeReport:
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


def get_time_attendance_report_for_month(month: Month) -> TrackedTimeReport:
    return get_time_attendance_report(month.start_date, month.end_date)


def prepare_attendance_report(
    duration: Month | Duration,
    attendance_report: TrackedTimeReport | None = None,
) -> pd.DataFrame:
    if attendance_report is None:
        attendance_report = get_time_attendance_report_for_month(month)
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
    new_columns = pd.date_range(start=month.start_date, periods=month.periods)
    all_days_report = df.reindex(columns=new_columns)
    return all_days_report


if __name__ == "__main__":
    month = Month(10)
    df = prepare_attendance_report(duration=month)
    holidays = get_holidays_by_name("Droplet")
    holiday_list = [pd.to_datetime(value.date) for value in holidays.value]
    present_mask = df.notnull()
    new_df = df.mask(present_mask, "P").astype(object)
    new_df.loc[:, df.columns.weekday >= 5] = "Off"  # ty: ignore[unresolved-attribute]
    export_with_weekdays(
        new_df,
        f"{month.name}-{month.year}.xlsx",
        holidays=holiday_list,
    )
