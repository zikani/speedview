from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QProgressBar,
    QLabel,
    QPushButton,
    QMessageBox,
    QTextEdit,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from ..update.updater import UpdateChecker
from ..utils.icon_utils import get_app_icon


class UpdateWorker(QThread):
    progress = pyqtSignal(float)
    bytes_progress = pyqtSignal(int, int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, updater):
        super().__init__()
        self.updater = updater

    def run(self):
        try:
            update_file = self.updater.download_update(
                progress_callback=lambda p: self.progress.emit(p),
                bytes_callback=lambda d, t: self.bytes_progress.emit(d, t),
            )
            if update_file:
                self.finished.emit(update_file)
            else:
                self.error.emit("Failed to download update package from GitHub Releases.")
        except Exception as e:
            self.error.emit(str(e))


class UpdateDialog(QDialog):
    def __init__(self, parent=None, settings=None, force_check=True, auto_check=True):
        super().__init__(parent)
        self.settings = settings
        self.force_check = force_check
        self.updater = UpdateChecker(settings=settings)
        self.init_ui()
        if auto_check:
            self.check_for_updates()

    def init_ui(self):
        self.setWindowTitle("SpeedView Software Update")
        self.setWindowIcon(get_app_icon())
        self.setMinimumSize(520, 440)
        self.resize(560, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAutoFillBackground(True)
        self.setStyleSheet(
            "QDialog { background-color: #0B1220; color: #F2F6FF; font-family: Inter, 'Segoe UI', Arial, sans-serif; }"
            "QFrame#updateHeader { background-color: #111B2E; border: 1px solid #1E2E4A; border-radius: 12px; }"
            "QLabel { color: #CBD5F5; font-size: 13px; background: transparent; }"
            "QLabel#headerTitle { color: #F2F6FF; font-size: 16px; font-weight: 700; }"
            "QLabel#versionMeta { color: #22D3EE; font-size: 12px; font-weight: 600; }"
            "QLabel#changelogHeading { color: #22D3EE; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; }"
            "QTextEdit { background-color: #080E1A; color: #E2ECFF; border: 1px solid #243656; border-radius: 10px; padding: 8px 10px; font-size: 12.5px; }"
            "QProgressBar { background-color: #111B2E; border: 1px solid #243656; border-radius: 6px; text-align: center; color: #F2F6FF; }"
            "QProgressBar::chunk { background-color: #22D3EE; border-radius: 5px; }"
            "QPushButton { background-color: #16233B; color: #E2ECFF; border: 1px solid #283C61; border-radius: 8px; padding: 8px 16px; font-weight: 600; }"
            "QPushButton:hover { background-color: #1E2F4E; border-color: #22D3EE; color: #FFFFFF; }"
            "QPushButton#primaryBtn { background-color: #2563EB; color: #FFFFFF; border: 1px solid #3B82F6; font-weight: 700; }"
            "QPushButton#primaryBtn:hover { background-color: #3B82F6; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QFrame(self)
        header.setObjectName("updateHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 12, 14, 12)
        header_layout.setSpacing(12)

        icon_label = QLabel(self)
        icon = get_app_icon()
        if not icon.isNull():
            icon_label.setPixmap(icon.pixmap(36, 36))
        icon_label.setFixedSize(36, 36)
        header_layout.addWidget(icon_label)

        title_col = QVBoxLayout()
        title_col.setSpacing(3)
        self.header_title = QLabel("Software Update")
        self.header_title.setObjectName("headerTitle")
        self.version_label = QLabel(f"Installed version: v{self.updater.current_version}")
        self.version_label.setObjectName("versionMeta")
        title_col.addWidget(self.header_title)
        title_col.addWidget(self.version_label)
        header_layout.addLayout(title_col, 1)

        layout.addWidget(header)

        self.status_label = QLabel("Checking GitHub Releases for updates...")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.changelog_heading = QLabel("ALL VERSION CHANGELOGS & FEATURES")
        self.changelog_heading.setObjectName("changelogHeading")
        layout.addWidget(self.changelog_heading)

        self.changelog_view = QTextEdit(self)
        self.changelog_view.setReadOnly(True)
        self.changelog_view.setPlaceholderText("Release notes and version features will appear here.")
        self._set_changelog_text(self.updater.get_all_changelogs_markdown(include_builtin=True))
        layout.addWidget(self.changelog_view, 1)

        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch(1)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.reject)
        btn_row.addWidget(self.close_button)

        self.update_button = QPushButton("Download & Install")
        self.update_button.setObjectName("primaryBtn")
        self.update_button.clicked.connect(self.start_update)
        self.update_button.hide()
        btn_row.addWidget(self.update_button)

        layout.addLayout(btn_row)

    def _set_changelog_text(self, text):
        notes = (text or self.updater.get_all_changelogs_markdown(include_builtin=True)).strip()
        if hasattr(self.changelog_view, "setMarkdown"):
            self.changelog_view.setMarkdown(notes)
        else:
            self.changelog_view.setPlainText(notes)

    def check_for_updates(self):
        if self.updater.check_for_updates(force=self.force_check):
            has_direct_asset = bool(
                self.updater.download_url and self.updater.download_url != self.updater.release_page_url
            )
            self.header_title.setText(f"Update Available: v{self.updater.latest_version}")
            self.version_label.setText(
                f"Installed: v{self.updater.current_version}  →  New Release: v{self.updater.latest_version}"
            )
            self.status_label.setText(
                f"SpeedView v{self.updater.latest_version} is ready to download and install."
            )
            self.changelog_heading.setText(f"WHAT'S NEW IN v{self.updater.latest_version}")
            self.changelog_heading.show()
            self.changelog_view.show()
            self._set_changelog_text(self.updater.release_notes)
            self.update_button.setText("Download & Install" if has_direct_asset else "Open Release Page")
            self.update_button.show()
        else:
            self.header_title.setText("You Are Up to Date")
            self.version_label.setText(f"Installed version: v{self.updater.current_version}")
            self.status_label.setText("No newer release was found on GitHub Releases.")
            self.changelog_heading.setText("ALL VERSION CHANGELOGS & FEATURES")
            self.changelog_heading.show()
            self.changelog_view.show()
            combined = self.updater.release_notes or self.updater.get_all_changelogs_markdown(include_builtin=True)
            self._set_changelog_text(combined)
            self.update_button.hide()
            if not self.force_check:
                self.close()

    def start_update(self):
        if not self.updater.download_url or self.updater.download_url == self.updater.release_page_url:
            self.updater.open_release_page()
            self.accept()
            return

        self.update_button.setEnabled(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.status_label.setText("Downloading update package to temporary folder...")

        self.worker = UpdateWorker(self.updater)
        self.worker.progress.connect(self.update_progress)
        self.worker.bytes_progress.connect(self.update_bytes_progress)
        self.worker.finished.connect(self.install_update)
        self.worker.error.connect(self.show_error)
        self.worker.start()

    def update_progress(self, progress):
        if progress < 0:
            if self.progress_bar.maximum() != 0:
                self.progress_bar.setRange(0, 0)
        else:
            if self.progress_bar.maximum() == 0:
                self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(int(progress))

    def update_bytes_progress(self, downloaded, total):
        mb = downloaded / (1024 * 1024)
        if total > 0:
            total_mb = total / (1024 * 1024)
            self.status_label.setText(
                f"Downloading update package... {mb:.2f} / {total_mb:.2f} MB"
            )
        else:
            self.status_label.setText(f"Downloading update package... {mb:.2f} MB")

    def _find_force_quit_host(self):
        widget = self.parent()
        while widget is not None:
            if hasattr(widget, 'force_quit'):
                return widget
            widget = widget.parent() if hasattr(widget, 'parent') else None
        return None

    def install_update(self, update_file):
        reply = QMessageBox.question(
            self,
            'Install Update',
            f'Update downloaded and extracted in:\n{self.updater.staged_dir or update_file}\n\n'
            'Install now? SpeedView will close, replace its files, and restart automatically.',
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            if self.updater.install_update(update_file, restart=True):
                self.accept()
                host = self._find_force_quit_host()
                if host is not None:
                    host.force_quit()
                else:
                    app = QApplication.instance()
                    if app is not None:
                        app.quit()
            else:
                self.show_error("Failed to launch the updater helper script.")
        else:
            self.update_button.setEnabled(True)
            self.status_label.setText("Update staged. Click Download & Install whenever ready.")

    def show_error(self, error_message):
        self.progress_bar.hide()
        self.update_button.setEnabled(True)
        self.status_label.setText(f"Update error: {error_message}")
        QMessageBox.critical(self, "Update Error", error_message)