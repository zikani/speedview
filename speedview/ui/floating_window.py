import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QShortcut
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QTimer, QByteArray, pyqtSignal
from PyQt5.QtGui import QKeySequence
from speedview.utils.svg_utils import apply_rounded_mask, update_floating_svg
from speedview.ui.resources.svg_templates import FLOATING_SVG_TEMPLATE


class FloatingWindow(QWidget):
    expand_requested = pyqtSignal()

    def __init__(self, speed_controller, settings, network_controller):
        super().__init__()
        self.speed_controller = speed_controller
        self.settings = settings
        self.network_controller = network_controller
        logging.info("FloatingWindow initialized")

        self.setup_ui()
        self.setup_shortcuts()

        self.dragging = False
        self.drag_start_position = None

        if hasattr(self.speed_controller, 'speed_updated'):
            self.speed_controller.speed_updated.connect(self.on_speed_updated)
        if hasattr(self.network_controller, 'connection_updated'):
            self.network_controller.connection_updated.connect(self.on_connection_updated)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)

        self.update_display()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

    def setup_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("SpeedView - Floating Mode")
        self.setFixedSize(250, 80)
        apply_rounded_mask(self, 0, 0, 250, 80, radius=15)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.svg_widget = QSvgWidget()
        self.svg_widget.setStyleSheet("background: transparent;")
        self.layout.addWidget(self.svg_widget)
        self.svg_widget.mousePressEvent = self.handle_svg_mouse_press

    def setup_shortcuts(self):
        """Configure keyboard shortcuts"""
        QShortcut(QKeySequence("Esc"), self, self.close)

    def _get_connection_info(self):
        selected_iface = getattr(self.settings, 'selected_interface', None)
        try:
            return self.network_controller.get_connection_info(selected_iface)
        except TypeError:
            return self.network_controller.get_connection_info()

    def update_display(self, forced_speeds=None):
        """Update the display with current network stats"""
        if forced_speeds is not None:
            download_speed, upload_speed = forced_speeds
        else:
            try:
                download_speed, upload_speed = self.speed_controller.get_current_speeds()
            except Exception:
                logging.exception("Failed to get current speeds in FloatingWindow")
                download_speed, upload_speed = 0.0, 0.0

        download_speed = download_speed if download_speed is not None else 0.0
        upload_speed = upload_speed if upload_speed is not None else 0.0
        display_speed = upload_speed if getattr(self.settings, 'show_upload_speed', False) else download_speed

        signal_strength = getattr(self.network_controller, 'signal_strength', 0)
        try:
            connection_type, band = self._get_connection_info()
        except Exception:
            logging.exception("Failed to get connection info in FloatingWindow")
            connection_type, band = "Unknown", ""

        svg_content = update_floating_svg(
            FLOATING_SVG_TEMPLATE,
            speed=display_speed,
            signal_strength=signal_strength,
            connection_type=connection_type,
            band=band,
            speed_unit=getattr(self.settings, 'speed_unit', 'Mbps'),
        )
        self.svg_widget.load(QByteArray(svg_content.encode('utf-8')))

    def on_speed_updated(self, download_speed, upload_speed):
        """Slot to handle speed updates from controller in a thread-safe way."""
        self.update_display((download_speed, upload_speed))

    def on_connection_updated(self, status, strength):
        """Slot to handle connection status updates from network controller."""
        self.update_display()

    def handle_svg_mouse_press(self, event):
        """Handle mouse press events for dragging and buttons with proper coordinate mapping"""
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            widget_width = max(1, self.svg_widget.width())
            widget_height = max(1, self.svg_widget.height())
            svg_x = pos.x() * (250.0 / widget_width)
            svg_y = pos.y() * (80.0 / widget_height)

            # Close button at (230, 20) radius 8
            if (svg_x - 230) ** 2 + (svg_y - 20) ** 2 <= 64:
                self.close()
                event.accept()
                return

            # Expand button at (20, 20) radius 8
            if (svg_x - 20) ** 2 + (svg_y - 20) ** 2 <= 64:
                self.settings.is_floating = False
                self.expand_requested.emit()
                self.close()
                event.accept()
                return

            self.dragging = True
            self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.drag_start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()

    def closeEvent(self, event):
        self.update_timer.stop()
        event.accept()