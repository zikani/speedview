import logging
import platform
import subprocess
import threading
import psutil
from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class SpeedController(QObject):
    """Controls network speed measurement and calculations"""

    speed_updated = pyqtSignal(float, float)  # Download speed, Upload speed (Mbps)
    test_completed = pyqtSignal(float, float)  # Speed test download, upload (Mbps)
    bytes_transferred = pyqtSignal(int, int)  # delta_recv, delta_sent (bytes)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings

        self.prev_bytes_recv = 0
        self.prev_bytes_sent = 0
        self._last_interface = getattr(self.settings, "selected_interface", None)
        self.last_download_speed = 0.0
        self.last_upload_speed = 0.0
        self.test_in_progress = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_speed)
        interval_ms = max(100, int(float(getattr(self.settings, "update_interval", 1.0)) * 1000))
        self.timer.start(interval_ms)

    def update_speed(self):
        """Update network speed measurements"""
        try:
            stats = psutil.net_io_counters(pernic=True)
            selected = getattr(self.settings, "selected_interface", None)

            # Reset baseline counters if interface selection changed
            if selected != self._last_interface:
                self._last_interface = selected
                self.prev_bytes_recv = 0
                self.prev_bytes_sent = 0

            if selected and selected in stats:
                net_io = stats[selected]
            else:
                net_io = psutil.net_io_counters()

            if net_io is None:
                return

            bytes_recv = net_io.bytes_recv
            bytes_sent = net_io.bytes_sent

            interval = max(0.1, float(getattr(self.settings, "update_interval", 1.0)))

            if self.prev_bytes_recv > 0:
                delta_recv = max(0, bytes_recv - self.prev_bytes_recv)
                delta_sent = max(0, bytes_sent - self.prev_bytes_sent)
                download_speed = (delta_recv * 8) / (1024 * 1024 * interval)
                upload_speed = (delta_sent * 8) / (1024 * 1024 * interval)
                logging.info(
                    f"Periodic speed update ({selected or 'all'}): download={download_speed:.2f} Mbps, upload={upload_speed:.2f} Mbps"
                )
                self.last_download_speed = download_speed
                self.last_upload_speed = upload_speed
                self.speed_updated.emit(download_speed, upload_speed)
                if delta_recv > 0 or delta_sent > 0:
                    self.bytes_transferred.emit(delta_recv, delta_sent)

            self.prev_bytes_recv = bytes_recv
            self.prev_bytes_sent = bytes_sent
        except Exception as e:
            logging.exception(f"Error updating speed: {e}")

    def set_update_interval(self, interval):
        """Change the update interval"""
        self.settings.update_interval = interval
        self.timer.setInterval(max(100, int(float(interval) * 1000)))

    def get_current_speeds(self):
        """Get the most recently calculated speeds"""
        return self.last_download_speed, self.last_upload_speed

    def get_network_interfaces(self):
        """Get list of available network interfaces"""
        interfaces = []
        try:
            stats = psutil.net_if_stats()
            for interface in stats:
                interfaces.append(interface)
        except Exception as e:
            logging.exception(f"Error getting network interfaces: {e}")
        return interfaces

    def run_speed_test(self):
        """Start a speed test in a background thread"""
        if self.test_in_progress:
            logging.info("Speed test already in progress. Skipping new test.")
            return
        self.test_in_progress = True
        logging.info("Starting speed test thread...")
        thread = threading.Thread(target=self._speed_test_thread, daemon=True)
        thread.start()

    def _speed_test_thread(self):
        """Thread to run network speed test"""
        try:
            import speedtest
            logging.info("Running network speed test...")
            st = speedtest.Speedtest()
            st.get_best_server()
            download_speed = st.download() / 1_000_000
            upload_speed = st.upload() / 1_000_000
            logging.info(f"Speed test complete: download={download_speed:.2f} Mbps, upload={upload_speed:.2f} Mbps")
            self.test_completed.emit(download_speed, upload_speed)
        except Exception as e:
            logging.exception(f"Speed test failed: {e}")
            self.test_completed.emit(0.0, 0.0)
        finally:
            self.test_in_progress = False

    def toggle_network_adapter(self, interface_name, enable=True):
        """Enable or disable a network adapter"""
        try:
            system = platform.system()
            if system == "Windows":
                state = "enable" if enable else "disable"
                subprocess.call(["netsh", "interface", "set", "interface", interface_name, state])
            elif system == "Linux":
                state = "up" if enable else "down"
                subprocess.call(["ip", "link", "set", interface_name, state])
        except Exception as e:
            print(f"Error toggling network adapter: {e}")