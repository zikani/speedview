import unittest
from speedview.ui.main_window import MainWindow
from speedview.models.settings import Settings
from speedview.controllers.speed_controller import SpeedController
from speedview.controllers.network_controller import NetworkController
from PyQt5.QtWidgets import QApplication
import sys

class DummySignal:
    def connect(self, slot):
        # Accept connections but do nothing
        self._slot = slot

class DummySpeedController(SpeedController):
    def __init__(self):
        self.last_download_speed = 10.0
        self.last_upload_speed = 5.0
        self.speed_updated = DummySignal()
        self.test_completed = DummySignal()
    def get_current_speeds(self):
        return (self.last_download_speed, self.last_upload_speed)

class DummyNetworkController(NetworkController):
    def __init__(self):
        super().__init__()
        self.connection_status = "Connected"
        self._signal_strength = 3
        self.connection_updated = DummySignal()
        self.signal_strength_updated = DummySignal()
    @property
    def signal_strength(self):
        return self._signal_strength
    @signal_strength.setter
    def signal_strength(self, value):
        self._signal_strength = value
    def get_connection_info(self):
        return ("WiFi", "5GHz")

class DummySystemTray:
    def __init__(self, *args, **kwargs):
        pass
    def show(self):
        pass
    def update_icon(self, *args, **kwargs):
        pass

import speedview.ui.main_window
speedview.ui.main_window.SystemTray = DummySystemTray

class TestMainWindowButtons(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication(sys.argv)
    def setUp(self):
        self.settings = Settings()
        self.speed_controller = DummySpeedController()
        self.network_controller = DummyNetworkController()
        self.window = MainWindow(self.settings, self.speed_controller, self.network_controller)
        self.window.show()
    def test_svg_buttons_exist(self):
        # Just ensure the SVG loads and widget is present
        self.assertIsNotNone(self.window.svg_widget)
    def test_update_display_runs(self):
        # Should not raise
        self.window.update_display()
    # More UI interaction tests would require QTest and event simulation

if __name__ == '__main__':
    unittest.main()
