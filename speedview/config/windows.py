import os
import winreg

# Windows-specific paths
APPDATA_DIR = os.path.join(os.getenv('APPDATA'), 'NetworkSpeedMeter')
CONFIG_FILE = os.path.join(APPDATA_DIR, 'config.json')
LOG_FILE = os.path.join(APPDATA_DIR, 'app.log')
TEMP_DIR = os.path.join(APPDATA_DIR, 'temp')

# Registry settings
REG_PATH = r'Software\NetworkSpeedMeter'
REG_AUTOSTART = 'AutoStart'

# Update settings
UPDATE_CHECK_INTERVAL = 24 * 60 * 60  # 24 hours in seconds
UPDATE_URL = "https://api.github.com/repos/yourusername/network-speed-meter/releases/latest"

# Windows UI settings
MIN_WIDTH = 400
MIN_HEIGHT = 300
DEFAULT_WIDTH = 500
DEFAULT_HEIGHT = 500
FLOATING_WIDTH = 200
FLOATING_HEIGHT = 80

# System tray settings
TRAY_ICON_SIZE = 16
TRAY_UPDATE_INTERVAL = 1000  # milliseconds

# Installation paths
INSTALL_DIR = os.path.join(os.getenv('PROGRAMFILES'), 'NetworkSpeedMeter')
UNINSTALL_REG_PATH = r'Software\Microsoft\Windows\CurrentVersion\Uninstall\NetworkSpeedMeter'

def set_autostart(enable=True):
    """Set application to start with Windows"""
    try:
        key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, REG_PATH)
        app_path = os.path.join(INSTALL_DIR, 'NetworkSpeedMeter.exe')
        
        if enable:
            winreg.SetValueEx(key, REG_AUTOSTART, 0, winreg.REG_SZ, app_path)
        else:
            try:
                winreg.DeleteValue(key, REG_AUTOSTART)
            except FileNotFoundError:
                pass
        
        return True
    except Exception as e:
        print(f"Error setting autostart: {e}")
        return False

def create_uninstall_reg_key():
    """Create uninstall information in Windows registry"""
    try:
        key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, 
                                r'Software\Microsoft\Windows\CurrentVersion\Uninstall\NetworkSpeedMeter')
        
        values = {
            'DisplayName': 'Network Speed Meter',
            'DisplayVersion': '1.0.0',
            'Publisher': 'Your Company',
            'UninstallString': os.path.join(INSTALL_DIR, 'uninstall.exe'),
            'DisplayIcon': os.path.join(INSTALL_DIR, 'NetworkSpeedMeter.exe'),
            'InstallLocation': INSTALL_DIR,
            'NoModify': 1,
            'NoRepair': 1
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
    try:
        winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, 
                        r'Software\Microsoft\Windows\CurrentVersion\Uninstall\NetworkSpeedMeter')
        return True
    except Exception as e:
        print(f"Error removing uninstall key: {e}")
        return False

def check_single_instance():
    """Ensure only one instance is running"""
    import win32event, win32api, winerror
    try:
        mutex = win32event.CreateMutex(None, 1, "NetworkSpeedMeter_Mutex")
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            return False
        return True
    except Exception as e:
        print(f"Error checking single instance: {e}")
        return True  # Allow running if check fails