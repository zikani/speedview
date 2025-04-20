import os
import json
import time
import logging

import psutil
from speedview.config.config import (
    DEFAULT_MAX_SPEED, DEFAULT_UPDATE_INTERVAL, DEFAULT_START_MINIMIZED,
    DEFAULT_MINIMIZE_TO_TRAY, DEFAULT_SHOW_UPLOAD_SPEED, DEFAULT_CLOSE_TO_TRAY,
    DEFAULT_MAX_UPLOAD, DEFAULT_ENABLE_NOTIFICATIONS, DEFAULT_NOTIFICATION_THRESHOLD,
    DEFAULT_SPEED_UNIT, CONFIG_FILE
)

logging.basicConfig(level=logging.DEBUG)

class SettingsError(Exception):
    """Base class for settings related errors"""
    pass

class ValidationError(SettingsError):
    """Error raised when settings validation fails"""
    pass

class SaveError(SettingsError):
    """Error raised when settings cannot be saved"""
    pass

class LoadError(SettingsError):
    """Error raised when settings cannot be loaded"""
    pass

class Settings:
    def __init__(self):
        # Core settings
        self.max_speed = DEFAULT_MAX_SPEED
        self.max_upload = DEFAULT_MAX_UPLOAD
        self.update_interval = DEFAULT_UPDATE_INTERVAL
        self.selected_interface = self._get_default_interface()  # Changed from None
        self.settings_version = 1  # Add version tracking

        # UI settings
        self.start_minimized = DEFAULT_START_MINIMIZED
        self.minimize_to_tray = DEFAULT_MINIMIZE_TO_TRAY
        self.close_to_tray = DEFAULT_CLOSE_TO_TRAY
        self.show_upload_speed = DEFAULT_SHOW_UPLOAD_SPEED
        self.speed_unit = DEFAULT_SPEED_UNIT
        self.is_floating = False
        self.show_test_notifications = True  # Add test notifications setting

        # Notification settings
        self.enable_notifications = DEFAULT_ENABLE_NOTIFICATIONS
        self.notification_threshold = DEFAULT_NOTIFICATION_THRESHOLD

        # Window state
        self.window_size = None
        self.window_position = None
        
        # Load saved settings if available
        self.load()

    def _get_default_interface(self):
        """Get the first active network interface as default"""
        try:
            stats = psutil.net_if_stats()
            # First try to find a wireless interface
            for interface, stat in stats.items():
                if stat.isup and "wi-fi" in interface.lower():
                    return interface
            # If no wireless interface, get the first active interface
            for interface, stat in stats.items():
                if stat.isup:
                    return interface
        except Exception as e:
            print(f"Error getting default interface: {e}")
        return None

    def load(self):
        """Load settings from file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save(self):
        """Save settings with proper error handling"""
        try:
            self.validate_settings()
            data = {
                'max_speed': self.max_speed,
                'max_upload': self.max_upload,
                'update_interval': self.update_interval,
                'selected_interface': self.selected_interface,
                'start_minimized': self.start_minimized,
                'minimize_to_tray': self.minimize_to_tray,
                'close_to_tray': self.close_to_tray,
                'show_upload_speed': self.show_upload_speed,
                'speed_unit': self.speed_unit,
                'is_floating': self.is_floating,
                'enable_notifications': self.enable_notifications,
                'notification_threshold': self.notification_threshold,
                'window_size': self.window_size,
                'window_position': self.window_position,
                'settings_version': self.settings_version
            }
            
            # Ensure the directory exists
            config_dir = os.path.dirname(CONFIG_FILE)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            retries = 3
            for attempt in range(retries):
                try:
                    logging.debug(f"Saving settings to {CONFIG_FILE}")
                    with open(CONFIG_FILE, 'w') as f:
                        json.dump(data, f, indent=4)
                    break
                except OSError as e:
                    if attempt < retries - 1:
                        time.sleep(1)  # Wait before retrying
                    else:
                        raise SettingsError(f"Failed to save settings: {str(e)}")
                
        except Exception as e:
            raise SettingsError(f"Failed to save settings: {str(e)}")

    def restore_defaults(self):
        """Reset all settings to default values"""
        self.__init__()

    def validate_settings(self):
        """Validate and fix settings values"""
        if not isinstance(self.max_speed, (int, float)) or self.max_speed <= 0:
            self.max_speed = DEFAULT_MAX_SPEED
        if not isinstance(self.max_upload, (int, float)) or self.max_upload <= 0:
            self.max_upload = DEFAULT_MAX_UPLOAD
        if not isinstance(self.update_interval, (int, float)) or self.update_interval < 0.1:
            self.update_interval = DEFAULT_UPDATE_INTERVAL
            
        # Validate network interface
        available_interfaces = list(psutil.net_if_stats().keys())
        if not self.selected_interface or self.selected_interface not in available_interfaces:
            self.selected_interface = self._get_default_interface()

    def backup_settings(self):
        """Create settings backup"""
        try:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            backup_path = f"settings_backup_{timestamp}.json"
            
            with open(backup_path, 'w') as f:
                json.dump(self.__dict__, f, indent=4)
            return backup_path
            
        except Exception as e:
            raise SettingsError(f"Failed to backup settings: {str(e)}")

    def restore_from_backup(self, backup_path):
        """Restore settings from backup"""
        try:
            with open(backup_path, 'r') as f:
                data = json.load(f)
                for key, value in data.items():
                    setattr(self, key, value)
            self.validate_settings()
            self.save()
        except Exception as e:
            raise SettingsError(f"Failed to restore settings: {str(e)}")
