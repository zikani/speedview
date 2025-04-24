import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QShortcut, QApplication
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QByteArray
from PyQt5.QtGui import QKeySequence
from speedview.utils.svg_utils import update_test_network_svg
from speedview.ui.resources.svg_templates import TEST_NETWORK_SVG

class TestNetworkDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.test_in_progress = False
        self.download_speed = 0
        self.upload_speed = 0
        self.status = "Ready to test"
        self.setup_ui()
        self.setup_shortcuts()
        self.update_display()

    def update_display(self, status=None, download=None, upload=None):
        """Update the SVG display with current status and speed values."""
        from speedview.utils.svg_utils import update_test_network_svg
        from speedview.ui.resources.svg_templates import TEST_NETWORK_SVG
        # Use provided or current state
        status = status if status is not None else self.status
        download = download if download is not None else self.download_speed
        upload = upload if upload is not None else self.upload_speed
        svg_content = update_test_network_svg(TEST_NETWORK_SVG, status, download, upload)
        self.svg_widget.load(QByteArray(svg_content.encode('utf-8')))

    def setup_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("Network Test")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.svg_widget = QSvgWidget()
        self.layout.addWidget(self.svg_widget)
        
        # Enable mouse events
        self.svg_widget.mousePressEvent = self.handle_svg_mouse_press
        # Initial SVG display
        self.update_display()

    def handle_svg_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            # Check if within close button area
            if 75 <= pos.x() <= 225 and 290 <= pos.y() <= 330:
                self.close()
                return
            # Otherwise, start dragging
            self.dragging = True
            self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if getattr(self, 'dragging', False) and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_start_position)

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def set_status(self, status: str):
        """Update the status label in the SVG dialog."""
        self.status = status
        self.update_display()

    def show_results(self, download_speed, upload_speed):
        """Display the test results in the SVG dialog."""
        status = "Test Complete!"
        svg_content = update_test_network_svg(TEST_NETWORK_SVG, status, download_speed, upload_speed)
        self.svg_widget.load(QByteArray(svg_content.encode('utf-8')))

    def show_failure(self):
        """Display a failure message in the SVG dialog."""
        status = "Test Failed"
        svg_content = update_test_network_svg(TEST_NETWORK_SVG, status, 0, 0)
        self.svg_widget.load(QByteArray(svg_content.encode('utf-8')))

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Esc"), self, self.close)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = TestNetworkDialog()
    dlg.show()
    sys.exit(app.exec_())
