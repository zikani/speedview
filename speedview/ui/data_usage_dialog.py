import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QShortcut, QApplication
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QByteArray, QTimer
from PyQt5.QtGui import QKeySequence

from speedview.models.data_usage import DataUsageTracker, format_bytes
from speedview.ui.resources.svg_templates import DATA_USAGE_SVG_TEMPLATE
from speedview.utils.svg_utils import apply_rounded_mask, update_data_usage_svg


class DataUsageDialog(QWidget):
    """Frameless SVG-rendered Data Usage window showing Daily/Monthly & App | Data | Date."""

    def __init__(self, tracker=None, parent=None):
        super().__init__(parent)
        self.tracker = tracker or DataUsageTracker()
        self.mode = "daily"
        self.dragging = False
        self.drag_start_position = None

        self.setup_ui()
        self.setup_shortcuts()
        self.refresh_display()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_display)
        self.refresh_timer.start(2000)

    def setup_ui(self):
        self.setWindowTitle("SpeedView - Data Usage")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")
        self.setFixedSize(520, 480)
        apply_rounded_mask(self, 4, 4, 512, 472, radius=24)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.svg_widget = QSvgWidget()
        self.svg_widget.setStyleSheet("background: transparent;")
        self.layout.addWidget(self.svg_widget)
        self.svg_widget.mousePressEvent = self.handle_svg_mouse_press

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Esc"), self, self.close)

    def refresh_display(self):
        daily_total, daily_rows = self.tracker.get_daily_usage()
        monthly_total, monthly_rows = self.tracker.get_monthly_usage()
        rows = daily_rows if self.mode == "daily" else monthly_rows

        svg_content = update_data_usage_svg(
            DATA_USAGE_SVG_TEMPLATE,
            daily_total_str=format_bytes(daily_total),
            monthly_total_str=format_bytes(monthly_total),
            rows=rows,
            mode=self.mode,
        )
        self.svg_widget.load(QByteArray(svg_content.encode("utf-8")))

    def handle_svg_mouse_press(self, event):
        if event.button() != Qt.LeftButton:
            return
        pos = event.pos()
        w = max(1, self.svg_widget.width())
        h = max(1, self.svg_widget.height())
        svg_x = pos.x() * (520.0 / w)
        svg_y = pos.y() * (480.0 / h)

        # Top-right close X (486, 26) r=11
        if (svg_x - 486) ** 2 + (svg_y - 26) ** 2 <= 169:
            self.close()
            event.accept()
            return

        # Bottom CLOSE button (185..335, 428..464)
        if 185 <= svg_x <= 335 and 428 <= svg_y <= 464:
            self.close()
            event.accept()
            return

        # DAILY tab (28..133, 130..160)
        if 28 <= svg_x <= 133 and 130 <= svg_y <= 160:
            self.mode = "daily"
            self.refresh_display()
            event.accept()
            return

        # MONTHLY tab (143..258, 130..160)
        if 143 <= svg_x <= 258 and 130 <= svg_y <= 160:
            self.mode = "monthly"
            self.refresh_display()
            event.accept()
            return

        # RESET button (392..492, 130..160)
        if 392 <= svg_x <= 492 and 130 <= svg_y <= 160:
            self.tracker.clear_usage()
            self.refresh_display()
            event.accept()
            return

        # Drag window anywhere else
        self.dragging = True
        self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()
        event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        event.accept()

    def closeEvent(self, event):
        self.refresh_timer.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = DataUsageDialog()
    dlg.show()
    sys.exit(app.exec_())
