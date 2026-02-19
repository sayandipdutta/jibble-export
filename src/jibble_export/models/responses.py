from datetime import datetime, date
from uuid import UUID
from typing import Annotated, Any, Literal
from datetime import timedelta
from pydantic import BaseModel, Discriminator, Field, Tag, BeforeValidator

EntityType = Literal["Member", "Date"]


class Subject(BaseModel):
    chipColor: str | None
    entityType: EntityType
    id: str
    isDeleted: bool
    name: str


class MemberValue(BaseModel):
    billableAmount: int
    id: UUID
    items: list[TrackedTimeReportValue] | None = None
    subject: Subject
    time: timedelta
    trackedTime: timedelta


def parse_custom_date(v: Any) -> date:
    if isinstance(v, str):
        return datetime.strptime(v, "%d %B %Y").date()
    return v


CustomDate = Annotated[date, BeforeValidator(parse_custom_date)]


class DateValue(BaseModel):
    billableAmount: int
    id: CustomDate
    items: list[TrackedTimeReportValue] | None = None
    subject: Subject
    time: timedelta
    trackedTime: timedelta


class TrackedTimeReport(BaseModel):
    odata_context: str = Field(alias="@odata.context")
    value: list[TrackedTimeReportValue]


def get_entity_type(d: dict) -> EntityType:
    id = d["id"]
    try:
        UUID(str(id))
        return "Member"
    except Exception:
        return "Date"


TrackedTimeReportValue = Annotated[
    Annotated[MemberValue, Tag("Member")] | Annotated[DateValue, Tag("Date")],
    Discriminator(get_entity_type),
]


class Calendars(BaseModel):
    odata_context: str = Field(alias="@odata.context")
    value: list[CalendarEntry]


class CalendarEntry(BaseModel):
    odata_etag: str = Field(alias="@odata.etag")
    name: str
    id: UUID


class HolidayResponse(BaseModel):
    odata_context: str = Field(alias="@odata.context")
    odata_count: int = Field(alias="@odata.count")
    value: list[HolidayEntry]


class HolidayEntry(BaseModel):
    calendarId: UUID
    date: date
    name: str
