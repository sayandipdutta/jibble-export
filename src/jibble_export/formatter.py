from itertools import chain
import pandas as pd
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

def export_with_weekdays(df, filename, holidays=frozenset()):
    rows = len(df)
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        df.to_excel(writer, startrow=2)
        
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        index_strings = [str(x) for x in df.index]

        max_length = max(len(s) for s in index_strings) if index_strings else 0
        worksheet.column_dimensions['A'].width = max_length + 2
        dates = df.columns

        for col_idx, date in enumerate(dates, start=2):  # start=2 because col A is index
            col_letter = get_column_letter(col_idx)

            worksheet[f"{col_letter}1"] = date.strftime("%a")  # weekday name
            worksheet[f"{col_letter}2"] = date.strftime("%d")  # day number

            if date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                fill = PatternFill(start_color="DDDDE0",
                                   end_color="DDDDE0",
                                   fill_type="solid")
                for i in range(1, rows + 4): # rows + header + two extra headers + open_end
                    worksheet[f"{col_letter}{i}"].fill = fill

            elif date in holidays:
                fill = PatternFill(start_color="DDDDFF",
                                   end_color="DDDDFF",
                                   fill_type="solid")
                for i in range(1, rows + 4): # rows + header + two extra headers + open_end
                    worksheet[f"{col_letter}{i}"].fill = fill

        for cell in chain(worksheet[1], worksheet[2]):
            cell.font = Font(bold=True)
