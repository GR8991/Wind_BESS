import unittest
from wind_bess.sld import generate_wind_bess_sld

class TestSldGeneration(unittest.TestCase):
    def _make(self, counts=(7, 7, 7, 6)):
        return generate_wind_bess_sld(
            project_name="Test Wind BESS", n_wtg=sum(counts), p_wtg_mw=3.8,
            feeder_counts=list(counts), p_bess_mw=100, e_bess_mwh=200,
            n_bess_feeders=4, v_mv_kv=34.5, v_hv_kv=115, gsu_mva=125,
            poi_export_mw=100, poi_import_mw=50,
        )

    def test_sld_svg_contains_project_equipment_and_disclaimer(self):
        svg = self._make()
        self.assertTrue(svg.startswith('<svg'))
        self.assertIn('Test Wind BESS', svg)
        self.assertIn('34.5 kV WIND COLLECTOR BUS', svg)
        self.assertIn('GSU', svg)
        self.assertIn('POI / GRID', svg)
        self.assertIn('NOT FOR CONSTRUCTION', svg)
        self.assertIn('CB • TBD', svg)

    def test_invalid_feeder_allocation_is_rejected(self):
        with self.assertRaises(ValueError):
            generate_wind_bess_sld(
                project_name="Bad", n_wtg=10, p_wtg_mw=3.8, feeder_counts=[4, 4],
                p_bess_mw=10, e_bess_mwh=40, n_bess_feeders=2, v_mv_kv=34.5,
                v_hv_kv=115, gsu_mva=20, poi_export_mw=10, poi_import_mw=0,
            )

if __name__ == '__main__':
    unittest.main()
