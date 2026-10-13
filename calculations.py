"""Traceable screening calculations. Inputs use MW, MVA, kV, km, ohm/km and A."""
from __future__ import annotations
from math import sqrt, acos, tan, cos, sin, radians
from typing import Iterable
import pandas as pd

SQRT3 = sqrt(3.0)

def require_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero; received {value}.")

def apparent_power_mva(p_mw: float, pf: float) -> float:
    require_positive("Power factor", pf)
    if pf > 1:
        raise ValueError("Power factor must be between 0 and 1.")
    return abs(p_mw) / pf

def reactive_power_mvar(p_mw: float, pf: float) -> float:
    require_positive("Power factor", pf)
    if pf > 1:
        raise ValueError("Power factor must be between 0 and 1.")
    return abs(p_mw) * tan(acos(pf))

def three_phase_current_a(s_mva: float, v_ll_kv: float, voltage_pu: float = 1.0) -> float:
    require_positive("Line-line voltage", v_ll_kv)
    require_positive("Voltage pu", voltage_pu)
    return abs(s_mva) * 1000 / (SQRT3 * v_ll_kv * voltage_pu)

def wtg_summary(n_wtg: int, p_wtg_mw: float, pf_wtg: float, v_lv_kv: float,
                v_mv_kv: float, voltage_min_pu: float = 1.0) -> dict:
    if n_wtg < 1:
        raise ValueError("Number of WTGs must be at least 1.")
    s_wtg = apparent_power_mva(p_wtg_mw, pf_wtg)
    q_wtg = reactive_power_mvar(p_wtg_mw, pf_wtg)
    return {
        "WTG count": n_wtg,
        "WTG active power (MW)": p_wtg_mw,
        "Gross wind active power (MW)": n_wtg * p_wtg_mw,
        "WTG apparent power (MVA)": s_wtg,
        "WTG reactive magnitude at stated PF (Mvar)": q_wtg,
        "WTG LV current at PF (A)": three_phase_current_a(s_wtg, v_lv_kv),
        "WTG LV current at minimum voltage pu (A)": three_phase_current_a(s_wtg, v_lv_kv, voltage_min_pu),
        "WTG MV current at PF (A)": three_phase_current_a(s_wtg, v_mv_kv),
        "WTG MV current at minimum voltage pu (A)": three_phase_current_a(s_wtg, v_mv_kv, voltage_min_pu),
        "Gross wind apparent power (MVA)": n_wtg * s_wtg,
        "Gross wind current at MV at stated PF (A)": three_phase_current_a(n_wtg*s_wtg, v_mv_kv),
    }

def feeder_summary(feeder_name: str, n_wtg: int, p_wtg_mw: float, pf: float,
                   v_mv_kv: float, voltage_min_pu: float = 1.0) -> dict:
    if n_wtg < 1:
        raise ValueError(f"{feeder_name}: turbine count must be >= 1.")
    p = n_wtg * p_wtg_mw
    s = apparent_power_mva(p, pf)
    return {
        "Feeder": feeder_name,
        "WTGs": n_wtg,
        "P (MW)": p,
        "S (MVA)": s,
        "Current @1.0 pu (A)": three_phase_current_a(s, v_mv_kv),
        "Current @minimum voltage (A)": three_phase_current_a(s, v_mv_kv, voltage_min_pu),
    }

def radial_sections(feeder_name: str, n_wtg: int, p_wtg_mw: float, pf: float,
                    v_mv_kv: float, voltage_min_pu: float,
                    home_run_km: float | None = None,
                    inter_wtg_km: float | None = None,
                    conductor_library: pd.DataFrame | None = None,
                    grouped_home_run_ampacity: dict | None = None) -> pd.DataFrame:
    """Create sections from remote end toward substation; section k carries k WTGs.
    Cable loss/voltage-drop are computed only if lengths are provided (>0) and R/X exist.
    """
    if n_wtg < 1:
        raise ValueError("n_wtg must be >= 1")
    rows = []
    for section in range(1, n_wtg + 1):
        k = section
        s_mva = k * apparent_power_mva(p_wtg_mw, pf)
        i_nom = three_phase_current_a(s_mva, v_mv_kv)
        i_min = three_phase_current_a(s_mva, v_mv_kv, voltage_min_pu)
        length = home_run_km if section == n_wtg else inter_wtg_km
        selected = None
        if conductor_library is not None and not conductor_library.empty:
            for _, c in conductor_library.iterrows():
                amp = c["Grouped ampacity (A)"] if section == n_wtg and "Grouped ampacity (A)" in c and pd.notna(c["Grouped ampacity (A)"]) else c["Ampacity (A)"]
                if pd.notna(amp) and float(amp) >= i_min:
                    selected = c.copy()
                    selected["_ampacity_used"] = float(amp)
                    break
        size = selected["Size"] if selected is not None else "NOT SIZED"
        ampacity = selected["_ampacity_used"] if selected is not None else None
        r = float(selected["Rac (ohm/km)"]) if selected is not None and pd.notna(selected.get("Rac (ohm/km)")) else None
        x = float(selected["X (ohm/km)"]) if selected is not None and pd.notna(selected.get("X (ohm/km)")) else None
        dv = loss = None
        if length is not None and length > 0 and r is not None and x is not None:
            sinphi = sqrt(max(0.0, 1-pf**2))
            dv = SQRT3 * i_nom * length * (r*pf + x*sinphi) / (v_mv_kv*1000) * 100
            loss = 3 * i_nom**2 * r * length / 1000
        rows.append({
            "Feeder": feeder_name, "Section": section,
            "Path description": "Home-run to substation" if section == n_wtg else f"WTG {n_wtg-section+1} to next WTG",
            "WTGs carried k": k, "P (MW)": k*p_wtg_mw, "S (MVA)": s_mva,
            "I @1.0 pu (A)": i_nom, "I @minimum voltage (A)": i_min,
            "Length (km)": length, "Selected size (screening)": size,
            "Ampacity used (A)": ampacity, "Loading (%)": (i_min/ampacity*100 if ampacity else None),
            "Rac (ohm/km)": r, "X (ohm/km)": x, "Voltage drop (%)": dv, "Loss (kW)": loss,
            "Length supplied?": bool(length is not None and length > 0)
        })
    return pd.DataFrame(rows)

