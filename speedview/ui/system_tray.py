from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QFontMetrics
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

class SystemTray:
    def __init__(self, main_window):
        self.main_window = main_window
        self.last_speed = 0
        self.setup_tray()

    def setup_tray(self):
        """Create the system tray icon and menu."""
        self.tray_icon = QSystemTrayIcon(self.main_window)
        
        # Create tray icon menu
        tray_menu = QMenu()
        
        # Add actions with icons
        actions = [
            ("Show", self.show_window, ":/icons/show-icon"),
            ("Float Mode", self.main_window.toggle_float_mode, ":/icons/float-icon"),
            ("Settings", self.main_window.open_settings, ":/icons/settings-icon"),
            ("Test Network", self.main_window.test_network, ":/icons/network-icon"),
            ("Exit", self.quit_application, ":/icons/exit-icon")
        ]
        
        for text, callback, icon in actions:
            action = QAction(QIcon(icon), text, self.main_window)
            action.triggered.connect(callback)
            tray_menu.addAction(action)
            if text == "Test Network":  # Add separator after network test
                tray_menu.addSeparator()
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # Initial icon setup
        self.update_tray_icon(0)
        
        # Show the tray icon
        self.tray_icon.show()
        
        # Connect signals
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def create_dynamic_icon(self, speed):
        """Create a dynamic tray icon showing the current speed."""
        size = 64  # Icon size
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background circle
        painter.setBrush(QColor(40, 40, 40))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, size-4, size-4)
        
        # Set text properties
        font = QFont("Arial", 10 if speed < 100 else 8)
        painter.setFont(font)
        painter.setPen(QColor(0, 240, 255))  # Cyan color
        
        # Draw speed text
        speed_text = f"{speed:.0f}" if speed >= 1 else f"{speed:.1f}"
        fm = QFontMetrics(font)
        text_rect = fm.boundingRect(speed_text)
        painter.drawText(
            (size - text_rect.width()) // 2,
            (size + fm.ascent() - fm.descent()) // 2,
            speed_text
        )
        
        painter.end()
        return QIcon(pixmap)

    def update_tray_icon(self, speed):
        """Update the tray icon and tooltip with current speed."""
        self.last_speed = speed
        icon = self.create_dynamic_icon(speed)
        self.tray_icon.setIcon(icon)
        
        # Enhanced tooltip with more information
        tooltip = (
            f"Network Speed Monitor\n"
            f"Current Speed: {speed:.2f} Mbps\n"
            f"Status: {'Active' if speed > 0 else 'Idle'}\n"
            f"Double-click to show/hide"
        )
        self.tray_icon.setToolTip(tooltip)

    def tray_icon_activated(self, reason):
        """Handle tray icon activation with more interaction options."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_window_visibility()
        elif reason == QSystemTrayIcon.MiddleClick:
            self.main_window.test_network()
        elif reason == QSystemTrayIcon.Context:
            pass  # Context menu handled automatically

    def toggle_window_visibility(self):
        """Toggle main window visibility."""
        if self.main_window.isVisible():
            self.main_window.hide()
        else:
            self.main_window.show()
            self.main_window.activateWindow()
            self.main_window.raise_()

    def show_window(self):
        """Show and activate the main window."""
        self.main_window.show()
        self.main_window.activateWindow()
        self.main_window.raise_()

    def quit_application(self):
        """Clean up and quit the application."""
        self.tray_icon.hide()  # Hide tray icon first
        QApplication.quit()