import os
import platform
import sys

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import winreg
else:
    winreg = None

# Cross-platform fallback base directory when Windows env vars are unset
_APPDATA_BASE = os.getenv('APPDATA') or os.getenv('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
_PROGRAMFILES_BASE = os.getenv('PROGRAMFILES') or '/opt'

APPDATA_DIR = os.path.join(_APPDATA_BASE, 'NetworkSpeedMeter')
CONFIG_FILE = os.path.join(APPDATA_DIR, 'config.json')
LOG_FILE = os.path.join(APPDATA_DIR, 'app.log')
TEMP_DIR = os.path.join(APPDATA_DIR, 'temp')

# Registry settings
REG_PATH = r'Software\Microsoft\Windows\CurrentVersion\Run'
REG_AUTOSTART = 'SpeedView'

# Update settings
UPDATE_CHECK_INTERVAL = 24 * 60 * 60  # 24 hours in seconds
UPDATE_URL = "https://api.github.com/repos/zikani/speedview/releases/latest"

# Windows UI settings
MIN_WIDTH = 400
MIN_HEIGHT = 300
DEFAULT_WIDTH = 500
DEFAULT_HEIGHT = 500
FLOATING_WIDTH = 136
FLOATING_HEIGHT = 40

# System tray settings
TRAY_ICON_SIZE = 16
TRAY_UPDATE_INTERVAL = 1000  # milliseconds

# Installation paths
INSTALL_DIR = os.path.join(_PROGRAMFILES_BASE, 'NetworkSpeedMeter')
UNINSTALL_REG_PATH = r'Software\Microsoft\Windows\CurrentVersion\Uninstall\NetworkSpeedMeter'


def _get_launch_command():
    """Return executable and script/arguments for launching SpeedView."""
    if getattr(sys, 'frozen', False):
        return sys.executable, []
    main_py = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'main.py'))
    return sys.executable, [main_py]


def apply_startup_setting(enable=True):
    """Enable or disable SpeedView automatic startup across Windows, Linux, and macOS."""
    system = platform.system()
    exe_path, args = _get_launch_command()

    if system == "Windows" and winreg is not None:
        try:
            key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
            if enable:
                cmd = f'"{exe_path}"' + (f' "{args[0]}"' if args else '')
                winreg.SetValueEx(key, REG_AUTOSTART, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, REG_AUTOSTART)
                except FileNotFoundError:
                    pass
            return True
        except Exception as e:
            print(f"Error setting Windows autostart: {e}")
            return False

    if system == "Darwin":
        try:
            agents_dir = os.path.expanduser("~/Library/LaunchAgents")
            plist_path = os.path.join(agents_dir, "com.speedview.app.plist")
            if enable:
                os.makedirs(agents_dir, exist_ok=True)
                prog_args = "".join(f"        <string>{a}</string>\n" for a in [exe_path] + args)
                plist_content = (
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
                    '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
                    '<plist version="1.0">\n'
                    '<dict>\n'
                    '    <key>Label</key>\n'
                    '    <string>com.speedview.app</string>\n'
                    '    <key>ProgramArguments</key>\n'
                    '    <array>\n'
                    f'{prog_args}'
                    '    </array>\n'
                    '    <key>RunAtLoad</key>\n'
                    '    <true/>\n'
                    '</dict>\n'
                    '</plist>\n'
                )
                with open(plist_path, "w", encoding="utf-8") as f:
                    f.write(plist_content)
            elif os.path.exists(plist_path):
                os.remove(plist_path)
            return True
        except Exception as e:
            print(f"Error setting macOS autostart: {e}")
            return False

    # Linux / XDG desktop autostart
    try:
        xdg_config = os.getenv("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
        autostart_dir = os.path.join(xdg_config, "autostart")
        desktop_file = os.path.join(autostart_dir, "speedview.desktop")
        if enable:
            os.makedirs(autostart_dir, exist_ok=True)
            exec_cmd = f'"{exe_path}"' + (f' "{args[0]}"' if args else '')
            desktop_content = (
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=SpeedView\n"
                "Comment=Network Speed Meter\n"
                f"Exec={exec_cmd}\n"
                "Terminal=false\n"
                "Categories=Network;Utility;\n"
                "X-GNOME-Autostart-enabled=true\n"
            )
            with open(desktop_file, "w", encoding="utf-8") as f:
                f.write(desktop_content)
        elif os.path.exists(desktop_file):
            os.remove(desktop_file)
        return True
    except Exception as e:
        print(f"Error setting Linux autostart: {e}")
        return False


def set_autostart(enable=True):
    """Set application to start on system boot."""
    return apply_startup_setting(enable)


def create_uninstall_reg_key():
    """Create uninstall information in Windows registry"""
    if not IS_WINDOWS or winreg is None:
        return False
    try:
        key = winreg.CreateKeyEx(
            winreg.HKEY_LOCAL_MACHINE,
            r'Software\Microsoft\Windows\CurrentVersion\Uninstall\NetworkSpeedMeter',
        )

        values = {
            'DisplayName': 'Network Speed Meter',
            'DisplayVersion': '1.0.0',
            'Publisher': 'SpeedView',
            'UninstallString': os.path.join(INSTALL_DIR, 'uninstall.exe'),
            'DisplayIcon': os.path.join(INSTALL_DIR, 'NetworkSpeedMeter.exe'),
            'InstallLocation': INSTALL_DIR,
            'NoModify': 1,
            'NoRepair': 1,
        }

        for name, value in values.items():
            if isinstance(value, str):
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
            else:
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)

        return True
    except Exception as e:
        print(f"Error creating uninstall key: {e}")
        return False


def remove_uninstall_reg_key():
    """Remove uninstall information from Windows registry"""
    if not IS_WINDOWS or winreg is None:
        return False
    try:
        winreg.DeleteKey(
            winreg.HKEY_LOCAL_MACHINE,
            r'Software\Microsoft\Windows\CurrentVersion\Uninstall\NetworkSpeedMeter',
        )
        return True
    except Exception as e:
        print(f"Error removing uninstall key: {e}")
        return False


def check_single_instance():
    """Ensure only one instance is running"""
    if not IS_WINDOWS:
        return True
    try:
        import win32event
        import win32api
        import winerror
        mutex = win32event.CreateMutex(None, 1, "NetworkSpeedMeter_Mutex")
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            return False
        return True
    except Exception as e:
        print(f"Error checking single instance: {e}")
        return True  # Allow running if check fails