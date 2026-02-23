import logging
from datetime import date
from jibble_export.formatter import export_attendance_report
import calendar
from uuid import UUID

import pandas as pd

from jibble_export.features.attendance import (
    get_time_attendance,
)
from jibble_export.features.holidays import get_holidays_by_name
from jibble_export.features.timeoffs import get_timeoffs
from jibble_export.models.duration import Duration
from jibble_export.models.responses import (
    DateValue,
    MemberValue,
    Subject,
)


def prepare_attendance_report(
    duration: Duration, holiday_calendar_name: str
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, dict[UUID, str]]:
    attendance_report = get_time_attendance(duration)
    holiday_list = get_holidays_by_name(holiday_calendar_name, duration)
    approved_timeoffs = get_timeoffs(duration, status="Approved")
    person_ids = [value.id for value in attendance_report.value]
    if not person_ids:
        logging.error("No person found! duration=%s, calendar=%s", duration, holiday_calendar_name)
        raise ValueError(f"No person found in the organization during given time period: {duration}!")
    dates_in_month = pd.date_range(
        start=duration.start_date,
        end=duration.end_date,
        freq="D",
    )
    tracked_time_df = pd.DataFrame(
        index=dates_in_month,
        columns=person_ids,
        dtype="timedelta64[us]",
    )
    holidays = pd.Series(
        index=dates_in_month,
        dtype=str,
    )
    timeoffs_df = pd.DataFrame(
        index=dates_in_month,
        columns=person_ids,
        dtype=str,
    )
    id_to_name: dict[UUID, str] = {}
    for value in attendance_report.value:
        match value:
            case MemberValue(
                id=id,
                subject=Subject(name=name),
                items=[*_, DateValue()] as items,
            ):
                id_to_name[id] = name
                tracked_time_df.loc[
                    pd.to_datetime([entry.id for entry in items]), id
                ] = [entry.trackedTime for entry in items]
            case _:
                raise NotImplementedError()

    for value in holiday_list.value:
        holidays[value.date] = value.name

    for value in approved_timeoffs.value:
        timeoff_indices = pd.date_range(value.startDate, value.endDate, freq="D")
        if pd.isna(timeoffs_df.loc[timeoff_indices, value.personId]).all():
            timeoffs_df.loc[timeoff_indices, value.personId] = (
                f"{value.policy.name}"
                if value.duration != 0.5
                else f"0.5 {value.policy.name}"
            )
        else:
            timeoffs_df.loc[timeoff_indices, value.personId] = value.policy.name
    return tracked_time_df, holidays, timeoffs_df, id_to_name


if __name__ == "__main__":
    month = calendar.FEBRUARY
    month_duration = Duration.month(month)
    timetracking, holidays, timeoffs, person_ids = prepare_attendance_report(
        duration=month_duration, holiday_calendar_name="Droplet"
    )
    filename = f"{month.name}-{date.today().year}.xlsx"
    export_attendance_report(timetracking, holidays, timeoffs, person_ids, filename)
