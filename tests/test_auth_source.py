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

    def test_auth_requires_allowlist(self):
        auth = Path(__file__).resolve().parents[1] / "wind_bess" / "auth.py"
        source = auth.read_text(encoding="utf-8")
        self.assertIn("st.user.is_logged_in", source)
        self.assertIn("allowed_emails", source)
        self.assertIn("st.stop()", source)

if __name__ == "__main__":
    unittest.main()
