import unittest
from pathlib import Path

class TestAuthGateSource(unittest.TestCase):
    def test_app_calls_auth_gate_before_dashboard(self):
        app = Path(__file__).resolve().parents[1] / "app.py"
        source = app.read_text(encoding="utf-8")
        self.assertIn("enforce_login()", source)
        self.assertLess(source.index("enforce_login()"), source.index('st.title("Wind + BESS Engineering Workbench")'))

    def test_gsu_impedance_is_passed_by_keyword(self):
        app = Path(__file__).resolve().parents[1] / "app.py"
        source = app.read_text(encoding="utf-8")
        self.assertIn("v_hv,v_mv,z_pu=z_pu_pct/100 if z_pu_pct>0 else None", source)

    def test_poi_chart_uses_existing_dataframe_column(self):
        app = Path(__file__).resolve().parents[1] / "app.py"
        source = app.read_text(encoding="utf-8")
        calculations = (Path(__file__).resolve().parents[1] / "wind_bess" / "calculations.py").read_text(encoding="utf-8")
        self.assertIn('x="BESS at MV (+discharge/-charge) (MW)"', source)
        self.assertIn('"BESS at MV (+discharge/-charge) (MW)"', calculations)
        self.assertIn('if scenarios.empty:', source)

    def test_auth_uses_email_allowlist_and_form(self):
        auth = Path(__file__).resolve().parents[1] / "wind_bess" / "auth.py"
        source = auth.read_text(encoding="utf-8")
        self.assertIn('st.text_input("Company email address"', source)
        self.assertIn('st.form_submit_button("Continue"', source)
        self.assertIn('"allowed_emails"', source)
        self.assertIn('normalized not in allowed', source)
        self.assertIn('st.stop()', source)

    def test_sld_generator_is_wired_into_app(self):
        app = Path(__file__).resolve().parents[1] / "app.py"
        source = app.read_text(encoding="utf-8")
        self.assertIn("from wind_bess.sld import generate_wind_bess_sld", source)
        self.assertIn('"SLD Generator"', source)
        self.assertIn("generate_wind_bess_sld(", source)

    def test_auth_discloses_email_only_limitation(self):
        auth = Path(__file__).resolve().parents[1] / "wind_bess" / "auth.py"
        source = auth.read_text(encoding="utf-8")
        self.assertIn("does not verify that you own it", source)

if __name__ == "__main__":
    unittest.main()
