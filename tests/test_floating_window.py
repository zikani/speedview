import unittest
from PyQt5.QtWidgets import QApplication
from speedview.ui.floating_window import FloatingWindow
from speedview.controllers.speed_controller import SpeedController
from speedview.controllers.network_controller import NetworkController
from speedview.models.settings import Settings
import sys

class DummySignal:
    def connect(self, slot):
        # Accept connections but do nothing
        self._slot = slot

class DummySpeedController(SpeedController):
    def __init__(self):
        # Do not call super().__init__ to avoid timer setup
        self.last_download_speed = 42.0
        self.last_upload_speed = 24.0
        self.speed_updated = DummySignal()
    def get_current_speeds(self):
        return (self.last_download_speed, self.last_upload_speed)

class DummyNetworkController(NetworkController):
    def __init__(self):
        self._signal_strength = 3
        self._connection_type = "WiFi"
        self._band = "5GHz"
        self.connection_updated = DummySignal()
        # Add any other signals/attributes your UI expects
    @property
    def signal_strength(self):
        return self._signal_strength
    @signal_strength.setter
    def signal_strength(self, value):
        self._signal_strength = value
    @property
    def signal_strength(self):
        return self._signal_strength
    def get_connection_info(self):
        return (self._connection_type, self._band)
    # Methods to simulate network changes
    def set_network(self, signal_strength, connection_type, band):
        self._signal_strength = signal_strength
        self._connection_type = connection_type
        self._band = band

class TestFloatingWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_floating_window_display(self):
        settings = Settings()
        speed_controller = DummySpeedController()
        network_controller = DummyNetworkController()
        window = FloatingWindow(speed_controller, settings, network_controller)
        window.show()
        # Simulate update
        window.update_display()
        # Check window is visible and has correct title
        self.assertTrue(window.isVisible())
        self.assertEqual(window.windowTitle(), "SpeedView - Floating Mode")
        window.close()

    def test_floating_window_network_change(self):
        settings = Settings()
        speed_controller = DummySpeedController()
        network_controller = DummyNetworkController()
        window = FloatingWindow(speed_controller, settings, network_controller)
        window.show()
        # Initial display
        window.update_display()
        # Simulate network change
        network_controller.set_network(1, "Ethernet", "N/A")
        window.update_display()
        # No crash, window remains visible
        self.assertTrue(window.isVisible())
        window.close()

if __name__ == '__main__':
    unittest.main()
