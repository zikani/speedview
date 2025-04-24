import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QShortcut
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QTimer, QByteArray
from PyQt5.QtGui import QKeySequence
from speedview.utils.svg_utils import update_floating_svg, save_svg_to_file
from speedview.controllers.network_controller import NetworkController
from speedview.ui.resources.svg_templates import FLOATING_SVG_TEMPLATE

class FloatingWindow(QWidget):
    def __init__(self, speed_controller, settings, network_controller):
        super().__init__()
        self.speed_controller = speed_controller
        self.settings = settings
        self.network_controller = network_controller
        logging.info("FloatingWindow initialized")
        
        self.setup_ui()
        self.setup_shortcuts()
        
        # Initial state
        self.dragging = False
        self.drag_start_position = None

        # Connect to speed_updated signal for thread-safe UI updates
        if hasattr(self.speed_controller, 'speed_updated'):
            self.speed_controller.speed_updated.connect(self.on_speed_updated)
        # Connect to network_controller connection_updated signal
        if hasattr(self.network_controller, 'connection_updated'):
            self.network_controller.connection_updated.connect(self.on_connection_updated)
        
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

        # Enable dragging and button interaction
        self.svg_widget.mousePressEvent = self.handle_svg_mouse_press
    
    def setup_shortcuts(self):
        """Configure keyboard shortcuts"""
        QShortcut(QKeySequence("Esc"), self, self.hide)
    
    def update_display(self, forced_speeds=None):
        """Update the display with current network stats"""
        # Allow forced speeds from signal for thread safety
        if forced_speeds is not None:
            download_speed, upload_speed = forced_speeds
        else:
            try:
                download_speed, upload_speed = self.speed_controller.get_current_speeds()
            except Exception:
                logging.exception("Failed to get current speeds in FloatingWindow")
                download_speed, upload_speed = 0, 0
        # Defensive: avoid crash if None
        download_speed = download_speed if download_speed is not None else 0
        upload_speed = upload_speed if upload_speed is not None else 0
        display_speed = upload_speed if self.settings.show_upload_speed else download_speed

        logging.info(f"FloatingWindow display update: download={download_speed}, upload={upload_speed}")

        # Update signal strength and connection info
        signal_strength = getattr(self.network_controller, 'signal_strength', 0)
        try:
            connection_type, band = self.network_controller.get_connection_info()
        except Exception:
            logging.exception("Failed to get connection info in FloatingWindow")
            connection_type, band = "Unknown", ""

        # Update SVG content using the template
        svg_content = update_floating_svg(
            FLOATING_SVG_TEMPLATE,
            speed=display_speed,
            signal_strength=signal_strength,
            connection_type=connection_type,
            band=band
        )
        
        logging.info("Loading SVG into floating window SVG widget...")
        self.svg_widget.load(QByteArray(svg_content.encode('utf-8')))
        logging.info("SVG loaded successfully in floating window.")
    
    def on_speed_updated(self, download_speed, upload_speed):
        """Slot to handle speed updates from controller in a thread-safe way."""
        if download_speed == 0 and upload_speed == 0:
            logging.warning("Speed test failed or no network detected (both speeds zero) in FloatingWindow.")
            # Disabled notification popup in floating mode
            return
        logging.info(f"Speed updated in FloatingWindow: download={download_speed}, upload={upload_speed}")
        self.update_display((download_speed, upload_speed))

    def on_connection_updated(self, status, strength):
        """Slot to handle connection status updates from network controller."""
        logging.info(f"FloatingWindow: Connection updated: {status}, strength={strength}")
        self.update_display()


    
    def handle_svg_mouse_press(self, event):
        """Handle mouse press events for dragging and buttons with proper coordinate mapping"""
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            
            # Map widget coordinates to SVG coordinates
            widget_width = self.svg_widget.width()
            widget_height = self.svg_widget.height()
            svg_width, svg_height = 250, 80  # Floating SVG viewBox size
            scale_x = svg_width / widget_width
            scale_y = svg_height / widget_height
            svg_x = pos.x() * scale_x
            svg_y = pos.y() * scale_y
            
            # Check for button clicks
            # Close button at (230, 20) with radius 8
            close_btn_center = (230, 20)
            close_btn_radius = 8
            dx = svg_x - close_btn_center[0]
            dy = svg_y - close_btn_center[1]
            if dx*dx + dy*dy <= close_btn_radius*close_btn_radius:
                logging.info("FloatingWindow: Close button clicked.")
                self.close()
                event.accept()
                return
                
            # Test Network button at (125, 60) with radius 15
            test_btn_center = (125, 60)
            test_btn_radius = 15
            dx = svg_x - test_btn_center[0]
            dy = svg_y - test_btn_center[1]
            if dx*dx + dy*dy <= test_btn_radius*test_btn_radius:
                logging.info("FloatingWindow: Test Network button clicked.")
                if hasattr(self.speed_controller, 'run_speed_test'):
                    self.speed_controller.run_speed_test()
                event.accept()
                return
                
            # Expand button at (20, 20) with radius 8
            expand_btn_center = (20, 20)
            expand_btn_radius = 8
            dx = svg_x - expand_btn_center[0]
            dy = svg_y - expand_btn_center[1]
            if dx*dx + dy*dy <= expand_btn_radius*expand_btn_radius:
                logging.info("FloatingWindow: Expand button clicked.")
                # Signal parent to switch back to main window
                self.close()
                if hasattr(self.settings, 'is_floating'):
                    self.settings.is_floating = False
                    self.settings.save()
                event.accept()
                return
                
            # If not on any button, start dragging
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