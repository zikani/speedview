from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QMessageBox,
                        QDialog, QFormLayout, QLabel, QComboBox, QCheckBox,
                        QSystemTrayIcon, QMenu, QAction, QSlider, QPushButton)
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
import psutil
import socket
import platform
import subprocess
import re  # For using regular expressions to update SVG
import speedtest
import sys
import os


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Network Speed Meter Settings")
        self.setMinimumWidth(300)
        
        self.layout = QFormLayout()
        self.setLayout(self.layout)
        
        # Display settings
        self.layout.addRow(QLabel("<b>Display Settings</b>"))
        
        self.max_speed_combo = QComboBox()
        for speed in ["50", "100", "250", "500", "1000"]:
            self.max_speed_combo.addItem(f"{speed} Mbps")
        current_max = str(int(parent.max_speed))
        index = self.max_speed_combo.findText(f"{current_max} Mbps")
        if index >= 0:
            self.max_speed_combo.setCurrentIndex(index)
        self.layout.addRow("Maximum Speed:", self.max_speed_combo)
        
        self.update_interval_combo = QComboBox()
        intervals = [("0.5", "500ms"), ("1", "1 second"), ("2", "2 seconds"), ("5", "5 seconds")]
        for value, text in intervals:
            self.update_interval_combo.addItem(text, float(value))
        current_interval = parent.timer.interval() / 1000
        for i, (value, _) in enumerate(intervals):
            if float(value) == current_interval:
                self.update_interval_combo.setCurrentIndex(i)
                break
        self.layout.addRow("Update Interval:", self.update_interval_combo)
        
        # Behavior settings
        self.layout.addRow(QLabel("<br><b>Behavior Settings</b>"))
        
        self.start_minimized_check = QCheckBox()
        self.start_minimized_check.setChecked(parent.start_minimized)
        self.layout.addRow("Start Minimized:", self.start_minimized_check)
        
        self.minimize_to_tray_check = QCheckBox()
        self.minimize_to_tray_check.setChecked(parent.minimize_to_tray)
        self.layout.addRow("Minimize to Tray:", self.minimize_to_tray_check)
        
        self.show_upload_speed_check = QCheckBox()
        self.show_upload_speed_check.setChecked(parent.show_upload_speed)
        self.layout.addRow("Show Upload Speed:", self.show_upload_speed_check)
        
        # Network Interface
        self.layout.addRow(QLabel("<br><b>Network Interface</b>"))
        
        self.interface_combo = QComboBox()
        interfaces = self.get_network_interfaces()
        for interface in interfaces:
            self.interface_combo.addItem(interface)
        if parent.selected_interface and parent.selected_interface in interfaces:
            index = self.interface_combo.findText(parent.selected_interface)
            if index >= 0:
                self.interface_combo.setCurrentIndex(index)
        self.layout.addRow("Interface:", self.interface_combo)
        
        # Buttons
        self.buttons_layout = QVBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.cancel_button)
        self.layout.addRow("", self.buttons_layout)
    
    def get_network_interfaces(self):
        interfaces = []
        stats = psutil.net_if_stats()
        for interface, _ in stats.items():
            interfaces.append(interface)
        return interfaces
    
    def get_settings(self):
        max_speed = int(self.max_speed_combo.currentText().split()[0])
        update_interval = self.update_interval_combo.currentData()
        start_minimized = self.start_minimized_check.isChecked()
        minimize_to_tray = self.minimize_to_tray_check.isChecked()
        show_upload_speed = self.show_upload_speed_check.isChecked()
        selected_interface = self.interface_combo.currentText()
        
        return {
            'max_speed': max_speed,
            'update_interval': update_interval,
            'start_minimized': start_minimized,
            'minimize_to_tray': minimize_to_tray,
            'show_upload_speed': show_upload_speed,
            'selected_interface': selected_interface
        }


class SpeedTestThread(QThread):
    finished = pyqtSignal(float, float)  # download_speed, upload_speed

    def run(self):
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            upload_speed = st.upload() / 1_000_000      # Convert to Mbps
            self.finished.emit(download_speed, upload_speed)
        except Exception as e:
            print(f"Speed test failed: {e}")
            self.finished.emit(0, 0)

