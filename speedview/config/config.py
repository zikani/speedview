# Application-wide constants
import os


APP_NAME = "Network Speed Meter"
APP_VERSION = "1.0.0"

APP_FEATURES = [
    "Frameless translucent SVG speedometer with Download/Upload scale and gear Settings button",
    "Real-time Ping / Latency badge (ms) displayed alongside the main gauge",
    "Transparent corner Float pill (136x40) displaying live signal strength and speed",
    "Automatic interface detection (Ethernet, Wi-Fi SSID/band, Virtual, Loopback, link speed, IPv4/IPv6)",
    "Live HTTP file streaming speed test with speedtest-cli and fast-cli fallbacks",
    "Per-app SQLite Data Usage tracker (App | Data | Date) with Daily & Monthly reports",
    "Background system tray daemon, OS autostart (Windows/Linux/macOS), and close-to-Float workflow",
    "3-day rate-limited GitHub Releases background auto-updater with temp .zip staging & helper restart",
]

CURRENT_CHANGELOG = [
    "Added 3-day GitHub Releases background auto-updater with temp .zip staging and detached swap-and-restart helper scripts (Windows/macOS/Linux)",
    "Added automated PyInstaller release packaging (speedview.spec, scripts/build_windows.bat/.ps1, and GitHub Actions)",
    "Added real-time TCP Ping / Latency indicator (#pingBadge) next to the speed gauge",
    "Rescaled compact transparent corner Float widget (signal + speed only), added gear icon Settings trigger, and redesigned Settings dark theme",
    "Unified close-to-Float and minimize-to-tray background lifecycle plus OS Start on Startup registration",
]

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

# Update settings (check once every 3 days to avoid API rate limits)
DEFAULT_AUTO_UPDATE = True
UPDATE_CHECK_INTERVAL_SECONDS = 3 * 24 * 60 * 60
DEFAULT_UPDATE_URL = "https://api.github.com/repos/zikani/speedview/releases/latest"
DEFAULT_RELEASES_PAGE_URL = "https://github.com/zikani/speedview/releases"

# File paths
_CONFIG_BASE_DIR = os.getenv("APPDATA") or os.getenv("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
CONFIG_FILE = os.path.join(_CONFIG_BASE_DIR, "NetworkSpeedMeter", "network_speed_meter.conf")
TEMP_SVG_FILE = "temp_speedometer.svg"

# UI Constants
WINDOW_SIZE = (500, 500)
FLOATING_WINDOW_SIZE = (136, 40)