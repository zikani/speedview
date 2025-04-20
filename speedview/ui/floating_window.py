from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QShortcut
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QTimer, QByteArray
from PyQt5.QtGui import QKeySequence
from speedview.utils.svg_utils import update_svg_speed, save_svg_to_file
from speedview.controllers.network_controller import NetworkController

class FloatingWindow(QWidget):
    def __init__(self, speed_controller, settings, network_controller):
        super().__init__()
        self.speed_controller = speed_controller
        self.settings = settings
        self.network_controller = network_controller
        
        self.setup_ui()
        self.setup_shortcuts()
        
        # Initial state
        self.dragging = False
        self.drag_start_position = None
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(500)  
        
        # Initial display
        self.update_display()
        
        # Set window flags without transparency
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
    
    def setup_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("SpeedView - Floating Mode")
        self.resize(250, 80)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.svg_widget = QSvgWidget()
        self.layout.addWidget(self.svg_widget)

        # Enable dragging
        self.svg_widget.mousePressEvent = self.handle_mouse_press
    
    def setup_shortcuts(self):
        """Configure keyboard shortcuts"""
        QShortcut(QKeySequence("Esc"), self, self.hide)
    
    def update_display(self):
        """Update the display with current network stats"""
        # Get current speeds
        download_speed, upload_speed = self.speed_controller.get_current_speeds()
        display_speed = upload_speed if self.settings.show_upload_speed else download_speed

        # Update signal strength and connection info
        signal_strength = self.network_controller.signal_strength  # Actual signal strength
        connection_type, band = self.network_controller.get_connection_info()  # Get connection type and band
        
        # Generate SVG content
        svg_content = self.generate_svg_content(
            speed=display_speed,
            signal_strength=signal_strength,
            connection_type=connection_type,
            band=band
        )
        
        self.svg_widget.load(QByteArray(svg_content.encode('utf-8')))
    
    def generate_svg_content(self, speed, signal_strength, connection_type, band):
        """Generate the SVG content with current values"""
        return f"""
        <svg width="250" height="80" viewBox="0 0 250 80" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="darkGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#121212"/>
              <stop offset="100%" stop-color="#000000"/>
            </linearGradient>
            <filter id="shadow">
              <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#00FF8F" flood-opacity="0.5"/>
            </filter>
          </defs>
          
          <rect width="250" height="80" rx="10" ry="10" fill="url(#darkGradient)" filter="url(#shadow)"/>
          
          <text x="60" y="35" font-family="Arial" font-size="20" font-weight="bold" fill="#00FF8F" text-anchor="middle">{speed:.1f}</text>
          <text x="60" y="55" font-family="Arial" font-size="14" fill="#00FF8F" text-anchor="middle">Mbps</text>
          
          <g transform="translate(130, 30)">
            <rect x="0" y="10" width="5" height="10" rx="1" fill="{'#00FF8F' if signal_strength >= 1 else '#222'}"/>
            <rect x="10" y="5" width="5" height="15" rx="1" fill="{'#00FF8F' if signal_strength >= 2 else '#222'}"/>
            <rect x="20" y="0" width="5" height="20" rx="1" fill="{'#00FF8F' if signal_strength >= 3 else '#222'}"/>
            <rect x="30" y="-5" width="5" height="25" rx="1" fill="{'#00FF8F' if signal_strength >= 4 else '#222'}"/>
          </g>
          
          <text x="200" y="35" font-family="Arial" font-size="14" fill="#00FF8F" text-anchor="middle">{connection_type}</text>
          <text x="200" y="55" font-family="Arial" font-size="12" fill="#00FF8F" text-anchor="middle">{band}</text>
        </svg>
        """
    
    def handle_mouse_press(self, event):
        """Handle mouse press events for dragging"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle window dragging"""
        if self.dragging:
            self.move(event.globalPos() - self.drag_start_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Stop dragging"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()

    def closeEvent(self, event):
        """Clean up on window close"""
        self.update_timer.stop()
        event.accept()