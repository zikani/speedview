from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QProgressBar,
    QLabel,
    QPushButton,
    QMessageBox,
)
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
    def __init__(self, parent=None, settings=None, force_check=True):
        super().__init__(parent)
        self.settings = settings
        self.force_check = force_check
        self.updater = UpdateChecker(settings=settings)
        self.init_ui()
        self.check_for_updates()

    def init_ui(self):
        self.setWindowTitle("Software Update")
        self.setFixedSize(440, 210)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAutoFillBackground(True)
        self.setStyleSheet(
            "QDialog { background-color: #0B1220; color: #F2F6FF; font-family: Inter, 'Segoe UI', Arial, sans-serif; }"
            "QLabel { color: #CBD5F5; font-size: 13px; }"
            "QProgressBar { background-color: #111B2E; border: 1px solid #243656; border-radius: 6px; text-align: center; color: #F2F6FF; }"
            "QProgressBar::chunk { background-color: #22D3EE; border-radius: 5px; }"
            "QPushButton { background-color: #2563EB; color: #FFFFFF; border: none; border-radius: 8px; padding: 8px 16px; font-weight: 700; }"
            "QPushButton:hover { background-color: #3B82F6; }"
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.status_label = QLabel("Checking for updates...")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.update_button = QPushButton("Download & Install")
        self.update_button.clicked.connect(self.start_update)
        self.update_button.hide()
        layout.addWidget(self.update_button)

        self.setLayout(layout)

    def check_for_updates(self):
        if self.updater.check_for_updates(force=self.force_check):
            has_direct_asset = bool(
                self.updater.download_url and self.updater.download_url != self.updater.release_page_url
            )
            self.update_button.setText("Download & Install" if has_direct_asset else "Open Release Page")
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
        if not self.updater.download_url or self.updater.download_url == self.updater.release_page_url:
            self.updater.open_release_page()
            self.accept()
            return

        self.update_button.setEnabled(False)
        self.progress_bar.show()
        self.status_label.setText("Downloading update package to temporary folder...")

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
            'The update package has been downloaded to a temporary folder.\n'
            'Install now? SpeedView will close, update its files, and restart automatically.',
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            if self.updater.can_self_replace():
                if self.updater.install_update(update_file, restart=True):
                    self.accept()
                    parent = self.parent()
                    if parent is not None and hasattr(parent, 'force_quit'):
                        parent.force_quit()
                    else:
                        app = QApplication.instance()
                        if app is not None:
                            app.quit()
                else:
                    self.show_error("Failed to launch update helper script")
            else:
                QMessageBox.information(
                    self,
                    "Update Downloaded",
                    f"Update archive downloaded and staged at:\n{self.updater.staged_dir or update_file}\n\n"
                    "Self-replacement activates automatically in packaged standalone builds.",
                )
                self.accept()

    def show_error(self, error_message):
        QMessageBox.critical(self, "Update Error", error_message)
        self.close()