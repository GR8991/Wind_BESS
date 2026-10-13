from __future__ import annotations
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

def build_preliminary_pdf(project_info: dict, tables: dict, findings=None) -> bytes:
    """Generate a compact preliminary engineering summary PDF from current app results."""
    bio=BytesIO()
    doc=SimpleDocTemplate(bio,pagesize=landscape(A4),rightMargin=12*mm,leftMargin=12*mm,topMargin=12*mm,bottomMargin=12*mm)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SmallCell",parent=styles["BodyText"],fontSize=7,leading=8))
    story=[]
    story.append(Paragraph("Wind + BESS Engineering Workbench",styles["Title"]))
    story.append(Paragraph("PRELIMINARY ENGINEERING — NOT FOR CONSTRUCTION",styles["Heading2"]))
    story.append(Paragraph("Generated from current user inputs. Not a construction document, utility approval, or signed engineering report.",styles["BodyText"]))
    story.append(Spacer(1,5*mm))
    rows=[["Project parameter","Value"]]+[[str(k),str(v)] for k,v in project_info.items()]
    t=Table(rows,colWidths=[55*mm,180*mm],repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17365D")),
                           ("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                           ("GRID",(0,0),(-1,-1),0.3,colors.grey),("FONTSIZE",(0,0),(-1,-1),8),
                           ("VALIGN",(0,0),(-1,-1),"TOP"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F2F5F9")])]))
    story.append(t)
    story.append(Spacer(1,5*mm))
    for title,df in tables.items():
        if df is None or len(df)==0:
            continue
        story.append(Paragraph(title,styles["Heading2"]))
        display=df.copy()
        # Keep reports readable: limit wide/long tables while full results remain in XLSX.
        if len(display)>30:
            display=display.head(30)
            truncated=True
        else:
            truncated=False
        cols=[str(c) for c in display.columns]
        data=[[Paragraph(c,styles["SmallCell"]) for c in cols]]
        for row in display.itertuples(index=False,name=None):
            data.append([Paragraph("" if v is None else str(v),styles["SmallCell"]) for v in row])
        available_width=landscape(A4)[0]-24*mm
        col_width=available_width/max(len(cols),1)
        tbl=Table(data,colWidths=[col_width]*len(cols),repeatRows=1)
        tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17365D")),
                                 ("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.25,colors.grey),
                                 ("FONTSIZE",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),"TOP"),
                                 ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F2F5F9")])]))
        story.append(tbl)
        if truncated:
            story.append(Paragraph("Only the first 30 rows are shown here. Download the Excel workbook for full results.",styles["Italic"]))
        story.append(Spacer(1,4*mm))
    if findings is not None and len(findings)>0:
        story.append(PageBreak())
        story.append(Paragraph("Validation findings and open items",styles["Heading1"]))
        rows=[list(findings.columns)]+findings.astype(str).values.tolist()
        tbl=Table(rows,repeatRows=1)
        tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17365D")),
                                 ("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.25,colors.grey),
                                 ("FONTSIZE",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),"TOP")]))
        story.append(tbl)
    doc.build(story)
    return bio.getvalue()
