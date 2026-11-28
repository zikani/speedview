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
    "Added Program Files onedir packaging, Inno Setup Windows Installer/Uninstaller & PyQt5 Setup Wizard, main app icon, and Desktop shortcut creation",
    "Added 3-day GitHub Releases background auto-updater with temp .zip staging and Python subprocess swap-and-restart",
    "Updated About and Updater widgets to display all released version changelogs and features",
    "Added real-time TCP Ping / Latency indicator (#pingBadge) next to the speed gauge",
    "Rescaled compact transparent corner Float widget (signal + speed only), added gear icon Settings trigger, and redesigned Settings dark theme",
    "Unified close-to-Float and minimize-to-tray background lifecycle plus OS Start on Startup registration",
]

RELEASE_HISTORY = [
    {
        "version": "1.0.0",
        "date": "2026-11-28",
        "title": "Cross-Platform Auto-Updater, GUI Installer & Live Ping",
        "features": [
            "Real-time Ping / Latency badge next to the main speedometer gauge",
            "Transparent compact corner Float widget (136x40) with live signal bars and speed",
            "Bundled app icon (ICO/PNG/SVG/ICNS), Desktop shortcut creator, Inno Setup Installer & GUI Setup/Uninstaller wizard",
            "3-day rate-limited GitHub Releases background auto-updater with Python subprocess file replacement & restart",
        ],
        "changes": list(CURRENT_CHANGELOG),
    },
    {
        "version": "0.9.0",
        "date": "2026-11-15",
        "title": "Live File Speed Testing & SQLite Data Usage",
        "features": [
            "Real-time HTTP file streaming download & chunked upload speed test (measure_file_speed)",
            "Per-application SQLite Data Usage tracker (App | Data | Date) with Daily & Monthly reports",
            "System tray dynamic speed badge icon with live network tooltip sync",
        ],
        "changes": [
            "Added speedtest-cli and fast-cli fallbacks for network speed testing",
            "Built frameless SVG dialogs for Network Speed Test and Data Usage views",
            "Implemented structured Ethernet, Wi-Fi (SSID, band, signal %), Virtual, and Loopback interface detection",
        ],
    },
    {
        "version": "0.8.0",
        "date": "2026-11-01",
        "title": "Frameless SVG Speedometer & Floating Mode",
        "features": [
            "Translucent frameless SVG main speedometer card with gradient gauge arc",
            "Switchable Download/Upload gauge mode and Mbps, MB/s, Kbps units",
            "Persistent JSON settings and desktop high-speed threshold notifications",
        ],
        "changes": [
            "Implemented in-memory SVG rendering to eliminate disk temp-file flicker",
            "Added keyboard shortcuts (Ctrl+S, Ctrl+T, Ctrl+F, Ctrl+U, Esc)",
        ],
    },
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
DEFAULT_RELEASES_API_URL = "https://api.github.com/repos/zikani/speedview/releases"
DEFAULT_RELEASES_PAGE_URL = "https://github.com/zikani/speedview/releases"

# File paths
_CONFIG_BASE_DIR = os.getenv("APPDATA") or os.getenv("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
CONFIG_FILE = os.path.join(_CONFIG_BASE_DIR, "NetworkSpeedMeter", "network_speed_meter.conf")
RELEASES_CACHE_FILE = os.path.join(_CONFIG_BASE_DIR, "NetworkSpeedMeter", "releases_cache.json")
TEMP_SVG_FILE = "temp_speedometer.svg"

# UI Constants
WINDOW_SIZE = (500, 500)
FLOATING_WINDOW_SIZE = (136, 40)