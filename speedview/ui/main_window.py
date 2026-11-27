import sys
import logging
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QMessageBox,
    QShortcut,
    QApplication,
    QAction,
    QMenuBar,
)
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, QByteArray
from PyQt5.QtGui import QKeySequence, QMouseEvent

from speedview.ui.resources.svg_templates import MAIN_SVG_TEMPLATE
from speedview.ui.settings_dialog import SettingsDialog
from speedview.ui.system_tray import SystemTray
from speedview.ui.floating_window import FloatingWindow
from speedview.ui.test_network_dialog import TestNetworkDialog
from speedview.utils.svg_utils import (
    update_svg_speed,
    update_svg_connection_status,
    update_svg_signal_strength,
)
from speedview.controllers.network_controller import NetworkController
from speedview.controllers.speed_controller import SpeedController
from speedview.models.settings import Settings
from .update_dialog import UpdateDialog


class MainWindow(QWidget):
    def __init__(self, settings=None, speed_controller=None, network_controller=None):
        super().__init__()
        self.settings = settings or Settings()
        self.speed_controller = speed_controller or SpeedController(self.settings)
        self.network_controller = network_controller or NetworkController(
            selected_interface=self.settings.selected_interface
        )
        self.floating_window = None
        self._test_dialog = None
        self.tray = None

        self.is_dragging = False
        self.drag_position = QPoint()
        self.last_speeds = (0.0, 0.0)

        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()
        self.init_system_tray()

        # Trigger initial real interface check and periodic refresh (every 5s)
        if hasattr(self.network_controller, 'check_connection_status'):
            self.network_controller.check_connection_status()
            self.connection_timer = QTimer(self)
            self.connection_timer.timeout.connect(self.network_controller.check_connection_status)
            self.connection_timer.start(5000)

        self.update_display()

        if self.settings.is_floating:
            self.toggle_float_mode(force=True)
        elif self.settings.start_minimized:
            self.hide()

    def setup_ui(self):
        """Initialize the user interface"""
        logging.info("Starting setup_ui in MainWindow...")
        self.setWindowTitle("SpeedView - Network Monitor")
        self.setFixedSize(500, 524)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        menu_bar = QMenuBar(self)
        help_menu = menu_bar.addMenu("Help")
        check_updates_action = QAction("Check for Updates", self)
        check_updates_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(check_updates_action)
        self.layout.setMenuBar(menu_bar)

        self.svg_widget = QSvgWidget()
        self.layout.addWidget(self.svg_widget)
        self.svg_widget.mousePressEvent = self.handle_svg_click

        if isinstance(self.settings.window_position, (list, tuple)) and len(self.settings.window_position) == 2:
            self.move(int(self.settings.window_position[0]), int(self.settings.window_position[1]))

        self.current_svg_template = MAIN_SVG_TEMPLATE
        logging.info("Finished setup_ui in MainWindow.")

    def setup_connections(self):
        """Connect signals and slots"""
        self.speed_controller.speed_updated.connect(self.update_speed_display)
        if hasattr(self.speed_controller, 'test_completed'):
            self.speed_controller.test_completed.connect(self.on_speed_test_complete)
        if hasattr(self.network_controller, 'connection_updated'):
            self.network_controller.connection_updated.connect(self.on_connection_updated)
        if hasattr(self.network_controller, 'signal_strength_updated'):
            self.network_controller.signal_strength_updated.connect(self.on_signal_strength_updated)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        QShortcut(QKeySequence("Ctrl+S"), self, self.open_settings)
        QShortcut(QKeySequence("Ctrl+T"), self, self.test_network)
        QShortcut(QKeySequence("Ctrl+F"), self, self.toggle_float_mode)
        QShortcut(QKeySequence("Ctrl+H"), self, self.show_history)
        QShortcut(QKeySequence("Esc"), self, self.hide_if_floating)

    def init_system_tray(self):
        """Initialize system tray icon if enabled"""
        if self.settings.minimize_to_tray and self.tray is None:
            self.tray = SystemTray(self)
            if hasattr(self.tray, 'show'):
                self.tray.show()

    def _get_real_connection_info(self):
        selected = getattr(self.settings, 'selected_interface', None)
        if hasattr(self.network_controller, 'get_interface_details'):
            details = self.network_controller.get_interface_details(selected)
            conn_type = details.get("connection_type", "Unknown")
            summary_parts = []
            if details.get("interface"):
                summary_parts.append(details["interface"])
            if details.get("ssid"):
                summary_parts.append(details["ssid"])
            if details.get("band"):
                summary_parts.append(details["band"])
            if details.get("link_speed_mbps"):
                summary_parts.append(f"{details['link_speed_mbps']} Mbps")
            ip_parts = [p for p in (details.get("ipv4"), details.get("ipv6")) if p]
            meta = " • ".join(ip_parts) if ip_parts else (details.get("summary") or "")
            type_line = f"{conn_type} ({' • '.join(summary_parts)})" if summary_parts else conn_type
            return type_line, meta
        try:
            conn_type, band = self.network_controller.get_connection_info(selected)
        except TypeError:
            conn_type, band = self.network_controller.get_connection_info()
        return conn_type, band

    def _render_svg(self, download_speed, upload_speed):
        """Render complete SVG frame directly into memory."""
        show_upload = bool(self.settings.show_upload_speed)
        display_speed = upload_speed if show_upload else download_speed
        max_scale = self.settings.max_upload if show_upload else self.settings.max_speed

        svg_content = update_svg_speed(
            self.current_svg_template,
            speed=display_speed,
            max_speed=max_scale,
            show_upload=show_upload,
            speed_unit=self.settings.speed_unit,
        )

        status = getattr(self.network_controller, 'connection_status', 'Unknown')
        type_line, meta = self._get_real_connection_info()
        svg_content = update_svg_connection_status(
            svg_content,
            status=status,
            connection_type=type_line,
            meta_text=meta,
        )

        strength = getattr(self.network_controller, 'signal_strength', 0)
        svg_content = update_svg_signal_strength(svg_content, strength)

        self.svg_widget.load(QByteArray(svg_content.encode('utf-8')))

        if self.tray is not None:
            if hasattr(self.tray, 'update_tray_icon'):
                self.tray.update_tray_icon(display_speed)
            elif hasattr(self.tray, 'update_icon'):
                self.tray.update_icon(display_speed)

    def update_display(self):
        """Update all display elements using live controller and settings state"""
        download_speed, upload_speed = self.speed_controller.get_current_speeds()
        self.last_speeds = (download_speed, upload_speed)
        self._render_svg(download_speed, upload_speed)

    def update_speed_display(self, download_speed, upload_speed):
        """Slot for speed_controller.speed_updated(download_speed, upload_speed)."""
        self.last_speeds = (download_speed, upload_speed)
        self._render_svg(download_speed, upload_speed)

    def on_connection_updated(self, status=None, strength=None):
        """Slot for connection status changes."""
        self.update_display()

    def on_signal_strength_updated(self, strength):
        """Slot for signal strength changes."""
        self.update_display()

    def update_connection_display(self):
        self.update_display()

    def update_signal_strength(self, strength):
        self.update_display()

    def handle_svg_click(self, event: QMouseEvent):
        """Map widget coordinates to 500x500 SVG viewBox and handle interactive buttons."""
        pos = event.pos()
        widget_width = max(1, self.svg_widget.width())
        widget_height = max(1, self.svg_widget.height())
        svg_x = pos.x() * (500.0 / widget_width)
        svg_y = pos.y() * (500.0 / widget_height)
        logging.info(f"SVG clicked at widget ({pos.x()}, {pos.y()}) mapped to SVG ({svg_x:.1f}, {svg_y:.1f})")

        if 175 <= svg_x <= 325 and 400 <= svg_y <= 440:
            self.test_network()
        elif ((svg_x - 450) ** 2 + (svg_y - 80) ** 2) <= 400:
            self.open_settings()
        elif 50 <= svg_x <= 150 and 400 <= svg_y <= 440:
            self.toggle_float_mode()
        elif 350 <= svg_x <= 450 and 400 <= svg_y <= 440:
            self.show_history()
        event.accept()

    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(parent=self, settings=self.settings)
        if dialog.exec_():
            self.apply_settings_changes()

    def apply_settings_changes(self):
        """Apply live changes from settings"""
        if hasattr(self.speed_controller, 'set_update_interval'):
            self.speed_controller.set_update_interval(self.settings.update_interval)
        if hasattr(self.network_controller, 'set_interface'):
            self.network_controller.set_interface(self.settings.selected_interface)

        if self.settings.minimize_to_tray and self.tray is None:
            self.init_system_tray()
        elif not self.settings.minimize_to_tray and self.tray is not None:
            if hasattr(self.tray, 'hide'):
                self.tray.hide()
            self.tray = None

        self.update_display()

    def test_network(self):
        """Start a network speed test with visual SVG dialog"""
        if self._test_dialog is not None and self._test_dialog.isVisible():
            self._test_dialog.raise_()
            self._test_dialog.activateWindow()
            return

        self._test_dialog = TestNetworkDialog(self)
        self._test_dialog.set_status("Running speed test...")
        self._test_dialog.show()
        self._test_dialog.raise_()
        self._test_dialog.activateWindow()

        if hasattr(self.network_controller, 'speed_test_complete'):
            try:
                self.network_controller.speed_test_complete.disconnect(self._on_test_dialog_result)
            except TypeError:
                pass
            self.network_controller.speed_test_complete.connect(self._on_test_dialog_result)

        if hasattr(self.network_controller, 'speed_test_failed'):
            try:
                self.network_controller.speed_test_failed.disconnect(self._on_test_dialog_failed)
            except TypeError:
                pass
            self.network_controller.speed_test_failed.connect(self._on_test_dialog_failed)

        if hasattr(self.network_controller, 'run_speed_test'):
            self.network_controller.run_speed_test()
        elif hasattr(self.speed_controller, 'run_speed_test'):
            self.speed_controller.run_speed_test()

    def _on_test_dialog_result(self, download_speed, upload_speed):
        if self._test_dialog is not None:
            if download_speed == 0 and upload_speed == 0:
                self._test_dialog.show_failure()
            else:
                self._test_dialog.show_results(download_speed, upload_speed)
        if hasattr(self.network_controller, 'speed_test_complete'):
            try:
                self.network_controller.speed_test_complete.disconnect(self._on_test_dialog_result)
            except TypeError:
                pass
        if hasattr(self.network_controller, 'speed_test_failed'):
            try:
                self.network_controller.speed_test_failed.disconnect(self._on_test_dialog_failed)
            except TypeError:
                pass

    def _on_test_dialog_failed(self, error_msg):
        if self._test_dialog is not None:
            self._test_dialog.show_failure("Test Failed")
        self._on_test_dialog_result(0, 0)

    def on_speed_test_complete(self, download_speed, upload_speed):
        """Handle completed speed test"""
        if self._test_dialog is not None:
            self._on_test_dialog_result(download_speed, upload_speed)
            return
        if download_speed == 0 and upload_speed == 0:
            QMessageBox.warning(self, "Test Failed", "Network speed test failed. Please check your connection.")
        elif self.settings.show_test_notifications and self.tray is not None and hasattr(self.tray, 'show_message'):
            self.tray.show_message(
                "Speed Test Complete",
                f"Download: {download_speed:.2f} Mbps\nUpload: {upload_speed:.2f} Mbps",
            )

    def toggle_float_mode(self, force=False):
        """Toggle floating window"""
        if not self.floating_window or force:
            if self.floating_window:
                self.floating_window.close()
            self.settings.is_floating = True
            self.floating_window = FloatingWindow(
                self.speed_controller,
                self.settings,
                self.network_controller,
            )
            self.floating_window.expand_requested.connect(self._on_floating_expand)
            self.floating_window.show()
            self.hide()
        else:
            self.settings.is_floating = False
            self.floating_window.close()
            self.floating_window = None
            self.show()

    def _on_floating_expand(self):
        self.settings.is_floating = False
        self.floating_window = None
        self.show()
        self.activateWindow()
        self.raise_()

    def hide_if_floating(self):
        """Hide window if in floating mode"""
        if self.settings.is_floating:
            self.hide()

    def closeEvent(self, event):
        """Handle window close event using live settings"""
        self.settings.window_size = [self.width(), self.height()]
        self.settings.window_position = [self.x(), self.y()]
        try:
            self.settings.save()
        except Exception as e:
            logging.warning(f"Could not save settings on close: {e}")

        should_hide_to_tray = (self.settings.close_to_tray or self.settings.minimize_to_tray) and self.tray is not None
        if should_hide_to_tray:
            event.ignore()
            self.hide()
        else:
            if hasattr(self, 'connection_timer'):
                self.connection_timer.stop()
            if self.tray is not None and hasattr(self.tray, 'hide'):
                self.tray.hide()
            if self.floating_window:
                self.floating_window.close()
            event.accept()

    def check_for_updates(self):
        """Check for software updates"""
        update_dialog = UpdateDialog(self, settings=self.settings)
        update_dialog.exec_()

    def show_history(self):
        """Show speed test history"""
        logging.info("Showing speed test history")
        QMessageBox.information(
            self,
            "Speed Test History",
            "Speed test history feature will be implemented in a future update.",
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    if not window.settings.start_minimized and not window.settings.is_floating:
        window.show()
    sys.exit(app.exec_())