def gsu_summary(p_poi_mw: float, pf_poi: float, gsu_mva: float,
                v_hv_kv: float, v_mv_kv: float, voltage_pu_cases=(0.95, 1.0, 1.05),
                z_pu: float | None = None) -> tuple[dict, pd.DataFrame]:
    s_poi = apparent_power_mva(p_poi_mw, pf_poi)
    q_poi = reactive_power_mvar(p_poi_mw, pf_poi)
    base = {
        "POI active power (MW)": p_poi_mw,
        "Assumed POI PF": pf_poi,
        "Required |Q| at POI (Mvar)": q_poi,
        "Required apparent power at POI (MVA)": s_poi,
        "GSU candidate rating (MVA)": gsu_mva,
        "GSU HV rated current (A)": three_phase_current_a(gsu_mva, v_hv_kv),
        "GSU MV rated current (A)": three_phase_current_a(gsu_mva, v_mv_kv),
        "GSU candidate loading at nominal voltage (%)": s_poi/gsu_mva*100,
    }
    cases=[]
    for vpu in voltage_pu_cases:
        s_equiv = s_poi / vpu
        cases.append({"HV voltage (pu)":vpu, "P (MW)":p_poi_mw,
                      "Q magnitude (Mvar)":q_poi, "Equivalent MVA/current loading (MVA)":s_equiv,
                      "Loading of GSU candidate (%)":s_equiv/gsu_mva*100,
                      "Current at HV (A)":three_phase_current_a(s_poi, v_hv_kv, vpu)})
    if z_pu and z_pu > 0:
        base["Infinite-source 3-phase fault via GSU at MV (kA; screening)"] = three_phase_current_a(gsu_mva, v_mv_kv)/(z_pu*1000)
        base["Infinite-source 3-phase fault via GSU at HV (kA; screening)"] = three_phase_current_a(gsu_mva, v_hv_kv)/(z_pu*1000)
    return base, pd.DataFrame(cases)

def bess_feeder_summary(p_bess_mw: float, n_feeders: int, pf_bess: float,
                        v_mv_kv: float, voltage_min_pu: float = 1.0) -> pd.DataFrame:
    if n_feeders < 1:
        raise ValueError("BESS feeder count must be >= 1.")
    p_each = p_bess_mw/n_feeders
    s_each = apparent_power_mva(p_each, pf_bess)
    return pd.DataFrame([{
        "Feeder": f"BESS-{i+1:02d}", "Assigned P (MW)": p_each, "Assigned S (MVA)": s_each,
        "Current @1.0 pu (A)": three_phase_current_a(s_each, v_mv_kv),
        "Current @minimum voltage (A)": three_phase_current_a(s_each, v_mv_kv, voltage_min_pu),
        "Basis": "Equal allocation screening only; replace with actual PCS/MVT grouping"
    } for i in range(n_feeders)])

def poi_scenarios(wind_mw: float, bess_mw_signed: list[float], wind_loss_pct: float,
                  bess_loss_pct: float, aux_mw: float, export_limit_mw: float,
                  import_limit_mw: float) -> pd.DataFrame:
    """BESS signed power: positive=discharge, negative=charge. Loss percentages are decimal fractions."""
    rows=[]
    for p_bess in bess_mw_signed:
        wind_at_poi = wind_mw * (1-wind_loss_pct)
        bess_at_poi = p_bess*(1-bess_loss_pct) if p_bess >= 0 else p_bess*(1+bess_loss_pct)
        net = wind_at_poi + bess_at_poi - aux_mw
        rows.append({"Wind at WTG terminals (MW)":wind_mw, "BESS at MV (+discharge/-charge) (MW)":p_bess,
                     "Wind at POI contribution (MW)":wind_at_poi, "BESS at POI contribution (MW)":bess_at_poi,
                     "Auxiliary load (MW)":aux_mw, "Net POI (+export) MW":net,
                     "Within POI limits?": (-import_limit_mw <= net <= export_limit_mw)})
    return pd.DataFrame(rows)

