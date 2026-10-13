from __future__ import annotations
import json
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
from wind_bess.calculations import (
    wtg_summary, feeder_summary, radial_sections, gsu_summary,
    bess_feeder_summary, poi_scenarios, optimize_dispatch
)
from wind_bess.validation import check_project, check_cable_results
from wind_bess.io_utils import workbook_bytes, read_tabular_upload, extract_benchmark_workbook
from wind_bess.report import build_preliminary_pdf

st.set_page_config(page_title="Wind + BESS Engineering Workbench", page_icon="⚡", layout="wide")
st.title("Wind + BESS Engineering Workbench")
st.caption("Release 1 MVP • Local engineering workstation • Preliminary calculations only")
st.warning("PRELIMINARY ENGINEERING — NOT FOR CONSTRUCTION. Results depend on user inputs and stated assumptions. This tool does not replace OEM data, utility approval, detailed studies or licensed engineering review.")

with st.sidebar:
    st.header("Project")
    project_name=st.text_input("Project name","Wind + BESS Project")
    mode=st.radio("Starting basis",["New project","Load included benchmark case"])
    st.caption("The benchmark case is based on the uploaded Rev P0 workbook. Imported assumptions remain visibly marked as assumptions.")

# Project inputs
if mode == "Load included benchmark case":
    defaults={"n_wtg":27,"p_wtg":3.8,"pf_wtg":0.95,"v_lv":0.69,"v_mv":34.5,"v_hv":115,
              "voltage_min":0.95,"feeders":[7,7,7,6],"p_bess":100.0,"e_bess":200.0,
              "bess_feeders":4,"pf_bess":0.95,"poi_pf":0.95,"poi_export":100.0,"poi_import":100.0,
              "gsu_mva":125.0,"z_pu":0.10,"wind_loss_pct":0.015,"bess_loss_pct":0.015,"aux_mw":1.0,
              "home_run_km":5.0,"inter_wtg_km":0.616}
else:
    defaults={"n_wtg":27,"p_wtg":3.8,"pf_wtg":0.95,"v_lv":0.69,"v_mv":34.5,"v_hv":115,
              "voltage_min":0.95,"feeders":[7,7,7,6],"p_bess":100.0,"e_bess":200.0,
              "bess_feeders":4,"pf_bess":0.95,"poi_pf":0.95,"poi_export":100.0,"poi_import":100.0,
              "gsu_mva":125.0,"z_pu":None,"wind_loss_pct":None,"bess_loss_pct":None,"aux_mw":None,
              "home_run_km":None,"inter_wtg_km":None}

tabs=st.tabs(["Project Setup","Wind Collector","BESS & GSU","POI Scenarios","Operations","Uploads & Benchmark","Export"])

with tabs[0]:
    st.subheader("Project design basis")
    st.write("Enter confirmed values where available. The app labels defaults and assumptions; it does not treat them as approved data.")
    c1,c2,c3=st.columns(3)
    with c1:
        n_wtg=st.number_input("Number of WTGs",min_value=1,max_value=500,value=int(defaults["n_wtg"]),step=1)
        p_wtg=st.number_input("WTG rated active power (MW)",min_value=0.01,value=float(defaults["p_wtg"]),step=0.1)
        pf_wtg=st.number_input("WTG PF magnitude (screening)",min_value=0.01,max_value=1.0,value=float(defaults["pf_wtg"]),step=0.01)
        v_lv=st.number_input("WTG LV voltage (kV)",min_value=0.01,value=float(defaults["v_lv"]),step=0.01)
    with c2:
        v_mv=st.number_input("Collector bus voltage (kV)",min_value=0.01,value=float(defaults["v_mv"]),step=0.5)
        v_hv=st.number_input("POI / GSU HV voltage (kV)",min_value=0.01,value=float(defaults["v_hv"]),step=5.0)
        voltage_min=st.number_input("Minimum voltage for current screening (pu)",min_value=0.5,max_value=1.0,value=float(defaults["voltage_min"]),step=0.01)
        poi_pf=st.number_input("POI PF magnitude (assumption unless utility confirmed)",min_value=0.01,max_value=1.0,value=float(defaults["poi_pf"]),step=0.01)
    with c3:
        p_bess=st.number_input("BESS active power (MW)",min_value=0.0,value=float(defaults["p_bess"]),step=1.0)
        e_bess=st.number_input("BESS energy (MWh)",min_value=0.0,value=float(defaults["e_bess"]),step=1.0)
        poi_export=st.number_input("Maximum POI export (MW)",min_value=0.0,value=float(defaults["poi_export"]),step=1.0)
        poi_import=st.number_input("Maximum POI import (MW)",min_value=0.0,value=float(defaults["poi_import"]),step=1.0)
    st.markdown("**Feeder allocation**")
    feeder_count=st.number_input("Number of wind collector feeders",min_value=1,max_value=20,value=len(defaults["feeders"]),step=1)
    default_counts=(defaults["feeders"]+[0]*20)[:int(feeder_count)]
    feeder_df=pd.DataFrame({"Feeder":[f"WF-{i+1:02d}" for i in range(int(feeder_count))],"WTGs":default_counts})
    feeder_df=st.data_editor(feeder_df,num_rows="fixed",use_container_width=True,key="feeder_alloc")
    feeder_counts=[int(x) for x in feeder_df["WTGs"].tolist()]
    if sum(feeder_counts)!=int(n_wtg):
        st.error(f"Feeder allocation totals {sum(feeder_counts)} WTGs, but project has {n_wtg}. Correct before relying on feeder results.")
    else:
        st.success(f"Allocation check passed: {sum(feeder_counts)} WTGs across {len(feeder_counts)} feeders.")
    st.caption("Benchmark case uses PF 0.95 and minimum voltage 0.95 pu as screening assumptions from the supplied workbook. New projects should confirm these inputs.")

