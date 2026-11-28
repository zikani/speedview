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

        mw.minimize_to_tray()
        self.assertFalse(mw.isVisible())
        self.assertTrue(mw.tray.shown)

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

        mw.floating_window.close()
        self.assertIsNone(mw.floating_window)
        self.assertFalse(mw.isVisible())

        mw.show()
        mw.open_data_usage(close_main=True)
        self.assertFalse(mw.isVisible())
        self.assertIsNotNone(mw._usage_dialog)
        self.assertTrue(mw._usage_dialog.isVisible())
        mw._usage_dialog.close()
        self.assertIsNotNone(mw.floating_window)
        mw.floating_window.close()

        mw.show()
        mw.test_network()
        self.assertIsNotNone(mw._test_dialog)
        mw._test_dialog.close()
        self.assertIsNotNone(mw.floating_window)
        self.assertFalse(mw.isVisible())
        mw.floating_window.close()

        dlg = SettingsDialog(parent=mw, settings=settings)
        self.assertFalse(dlg.testAttribute(Qt.WA_TranslucentBackground))
        self.assertIn("#0B1220", dlg.styleSheet())
        self.assertTrue(hasattr(dlg, "start_on_startup_checkbox"))
        dlg.close()

        mw.force_quit()
        mw.deleteLater()
        self._app.processEvents()

    def test_start_on_startup_registration(self):
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        import speedview.config.windows as win_cfg

        with tempfile.TemporaryDirectory() as tmpdir:
            old_xdg = os.environ.get("XDG_CONFIG_HOME")
            os.environ["XDG_CONFIG_HOME"] = tmpdir
            try:
                # Verify Linux/XDG behavior regardless of the CI runner OS.
                with patch("speedview.config.windows.platform.system", return_value="Linux"):
                    self.assertTrue(win_cfg.apply_startup_setting(True))
                    desktop_path = os.path.join(tmpdir, "autostart", "speedview.desktop")
                    self.assertTrue(os.path.exists(desktop_path))
                    self.assertTrue(win_cfg.apply_startup_setting(False))
                    self.assertFalse(os.path.exists(desktop_path))

                # Verify Windows Registry branch cleanly without modifying host registry.
                fake_winreg = SimpleNamespace(
                    HKEY_CURRENT_USER="HKCU",
                    KEY_SET_VALUE=2,
                    REG_SZ=1,
                    CreateKeyEx=MagicMock(return_value="key_handle"),
                    SetValueEx=MagicMock(),
                    DeleteValue=MagicMock(),
                )
                with patch("speedview.config.windows.platform.system", return_value="Windows"), \
                     patch.object(win_cfg, "winreg", fake_winreg):
                    self.assertTrue(win_cfg.apply_startup_setting(True))
                    fake_winreg.SetValueEx.assert_called_once()
                    self.assertTrue(win_cfg.apply_startup_setting(False))
                    fake_winreg.DeleteValue.assert_called_once()
            finally:
                if old_xdg is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = old_xdg

    def test_auto_updater_cooldown_platform_selection_and_zip_replace(self):
        import json
        import shutil
        import threading
        import time
        import zipfile
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from speedview.update.updater import UpdateChecker

        settings = Settings()
        # Within 3 days -> should skip API unless forced
        settings.last_update_check = time.time() - 60
        with patch.object(settings, "save"):
            checker = UpdateChecker(settings=settings)
            self.assertFalse(checker.should_check_for_updates(force=False))
            self.assertTrue(checker.should_check_for_updates(force=True))

            # Expired (>= 3 days) -> should allow check
            settings.last_update_check = time.time() - (3 * 24 * 60 * 60 + 5)
            self.assertTrue(checker.should_check_for_updates(force=False))

            # Platform asset selection should prefer OS-matching .zip archives
            assets = [
                {"name": "SpeedView-windows-x64.exe", "browser_download_url": "https://example/win.exe"},
                {"name": "SpeedView-windows-x64.zip", "browser_download_url": "https://example/win.zip"},
                {"name": "SpeedView-macos.zip", "browser_download_url": "https://example/mac.zip"},
                {"name": "SpeedView-linux-x64.tar.gz", "browser_download_url": "https://example/lin.tar.gz"},
                {"name": "SpeedView-linux-x64.zip", "browser_download_url": "https://example/lin.zip"},
            ]
            self.assertEqual(checker._select_asset_for_platform(assets, "Windows")[1], "SpeedView-windows-x64.zip")
            self.assertEqual(checker._select_asset_for_platform(assets, "Darwin")[1], "SpeedView-macos.zip")
            self.assertEqual(checker._select_asset_for_platform(assets, "Linux")[1], "SpeedView-linux-x64.zip")

            # Serve mock GitHub Release JSON + .zip payload over local HTTP
            with tempfile.TemporaryDirectory() as workdir:
                zip_bytes_path = os.path.join(workdir, "SpeedView-linux-x64.zip")
                with zipfile.ZipFile(zip_bytes_path, "w") as zf:
                    zf.writestr("SpeedView-linux-x64", b"NEW_BINARY_V99")
                with open(zip_bytes_path, "rb") as f:
                    zip_payload = f.read()

                class ReleaseHandler(BaseHTTPRequestHandler):
                    def do_GET(self):
                        if self.path == "/release":
                            body = json.dumps({
                                "tag_name": "v9.9.9",
                                "body": "Auto update test release",
                                "html_url": "https://example/releases/v9.9.9",
                                "assets": [
                                    {
                                        "name": "SpeedView-linux-x64.zip",
                                        "browser_download_url": f"http://127.0.0.1:{port}/SpeedView-linux-x64.zip",
                                    },
                                    {
                                        "name": "SpeedView-windows-x64.zip",
                                        "browser_download_url": f"http://127.0.0.1:{port}/SpeedView-windows-x64.zip",
                                    },
                                    {
                                        "name": "SpeedView-macos.zip",
                                        "browser_download_url": f"http://127.0.0.1:{port}/SpeedView-macos.zip",
                                    },
                                ],
                            }).encode("utf-8")
                            self.send_response(200)
                            self.send_header("Content-Type", "application/json")
                            self.send_header("Content-Length", str(len(body)))
                            self.end_headers()
                            self.wfile.write(body)
                        elif self.path.endswith(".zip"):
                            self.send_response(200)
                            self.send_header("Content-Length", str(len(zip_payload)))
                            self.end_headers()
                            self.wfile.write(zip_payload)
                        else:
                            self.send_response(404)
                            self.end_headers()

                    def log_message(self, format, *args):
                        pass

                server = ThreadingHTTPServer(("127.0.0.1", 0), ReleaseHandler)
                port = server.server_address[1]
                srv_thread = threading.Thread(target=server.serve_forever, daemon=True)
                srv_thread.start()
                try:
                    settings.update_url = f"http://127.0.0.1:{port}/release"
                    settings.last_update_check = 0.0
                    up = UpdateChecker(settings=settings)
                    self.assertTrue(up.check_for_updates(force=False))
                    self.assertEqual(up.latest_version, "9.9.9")
                    self.assertGreater(settings.last_update_check, 0.0)
                    # Second immediate non-forced check must be skipped by 3-day limit
                    self.assertFalse(up.check_for_updates(force=False))

                    downloaded = up.download_update()
                    self.assertIsNotNone(downloaded)
                    self.assertTrue(os.path.exists(downloaded))

                    target_bin = os.path.join(workdir, "SpeedView-linux-x64")
                    with open(target_bin, "wb") as f:
                        f.write(b"OLD_BINARY_V1")

                    # Execute generated POSIX helper script when testing on POSIX (or validate .bat generation)
                    if os.name == "posix":
                        self.assertTrue(
                            up.install_update(
                                downloaded,
                                target_path=target_bin,
                                restart=False,
                                launch_script=True,
                                wait_pid=0,
                            )
                        )
                        deadline = time.time() + 5.0
                        replaced = False
                        while time.time() < deadline:
                            if os.path.exists(target_bin):
                                with open(target_bin, "rb") as f:
                                    if f.read() == b"NEW_BINARY_V99":
                                        replaced = True
                                        break
                            time.sleep(0.05)
                        self.assertTrue(replaced)
                        if up.last_helper_process is not None:
                            up.last_helper_process.wait(timeout=5)
                        self.assertFalse(os.path.exists(up.staged_dir))
                    else:
                        self.assertTrue(
                            up.install_update(
                                downloaded,
                                target_path=target_bin,
                                restart=False,
                                launch_script=False,
                                wait_pid=0,
                            )
                        )
                        self.assertTrue(os.path.exists(up.last_helper_script))
                        os.remove(up.last_helper_script)
                        shutil.rmtree(up.staged_dir, ignore_errors=True)
                finally:
                    server.shutdown()
                    server.server_close()


if __name__ == '__main__':
    unittest.main()
