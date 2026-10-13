# Initial benchmark case — source-derived inputs

Source files supplied in the conversation:
- `Calc_Workbook_Wind_BESS_115kV_P0.xlsx`
- `A_Overall_SLD.svg`

Values taken from the workbook's `Inputs`, `WTG`, `Feeder_Sections`, `BESS_Feeders`, `GSU_Sizing` and `POI_Scenarios` sheets:

| Parameter | Value | Source status |
|---|---:|---|
| WTG count | 27 | Frozen/client data in source workbook |
| WTG active power | 3.8 MW | Frozen/client data; exact model still TBC |
| LV voltage | 0.69 kV | Frozen/client data |
| MV collector voltage | 34.5 kV | Frozen/client data |
| POI voltage | 115 kV | Frozen/client data |
| Wind feeder allocation | 7 / 7 / 7 / 6 | Source workbook |
| BESS | 100 MW / 200 MWh | Source workbook/project basis |
| BESS feeders | 4 | Source workbook/project basis |
| POI export/import | 100 MW / 100 MW | Source workbook/project basis |
| WTG PF | 0.95 | Assumption / OEM P-Q capability confirmation needed |
| POI PF | 0.95 | Assumption / utility requirement confirmation needed |
| Minimum voltage | 0.95 pu | Screening assumption |
| GSU candidate | 125 MVA | Candidate only |
| GSU impedance | 10% | Screening assumption in source workbook |
| Illustrative home-run length | 5 km | Illustrative source-workbook assumption |
| Illustrative inter-WTG section length | 0.616 km | Illustrative source-workbook assumption |
| Wind/BESS loss assumptions | 1.5% each | Screening assumptions in source workbook |
| Auxiliary load | 1 MW | Screening assumption in source workbook |

The source workbook is Rev P0 and is copied for reference; its formulas are not used as the live calculation engine. The app re-computes supported quantities independently.
