from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QFontMetrics
from PyQt5.QtCore import Qt
from speedview.utils.svg_utils import convert_speed


class SystemTray:
    def __init__(self, main_window):
        self.main_window = main_window
        self.last_speed = 0
        self.setup_tray()

    def setup_tray(self):
        """Create the system tray icon and menu."""
        self.tray_icon = QSystemTrayIcon(self.main_window)
        tray_menu = QMenu()

        actions = [
            ("Show", self.show_window),
            ("Float Mode", self.main_window.toggle_float_mode),
            ("Data Usage", self.main_window.open_data_usage),
            ("Settings", self.main_window.open_settings),
            ("Test Network", self.main_window.test_network),
            ("Exit", self.quit_application),
        ]

        for text, callback in actions:
            action = QAction(text, self.main_window)
            action.triggered.connect(callback)
            tray_menu.addAction(action)
            if text == "Test Network":
                tray_menu.addSeparator()

        self.tray_icon.setContextMenu(tray_menu)
        self.update_tray_icon(0)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def create_dynamic_icon(self, display_speed):
        """Create a dynamic tray icon showing the current speed."""
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(QColor(40, 40, 40))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, size - 4, size - 4)

        font = QFont("Arial", 10 if display_speed < 100 else 8)
        painter.setFont(font)
        painter.setPen(QColor(0, 240, 255))

        speed_text = f"{display_speed:.0f}" if display_speed >= 1 else f"{display_speed:.1f}"
        fm = QFontMetrics(font)
        text_rect = fm.boundingRect(speed_text)
        painter.drawText(
            (size - text_rect.width()) // 2,
            (size + fm.ascent() - fm.descent()) // 2,
            speed_text,
        )

        painter.end()
        return QIcon(pixmap)

    def update_tray_icon(self, speed):
        """Update the tray icon and tooltip with current speed, direction, and connection status."""
        self.last_speed = speed
        settings = getattr(self.main_window, "settings", None)
        unit = getattr(settings, "speed_unit", "Mbps")
        show_upload = bool(getattr(settings, "show_upload_speed", False))
        direction = "Upload" if show_upload else "Download"
        display_speed = convert_speed(speed, unit)

        icon = self.create_dynamic_icon(display_speed)
        self.tray_icon.setIcon(icon)

        nc = getattr(self.main_window, "network_controller", None)
        conn_status = getattr(nc, "connection_status", "Active" if speed > 0 else "Idle") if nc else ("Active" if speed > 0 else "Idle")
        details = getattr(nc, "interface_details", None) if nc else None
        iface = getattr(settings, "selected_interface", None) or (details.get("interface") if isinstance(details, dict) else None)
        iface_suffix = f" ({iface})" if iface else ""

        tooltip = (
            f"SpeedView Network Monitor\n"
            f"{direction}: {display_speed:.2f} {unit}\n"
            f"Network: {conn_status}{iface_suffix}\n"
            f"Double-click to show/hide"
        )
        self.tray_icon.setToolTip(tooltip)

    def update_icon(self, speed):
        """Alias for update_tray_icon."""
        self.update_tray_icon(speed)

    def show_message(self, title, message, icon=QSystemTrayIcon.Information, msecs=4000):
        self.tray_icon.showMessage(title, message, icon, msecs)

    def hide(self):
        self.tray_icon.hide()

    def show(self):
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_window_visibility()
        elif reason == QSystemTrayIcon.MiddleClick:
            self.main_window.test_network()

    def toggle_window_visibility(self):
        """Toggle main window visibility."""
        if self.main_window.isVisible():
            self.main_window.hide()
        else:
            self.show_window()

    def show_window(self):
        """Show and activate the main window."""
        self.main_window.show()
        self.main_window.activateWindow()
        self.main_window.raise_()

    def quit_application(self):
        """Clean up and quit the application."""
        if hasattr(self.main_window, "force_quit"):
            self.main_window.force_quit()
            return
        self.tray_icon.hide()
        QApplication.quit()