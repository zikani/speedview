from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QProgressBar, 
                           QLabel, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from ..update.updater import UpdateChecker

class UpdateWorker(QThread):
    progress = pyqtSignal(float)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, updater):
        super().__init__()
        self.updater = updater

    def run(self):
        try:
            update_file = self.updater.download_update(
                progress_callback=lambda p: self.progress.emit(p)
            )
            if update_file:
                self.finished.emit(update_file)
            else:
                self.error.emit("Failed to download update")
        except Exception as e:
            self.error.emit(str(e))

class UpdateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.updater = UpdateChecker()
        self.init_ui()
        self.check_for_updates()

    def init_ui(self):
        self.setWindowTitle("Software Update")
        self.setFixedSize(400, 150)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Checking for updates...")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        self.update_button = QPushButton("Update Now")
        self.update_button.clicked.connect(self.start_update)
        self.update_button.hide()
        layout.addWidget(self.update_button)
        
        self.setLayout(layout)

    def check_for_updates(self):
        if self.updater.check_for_updates():
            self.status_label.setText(
                f"New version {self.updater.latest_version} is available!\n"
                f"Current version: {self.updater.current_version}\n\n"
                f"Release Notes:\n{self.updater.release_notes}"
            )
            self.update_button.show()
        else:
            self.status_label.setText("You have the latest version!")
            self.close()

    def start_update(self):
        self.update_button.setEnabled(False)
        self.progress_bar.show()
        self.status_label.setText("Downloading update...")
        
        self.worker = UpdateWorker(self.updater)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.install_update)
        self.worker.error.connect(self.show_error)
        self.worker.start()

    def update_progress(self, progress):
        self.progress_bar.setValue(int(progress))

    def install_update(self, update_file):
        reply = QMessageBox.question(
            self, 
            'Install Update',
            'The update has been downloaded. Install now?\n'
            'The application will restart automatically.',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.updater.install_update(update_file):
                self.accept()
            else:
                self.show_error("Failed to install update")

    def show_error(self, error_message):
        QMessageBox.critical(self, "Update Error", error_message)
        self.close()