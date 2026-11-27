from PyQt5.QtWidgets import QApplication
from speedview.ui.main_window import MainWindow


class NetworkSpeedMeter(MainWindow):
    """Consolidated application main window entry point."""

    def __init__(self, settings=None, speed_controller=None, network_controller=None):
        super().__init__(
            settings=settings,
            speed_controller=speed_controller,
            network_controller=network_controller,
        )


if __name__ == '__main__':
    app = QApplication([])
    window = NetworkSpeedMeter()
    if not window.settings.start_minimized and not window.settings.is_floating:
        window.show()
    app.exec_()