with tabs[1]:
    st.subheader("Wind turbine and radial collector calculations")
    summary=wtg_summary(int(n_wtg),p_wtg,pf_wtg,v_lv,v_mv,voltage_min)
    metrics=st.columns(4)
    metrics[0].metric("Gross wind",f"{summary['Gross wind active power (MW)']:.2f} MW")
    metrics[1].metric("WTG S",f"{summary['WTG apparent power (MVA)']:.2f} MVA")
    metrics[2].metric("WTG LV current",f"{summary['WTG LV current at PF (A)']:,.0f} A")
    metrics[3].metric("WTG MV current",f"{summary['WTG MV current at PF (A)']:.1f} A")
    st.markdown("**Traceable formulae**")
    st.latex(r"S_{WTG}=P_{WTG}/PF")
    st.latex(r"I=\frac{S\times1000}{\sqrt{3}\,V_{LL}\,V_{pu}}")
    st.dataframe(pd.DataFrame([{"Parameter":k,"Result":v} for k,v in summary.items()]),use_container_width=True)
    st.markdown("**Conductor library (screening values; replace with approved manufacturer/design data)**")
    conductor_df=pd.DataFrame([
        {"Size":"1/0 AWG","Ampacity (A)":174,"Grouped ampacity (A)":None,"Rac (ohm/km)":0.6912,"X (ohm/km)":0.1899},
        {"Size":"4/0 AWG","Ampacity (A)":253,"Grouped ampacity (A)":None,"Rac (ohm/km)":0.3452,"X (ohm/km)":0.1700},
        {"Size":"350 kcmil","Ampacity (A)":332,"Grouped ampacity (A)":None,"Rac (ohm/km)":0.2092,"X (ohm/km)":0.1562},
        {"Size":"500 kcmil","Ampacity (A)":401,"Grouped ampacity (A)":None,"Rac (ohm/km)":0.1470,"X (ohm/km)":0.1474},
        {"Size":"750 kcmil","Ampacity (A)":495,"Grouped ampacity (A)":455,"Rac (ohm/km)":0.0990,"X (ohm/km)":0.1377},
        {"Size":"1000 kcmil","Ampacity (A)":524,"Grouped ampacity (A)":654,"Rac (ohm/km)":0.0754,"X (ohm/km)":0.1311},
    ])
    conductor_df=st.data_editor(conductor_df,num_rows="dynamic",use_container_width=True,key="cable_lib")
    benchmark_lengths=(mode=="Load included benchmark case")
    st.markdown("**Cable section length assumptions**")
    lc1,lc2=st.columns(2)
    with lc1:
        home_run_km=st.number_input("Home-run length per feeder (km)",min_value=0.0,value=float(defaults["home_run_km"] or 0.0),step=0.1)
    with lc2:
        inter_wtg_km=st.number_input("Each inter-WTG section length (km)",min_value=0.0,value=float(defaults["inter_wtg_km"] or 0.0),step=0.01)
    if mode=="New project" and (home_run_km==0 or inter_wtg_km==0):
        st.info("Enter actual route lengths to calculate cable voltage drop and losses. Zero is treated as missing data, not as a real zero-length cable.")
    section_frames=[]
    for i,count in enumerate(feeder_counts):
        if count<1:
            continue
        sec=radial_sections(f"WF-{i+1:02d}",count,p_wtg,pf_wtg,v_mv,voltage_min,
                            home_run_km if home_run_km>0 else None,
                            inter_wtg_km if inter_wtg_km>0 else None,conductor_df)
        section_frames.append(sec)
    sections=pd.concat(section_frames,ignore_index=True) if section_frames else pd.DataFrame()
    if not sections.empty:
        st.dataframe(sections,hide_index=True,use_container_width=True)
        if sections["Loss (kW)"].notna().any():
            totals=sections.groupby("Feeder",as_index=False).agg(**{"Cable loss (kW)":("Loss (kW)","sum"),"Voltage drop sum (%)":("Voltage drop (%)","sum")})
            st.dataframe(totals,use_container_width=True)
            st.caption("Section voltage drops are shown as a screening sum along a radial path. Validate voltage profile with load-flow software before design approval.")
        else:
            st.warning("Cable losses and voltage drop are not calculated because valid lengths or conductor data are missing.")
    cable_checks=check_cable_results(sections) if not sections.empty else pd.DataFrame()

