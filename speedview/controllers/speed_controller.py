import logging
import psutil
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
import threading
import speedtest
import subprocess

class SpeedController(QObject):
    """Controls network speed measurement and calculations"""
    
    speed_updated = pyqtSignal(float, float)  # Download speed, Upload speed
    
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        
        self.prev_bytes_recv = 0
        self.prev_bytes_sent = 0
        self.last_download_speed = 0
        self.last_upload_speed = 0
        self.test_in_progress = False  # Prevent concurrent speed tests
        
        # Setup timer for periodic updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_speed)
        self.timer.start(int(self.settings.update_interval * 2000))  # Increased interval to reduce CPU usage
    
    def update_speed(self):
        """Update network speed measurements"""
        try:
            stats = psutil.net_io_counters(pernic=True)
            
            # If interface is selected, use that specific one
            if self.settings.selected_interface and self.settings.selected_interface in stats:
                net_io = stats[self.settings.selected_interface]
            else:
                # Otherwise use the default overall counters
                net_io = psutil.net_io_counters()
            
            bytes_recv = net_io.bytes_recv
            bytes_sent = net_io.bytes_sent
            
            if self.prev_bytes_recv > 0:
                # Calculate speeds in Mbps
                download_speed = ((bytes_recv - self.prev_bytes_recv) * 8) / (1024 * 1024 * self.settings.update_interval)
                upload_speed = ((bytes_sent - self.prev_bytes_sent) * 8) / (1024 * 1024 * self.settings.update_interval)
                logging.info(f"Periodic speed update: download={download_speed:.2f} Mbps, upload={upload_speed:.2f} Mbps")
                # Emit the signal with updated speeds
                self.speed_updated.emit(download_speed, upload_speed)
                # Store for later use
                self.last_download_speed = download_speed
                self.last_upload_speed = upload_speed
            
            # Store the current byte counts for next calculation
            self.prev_bytes_recv = bytes_recv
            self.prev_bytes_sent = bytes_sent
        except Exception as e:
            logging.exception(f"Error updating speed: {e}")
    
    def set_update_interval(self, interval):
        """Change the update interval"""
        self.settings.update_interval = interval
        self.timer.setInterval(int(interval * 1000))
    
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
        thread = threading.Thread(target=self._speed_test_thread)
        thread.daemon = True
        thread.start()

    def _speed_test_thread(self):
        """Thread to run network speed test"""
        try:
            logging.info("Running network speed test...")
            st = speedtest.Speedtest()
            st.get_best_server()
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            upload_speed = st.upload() / 1_000_000      # Convert to Mbps
            logging.info(f"Speed test complete: download={download_speed:.2f} Mbps, upload={upload_speed:.2f} Mbps")
            self.speed_updated.emit(download_speed, upload_speed)
        except Exception as e:
            logging.exception(f"Speed test failed: {e}")
            self.speed_updated.emit(0, 0)
        finally:
            self.test_in_progress = False

    def toggle_network_adapter(self, interface_name, enable=True):
        """Enable or disable a network adapter"""
        try:
            if enable:
                subprocess.call(["netsh", "interface", "set", "interface", interface_name, "enable"])
            else:
                subprocess.call(["netsh", "interface", "set", "interface", interface_name, "disable"])
        except Exception as e:
            print(f"Error toggling network adapter: {e}")