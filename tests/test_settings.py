import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from PyQt5.QtWidgets import QApplication
from speedview.models.settings import Settings
from speedview.models.data_usage import DataUsageTracker, format_bytes
from speedview.ui.settings_dialog import SettingsDialog
from speedview.ui.data_usage_dialog import DataUsageDialog
from speedview.controllers.network_controller import NetworkController
from speedview.utils.svg_utils import (
    update_svg_speed,
    update_svg_ping,
    update_test_network_svg,
    update_floating_svg,
    update_data_usage_svg,
)
from speedview.ui.resources.svg_templates import (
    MAIN_SVG_TEMPLATE,
    TEST_NETWORK_SVG,
    FLOATING_SVG_TEMPLATE,
    DATA_USAGE_SVG_TEMPLATE,
)


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
        self.assertIn("USAGE", MAIN_SVG_TEMPLATE)
        self.assertNotIn("HISTORY", MAIN_SVG_TEMPLATE)
        self.assertIn('id="pingBadge"', MAIN_SVG_TEMPLATE)
        self.assertIn('M19.4 15', MAIN_SVG_TEMPLATE)  # Gear cogwheel icon path

        main_svg = update_svg_speed(MAIN_SVG_TEMPLATE, speed=25.0, max_speed=100, speed_unit="Mbps")
        self.assertIn("25.00", main_svg)
        self.assertIn("Mbps", main_svg)

        ping_svg = update_svg_ping(main_svg, 24)
        self.assertIn("24 ms", ping_svg)
        ping_off_svg = update_svg_ping(main_svg, None)
        self.assertIn("-- ms", ping_off_svg)

        test_svg = update_test_network_svg(TEST_NETWORK_SVG, "Test Complete!", 42.5, 11.25)
        self.assertIn("42.50 Mbps", test_svg)
        self.assertIn("11.25 Mbps", test_svg)
        self.assertIn("Test Complete!", test_svg)

        float_svg = update_floating_svg(FLOATING_SVG_TEMPLATE, 12.3, 100)
        self.assertIn("12.3", float_svg)
        self.assertIn('id="signalBars"', float_svg)
        self.assertNotIn('id="connectionType"', float_svg)
        self.assertIn('fill-opacity="0.52"', float_svg)

    def test_data_usage_tracker_and_svg_dialog(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "usage.db")
            tracker = DataUsageTracker(db_path=db_path)
            tracker.record_traffic(1024 * 1024, 512 * 1024)

            daily_total, daily_rows = tracker.get_daily_usage()
            monthly_total, monthly_rows = tracker.get_monthly_usage()
            self.assertEqual(daily_total, 1536 * 1024)
            self.assertEqual(monthly_total, 1536 * 1024)
            self.assertGreaterEqual(len(daily_rows), 1)
            self.assertIn("app", daily_rows[0])
            self.assertIn("bytes", daily_rows[0])
            self.assertIn("date", daily_rows[0])

            svg_out = update_data_usage_svg(
                DATA_USAGE_SVG_TEMPLATE,
                format_bytes(daily_total),
                format_bytes(monthly_total),
                daily_rows,
                mode="daily",
            )
            self.assertIn("1.50 MB", svg_out)
            self.assertIn(daily_rows[0]["app"][:10], svg_out)

            dlg = DataUsageDialog(tracker=tracker)
            dlg.show()
            self.assertTrue(dlg.isVisible())
            dlg.close()

    def test_restore_defaults_resets_values(self):
        settings = Settings()
        settings.max_speed = 999
        settings.speed_unit = "Kbps"
        settings.show_upload_speed = True
        settings.restore_defaults()
        self.assertEqual(settings.max_speed, 100)
        self.assertEqual(settings.speed_unit, "Mbps")
        self.assertFalse(settings.show_upload_speed)

    def test_system_tray_tooltip_sync(self):
        from PyQt5.QtWidgets import QWidget
        from speedview.ui.system_tray import SystemTray

        class StubMain(QWidget):
            def __init__(self):
                super().__init__()
                self.settings = Settings()
                self.network_controller = NetworkController(selected_interface="eth1")
            def toggle_float_mode(self): pass
            def open_data_usage(self): pass
            def open_settings(self): pass
            def test_network(self): pass

        main = StubMain()
        main.settings.show_upload_speed = True
        main.settings.speed_unit = "Mbps"
        main.settings.selected_interface = "eth1"
        main.network_controller.connection_status = "Connected"

        tray = SystemTray(main)
        tray.update_tray_icon(12.5)
        tip = tray.tray_icon.toolTip()
        self.assertIn("Upload: 12.50 Mbps", tip)
        self.assertIn("Connected (eth1)", tip)
        tray.hide()
        main.close()

    def test_measure_file_speed_realtime_metrics(self):
        import threading
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        payload = b"A" * (512 * 1024)

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                _ = self.rfile.read(length)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")

            def log_message(self, format, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            nc = NetworkController()
            progress_events = []
            dl, ul = nc.measure_file_speed(
                download_urls=[f"http://127.0.0.1:{port}/test.bin"],
                upload_urls=[f"http://127.0.0.1:{port}/upload"],
                upload_size_bytes=256 * 1024,
                progress_callback=lambda s, d, u: progress_events.append((s, d, u)),
            )
            self.assertGreater(dl, 0.0)
            self.assertGreater(ul, 0.0)
            self.assertGreaterEqual(len(progress_events), 2)
        finally:
            server.shutdown()
            server.server_close()

    def test_window_lifecycle_and_settings_theme(self):
        from PyQt5.QtCore import Qt
        from speedview.ui.main_window import MainWindow

        class DummyTray:
            def __init__(self, *args, **kwargs):
                self.shown = False
            def show(self):
                self.shown = True
            def hide(self):
                self.shown = False
            def update_tray_icon(self, *args, **kwargs):
                pass

        settings = Settings()
        settings.start_minimized = False
        settings.is_floating = False

        mw = MainWindow(settings=settings)
        mw.tray = DummyTray()
        mw.show()

        # 1. Minimize -> hides main window to tray
        mw.minimize_to_tray()
        self.assertFalse(mw.isVisible())
        self.assertTrue(mw.tray.shown)

        # 2. Close MainWindow -> opens compact transparent Float widget (136x40) in corner and hides MainWindow
        mw.show()
        mw.close()
        self.assertIsNotNone(mw.floating_window)
        self.assertEqual((mw.floating_window.width(), mw.floating_window.height()), (136, 40))
        self.assertTrue(mw.floating_window.testAttribute(Qt.WA_TranslucentBackground))
        self.assertLess(mw.floating_window.windowOpacity(), 1.0)
        avail = self._app.primaryScreen().availableGeometry()
        self.assertGreaterEqual(mw.floating_window.x(), avail.right() - 136 - 40)
        self.assertGreaterEqual(mw.floating_window.y(), avail.bottom() - 40 - 40)
        self.assertFalse(mw.isVisible())

        # 3. Close Float widget -> stays minimized in tray (background)
        mw.floating_window.close()
        self.assertIsNone(mw.floating_window)
        self.assertFalse(mw.isVisible())

        # 4. Usage button -> opens DataUsageDialog and hides MainWindow; closing DataUsageDialog opens Float!
        mw.show()
        mw.open_data_usage(close_main=True)
        self.assertFalse(mw.isVisible())
        self.assertIsNotNone(mw._usage_dialog)
        self.assertTrue(mw._usage_dialog.isVisible())
        mw._usage_dialog.close()
        self.assertIsNotNone(mw.floating_window)
        mw.floating_window.close()

        # 5. Closing TestNetworkDialog also opens Float widget
        mw.show()
        mw.test_network()
        self.assertIsNotNone(mw._test_dialog)
        mw._test_dialog.close()
        self.assertIsNotNone(mw.floating_window)
        self.assertFalse(mw.isVisible())
        mw.floating_window.close()

        # 6. SettingsDialog does NOT inherit MainWindow transparent background & has start_on_startup checkbox
        dlg = SettingsDialog(parent=mw, settings=settings)
        self.assertFalse(dlg.testAttribute(Qt.WA_TranslucentBackground))
        self.assertIn("#0B1220", dlg.styleSheet())
        self.assertTrue(hasattr(dlg, "start_on_startup_checkbox"))
        dlg.close()

        mw.force_quit()

    def test_start_on_startup_registration(self):
        from speedview.config.windows import apply_startup_setting

        with tempfile.TemporaryDirectory() as tmpdir:
            old_xdg = os.environ.get("XDG_CONFIG_HOME")
            os.environ["XDG_CONFIG_HOME"] = tmpdir
            try:
                # This test verifies Linux/XDG behavior regardless of the CI runner OS.
                with patch("speedview.config.windows.platform.system", return_value="Linux"):
                    self.assertTrue(apply_startup_setting(True))
                    desktop_path = os.path.join(tmpdir, "autostart", "speedview.desktop")
                    self.assertTrue(os.path.exists(desktop_path))
                    self.assertTrue(apply_startup_setting(False))
                    self.assertFalse(os.path.exists(desktop_path))
            finally:
                if old_xdg is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = old_xdg


if __name__ == '__main__':
    unittest.main()
