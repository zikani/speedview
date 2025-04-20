from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QMessageBox,
                              QDialog, QFormLayout, QLabel, QComboBox, QCheckBox,
                              QSystemTrayIcon, QMenu, QAction, QSlider, QPushButton,QLineEdit,QDialogButtonBox)
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
from speedview.models.settings import Settings
from speedview.controllers.network_controller import NetworkController
from speedview.controllers.speed_controller import SpeedController
from speedview.ui.resources.svg_templates import MAIN_SVG_TEMPLATE, FLOATING_SVG_TEMPLATE
from speedview.utils.svg_utils import update_svg_connection_status, update_svg_speed, save_svg_to_file
from speedview.ui.floating_window import FloatingWindow
from speedview.ui.settings_dialog import SettingsDialog

import psutil
import socket
import platform
import subprocess
import re  
import speedtest
import sys
import os



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
        self.settings = Settings()
        self.settings.load()
        self.max_speed = self.settings.max_speed
        self.update_interval = self.settings.update_interval
        self.start_minimized = self.settings.start_minimized
        self.minimize_to_tray = self.settings.minimize_to_tray
        self.show_upload_speed = self.settings.show_upload_speed
        self.selected_interface = self.settings.selected_interface
        self.is_floating = self.settings.is_floating
        
        # Controllers
        self.network_controller = NetworkController()
        self.speed_controller = SpeedController(self.settings)
        
        # Connect signals
        self.network_controller.connection_updated.connect(self.update_connection_status)
        self.network_controller.speed_test_complete.connect(self.on_speed_test_complete)
        self.speed_controller.speed_updated.connect(self.update_speed_display)
        
        self.setup_ui()
        self.setup_shortcuts()
        self.network_controller.check_connection_status()
        if self.settings.is_floating:
            self.toggle_float_mode()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_speed)
        self.timer.start(int(self.update_interval * 1000))

        self.prev_bytes_received = 0
        self.prev_bytes_sent = 0
        
        # Start minimized if setting is enabled
        if self.start_minimized:
            self.hide()
            
        # Get initial connection status
        self.connection_status = self.network_controller.connection_status
        self.signal_strength = self.network_controller.signal_strength

        self.tray = None  # Add system tray initialization
        self.init_system_tray()
    
    def setup_ui(self):
        # Setup UI components
        self.setWindowTitle("Network Speed Meter")
        self.setGeometry(100, 100, 500, 500)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.svg_widget = QSvgWidget()
        self.layout.addWidget(self.svg_widget)
        self.svg_widget.mousePressEvent = self.handle_svg_click
        
        # Add SVG for the network speed meter
        self.svg_code = MAIN_SVG_TEMPLATE
        self.load_svg(self.svg_code)

        # Add Help menu with update check
        from PyQt5.QtWidgets import QMenuBar, QMenu, QAction
        menu_bar = QMenuBar(self)
        help_menu = menu_bar.addMenu("Help")
        
        check_updates_action = QAction("Check for Updates", self)
        check_updates_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(check_updates_action)
        
        self.layout.setMenuBar(menu_bar)

    def setup_shortcuts(self):
        # Setup keyboard shortcuts
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        QShortcut(QKeySequence("Ctrl+S"), self, self.open_settings)
        QShortcut(QKeySequence("Ctrl+T"), self, self.test_network)
        QShortcut(QKeySequence("Ctrl+F"), self, self.toggle_float_mode)
        QShortcut(QKeySequence("Esc"), self, self.hide_if_floating)

    def load_svg(self, svg_content):
        # Load SVG content into the widget
        svg_path = save_svg_to_file(svg_content)
        self.svg_widget.load(svg_path)

    def update_speed_display(self):
        """Update the displayed speed in the floating window."""
        download_speed, upload_speed = self.speed_controller.get_current_speeds()
        display_speed = upload_speed if self.settings.show_upload_speed else download_speed
        # Update the SVG or any other UI component to reflect the new speed
        updated_svg = update_svg_speed(self.svg_code, display_speed, self.settings.max_speed)
        self.load_svg(updated_svg)

    def update_connection_status(self, status, signal_strength):
        """Update connection status display"""
        self.connection_status = status
        self.signal_strength = signal_strength
        updated_svg = update_svg_connection_status(
            self.svg_code, 
            status=status,
            signal_strength=signal_strength
        )
        self.load_svg(updated_svg)

    def handle_svg_click(self, event):
        """Handle clicks on SVG elements"""
        pos = event.pos()
        # Test Network Button region
        if 175 <= pos.x() <= 325 and 400 <= pos.y() <= 440:
            self.test_network()
        # Settings Icon region
        elif ((pos.x()-420)**2 + (pos.y()-80)**2) <= 225:
            self.open_settings()
        # Float Button region
        elif 50 <= pos.x() <= 150 and 400 <= pos.y() <= 440:
            self.toggle_float_mode()

    def apply_settings(self):
        """Apply settings changes"""
        # Update core settings
        self.max_speed = self.settings.max_speed
        self.update_interval = self.settings.update_interval
        self.selected_interface = self.settings.selected_interface
        
        # Update timers
        self.timer.setInterval(int(self.update_interval * 1000))
        
        # Update display mode
        if self.settings.is_floating != self.is_floating:
            self.toggle_float_mode()
        
        # Update tray
        if self.settings.minimize_to_tray:
            if not self.tray:
                self.init_system_tray()
        elif self.tray:
            self.tray.hide()
            self.tray = None
        
        # Refresh UI
        self.refresh_ui()

    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(parent=self, settings=self.settings)
        if dialog.exec_():
            self.apply_settings()

    def test_network(self):
        # Start a network speed test
        QMessageBox.information(self, "Network Test", "Starting network speed test. This may take a moment...")
        self.network_controller.run_speed_test()

    def on_speed_test_complete(self, download_speed, upload_speed):
        # Handle completed speed test
        if download_speed == 0 and upload_speed == 0:
            QMessageBox.warning(self, "Test Failed", "Network speed test failed. Please check your connection and try again.")
            return
        self.update_speed_display()
        QMessageBox.information(self, "Test Results", f"Download Speed: {download_speed:.2f} Mbps\nUpload Speed: {upload_speed:.2f} Mbps")

    def init_system_tray(self):
        """Initialize system tray icon."""
        from speedview.ui.system_tray import SystemTray
        self.tray = SystemTray(self)

    def toggle_float_mode(self):
        """Toggle between normal and floating display modes."""
        self.settings.is_floating = not self.settings.is_floating  # Toggle floating mode

        if self.settings.is_floating:
            # Pass the network_controller along with speed_controller and settings
            self.floating_window = FloatingWindow(self.speed_controller, self.settings, self.network_controller)
            self.floating_window.show()
            self.hide()
        else:
            self.show()
            if hasattr(self, 'floating_window'):
                self.floating_window.close()
                del self.floating_window

    def hide_if_floating(self):
        # Hide window if in floating mode
        if self.is_floating:
            self.hide()

    def refresh_ui(self):
        # Refresh UI after settings change
        self.svg_code = FLOATING_SVG_TEMPLATE if self.is_floating else MAIN_SVG_TEMPLATE
        self.update_speed_display()

    def closeEvent(self, event):
        # Handle window close event
        self.settings.save()
        if self.minimize_to_tray:
            event.ignore()
            self.hide()
        else:
            event.accept()

    def update_speed(self):
        """Update network speed measurements"""
        try:
            stats = psutil.net_io_counters(pernic=True)
            
            # If interface is selected, use that specific one
            if self.selected_interface and self.selected_interface in stats:
                net_io = stats[self.selected_interface]
            else:
                # Otherwise use the default overall counters
                net_io = psutil.net_io_counters()
            
            bytes_recv = net_io.bytes_recv
            bytes_sent = net_io.bytes_sent
            
            if self.prev_bytes_received > 0:
                # Calculate speeds in Mbps
                download_speed = ((bytes_recv - self.prev_bytes_received) * 8) / (1024 * 1024 * self.update_interval)
                upload_speed = ((bytes_sent - self.prev_bytes_sent) * 8) / (1024 * 1024 * self.update_interval)
                
                # Update the display
                self.update_speed_display()
            
            # Store current values for next calculation
            self.prev_bytes_received = bytes_recv
            self.prev_bytes_sent = bytes_sent
            
        except Exception as e:
            print(f"Error updating speed: {e}")

    def check_for_updates(self):
        """Check for software updates"""
        from speedview.ui.update_dialog import UpdateDialog
        dialog = UpdateDialog(self)
        dialog.exec_()

if __name__ == '__main__':
    app = QApplication([])
    window = NetworkSpeedMeter()
    window.show()
    app.exec_()