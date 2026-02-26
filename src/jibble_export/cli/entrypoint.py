from pathlib import Path
import logging
from jibble_export.utils import date_json_encoder
import json
from jibble_export.settings import setting
import calendar
from datetime import date
import inspect
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter

import pandas as pd


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

      Special values:
      If LAST_ONE_MONTH report is exported on 24th Feb, 2026
        $ jibble export --duration LAST_ONE_MONTH
        # Report successfully exported to attendance_report_2026-01-25_2026-02-24.xlsx
      If LAST_MONTH report is exported in Feb, 2026
        $ jibble export --duration LAST_MONTH
        # Report successfully exported to attendance_report_JANUARY-2026.xlsx

    When date format is used, it has to be in yyyy-mm-dd format.
    """
    from jibble_export.formatter import export_attendance_report
    from jibble_export.features.reports import prepare_attendance_report
    from jibble_export.models.duration import Duration

    outfile_prefix = "attendance_report_"
    filename = outfile_prefix.removesuffix("_") + ".xlsx"
    match args.duration:
        case None:
            duration = Duration.current_month()
            today = date.today()
            filename = (
                f"{outfile_prefix}{calendar.Month(today.month).name}-{today.year}.xlsx"
            )
        case "LAST_ONE_MONTH":
            today = pd.Timestamp.today()
            end_date = (today - pd.DateOffset(days=1)).to_pydatetime().date()
            start_date = (today - pd.DateOffset(months=1)).to_pydatetime().date()
            duration = Duration(start_date, end_date)
            filename = f"{outfile_prefix}{start_date:%Y-%m-%d}_{end_date:%Y-%m-%d}.xlsx"
        case "LAST_MONTH":
            today = date.today()
            last_month, last_year = (
                (12, today.year - 1)
                if today.month == 1
                else (today.month - 1, today.year)
            )
            calendar_month = calendar.Month(last_month)
            duration = Duration.month(calendar_month, last_year)
            filename = f"{outfile_prefix}{calendar_month.name}-{last_year}.xlsx"
        case str():
            try:
                start, end = args.duration.split(":", maxsplit=1)
                duration = Duration(
                    date.strptime(start, "%Y-%m-%d"), date.strptime(end, "%Y-%m-%d")
                )
                filename = f"{outfile_prefix}{args.duration.replace(':', '_')}.xlsx"
            except ValueError:
                try:
                    month_name, year = args.duration.split(",", maxsplit=1)
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
    filename = setting.reports_dir / filename
    if args.outfile:
        filename = args.outfile
    timetracking, holidays, timeoffs, person_ids = prepare_attendance_report(
        duration=duration,
        holiday_calendar_name=args.calendar,
    )
    export_attendance_report(
        timetracking, holidays, timeoffs, person_ids, str(filename)
    )
    if args.json:
        setting.reports_dir.mkdir(exist_ok=True)
        with (report_details_path := setting.reports_dir / "latest.json").open(
            "w"
        ) as fh:
            json.dump(
                {
                    "start": duration.start_date,
                    "end": duration.end_date,
                    "path": str(Path(filename).resolve()),
                },
                fh,
                default=date_json_encoder,
            )
        logging.info(
            "Report generation details written to %s", report_details_path.resolve()
        )


def clockin_handler(args: Namespace):
    from jibble_export.features.clocking import clock_in

    td = pd.Timedelta(args.autoout if args.autoout is not None else 0)
    if td > pd.Timedelta(days=1):
        raise ValueError("Auto clock out time cannot be longer than 1 day.")
    clock_in(auto_clock_out_after=td.to_pytimedelta())


def clockout_handler(args: Namespace):
    from jibble_export.features.clocking import clock_out

    clock_out()


def main():
    parser = ArgumentParser("jibble")
    subparsers = parser.add_subparsers()

    clockin_parser = subparsers.add_parser("clockin")
    clockin_parser.add_argument(
        "--autoout",
        help="Autoclockout after given timedelta in ISO 8601 timedelta format. e.g. `--autoout PT9H` for 9 hours.",
    )
    clockin_parser.set_defaults(func=clockin_handler)

    clockout_parser = subparsers.add_parser("clockout")
    clockout_parser.set_defaults(func=clockout_handler)

    export_parser = subparsers.add_parser(
        "export", formatter_class=RawTextHelpFormatter
    )
    export_parser.add_argument(
        "--calendar", "-c", help="Name of the calendar", default="Droplet"
    )
    export_parser.add_argument("--outfile", "-o", help="Path to the exported file")
    export_parser.add_argument("--duration", "-d", help=inspect.getdoc(export_handler))
    export_parser.add_argument(
        "--json",
        action="store_true",
        help="create reports/latest.json with export information. Useful for CI.",
    )
    export_parser.set_defaults(func=export_handler)

    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as msg:
        parser.error(str(msg))
