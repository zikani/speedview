import socket
import platform
import subprocess
import re
import threading
from PyQt5.QtCore import QObject, pyqtSignal
import speedtest

class NetworkController(QObject):
    """Handles network connectivity and testing"""
    
    connection_updated = pyqtSignal(str, int)  # status, signal_strength
    speed_test_complete = pyqtSignal(float, float)  # download_speed, upload_speed
    speed_test_failed = pyqtSignal(str)  # error_message
    
    def __init__(self):
        super().__init__()
        self.connection_status = "Unknown"
        self.signal_strength = 0
        self.updating = False
    
    def check_connection_status(self):
        """Check if network is connected"""
        try:
            # Don't run checks if already updating
            if self.updating:
                return

            self.updating = True
            
            # Start a thread to check connection
            thread = threading.Thread(target=self._check_connection_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            print(f"Error checking connection: {e}")
            self.updating = False
    
    def _check_connection_thread(self):
        """Thread to check connection status to avoid UI freezing"""
        status = "Disconnected"
        strength = 0
        try:
            # Check if we can reach Google's DNS
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            status = "Connected"
        except TimeoutError:
            print("Network check timed out (no internet connection or very slow response).")
            # Remain as Disconnected, but do not crash
        except OSError as e:
            print(f"Network unreachable or error: {e}")
            # Remain as Disconnected, but do not interrupt app
        except Exception as e:
            print(f"Unexpected error during network check: {e}")
            # Remain as Disconnected
        
        # Get signal strength on a connected network
        if status == "Connected":
            strength = self._get_signal_strength()
        
        # Update status if changed
        if status != self.connection_status or strength != self.signal_strength:
            self.connection_status = status
            self.signal_strength = strength
            # Emit signal on the main thread
            self.connection_updated.emit(status, strength)
        
        self.updating = False
    
    def _get_signal_strength(self):
        """Get wifi signal strength - platform specific implementations"""
        try:
            system = platform.system()
            
            if system == "Windows":
                output = subprocess.check_output(["netsh", "wlan", "show", "interfaces"]).decode('utf-8')
                signal_match = re.search(r"Signal\s+:\s+(\d+)%", output)
                if signal_match:
                    return int(signal_match.group(1))
            
            elif system == "Linux":
                # Try reading from /proc/net/wireless
                try:
                    with open('/proc/net/wireless', 'r') as f:
                        for line in f:
                            if ":" in line and not line.startswith("Inter"):
                                parts = line.split()
                                if len(parts) >= 4:
                                    # Quality link is usually the 3rd column
                                    quality = int(float(parts[2].replace('.', '')))
                                    # Convert to percentage (usually out of 70)
                                    return min(100, int(quality * 100 / 70))
                except:
                    pass
            
            elif system == "Darwin":  # macOS
                try:
                    cmd = ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"]
                    output = subprocess.check_output(cmd).decode('utf-8')
                    signal_match = re.search(r"agrCtlRSSI:\s*(-\d+)", output)
                    if signal_match:
                        rssi = int(signal_match.group(1))
                        # Convert RSSI to percentage (typically -30 is excellent, -90 is unusable)
                        return max(0, min(100, 2 * (rssi + 100)))
                except:
                    pass
            
            # Default value if can't determine
            return 75
        except:
            return 0
    
    def run_speed_test(self):
        """Start a speed test in a background thread"""
        thread = threading.Thread(target=self._speed_test_thread)
        thread.daemon = True
        thread.start()
    
    def _speed_test_thread(self):
        """Thread to run network speed test"""
        try:
            import speedtest
            st = speedtest.Speedtest()
            st.get_best_server()
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            upload_speed = st.upload() / 1_000_000      # Convert to Mbps
            self.speed_test_complete.emit(download_speed, upload_speed)
        except Exception as e:
            print(f"Speedtest failed: {e}\nTrying fast.com backend...")
            # Try fast-cli as fallback
            try:
                import subprocess
                import json
                # Use 'fast --json' (fast-cli does not support --unit)
                result = subprocess.run(
                    ['fast', '--json'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    download_speed = float(data.get('downloadSpeed', 0))
                    # fast-cli does not provide upload, so set to 0
                    upload_speed = 0.0
                    self.speed_test_complete.emit(download_speed, upload_speed)
                else:
                    print(f"fast-cli failed: {result.stderr}")
                    self.speed_test_failed.emit(f"fast-cli failed: {result.stderr}")
            except Exception as fallback_e:
                print(f"Both speedtest and fast-cli failed: {fallback_e}")
                self.speed_test_failed.emit(f"Speedtest failed: {e}; fast-cli failed: {fallback_e}")
    
    def get_connection_info(self):
        """Get the current connection type and band."""
        if self.connection_status == "Connected":
            # Example values; replace with actual logic to determine connection type and band
            connection_type = "WiFi"  # or "Ethernet"
            band = "5GHz"  # or "2.4GHz"
        else:
            connection_type = "Disconnected"
            band = "N/A"
        
        return connection_type, band