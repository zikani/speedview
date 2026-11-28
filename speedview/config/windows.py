import os
import platform
import sys

from speedview.config.config import APP_VERSION

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
if IS_WINDOWS:
    INSTALL_DIR = os.path.join(os.getenv('PROGRAMFILES') or r'C:\Program Files', 'SpeedView')
elif platform.system() == 'Darwin':
    INSTALL_DIR = '/Applications/SpeedView.app'
else:
    INSTALL_DIR = os.path.expanduser('~/.local/share/SpeedView')
UNINSTALL_REG_PATH = r'Software\Microsoft\Windows\CurrentVersion\Uninstall\SpeedView'


def _get_launch_command():
    """Return executable and script/arguments for launching SpeedView."""
    if getattr(sys, 'frozen', False):
        return sys.executable, []
    main_py = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'main.py'))
    return sys.executable, [main_py]


def get_desktop_shortcut_path():
    """Return the OS-appropriate desktop shortcut file path."""
    system = platform.system()
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if system == "Windows":
        return os.path.join(desktop, "SpeedView.lnk")
    if system == "Darwin":
        return os.path.join(desktop, "SpeedView.command")
    return os.path.join(desktop, "speedview.desktop")


def _create_windows_lnk(shortcut_path, target_exe, arguments="", icon_path="", working_dir="", description="SpeedView Network Speed Meter"):
    """Create a Windows .lnk shortcut using win32com/winshell or PowerShell WScript.Shell."""
    os.makedirs(os.path.dirname(shortcut_path), exist_ok=True)
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        sc = shell.CreateShortcut(shortcut_path)
        sc.TargetPath = target_exe
        if arguments:
            sc.Arguments = arguments
        if working_dir:
            sc.WorkingDirectory = working_dir
        if icon_path and os.path.exists(icon_path):
            sc.IconLocation = icon_path
        sc.Description = description
        sc.save()
        return os.path.exists(shortcut_path)
    except Exception:
        import subprocess
        ps_script = (
            f'$ws = New-Object -ComObject WScript.Shell; '
            f'$sc = $ws.CreateShortcut("{shortcut_path}"); '
            f'$sc.TargetPath = "{target_exe}"; '
            f'$sc.Arguments = "{arguments}"; '
            f'$sc.WorkingDirectory = "{working_dir}"; '
            f'$sc.Description = "{description}"; '
            + (f'$sc.IconLocation = "{icon_path}"; ' if icon_path and os.path.exists(icon_path) else '')
            + '$sc.Save()'
        )
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
        )
        return res.returncode == 0 and os.path.exists(shortcut_path)


def create_desktop_shortcut(target_path=None, icon_path=None):
    """Create a SpeedView shortcut on the user's Desktop across Windows, Linux, and macOS."""
    from speedview.utils.icon_utils import get_ico_path, get_png_icon_path

    system = platform.system()
    shortcut_path = get_desktop_shortcut_path()
    os.makedirs(os.path.dirname(shortcut_path), exist_ok=True)

    if target_path:
        exe_path = os.path.abspath(target_path)
        args = []
        work_dir = os.path.dirname(exe_path)
    else:
        exe_path, args = _get_launch_command()
        work_dir = os.path.dirname(args[0]) if args else os.path.dirname(exe_path)

    if system == "Windows":
        resolved_icon = icon_path or get_ico_path()
        arg_str = f'"{args[0]}"' if args else ""
        return _create_windows_lnk(
            shortcut_path=shortcut_path,
            target_exe=exe_path,
            arguments=arg_str,
            icon_path=resolved_icon,
            working_dir=work_dir,
        )

    if system == "Darwin":
        try:
            cmd = f'"{exe_path}"' + (f' "{args[0]}"' if args else '')
            with open(shortcut_path, "w", encoding="utf-8") as f:
                f.write(f"#!/bin/sh\nnohup {cmd} >/dev/null 2>&1 &\n")
            os.chmod(shortcut_path, 0o755)
            return os.path.isfile(shortcut_path)
        except OSError:
            return False

    try:
        resolved_icon = icon_path or get_png_icon_path()
        exec_cmd = f'"{exe_path}"' + (f' "{args[0]}"' if args else '')
        content = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=SpeedView\n"
            "Comment=Real-time Network Speed Meter\n"
            f"Exec={exec_cmd}\n"
            f"Icon={resolved_icon}\n"
            "Terminal=false\n"
            "Categories=Network;Utility;\n"
        )
        tmp = shortcut_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, shortcut_path)
        os.chmod(shortcut_path, 0o755)
        return os.path.isfile(shortcut_path)
    except OSError:
        return False


def remove_desktop_shortcut():
    """Remove the SpeedView desktop shortcut if it exists."""
    shortcut_path = get_desktop_shortcut_path()
    try:
        if os.path.lexists(shortcut_path):
            os.remove(shortcut_path)
        return not os.path.lexists(shortcut_path)
    except OSError:
        return False


