from datetime import date
from typing import cast
from collections.abc import Iterator
from operator import attrgetter
from itertools import groupby, chain
from uuid import UUID
from jibble_export.features.timeoffs import get_timeoffs
from jibble_export.features.attendance import get_time_attendance_for_month
import calendar
from jibble_export.models.duration import Month
import pandas as pd
from jibble_export.models.responses import (
    MemberValue,
    DateValue,
    Subject,
    TimeoffEntries, Holidays,
)


def prepare_attendance_report(month: Month, holiday_calendar_name: str) -> tuple[pd.DataFrame, Holidays, list[tuple[UUID, list[date]]]]:
    attendance_report = get_time_attendance_for_month(month)
    holiday_list = get_holidays_by_name(holiday_calendar_name, month.year)
    approved_timeoffs = get_timeoffs(
        month.start_date, month.end_date, status="Approved"
    )
    holidays_in_period = [
        holiday
        for holiday in holiday_list.value
        if month.start_date <= pd.to_datetime(holiday.date) <= month.end_date
    ]
    attendance_by_members: dict[tuple[UUID, str], dict[str, bool]] = {}
    for value in attendance_report.value:
        match value:
            case MemberValue(
                id=id,
                subject=Subject(name=name),
                items=[*_, DateValue()] as items,
            ):
                attendance_by_members[id, name] = {
                    entry.id: entry.trackedTime for entry in items
                }

            case _:
                raise NotImplementedError()
    df = pd.DataFrame.from_records(attendance_by_members)
    df = df.reindex(
        pd.MultiIndex.from_tuples(df.columns, names=("uuid", "name")), axis="columns"
    ).T
    df = df.set_axis(pd.DatetimeIndex(df.columns), axis="columns").reindex(
        columns=pd.date_range(start=month.start_date, periods=month.periods)
    )
    breakpoint()
    timeoff_indexers: list[tuple[UUID, list[date]]] = []
    personwise_timeoffs = cast(
        Iterator[tuple[UUID, Iterator[TimeoffEntries]]],
        groupby(approved_timeoffs.value, attrgetter("personId")),
    )
    for personId, member_timeoffs in personwise_timeoffs:
        offs = list(
            chain.from_iterable(
                pd.date_range(start=timeoff.startDate, periods=timeoff.duration)
                for timeoff in member_timeoffs
            )
        )
        timeoff_indexers.append((personId, offs))
    return df, holiday_list, timeoff_indexers


if __name__ == "__main__":
    from jibble_export.features.holidays import get_holidays_by_name

    month = Month(calendar.FEBRUARY)
    df, holidays, timeoffs = prepare_attendance_report(month=month, holiday_calendar_name="Droplet")
    # holidays = get_holidays_by_name("Droplet")
    # holiday_list = [pd.to_datetime(value.date) for value in holidays.value]
    # present_mask = df.notnull()
    # new_df = df.mask(present_mask, "P").astype(object)
    # new_df.loc[:, df.columns.weekday >= 5] = "Off"  # ty: ignore[unresolved-attribute]
    # export_with_weekdays(
    #     new_df,
    #     f"{month.name}-{month.year}.xlsx",
    #     holidays=holiday_list,
    # )