with tabs[2]:
    st.subheader("BESS feeder currents and GSU candidate")
    c1,c2,c3=st.columns(3)
    with c1:
        n_bess_feeders=st.number_input("Number of BESS MV feeders",min_value=1,max_value=20,value=int(defaults["bess_feeders"]),step=1)
        pf_bess=st.number_input("BESS PF magnitude (screening)",min_value=0.01,max_value=1.0,value=float(defaults["pf_bess"]),step=0.01)
    with c2:
        gsu_mva=st.number_input("GSU candidate rating (MVA)",min_value=1.0,value=float(defaults["gsu_mva"]),step=5.0)
        z_default=defaults["z_pu"] if defaults["z_pu"] is not None else 0.10
        z_pu_pct=st.number_input("GSU impedance (%) — optional screening input",min_value=0.0,max_value=30.0,value=float(z_default*100),step=0.5)
    with c3:
        gsu_status=st.selectbox("GSU status",["Candidate only — not approved","Utility/OEM data confirmed"],index=0)
        st.caption("Choose confirmed only when supported by a controlled specification.")
    bess_table=bess_feeder_summary(p_bess,int(n_bess_feeders),pf_bess,v_mv,voltage_min)
    st.markdown("**BESS feeders — equal allocation screening**")
    st.dataframe(bess_table,use_container_width=True,hide_index=True)
    gsu_base,gsu_cases=gsu_summary(poi_export,poi_pf,gsu_mva,v_hv,v_mv,z_pu_pct/100 if z_pu_pct>0 else None)
    st.markdown("**GSU sizing**")
    gcols=st.columns(4)
    gcols[0].metric("POI apparent power",f"{gsu_base['Required apparent power at POI (MVA)']:.2f} MVA")
    gcols[1].metric("Required |Q|",f"{gsu_base['Required |Q| at POI (Mvar)']:.2f} Mvar")
    gcols[2].metric("HV rated current",f"{gsu_base['GSU HV rated current (A)']:.1f} A")
    gcols[3].metric("MV rated current",f"{gsu_base['GSU MV rated current (A)']:.1f} A")
    st.dataframe(pd.DataFrame([{"Parameter":k,"Value":v} for k,v in gsu_base.items()]),use_container_width=True)
    st.dataframe(gsu_cases,use_container_width=True,hide_index=True)
    st.caption("The voltage-dependent equivalent MVA is a screening proxy for current loading at fixed active/reactive power. Final transformer loading requires a load-flow/transformer study and confirmed utility P–Q requirement.")

