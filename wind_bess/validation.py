"""Rule-based engineering checks; checks do not certify code or utility compliance."""
from __future__ import annotations
import pandas as pd

def check_project(n_wtg, feeder_counts, p_wtg_mw, p_bess_mw, bess_feeders,
                  poi_export_mw, poi_import_mw, gsu_mva, wtg_total_current_mw=None):
    findings=[]
    if sum(feeder_counts) != n_wtg:
        findings.append({"Severity":"ERROR","Check":"Wind feeder allocation","Result":f"Feeder sum {sum(feeder_counts)} does not equal {n_wtg} WTGs.","Action":"Correct the feeder allocation."})
    else:
        findings.append({"Severity":"PASS","Check":"Wind feeder allocation","Result":f"{n_wtg} WTGs allocated across {len(feeder_counts)} feeders.","Action":"None."})
    if p_wtg_mw <= 0 or n_wtg <= 0:
        findings.append({"Severity":"ERROR","Check":"Wind ratings","Result":"WTG count and rating must be positive.","Action":"Correct inputs."})
    if bess_feeders < 1:
        findings.append({"Severity":"ERROR","Check":"BESS feeders","Result":"At least one BESS feeder is required.","Action":"Set a valid feeder count."})
    if poi_export_mw <= 0 or poi_import_mw <= 0:
        findings.append({"Severity":"ERROR","Check":"POI limits","Result":"Import/export limits must be positive magnitudes.","Action":"Enter confirmed limits."})
    if gsu_mva > 0:
        findings.append({"Severity":"INFO","Check":"GSU status","Result":f"{gsu_mva:g} MVA entered; rating is not automatically approved.","Action":"Validate load flow, reactive envelope, losses, ambient, impedance and utility requirements."})
    if p_bess_mw > 0 and bess_feeders > 0:
        findings.append({"Severity":"INFO","Check":"BESS feeder allocation","Result":"Equal allocation is only a screening assumption unless PCS/MVT grouping is provided.","Action":"Replace with actual PCS and transformer grouping."})
    return pd.DataFrame(findings)

def check_cable_results(sections: pd.DataFrame, max_voltage_drop_pct: float = 3.0) -> pd.DataFrame:
    rows=[]
    for _,r in sections.iterrows():
        if not r.get("Length supplied?", False):
            rows.append({"Severity":"OPEN","Check":f"{r['Feeder']} section {r['Section']} length","Result":"Length not supplied; voltage drop and loss not calculated.","Action":"Enter route length and verify cable R/X."})
        if r.get("Selected size (screening)") == "NOT SIZED":
            rows.append({"Severity":"ERROR","Check":f"{r['Feeder']} section {r['Section']} ampacity","Result":"No conductor in the supplied library meets calculated current.","Action":"Expand the validated cable library or change design; do not silently select a size."})
        dv=r.get("Voltage drop (%)")
        if dv is not None and pd.notna(dv) and dv > max_voltage_drop_pct:
            rows.append({"Severity":"WARNING","Check":f"{r['Feeder']} section {r['Section']} voltage drop","Result":f"{dv:.3f}% exceeds screening threshold {max_voltage_drop_pct:.2f}%.","Action":"Review cable size, route, voltage profile and design criterion."})
    return pd.DataFrame(rows, columns=["Severity","Check","Result","Action"])
