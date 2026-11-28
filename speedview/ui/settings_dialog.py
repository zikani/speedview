from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QFormLayout,
    QLineEdit,
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QMessageBox,
    QGroupBox,
    QVBoxLayout,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QWidget,
    QFrame,
)
from PyQt5.QtCore import Qt
import psutil

from speedview.config.config import APP_VERSION, DEFAULT_RELEASES_PAGE_URL
from speedview.config.windows import apply_startup_setting
from speedview.update.updater import UpdateChecker


SETTINGS_MODERN_QSS = """
QDialog {
    background-color: #0B1220;
    color: #F2F6FF;
    font-family: Inter, 'Segoe UI', Roboto, Arial, sans-serif;
    font-size: 13px;
}
QScrollArea {
    background-color: transparent;
    border: none;
}
QWidget#settingsContent {
    background-color: #0B1220;
}
QFrame#headerCard {
    background-color: #111B2E;
    border: 1px solid #1E2E4A;
    border-radius: 14px;
}
QLabel#titleLabel {
    color: #F2F6FF;
    font-size: 18px;
    font-weight: 700;
}
QLabel#subtitleLabel {
    color: #8FA3C9;
    font-size: 12px;
}
QGroupBox {
    background-color: #111B2E;
    border: 1px solid #1E2E4A;
    border-radius: 12px;
    margin-top: 14px;
    padding: 16px 14px 12px 14px;
    font-weight: 700;
    font-size: 12px;
    color: #22D3EE;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: 4px;
    padding: 0 6px;
    background-color: #0B1220;
    color: #22D3EE;
    letter-spacing: 0.6px;
}
QLabel {
    color: #CBD5F5;
    font-size: 12.5px;
    background: transparent;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #080E1A;
    color: #F2F6FF;
    border: 1px solid #243656;
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 22px;
    selection-background-color: #2563EB;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #22D3EE;
}
QComboBox:disabled, QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #0D1524;
    color: #5C6E91;
    border-color: #182338;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #0E1628;
    color: #F2F6FF;
    border: 1px solid #243656;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
}
QCheckBox {
    color: #E2ECFF;
    spacing: 8px;
    background: transparent;
}
QCheckBox::indicator {
    width: 17px;
    height: 17px;
    border-radius: 5px;
    border: 1.5px solid #334A70;
    background-color: #080E1A;
}
QCheckBox::indicator:checked {
    background-color: #22D3EE;
    border-color: #22D3EE;
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
QPushButton:pressed {
    background-color: #132036;
}
QPushButton#headerPill {
    background-color: #16233B;
    color: #9FB3D9;
    border: 1px solid #243656;
    border-radius: 14px;
    padding: 5px 12px;
    font-size: 11.5px;
}
QPushButton#headerPill:hover {
    color: #22D3EE;
    border-color: #22D3EE;
}
QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2563EB, stop:1 #1E40AF);
    color: #FFFFFF;
    border: 1px solid #3B82F6;
    border-radius: 9px;
    padding: 8px 18px;
    font-weight: 700;
}
QPushButton#primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3B82F6, stop:1 #2563EB);
}
QScrollBar:vertical {
    background: #0B1220;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #243656;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QMessageBox {
    background-color: #0E1628;
    color: #F2F6FF;
}
QMessageBox QLabel {
    color: #F2F6FF;
}
"""


class SettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        if settings is None:
            raise ValueError("Settings object must be provided")
        self.settings = settings
        self.updater = UpdateChecker(settings=self.settings)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("SpeedView Settings")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAutoFillBackground(True)
        self.setStyleSheet(SETTINGS_MODERN_QSS)
        self.setMinimumSize(500, 520)
        self.resize(520, 600)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        self.create_header(root_layout)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setObjectName("settingsContent")
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(2, 2, 6, 4)
        self.layout.setSpacing(10)

        self.create_monitoring_group()
        self.create_behavior_group()
        self.create_display_group()
        self.create_notification_group()
        self.layout.addStretch(1)

        scroll.setWidget(content)
        root_layout.addWidget(scroll, 1)

        self.create_button_box(root_layout)
        self.load_settings()

    def create_header(self, parent_layout):
        """Create modern header banner with quick Help / About / Updates actions."""
        header = QFrame(self)
        header.setObjectName("headerCard")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 12, 14, 12)
        header_layout.setSpacing(10)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title = QLabel("SpeedView Settings")
        title.setObjectName("titleLabel")
        subtitle = QLabel(f"Configure interface, gauge scaling, tray & alerts  •  v{APP_VERSION}")
        subtitle.setObjectName("subtitleLabel")
        text_col.addWidget(title)
        text_col.addWidget(subtitle)
        header_layout.addLayout(text_col, 1)

        help_btn = QPushButton("Help")
        help_btn.setObjectName("headerPill")
        help_btn.clicked.connect(self.show_help)
        header_layout.addWidget(help_btn)

        about_btn = QPushButton("About")
        about_btn.setObjectName("headerPill")
        about_btn.clicked.connect(self.show_about)
        header_layout.addWidget(about_btn)

        updates_btn = QPushButton("Updates")
        updates_btn.setObjectName("headerPill")
        updates_btn.clicked.connect(self.check_updates)
        header_layout.addWidget(updates_btn)

        parent_layout.addWidget(header)

    def show_help(self):
        """Show help documentation."""
        QMessageBox.information(
            self,
            "SpeedView Help",
            "SpeedView - Network Speed Meter:\n\n"
            "1. Monitoring:\n"
            "   - Choose a specific network interface or enable Auto-select.\n"
            "   - Configure download/upload gauge scales and refresh rate.\n\n"
            "2. Behavior & Background:\n"
            "   - Minimizing sends SpeedView to the system tray.\n"
            "   - Closing the main window opens the compact Float widget.\n"
            "   - Closing the Float widget keeps background monitoring running in the tray.\n\n"
            "3. Display & Alerts:\n"
            "   - Switch between Mbps, MB/s, and Kbps units.\n"
            "   - Set high-speed notification thresholds.",
        )

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About SpeedView",
            f"SpeedView - Network Speed Meter v{APP_VERSION}\n\n"
            "A cross-platform real-time network speed monitor built with PyQt5 and SVG.\n\n"
            f"Releases: {DEFAULT_RELEASES_PAGE_URL}\n"
            "Licensed under MIT",
        )

    def check_updates(self):
        """Check for software updates immediately (bypassing the 3-day cooldown)."""
        try:
            self.updater = UpdateChecker(settings=self.settings)
            has_update = self.updater.check_for_updates(force=True)

            if has_update:
                reply = QMessageBox.question(
                    self,
                    "Update Available",
                    f"Version {self.updater.latest_version} is available. Download and install update now?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    self.start_update()
            else:
                QMessageBox.information(self, "Up to Date", "You are running the latest version.")
        except Exception as e:
            QMessageBox.warning(self, "Update Check Failed", f"Could not check for updates:\n{str(e)}")

    def create_monitoring_group(self):
        """Create monitoring settings card."""
        group = QGroupBox("MONITORING & INTERFACE")
        layout = QFormLayout()
        layout.setSpacing(10)
        layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        interface_layout = QVBoxLayout()
        interface_layout.setSpacing(6)

        interface_select_layout = QHBoxLayout()
        interface_select_layout.setSpacing(8)
        self.network_interface_combo = QComboBox()
        self.refresh_interfaces_button = QPushButton("Refresh")
        self.refresh_interfaces_button.clicked.connect(self.refresh_interfaces)
        interface_select_layout.addWidget(self.network_interface_combo, 1)
        interface_select_layout.addWidget(self.refresh_interfaces_button)
        interface_layout.addLayout(interface_select_layout)

        self.auto_select_checkbox = QCheckBox("Auto-select best active interface")
        self.auto_select_checkbox.setToolTip("Automatically switch to the best available network interface")
        self.auto_select_checkbox.toggled.connect(
            lambda checked: self.network_interface_combo.setEnabled(not checked)
        )
        interface_layout.addWidget(self.auto_select_checkbox)

        self.refresh_interfaces()
        layout.addRow("Network Interface:", interface_layout)

        self.max_speed_input = QSpinBox()
        self.max_speed_input.setRange(1, 10000)
        self.max_speed_input.setSuffix(" Mbps")
        self.max_speed_input.setToolTip("Maximum expected download speed for gauge scaling")
        layout.addRow("Max Download Scale:", self.max_speed_input)

        self.max_upload_input = QSpinBox()
        self.max_upload_input.setRange(1, 10000)
        self.max_upload_input.setSuffix(" Mbps")
        self.max_upload_input.setToolTip("Maximum expected upload speed for gauge scaling")
        layout.addRow("Max Upload Scale:", self.max_upload_input)

        self.update_interval_input = QDoubleSpinBox()
        self.update_interval_input.setRange(0.1, 60.0)
        self.update_interval_input.setSuffix(" s")
        self.update_interval_input.setSingleStep(0.5)
        self.update_interval_input.setToolTip("How often to sample network throughput")
        layout.addRow("Update Interval:", self.update_interval_input)

        self.update_url_input = QLineEdit()
        self.update_url_input.setPlaceholderText("https://api.github.com/repos/...")
        self.update_url_input.setToolTip("URL used to check for software updates")
        layout.addRow("Update URL:", self.update_url_input)

        group.setLayout(layout)
        self.layout.addWidget(group)

    def refresh_interfaces(self):
        """Refresh the list of network interfaces."""
        try:
            self.network_interface_combo.clear()
            interfaces = []
            stats = psutil.net_if_stats()

            for interface, stat in stats.items():
                if stat.isup and not any(x in interface.lower() for x in ['vethernet', 'vmware', 'virtual']):
                    speed = f"{stat.speed} Mbps" if stat.speed else "Active"
                    self.network_interface_combo.addItem(f"{interface} ({speed})", interface)
                    interfaces.append(interface)

            for interface, stat in stats.items():
                if stat.isup and any(x in interface.lower() for x in ['vethernet', 'vmware', 'virtual']):
                    self.network_interface_combo.addItem(f"{interface} (Virtual - Active)", interface)
                    interfaces.append(interface)

            for interface, stat in stats.items():
                if not stat.isup:
                    self.network_interface_combo.addItem(f"{interface} (Inactive)", interface)
                    interfaces.append(interface)

            if self.settings.selected_interface in interfaces:
                index = self.network_interface_combo.findData(self.settings.selected_interface)
                if index >= 0:
                    self.network_interface_combo.setCurrentIndex(index)
        except Exception as e:
            print(f"Error refreshing interfaces: {e}")
            self.network_interface_combo.addItem("No interfaces found", None)

    def create_behavior_group(self):
        """Create application behavior card."""
        group = QGroupBox("BEHAVIOR & SYSTEM TRAY")
        layout = QVBoxLayout()
        layout.setSpacing(8)

        self.start_on_startup_checkbox = QCheckBox("Start SpeedView automatically on system startup")
        self.start_on_startup_checkbox.setToolTip("Launch SpeedView automatically when you log in")
        layout.addWidget(self.start_on_startup_checkbox)

        self.start_minimized_checkbox = QCheckBox("Start minimized in system tray on launch")
        self.start_minimized_checkbox.setToolTip("Start the application hidden in the system tray")
        layout.addWidget(self.start_minimized_checkbox)

        self.minimize_to_tray_checkbox = QCheckBox("Keep system tray icon active for background monitoring")
        self.minimize_to_tray_checkbox.setToolTip("Minimize to system tray and keep tracking speed & data usage")
        layout.addWidget(self.minimize_to_tray_checkbox)

        self.close_to_tray_checkbox = QCheckBox("Switch to Float / Tray when closing windows")
        self.close_to_tray_checkbox.setToolTip("Keep running in background instead of quitting on window close")
        layout.addWidget(self.close_to_tray_checkbox)

        self.auto_update_checkbox = QCheckBox("Automatically check & install updates in background (every 3 days)")
        self.auto_update_checkbox.setToolTip(
            "Check GitHub Releases every 3 days to avoid API rate limits and auto-apply updates"
        )
        layout.addWidget(self.auto_update_checkbox)

        group.setLayout(layout)
        self.layout.addWidget(group)

    def create_display_group(self):
        """Create display settings card."""
        group = QGroupBox("DISPLAY & UNITS")
        layout = QFormLayout()
        layout.setSpacing(10)

        self.speed_unit_combo = QComboBox()
        self.speed_unit_combo.addItems(["Mbps", "MB/s", "Kbps"])
        self.speed_unit_combo.setToolTip("Unit to display network speeds")
        layout.addRow("Speed Unit:", self.speed_unit_combo)

        self.show_upload_speed_checkbox = QCheckBox("Show upload speed on main gauge instead of download")
        self.show_upload_speed_checkbox.setToolTip("Toggle primary gauge display between Download and Upload")
        layout.addRow("", self.show_upload_speed_checkbox)

        group.setLayout(layout)
        self.layout.addWidget(group)

    def create_notification_group(self):
        """Create notification settings card."""
        group = QGroupBox("NOTIFICATIONS")
        layout = QFormLayout()
        layout.setSpacing(10)

        self.enable_notifications_checkbox = QCheckBox("Enable desktop high-speed & speed-test alerts")
        self.enable_notifications_checkbox.setToolTip("Enable system tray notifications")
        layout.addRow("", self.enable_notifications_checkbox)

        self.notification_threshold = QSpinBox()
        self.notification_threshold.setRange(1, 10000)
        self.notification_threshold.setSuffix(" Mbps")
        self.notification_threshold.setToolTip("Speed threshold for notifications")
        layout.addRow("Alert Threshold:", self.notification_threshold)

        group.setLayout(layout)
        self.layout.addWidget(group)

    def create_button_box(self, parent_layout):
        """Create the dialog footer button box."""
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults
        )
        ok_btn = self.buttons.button(QDialogButtonBox.Ok)
        ok_btn.setText("Save Settings")
        ok_btn.setObjectName("primaryBtn")
        cancel_btn = self.buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setText("Cancel")
        restore_btn = self.buttons.button(QDialogButtonBox.RestoreDefaults)
        restore_btn.setText("Restore Defaults")

        restore_btn.clicked.connect(self.restore_defaults)
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        parent_layout.addWidget(self.buttons)

    def load_settings(self):
        """Load current settings into the dialog."""
        self.max_speed_input.setValue(int(self.settings.max_speed))
        self.max_upload_input.setValue(int(self.settings.max_upload))
        self.update_interval_input.setValue(float(self.settings.update_interval))
        self.speed_unit_combo.setCurrentText(self.settings.speed_unit)

        auto_select = bool(getattr(self.settings, 'auto_select_interface', False)) or self.settings.selected_interface is None
        self.auto_select_checkbox.setChecked(auto_select)
        self.network_interface_combo.setEnabled(not auto_select)

        if self.settings.selected_interface:
            idx = self.network_interface_combo.findData(self.settings.selected_interface)
            if idx >= 0:
                self.network_interface_combo.setCurrentIndex(idx)

        self.start_on_startup_checkbox.setChecked(bool(getattr(self.settings, 'start_on_startup', False)))
        self.start_minimized_checkbox.setChecked(bool(self.settings.start_minimized))
        self.minimize_to_tray_checkbox.setChecked(bool(self.settings.minimize_to_tray))
        self.close_to_tray_checkbox.setChecked(bool(self.settings.close_to_tray))
        self.auto_update_checkbox.setChecked(bool(getattr(self.settings, 'auto_update', True)))
        self.show_upload_speed_checkbox.setChecked(bool(self.settings.show_upload_speed))
        self.enable_notifications_checkbox.setChecked(bool(self.settings.enable_notifications))
        self.notification_threshold.setValue(int(self.settings.notification_threshold))
        self.update_url_input.setText(self.settings.update_url or "")

    def validate_and_accept(self):
        """Validate inputs, apply to settings, and save."""
        try:
            if not self.auto_select_checkbox.isChecked():
                current_index = self.network_interface_combo.currentIndex()
                interface = self.network_interface_combo.itemData(current_index)

                if not interface:
                    raise ValueError("No valid network interface available")

                stats = psutil.net_if_stats()
                if interface not in stats or not stats[interface].isup:
                    reply = QMessageBox.question(
                        self,
                        "Interface Warning",
                        f"The selected interface '{interface}' appears to be inactive. "
                        "Would you like to select it anyway?",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if reply == QMessageBox.No:
                        return

            self._update_settings()

            try:
                self.settings.save()
            except Exception as e:
                raise ValueError(f"Failed to save settings: {str(e)}")

            super().accept()
        except ValueError as e:
            QMessageBox.critical(self, "Validation Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Settings Error", f"An unexpected error occurred:\n{str(e)}")

    def _update_settings(self):
        """Update settings from UI values."""
        auto_select = self.auto_select_checkbox.isChecked()
        self.settings.auto_select_interface = auto_select

        if auto_select:
            self.settings.selected_interface = self.settings._get_default_interface()
        else:
            current_index = self.network_interface_combo.currentIndex()
            self.settings.selected_interface = self.network_interface_combo.itemData(current_index)

        self.settings.max_speed = self.max_speed_input.value()
        self.settings.max_upload = self.max_upload_input.value()
        self.settings.update_interval = self.update_interval_input.value()
        self.settings.speed_unit = self.speed_unit_combo.currentText()
        self.settings.start_on_startup = self.start_on_startup_checkbox.isChecked()
        self.settings.start_minimized = self.start_minimized_checkbox.isChecked()
        self.settings.minimize_to_tray = self.minimize_to_tray_checkbox.isChecked()
        self.settings.close_to_tray = self.close_to_tray_checkbox.isChecked()
        self.settings.auto_update = self.auto_update_checkbox.isChecked()
        self.settings.show_upload_speed = self.show_upload_speed_checkbox.isChecked()
        self.settings.enable_notifications = self.enable_notifications_checkbox.isChecked()
        self.settings.notification_threshold = self.notification_threshold.value()
        self.settings.update_url = self.update_url_input.text().strip()
        apply_startup_setting(bool(self.settings.start_on_startup))

    def save_settings(self):
        """Save dialog values back to settings object."""
        self._update_settings()
        self.settings.save()

    def restore_defaults(self):
        """Restore default settings."""
        reply = QMessageBox.question(
            self,
            "Restore Defaults",
            "Are you sure you want to restore all settings to their default values?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.settings.restore_defaults()
            self.load_settings()
            QMessageBox.information(
                self,
                "Defaults Restored",
                "All settings have been restored to default values.",
            )

    def start_update(self):
        """Download and apply the update package via temp staging + helper script."""
        if not self.updater.update_available:
            if not self.updater.check_for_updates(force=True):
                QMessageBox.information(self, "No Updates", "You are already using the latest version.")
                return

        if not self.updater.download_url or self.updater.download_url == self.updater.release_page_url:
            self.updater.open_release_page()
            return

        update_file = self.updater.download_update()
        if not update_file:
            QMessageBox.warning(self, "Update Failed", "Failed to download the update.")
            return

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
                QMessageBox.warning(self, "Update Failed", "Failed to launch the updater helper script.")
        else:
            QMessageBox.information(
                self,
                "Update Downloaded",
                f"Update downloaded and extracted to:\n{self.updater.staged_dir or update_file}\n\n"
                "Automatic replace & restart is active in standalone frozen releases.",
            )