with tabs[3]:
    st.subheader("POI operating scenarios")
    st.caption("Positive BESS MW means discharge; negative means charging. Losses and auxiliary load must be entered or clearly marked as assumptions.")
    c1,c2,c3=st.columns(3)
    with c1:
        wind_loss_pct_in=st.number_input("Wind path losses (%)",min_value=0.0,max_value=20.0,value=float((defaults["wind_loss_pct"] or 0)*100),step=0.1)
    with c2:
        bess_loss_pct_in=st.number_input("BESS path losses (%)",min_value=0.0,max_value=20.0,value=float((defaults["bess_loss_pct"] or 0)*100),step=0.1)
    with c3:
        aux_mw_in=st.number_input("Auxiliary load (MW)",min_value=0.0,value=float(defaults["aux_mw"] or 0.0),step=0.1)
    scen_bess=st.multiselect("BESS operating setpoints (MW; + discharge / − charge)",options=[-100,-75,-50,-25,0,25,50,75,100],default=[-100,0,100])
    scen_wind=st.number_input("Wind generation for these scenarios (MW)",min_value=0.0,value=float(n_wtg*p_wtg),step=1.0)
    scenarios=poi_scenarios(scen_wind,scen_bess,wind_loss_pct_in/100,bess_loss_pct_in/100,aux_mw_in,poi_export,poi_import)
    st.dataframe(scenarios,use_container_width=True,hide_index=True)
    fig=px.bar(scenarios,x="BESS at MV (+discharge/-charge MW)",y="Net POI (+export) MW",color="Within POI limits?",title="Net POI exchange by BESS operating setpoint")
    st.plotly_chart(fig,use_container_width=True)

with tabs[4]:
    st.subheader("Operational / financial analysis MVP")
    st.write("Upload time-series wind availability and market price data. This release uses a transparent heuristic dispatch rule, not a guaranteed revenue optimizer or market bidding model.")
    uploaded_ops=st.file_uploader("Upload CSV/XLSX with timestamp, wind MW and price columns",type=["csv","xlsx"],key="ops_upload")
    if uploaded_ops:
        try:
            ops_df=read_tabular_upload(uploaded_ops)
            st.dataframe(ops_df.head(10),use_container_width=True)
            cols=list(ops_df.columns)
            timestamp_col=st.selectbox("Timestamp column (optional)",["<row order>"]+cols)
            wind_col=st.selectbox("Wind availability column (MW)",cols)
            price_col=st.selectbox("Price column",cols)
            rte=st.slider("BESS round-trip efficiency (assumption)",0.50,1.00,0.88,0.01)
            initial_soc=st.number_input("Initial SOC (MWh)",min_value=0.0,max_value=float(max(e_bess,0.01)),value=float(e_bess*0.5),step=1.0)
            capture=st.checkbox("Prioritize capture of wind above POI export cap",value=True)
            op_input=ops_df.rename(columns={wind_col:"wind_mw",price_col:"price"})
            if timestamp_col!="<row order>":
                op_input=op_input.rename(columns={timestamp_col:"timestamp"})
            if st.button("Run dispatch screening"):
                dispatch=optimize_dispatch(op_input,"wind_mw","price",n_wtg*p_wtg,p_bess,e_bess,rte,initial_soc,poi_export,poi_import,capture)
                st.session_state["dispatch_result"]=dispatch
                total_export=dispatch["Net POI (MW)"].sum()*dispatch["Interval (h)"].iloc[0]
                st.metric("Net POI energy (MWh, interval-weighted)",f"{total_export:,.1f}")
                st.plotly_chart(px.line(dispatch,x="timestamp",y=["Wind available (MW)","Net POI (MW)","BESS power (+discharge/-charge MW)"],title="Dispatch screening"),use_container_width=True)
                st.plotly_chart(px.line(dispatch,x="timestamp",y="SOC (MWh)",title="BESS SOC trajectory"),use_container_width=True)
                st.dataframe(dispatch,use_container_width=True)
        except Exception as e:
            st.error(f"Could not read/run the uploaded data: {e}")
    else:
        st.info("No operational data uploaded. No generation or price data are fabricated.")
    if "dispatch_result" in st.session_state:
        st.download_button("Download dispatch results CSV",st.session_state["dispatch_result"].to_csv(index=False).encode("utf-8"),"dispatch_results.csv","text/csv")

with tabs[5]:
    st.subheader("Upload and inspect engineering workbooks")
    benchmark_upload=st.file_uploader("Upload the existing Wind+BESS calculation workbook",type=["xlsx"],key="benchmark_upload")
    if benchmark_upload:
        try:
            benchmark=extract_benchmark_workbook(benchmark_upload)
            st.write("Workbook sheets:",", ".join(benchmark["sheet_names"]))
            sheet_pick=st.selectbox("Inspect sheet",benchmark["sheet_names"])
            st.dataframe(benchmark["sheets"][sheet_pick],use_container_width=True)
        except Exception as e:
            st.error(f"Workbook could not be inspected: {e}")
    st.markdown("**Included benchmark reference**")
    st.write("The included reference workbook is `data/Calc_Workbook_Wind_BESS_115kV_P0.xlsx`. It is a reference only; the app's calculations are independently implemented and do not execute Excel formulas.")
    sld_path=Path(__file__).parent/"data"/"A_Overall_SLD.svg"
    if sld_path.exists():
        st.download_button("Download benchmark SLD (SVG)",sld_path.read_bytes(),"A_Overall_SLD.svg","image/svg+xml")

