import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QMessageBox, QShortcut, 
                             QApplication, QAction)
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QKeySequence, QMouseEvent, QIcon

from network_speed_meter.speedview.ui.resources.svg_templates import MAIN_SVG_TEMPLATE
from speedview.ui.settings_dialog import SettingsDialog
from speedview.ui.system_tray import SystemTray
from speedview.ui.floating_window import FloatingWindow
from speedview.utils.svg_utils import (update_svg_speed, update_svg_connection_status,
                                       update_svg_signal_strength)
from speedview.controllers.network_controller import NetworkController
from speedview.controllers.speed_controller import SpeedController
from speedview.models.settings import Settings
from .update_dialog import UpdateDialog

class MainWindow(QWidget):
    def __init__(self, settings, speed_controller, network_controller):
        super().__init__()
        self.settings = settings
        self.speed_controller = speed_controller
        self.network_controller = network_controller
        self.floating_window = None
        
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()
        self.init_system_tray()
        
        # Initial state
        self.is_dragging = False
        self.drag_position = QPoint()
        self.last_speeds = (0.0, 0.0)  # (download, upload)
        
        # Initial updates
        self.update_connection_display()
        self.update_display()
        
        # Start update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(2000)  # Update every 2 seconds for reduced CPU usage

    def setup_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("SpeedView - Network Monitor")
        self.setWindowIcon(QIcon(":/icons/app_icon"))
        
        # Main layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        # SVG display
        self.svg_widget = QSvgWidget()
        self.layout.addWidget(self.svg_widget)
        
        # Window properties
        self.setMinimumSize(500, 500)
        self.resize(self.settings.window_size)
        self.move(self.settings.window_position)
        
        # Load initial SVG
        self.current_svg_template = MAIN_SVG_TEMPLATE
        self.update_display()

        # Add Help menu
        help_menu = self.menuBar().addMenu("Help")
        check_updates_action = QAction("Check for Updates", self)
        check_updates_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(check_updates_action)

    def setup_connections(self):
        """Connect signals and slots"""
        self.speed_controller.speed_updated.connect(self.update_speed_display)
        self.speed_controller.test_completed.connect(self.on_speed_test_complete)
        self.network_controller.connection_updated.connect(self.update_connection_display)
        self.network_controller.signal_strength_updated.connect(self.update_signal_strength)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        QShortcut(QKeySequence("Ctrl+S"), self, self.open_settings)
        QShortcut(QKeySequence("Ctrl+T"), self, self.test_network)
        QShortcut(QKeySequence("Ctrl+F"), self, self.toggle_float_mode)
        QShortcut(QKeySequence("Esc"), self, self.hide_if_floating)

    def init_system_tray(self):
        """Initialize system tray icon if enabled"""
        if self.settings.minimize_to_tray:
            self.tray = SystemTray(self)
            self.tray.show()

    def update_display(self):
        """Update all display elements"""
        download_speed, upload_speed = self.speed_controller.get_current_speeds()
        self.last_speeds = (download_speed, upload_speed)
        
        # Update speed display
        display_speed = upload_speed if self.settings.show_upload_speed else download_speed
        svg_content = update_svg_speed(
            self.current_svg_template,
            speed=display_speed,
            max_speed=self.settings.max_speed,
            show_upload=self.settings.show_upload_speed
        )
        
        # Update connection status
        status = self.network_controller.connection_status
        svg_content = update_svg_connection_status(
            svg_content,
            status=status,
            connection_type=self.network_controller.get_connection_info()[0]
        )
        
        # Update signal strength
        strength = self.network_controller.signal_strength
        svg_content = update_svg_signal_strength(svg_content, strength)
        
        # Load updated SVG
        self.svg_widget.load(svg_content.encode('utf-8'))
        
        # Update tray icon if available
        if hasattr(self, 'tray') and self.tray:
            self.tray.update_icon(display_speed)

    def update_speed_display(self, download_speed, upload_speed):
        """Update only the speed display"""
        self.last_speeds = (download_speed, upload_speed)
        display_speed = upload_speed if self.settings.show_upload_speed else download_speed
        
        svg_content = update_svg_speed(
            self.current_svg_template,
            speed=display_speed,
            max_speed=self.settings.max_speed,
            show_upload=self.settings.show_upload_speed
        )
        self.svg_widget.load(svg_content.encode('utf-8'))
        
        if hasattr(self, 'tray') and self.tray:
            self.tray.update_icon(display_speed)

    def update_connection_display(self):
        """Update connection status display"""
        status = self.network_controller.connection_status
        svg_content = update_svg_connection_status(
            self.current_svg_template,
            status=status,
            connection_type=self.network_controller.get_connection_info()[0]
        )
        self.svg_widget.load(svg_content.encode('utf-8'))

    def update_signal_strength(self, strength):
        """Update signal strength indicator"""
        svg_content = update_svg_signal_strength(
            self.current_svg_template,
            strength=strength
        )
        self.svg_widget.load(svg_content.encode('utf-8'))

    def handle_svg_click(self, event: QMouseEvent):
        """Handle clicks on the SVG widget"""
        pos = event.pos()
        
        # Test Network Button (175,400 to 325,440)
        if 175 <= pos.x() <= 325 and 400 <= pos.y() <= 440:
            self.test_network()
        
        # Settings Icon (420,80 with 15px radius)
        elif ((pos.x()-420)**2 + (pos.y()-80)**2) <= 225:  # 15^2
            self.open_settings()
        
        # Float Button (50,400 to 150,440)
        elif 50 <= pos.x() <= 150 and 400 <= pos.y() <= 440:
            self.toggle_float_mode()

    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self.settings, parent=self)
        if dialog.exec_():
            self.apply_settings_changes()

    def apply_settings_changes(self):
        """Apply changes from settings dialog"""
        # Update tray icon if needed
        if self.settings.minimize_to_tray and not hasattr(self, 'tray'):
            self.init_system_tray()
        elif not self.settings.minimize_to_tray and hasattr(self, 'tray'):
            self.tray.hide()
            del self.tray
        
        # Refresh display
        self.update_display()

    def test_network(self):
        """Start a network speed test"""
        if not self.speed_controller.test_in_progress:
            self.speed_controller.run_speed_test()
        else:
            QMessageBox.information(self, "Test Running", 
                                 "A speed test is already in progress.")

    def on_speed_test_complete(self, download_speed, upload_speed):
        """Handle completed speed test"""
        if download_speed == 0 and upload_speed == 0:
            QMessageBox.warning(self, "Test Failed", 
                              "Network speed test failed. Please check your connection.")
        elif self.settings.show_test_notifications:
            if hasattr(self, 'tray') and self.tray:
                self.tray.show_message(
                    "Speed Test Complete",
                    f"Download: {download_speed:.2f} Mbps\nUpload: {upload_speed:.2f} Mbps"
                )

    def toggle_float_mode(self):
        """Toggle floating window"""
        if not self.floating_window:
            self.floating_window = FloatingWindow(
                self.speed_controller,
                self.settings,
                self.network_controller
            )
            self.floating_window.show()
            self.hide()
        else:
            self.floating_window.close()
            self.floating_window = None
            self.show()

    def hide_if_floating(self):
        """Hide window if in floating mode"""
        if self.settings.is_floating:
            self.hide()

    def closeEvent(self, event):
        """Handle window close event"""
        self.update_timer.stop()
        self.settings.window_size = self.size()
        self.settings.window_position = self.pos()
        self.settings.save()
        
        if self.settings.minimize_to_tray and hasattr(self, 'tray') and self.tray:
            event.ignore()
            self.hide()
        else:
            if hasattr(self, 'tray') and self.tray:
                self.tray.hide()
            if self.floating_window:
                self.floating_window.close()
            event.accept()

    def check_for_updates(self):
        """Check for software updates"""
        update_dialog = UpdateDialog(self)
        update_dialog.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Use real controllers
    settings = Settings()
    speed_controller = SpeedController(settings)
    network_controller = NetworkController()
    
    window = MainWindow(settings, speed_controller, network_controller)
    window.show()
    sys.exit(app.exec_())