def create_start_menu_shortcut(target_path=None, icon_path=None, uninstaller_path=None):
    """Create Start Menu / Applications shortcut (plus optional Uninstall shortcut)."""
    from speedview.utils.icon_utils import get_ico_path, get_png_icon_path

    system = platform.system()
    if target_path:
        exe_path = os.path.abspath(target_path)
        args = []
        work_dir = os.path.dirname(exe_path)
    else:
        exe_path, args = _get_launch_command()
        work_dir = os.path.dirname(args[0]) if args else os.path.dirname(exe_path)

    if system == "Windows":
        programs_dir = os.path.join(
            os.getenv("APPDATA") or os.path.expanduser("~"),
            "Microsoft", "Windows", "Start Menu", "Programs", "SpeedView",
        )
        os.makedirs(programs_dir, exist_ok=True)
        resolved_icon = icon_path or get_ico_path()
        ok = _create_windows_lnk(
            shortcut_path=os.path.join(programs_dir, "SpeedView.lnk"),
            target_exe=exe_path,
            arguments=f'"{args[0]}"' if args else "",
            icon_path=resolved_icon,
            working_dir=work_dir,
        )
        if uninstaller_path:
            _create_windows_lnk(
                shortcut_path=os.path.join(programs_dir, "Uninstall SpeedView.lnk"),
                target_exe=os.path.abspath(uninstaller_path),
                arguments="--uninstall",
                icon_path=resolved_icon,
                working_dir=work_dir,
                description="Uninstall SpeedView",
            )
        return ok

    if system == "Linux":
        apps_dir = os.path.join(
            os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share"),
            "applications",
        )
        os.makedirs(apps_dir, exist_ok=True)
        desktop_file = os.path.join(apps_dir, "speedview.desktop")
        resolved_icon = icon_path or get_png_icon_path()
        exec_cmd = f'"{exe_path}"' + (f' "{args[0]}"' if args else '')
        content = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=SpeedView\n"
            "Comment=Real-time Network Speed Meter\n"
            f"Exec={exec_cmd}\n"
            f"Icon={resolved_icon}\n"
            "Terminal=false\n"
            "Categories=Network;Utility;\n"
        )
        with open(desktop_file, "w", encoding="utf-8") as f:
            f.write(content)
        os.chmod(desktop_file, 0o755)
        return os.path.isfile(desktop_file)
    return True


def remove_start_menu_shortcut():
    """Remove Start Menu / Applications shortcuts."""
    import shutil
    system = platform.system()
    try:
        if system == "Windows":
            programs_dir = os.path.join(
                os.getenv("APPDATA") or os.path.expanduser("~"),
                "Microsoft", "Windows", "Start Menu", "Programs", "SpeedView",
            )
            if os.path.isdir(programs_dir):
                shutil.rmtree(programs_dir, ignore_errors=True)
        elif system == "Linux":
            apps_dir = os.path.join(
                os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share"),
                "applications",
            )
            desktop_file = os.path.join(apps_dir, "speedview.desktop")
            if os.path.lexists(desktop_file):
                os.remove(desktop_file)
        return True
    except OSError:
        return False


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
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if not xdg_config:
            xdg_config = os.path.expanduser("~/.config")
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
            tmp_file = desktop_file + ".tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                f.write(desktop_content)
            os.replace(tmp_file, desktop_file)
        elif os.path.lexists(desktop_file):
            os.remove(desktop_file)

        if enable:
            return os.path.isfile(desktop_file)
        return not os.path.lexists(desktop_file)
    except OSError as e:
        print(f"Error setting Linux autostart: {e}")
        return False


def set_autostart(enable=True):
    """Set application to start on system boot."""
    return apply_startup_setting(enable)


def create_uninstall_reg_key(install_dir=None, uninstall_cmd=None, icon_path=None, version_str=APP_VERSION):
    """Create uninstall information in Windows registry (HKLM with HKCU fallback for non-admin)."""
    if not IS_WINDOWS or winreg is None:
        return False
    target_dir = install_dir or INSTALL_DIR
    uninstall_exe = uninstall_cmd or f'"{os.path.join(target_dir, "SpeedView-Setup.exe")}" --uninstall'
    display_icon = icon_path or os.path.join(target_dir, "SpeedView.exe")
    values = {
        'DisplayName': 'SpeedView - Network Speed Meter',
        'DisplayVersion': version_str,
        'Publisher': 'SpeedView',
        'UninstallString': uninstall_exe,
        'DisplayIcon': display_icon,
        'InstallLocation': target_dir,
        'NoModify': 1,
        'NoRepair': 1,
    }
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            key = winreg.CreateKeyEx(hive, UNINSTALL_REG_PATH, 0, winreg.KEY_SET_VALUE)
            for name, value in values.items():
                if isinstance(value, str):
                    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
                else:
                    winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
            return True
        except Exception:
            continue
    return False


def remove_uninstall_reg_key():
    """Remove uninstall information from Windows registry."""
    if not IS_WINDOWS or winreg is None:
        return False
    removed = False
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            winreg.DeleteKey(hive, UNINSTALL_REG_PATH)
            removed = True
        except FileNotFoundError:
            pass
        except Exception:
            pass
    return removed


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