with tabs[6]:
    st.subheader("Validation and export")
    checks=check_project(int(n_wtg),feeder_counts,p_wtg,p_bess,int(n_bess_feeders),poi_export,poi_import,gsu_mva)
    st.dataframe(checks,use_container_width=True,hide_index=True)
    if not cable_checks.empty:
        st.markdown("**Cable checks / open items**")
        st.dataframe(cable_checks,use_container_width=True,hide_index=True)
    assumptions=pd.DataFrame([
        {"Parameter":"WTG PF","Value":pf_wtg,"Status":"Assumption unless GE Vernova P-Q chart confirms"},
        {"Parameter":"Minimum voltage pu","Value":voltage_min,"Status":"Screening assumption; confirm load flow/utility voltage schedule"},
        {"Parameter":"POI PF","Value":poi_pf,"Status":"Confirm applicable interconnection requirement"},
        {"Parameter":"GSU rating","Value":f"{gsu_mva} MVA","Status":gsu_status},
        {"Parameter":"Cable lengths","Value":f"Home-run={home_run_km} km; inter-WTG={inter_wtg_km} km","Status":"Benchmark illustrative values" if mode=="Load included benchmark case" else "User input; confirm against site routing"},
        {"Parameter":"BESS feeder allocation","Value":f"{n_bess_feeders} feeders equally allocated","Status":"Replace with actual PCS/MVT grouping"},
        {"Parameter":"Cable library","Value":"Values displayed in Wind Collector tab","Status":"Screening only; validate with manufacturer/installation study"},
    ])
    project_info={"Project":project_name,"Wind MW":n_wtg*p_wtg,"BESS MW":p_bess,"BESS MWh":e_bess,"POI kV":v_hv,"MV kV":v_mv,"Status":"PRELIMINARY ENGINEERING — NOT FOR CONSTRUCTION"}
    sheets={"WTG Summary":pd.DataFrame([{"Parameter":k,"Value":v} for k,v in summary.items()]),
            "Wind Feeders":pd.DataFrame([feeder_summary(f"WF-{i+1:02d}",c,p_wtg,pf_wtg,v_mv,voltage_min) for i,c in enumerate(feeder_counts) if c>0]),
            "Wind Cable Sections":sections,
            "BESS Feeders":bess_table,
            "GSU Summary":pd.DataFrame([{"Parameter":k,"Value":v} for k,v in gsu_base.items()]),
            "GSU Voltage Cases":gsu_cases,
            "POI Scenarios":scenarios,
            "Validation":checks,
            "Assumptions":assumptions}
    xlsx_bytes=workbook_bytes(sheets,project_info)
    st.download_button("Download calculation workbook (XLSX)",xlsx_bytes,"Wind_BESS_Engineering_Workbench_Results.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    pdf_tables={"WTG Summary":pd.DataFrame([{"Parameter":k,"Value":v} for k,v in summary.items()]),
                "Wind Feeders":pd.DataFrame([feeder_summary(f"WF-{i+1:02d}",c,p_wtg,pf_wtg,v_mv,voltage_min) for i,c in enumerate(feeder_counts) if c>0]),
                "BESS Feeders":bess_table,
                "GSU Summary":pd.DataFrame([{"Parameter":k,"Value":v} for k,v in gsu_base.items()]),
                "POI Scenarios":scenarios,
                "Assumptions":assumptions}
    pdf_bytes=build_preliminary_pdf(project_info,pdf_tables,checks)
    st.download_button("Download preliminary summary report (PDF)",pdf_bytes,"Wind_BESS_Engineering_Workbench_Preliminary_Report.pdf","application/pdf")
    st.download_button("Download assumptions register (CSV)",assumptions.to_csv(index=False).encode("utf-8"),"assumptions_open_items.csv","text/csv")
    st.caption("The exports contain calculated values and traceable input/result tables. They are not a signed design package.")

