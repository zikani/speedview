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
    CURRENT_CHANGELOG,
    DEFAULT_RELEASES_PAGE_URL,
)
from speedview.ui.update_dialog import UpdateDialog


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
    """About dialog displaying SpeedView's current features and release changelog."""

    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.settings = settings
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"About SpeedView v{APP_VERSION}")
        self.setMinimumSize(500, 480)
        self.resize(520, 520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAutoFillBackground(True)
        self.setStyleSheet(ABOUT_DIALOG_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QFrame(self)
        header.setObjectName("aboutHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(14, 12, 14, 12)
        header_layout.setSpacing(3)

        title_label = QLabel("SpeedView — Network Speed Meter")
        title_label.setObjectName("aboutTitle")
        self.version_label = QLabel(f"Version v{APP_VERSION}  •  Cross-Platform PyQt5 & SVG  •  MIT License")
        self.version_label.setObjectName("aboutMeta")

        header_layout.addWidget(title_label)
        header_layout.addWidget(self.version_label)
        layout.addWidget(header)

        features_heading = QLabel("CURRENT FEATURES")
        features_heading.setObjectName("sectionHeading")
        layout.addWidget(features_heading)

        self.features_view = QTextEdit(self)
        self.features_view.setReadOnly(True)
        self.features_view.setPlainText("\n".join(f"• {item}" for item in APP_FEATURES))
        layout.addWidget(self.features_view, 1)

        changelog_heading = QLabel(f"CHANGELOG — v{APP_VERSION}")
        changelog_heading.setObjectName("sectionHeading")
        layout.addWidget(changelog_heading)

        self.changelog_view = QTextEdit(self)
        self.changelog_view.setReadOnly(True)
        self.changelog_view.setPlainText("\n".join(f"• {entry}" for entry in CURRENT_CHANGELOG))
        layout.addWidget(self.changelog_view, 1)

        footer = QHBoxLayout()
        footer.setSpacing(8)

        releases_btn = QPushButton("GitHub Releases")
        releases_btn.clicked.connect(lambda: webbrowser.open(DEFAULT_RELEASES_PAGE_URL))
        footer.addWidget(releases_btn)

        updates_btn = QPushButton("Check for Updates")
        updates_btn.clicked.connect(self.open_updater)
        footer.addWidget(updates_btn)

        footer.addStretch(1)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("primaryBtn")
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)

        layout.addLayout(footer)

    def open_updater(self):
        dialog = UpdateDialog(parent=self, settings=self.settings, force_check=True)
        dialog.exec_()
