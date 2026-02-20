from functools import cached_property
from datetime import date, timedelta
import calendar
from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class Month:
    index: calendar.Month = field(default_factory=lambda: date.today().month)
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
