from typing import Self
from functools import cached_property
from datetime import date, timedelta
import calendar
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Duration:
    start_date: date
    end_date: date

    @cached_property
    def periods(self) -> int:
        return (self.end_date - self.start_date).days

    @classmethod
    def current_month(cls) -> Self:
        today = date.today()
        return cls.month(month=calendar.Month(today.month), year=today.year)

    @classmethod
    def month(cls, month: calendar.Month, year: int | None = None) -> Self:
        year = year if year is not None else date.today().year
        first_day_of_month = pd.to_datetime(date(year=year, month=month, day=1))
        last_day_of_month = first_day_of_month + timedelta(
            days=first_day_of_month.days_in_month - 1
        )
        return cls(first_day_of_month, last_day_of_month)

    @classmethod
    def current_year(cls) -> Self:
        today = date.today()
        return cls(today.replace(month=1, day=1), today.replace(month=12, day=31))

    @classmethod
    def year(cls, year: int) -> Self:
        return cls(date(year, 1, 1), date(year, 12, 31))

    def __str__(self):
        return f"{type(self).__name__}(start_date={self.start_date:%Y-%m-%d}, end_date={self.end_date:%Y-%m-%d})"
