import unittest
import math
import pandas as pd
from wind_bess.calculations import (
    apparent_power_mva, reactive_power_mvar, three_phase_current_a,
    wtg_summary, feeder_summary, gsu_summary, bess_feeder_summary,
    cable_section_calculation, poi_scenarios
)
from wind_bess.validation import check_project

class TestBenchmarks(unittest.TestCase):
    def test_wind_capacity(self):
        self.assertAlmostEqual(27*3.8, 102.6, places=6)

    def test_wtg_mva_and_current(self):
        s=apparent_power_mva(3.8,0.95)
        self.assertAlmostEqual(s,4.0,places=9)
        self.assertAlmostEqual(three_phase_current_a(s,0.69),3347.5,delta=2.0)
        self.assertAlmostEqual(three_phase_current_a(s,34.5),66.94,delta=0.1)

    def test_wind_feeder_currents(self):
        f7=feeder_summary("WF-01",7,3.8,0.95,34.5,0.95)
        f6=feeder_summary("WF-04",6,3.8,0.95,34.5,0.95)
        self.assertAlmostEqual(f7["Current @1.0 pu (A)"],468.6,delta=0.2)
        self.assertAlmostEqual(f7["Current @minimum voltage (A)"],493.2,delta=0.3)
        self.assertAlmostEqual(f6["Current @1.0 pu (A)"],401.6,delta=0.2)

    def test_gsu(self):
        base,cases=gsu_summary(100,0.95,125,115,34.5,[0.95,1.0,1.05],0.10)
        self.assertAlmostEqual(base["Required apparent power at POI (MVA)"],105.2631579,places=5)
        self.assertAlmostEqual(base["Required |Q| at POI (Mvar)"],32.8684,delta=0.01)
        self.assertAlmostEqual(base["GSU HV rated current (A)"],627.6,delta=0.2)
        self.assertAlmostEqual(base["GSU MV rated current (A)"],2091.8,delta=0.5)
        self.assertAlmostEqual(cases.iloc[0]["Equivalent MVA/current loading (MVA)"],110.8033,delta=0.01)

    def test_bess_feeder(self):
        b=bess_feeder_summary(100,4,0.95,34.5,0.95)
        self.assertAlmostEqual(b.iloc[0]["Current @1.0 pu (A)"],440.4,delta=0.2)
        self.assertAlmostEqual(b.iloc[0]["Current @minimum voltage (A)"],463.6,delta=0.3)

    def test_cable_calculation(self):
        result=cable_section_calculation(468.6,1.0,0.0754,0.1311,34.5,0.95)
        self.assertGreater(result["Voltage drop (%)"],0)
        self.assertGreater(result["Loss (kW)"],0)

    def test_poi_scenarios(self):
        df=poi_scenarios(102.6,[-100,0,100],0.015,0.015,1,100,100)
        self.assertEqual(len(df),3)
        self.assertFalse(bool(df.iloc[2]["Within POI limits?"])) # wind full + 100 MW discharge exceeds export cap

    def test_allocation_check(self):
        checks=check_project(27,[7,7,7,6],3.8,100,4,100,100,125)
        self.assertTrue((checks["Severity"]!="ERROR").all())
        checks_bad=check_project(27,[7,7,7,5],3.8,100,4,100,100,125)
        self.assertTrue((checks_bad["Severity"]=="ERROR").any())

if __name__ == "__main__":
    unittest.main()
