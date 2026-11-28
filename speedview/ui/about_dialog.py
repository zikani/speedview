import webbrowser
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QTextEdit,
)
from PyQt5.QtCore import Qt

from speedview.config.config import (
    APP_FEATURES,
    APP_VERSION,
    DEFAULT_RELEASES_PAGE_URL,
)
from speedview.ui.update_dialog import UpdateDialog
from speedview.update.updater import UpdateChecker
from speedview.utils.icon_utils import get_app_icon


ABOUT_DIALOG_QSS = """
QDialog {
    background-color: #0B1220;
    color: #F2F6FF;
    font-family: Inter, 'Segoe UI', Roboto, Arial, sans-serif;
    font-size: 13px;
}
QFrame#aboutHeader {
    background-color: #111B2E;
    border: 1px solid #1E2E4A;
    border-radius: 12px;
}
QLabel#aboutTitle {
    color: #F2F6FF;
    font-size: 18px;
    font-weight: 700;
}
QLabel#aboutMeta {
    color: #22D3EE;
    font-size: 12px;
    font-weight: 600;
}
QLabel#sectionHeading {
    color: #22D3EE;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
    margin-top: 4px;
}
QTextEdit {
    background-color: #080E1A;
    color: #E2ECFF;
    border: 1px solid #243656;
    border-radius: 10px;
    padding: 8px 10px;
    font-size: 12.5px;
}
QPushButton {
    background-color: #16233B;
    color: #E2ECFF;
    border: 1px solid #283C61;
    border-radius: 8px;
    padding: 7px 14px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #1E2F4E;
    border-color: #22D3EE;
    color: #FFFFFF;
}
QPushButton#primaryBtn {
    background-color: #2563EB;
    color: #FFFFFF;
    border: 1px solid #3B82F6;
    font-weight: 700;
}
QPushButton#primaryBtn:hover {
    background-color: #3B82F6;
}
"""


class AboutDialog(QDialog):
    """About dialog displaying SpeedView's current features and full release changelog history."""

    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.settings = settings
        self.updater = UpdateChecker(settings=self.settings)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"About SpeedView v{APP_VERSION}")
        self.setWindowIcon(get_app_icon())
        self.setMinimumSize(540, 540)
        self.resize(580, 580)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAutoFillBackground(True)
        self.setStyleSheet(ABOUT_DIALOG_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QFrame(self)
        header.setObjectName("aboutHeader")
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(14, 12, 14, 12)
        header_row.setSpacing(12)

        icon_label = QLabel(self)
        icon = get_app_icon()
        if not icon.isNull():
            icon_label.setPixmap(icon.pixmap(44, 44))
        icon_label.setFixedSize(44, 44)
        header_row.addWidget(icon_label)

        header_text_col = QVBoxLayout()
        header_text_col.setSpacing(3)
        title_label = QLabel("SpeedView — Network Speed Meter")
        title_label.setObjectName("aboutTitle")
        self.version_label = QLabel(f"Version v{APP_VERSION}  •  Cross-Platform PyQt5 & SVG  •  MIT License")
        self.version_label.setObjectName("aboutMeta")
        header_text_col.addWidget(title_label)
        header_text_col.addWidget(self.version_label)
        header_row.addLayout(header_text_col, 1)

        layout.addWidget(header)

        features_heading = QLabel("CURRENT FEATURES")
        features_heading.setObjectName("sectionHeading")
        layout.addWidget(features_heading)

        self.features_view = QTextEdit(self)
        self.features_view.setReadOnly(True)
        self.features_view.setPlainText("\n".join(f"• {item}" for item in APP_FEATURES))
        layout.addWidget(self.features_view, 1)

        changelog_heading = QLabel("RELEASE CHANGELOG & FEATURES (ALL VERSIONS)")
        changelog_heading.setObjectName("sectionHeading")
        layout.addWidget(changelog_heading)

        self.changelog_view = QTextEdit(self)
        self.changelog_view.setReadOnly(True)
        self._load_changelog_history(force_remote=False)
        layout.addWidget(self.changelog_view, 2)

        footer = QHBoxLayout()
        footer.setSpacing(8)

        releases_btn = QPushButton("GitHub Releases")
        releases_btn.clicked.connect(lambda: webbrowser.open(DEFAULT_RELEASES_PAGE_URL))
        footer.addWidget(releases_btn)

        refresh_btn = QPushButton("Refresh Releases")
        refresh_btn.clicked.connect(lambda: self._load_changelog_history(force_remote=True))
        footer.addWidget(refresh_btn)

        updates_btn = QPushButton("Check for Updates")
        updates_btn.clicked.connect(self.open_updater)
        footer.addWidget(updates_btn)

        footer.addStretch(1)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("primaryBtn")
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)

        layout.addLayout(footer)

    def _load_changelog_history(self, force_remote=False):
        if force_remote:
            self.updater.fetch_all_releases(force=True)
        markdown_text = self.updater.get_all_changelogs_markdown(include_builtin=True)
        if hasattr(self.changelog_view, "setMarkdown"):
            self.changelog_view.setMarkdown(markdown_text)
        else:
            self.changelog_view.setPlainText(markdown_text)

    def open_updater(self):
        dialog = UpdateDialog(parent=self, settings=self.settings, force_check=True)
        dialog.exec_()
        self._load_changelog_history(force_remote=False)