def cable_section_calculation(current_a: float, length_km: float, r_ohm_km: float,
                              x_ohm_km: float, v_ll_kv: float, pf: float) -> dict:
    """Three-phase screening: ΔV% = √3 I L (R PF + X sinφ) / VLL × 100; loss=3I²RL."""
    if min(current_a, length_km, r_ohm_km, x_ohm_km, v_ll_kv) < 0:
        raise ValueError("Current, length, R, X and voltage cannot be negative.")
    sinphi = sqrt(max(0.0, 1-pf**2))
    dv = SQRT3*current_a*length_km*(r_ohm_km*pf+x_ohm_km*sinphi)/(v_ll_kv*1000)*100
    loss = 3*current_a**2*r_ohm_km*length_km/1000
    return {"Voltage drop (%)":dv, "Loss (kW)":loss}

def optimize_dispatch(df: pd.DataFrame, wind_col: str, price_col: str,
                      wind_capacity_mw: float, bess_power_mw: float, bess_energy_mwh: float,
                      round_trip_efficiency: float, initial_soc_mwh: float,
                      export_limit_mw: float, import_limit_mw: float,
                      capture_curtailment: bool = True) -> pd.DataFrame:
    """Transparent heuristic hourly dispatch, not a market-optimal MILP.
    Input rows must be equally spaced; interval duration is inferred from timestamp if present, else 1 h.
    Wind column is MW available at the site before POI cap. Positive BESS power means discharge.
    """
    if not 0 < round_trip_efficiency <= 1:
        raise ValueError("Round-trip efficiency must be in (0, 1].")
    if bess_power_mw < 0 or bess_energy_mwh < 0:
        raise ValueError("BESS ratings cannot be negative.")
    work = df.copy().reset_index(drop=True)
    if "timestamp" in work.columns and len(work) > 1:
        ts = pd.to_datetime(work["timestamp"], errors="coerce")
        diffs = ts.diff().dropna().dt.total_seconds()/3600
        dt = float(diffs.median()) if len(diffs) else 1.0
        if dt <= 0: dt = 1.0
    else:
        dt = 1.0
    # Use symmetric charge/discharge efficiency so eta_c*eta_d=RTE.
    eta = sqrt(round_trip_efficiency)
    soc = min(max(initial_soc_mwh, 0.0), bess_energy_mwh)
    rows=[]
    prices = pd.to_numeric(work[price_col], errors="coerce").fillna(0).tolist()
    winds = pd.to_numeric(work[wind_col], errors="coerce").fillna(0).clip(lower=0, upper=wind_capacity_mw).tolist()
    for i,(wind,price) in enumerate(zip(winds,prices)):
        available_for_export = min(wind, export_limit_mw)
        curtailed = max(0.0, wind-export_limit_mw)
        p_bess = 0.0
        # Charge on surplus above export cap first; otherwise charge when price is negative.
        if bess_power_mw > 0 and soc < bess_energy_mwh and (capture_curtailment and curtailed > 0 or price < 0):
            charge_headroom = min(bess_power_mw, (bess_energy_mwh-soc)/(eta*dt))
            if curtailed > 0 and capture_curtailment:
                p_charge = min(charge_headroom, curtailed)
            else:
                p_charge = charge_headroom
            p_bess = -max(0.0, p_charge)
            soc += (-p_bess)*eta*dt
        elif bess_power_mw > 0 and soc > 0 and price > 0:
            p_discharge = min(bess_power_mw, soc*eta/dt, max(0.0, export_limit_mw-wind))
            # If wind already exceeds export cap, don't discharge; charge/capture logic should act first.
            if wind < export_limit_mw:
                p_bess = max(0.0, p_discharge)
                soc -= p_bess/eta*dt
        soc = min(max(soc,0.0),bess_energy_mwh)
        net = wind + p_bess
        # Enforce import/export caps as a simple dispatch limit.
        net = min(export_limit_mw, max(-import_limit_mw, net))
        rows.append({"timestamp":work.loc[i,"timestamp"] if "timestamp" in work.columns else i,
                     "Wind available (MW)":wind,"Price":price,"BESS power (+discharge/-charge MW)":p_bess,
                     "Net POI before clamp (MW)":wind+p_bess,"Net POI (MW)":net,
                     "Estimated curtailed (MW)":max(0.0,wind-net) if p_bess < 0 else max(0.0,wind-export_limit_mw),
                     "SOC (MWh)":soc,"Interval (h)":dt})
    return pd.DataFrame(rows)
