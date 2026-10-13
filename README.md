# Wind + BESS Engineering Workbench — Release 1 MVP

**Status:** preliminary engineering utility; not for construction, procurement, relay setting release, or utility compliance certification.

## What is included

- Modular Python calculations (`wind_bess/calculations.py`)
- Rule-based checks (`wind_bess/validation.py`)
- Streamlit interface (`app.py`)
- Wind WTG, radial collector feeder, cable screening, BESS feeder and GSU calculations
- POI operating scenarios with explicit loss/auxiliary assumptions
- CSV/XLSX time-series upload and transparent heuristic dispatch screening
- Excel export with result tables and assumptions register
- Preliminary PDF summary report export
- Independent unit tests
- Uploaded P0 calculation workbook and overall SLD SVG as benchmark references

## Windows setup

1. Extract the ZIP to a writable local folder, e.g. `C:\Wind_BESS_Engineering_Workbench`.
2. Install Python 3.11 or 3.12 from python.org and ensure the Python launcher (`py`) is available.
3. Double-click `run_app.bat`.
4. On first run, the script creates `.venv`, installs dependencies, and launches Streamlit.
5. If Windows Firewall asks about network access, the app is intended for local use; do not expose the port to a public network.

Manual setup in PowerShell:

```powershell
cd C:\Wind_BESS_Engineering_Workbench
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Unit tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Calculation conventions

- Power factor is entered as a positive magnitude from 0 to 1.
- Positive BESS power means discharge; negative means charging.
- Three-phase current: `I(A) = S(MVA) × 1000 / (sqrt(3) × V_LL(kV) × voltage_pu)`.
- Apparent power: `S(MVA) = abs(P(MW)) / PF`.
- Reactive power magnitude: `Q(Mvar) = abs(P(MW)) × tan(acos(PF))`.
- Three-phase cable loss screening: `3 × I² × R × L / 1000` kW where R is AC resistance in ohm/km and L is km.
- Cable voltage-drop screening uses `sqrt(3) × I × L × (R×PF + X×sinφ) / V_LL × 100`, with V in volts.
- Cable library values are screening values transcribed from the supplied P0 workbook; validate against actual cable manufacturer data and installation assumptions before use.
- The included benchmark mode uses illustrative cable lengths and assumed loss/auxiliary inputs. New project mode does not silently invent cable route lengths; zero lengths mean missing inputs and voltage drop/loss are not calculated.
- The operational module is a heuristic demonstration, not an optimized market bidding strategy. It requires validation before commercial use.

## Known MVP limitations / next release

1. Detailed cable thermal ampacity per IEC 60287 is not implemented as a full solver; the initial library is a screening lookup only.
2. Short-circuit, grounding, protection coordination, CT/VT sizing, arc-flash and relay-setting calculations are not final design functions.
3. The first dispatch method is heuristic, not MILP/LP optimization and does not model degradation, forecast uncertainty, ancillary services, tariff rules, or market settlement.
4. The app inspects user-uploaded Excel sheets but does not execute Excel formulas. Its calculations are independently coded.
5. No database/login/multi-user functions in Release 1 local MVP.
6. The uploaded SLD is included for reference only; the app does not claim to infer all electrical connectivity from the drawing.
7. All utility/OEM/site assumptions must be controlled in the project design basis.

## Benchmark files

- `data/Calc_Workbook_Wind_BESS_115kV_P0.xlsx`
- `data/A_Overall_SLD.svg`
- `reference/benchmark_basis.md`

## Design principle

Every output is a calculation aid, not a certificate. Mark confirmed inputs, assumptions, and open items separately. Do not turn missing OEM/utility data into a hidden default.
