from uuid import UUID
import logging
from itertools import chain

import pandas as pd
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter


colorfills = {
    "Casual Leave": PatternFill(
        start_color="DDBBDDFF",
        end_color="DDBBDDFF",
        fill_type="solid",
    ),
    "Sick Leave": PatternFill(
        start_color="BBBBDDFF",
        end_color="BBBBDDFF",
        fill_type="solid",
    ),
    "Unpaid Leave": PatternFill(
        start_color="FF2222FF",
        end_color="FF2222FF",
        fill_type="solid",
    ),
    "Present": PatternFill(
        start_color="FFAAFFEF",
        end_color="FFAAFFEF",
        fill_type="solid",
    ),
    "Holidays": PatternFill(
        start_color="FEDCBAFF",
        end_color="FEDCBAFF",
        fill_type="solid",
    ),
    "W/Off": PatternFill(
        start_color="770088FF",
        end_color="770088FF",
        fill_type="solid",
    ),
}


def export_attendance_report(
    tracked_time_report: pd.DataFrame,
    holidays: pd.Series,
    timeoffs: pd.DataFrame,
    id_person_map: dict[UUID, str],
    filename: str,
):
    attendance_report = pd.DataFrame(
        index=tracked_time_report.index,
        columns=tracked_time_report.columns,
        dtype=object,
    )
    notnull_holidays = holidays.dropna()
    for person_id in timeoffs.columns:
        attendance_report.loc[notnull_holidays.index, person_id] = notnull_holidays
    attendance_report[tracked_time_report.notnull()] = "Present"
    attendance_report.loc[attendance_report.index.weekday >= 5, :] = "W/Off"  # ty: ignore[unresolved-attribute]
    for person_id in timeoffs.columns:
        notnull_timeoffs = timeoffs[person_id].dropna()
        attendance_report.loc[notnull_timeoffs.index, person_id] = notnull_timeoffs
    attendance_report = attendance_report.T

    longest_name_chars = max(map(len, id_person_map.values()), default=2)

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        attendance_report.to_excel(writer, startrow=1, startcol=1, index=False)
        worksheet = writer.sheets["Sheet1"]
        worksheet.sheet_format.defaultColWidth = 15
        dates = attendance_report.columns

        for i, person_id in enumerate(attendance_report.index, start=3):
            worksheet[f"A{i}"] = id_person_map.get(person_id, "N/A")

        worksheet.column_dimensions["A"].width = longest_name_chars + 2
        for col_idx, date in enumerate(
            dates, start=2
        ):  # start=2 because col A is index
            col_letter = get_column_letter(col_idx)
            for i, entry in enumerate(attendance_report[date], start=3):
                if pd.isna(entry):
                    continue
                elif entry.endswith("Casual Leave"):
                    worksheet[f"{col_letter}{i}"].fill = colorfills["Casual Leave"]
                elif entry.endswith("Sick Leave"):
                    worksheet[f"{col_letter}{i}"].fill = colorfills["Sick Leave"]
                elif entry.endswith("Unpaid Leave"):
                    worksheet[f"{col_letter}{i}"].fill = colorfills["Unpaid Leave"]
                elif entry == "Present":
                    worksheet[f"{col_letter}{i}"].fill = colorfills["Present"]
                elif entry == "W/Off":
                    worksheet[f"{col_letter}{i}"].fill = colorfills["W/Off"]
                else:
                    worksheet[f"{col_letter}{i}"].fill = colorfills["Holidays"]

            worksheet[f"{col_letter}1"] = date.strftime("%a")  # weekday name
            worksheet[f"{col_letter}2"] = date.strftime("%d")  # day number

            if date.weekday() >= 5:
                worksheet.column_dimensions[col_letter].width = 6

        for cell in chain(worksheet[1], worksheet[2]):
            cell.font = Font(bold=True)
    logging.info(f"Report successfully exported to {filename}")


def export_with_weekdays(df, filename, holidays=frozenset(), timeoffs=list()):
    df = df.astype(object)
    df[df.notnull()] = "P"
    idx = pd.IndexSlice
    for person_id, cols in timeoffs:
        df.loc[idx[person_id, :], cols] = "Leave"
    rows = len(df)
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        df.to_excel(writer, startrow=2)

        worksheet = writer.sheets["Sheet1"]
        index_strings = [str(x) for x in df.index]

        max_length = max(len(s) for s in index_strings) if index_strings else 0
        worksheet.column_dimensions["A"].width = max_length + 2
        dates = df.columns

        for col_idx, date in enumerate(
            dates, start=2
        ):  # start=2 because col A is index
            col_letter = get_column_letter(col_idx)

            worksheet[f"{col_letter}1"] = date.strftime("%a")  # weekday name
            worksheet[f"{col_letter}2"] = date.strftime("%d")  # day number

            if date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                fill = PatternFill(
                    start_color="DDDDE0", end_color="DDDDE0", fill_type="solid"
                )
                for i in range(0, rows + 3):  # rows + header + two extra headers
                    worksheet[f"{col_letter}{i + 1}"].fill = fill

            elif date in holidays:
                fill = PatternFill(
                    start_color="DDDDFF", end_color="DDDDFF", fill_type="solid"
                )
                for i in range(0, rows + 3):  # rows + header + two extra headers
                    worksheet[f"{col_letter}{i + 1}"].fill = fill

        for cell in chain(worksheet[1], worksheet[2]):
            cell.font = Font(bold=True)
    logging.info(f"Report successfully exported to {filename}")
