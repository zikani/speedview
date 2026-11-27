import os
import platform

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import winshell
    from win32com.client import Dispatch
else:
    winshell = None
    Dispatch = None

from speedview.config.windows import INSTALL_DIR


def create_shortcut(target_path, shortcut_path, description="", arguments=""):
    """Create a Windows shortcut"""
    if not IS_WINDOWS or Dispatch is None:
        return False
    try:
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target_path
        shortcut.Arguments = arguments
        shortcut.Description = description
        shortcut.WorkingDirectory = os.path.dirname(target_path)
        shortcut.IconLocation = target_path
        shortcut.save()
        return True
    except Exception as e:
        print(f"Error creating shortcut: {e}")
        return False


def create_program_shortcuts():
    """Create all necessary program shortcuts"""
    if not IS_WINDOWS or winshell is None:
        return False
    try:
        exe_path = os.path.join(INSTALL_DIR, 'NetworkSpeedMeter.exe')

        # Desktop shortcut
        desktop = winshell.desktop()
        desktop_path = os.path.join(desktop, 'Network Speed Meter.lnk')
        create_shortcut(exe_path, desktop_path, "Network Speed Meter")

        # Start Menu shortcut
        start_menu = winshell.start_menu()
        programs_path = os.path.join(start_menu, 'Programs', 'Network Speed Meter')
        os.makedirs(programs_path, exist_ok=True)
        start_menu_path = os.path.join(programs_path, 'Network Speed Meter.lnk')
        create_shortcut(exe_path, start_menu_path, "Network Speed Meter")

        return True
    except Exception as e:
        print(f"Error creating program shortcuts: {e}")
        return False


def remove_shortcuts():
    """Remove all program shortcuts"""
    if not IS_WINDOWS or winshell is None:
        return False
    try:
        # Remove desktop shortcut
        desktop = winshell.desktop()
        desktop_path = os.path.join(desktop, 'Network Speed Meter.lnk')
        if os.path.exists(desktop_path):
            os.remove(desktop_path)

        # Remove Start Menu shortcuts
        start_menu = winshell.start_menu()
        programs_path = os.path.join(start_menu, 'Programs', 'Network Speed Meter')
        if os.path.exists(programs_path):
            winshell.delete_file(programs_path, no_confirm=True)

        return True
    except Exception as e:
        print(f"Error removing shortcuts: {e}")
        return False