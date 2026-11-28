import sys
import time
import threading
import logging
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QMessageBox,
    QShortcut,
    QApplication,
)
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, QByteArray, pyqtSignal
from PyQt5.QtGui import QKeySequence, QMouseEvent

from speedview.ui.resources.svg_templates import MAIN_SVG_TEMPLATE
from speedview.ui.settings_dialog import SettingsDialog
from speedview.ui.system_tray import SystemTray
from speedview.ui.floating_window import FloatingWindow
from speedview.ui.test_network_dialog import TestNetworkDialog
from speedview.ui.data_usage_dialog import DataUsageDialog
from speedview.utils.svg_utils import (
    apply_rounded_mask,
    update_svg_speed,
    update_svg_connection_status,
    update_svg_signal_strength,
    update_svg_ping,
)
from speedview.controllers.network_controller import NetworkController
from speedview.controllers.speed_controller import SpeedController
from speedview.models.settings import Settings
from speedview.models.data_usage import DataUsageTracker
from speedview.update.updater import UpdateChecker
from .update_dialog import UpdateDialog


class MainWindow(QWidget):
    background_update_ready = pyqtSignal(str, str)

    def __init__(self, settings=None, speed_controller=None, network_controller=None, data_usage_tracker=None):
        super().__init__()
        self.settings = settings or Settings()
        self.speed_controller = speed_controller or SpeedController(self.settings)
        self.network_controller = network_controller or NetworkController(
            selected_interface=self.settings.selected_interface
        )
        self.data_usage_tracker = data_usage_tracker or DataUsageTracker()
        self.floating_window = None
        self._test_dialog = None
        self._usage_dialog = None
        self.tray = None

        self.is_dragging = False
        self.drag_position = QPoint()
        self.last_speeds = (0.0, 0.0)
        self._last_threshold_alert = 0.0
        self._force_quit = False
        self._suppress_child_float = False
        self._checking_updates = False
        self._pending_updater = None

        app = QApplication.instance()
        if app is not None:
            app.setQuitOnLastWindowClosed(False)

        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()
        self.init_system_tray()

        if hasattr(self.network_controller, 'check_connection_status'):
            self.network_controller.check_connection_status()
            self.connection_timer = QTimer(self)
            self.connection_timer.timeout.connect(self.network_controller.check_connection_status)
            self.connection_timer.start(3000)

        self.background_update_ready.connect(self._on_background_update_ready)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.start_background_update_check)
        # Poll timer every 6h; UpdateChecker enforces the 3-day GitHub API cooldown
        self.update_timer.start(6 * 60 * 60 * 1000)
        QTimer.singleShot(2500, self.start_background_update_check)

        self.update_display()

        if self.settings.is_floating:
            self.toggle_float_mode(force=True)
        elif self.settings.start_minimized:
            self.hide()

    def setup_ui(self):
        """Initialize the frameless translucent SVG user interface (no menu bar or box background)."""
        logging.info("Starting setup_ui in MainWindow...")
        self.setWindowTitle("SpeedView - Network Monitor")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("MainWindow { background: transparent; }")
        self.setFixedSize(500, 500)
        apply_rounded_mask(self, 0, 0, 500, 500, radius=28)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.svg_widget = QSvgWidget()
        self.svg_widget.setStyleSheet("background: transparent;")
        self.layout.addWidget(self.svg_widget)
        self.svg_widget.mousePressEvent = self.handle_svg_click

        if isinstance(self.settings.window_position, (list, tuple)) and len(self.settings.window_position) == 2:
            self.move(int(self.settings.window_position[0]), int(self.settings.window_position[1]))

        self.current_svg_template = MAIN_SVG_TEMPLATE
        logging.info("Finished setup_ui in MainWindow.")

    def setup_connections(self):
        """Connect signals and slots"""
        self.speed_controller.speed_updated.connect(self.update_speed_display)
        try:
            if hasattr(self.speed_controller, 'bytes_transferred'):
                self.speed_controller.bytes_transferred.connect(self.on_bytes_transferred)
        except RuntimeError:
            pass
        try:
            if hasattr(self.speed_controller, 'test_completed'):
                self.speed_controller.test_completed.connect(self.on_speed_test_complete)
        except RuntimeError:
            pass
        if hasattr(self.network_controller, 'connection_updated'):
            self.network_controller.connection_updated.connect(self.on_connection_updated)
        if hasattr(self.network_controller, 'signal_strength_updated'):
            self.network_controller.signal_strength_updated.connect(self.on_signal_strength_updated)
        try:
            if hasattr(self.network_controller, 'latency_updated'):
                self.network_controller.latency_updated.connect(self.on_latency_updated)
        except RuntimeError:
            pass

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        QShortcut(QKeySequence("Ctrl+S"), self, self.open_settings)
        QShortcut(QKeySequence("Ctrl+T"), self, self.test_network)
        QShortcut(QKeySequence("Ctrl+F"), self, self.toggle_float_mode)
        QShortcut(QKeySequence("Ctrl+U"), self, self.open_data_usage)
        QShortcut(QKeySequence("Ctrl+H"), self, self.open_data_usage)
        QShortcut(QKeySequence("Esc"), self, self.hide_if_floating)

    def init_system_tray(self):
        """Initialize system tray icon if enabled"""
        if self.settings.minimize_to_tray and self.tray is None:
            self.tray = SystemTray(self)
            if hasattr(self.tray, 'show'):
                self.tray.show()

    def ensure_tray_visible(self):
        """Ensure a system tray icon is initialized and visible for background operation."""
        if self.tray is None:
            self.tray = SystemTray(self)
        if hasattr(self.tray, 'show'):
            self.tray.show()

    def minimize_to_tray(self):
        """Minimize MainWindow directly to the system tray."""
        self.ensure_tray_visible()
        self.hide()

    def on_bytes_transferred(self, delta_recv, delta_sent):
        """Persist real byte deltas to DataUsageTracker and refresh open DataUsageDialog."""
        self.data_usage_tracker.record_traffic(delta_recv, delta_sent)
        if self._usage_dialog is not None and self._usage_dialog.isVisible():
            self._usage_dialog.refresh_display()

    def _get_real_connection_info(self):
        selected = getattr(self.settings, 'selected_interface', None)
        if hasattr(self.network_controller, 'get_cached_interface_details'):
            details = self.network_controller.get_cached_interface_details(selected)
        elif hasattr(self.network_controller, 'get_interface_details'):
            details = self.network_controller.get_interface_details(selected)
        else:
            details = None

        if details is not None:
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

        latency_ms = getattr(self.network_controller, 'latency_ms', None)
        svg_content = update_svg_ping(svg_content, latency_ms)

        self.svg_widget.load(QByteArray(svg_content.encode('utf-8')))

        if self.tray is not None:
            if hasattr(self.tray, 'update_tray_icon'):
                self.tray.update_tray_icon(display_speed)
            elif hasattr(self.tray, 'update_icon'):
                self.tray.update_icon(display_speed)

            if (
                getattr(self.settings, 'enable_notifications', False)
                and display_speed >= getattr(self.settings, 'notification_threshold', 50)
                and (time.time() - self._last_threshold_alert) >= 60.0
                and hasattr(self.tray, 'show_message')
            ):
                self._last_threshold_alert = time.time()
                self.tray.show_message(
                    "High Network Speed Alert",
                    f"Speed reached {display_speed:.2f} Mbps (threshold: {self.settings.notification_threshold} Mbps)",
                )

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
        self.update_display()

    def on_signal_strength_updated(self, strength):
        self.update_display()

    def on_latency_updated(self, latency_ms):
        self.update_display()

    def update_connection_display(self):
        self.update_display()

    def update_signal_strength(self, strength):
        self.update_display()

    def handle_svg_click(self, event: QMouseEvent):
        """Map widget coordinates to 500x500 SVG viewBox, handle buttons, or drag frameless window."""
        if event.button() != Qt.LeftButton:
            return
        pos = event.pos()
        widget_width = max(1, self.svg_widget.width())
        widget_height = max(1, self.svg_widget.height())
        svg_x = pos.x() * (500.0 / widget_width)
        svg_y = pos.y() * (500.0 / widget_height)
        logging.info(f"SVG clicked at widget ({pos.x()}, {pos.y()}) mapped to SVG ({svg_x:.1f}, {svg_y:.1f})")

        # Minimize button (442, 24) -> minimize to tray
        if ((svg_x - 442) ** 2 + (svg_y - 24) ** 2) <= 144:
            self.minimize_to_tray()
        # Close button (472, 24) -> switch to float widget
        elif ((svg_x - 472) ** 2 + (svg_y - 24) ** 2) <= 144:
            self.close()
        # Test Network button (175..325, 400..440)
        elif 175 <= svg_x <= 325 and 400 <= svg_y <= 440:
            self.test_network()
        # Settings icon (450, 80) r=20
        elif ((svg_x - 450) ** 2 + (svg_y - 80) ** 2) <= 400:
            self.open_settings()
        # Float button (50..150, 400..440)
        elif 50 <= svg_x <= 150 and 400 <= svg_y <= 440:
            self.toggle_float_mode()
        # Usage button (350..450, 400..440) -> open Data Usage & close MainWindow
        elif 350 <= svg_x <= 450 and 400 <= svg_y <= 440:
            self.open_data_usage(close_main=True)
        else:
            self.is_dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.is_dragging = False
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
        if self.floating_window is not None:
            self.floating_window.update_display()

    def open_data_usage(self, close_main=False):
        """Open the SVG Data Usage window showing App | Data | Date and Daily/Monthly totals."""
        if self._usage_dialog is None:
            self._usage_dialog = DataUsageDialog(tracker=self.data_usage_tracker, parent=None)
            self._usage_dialog.closed.connect(self._on_child_closed_open_float)
        else:
            self._usage_dialog.refresh_display()
        self._usage_dialog.show()
        self._usage_dialog.raise_()
        self._usage_dialog.activateWindow()
        if close_main:
            self.ensure_tray_visible()
            self.hide()

    def show_history(self):
        """Alias for open_data_usage."""
        self.open_data_usage()

    def test_network(self):
        """Start a network speed test with visual SVG dialog"""
        if self._test_dialog is not None and self._test_dialog.isVisible():
            self._test_dialog.raise_()
            self._test_dialog.activateWindow()
            return

        self._test_dialog = TestNetworkDialog(self)
        self._test_dialog.closed.connect(self._on_child_closed_open_float)
        self._test_dialog.set_status("Running speed test...")
        self._test_dialog.show()
        self._test_dialog.raise_()
        self._test_dialog.activateWindow()

        if hasattr(self.network_controller, 'speed_test_progress'):
            try:
                self.network_controller.speed_test_progress.disconnect(self._on_test_dialog_progress)
            except (TypeError, RuntimeError):
                pass
            try:
                self.network_controller.speed_test_progress.connect(self._on_test_dialog_progress)
            except RuntimeError:
                pass

        if hasattr(self.network_controller, 'speed_test_complete'):
            try:
                self.network_controller.speed_test_complete.disconnect(self._on_test_dialog_result)
            except (TypeError, RuntimeError):
                pass
            self.network_controller.speed_test_complete.connect(self._on_test_dialog_result)

        if hasattr(self.network_controller, 'speed_test_failed'):
            try:
                self.network_controller.speed_test_failed.disconnect(self._on_test_dialog_failed)
            except (TypeError, RuntimeError):
                pass
            self.network_controller.speed_test_failed.connect(self._on_test_dialog_failed)

        if hasattr(self.network_controller, 'run_speed_test'):
            self.network_controller.run_speed_test()
        elif hasattr(self.speed_controller, 'run_speed_test'):
            self.speed_controller.run_speed_test()

    def _disconnect_test_signals(self):
        if hasattr(self.network_controller, 'speed_test_progress'):
            try:
                self.network_controller.speed_test_progress.disconnect(self._on_test_dialog_progress)
            except (TypeError, RuntimeError):
                pass
        if hasattr(self.network_controller, 'speed_test_complete'):
            try:
                self.network_controller.speed_test_complete.disconnect(self._on_test_dialog_result)
            except (TypeError, RuntimeError):
                pass
        if hasattr(self.network_controller, 'speed_test_failed'):
            try:
                self.network_controller.speed_test_failed.disconnect(self._on_test_dialog_failed)
            except (TypeError, RuntimeError):
                pass

    def _on_test_dialog_progress(self, status, download_speed, upload_speed):
        if self._test_dialog is not None and self._test_dialog.isVisible():
            self._test_dialog.update_display(status, download_speed, upload_speed)

    def _on_test_dialog_result(self, download_speed, upload_speed):
        if self._test_dialog is not None:
            if download_speed == 0 and upload_speed == 0:
                self._test_dialog.show_failure()
            else:
                self._test_dialog.show_results(download_speed, upload_speed)
        self._disconnect_test_signals()

    def _on_test_dialog_failed(self, error_msg):
        if self._test_dialog is not None:
            msg = str(error_msg).splitlines()[0] if error_msg else "Test Failed"
            self._test_dialog.show_failure(msg)
        self._disconnect_test_signals()

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
            self.floating_window.closed.connect(self._on_floating_closed)
            self.floating_window.show()
            self.hide()
        else:
            self.settings.is_floating = False
            self.floating_window.close()
            self.floating_window = None
            self.show()

    def _on_child_closed_open_float(self):
        """Closing any secondary window opens the Float gadget instead of stranding or quitting."""
        if self._force_quit or self._suppress_child_float:
            return
        self.ensure_tray_visible()
        self.toggle_float_mode(force=True)

    def _on_floating_closed(self):
        """When Float widget is closed, minimize to tray and keep running in background."""
        self.floating_window = None
        self.settings.is_floating = False
        self.ensure_tray_visible()

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

    def force_quit(self):
        """Explicitly shut down background monitoring and exit the application."""
        self._force_quit = True
        self._suppress_child_float = True
        self.close()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def closeEvent(self, event):
        """Closing MainWindow switches to the Float widget instead of quitting, unless force_quit."""
        self.settings.window_size = [self.width(), self.height()]
        self.settings.window_position = [self.x(), self.y()]
        try:
            self.settings.save()
        except Exception as e:
            logging.warning(f"Could not save settings on close: {e}")

        if not self._force_quit:
            event.ignore()
            self.ensure_tray_visible()
            self.toggle_float_mode(force=True)
            return

        self._suppress_child_float = True
        if hasattr(self, 'connection_timer'):
            self.connection_timer.stop()
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        if self.tray is not None and hasattr(self.tray, 'hide'):
            self.tray.hide()
        if self.floating_window:
            self.floating_window.close()
        if self._usage_dialog:
            self._usage_dialog.close()
        if self._test_dialog:
            self._test_dialog.close()
        event.accept()

    def start_background_update_check(self, force=False):
        """Check GitHub Releases in the background (throttled to every 3 days)."""
        if self._force_quit or self._checking_updates:
            return
        if not force and not getattr(self.settings, 'auto_update', True):
            return

        probe = UpdateChecker(settings=self.settings)
        if not probe.should_check_for_updates(force=force):
            return

        self._checking_updates = True

        def _worker():
            try:
                updater = UpdateChecker(settings=self.settings)
                if not updater.check_for_updates(force=force):
                    return
                if not updater.download_url or updater.download_url == updater.release_page_url:
                    return
                staged_path = updater.download_update()
                if staged_path:
                    self._pending_updater = updater
                    self.background_update_ready.emit(str(updater.latest_version or ""), staged_path)
            except Exception as exc:
                logging.warning(f"Background update check failed: {exc}")
            finally:
                self._checking_updates = False

        threading.Thread(target=_worker, daemon=True).start()

    def _on_background_update_ready(self, latest_version, staged_path):
        """Apply downloaded background update when running as a packaged binary."""
        if self._force_quit:
            return
        if self.tray is not None and hasattr(self.tray, 'show_message'):
            self.tray.show_message(
                "SpeedView Update Ready",
                f"Version {latest_version} downloaded in background.",
            )
        if self._pending_updater is not None and self._pending_updater.can_self_replace():
            if self._pending_updater.install_update(staged_path, restart=True):
                self.force_quit()

    def check_for_updates(self):
        """Check for software updates manually."""
        update_dialog = UpdateDialog(self, settings=self.settings, force_check=True)
        update_dialog.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    if not window.settings.start_minimized and not window.settings.is_floating:
        window.show()
    sys.exit(app.exec_())