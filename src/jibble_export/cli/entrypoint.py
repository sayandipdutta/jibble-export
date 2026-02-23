import calendar
from datetime import date
import inspect
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter


def get_calendar_month(month_name: str) -> calendar.Month:
    assert len(month_name) >= 3
    for month in calendar.Month:
        if str(month.name)[:3].casefold().startswith(month_name[:3].casefold()):
            return month
    raise ValueError("Unknwon month %s" % month_name)


def export_handler(args: Namespace):
    """
    Export attendance report for given duration.

    If duration is not provided, then report is exported for current month, year.

    Outfile filename is guessed from duration.

    Duration format:
        $ jibble export --duration "2026-02-01:2026-02-28"
        # Report successfully exported to attendance_report_2026-02-01_2026-02-28.xlsx
        $ jibble export --duration feb
        # Report successfully exported to attendance_report_FEBRUARY-2026.xlsx
        $ jibble export --duration feb,2026
        # Report successfully exported to attendance_report_FEBRUARY-2026.xlsx
        $ jibble export --duration 2026
        # Report successfully exported to attendance_report_2026.xlsx

    When date format is used, it has to be in yyyy-mm-dd format.
    """
    from jibble_export.formatter import export_attendance_report
    from jibble_export.features.reports import prepare_attendance_report
    from jibble_export.models.duration import Duration

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

def clockin_handler(args: Namespace):
    from jibble_export.features.clocking import clock_in
    clock_in()

def clockout_handler(args: Namespace):
    from jibble_export.features.clocking import clock_out
    clock_out()


def main():
    parser = ArgumentParser("jibble")
    subparsers = parser.add_subparsers()

    clockin_parser = subparsers.add_parser("clockin")
    clockin_parser.set_defaults(func=clockin_handler)

    clockout_parser = subparsers.add_parser("clockout")
    clockout_parser.set_defaults(func=clockout_handler)

    export_parser = subparsers.add_parser("export", formatter_class=RawTextHelpFormatter)
    export_parser.add_argument("--duration", "-d", help=inspect.getdoc(export_handler))
    export_parser.set_defaults(func=export_handler)


    args = parser.parse_args()
    args.func(args)
