from PyQt5.QtWidgets import (QDialog, QFormLayout, QLineEdit, QCheckBox, QComboBox, 
                            QDialogButtonBox, QMessageBox, QGroupBox, QVBoxLayout, 
                            QSpinBox, QDoubleSpinBox, QLabel, QMenuBar, QMenu, QAction, QPushButton, QHBoxLayout)
from PyQt5.QtCore import Qt
import psutil

from speedview.config.config import APP_VERSION  # For network interface detection
from speedview.update.version_checker import VersionChecker  # Adjust the import path as necessary
from speedview.update.updater import UpdateChecker
class SettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        if settings is None:
            raise ValueError("Settings object must be provided")
        self.settings = settings
        self.updater = UpdateChecker()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Network Monitor Settings")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(400)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create settings groups
        self.create_monitoring_group()
        self.create_behavior_group()
        self.create_display_group()
        self.create_notification_group()
        
        # Add dialog buttons
        self.create_button_box()
        
        # Load current settings
        self.load_settings()

    def create_menu_bar(self):
        """Create menu bar with Help, About, and Update options"""
        self.menu_bar = QMenuBar(self)
        
        # Help Menu
        help_menu = QMenu("&Help", self)
        self.menu_bar.addMenu(help_menu)
        
        help_action = QAction("View &Help", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        # About Menu
        about_menu = QMenu("&About", self)
        self.menu_bar.addMenu(about_menu)
        
        about_action = QAction("&About Network Speed Meter", self)
        about_action.triggered.connect(self.show_about)
        about_menu.addAction(about_action)
        
        version_action = QAction("Check for &Updates", self)
        version_action.triggered.connect(self.check_updates)
        about_menu.addAction(version_action)
        
        # Add menubar to layout
        self.layout.addWidget(self.menu_bar)  # Add the menu bar to the layout

    def show_help(self):
        """Show help documentation"""
        QMessageBox.information(self, "Help",
            """Network Speed Meter Help:
            
1. Monitoring Settings:
   - Select your network interface
   - Set maximum speeds for scaling
   - Adjust update interval
            
2. Application Behavior:
   - Configure startup options
   - System tray behavior
   
3. Display Settings:
   - Speed units and display options
   
4. Notification Settings:
   - Configure speed alerts
   - Set notification thresholds""")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About Network Speed Meter",
            f"""Network Speed Meter v{APP_VERSION}
            
A real-time network speed monitoring tool.
            
© 2024 Your Company
Licensed under MIT""")

    def check_updates(self):
        """Check for software updates"""
        try:
            version_checker = VersionChecker(APP_VERSION)  # Use the current app version
            has_update = version_checker.check_for_updates()
            
            if has_update:
                reply = QMessageBox.question(self, "Update Available",
                    "A new version is available. Would you like to update now?",
                    QMessageBox.Yes | QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    self.start_update()  # Implement the update logic
            else:
                QMessageBox.information(self, "Up to Date",
                    "You are running the latest version.")
        except Exception as e:
            QMessageBox.warning(self, "Update Check Failed",
                f"Could not check for updates:\n{str(e)}")

    def create_monitoring_group(self):
        """Create monitoring settings group."""
        group = QGroupBox("Monitoring Settings")
        layout = QFormLayout()
        
        # Network Interface Selection with refresh button and auto-select checkbox
        interface_layout = QVBoxLayout()
        
        # Interface selection row
        interface_select_layout = QHBoxLayout()
        self.network_interface_combo = QComboBox()
        self.refresh_interfaces_button = QPushButton("Refresh")
        self.refresh_interfaces_button.clicked.connect(self.refresh_interfaces)
        interface_select_layout.addWidget(self.network_interface_combo)
        interface_select_layout.addWidget(self.refresh_interfaces_button)
        interface_layout.addLayout(interface_select_layout)
        
        # Auto-select checkbox row
        auto_select_layout = QHBoxLayout()
        self.auto_select_checkbox = QCheckBox("Auto-select best interface")
        self.auto_select_checkbox.setToolTip("Automatically switch to the best available network interface")
        auto_select_layout.addWidget(self.auto_select_checkbox)
        interface_layout.addLayout(auto_select_layout)
        
        self.refresh_interfaces()  # Load initial interfaces
        layout.addRow("Network Interface:", interface_layout)
        
        # Max Speed
        self.max_speed_input = QSpinBox()
        self.max_speed_input.setRange(1, 10000)
        self.max_speed_input.setSuffix(" Mbps")
        self.max_speed_input.setToolTip("Maximum expected download speed for scaling")
        layout.addRow("Max Download Speed:", self.max_speed_input)
        
        # Max Upload Speed
        self.max_upload_input = QSpinBox()
        self.max_upload_input.setRange(1, 10000)
        self.max_upload_input.setSuffix(" Mbps")
        self.max_upload_input.setToolTip("Maximum expected upload speed for scaling")
        layout.addRow("Max Upload Speed:", self.max_upload_input)
        
        # Update Interval
        self.update_interval_input = QDoubleSpinBox()
        self.update_interval_input.setRange(0.1, 60.0)
        self.update_interval_input.setSuffix(" seconds")
        self.update_interval_input.setSingleStep(0.5)
        self.update_interval_input.setToolTip("How often to update the speed display")
        layout.addRow("Update Interval:", self.update_interval_input)
        
        group.setLayout(layout)
        self.layout.addWidget(group)

    def refresh_interfaces(self):
        """Refresh the list of network interfaces"""
        try:
            self.network_interface_combo.clear()
            interfaces = []
            stats = psutil.net_if_stats()
            
            # First add physical interfaces that are active
            for interface, stat in stats.items():
                if stat.isup and not any(x in interface.lower() for x in ['vethernet', 'vmware', 'virtual']):
                    speed = f"{stat.speed}Mbps" if stat.speed else "Unknown speed"
                    self.network_interface_combo.addItem(f"{interface} (Active - {speed})", interface)
                    interfaces.append(interface)
            
            # Then add virtual interfaces that are active
            for interface, stat in stats.items():
                if stat.isup and any(x in interface.lower() for x in ['vethernet', 'vmware', 'virtual']):
                    self.network_interface_combo.addItem(f"{interface} (Virtual - Active)", interface)
                    interfaces.append(interface)
            
            # Finally add inactive interfaces
            for interface, stat in stats.items():
                if not stat.isup:
                    self.network_interface_combo.addItem(f"{interface} (Inactive)", interface)
            
            # Restore selected interface if it exists
            if self.settings.selected_interface in interfaces:
                index = self.network_interface_combo.findData(self.settings.selected_interface)
                if index >= 0:
                    self.network_interface_combo.setCurrentIndex(index)
            
        except Exception as e:
            print(f"Error refreshing interfaces: {e}")
            self.network_interface_combo.addItem("No interfaces found")

    def create_behavior_group(self):
        """Create application behavior group."""
        group = QGroupBox("Application Behavior")
        layout = QFormLayout()
        
        self.start_minimized_checkbox = QCheckBox()
        self.start_minimized_checkbox.setToolTip("Start the application minimized to system tray")
        layout.addRow("Start Minimized:", self.start_minimized_checkbox)
        
        self.minimize_to_tray_checkbox = QCheckBox()
        self.minimize_to_tray_checkbox.setToolTip("Minimize to system tray instead of taskbar")
        layout.addRow("Minimize to Tray:", self.minimize_to_tray_checkbox)
        
        self.close_to_tray_checkbox = QCheckBox()
        self.close_to_tray_checkbox.setToolTip("Close button minimizes to tray instead of exiting")
        layout.addRow("Close to Tray:", self.close_to_tray_checkbox)
        
        group.setLayout(layout)
        self.layout.addWidget(group)

    def create_display_group(self):
        """Create display settings group."""
        group = QGroupBox("Display Settings")
        layout = QFormLayout()
        
        self.show_upload_speed_checkbox = QCheckBox()
        self.show_upload_speed_checkbox.setToolTip("Show upload speed in addition to download speed")
        layout.addRow("Show Upload Speed:", self.show_upload_speed_checkbox)
        
        self.speed_unit_combo = QComboBox()
        self.speed_unit_combo.addItems(["Mbps", "MB/s", "Kbps"])
        self.speed_unit_combo.setToolTip("Unit to display network speeds")
        layout.addRow("Speed Unit:", self.speed_unit_combo)
        
        group.setLayout(layout)
        self.layout.addWidget(group)

    def create_notification_group(self):
        """Create notification settings group."""
        group = QGroupBox("Notification Settings")
        layout = QFormLayout()
        
        self.enable_notifications_checkbox = QCheckBox()
        self.enable_notifications_checkbox.setToolTip("Enable desktop notifications")
        layout.addRow("Enable Notifications:", self.enable_notifications_checkbox)
        
        self.notification_threshold = QSpinBox()
        self.notification_threshold.setRange(1, 10000)
        self.notification_threshold.setSuffix(" Mbps")
        self.notification_threshold.setToolTip("Speed threshold for notifications")
        layout.addRow("Notification Threshold:", self.notification_threshold)
        
        group.setLayout(layout)
        self.layout.addWidget(group)

    def create_button_box(self):
        """Create the dialog button box."""
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | 
            QDialogButtonBox.Cancel | 
            QDialogButtonBox.RestoreDefaults
        )
        self.buttons.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restore_defaults)
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_network_interfaces(self):
        """Get list of available network interfaces."""
        interfaces = []
        try:
            stats = psutil.net_if_stats()
            for interface, stat in stats.items():
                if stat.isup:  # Only include active interfaces
                    interfaces.append(interface)
        except Exception as e:
            print(f"Error getting network interfaces: {e}")
        
        return interfaces or ["No interfaces found"]

    def load_settings(self):
        """Load current settings into the dialog."""
        self.max_speed_input.setValue(self.settings.max_speed)
        self.max_upload_input.setValue(self.settings.max_upload)
        self.update_interval_input.setValue(self.settings.update_interval)
        self.start_minimized_checkbox.setChecked(self.settings.start_minimized)
        self.minimize_to_tray_checkbox.setChecked(self.settings.minimize_to_tray)
        self.close_to_tray_checkbox.setChecked(self.settings.close_to_tray)
        self.show_upload_speed_checkbox.setChecked(self.settings.show_upload_speed)
        self.speed_unit_combo.setCurrentText(self.settings.speed_unit)
        self.enable_notifications_checkbox.setChecked(self.settings.enable_notifications)
        self.notification_threshold.setValue(self.settings.notification_threshold)
        
        # Set network interface
        index = self.network_interface_combo.findText(self.settings.selected_interface)
        if index >= 0:
            self.network_interface_combo.setCurrentIndex(index)

    def validate_and_accept(self):
        """Enhanced settings validation"""
        try:
            # Get the selected interface
            current_index = self.network_interface_combo.currentIndex()
            interface = self.network_interface_combo.itemData(current_index)
            
            if interface == "No interfaces found":
                raise ValueError("No valid network interface available")
            
            # Validate network interface is active
            stats = psutil.net_if_stats()
            if interface not in stats or not stats[interface].isup:
                reply = QMessageBox.question(
                    self,
                    "Interface Warning",
                    f"The selected interface '{interface}' appears to be inactive. "
                    "Would you like to select it anyway?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # Update settings
            self._update_settings()
            
            # Save settings
            try:
                self.settings.save()
            except Exception as e:
                raise ValueError(f"Failed to save settings: {str(e)}")
            
            super().accept()
            
        except ValueError as e:
            QMessageBox.critical(self, "Validation Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Settings Error", f"An unexpected error occurred:\n{str(e)}")

    def _validate_interface(self, interface):
        """Validate network interface"""
        try:
            stats = psutil.net_if_stats().get(interface)
            return stats and stats.isup
        except:
            return False

    def _update_settings(self):
        """Update settings from UI values"""
        # Get the selected interface from the combo box data
        current_index = self.network_interface_combo.currentIndex()
        selected_interface = self.network_interface_combo.itemData(current_index)
        
        # Only update interface if auto-select is disabled
        if not self.auto_select_checkbox.isChecked():
            self.settings.selected_interface = selected_interface
        
        # Store auto-select preference
        self.settings.auto_select_interface = self.auto_select_checkbox.isChecked()
        
        self.settings.max_speed = self.max_speed_input.value()
        self.settings.max_upload = self.max_upload_input.value()
        self.settings.update_interval = self.update_interval_input.value()
        self.settings.start_minimized = self.start_minimized_checkbox.isChecked()
        self.settings.minimize_to_tray = self.minimize_to_tray_checkbox.isChecked()
        self.settings.close_to_tray = self.close_to_tray_checkbox.isChecked()
        self.settings.show_upload_speed = self.show_upload_speed_checkbox.isChecked()
        self.settings.speed_unit = self.speed_unit_combo.currentText()
        self.settings.enable_notifications = self.enable_notifications_checkbox.isChecked()
        self.settings.notification_threshold = self.notification_threshold.value()

    def restore_defaults(self):
        """Restore default settings."""
        reply = QMessageBox.question(
            self,
            "Restore Defaults",
            "Are you sure you want to restore all settings to their default values?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.settings.restore_defaults()
            self.load_settings()
            QMessageBox.information(self, "Defaults Restored", 
                                  "All settings have been restored to default values.")

    def migrate_settings(self):
        """Add settings migration support"""
        current_version = 1
        if 'settings_version' not in self.settings.__dict__:
            # Perform settings migration
            self.settings.settings_version = current_version
            self.settings.save()

    def backup_settings(self):
        """Add settings backup/restore"""
        import json
        import time
        backup_path = f"settings_backup_{int(time.time())}.json"
        with open(backup_path, 'w') as f:
            json.dump(self.settings.__dict__, f, indent=4)

    def start_update(self):
        """Start the update process"""
        if self.updater.check_for_updates():
            # Logic to download and install the update
            update_file = self.updater.download_update()
            if update_file:
                QMessageBox.information(self, "Update Downloaded", "The update has been downloaded. It will be installed now.")
                self.updater.install_update(update_file)
            else:
                QMessageBox.warning(self, "Update Failed", "Failed to download the update.")
        else:
            QMessageBox.information(self, "No Updates", "You are already using the latest version.")
