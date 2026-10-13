from __future__ import annotations
from io import BytesIO
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

def read_tabular_upload(uploaded_file) -> pd.DataFrame:
    name=uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if name.endswith(".xlsx") or name.endswith(".xlsm"):
        xls=pd.ExcelFile(uploaded_file)
        return pd.read_excel(xls, sheet_name=xls.sheet_names[0])
    raise ValueError("Supported input formats are CSV and XLSX.")

def workbook_bytes(sheets: dict[str,pd.DataFrame], project_info: dict | None = None) -> bytes:
    wb=Workbook()
    ws=wb.active
    ws.title="Project Summary"
    ws.append(["Wind + BESS Engineering Workbench"])
    ws.append(["Status","PRELIMINARY ENGINEERING — NOT FOR CONSTRUCTION"])
    if project_info:
        ws.append([])
        ws.append(["Parameter","Value"])
        for k,v in project_info.items():
            ws.append([k,v])
    style_sheet(ws)
    for name,df in sheets.items():
        sh=wb.create_sheet(name[:31])
        sh.append(list(df.columns))
        for row in df.itertuples(index=False, name=None):
            sh.append([None if pd.isna(v) else (v.item() if hasattr(v,"item") else v) for v in row])
        style_sheet(sh)
    bio=BytesIO()
    wb.save(bio)
    return bio.getvalue()

def style_sheet(ws):
    navy="17365D"
    for cell in ws[1]:
        cell.font=Font(bold=True,color="FFFFFF")
        cell.fill=PatternFill("solid",fgColor=navy)
        cell.alignment=Alignment(wrap_text=True,vertical="center")
    ws.freeze_panes="A2"
    ws.auto_filter.ref=ws.dimensions if ws.max_row>1 else "A1:A1"
    for col in ws.columns:
        values=[len(str(c.value)) if c.value is not None else 0 for c in list(col)[:100]]
        ws.column_dimensions[get_column_letter(col[0].column)].width=min(max(max(values,default=10)+2,12),38)

def extract_benchmark_workbook(uploaded_file) -> dict:
    """Read sheet names and selected values from the supplied P0 calculation workbook."""
    xls=pd.ExcelFile(uploaded_file)
    result={"sheet_names":xls.sheet_names,"sheets":{}}
    for name in xls.sheet_names:
        try:
            df=pd.read_excel(xls,sheet_name=name,header=None)
            result["sheets"][name]=df
        except Exception:
            pass
    return result
