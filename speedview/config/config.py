# Application-wide constants
import os


APP_NAME = "Network Speed Meter"
APP_VERSION = "1.0.0"

# Default settings
DEFAULT_MAX_SPEED = 100
DEFAULT_MAX_UPLOAD = 50  # Added default max upload speed
DEFAULT_UPDATE_INTERVAL = 1.0
DEFAULT_START_MINIMIZED = False
DEFAULT_START_ON_STARTUP = False
DEFAULT_MINIMIZE_TO_TRAY = True
DEFAULT_SHOW_UPLOAD_SPEED = False
DEFAULT_CLOSE_TO_TRAY = True  # Added default close to tray
DEFAULT_ENABLE_NOTIFICATIONS = True  # Added default notifications
DEFAULT_NOTIFICATION_THRESHOLD = 50  # Added default threshold
DEFAULT_SPEED_UNIT = "Mbps"  # Added default speed unit

# New settings for help and update
DEFAULT_SHOW_HELP = True
DEFAULT_SHOW_ABOUT = True

# Update URL for the update checker
DEFAULT_UPDATE_URL = "https://api.github.com/repos/zikani/speedview/releases/latest"
DEFAULT_RELEASES_PAGE_URL = "https://github.com/zikani/speedview/releases"

# File paths
_CONFIG_BASE_DIR = os.getenv("APPDATA") or os.getenv("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
CONFIG_FILE = os.path.join(_CONFIG_BASE_DIR, "NetworkSpeedMeter", "network_speed_meter.conf")
TEMP_SVG_FILE = "temp_speedometer.svg"

# UI Constants
WINDOW_SIZE = (500, 500)
FLOATING_WINDOW_SIZE = (136, 40)