class NetworkSpeedMeter(QWidget):
    def __init__(self):
        super().__init__()
        
        # Default settings
        self.max_speed = 100
        self.update_interval = 1.0  # seconds
        self.start_minimized = False
        self.minimize_to_tray = True
        self.show_upload_speed = False
        self.selected_interface = None
        self.is_floating = False
        
        self.setWindowTitle("Network Speed Meter")
        self.setGeometry(100, 100, 500, 500)
        
        # Setup system tray
        self.setup_tray()
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.svg_widget = QSvgWidget()
        self.layout.addWidget(self.svg_widget)
        self.svg_widget.mousePressEvent = self.handle_svg_click
        
        # Add SVG for the network speed meter
        self.update_svg_template()
        self.load_svg(self.svg_code)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_speed)
        self.timer.start(int(self.update_interval * 1000))

        self.prev_bytes_received = 0
        self.prev_bytes_sent = 0
        
        # Start minimized if setting is enabled
        if self.start_minimized:
            self.hide()
            
        # Get initial connection status
        self.connection_status = self.check_connection_status()
        self.signal_strength = self.get_signal_strength()
    
    def update_svg_template(self):
        self.svg_code = """
<svg width="500" height="500" viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="backgroundGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#121212" />
      <stop offset="100%" stop-color="#000000" />
    </linearGradient>

    <linearGradient id="speedArcGradient" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00F0FF" />
      <stop offset="100%" stop-color="#0050FF" />
    </linearGradient>

    <filter id="shadowEffect">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#00F0FF" flood-opacity="0.5"/>
    </filter>

    <linearGradient id="buttonGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0066FF" />
      <stop offset="100%" stop-color="#0038AA" />
    </linearGradient>

    <linearGradient id="buttonHoverGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0088FF" />
      <stop offset="100%" stop-color="#0050CC" />
    </linearGradient>
  </defs>

  <rect width="500" height="500" fill="url(#backgroundGradient)"/>

  <circle cx="250" cy="250" r="220" fill="none" stroke="#333" stroke-width="2" opacity="0.5"/>

  <path d="M80 250 A170 170 0 0 1 420 250" fill="none" stroke="#333" stroke-width="20" stroke-linecap="round" opacity="0.3"/>

  <path id="activeArc" d="M80 250 A170 170 0 0 1 250 80" fill="none" stroke="url(#speedArcGradient)" stroke-width="20" stroke-linecap="round" opacity="0.8" stroke-dasharray="0, 534" style="animation: arcFill 1.5s ease-out forwards"/>

  <g font-family="Arial" font-weight="bold">
    <g transform="rotate(-135 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="3"/>
      <text x="250" y="50" text-anchor="middle" font-size="16" fill="#00F0FF">0</text>
    </g>

    <g transform="rotate(-105 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="14" fill="#00F0FF" opacity="0.7">5</text>
    </g>

    <g transform="rotate(-75 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="14" fill="#00F0FF" opacity="0.7">10</text>
    </g>

    <g transform="rotate(-45 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="14" fill="#00F0FF" opacity="0.7">20</text>
    </g>

    <g transform="rotate(-15 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="14" fill="#00F0FF" opacity="0.7">30</text>
    </g>

    <g transform="rotate(15 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="14" fill="#00F0FF" opacity="0.7">50</text>
    </g>

    <g transform="rotate(45 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="14" fill="#00F0FF" opacity="0.7">75</text>
    </g>

    <g transform="rotate(75 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="3"/>
      <text x="250" y="50" text-anchor="middle" font-size="16" fill="#00F0FF">100</text>
    </g>
  </g>

  <g id="needle" transform="rotate(-135 250 250)" filter="url(#shadowEffect)">
    <path d="M250 250 L255 120 L250 110 L245 120 Z" fill="#00F0FF"/>
    <circle cx="250" cy="250" r="10" fill="#00F0FF"/>
  </g>

  <circle cx="250" cy="250" r="5" fill="#fff"/>

  <text id="speedValue" x="250" y="300" text-anchor="middle" font-family="Arial" font-size="48" font-weight="bold" fill="#00F0FF">0.00</text>
  <text x="250" y="340" text-anchor="middle" font-family="Arial" font-size="20" fill="#00F0FF" opacity="0.7">Mbps</text>

  <g id="settingsIcon" transform="translate(420 80)" class="button" opacity="0.8">
    <circle cx="30" cy="30" r="15" fill="none" stroke="#00F0FF" stroke-width="2"/>
    <path d="M30 15 L30 10 M30 45 L30 50 M39.6 20.4 L43.3 16.7 M16.7 43.3 L20.4 39.6 M45 30 L50 30 M10 30 L5 30 M20.4 20.4 L16.7 16.7 M39.6 39.6 L43.3 43.3"
          stroke="#00F0FF" stroke-width="2" stroke-linecap="round"/>
    <circle cx="30" cy="30" r="3" fill="#00F0FF"/>
  </g>

  <g transform="translate(0 10)">
    <path d="M250 360 L240 350 M250 360 L260 350 M250 360 L250 390" stroke="#00F0FF" stroke-width="3" fill="none"/>
  </g>

  <g transform="translate(50 50)">
    <path d="M20 10 L20 30 M30 5 L30 30 M40 0 L40 30" stroke="#00F0FF" stroke-width="3" fill="none" opacity="0.7"/>
  </g>

  <text id="connectionStatus" x="460" y="70" text-anchor="end" font-family="Arial" font-size="16" fill="#00F0FF" opacity="0.7">Connected</text>

  <!-- Signal Strength Indicator -->
  <g id="signalStrength" transform="translate(380 70)">
    <rect x="0" y="0" width="5" height="15" rx="1" fill="#333333"/>
    <rect x="8" y="-5" width="5" height="20" rx="1" fill="#333333"/>
    <rect x="16" y="-10" width="5" height="25" rx="1" fill="#333333"/>
    <rect x="24" y="-15" width="5" height="30" rx="1" fill="#333333"/>
  </g>

  <rect id="testButton" x="175" y="400" width="150" height="40" rx="20" fill="url(#buttonGradient)" class="button"/>
  <text x="250" y="427" text-anchor="middle" font-family="Arial" font-size="16" font-weight="bold" fill="white">Test Network</text>

  <rect id="floatButton" x="50" y="400" width="100" height="40" rx="20" fill="url(#buttonGradient)" class="button"/>
  <text x="100" y="427" text-anchor="middle" font-family="Arial" font-size="16" font-weight="bold" fill="white">Float</text>

  <style>
    <![CDATA[
      .button {
        cursor: pointer;
        transition: all 0.3s ease;
      }
      .button:hover {
        fill: url(#buttonHoverGradient);
        transform: translateY(-2px);
        opacity: 1 !important;
      }
      .button:active {
        transform: translateY(1px);
      }
      #speedValue {
        transition: all 0.5s ease-out;
      }
      #settingsIcon:hover {
        transform: translate(420px, 80px) rotate(30deg);
        opacity: 1 !important;
      }
    ]]>
  </style>
</svg>
        """

    def setup_tray(self):
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create a self-created icon for the tray
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        
        # Create tray icon menu
        tray_menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        float_action = QAction("Float Mode", self)
        float_action.triggered.connect(self.toggle_float_mode)
        tray_menu.addAction(float_action)
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        tray_menu.addAction(settings_action)
        
        test_action = QAction("Test Network", self)
        test_action.triggered.connect(self.test_network)
        tray_menu.addAction(test_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(app.quit)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # Set icon
        self.update_tray_icon(0)
        
        # Show the tray icon
        self.tray_icon.show()
        
        # Connect signals
        self.tray_icon.activated.connect(self.tray_icon_activated)
    
    def update_tray_icon(self, speed):
        # Create a speed-based color icon for the tray
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        
        # Set the tray icon with updated tooltip
        self.tray_icon.setIcon(QIcon(pixmap))
        self.tray_icon.setToolTip(f"Network Speed: {speed:.2f} Mbps")
    
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    
    def load_svg(self, svg_string):
        with open("temp_speedometer.svg", "w") as f:
            f.write(svg_string)
        self.svg_widget.load("temp_speedometer.svg")
    
    def update_speed(self):
        # Check connection status and update indicator
        new_connection_status = self.check_connection_status()
        new_signal_strength = self.get_signal_strength()
        
        if new_connection_status != self.connection_status or new_signal_strength != self.signal_strength:
            self.connection_status = new_connection_status
            self.signal_strength = new_signal_strength
            self.update_connection_indicator()
        
        # Get network traffic data
        stats = psutil.net_io_counters(pernic=True)
        
        # If interface is selected, use that specific one
        if self.selected_interface and self.selected_interface in stats:
            net_io = stats[self.selected_interface]
        else:
            # Otherwise use the default overall counters
            net_io = psutil.net_io_counters()
        
        bytes_received = net_io.bytes_recv
        bytes_sent = net_io.bytes_sent

        if self.prev_bytes_received > 0:
            # Calculate speeds
            download_speed = (bytes_received - self.prev_bytes_received) / 1024  # KB/s
            upload_speed = (bytes_sent - self.prev_bytes_sent) / 1024  # KB/s
            
            # Convert to Mbps
            download_speed_mbps = download_speed * 8 / 1000
            upload_speed_mbps = upload_speed * 8 / 1000
            
            # Determine which speed to display based on settings
            display_speed_mbps = upload_speed_mbps if self.show_upload_speed else download_speed_mbps
            
            # Update tray icon
            self.update_tray_icon(display_speed_mbps)

            # Calculate needle angle based on displayed speed
            angle = -135 + (display_speed_mbps / self.max_speed) * 270
            angle = max(min(angle, 135), -135)

            # Update SVG display
            updated_svg = re.sub(r"<text id=\"speedValue\".*?>.*?</text>",
                               f"<text id=\"speedValue\" x=\"250\" y=\"300\" text-anchor=\"middle\" font-family=\"Arial\" font-size=\"48\" font-weight=\"bold\" fill=\"#00F0FF\">{display_speed_mbps:.2f}</text>",
                               self.svg_code)

            updated_svg = re.sub(r"<g id=\"needle\" transform=\"rotate\(.*? 250 250\)\".*?>",
                               f"<g id=\"needle\" transform=\"rotate({angle:.2f} 250 250)\" filter=\"url(#shadowEffect)\">",
                               updated_svg)

            # Update speed type label if needed
            speed_type = "Upload" if self.show_upload_speed else "Download"
            updated_svg = re.sub(r"<text x=\"250\" y=\"340\".*?>Mbps</text>",
                               f"<text x=\"250\" y=\"340\" text-anchor=\"middle\" font-family=\"Arial\" font-size=\"20\" fill=\"#00F0FF\" opacity=\"0.7\">{speed_type} Mbps</text>",
                               updated_svg)

            self.load_svg(updated_svg)
            self.svg_code = updated_svg

        self.prev_bytes_received = bytes_received
        self.prev_bytes_sent = bytes_sent
    
    def check_connection_status(self):
        try:
            # Check if we can reach Google's DNS
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return "Connected"
        except OSError:
            return "Disconnected"
    
    def get_signal_strength(self):
        # This is a placeholder. Actual implementation will vary by platform
        # For Windows, you might use 'netsh wlan show interfaces' command
        # For Linux, you could read from /proc/net/wireless
        try:
            if platform.system() == "Windows":
                output = subprocess.check_output(["netsh", "wlan", "show", "interfaces"]).decode('utf-8')
                signal_match = re.search(r"Signal\s+:\s+(\d+)%", output)
                if signal_match:
                    signal_percent = int(signal_match.group(1))
                    return signal_percent
            # Add platform-specific code for other OS types
            return 75  # Default value if can't determine
        except:
            return 0
    
    def update_connection_indicator(self):
        # Update connection status text
        updated_svg = re.sub(r"<text id=\"connectionStatus\".*?>.*?</text>",
                           f"<text id=\"connectionStatus\" x=\"460\" y=\"70\" text-anchor=\"end\" font-family=\"Arial\" font-size=\"16\" fill=\"{('#00F0FF' if self.connection_status == 'Connected' else '#FF5050')}\" opacity=\"0.7\">{self.connection_status}</text>",
                           self.svg_code)
        
        # Update signal strength bars
        signal_bars = ["#333333", "#333333", "#333333", "#333333"]  # Default all gray
        
        if self.connection_status == "Connected":
            if self.signal_strength > 0:
                signal_bars[0] = "#00F0FF"
            if self.signal_strength >= 25:
                signal_bars[1] = "#00F0FF"
            if self.signal_strength >= 50:
                signal_bars[2] = "#00F0FF"
            if self.signal_strength >= 75:
                signal_bars[3] = "#00F0FF"
        
        # Update signal strength indicator with regex
        signal_pattern = r"<g id=\"signalStrength\".*?</g>"
        signal_replacement = f"""<g id="signalStrength" transform="translate(380 70)">
    <rect x="0" y="0" width="5" height="15" rx="1" fill="{signal_bars[0]}"/>
    <rect x="8" y="-5" width="5" height="20" rx="1" fill="{signal_bars[1]}"/>
    <rect x="16" y="-10" width="5" height="25" rx="1" fill="{signal_bars[2]}"/>
    <rect x="24" y="-15" width="5" height="30" rx="1" fill="{signal_bars[3]}"/>
  </g>"""
        
        updated_svg = re.sub(signal_pattern, signal_replacement, updated_svg)
        
        self.load_svg(updated_svg)
        self.svg_code = updated_svg
    
    def handle_svg_click(self, event):
        # Check if click is within the test button area
        test_button_x, test_button_y = 175, 400
        test_button_width, test_button_height = 150, 40
        
        if (test_button_x <= event.pos().x() <= test_button_x + test_button_width and
            test_button_y <= event.pos().y() <= test_button_y + test_button_height):
            self.test_network()
        
        # Check if click is within the settings icon area
        settings_x, settings_y = 420, 80
        settings_radius = 30
        
        distance = ((event.pos().x() - (settings_x + settings_radius))**2 + 
                    (event.pos().y() - (settings_y + settings_radius))**2)**0.5
        
        if distance <= settings_radius:
            self.open_settings()
        
        # Check if click is within the float button area
        float_button_x, float_button_y = 50, 400
        float_button_width, float_button_height = 100, 40
        
        if (float_button_x <= event.pos().x() <= float_button_x + float_button_width and
            float_button_y <= event.pos().y() <= float_button_y + float_button_height):
            self.toggle_float_mode()
    
    def open_settings(self):
        dialog = SettingsDialog(self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            # Get settings from dialog
            settings = dialog.get_settings()
            
            # Apply settings
            self.max_speed = settings['max_speed']
            
            # Update timer interval if changed
            new_interval = int(settings['update_interval'] * 1000)
            if new_interval != self.timer.interval():
                self.timer.setInterval(new_interval)
                self.update_interval = settings['update_interval']
            
            self.start_minimized = settings['start_minimized']
            self.minimize_to_tray = settings['minimize_to_tray']
            
            # If upload/download setting changed, force an update
            if self.show_upload_speed != settings['show_upload_speed']:
                self.show_upload_speed = settings['show_upload_speed']
                self.update_speed()
            
            # Update interface if needed
            if self.selected_interface != settings['selected_interface']:
                self.selected_interface = settings['selected_interface']
                self.prev_bytes_received = 0  # Reset counters
                self.prev_bytes_sent = 0
    
    def toggle_float_mode(self):
        self.is_floating = not self.is_floating
        
        if self.is_floating:
            # Set to small floating mode
            self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
            self.resize(200, 200)
            # Create a more compact SVG for floating mode
            self.create_floating_svg()
        else:
            # Restore normal window mode
            self.setWindowFlags(Qt.Window)
            self.resize(500, 500)
            self.update_svg_template()
        
        self.show()
        self.update_speed()  # Force an update
    
    def create_floating_svg(self):
        # Create a simplified SVG for the floating mode
        self.svg_code = """
<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="backgroundGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#121212" />
      <stop offset="100%" stop-color="#000000" />
    </linearGradient>
    <linearGradient id="speedArcGradient" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00F0FF" />
      <stop offset="100%" stop-color="#0050FF" />
    </linearGradient>
  </defs>

  <rect width="200" height="200" fill="url(#backgroundGradient)" rx="10" ry="10"/>
  
  <!-- Signal bars -->
  <g id="signalStrength" transform="translate(150 25) scale(0.7)">
    <rect x="0" y="0" width="5" height="15" rx="1" fill="#333333"/>
    <rect x="8" y="-5" width="5" height="20" rx="1" fill="#333333"/>
    <rect x="16" y="-10" width="5" height="25" rx="1" fill="#333333"/>
    <rect x="24" y="-15" width="5" height="30" rx="1" fill="#333333"/>
  </g>

  <text id="connectionStatus" x="20" y="20" font-family="Arial" font-size="10" fill="#00F0FF">Connected</text>
  
  <text id="speedValue" x="100" y="100" text-anchor="middle" font-family="Arial" font-size="36" font-weight="bold" fill="#00F0FF">0.00</text>
  <text x="100" y="130" text-anchor="middle" font-family="Arial" font-size="14" fill="#00F0FF">Mbps</text>
  
  <circle cx="100" cy="160" r="15" fill="none" stroke="#00F0FF" stroke-width="2" class="button" id="settingsIcon"/>
  <path d="M100 150 L100 148 M100 172 L100 170 M108 152 L110 150 M90 170 L92 168 M112 160 L110 160 M90 160 L88 160 M92 152 L90 150 M108 168 L110 170"
        stroke="#00F0FF" stroke-width="1" stroke-linecap="round"/>
        
  <circle cx="20" cy="160" r="10" fill="none" stroke="#00F0FF" stroke-width="2" class="button" id="closeButton"/>
  <path d="M16 156 L24 164 M24 156 L16 164" stroke="#00F0FF" stroke-width="2"/>
  
  <circle cx="180" cy="160" r="10" fill="none" stroke="#00F0FF" stroke-width="2" class="button" id="testButton"/>
  <path d="M175 160 L185 160 M180 155 L180 165" stroke="#00F0FF" stroke-width="2"/>
  
  <style>
    <![CDATA[
      .button {
        cursor: pointer;
        transition: all 0.3s ease;
      }
      .button:hover {
        opacity: 1 !important;
        stroke: #00FFFF;
      }
    ]]>
  </style>
</svg>
        """
    
    def closeEvent(self, event):
        if self.minimize_to_tray:
            event.ignore()
            self.hide()
        else:
            event.accept()
    
    def test_network(self):
        # Show a message that the test is starting
        QMessageBox.information(self, "Network Test", "Starting network speed test. This may take a moment...")
        
        # Create and start the speed test thread
        self.test_thread = SpeedTestThread()
        self.test_thread.finished.connect(self.on_speed_test_complete)
        self.test_thread.start()

    def on_speed_test_complete(self, download_speed, upload_speed):
        # Update the display with the test results
        display_speed = upload_speed if self.show_upload_speed else download_speed
        
        angle = -135 + (display_speed / self.max_speed) * 270
        angle = max(min(angle, 135), -135)

        if self.is_floating:
            # Update the floating mode display
            updated_svg = re.sub(r"<text id=\"speedValue\".*?>.*?</text>",
                               f"<text id=\"speedValue\" x=\"100\" y=\"100\" text-anchor=\"middle\" font-family=\"Arial\" font-size=\"36\" font-weight=\"bold\" fill=\"#00F0FF\">{display_speed:.2f}</text>",
                               self.svg_code)
        else:
            # Update the normal mode display
            updated_svg = re.sub(r"<text id=\"speedValue\".*?>.*?</text>",
                               f"<text id=\"speedValue\" x=\"250\" y=\"300\" text-anchor=\"middle\" font-family=\"Arial\" font-size=\"48\" font-weight=\"bold\" fill=\"#00F0FF\">{display_speed:.2f}</text>",
                               self.svg_code)

            updated_svg = re.sub(r"<g id=\"needle\" transform=\"rotate\(.*? 250 250\)\".*?>",
                               f"<g id=\"needle\" transform=\"rotate({angle:.2f} 250 250)\" filter=\"url(#shadowEffect)\">",
                               updated_svg)

        self.load_svg(updated_svg)
        self.svg_code = updated_svg

        # Show results dialog
        QMessageBox.information(self, "Test Results",
                              f"Download Speed: {download_speed:.2f} Mbps\n"
                              f"Upload Speed: {upload_speed:.2f} Mbps")

if __name__ == '__main__':
    app = QApplication([])
    window = NetworkSpeedMeter()
    window.show()
    app.exec_()