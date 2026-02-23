from jibble_export.formatter import export_attendance_report
from jibble_export.features.reports import prepare_attendance_report
import calendar
from datetime import date
from jibble_export.models.duration import Duration
import inspect
from jibble_export.features.clocking import clock_in, clock_out
from argparse import ArgumentParser, Namespace


def get_calendar_month(month_name: str) -> calendar.Month:
    assert len(month_name) >= 3
    for month in calendar.Month:
        if str(month.name)[:3].casefold().startswith(month_name[:3].casefold()):
            return month
    raise ValueError("Unknwon month %s" % month_name)


def export_handler(args: Namespace):
    """
    Export attendance report for given duration.

    Duration format:
        $ jibble export --duration "2026-02-01:2026-02-28"
        $ jibble export --duration feb
        $ jibble export --duration feb,2026
        $ jibble export --duration 2026

    When date format is used, it has to be in yyyy-mm-dd format.

    If duration is not provided, then report is exported for current month, year.
    """
    outfile_prefix = "attendance_report_"
    filename = outfile_prefix.removesuffix('_') + ".xlsx"
    if args.duration is None:
        duration = Duration.current_month()
        today = date.today()
        filename = f"{outfile_prefix}{calendar.Month(today.month).name}-{today.year}.xlsx"
    elif isinstance(args.duration, str):
        try:
            start, end = args.duration.split(":", maxsplit=1)
            duration = Duration(date.strptime(start, "%Y-%m-%d"), date.strptime(end, "%Y-%m-%d"))
            filename = f"{outfile_prefix}{args.duration.replace(':', '_')}.xlsx"
        except ValueError:
            try:
                month_name, year = args.duration.split(',', maxsplit=1)
                calendar_month = get_calendar_month(month_name)
                duration = Duration.month(calendar_month, int(year))
                filename = f"{outfile_prefix}{calendar_month.name}-{int(year)}.xlsx"
            except ValueError:
                if args.duration.isnumeric():
                    duration = Duration.year(int(args.duration))
                    filename = f"{outfile_prefix}{args.duration}.xlsx"
                else:
                    calendar_month = get_calendar_month(args.duration)
                    duration = Duration.month(calendar_month)
                    filename = f"{outfile_prefix}{calendar_month.name}-{date.today().year}.xlsx"
    timetracking, holidays, timeoffs, person_ids = prepare_attendance_report(
        duration=duration, holiday_calendar_name="Droplet"
    )
    export_attendance_report(timetracking, holidays, timeoffs, person_ids, filename)


def main():
    parser = ArgumentParser("jibble")
    subparsers = parser.add_subparsers()

    clockin_parser = subparsers.add_parser("clockin")
    clockin_parser.set_defaults(func=lambda args: clock_in())

    clockout_parser = subparsers.add_parser("clockout")
    clockout_parser.set_defaults(func=lambda args: clock_out())

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--duration", "-d", help=inspect.getdoc(export_handler))
    export_parser.set_defaults(func=export_handler)


    args = parser.parse_args()
    args.func(args)
