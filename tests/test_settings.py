import sys
import unittest
from PyQt5.QtWidgets import QApplication
from speedview.models.settings import Settings
from speedview.ui.settings_dialog import SettingsDialog
from speedview.controllers.network_controller import NetworkController
from speedview.utils.svg_utils import update_svg_speed, update_test_network_svg, update_floating_svg
from speedview.ui.resources.svg_templates import MAIN_SVG_TEMPLATE, TEST_NETWORK_SVG, FLOATING_SVG_TEMPLATE


class TestSettingsAndDetection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication(sys.argv)

    def test_default_interface_skips_loopback(self):
        settings = Settings()
        self.assertNotEqual(settings.selected_interface, "lo")

    def test_settings_dialog_selects_interface_by_data(self):
        settings = Settings()
        dialog = SettingsDialog(settings=settings)
        if settings.selected_interface:
            selected_data = dialog.network_interface_combo.currentData()
            self.assertEqual(selected_data, settings.selected_interface)
        dialog.close()

    def test_real_interface_detection_returns_structured_data(self):
        nc = NetworkController()
        details = nc.get_interface_details(connected=True)
        self.assertIn("connection_type", details)
        self.assertIn("ipv4", details)
        self.assertIn("link_speed_mbps", details)
        conn_type, detail = nc.get_connection_info()
        self.assertIsInstance(conn_type, str)
        self.assertIsInstance(detail, str)

    def test_svg_updates_in_memory(self):
        main_svg = update_svg_speed(MAIN_SVG_TEMPLATE, speed=25.0, max_speed=100, speed_unit="Mbps")
        self.assertIn("25.00", main_svg)
        self.assertIn("Mbps", main_svg)

        test_svg = update_test_network_svg(TEST_NETWORK_SVG, "Test Complete!", 42.5, 11.25)
        self.assertIn("42.50 Mbps", test_svg)
        self.assertIn("11.25 Mbps", test_svg)
        self.assertIn("Test Complete!", test_svg)

        float_svg = update_floating_svg(FLOATING_SVG_TEMPLATE, 12.3, 100, "Ethernet", "1000 Mbps")
        self.assertIn("12.3", float_svg)
        self.assertIn("Ethernet", float_svg)
        self.assertIn("1000 Mbps", float_svg)


if __name__ == '__main__':
    unittest.main()
